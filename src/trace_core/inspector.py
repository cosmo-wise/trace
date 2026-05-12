from __future__ import annotations

from pathlib import Path
from typing import Any

from trace_core.protocol import inspect_protocol


def inspect_run(
    run_dir: Path,
    *,
    status: str | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    protocol = inspect_protocol(run_dir)
    run = protocol["run"]
    artifacts = protocol["artifacts"]
    events = protocol["events"]
    warnings = [event for event in events if event.get("status") == "warning"]
    errors = [
        event
        for event in events
        if event.get("status") not in {"ok", "warning", "passed", "running"}
    ]
    module_health = build_module_health(events, artifacts)
    return {
        "ok": not protocol["missing"],
        "missing": protocol["missing"],
        "run_id": run.get("run_id", ""),
        "status": status or run.get("status", "unknown"),
        "message": message,
        "event_count": len(events),
        "warning_count": len(warnings),
        "error_count": len(errors),
        "warnings": warnings[:20],
        "errors": errors[:20],
        "artifact_count": len(artifacts),
        "artifact_bytes": sum(int(item.get("size_bytes", 0)) for item in artifacts),
        "artifacts": artifacts,
        "module_health": module_health,
    }


def build_module_health(
    events: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    modules = sorted(
        {
            str(item.get("module") or "unknown")
            for item in [*events, *artifacts]
        }
    )
    health: dict[str, Any] = {}
    for module in modules:
        module_events = [event for event in events if str(event.get("module") or "unknown") == module]
        module_artifacts = [
            artifact
            for artifact in artifacts
            if str(artifact.get("module") or "unknown") == module
        ]
        warnings = [event for event in module_events if event.get("status") == "warning"]
        errors = [
            event
            for event in module_events
            if event.get("status") not in {"ok", "warning", "passed", "running"}
        ]
        if errors:
            status = "failed"
        elif warnings:
            status = "warning"
        else:
            status = "passed"
        health[module] = {
            "status": status,
            "event_count": len(module_events),
            "artifact_count": len(module_artifacts),
            "warning_count": len(warnings),
            "error_count": len(errors),
            "warnings": warnings[:10],
            "errors": errors[:10],
        }
    return health
