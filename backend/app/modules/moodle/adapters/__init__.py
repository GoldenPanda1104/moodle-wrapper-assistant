from __future__ import annotations

from app.modules.moodle.adapters.base import MoodleAdapter
from app.modules.moodle.adapters.uip import UIPMoodleAdapter


def get_adapter(user) -> MoodleAdapter:
    username = ""
    password = ""
    base_url = None

    if isinstance(user, dict):
        username = user.get("username", "") or ""
        password = user.get("password", "") or ""
        base_url = user.get("base_url")
    else:
        username = getattr(user, "username", "") or ""
        password = getattr(user, "password", "") or ""
        base_url = getattr(user, "base_url", None)

    return UIPMoodleAdapter(username=username, password=password, base_url=base_url)


__all__ = ["MoodleAdapter", "UIPMoodleAdapter", "get_adapter"]
