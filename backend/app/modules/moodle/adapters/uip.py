
from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qs, urlparse

import dateparser
from playwright.async_api import Locator, Page

from app.core.config import settings
from app.modules.moodle.adapters.base import MoodleAdapter
from app.modules.moodle.client import MoodleClient
from app.modules.moodle.models import (
    MoodleCourse,
    MoodleGradeItem,
    MoodleModule,
    MoodleModuleSurvey,
)


class UIPMoodleAdapter(MoodleAdapter):
    def __init__(self, username: str, password: str, base_url: Optional[str] = None):
        self._client = MoodleClient(base_url or settings.MOODLE_BASE_URL, username, password)
        self._logger = logging.getLogger("moodle")
        self._logged_in = False
        self._courses_cache: list[MoodleCourse] | None = None
        self._modules_cache: dict[str, list[MoodleModule]] = {}

    async def login(self) -> None:
        if self._logged_in:
            return
        if not self._client.base_url or not self._client.username or not self._client.password:
            raise ValueError("Missing Moodle credentials or base URL.")

        for attempt in range(3):
            try:
                page = await self._client.open()

                await page.goto(self._client.base_url, wait_until="domcontentloaded", timeout=30000)

                if await page.locator("body#page-my-index").count() == 0:
                    login_form = page.locator("input[name='username']")
                    if await login_form.count() > 0:
                        await page.fill("input[name='username']", self._client.username)
                        await page.fill("input[name='password']", self._client.password)
                await page.click("button[type='submit']")
                await page.wait_for_timeout(1500)

                await page.goto(
                    f"{self._client.base_url}/my/",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                await page.wait_for_timeout(1500)
                has_dashboard = await page.locator("body#page-my-index").count() > 0
                has_user_menu = await page.locator("#user-menu-toggle").count() > 0
                has_logout = await page.locator("a[href*='logout']").count() > 0
                has_loggedin_body = await page.locator("body.loggedin").count() > 0
                has_userid = await page.locator("[data-userid]").count() > 0

                if not (has_dashboard or has_user_menu or has_logout or has_loggedin_body or has_userid):
                    await page.goto(self._client.base_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(1000)
                    has_user_menu = await page.locator("#user-menu-toggle").count() > 0
                    has_logout = await page.locator("a[href*='logout']").count() > 0
                    has_loggedin_body = await page.locator("body.loggedin").count() > 0
                    has_userid = await page.locator("[data-userid]").count() > 0
                    if not (has_user_menu or has_logout or has_loggedin_body or has_userid):
                        raise RuntimeError("Login failed or dashboard not detected.")

                self._logger.info("[Moodle] Login OK")
                self._logged_in = True
                return
            except Exception as exc:
                self._logger.warning("[Moodle] Login attempt %s failed: %s", attempt + 1, exc)
                await self._client.close()
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    raise
    async def close(self) -> None:
        await self._client.close()
        self._logged_in = False
        self._courses_cache = None
        self._modules_cache = {}

    async def get_courses(self) -> list[MoodleCourse]:
        await self.login()
        if self._courses_cache is not None:
            return list(self._courses_cache)

        for attempt in range(3):
            try:
                page = await self._client.get_page(f"{self._client.base_url}/my/")
                course_cards = page.locator("[data-region='course-content'][data-course-id]")
                if await course_cards.count() == 0:
                    try:
                        await page.wait_for_selector(
                            "[data-region='course-content'][data-course-id]",
                            timeout=5000,
                        )
                        course_cards = page.locator("[data-region='course-content'][data-course-id]")
                    except Exception:
                        page = await self._client.get_page(f"{self._client.base_url}/my/courses.php")
                        course_cards = page.locator("[data-region='course-content'][data-course-id]")
                count = await course_cards.count()

                courses: dict[str, MoodleCourse] = {}
                for idx in range(count):
                    card = course_cards.nth(idx)
                    course_id = await card.get_attribute("data-course-id")
                    if not course_id:
                        continue
                    link = card.locator("a.coursename").first
                    href = await link.get_attribute("href")
                    name = await _extract_course_name(link)
                    if not name:
                        name = f"Course {course_id}"
                    if href:
                        courses[course_id] = MoodleCourse(id=course_id, name=name)

                if not courses:
                    links = page.locator("a[href*='course/view.php?id=']")
                    link_count = await links.count()
                    for idx in range(link_count):
                        link = links.nth(idx)
                        href = await link.get_attribute("href") or ""
                        course_id = _extract_course_id(href)
                        if not course_id:
                            continue
                        name = await _extract_course_name(link)
                        if not name:
                            name = f"Course {course_id}"
                        courses[course_id] = MoodleCourse(id=course_id, name=name)

                self._courses_cache = list(courses.values())
                return list(self._courses_cache)
            except Exception as exc:
                self._logger.warning("[Moodle] Get courses attempt %s failed: %s", attempt + 1, exc)
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    raise

    async def get_modules(self, course_id: str) -> list[MoodleModule]:
        await self.login()
        if course_id in self._modules_cache:
            return list(self._modules_cache[course_id])
        page = await self._client.get_page(f"{self._client.base_url}/course/view.php?id={course_id}")
        modules = await _extract_modules(page, course_id)
        self._modules_cache[course_id] = modules
        return list(modules)

    async def get_grades(self) -> list[MoodleGradeItem]:
        await self.login()
        courses = await self.get_courses()
        course_ids = [course.id for course in courses]
        return await _fetch_grade_items(self._client, course_ids)

    async def get_quizzes(self) -> list[MoodleGradeItem]:
        await self.login()
        courses = await self.get_courses()
        course_ids = [course.id for course in courses]
        return await _fetch_grade_items(self._client, course_ids, item_type_filter={"quiz"})

    async def get_surveys(self) -> list[MoodleModuleSurvey]:
        await self.login()
        courses = await self.get_courses()
        modules: list[MoodleModule] = []
        for course in courses:
            modules.extend(await self.get_modules(course.id))
        updated_modules, surveys = await _enrich_modules_with_surveys(self._client, modules)
        self._update_module_cache(updated_modules)
        return surveys

    async def complete_survey(self, completion_url: str) -> dict:
        await self.login()
        page = await self._client.get_page(completion_url)
        form_found, reason = await _fill_feedback_form(page)
        if not form_found:
            return {
                "submitted": False,
                "url": page.url,
                "reason": reason or "form_not_found",
            }

        submit = page.locator("form#feedback_complete_form input[type='submit'][name='savevalues']").first
        if await submit.count() == 0:
            completed, completion_reason = await _detect_completion_status(page)
            if completed is True:
                return {
                    "submitted": True,
                    "url": page.url,
                    "reason": completion_reason or "already_completed",
                }
            return {
                "submitted": True,
                "url": page.url,
                "reason": completion_reason or "submit_not_found_assumed_complete",
            }

        await submit.click()
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(1000)

        form_present = await page.locator("form#feedback_complete_form").count() > 0
        if not form_present:
            result = {"submitted": True, "url": page.url}
        else:
            completed, completion_reason = await _detect_completion_status(page)
            result = {
                "submitted": bool(completed),
                "url": page.url,
                "reason": completion_reason or "submit_unknown",
            }
        self._logger.info("[Moodle] Survey completion result: %s", result)
        return result

    def _update_module_cache(self, modules: list[MoodleModule]) -> None:
        grouped: dict[str, list[MoodleModule]] = {}
        for module in modules:
            grouped.setdefault(module.course_id, []).append(module)
        for course_id, course_modules in grouped.items():
            self._modules_cache[course_id] = course_modules


async def _fetch_grade_items(
    client: MoodleClient,
    course_ids: list[str],
    item_type_filter: set[str] | None = None,
) -> list[MoodleGradeItem]:
    items: list[MoodleGradeItem] = []
    for course_id in course_ids:
        items.extend(await _extract_grade_items(client, course_id, item_type_filter=item_type_filter))
    return items


async def _extract_modules(page: Page, course_id: str) -> list[MoodleModule]:
    modules = await _extract_modules_from_courseindex(page, course_id)
    if modules:
        return modules
    return await _extract_modules_from_activity_list(page, course_id)

async def _extract_grade_items(
    client: MoodleClient,
    course_id: str,
    item_type_filter: set[str] | None = None,
) -> list[MoodleGradeItem]:
    items: list[MoodleGradeItem] = []
    base_items: list[dict] = []
    try:
        page = await client.get_page(f"{client.base_url}/grade/report/user/index.php?id={course_id}")
    except Exception as exc:
        logging.getLogger("moodle").warning(
            "[Moodle] Grade report load failed for course %s: %s", course_id, exc
        )
        return items
    try:
        await page.wait_for_selector("table.user-grade", timeout=5000)
    except Exception:
        logging.getLogger("moodle").warning("[Moodle] No grade table found for course %s", course_id)
        return items

    rows = page.locator("table.user-grade tbody tr")
    count = await rows.count()
    for idx in range(count):
        row = rows.nth(idx)
        link = row.locator("th.column-itemname a.gradeitemheader").first
        if await link.count() == 0:
            link = row.locator("th.column-itemname a[href*='mod/']").first
        if await link.count() == 0:
            continue

        title = _normalize_text((await link.text_content()) or "")
        url = await link.get_attribute("href") or ""
        external_id = _extract_activity_id_from_url(url) or f"{course_id}-item-{idx + 1}"

        item_type_label = _normalize_text(await _text_or_empty(row, "th.column-itemname .dimmed_text"))
        if not item_type_label:
            icon = row.locator("th.column-itemname img[alt]").first
            if await icon.count() > 0:
                item_type_label = _normalize_text((await icon.get_attribute("alt")) or "")
        item_type = _map_grade_item_type(item_type_label)
        if not item_type and url:
            item_type = _map_grade_item_type_from_url(url)
        if item_type_filter and item_type not in item_type_filter:
            continue
        if not item_type:
            continue
        grade_display = _normalize_text(
            await _text_or_empty(row, "td.column-grade div.d-flex > div:first-child")
        )
        if not grade_display:
            grade_display = _normalize_text(await _text_or_empty(row, "td.column-grade"))
        grade_value = _parse_grade_value(grade_display)
        if grade_value is None:
            grade_display = ""

        base_items.append(
            {
                "id": external_id,
                "course_id": course_id,
                "title": title or f"Actividad {idx + 1}",
                "item_type": item_type,
                "grade_value": grade_value,
                "grade_display": grade_display or None,
                "url": url or None,
            }
        )

    for base in base_items:
        available_at = None
        due_at = None
        submission_status = None
        grading_status = None
        last_submission_at = None
        attempts_allowed = None
        time_limit_minutes = None
        url = base.get("url")
        if url and "mod/assign/view.php" in url:
            details = await _extract_assignment_details(client, url)
            available_at = details.get("available_at")
            due_at = details.get("due_at")
            submission_status = details.get("submission_status")
            grading_status = details.get("grading_status")
            last_submission_at = details.get("last_submission_at")
        elif url and "mod/quiz/view.php" in url:
            details = await _extract_quiz_details(client, url)
            available_at = details.get("available_at")
            due_at = details.get("due_at")
            attempts_allowed = details.get("attempts_allowed")
            time_limit_minutes = details.get("time_limit_minutes")

        items.append(
            MoodleGradeItem(
                id=base["id"],
                course_id=base["course_id"],
                title=base["title"],
                item_type=base["item_type"],
                grade_value=base["grade_value"],
                grade_display=base["grade_display"],
                url=url,
                available_at=available_at,
                due_at=due_at,
                submission_status=submission_status,
                grading_status=grading_status,
                last_submission_at=last_submission_at,
                attempts_allowed=attempts_allowed,
                time_limit_minutes=time_limit_minutes,
            )
        )

    return items


async def _extract_modules_from_courseindex(page: Page, course_id: str) -> list[MoodleModule]:
    modules: list[MoodleModule] = []
    section_nodes = page.locator(".grid-section.card .grid-section-inner")
    count = await section_nodes.count()
    logging.getLogger("moodle").info("[Moodle] Course index sections detected: %s", count)
    if count == 0:
        return modules

    for idx in range(count):
        section = section_nodes.nth(idx)

        href = await section.get_attribute("href") or ""
        title = _normalize_text(await _text_or_empty(section, ".card-body .card-header .text-truncate"))
        if not title:
            title = _normalize_text(await _text_or_empty(section, ".card-header"))
        module_id = href.split("id=")[-1].split("&")[0]

        locked = await section.locator(".courseindex-locked").count() > 0
        visible = not locked
        blocked = locked
        block_reason = "locked" if locked else None
        has_survey = False

        modules.append(
            MoodleModule(
                id=module_id,
                course_id=course_id,
                title=title or f"Module {idx + 1}",
                visible=visible,
                blocked=blocked,
                block_reason=block_reason,
                has_survey=has_survey,
                url=href or None,
            )
        )

        logging.getLogger("moodle").debug(
            "[Moodle] Course %s module detected: %s", course_id, asdict(modules[-1])
        )

    return modules


async def _extract_modules_from_activity_list(page: Page, course_id: str) -> list[MoodleModule]:
    modules: list[MoodleModule] = []
    activity_nodes = page.locator("li.activity-wrapper[data-id]")
    count = await activity_nodes.count()

    for idx in range(count):
        activity = activity_nodes.nth(idx)
        title = (await _text_or_empty(activity, ".instancename")) or (
            await _text_or_empty(activity, ".activityname")
        )
        title = _normalize_text(title) or f"Activity {idx + 1}"
        module_id = await activity.get_attribute("data-id") or f"activity-{idx + 1}"
        link = activity.locator("a[href*='mod/']").first
        if await link.count() == 0:
            link = activity.locator("a[href]").first
        href = await link.get_attribute("href") or ""

        class_attr = (await activity.get_attribute("class")) or ""
        visible = "dimmed" not in class_attr and "hidden" not in class_attr

        availability_text = (await _text_or_empty(activity, ".availabilityinfo")).strip()
        blocked = bool(availability_text)
        block_reason = availability_text if availability_text else None

        has_survey = await _has_survey(activity)

        modules.append(
            MoodleModule(
                id=module_id,
                course_id=course_id,
                title=title,
                visible=visible,
                blocked=blocked,
                block_reason=block_reason,
                has_survey=has_survey,
                url=href or None,
            )
        )

    return modules

async def _enrich_modules_with_surveys(
    client: MoodleClient, modules: list[MoodleModule]
) -> tuple[list[MoodleModule], list[MoodleModuleSurvey]]:
    module_surveys: list[MoodleModuleSurvey] = []
    has_survey_map: dict[tuple[str, str], bool] = {
        (module.course_id, module.id): module.has_survey for module in modules
    }

    for module in modules:
        if not module.url or "course/section.php" not in module.url:
            continue
        try:
            page = await client.get_page(module.url)
            surveys = await _extract_module_surveys(page, module, client.base_url)
        except Exception as exc:
            logging.getLogger("moodle").warning(
                "[Moodle] Module survey load failed for %s: %s", module.url, exc
            )
            continue
        key = (module.course_id, module.id)
        has_survey_map[key] = bool(surveys)
        if surveys:
            module_surveys.extend(surveys)

    updated_modules: list[MoodleModule] = []
    for module in modules:
        key = (module.course_id, module.id)
        updated_modules.append(
            MoodleModule(
                id=module.id,
                course_id=module.course_id,
                title=module.title,
                visible=module.visible,
                blocked=module.blocked,
                block_reason=module.block_reason,
                has_survey=has_survey_map.get(key, False),
                url=module.url,
            )
        )

    return updated_modules, module_surveys


async def _text_or_empty(scope: Locator, selector: str) -> str:
    node = scope.locator(selector).first
    if await node.count() == 0:
        return ""
    return (await node.text_content()) or ""


async def _has_survey(activity: Locator) -> bool:
    class_attr = (await activity.get_attribute("class")) or ""
    if "modtype_feedback" not in class_attr and "modtype_survey" not in class_attr:
        return False
    title = (await _text_or_empty(activity, ".instancename")) or (
        await _text_or_empty(activity, ".activityname")
    )
    return _matches_survey_name(title)


async def _extract_module_surveys(
    page: Page, module: MoodleModule, base_url: str
) -> list[MoodleModuleSurvey]:
    surveys: list[MoodleModuleSurvey] = []
    activity_nodes = page.locator("li.activity-wrapper")
    count = await activity_nodes.count()

    for idx in range(count):
        activity = activity_nodes.nth(idx)
        class_attr = (await activity.get_attribute("class")) or ""
        if "modtype_feedback" not in class_attr and "modtype_survey" not in class_attr:
            continue

        title = (await _text_or_empty(activity, ".instancename")) or (
            await _text_or_empty(activity, ".activityname")
        )
        title = _normalize_text(title)
        if not _matches_survey_name(title):
            continue

        module_id = module.id
        activity_id = await activity.get_attribute("data-id") or f"survey-{idx + 1}"
        link = activity.locator("a[href*='mod/feedback']").first
        if await link.count() == 0:
            link = activity.locator("a[href*='mod/survey']").first
        if await link.count() == 0:
            link = activity.locator("a[href]").first
        href = await link.get_attribute("href") or ""

        completion_url = None
        if activity_id.isdigit() and module.course_id.isdigit():
            completion_url = (
                f"{base_url.rstrip('/')}/mod/feedback/complete.php"
                f"?id={activity_id}&courseid={module.course_id}"
            )

        surveys.append(
            MoodleModuleSurvey(
                id=activity_id,
                module_id=module_id,
                course_id=module.course_id,
                title=title or "Enviar encuesta",
                url=href or None,
                completion_url=completion_url,
            )
        )

    return surveys


def _normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def _matches_survey_name(value: str) -> bool:
    if not value:
        return False
    lowered = _normalize_text(value).lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return "envianos tu opinion" in normalized


def _map_grade_item_type(value: str) -> str | None:
    if not value:
        return None
    lowered = _normalize_text(value).lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    if "tarea" in normalized:
        return "assignment"
    if "cuestionario" in normalized or "quiz" in normalized:
        return "quiz"
    return None


def _parse_grade_value(value: str) -> float | None:
    if not value:
        return None
    cleaned = value.strip()
    if cleaned == "-" or cleaned.lower() == "na":
        return None
    cleaned = cleaned.replace("%", "").strip()
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_activity_id_from_url(url: str) -> str | None:
    if "id=" not in url:
        return None
    return url.split("id=")[-1].split("&")[0]


def _map_grade_item_type_from_url(url: str) -> str | None:
    normalized = _normalize_text(url).lower()
    if "mod/assign" in normalized:
        return "assignment"
    if "mod/quiz" in normalized:
        return "quiz"
    return None

async def _extract_assignment_details(client: MoodleClient, url: str) -> dict[str, str | None]:
    details: dict[str, str | None] = {
        "available_at": None,
        "due_at": None,
        "submission_status": None,
        "grading_status": None,
        "last_submission_at": None,
    }
    try:
        page = await client.get_page(url)
        available_at, due_at = await _extract_activity_dates(page)
        details["available_at"] = available_at
        details["due_at"] = due_at

        try:
            await page.wait_for_selector(".submissionstatustable table", timeout=3000)
        except Exception:
            pass
        rows = page.locator(".submissionstatustable table tr")
        row_count = await rows.count()
        for idx in range(row_count):
            row = rows.nth(idx)
            label = _normalize_text(await _text_or_empty(row, "th"))
            value = _normalize_text(await _text_or_empty(row, "td"))
            normalized_label = _normalize_for_compare(label)
            if "estado de la entrega" in normalized_label:
                details["submission_status"] = value or None
            elif "estado de la calificacion" in normalized_label:
                details["grading_status"] = value or None
            elif "ultima modificacion" in normalized_label:
                details["last_submission_at"] = _format_datetime(_parse_spanish_datetime(value))
    except Exception as exc:
        logging.getLogger("moodle").warning("[Moodle] Assignment detail parse failed: %s", exc)
    return details


async def _extract_quiz_details(client: MoodleClient, url: str) -> dict[str, str | int | None]:
    details: dict[str, str | int | None] = {
        "available_at": None,
        "due_at": None,
        "attempts_allowed": None,
        "time_limit_minutes": None,
    }
    try:
        page = await client.get_page(url)
        available_at, due_at = await _extract_activity_dates(page)
        details["available_at"] = available_at
        details["due_at"] = due_at

        try:
            await page.wait_for_selector(".quizinfo p", timeout=3000)
        except Exception:
            pass
        info_nodes = page.locator(".quizinfo p")
        info_count = await info_nodes.count()
        for idx in range(info_count):
            text = _normalize_text((await info_nodes.nth(idx).text_content()) or "")
            normalized = _normalize_for_compare(text)
            if "intentos permitidos" in normalized:
                details["attempts_allowed"] = _parse_int_after_label(text)
            elif "limite de tiempo" in normalized:
                details["time_limit_minutes"] = _parse_duration_minutes(text)
    except Exception as exc:
        logging.getLogger("moodle").warning("[Moodle] Quiz detail parse failed: %s", exc)
    return details


async def _extract_activity_dates(page: Page) -> tuple[str | None, str | None]:
    def parse_lines(lines: list[str]) -> tuple[str | None, str | None]:
        available_at = None
        due_at = None
        for line in lines:
            text = _normalize_text(line)
            if not text:
                continue
            lowered = _normalize_for_compare(text)
            if any(keyword in lowered for keyword in ("apertura", "abre", "abrio")):
                available_at = _format_datetime(_parse_spanish_datetime(_split_after_label(text)))
            elif any(keyword in lowered for keyword in ("cierre", "cierra", "cerro")):
                due_at = _format_datetime(_parse_spanish_datetime(_split_after_label(text)))
        return available_at, due_at

    selectors = [
        ".activity-dates div",
        "[data-region='activity-dates'] div",
        ".activity-information .activity-dates div",
    ]
    for selector in selectors:
        try:
            await page.wait_for_selector(selector, timeout=3000)
        except Exception:
            continue
        nodes = page.locator(selector)
        count = await nodes.count()
        if count == 0:
            continue
        lines = []
        for idx in range(count):
            lines.append((await nodes.nth(idx).text_content()) or "")
        available_at, due_at = parse_lines(lines)
        if available_at or due_at:
            return available_at, due_at

    container_selectors = [
        ".activity-dates",
        "[data-region='activity-dates']",
        ".activity-information .activity-dates",
    ]
    for selector in container_selectors:
        container = page.locator(selector).first
        if await container.count() == 0:
            continue
        try:
            raw = (await container.inner_text()) or ""
        except Exception:
            continue
        lines = [line for line in raw.splitlines() if line.strip()]
        available_at, due_at = parse_lines(lines)
        if available_at or due_at:
            return available_at, due_at
    return None, None


def _normalize_for_compare(value: str) -> str:
    lowered = _normalize_text(value).lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _split_after_label(value: str) -> str:
    if ":" not in value:
        return value
    return value.split(":", 1)[1].strip()


def _parse_spanish_datetime(value: str) -> datetime | None:
    if not value:
        return None
    cleaned = _normalize_text(value)
    parsed = dateparser.parse(
        cleaned,
        languages=["es"],
        settings={
            "RETURN_AS_TIMEZONE_AWARE": True,
            "TIMEZONE": "UTC",
            "PREFER_DAY_OF_MONTH": "first",
        },
    )
    if parsed:
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    cleaned = re.sub(r"^[^\d,]+,\s*", "", cleaned)
    match = re.search(r"(\d{1,2}) de (\w+) de (\d{4}), (\d{2}):(\d{2})", cleaned)
    if not match:
        return None
    day = int(match.group(1))
    month_name = _normalize_for_compare(match.group(2))
    year = int(match.group(3))
    hour = int(match.group(4))
    minute = int(match.group(5))
    months = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "setiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }
    month = months.get(month_name)
    if not month:
        return None
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def _format_datetime(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.isoformat()


def _parse_int_after_label(value: str) -> int | None:
    if ":" in value:
        value = value.split(":", 1)[1].strip()
    match = re.search(r"(\d+)", value)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _parse_duration_minutes(value: str) -> int | None:
    if ":" in value:
        value = value.split(":", 1)[1].strip()
    match = re.search(r"(\d+)", value)
    if not match:
        return None
    amount = int(match.group(1))
    normalized = _normalize_for_compare(value)
    if "hora" in normalized:
        return amount * 60
    return amount

async def _fill_feedback_form(page: Page) -> tuple[bool, str | None]:
    await page.wait_for_load_state("domcontentloaded")

    form_selector = "form#feedback_complete_form"
    try:
        await page.wait_for_selector(form_selector, timeout=10000)
    except Exception:
        form_selector = ""

    form = page.locator(form_selector).first if form_selector else page.locator("form").first
    if await form.count() == 0:
        form = page.locator("form.feedback_form").first
    if await form.count() == 0:
        form = page.locator("form[action*='mod/feedback/complete.php']").first
    if await form.count() == 0:
        login_form = page.locator("input[name='username'], input[name='password']")
        if await login_form.count() > 0:
            return False, "login_required"
        return False, "form_not_found"

    radio_names = await form.locator("input[type='radio'][name]").evaluate_all(
        "els => Array.from(new Set(els.map(e => e.name)))"
    )
    for name in radio_names:
        group = form.locator(f"input[type='radio'][name='{name}']")
        checked = await group.evaluate_all("els => els.some(e => e.checked)")
        if checked:
            continue
        option = group.first
        if await option.count() == 0 or await option.is_disabled():
            continue
        await option.check()

    checkbox_names = await form.locator("input[type='checkbox'][name]").evaluate_all(
        "els => Array.from(new Set(els.map(e => e.name)))"
    )
    for name in checkbox_names:
        group = form.locator(f"input[type='checkbox'][name='{name}']")
        checked = await group.evaluate_all("els => els.some(e => e.checked)")
        if checked:
            continue
        option = group.first
        if await option.count() == 0 or await option.is_disabled():
            continue
        await option.check()

    selects = form.locator("select[name]")
    for idx in range(await selects.count()):
        select = selects.nth(idx)
        values = await select.evaluate("el => Array.from(el.options).map(o => o.value)")
        chosen = None
        for value in values:
            if value is not None and value != "":
                chosen = value
                break
        if chosen is None and values:
            chosen = values[0]
        if chosen is not None:
            await select.select_option(chosen)

    textareas = form.locator("textarea[name]")
    for idx in range(await textareas.count()):
        field = textareas.nth(idx)
        if (await field.input_value()).strip():
            continue
        await field.fill("Sin comentarios.")

    inputs = form.locator(
        "input[type='text'][name], input[type='number'][name], input[type='email'][name]"
    )
    for idx in range(await inputs.count()):
        field = inputs.nth(idx)
        if (await field.input_value()).strip():
            continue
        await field.fill("Sin comentarios.")

    return True, None


async def _detect_completion_status(page: Page) -> tuple[Optional[bool], Optional[str]]:
    completion_text = await _safe_text(page.locator(".completion-info").first)
    normalized_completion = _normalize_for_compare(completion_text)
    if "por hacer" in normalized_completion:
        return False, "completion_pending"
    if "completado" in normalized_completion or "completo" in normalized_completion:
        return True, "completion_badge"

    body_text = await _safe_text(page.locator("body").first)
    normalized = _normalize_for_compare(body_text)
    success_markers = [
        "gracias por completar",
        "gracias por enviar",
        "sus respuestas han sido enviadas",
        "respuestas han sido enviadas",
        "respuestas guardadas",
        "ya ha completado",
        "ya has completado",
        "ya respondio",
        "ya respondio la encuesta",
    ]
    for marker in success_markers:
        if marker in normalized:
            return True, "completion_text"
    return None, None


async def _safe_text(locator: Locator) -> str:
    try:
        text = await locator.text_content()
    except Exception:
        text = None
    return text or ""


def _extract_course_id(href: str) -> Optional[str]:
    parsed = urlparse(href)
    params = parse_qs(parsed.query)
    course_ids = params.get("id")
    if not course_ids:
        return None
    return course_ids[0]


async def _extract_course_name(link: Locator) -> str:
    candidates = [".multiline", ".text-truncate", ".coursename"]
    for selector in candidates:
        node = link.locator(selector).first
        if await node.count() > 0:
            name = _clean_course_name(await node.inner_text())
            if name:
                return name
    return _clean_course_name(await link.inner_text())


def _normalize_text_optional(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def _clean_course_name(value: Optional[str]) -> str:
    text = _normalize_text_optional(value)
    if not text:
        return ""
    lowered = text.lower()
    marker = "nombre del curso"
    if lowered.startswith(marker):
        text = _normalize_text_optional(text[len(marker) :])
    if not text:
        return ""
    best = ""
    for match in re.finditer(r"\s+", text):
        prefix = text[: match.start()].strip()
        rest = text[match.end() :].strip()
        if len(prefix) < 30 or len(rest) < 8:
            continue
        if rest.startswith(prefix) or prefix.startswith(rest):
            if len(prefix) > len(best):
                best = prefix
    return best or text
