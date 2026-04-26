# trace

`trace` is Chariot's local-file evidence capture module. It is intentionally named `trace` (no `chariot-` prefix) and stores a run as ordinary files, not a backend service.

## Layout

```text
trace-run/
  run.json
  timeline.jsonl
  artifacts/index.json
  artifacts/<artifact-id>/payload/<copied files>
  summary.json
  evidence.md
```

## CLI

```bash
python cli.py start --run-id demo --out trace-run --json
python cli.py event --run trace-run --module relay --phase query-plan --type phase_completed --message ok --json
python cli.py artifact --run trace-run --module relay --phase query-plan --path result.json --type json --role output --json
python cli.py finalize --run trace-run --status passed --json
python cli.py inspect --run trace-run --json
python cli.py doctor --json
```

## Library

```python
from pathlib import Path
from trace_core import TraceRun

trace = TraceRun.start("demo", Path("trace-run"))
trace.record_event("relay", "query-plan", "phase_completed", "ok", "planned queries")
trace.copy_artifact("relay", "query-plan", Path("result.json"), "json", "output")
trace.finalize("passed")
```

Producer adapters may also write the documented JSONL/manifest protocol directly. Python producers should use optional import or subprocess boundaries and stay non-strict by default; Harness and Trial use TypeScript-native protocol writers validated by `trace inspect`.

Python producer copies of `trace_capture.py` are synchronized from the Chariot workspace template with `python3 tools/chariot/sync_trace_capture.py --check` or `--write`. This keeps Relay, Scout, Course, and Scribe runtime-independent from the sibling `trace` repo while avoiding helper drift.
