from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_EVENT_FIELDS = {
    "event_id",
    "run_id",
    "timestamp",
    "type",
    "module",
    "phase",
    "status",
    "message",
}

REQUIRED_RUN_FILES = ["run.json", "timeline.jsonl", "artifacts/index.json"]


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        missing = REQUIRED_EVENT_FIELDS.difference(payload)
        if missing:
            raise ValueError(f"timeline line {line_no} missing fields: {sorted(missing)}")
        events.append(payload)
    return events


def inspect_protocol(run_dir: Path) -> dict[str, Any]:
    missing = [rel for rel in REQUIRED_RUN_FILES if not (run_dir / rel).exists()]
    run = read_json(run_dir / "run.json") if not missing else {}
    events = read_events(run_dir / "timeline.jsonl") if not missing else []
    index_path = run_dir / "artifacts" / "index.json"
    index = read_json(index_path) if index_path.exists() else {"artifacts": []}
    artifacts = index.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise ValueError("artifacts/index.json artifacts must be a list")
    return {"missing": missing, "run": run, "events": events, "artifacts": artifacts}
