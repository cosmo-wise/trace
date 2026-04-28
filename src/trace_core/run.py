from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from trace_core.artifacts import copy_payload, path_size, sanitize_slug
from trace_core.models import ArtifactEntry, TraceEvent
from trace_core.protocol import inspect_protocol
from trace_core.render import render_evidence

DEFAULT_MAX_ARTIFACT_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_RUN_BYTES = 250 * 1024 * 1024


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
        event = TraceEvent(
            event_id=str(uuid.uuid4()),
            run_id=self.run_id,
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

    def copy_artifact(
        self,
        module: str,
        phase: str,
        source_path: Path,
        artifact_type: str = "other",
        role: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactEntry:
        return self._copy_artifact(module, phase, source_path, artifact_type, role, metadata)

    def record_log(
        self,
        module: str,
        phase: str,
        source_path: Path,
        name: str | None = None,
    ) -> ArtifactEntry:
        return self._copy_artifact(
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
        (self.run_dir / "evidence.md").write_text(render_evidence(summary), encoding="utf-8")
        return summary

    def inspect(self, *, status: str | None = None, message: str | None = None) -> dict[str, Any]:
        protocol = inspect_protocol(self.run_dir)
        run = protocol["run"]
        artifacts = protocol["artifacts"]
        events = protocol["events"]
        warnings = [event for event in events if event.get("status") == "warning"]
        errors = [
            event
            for event in events
            if event.get("status") not in {"ok", "warning", "passed", "running"}
        ]
        return {
            "ok": not protocol["missing"],
            "missing": protocol["missing"],
            "run_id": run.get("run_id", ""),
            "status": status or run.get("status", "unknown"),
            "message": message,
            "event_count": len(events),
            "warning_count": len(warnings),
            "error_count": len(errors),
            "warnings": warnings[:20],
            "errors": errors[:20],
            "artifact_count": len(artifacts),
            "artifact_bytes": sum(int(item.get("size_bytes", 0)) for item in artifacts),
            "artifacts": artifacts,
        }

    @property
    def run_id(self) -> str:
        return str(self._read_json(self.run_json)["run_id"])

    def _copy_artifact(
        self,
        module: str,
        phase: str,
        source_path: Path,
        artifact_type: str,
        role: str | None,
        metadata: dict[str, Any] | None,
        *,
        event_type: str = "artifact_copied",
    ) -> ArtifactEntry:
        source = source_path.resolve()
        if not source.exists():
            raise FileNotFoundError(f"artifact source does not exist: {source}")
        size = path_size(source)
        if size > self.max_artifact_bytes or self._current_run_bytes() + size > self.max_run_bytes:
            message = f"artifact skipped by budget: {source}"
            if self.strict:
                raise ValueError(message)
            self.record_event(module, phase, "artifact_skipped", "warning", message)
            raise RuntimeError(message)
        artifact_id = self._next_artifact_id(module, phase, source.name)
        trace_path = self.artifacts_dir / artifact_id / "payload"
        sha256, files = copy_payload(source, trace_path)
        entry = ArtifactEntry(
            artifact_id=artifact_id,
            module=module,
            phase=phase,
            artifact_type=artifact_type,
            source_path=str(source),
            trace_path=str(trace_path.relative_to(self.run_dir)),
            size_bytes=size,
            sha256=sha256,
            role=role,
            files=files,
            metadata=metadata or {},
        )
        self._append_artifact(entry)
        self.record_event(
            module,
            phase,
            event_type,
            "ok",
            f"copied {artifact_type} artifact",
            source_path=str(source),
            trace_path=entry.trace_path,
            sha256=sha256,
            size_bytes=size,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            role=role,
        )
        return entry

    def _next_artifact_id(self, module: str, phase: str, name: str) -> str:
        base = "-".join(sanitize_slug(part) for part in [module, phase, name])
        return f"{base}-{uuid.uuid4().hex[:8]}"

    def _append_artifact(self, entry: ArtifactEntry) -> None:
        index = self._read_json(self.index_json)
        artifacts = index.setdefault("artifacts", [])
        if not isinstance(artifacts, list):
            raise ValueError("artifacts/index.json artifacts must be a list")
        artifacts.append(entry.to_dict())
        self._write_json(self.index_json, index)

    def _current_run_bytes(self) -> int:
        if not self.artifacts_dir.exists():
            return 0
        return sum(path.stat().st_size for path in self.artifacts_dir.rglob("*") if path.is_file())

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


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
