from __future__ import annotations

import asyncio
import logging
import unicodedata
from dataclasses import asdict

from app.modules.moodle.client import MoodleClient
from app.modules.moodle.models import MoodleCourse, MoodleModule, MoodleModuleSurvey
from playwright.async_api import Locator, Page


async def scrape(client: MoodleClient) -> dict:
    logger = logging.getLogger("moodle")
    courses: list[MoodleCourse] = []
    modules: list[MoodleModule] = []
    module_surveys: list[MoodleModuleSurvey] = []

    for attempt in range(3):
        try:
            course_rows = await client.get_courses()
            logger.info("[Moodle] Cursos detectados: %s", len(course_rows))
            for course in course_rows:
                courses.append(MoodleCourse(id=course["id"], name=course["name"]))
                page = await client.get_course_page(course["id"])
                modules.extend(await _extract_modules(page, course["id"]))

            modules, module_surveys = await _enrich_modules_with_surveys(client, modules)

            logger.info("[Moodle] Modulos detectados: %s", len(modules))
            logger.info("[Moodle] Encuestas detectadas: %s", len(module_surveys))
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
    }
    return data


async def _extract_modules(page: Page, course_id: str) -> list[MoodleModule]:
    modules = await _extract_modules_from_courseindex(page, course_id)
    if modules:
        return modules
    return await _extract_modules_from_activity_list(page, course_id)


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

        surveys.append(
            MoodleModuleSurvey(
                id=activity_id,
                module_id=module_id,
                course_id=module.course_id,
                title=title or "Enviar encuesta",
                url=href or None,
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
