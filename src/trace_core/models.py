from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TraceEvent:
    event_id: str
    run_id: str
    timestamp: str
    type: str
    module: str
    phase: str
    status: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_path: str | None = None
    trace_path: str | None = None
    sha256: str | None = None
    size_bytes: int | None = None
    artifact_id: str | None = None
    artifact_type: str | None = None
    role: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "type": self.type,
            "module": self.module,
            "phase": self.phase,
            "status": self.status,
            "message": self.message,
            "metadata": self.metadata,
        }
        optional = {
            "source_path": self.source_path,
            "trace_path": self.trace_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "role": self.role,
        }
        payload.update({key: value for key, value in optional.items() if value is not None})
        return payload


@dataclass(frozen=True)
class ArtifactEntry:
    artifact_id: str
    module: str
    phase: str
    artifact_type: str
    source_path: str
    trace_path: str
    size_bytes: int
    sha256: str | None
    role: str | None = None
    files: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "artifact_id": self.artifact_id,
            "module": self.module,
            "phase": self.phase,
            "artifact_type": self.artifact_type,
            "source_path": self.source_path,
            "trace_path": self.trace_path,
            "size_bytes": self.size_bytes,
            "files": self.files,
            "metadata": self.metadata,
        }
        if self.sha256 is not None:
            payload["sha256"] = self.sha256
        if self.role is not None:
            payload["role"] = self.role
        return payload
