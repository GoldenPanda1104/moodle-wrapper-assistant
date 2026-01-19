from __future__ import annotations

import logging
import unicodedata
from typing import Optional

from playwright.async_api import Page

from app.modules.moodle.client import MoodleClient, build_client_from_settings


async def complete_survey(completion_url: str, client: Optional[MoodleClient] = None) -> dict:
    logger = logging.getLogger("moodle")
    owns_client = client is None
    client = client or build_client_from_settings()
    if owns_client:
        await client.login()
    try:
        page = await client.get_page(completion_url)
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
        logger.info("[Moodle] Survey completion result: %s", result)
        return result
    finally:
        if owns_client:
            await client.close()


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
    normalized_completion = _normalize(completion_text)
    if "por hacer" in normalized_completion:
        return False, "completion_pending"
    if "completado" in normalized_completion or "completo" in normalized_completion:
        return True, "completion_badge"

    body_text = await _safe_text(page.locator("body").first)
    normalized = _normalize(body_text)
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


async def _safe_text(locator) -> str:
    try:
        text = await locator.text_content()
    except Exception:
        text = None
    return text or ""


def _normalize(value: str) -> str:
    lowered = " ".join(value.split()).strip().lower()
    normalized = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))
