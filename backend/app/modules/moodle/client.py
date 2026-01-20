from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.core.config import settings
from playwright.async_api import Browser, Page, Playwright, async_playwright


class MoodleClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._logger = logging.getLogger("moodle")

    async def open(self) -> Page:
        if self._page:
            return self._page
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._page = await self._browser.new_page()
        return self._page

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Client not initialized. Call open() first.")
        return self._page

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None
        self._page = None

    async def get_page(self, url: str) -> Page:
        if self._page is None:
            raise RuntimeError("Client not initialized. Call open() first.")
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
