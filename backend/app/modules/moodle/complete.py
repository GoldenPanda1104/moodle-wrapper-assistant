from __future__ import annotations

from app.modules.moodle.adapters.base import MoodleAdapter


async def complete_survey(completion_url: str, adapter: MoodleAdapter) -> dict:
    return await adapter.complete_survey(completion_url)
