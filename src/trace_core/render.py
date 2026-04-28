from __future__ import annotations

from typing import Any


def render_evidence(summary: dict[str, Any]) -> str:
    lines = [
        f"# Trace evidence: {summary['run_id']}",
        "",
        f"- Status: {summary['status']}",
        f"- Events: {summary['event_count']}",
        f"- Warnings: {summary.get('warning_count', 0)}",
        f"- Errors: {summary.get('error_count', 0)}",
        f"- Artifacts: {summary['artifact_count']}",
        f"- Copied bytes: {summary['artifact_bytes']}",
    ]
    if summary.get("message"):
        lines.append(f"- Message: {summary['message']}")
    warnings = summary.get("warnings") or []
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings[:10]:
            lines.append(
                "- "
                f"{warning.get('module', 'unknown')}/{warning.get('phase', 'unknown')} "
                f"{warning.get('type', 'event')}: {warning.get('message', '')}"
            )
    lines.extend(["", "## Artifacts", ""])
    artifacts = summary.get("artifacts", [])
    if not artifacts:
        lines.append("No artifacts copied.")
    for artifact in artifacts:
        lines.append(
            "- "
            f"{artifact['artifact_id']} ({artifact['module']}/{artifact['phase']}): "
            f"{artifact['artifact_type']} -> {artifact['trace_path']}"
        )
    lines.append("")
    return "\n".join(lines)
