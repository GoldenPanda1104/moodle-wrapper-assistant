from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class PipelineEvent:
    event: str
    message: str
    level: str = "info"
    ts: str = ""
    url: str | None = None

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "event": self.event,
            "message": self.message,
            "level": self.level,
            "ts": self.ts or datetime.now(timezone.utc).isoformat(),
        }
        if self.url:
            payload["url"] = self.url
        return payload


class PipelineStreamManager:
    def __init__(self, max_history: int = 200) -> None:
        self._runs: Dict[str, List[asyncio.Queue[Dict[str, Any]]]] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._completed: set[str] = set()
        self._lock = asyncio.Lock()
        self._max_history = max_history

    async def create_run(self) -> str:
        run_id = uuid.uuid4().hex
        async with self._lock:
            self._runs[run_id] = []
            self._history[run_id] = []
        return run_id

    async def subscribe(self, run_id: str) -> asyncio.Queue[Dict[str, Any]]:
        async with self._lock:
            if run_id not in self._history:
                raise KeyError(run_id)
            queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
            self._runs[run_id].append(queue)
            return queue

    async def unsubscribe(self, run_id: str, queue: asyncio.Queue[Dict[str, Any]]) -> None:
        async with self._lock:
            queues = self._runs.get(run_id)
            if not queues:
                return
            if queue in queues:
                queues.remove(queue)

    async def history(self, run_id: str) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self._history.get(run_id, []))

    async def publish(self, run_id: str, payload: Dict[str, Any]) -> None:
        async with self._lock:
            if run_id not in self._history:
                return
            history = self._history[run_id]
            history.append(payload)
            if len(history) > self._max_history:
                del history[:-self._max_history]
            queues = list(self._runs.get(run_id, []))
        for queue in queues:
            await queue.put(payload)

    async def mark_done(self, run_id: str, payload: Dict[str, Any]) -> None:
        async with self._lock:
            self._completed.add(run_id)
        await self.publish(run_id, payload)

    async def is_completed(self, run_id: str) -> bool:
        async with self._lock:
            return run_id in self._completed
