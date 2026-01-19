from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from dataclasses import asdict
from datetime import datetime, timezone

from app.modules.moodle.client import MoodleClient
from app.modules.moodle.models import (
    MoodleCourse,
    MoodleGradeItem,
    MoodleModule,
    MoodleModuleSurvey,
)
from playwright.async_api import Locator, Page


async def scrape(client: MoodleClient) -> dict:
    logger = logging.getLogger("moodle")
    courses: list[MoodleCourse] = []
    modules: list[MoodleModule] = []
    module_surveys: list[MoodleModuleSurvey] = []
    grade_items: list[MoodleGradeItem] = []

    for attempt in range(3):
        try:
            course_rows = await client.get_courses()
            logger.info("[Moodle] Cursos detectados: %s", len(course_rows))
            for course in course_rows:
                courses.append(MoodleCourse(id=course["id"], name=course["name"]))
                page = await client.get_course_page(course["id"])
                modules.extend(await _extract_modules(page, course["id"]))
                grade_items.extend(await _extract_grade_items(client, course["id"]))

            modules, module_surveys = await _enrich_modules_with_surveys(client, modules)

            logger.info("[Moodle] Modulos detectados: %s", len(modules))
            logger.info("[Moodle] Encuestas detectadas: %s", len(module_surveys))
            logger.info("[Moodle] Calificaciones detectadas: %s", len(grade_items))
            break
        except Exception as exc:
            logger.warning("[Moodle] Scrape attempt %s failed: %s", attempt + 1, exc)
            if attempt < 2:
                await asyncio.sleep(2)
            else:
                raise

    data = {
        "courses": [asdict(course) for course in courses],
        "modules": [asdict(module) for module in modules],
        "module_surveys": [asdict(survey) for survey in module_surveys],
        "grade_items": [asdict(item) for item in grade_items],
    }
    return data


async def scrape_grade_items(
    client: MoodleClient,
    course_ids: list[str],
    item_type_filter: set[str] | None = None,
) -> list[MoodleGradeItem]:
    items: list[MoodleGradeItem] = []
    for course_id in course_ids:
        items.extend(await _extract_grade_items(client, course_id, item_type_filter=item_type_filter))
    return items


async def scrape_modules(client: MoodleClient, course_ids: list[str]) -> list[MoodleModule]:
    modules: list[MoodleModule] = []
    for course_id in course_ids:
        page = await client.get_course_page(course_id)
        modules.extend(await _extract_modules(page, course_id))
    return modules


async def enrich_modules_with_surveys(
    client: MoodleClient, modules: list[MoodleModule]
) -> tuple[list[MoodleModule], list[MoodleModuleSurvey]]:
    return await _enrich_modules_with_surveys(client, modules)


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
    page = await client.get_page(f"{client.base_url}/grade/report/user/index.php?id={course_id}")
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
        grade_display = _normalize_text(await _text_or_empty(row, "td.column-grade div.d-flex > div:first-child"))
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

        #log modules
        logging.getLogger("moodle").debug("[Moodle] Course %s module detected: %s", course_id, asdict(modules[-1]))

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
        page = await client.get_page(module.url)
        surveys = await _extract_module_surveys(page, module)
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


async def _extract_activity_id(activity: Locator, fallback_idx: int) -> str:
    href = await activity.locator("a[href*='mod/']").first.get_attribute("href")
    if href and "id=" in href:
        return href.split("id=")[-1].split("&")[0]
    return f"activity-{fallback_idx + 1}"


async def _has_survey(activity) -> bool:
    class_attr = (await activity.get_attribute("class")) or ""
    if "modtype_feedback" not in class_attr and "modtype_survey" not in class_attr:
        return False
    title = (await _text_or_empty(activity, ".instancename")) or (
        await _text_or_empty(activity, ".activityname")
    )
    return _matches_survey_name(title)


async def _extract_module_surveys(
    page: Page, module: MoodleModule
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
                "https://moodle.uip.edu.pa/mod/feedback/complete.php"
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
        try:
            await page.wait_for_selector(".activity-dates", timeout=3000)
        except Exception:
            pass
        date_nodes = page.locator(".activity-dates div")
        date_count = await date_nodes.count()
        for idx in range(date_count):
            text = _normalize_text((await date_nodes.nth(idx).text_content()) or "")
            if not text:
                continue
            lowered = _normalize_for_compare(text)
            if lowered.startswith("apertura"):
                details["available_at"] = _format_datetime(_parse_spanish_datetime(_split_after_label(text)))
            elif lowered.startswith("cierre"):
                details["due_at"] = _format_datetime(_parse_spanish_datetime(_split_after_label(text)))

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
        try:
            await page.wait_for_selector(".activity-dates", timeout=3000)
        except Exception:
            pass
        date_nodes = page.locator(".activity-dates div")
        date_count = await date_nodes.count()
        for idx in range(date_count):
            text = _normalize_text((await date_nodes.nth(idx).text_content()) or "")
            if not text:
                continue
            lowered = _normalize_for_compare(text)
            if lowered.startswith("abrio"):
                details["available_at"] = _format_datetime(_parse_spanish_datetime(_split_after_label(text)))
            elif lowered.startswith("cierra") or lowered.startswith("cerro"):
                details["due_at"] = _format_datetime(_parse_spanish_datetime(_split_after_label(text)))

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
    match = re.search(
        r"(\\d{1,2}) de ([a-zA-Záéíóúñ]+) de (\\d{4}), (\\d{2}):(\\d{2})",
        cleaned,
    )
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
    match = re.search(r"(\\d+)", value)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _parse_duration_minutes(value: str) -> int | None:
    if ":" in value:
        value = value.split(":", 1)[1].strip()
    match = re.search(r"(\\d+)", value)
    if not match:
        return None
    amount = int(match.group(1))
    normalized = _normalize_for_compare(value)
    if "hora" in normalized:
        return amount * 60
    return amount
