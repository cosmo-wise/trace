"""Export a compass-friendly digest from a trace run."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from trace_core.inspector import inspect_run
from trace_core.protocol import read_json


def export_portal_digest(run_dir: Path) -> dict[str, Any]:
    """Produce a lightweight digest for compass ingestion.

    The digest is intentionally minimal — compass should not need to
    understand the full trace protocol.
    """
    run_data = read_json(run_dir / "run.json") if (run_dir / "run.json").exists() else {}
    summary = read_json(run_dir / "summary.json") if (run_dir / "summary.json").exists() else {}
    inspect = inspect_run(run_dir)

    return {
        "run_id": run_data.get("run_id", ""),
        "status": run_data.get("status", "unknown"),
        "label": run_data.get("label"),
        "started_at": run_data.get("started_at"),
        "completed_at": run_data.get("completed_at"),
        "module_count": len(inspect.get("modules", {})),
        "artifact_count": inspect.get("summary", {}).get("total_artifacts", 0),
        "event_count": inspect.get("summary", {}).get("total_events", 0),
        "module_health": {
            mod: info.get("status", "unknown")
            for mod, info in inspect.get("module_health", {}).items()
        },
        "overall_health": summary.get("module_health", {}).get("overall", "unknown"),
    }
