"""Tests for trace run validation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from trace_core.validate import validate_run


def test_validate_invalid_directory() -> None:
    """validate_run on a non-existent directory should report errors."""
    result = validate_run(Path("/nonexistent"))
    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_validate_valid_run() -> None:
    """Create a minimal valid run directory and validate it."""
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp)
        run_json = {"version": 1, "run_id": "test", "status": "passed", "started_at": "2025-01-01T00:00:00Z"}
        (run_dir / "run.json").write_text(json.dumps(run_json), encoding="utf-8")
        (run_dir / "timeline.jsonl").write_text(
            json.dumps({"event_id": "e1", "run_id": "test", "timestamp": "2025-01-01T00:00:00Z",
                         "type": "test", "module": "test", "phase": "test", "status": "ok", "message": "test"}) + "\n",
            encoding="utf-8",
        )
        (run_dir / "artifacts").mkdir()
        (run_dir / "artifacts" / "index.json").write_text(
            json.dumps({"version": 1, "artifacts": []}), encoding="utf-8",
        )
        result = validate_run(run_dir)
        assert result["valid"] is True
