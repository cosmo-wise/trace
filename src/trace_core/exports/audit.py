"""Export an audit bundle with redaction applied."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from trace_core.bundle import bundle_run
from trace_core.exports.summary import export_summary
from trace_core.redaction.engine import RedactionEngine


def export_audit_bundle(
    run_dir: Path,
    output_path: Path,
    *,
    redact: bool = True,
    redaction_rules: list[Any] | None = None,
) -> dict[str, Any]:
    """Package a run directory as an audit-ready evidence bundle.

    Optionally applies redaction before bundling.
    Returns metadata about the bundle.
    """
    if redact:
        engine = RedactionEngine(redaction_rules)
        report = engine.redact_run(run_dir)
        source_dir = Path(report.output_dir)
    else:
        source_dir = run_dir

    bundle_path = bundle_run(source_dir, output_path)
    summary = export_summary(source_dir)

    return {
        "bundle_path": str(bundle_path),
        "bundle_size_bytes": bundle_path.stat().st_size if bundle_path.exists() else 0,
        "redacted": redact,
        "source_run": str(run_dir),
        "summary": summary,
    }
