"""Tests for trace redaction engine."""

from __future__ import annotations

import tempfile
from pathlib import Path

from trace_core.redaction.engine import RedactionEngine
from trace_core.redaction.rules import RedactionRule


def test_redact_credentials() -> None:
    engine = RedactionEngine()
    text = "API_KEY=sk-1234567890abcdefghij and token=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    result = engine.redact_text(text)
    assert "***" in result
    assert "sk-1234567890abcdefghij" not in result


def test_redact_email() -> None:
    engine = RedactionEngine()
    text = "Contact admin@example.com for access"
    result = engine.redact_text(text)
    assert "***@***" in result or "***" in result
    assert "admin@example.com" not in result


def test_redact_aws_key() -> None:
    engine = RedactionEngine()
    text = "AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE"
    result = engine.redact_text(text)
    assert "AKIAIOSFODNN7EXAMPLE" not in result


def test_redact_custom_rule() -> None:
    engine = RedactionEngine([])
    engine.add_rule(RedactionRule(name="custom", pattern=r"CUSTOM_SECRET", replacement="***"))
    result = engine.redact_text("My CUSTOM_SECRET is here")
    assert "***" in result
    assert "CUSTOM_SECRET" not in result


def test_redact_run_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        run_dir.mkdir()
        (run_dir / "data.json").write_text('{"api_key": "sk-1234"}', encoding="utf-8")
        (run_dir / "README.md").write_text("Email: user@test.com", encoding="utf-8")

        engine = RedactionEngine()
        report = engine.redact_run(run_dir)

        assert report.redacted_count > 0
        assert len(report.affected_files) > 0
