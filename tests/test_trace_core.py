import json
from pathlib import Path

import pytest

from trace_core import TraceRun


def test_trace_lifecycle_copies_file_and_finalizes(tmp_path: Path) -> None:
    source = tmp_path / "result.json"
    source.write_text('{"ok": true}\n', encoding="utf-8")
    trace = TraceRun.start("demo", tmp_path / "trace-run", "Demo")

    trace.record_event("relay", "query-plan", "phase_completed", "ok", "planned")
    artifact = trace.copy_artifact("relay", "query-plan", source, "json", "output")
    summary = trace.finalize("passed", "done")

    assert artifact.trace_path.startswith("artifacts/")
    assert (tmp_path / "trace-run" / artifact.trace_path / source.name).exists()
    assert summary["ok"] is True
    assert summary["artifact_count"] == 1
    assert summary["module_health"]["relay"]["artifact_count"] == 1
    assert (tmp_path / "trace-run" / "module-health.json").exists()
    assert (tmp_path / "trace-run" / "summary.json").exists()
    assert "Trace evidence: demo" in (tmp_path / "trace-run" / "evidence.md").read_text()


def test_trace_copies_directory_with_hash_entries(tmp_path: Path) -> None:
    source_dir = tmp_path / "artifacts"
    (source_dir / "nested").mkdir(parents=True)
    (source_dir / "nested" / "report.md").write_text("# Report\n", encoding="utf-8")

    trace = TraceRun.start("dir", tmp_path / "trace-run")
    entry = trace.copy_artifact("scout", "research", source_dir, "directory", "artifacts")

    assert entry.sha256 is None
    assert entry.files[0]["path"] == "nested/report.md"
    assert (tmp_path / "trace-run" / entry.trace_path / "nested" / "report.md").exists()


def test_strict_budget_failure_does_not_mutate_index(tmp_path: Path) -> None:
    source = tmp_path / "large.log"
    source.write_text("too large", encoding="utf-8")
    trace = TraceRun.start("budget", tmp_path / "trace-run", max_artifact_bytes=1, strict=True)

    with pytest.raises(ValueError):
        trace.copy_artifact("trial", "run", source, "log")

    index = json.loads((tmp_path / "trace-run" / "artifacts" / "index.json").read_text())
    assert index["artifacts"] == []


def test_inspect_accepts_protocol_written_by_adapter(tmp_path: Path) -> None:
    run_dir = tmp_path / "trace-run"
    (run_dir / "artifacts" / "harness-run" / "payload").mkdir(parents=True)
    (run_dir / "run.json").write_text(
        json.dumps({"version": 1, "run_id": "adapter", "status": "running"}),
        encoding="utf-8",
    )
    (run_dir / "timeline.jsonl").write_text(
        json.dumps(
            {
                "event_id": "1",
                "run_id": "adapter",
                "timestamp": "2026-04-26T00:00:00Z",
                "type": "artifact_copied",
                "module": "harness",
                "phase": "finalize",
                "status": "ok",
                "message": "copied",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "artifacts" / "index.json").write_text(
        json.dumps(
            {
                "version": 1,
                "artifacts": [
                    {
                        "artifact_id": "harness-run",
                        "module": "harness",
                        "phase": "finalize",
                        "artifact_type": "json",
                        "source_path": "trace-summary.json",
                        "trace_path": "artifacts/harness-run/payload",
                        "size_bytes": 2,
                        "files": [],
                        "metadata": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert TraceRun.open(run_dir).inspect()["artifact_count"] == 1


def test_inspect_surfaces_warning_events_without_hiding_protocol_ok(tmp_path: Path) -> None:
    trace = TraceRun.start("warnings", tmp_path / "trace-run")
    trace.record_event(
        "chariot",
        "artifact-sweep",
        "artifact_missing",
        "warning",
        "missing artifact: optional-report.json",
    )

    summary = trace.finalize("passed", "done")

    assert summary["ok"] is True
    assert summary["warning_count"] == 1
    assert summary["warnings"][0]["type"] == "artifact_missing"
    assert summary["module_health"]["chariot"]["status"] == "warning"
    evidence = (tmp_path / "trace-run" / "evidence.md").read_text(encoding="utf-8")
    assert "Warnings: 1" in evidence
    assert "## Module Health" in evidence
    assert "missing artifact: optional-report.json" in evidence


def test_module_health_tracks_failed_modules_and_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "report.json"
    source.write_text('{"ok": false}\n', encoding="utf-8")
    trace = TraceRun.start("health", tmp_path / "trace-run")

    trace.record_event("trial", "run", "quality_gate", "failed", "route failed")
    trace.copy_artifact("trial", "run", source, "json", "report")
    summary = trace.finalize("failed", "done")

    trial = summary["module_health"]["trial"]
    assert trial["status"] == "failed"
    assert trial["error_count"] == 1
    assert trial["artifact_count"] == 1
    module_health = json.loads((tmp_path / "trace-run" / "module-health.json").read_text())
    assert module_health["trial"]["status"] == "failed"


def test_trace_accepts_carriage_as_artifact_source_module(tmp_path: Path) -> None:
    source = tmp_path / "profile-manifest.json"
    source.write_text('{"runtimeOwner":"carriage"}\n', encoding="utf-8")
    trace = TraceRun.start("carriage-run", tmp_path / "trace-run")

    trace.copy_artifact("carriage", "run", source, "json", "runtime-owner")
    summary = trace.finalize("passed", "done")

    assert summary["module_health"]["carriage"]["artifact_count"] == 1
    assert summary["module_health"]["carriage"]["status"] == "passed"
