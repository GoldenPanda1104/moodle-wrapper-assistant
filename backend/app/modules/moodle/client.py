from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

from app.core.config import settings
from playwright.async_api import Browser, Locator, Page, Playwright, async_playwright


@dataclass
class MoodleSession:
    base_url: str
    username: str


class MoodleClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._session: Optional[MoodleSession] = None
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._logger = logging.getLogger("moodle")

    async def login(self) -> MoodleSession:
        if not self.base_url or not self.username or not self.password:
            raise ValueError("Missing Moodle credentials or base URL.")

        for attempt in range(3):
            try:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=True)
                self._page = await self._browser.new_page()

                await self._page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)

                # If we're already logged in, the dashboard body should be present.
                if await self._page.locator("body#page-my-index").count() == 0:
                    login_form = self._page.locator("input[name='username']")
                    if await login_form.count() > 0:
                        await self._page.fill("input[name='username']", self.username)
                        await self._page.fill("input[name='password']", self.password)
                await self._page.click("button[type='submit']")
                await self._page.wait_for_timeout(1500)

                # Basic session validation: dashboard body or user menu.
                await self._page.goto(f"{self.base_url}/my/", wait_until="domcontentloaded", timeout=30000)
                await self._page.wait_for_timeout(1500)
                has_dashboard = await self._page.locator("body#page-my-index").count() > 0
                has_user_menu = await self._page.locator("#user-menu-toggle").count() > 0
                has_logout = await self._page.locator("a[href*='logout']").count() > 0
                has_loggedin_body = await self._page.locator("body.loggedin").count() > 0
                has_userid = await self._page.locator("[data-userid]").count() > 0

                if not (has_dashboard or has_user_menu or has_logout or has_loggedin_body or has_userid):
                    # Final fallback: check home page for logged-in indicators.
                    await self._page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                    await self._page.wait_for_timeout(1000)
                    has_user_menu = await self._page.locator("#user-menu-toggle").count() > 0
                    has_logout = await self._page.locator("a[href*='logout']").count() > 0
                    has_loggedin_body = await self._page.locator("body.loggedin").count() > 0
                    has_userid = await self._page.locator("[data-userid]").count() > 0
                    if not (has_user_menu or has_logout or has_loggedin_body or has_userid):
                        raise RuntimeError("Login failed or dashboard not detected.")

                self._logger.info("[Moodle] Login OK")
                self._session = MoodleSession(base_url=self.base_url, username=self.username)
                return self._session
            except Exception as exc:
                self._logger.warning("[Moodle] Login attempt %s failed: %s", attempt + 1, exc)
                await self.close()
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    raise

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None
        self._page = None
        self._session = None

    async def get_courses(self) -> list[dict]:
        if self._session is None or self._page is None:
            raise RuntimeError("Login required before fetching courses.")

        for attempt in range(3):
            try:
                await self._page.goto(f"{self.base_url}/my/", wait_until="domcontentloaded", timeout=30000)
                course_cards = self._page.locator("[data-region='course-content'][data-course-id]")
                if await course_cards.count() == 0:
                    try:
                        await self._page.wait_for_selector(
                            "[data-region='course-content'][data-course-id]",
                            timeout=5000,
                        )
                        course_cards = self._page.locator("[data-region='course-content'][data-course-id]")
                    except Exception:
                        await self._page.goto(
                            f"{self.base_url}/my/courses.php",
                            wait_until="domcontentloaded",
                            timeout=30000,
                        )
                        course_cards = self._page.locator("[data-region='course-content'][data-course-id]")
                count = await course_cards.count()

                courses: dict[str, dict] = {}
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
                        courses[course_id] = {"id": course_id, "name": name, "link": href}

                if not courses:
                    # Fallback for list views without course cards.
                    links = self._page.locator("a[href*='course/view.php?id=']")
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
                        courses[course_id] = {"id": course_id, "name": name, "link": href}

                return list(courses.values())
            except Exception as exc:
                self._logger.warning("[Moodle] Get courses attempt %s failed: %s", attempt + 1, exc)
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    raise

    async def get_course_page(self, course_id: str) -> Page:
        if self._session is None or self._page is None:
            raise RuntimeError("Login required before fetching course page.")
        for attempt in range(3):
            try:
                await self._page.goto(
                    f"{self.base_url}/course/view.php?id={course_id}",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                return self._page
            except Exception as exc:
                self._logger.warning("[Moodle] Course %s load attempt %s failed: %s", course_id, attempt + 1, exc)
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    raise

    async def get_page(self, url: str) -> Page:
        if self._session is None or self._page is None:
            raise RuntimeError("Login required before fetching page.")
        target = url
        if url.startswith("/"):
            target = f"{self.base_url}{url}"
        elif not url.startswith("http"):
            target = f"{self.base_url}/{url.lstrip('/')}"
        for attempt in range(3):
            try:
                await self._page.goto(target, wait_until="domcontentloaded", timeout=30000)
                return self._page
            except Exception as exc:
                self._logger.warning("[Moodle] Page load attempt %s failed: %s", attempt + 1, exc)
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    raise


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


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def _clean_course_name(value: Optional[str]) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    lowered = text.lower()
    marker = "nombre del curso"
    if lowered.startswith(marker):
        text = _normalize_text(text[len(marker):])
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


def build_client_from_credentials(username: str, password: str) -> MoodleClient:
    return MoodleClient(
        base_url=settings.MOODLE_BASE_URL,
        username=username,
        password=password,
    )


def build_client_from_settings() -> MoodleClient:
    return build_client_from_credentials(
        username=settings.MOODLE_USERNAME,
        password=settings.MOODLE_PASSWORD,
    )
