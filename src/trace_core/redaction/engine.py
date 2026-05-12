"""Redaction engine that applies rules to trace run directories."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from trace_core.redaction.reports import RedactionReport
from trace_core.redaction.rules import RedactionRule, builtin_rules


class RedactionEngine:
    """Apply redaction rules to a trace run directory."""

    def __init__(self, rules: list[RedactionRule] | None = None) -> None:
        self._rules = rules or builtin_rules()

    def add_rule(self, rule: RedactionRule) -> None:
        """Add a custom redaction rule."""
        self._rules.append(rule)

    @property
    def rules(self) -> list[RedactionRule]:
        return list(self._rules)

    def redact_run(
        self,
        run_dir: Path,
        output_dir: Path | None = None,
    ) -> RedactionReport:
        """Redact all text files in a trace run directory.

        Returns a RedactionReport with details of what was redacted.
        """
        if output_dir is None:
            output_dir = run_dir.parent / f"{run_dir.name}-redacted"

        if output_dir.exists():
            shutil.rmtree(output_dir)
        shutil.copytree(run_dir, output_dir)

        text_extensions = {".json", ".jsonl", ".md", ".txt", ".yaml", ".yml", ".log", ".env"}
        redacted_count = 0
        redacted_files: list[dict[str, Any]] = []

        for file_path in output_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix not in text_extensions:
                continue
            original = file_path.read_text(encoding="utf-8")
            content = original
            file_applied_rules: list[str] = []
            for rule in self._rules:
                new_content = rule.apply(content, str(file_path))
                if new_content != content:
                    file_applied_rules.append(rule.name)
                    redacted_count += 1
                content = new_content
            if content != original:
                file_path.write_text(content, encoding="utf-8")
                redacted_files.append({
                    "path": str(file_path.relative_to(output_dir)),
                    "rules_applied": file_applied_rules,
                })

        return RedactionReport(
            source_dir=str(run_dir),
            output_dir=str(output_dir),
            total_rules=len(self._rules),
            redacted_files=redacted_files,
            redacted_count=redacted_count,
        )

    def redact_text(self, text: str, source_path: str | None = None) -> str:
        """Apply all rules to a text string."""
        content = text
        for rule in self._rules:
            content = rule.apply(content, source_path)
        return content
