from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


SNAPSHOT_DIR = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True)
class MoodleSnapshot:
    id: str
    taken_at: str
    data: dict[str, Any]


def _ensure_snapshot_dir() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def _snapshot_path(user_id: int) -> Path:
    return SNAPSHOT_DIR / f"snapshot-{user_id}.json"


def save_snapshot(user_id: int, data: dict) -> MoodleSnapshot:
    _ensure_snapshot_dir()
    snapshot = MoodleSnapshot(
        id=str(int(datetime.now(tz=timezone.utc).timestamp())),
        taken_at=datetime.now(tz=timezone.utc).isoformat(),
        data=data,
    )
    _snapshot_path(user_id).write_text(
        json.dumps(snapshot.__dict__, ensure_ascii=True), encoding="ascii"
    )
    return snapshot


def get_last_snapshot(user_id: int) -> Optional[MoodleSnapshot]:
    path = _snapshot_path(user_id)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="ascii"))
    return MoodleSnapshot(**payload)
