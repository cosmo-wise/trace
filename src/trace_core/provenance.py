"""Provenance metadata helpers for trace evidence.

Provenance records the origin of a trace run or artifact:
which module created it, during what phase, and from what source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Provenance:
    """Provenance metadata for a trace run or artifact."""

    module: str
    phase: str
    source: str = ""
    version: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "module": self.module,
            "phase": self.phase,
        }
        if self.source:
            result["source"] = self.source
        if self.version:
            result["version"] = self.version
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Provenance:
        return cls(
            module=data.get("module", ""),
            phase=data.get("phase", ""),
            source=data.get("source", ""),
            version=data.get("version", ""),
            metadata=data.get("metadata", {}),
        )
