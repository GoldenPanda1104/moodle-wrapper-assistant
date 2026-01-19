from __future__ import annotations

from typing import Any, Optional


def _index_by_id(items: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in items}


def diff_snapshots(old: Optional[dict], new: dict) -> list[dict[str, Any]]:
    diffs: list[dict[str, Any]] = []
    old_data = old or {"courses": [], "modules": []}

    old_courses = _index_by_id(old_data.get("courses", []))
    new_courses = _index_by_id(new.get("courses", []))

    old_modules = _index_by_id(old_data.get("modules", []))
    new_modules = _index_by_id(new.get("modules", []))

    for course_id, course in new_courses.items():
        if course_id not in old_courses:
            diffs.append(
                {
                    "type": "course_detected",
                    "course_id": course_id,
                    "course": course["name"],
                }
            )

    for module_id, module in new_modules.items():
        course_name = new_courses.get(module["course_id"], {}).get("name", "Unknown")
        if module_id not in old_modules:
            diffs.append(
                {
                    "type": "module_detected",
                    "course_id": module["course_id"],
                    "course": course_name,
                    "module_id": module_id,
                    "module": module["title"],
                    "module_url": module.get("url"),
                }
            )
            if module.get("has_survey"):
                diffs.append(
                    {
                        "type": "survey_detected",
                        "course_id": module["course_id"],
                        "course": course_name,
                        "module_id": module_id,
                        "module": module["title"],
                        "module_url": module.get("url"),
                    }
                )
            if module.get("blocked"):
                diffs.append(
                    {
                        "type": "blocked_detected",
                        "course_id": module["course_id"],
                        "course": course_name,
                        "module_id": module_id,
                        "module": module["title"],
                        "reason": module.get("block_reason"),
                        "module_url": module.get("url"),
                    }
                )
            continue

        old_module = old_modules[module_id]
        if not old_module.get("has_survey") and module.get("has_survey"):
            diffs.append(
                {
                    "type": "survey_detected",
                    "course_id": module["course_id"],
                    "course": course_name,
                    "module_id": module_id,
                    "module": module["title"],
                    "module_url": module.get("url"),
                }
            )

        if old_module.get("blocked") != module.get("blocked"):
            change_type = "blocked_detected" if module.get("blocked") else "module_unlocked"
            diffs.append(
                {
                    "type": change_type,
                    "course_id": module["course_id"],
                    "course": course_name,
                    "module_id": module_id,
                    "module": module["title"],
                    "reason": module.get("block_reason"),
                    "module_url": module.get("url"),
                }
            )

    return diffs
