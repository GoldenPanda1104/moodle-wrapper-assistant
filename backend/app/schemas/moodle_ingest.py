"""Schema para el body del endpoint POST /api/v1/moodle/ingest."""

from pydantic import BaseModel, Field


class MoodleIngestBody(BaseModel):
    """Contrato del payload de ingest (docs/moodle-ingest-spec.md)."""

    user_id: int = Field(..., description="ID del usuario en la BD del backend")
    snapshot: dict = Field(
        ...,
        description="Estado completo: courses, modules, module_surveys, grade_items",
    )
    diffs: list[dict] = Field(
        default_factory=list,
        description="Lista de diferencias respecto al snapshot anterior",
    )
