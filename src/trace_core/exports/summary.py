"""Export a structured summary-1.0.json for compass/stirrup consumption."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from trace_core.inspector import inspect_run
from trace_core.protocol import read_json


def export_summary(run_dir: Path, *, json_output: bool = False) -> dict[str, Any]:
    """Produce a summary-1.0.json from a trace run directory."""
    run_data = read_json(run_dir / "run.json") if (run_dir / "run.json").exists() else {}
    inspect = inspect_run(run_dir)

    summary: dict[str, Any] = {
        "version": 1,
        "run_id": run_data.get("run_id", ""),
        "status": run_data.get("status", "unknown"),
        "label": run_data.get("label"),
        "started_at": run_data.get("started_at"),
        "completed_at": run_data.get("completed_at"),
        "modules": inspect.get("modules", {}),
        "artifacts": {
            "total": inspect.get("summary", {}).get("total_artifacts", 0),
            "by_type": inspect.get("summary", {}).get("artifacts_by_type", {}),
            "total_bytes": sum(
                a.get("size_bytes", 0)
                for a in inspect.get("artifacts", [])
            ),
        },
        "events": {
            "total": inspect.get("summary", {}).get("total_events", 0),
            "by_status": inspect.get("summary", {}).get("events_by_status", {}),
        },
        "module_health": inspect.get("module_health", {}),
        "sensitivity_level": run_data.get("sensitivity_level", "internal"),
        "provenance": run_data.get("provenance"),
    }
    return summary
