from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from trace_core.models import TraceEvent


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class TraceTimeline:
    def __init__(self, timeline_path: Path, run_id_fn: Callable[[], str]) -> None:
        self.timeline = timeline_path
        self._run_id_fn = run_id_fn

    def record_event(
        self,
        module: str,
        phase: str,
        event_type: str,
        status: str,
        message: str,
        metadata: dict[str, Any] | None = None,
        **fields: Any,
    ) -> TraceEvent:
        event = TraceEvent(
            event_id=str(uuid.uuid4()),
            run_id=self._run_id_fn(),
            timestamp=_now(),
            type=event_type,
            module=module,
            phase=phase,
            status=status,
            message=message,
            metadata=metadata or {},
            **fields,
        )
        self.timeline.parent.mkdir(parents=True, exist_ok=True)
        with self.timeline.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return event
