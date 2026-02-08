"""
Helpers para obtener y fusionar datos Moodle (cursos, módulos, encuestas).
Sin dependencias de BD; reutilizado por el pipeline del backend y por el scraper.
"""
from __future__ import annotations

from app.modules.moodle.models import MoodleModule


async def _fetch_modules(adapter, courses: list) -> list[MoodleModule]:
    """Obtiene todos los módulos de la lista de cursos vía el adapter."""
    modules: list[MoodleModule] = []
    for course in courses:
        modules.extend(await adapter.get_modules(course.id))
    return modules


async def _fetch_modules_by_ids(adapter, course_ids: list[str]) -> list[MoodleModule]:
    """Obtiene módulos por lista de course_id."""
    modules: list[MoodleModule] = []
    for course_id in course_ids:
        modules.extend(await adapter.get_modules(course_id))
    return modules


def _merge_survey_flags(
    modules: list[MoodleModule], surveys: list
) -> list[MoodleModule]:
    """Marca has_survey en cada módulo según las encuestas devueltas por el adapter."""
    survey_map = {(s.course_id, s.module_id) for s in surveys}
    updated: list[MoodleModule] = []
    for module in modules:
        has_survey = (module.course_id, module.id) in survey_map
        updated.append(
            MoodleModule(
                id=module.id,
                course_id=module.course_id,
                title=module.title,
                visible=module.visible,
                blocked=module.blocked,
                block_reason=module.block_reason,
                has_survey=has_survey,
                url=module.url,
            )
        )
    return updated
