"""Redaction report model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RedactionReport:
    """Report detailing what was redacted during a redaction operation."""

    source_dir: str
    output_dir: str
    total_rules: int
    redacted_files: list[dict[str, Any]] = field(default_factory=list)
    redacted_count: int = 0

    @property
    def total_redactions(self) -> int:
        """Total count of individual redaction applications."""
        return self.redacted_count

    @property
    def affected_files(self) -> list[str]:
        """List of file paths that were redacted."""
        return [f["path"] for f in self.redacted_files]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_dir": self.source_dir,
            "output_dir": self.output_dir,
            "total_rules": self.total_rules,
            "redacted_files": self.redacted_files,
            "redacted_count": self.redacted_count,
            "affected_file_count": len(self.redacted_files),
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
