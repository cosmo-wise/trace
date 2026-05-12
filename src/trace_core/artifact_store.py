from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from trace_core.artifacts import copy_payload, path_size, sanitize_slug
from trace_core.models import ArtifactEntry, TraceEvent

DEFAULT_MAX_ARTIFACT_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_RUN_BYTES = 250 * 1024 * 1024


class TraceArtifactStore:
    def __init__(
        self,
        run_dir: Path,
        artifacts_dir: Path,
        index_json: Path,
        *,
        max_artifact_bytes: int,
        max_run_bytes: int,
        strict: bool,
        record_event: Callable[..., TraceEvent],
        read_json: Callable[..., dict[str, Any]],
        write_json: Callable[..., None],
    ) -> None:
        self.run_dir = run_dir
        self.artifacts_dir = artifacts_dir
        self.index_json = index_json
        self.max_artifact_bytes = max_artifact_bytes
        self.max_run_bytes = max_run_bytes
        self.strict = strict
        self._record_event = record_event
        self._read_json = read_json
        self._write_json = write_json

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
            self._record_event(module, phase, "artifact_skipped", "warning", message)
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
        self._record_event(
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
