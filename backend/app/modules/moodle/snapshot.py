from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "snapshot.json"


@dataclass(frozen=True)
class MoodleSnapshot:
    id: str
    taken_at: str
    data: dict[str, Any]


def _ensure_snapshot_dir() -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)


def save_snapshot(data: dict) -> MoodleSnapshot:
    _ensure_snapshot_dir()
    snapshot = MoodleSnapshot(
        id=str(int(datetime.now(tz=timezone.utc).timestamp())),
        taken_at=datetime.now(tz=timezone.utc).isoformat(),
        data=data,
    )
    SNAPSHOT_PATH.write_text(json.dumps(snapshot.__dict__, ensure_ascii=True), encoding="ascii")
    return snapshot


def get_last_snapshot() -> Optional[MoodleSnapshot]:
    if not SNAPSHOT_PATH.exists():
        return None
    payload = json.loads(SNAPSHOT_PATH.read_text(encoding="ascii"))
    return MoodleSnapshot(**payload)
