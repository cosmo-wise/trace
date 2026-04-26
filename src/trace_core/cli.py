from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from trace_core.run import TraceRun


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        payload = _dispatch(args)
    except Exception as exc:  # noqa: BLE001 - CLI must return structured failures.
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"trace: {exc}")
        return 1
    if payload is not None:
        _print_payload(payload, as_json=getattr(args, "json", False))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trace", description="Capture local trace evidence runs.")
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start")
    start.add_argument("--run-id", required=True)
    start.add_argument("--out", required=True, type=Path)
    start.add_argument("--label")
    start.add_argument("--json", action="store_true")

    event = sub.add_parser("event")
    _run_args(event)
    event.add_argument("--module", required=True)
    event.add_argument("--phase", required=True)
    event.add_argument("--type", required=True)
    event.add_argument("--status", default="ok")
    event.add_argument("--message", default="")
    event.add_argument("--metadata-json", default="{}")

    artifact = sub.add_parser("artifact")
    _run_args(artifact)
    artifact.add_argument("--module", required=True)
    artifact.add_argument("--phase", required=True)
    artifact.add_argument("--path", required=True, type=Path)
    artifact.add_argument("--type", default="other")
    artifact.add_argument("--role")
    artifact.add_argument("--strict", action="store_true")

    log = sub.add_parser("log")
    _run_args(log)
    log.add_argument("--module", required=True)
    log.add_argument("--phase", required=True)
    log.add_argument("--file", required=True, type=Path)
    log.add_argument("--name")
    log.add_argument("--strict", action="store_true")

    final = sub.add_parser("finalize")
    _run_args(final)
    final.add_argument("--status", default="passed")
    final.add_argument("--message")

    inspect = sub.add_parser("inspect")
    _run_args(inspect)

    doctor = sub.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")
    return parser


def _run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--json", action="store_true")


def _dispatch(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.command == "start":
        trace = TraceRun.start(args.run_id, args.out, args.label)
        return {"ok": True, "run": str(trace.run_dir), "run_id": trace.run_id}
    if args.command == "event":
        event = TraceRun.open(args.run).record_event(
            args.module,
            args.phase,
            args.type,
            args.status,
            args.message,
            json.loads(args.metadata_json),
        )
        return {"ok": True, "event": event.to_dict()}
    if args.command == "artifact":
        entry = TraceRun.open(args.run, strict=args.strict).copy_artifact(
            args.module, args.phase, args.path, args.type, args.role
        )
        return {"ok": True, "artifact": entry.to_dict()}
    if args.command == "log":
        entry = TraceRun.open(args.run, strict=args.strict).record_log(
            args.module, args.phase, args.file, args.name
        )
        return {"ok": True, "artifact": entry.to_dict()}
    if args.command == "finalize":
        return TraceRun.open(args.run).finalize(args.status, args.message)
    if args.command == "inspect":
        return TraceRun.open(args.run).inspect()
    if args.command == "doctor":
        return _doctor()
    return None


def _doctor() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "sample.log"
        source.write_text("trace doctor ok\n", encoding="utf-8")
        trace = TraceRun.start("doctor", root / "trace-run", "doctor")
        trace.record_log("trace", "doctor", source)
        summary = trace.finalize("passed", "doctor completed")
        return {"ok": summary["ok"], "checks": ["local-file-run", "artifact-copy", "finalize"]}


def _print_payload(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
