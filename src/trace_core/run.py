from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trace_core.artifact_store import (
    DEFAULT_MAX_ARTIFACT_BYTES,
    DEFAULT_MAX_RUN_BYTES,
    TraceArtifactStore,
)
from trace_core.inspector import build_module_health, inspect_run
from trace_core.models import ArtifactEntry, TraceEvent
from trace_core.render import render_evidence
from trace_core.timeline import TraceTimeline, _now


class TraceRun:
    def __init__(
        self,
        run_dir: Path,
        *,
        strict: bool = False,
        max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
        max_run_bytes: int = DEFAULT_MAX_RUN_BYTES,
    ) -> None:
        self.run_dir = run_dir.resolve()
        self.strict = strict
        self.max_artifact_bytes = max_artifact_bytes
        self.max_run_bytes = max_run_bytes
        self.run_json = self.run_dir / "run.json"
        self.timeline = self.run_dir / "timeline.jsonl"
        self.artifacts_dir = self.run_dir / "artifacts"
        self.index_json = self.artifacts_dir / "index.json"

        self._timeline = TraceTimeline(self.timeline, lambda: self.run_id)
        self._artifact_store = TraceArtifactStore(
            self.run_dir,
            self.artifacts_dir,
            self.index_json,
            max_artifact_bytes=max_artifact_bytes,
            max_run_bytes=max_run_bytes,
            strict=strict,
            record_event=self._timeline.record_event,
            read_json=self._read_json,
            write_json=self._write_json,
        )

    @classmethod
    def start(
        cls,
        run_id: str,
        run_dir: Path,
        label: str | None = None,
        **kwargs: Any,
    ) -> TraceRun:
        trace = cls(run_dir, **kwargs)
        trace.run_dir.mkdir(parents=True, exist_ok=True)
        trace.artifacts_dir.mkdir(parents=True, exist_ok=True)
        trace._write_json(
            trace.run_json,
            {
                "version": 1,
                "run_id": run_id,
                "label": label,
                "status": "running",
                "started_at": _now(),
            },
        )
        trace._write_json(trace.index_json, {"version": 1, "artifacts": []})
        trace.record_event("trace", "run", "run_started", "ok", "trace run started")
        return trace

    @classmethod
    def open(cls, run_dir: Path, **kwargs: Any) -> TraceRun:
        trace = cls(run_dir, **kwargs)
        if not trace.run_json.exists():
            raise FileNotFoundError(f"trace run does not exist: {trace.run_dir}")
        return trace

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
        return self._timeline.record_event(module, phase, event_type, status, message, metadata, **fields)

    def copy_artifact(
        self,
        module: str,
        phase: str,
        source_path: Path,
        artifact_type: str = "other",
        role: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactEntry:
        return self._artifact_store._copy_artifact(module, phase, source_path, artifact_type, role, metadata)

    def record_log(
        self,
        module: str,
        phase: str,
        source_path: Path,
        name: str | None = None,
    ) -> ArtifactEntry:
        return self._artifact_store._copy_artifact(
            module,
            phase,
            source_path,
            "log",
            name or "log",
            None,
            event_type="log_recorded",
        )

    def finalize(self, status: str = "passed", message: str | None = None) -> dict[str, Any]:
        self.record_event("trace", "run", "run_finalized", status, message or "trace run finalized")
        run = self._read_json(self.run_json)
        run.update({"status": status, "completed_at": _now()})
        self._write_json(self.run_json, run)
        summary = self.inspect(status=status, message=message)
        self._write_json(self.run_dir / "summary.json", summary)
        self._write_json(self.run_dir / "module-health.json", summary["module_health"])
        (self.run_dir / "evidence.md").write_text(render_evidence(summary), encoding="utf-8")
        return summary

    def inspect(self, *, status: str | None = None, message: str | None = None) -> dict[str, Any]:
        return inspect_run(self.run_dir, status=status, message=message)

    @property
    def run_id(self) -> str:
        return str(self._read_json(self.run_json)["run_id"])

    def _read_json(self, path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a JSON object")
        return payload

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
