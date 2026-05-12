"""Schema validation for trace run directories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trace_core.protocol import REQUIRED_RUN_FILES, read_events, read_json


def validate_run(
    run_dir: Path,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """Validate a trace run directory against the expected schema.

    Returns a validation report with missing files, schema errors, and
    artifact integrity checks.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Check required files exist
    missing = [rel for rel in REQUIRED_RUN_FILES if not (run_dir / rel).exists()]
    if missing:
        errors.append(f"missing required files: {', '.join(missing)}")

    # Validate run.json
    run_json = run_dir / "run.json"
    if run_json.exists():
        try:
            run_data = read_json(run_json)
            validate_run_manifest(run_data, errors, warnings)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"run.json parse error: {exc}")

    # Validate timeline
    timeline = run_dir / "timeline.jsonl"
    if timeline.exists():
        try:
            events = read_events(timeline)
            for event in events:
                validate_timeline_event(event, errors, warnings)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"timeline.jsonl error: {exc}")
    elif run_json.exists():
        errors.append("timeline.jsonl missing but run.json exists")

    # Validate artifact index
    index_path = run_dir / "artifacts" / "index.json"
    if index_path.exists():
        try:
            index = read_json(index_path)
            validate_artifact_index(index, errors, warnings)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"artifacts/index.json error: {exc}")
    elif run_json.exists():
        errors.append("artifacts/index.json missing but run.json exists")

    return {
        "valid": len(errors) == 0,
        "run_dir": str(run_dir),
        "errors": errors,
        "warnings": warnings,
        "strict": strict,
    }


def validate_run_manifest(data: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Validate run.json contents."""
    required = {"version", "run_id", "status", "started_at"}
    missing = required - set(data.keys())
    if missing:
        errors.append(f"run.json missing fields: {sorted(missing)}")

    valid_statuses = {"running", "passed", "failed", "error", "cancelled", "suspended"}
    if data.get("status") not in valid_statuses:
        warnings.append(f"run.json unknown status: {data.get('status')}")


def validate_timeline_event(event: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Validate a single timeline event."""
    required = {"event_id", "run_id", "timestamp", "type", "module", "phase", "status", "message"}
    missing = required - set(event.keys())
    if missing:
        errors.append(f"timeline event missing fields: {sorted(missing)}")


def validate_artifact_index(index: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Validate artifacts/index.json."""
    if "version" not in index:
        errors.append("artifact index missing version")
    artifacts = index.get("artifacts", [])
    if not isinstance(artifacts, list):
        errors.append("artifact index artifacts must be a list")
        return
    for i, entry in enumerate(artifacts):
        required = {"artifact_id", "module", "phase", "artifact_type", "source_path", "trace_path", "size_bytes"}
        missing = required - set(entry.keys()) if isinstance(entry, dict) else required
        if missing:
            errors.append(f"artifact index entry {i} missing fields: {sorted(missing)}")
