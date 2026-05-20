# trace

<p align="center">
  Local-file evidence capture for AI-driven development workflows
</p>

<p align="center">

[![Version][version-shield]][version-url]
[![License][license-shield]][license-url]
[![Python][python-shield]][python-url]
[![Build][build-shield]][build-url]

</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="#cli">CLI</a> &middot;
  <a href="#library-usage">Library</a> &middot;
  <a href="#how-it-works">How It Works</a> &middot;
  <a href="README-CN.md">🇨🇳 中文版</a>
</p>

---

## The Problem

Observability for AI-driven development pipelines is typically either too heavy (dedicated databases, tracing backends, queues) or too ad-hoc (scattered log files, missing context, no structured retrieval). When multiple agents produce artifacts across different phases, reconstructing what happened requires stitching together inconsistent formats.

Trace solves this by capturing events, artifacts, and logs as plain files in a consistent layout — inspectable with any text editor, composable across runs, and light enough for local AI agent workflows.

## Features

- **Zero-infrastructure capture** — No database, queue, or daemon. Every run is a plain-file directory.
- **Structured timeline** — JSONL event stream with module, phase, type, and status for every step.
- **Artifact registry** — Self-describing artifact index with content-addressable payload storage.
- **Run redaction** — `trace redact` strips local paths and identifiers before sharing.
- **Inspectable at rest** — Read a completed run with any text editor, CLI tool, or AI agent.
- **Multiple verbosity levels** — Compact single-line export-summary for orchestration, full evidence bundles for deep inspection.

## When to Use

Reach for Trace when you need lightweight, file-based run capture for multi-agent or multi-phase AI development workflows. Use after you've started producing events or artifacts that need structured collection for later review, replay, or audit.

**Not for:** High-throughput production observability, real-time streaming dashboards, or long-term archival at scale. Trace is designed for local and CI-scale usage — not as a replacement for dedicated tracing backends.

## Quick Start

```bash
# Start a new run
python cli.py start --run-id demo --out trace-run

# Record events and artifacts
python cli.py event --run trace-run --module relay --phase query-plan --type phase_completed --message ok
python cli.py artifact --run trace-run --module relay --phase query-plan --path result.json --type json --role output

# Finalize
python cli.py finalize --run trace-run --status passed

# Inspect
python cli.py inspect --run trace-run
```

## Install

```bash
pip install trace
```

Requires Python 3.11+. No runtime dependencies beyond the standard library.

## CLI

```bash
# Lifecycle
python cli.py start --run-id demo --out trace-run --json
python cli.py finalize --run trace-run --status passed --json

# Capture
python cli.py event --run trace-run --module relay --phase query-plan --type phase_completed --message ok --json
python cli.py artifact --run trace-run --module relay --phase query-plan --path result.json --type json --role output --json
python cli.py log --run trace-run --module relay --phase query-plan --level warning --message "rate limit approaching" --json

# Inspect & transform
python cli.py inspect --run trace-run --json
python cli.py doctor --json
python cli.py validate --run trace-run --json
python cli.py redact --run trace-run --out trace-run-redacted --json
python cli.py export-summary --run trace-run --json
python cli.py bundle --run trace-run --out trace-run-bundle --json
```

| Command | Purpose |
|---------|---------|
| `start` | Initialize a new run directory |
| `event` | Record a structured event on the timeline |
| `artifact` | Copy a file into the artifact registry |
| `log` | Record a warning or error message |
| `finalize` | Mark the run as passed or failed |
| `inspect` | Print a human-readable run summary |
| `doctor` | Check Python and schema prerequisites |
| `validate` | Check run directory consistency and completeness |
| `redact` | Copy run directory, stripping local paths and identifiers |
| `export-summary` | Print a compact single-line summary for orchestration |
| `bundle` | Package the run directory into a self-contained archive |

## Library Usage

```python
from pathlib import Path
from trace_core import TraceRun

trace = TraceRun.start("demo", Path("trace-run"))
trace.record_event("relay", "query-plan", "phase_completed", "ok", "planned queries")
trace.copy_artifact("relay", "query-plan", Path("result.json"), "json", "output")
trace.finalize("passed")
```

`trace inspect` and `trace finalize` summaries include `warning_count`, `error_count`, and sampled warnings/errors. This keeps a run with complete protocol files distinguishable from a genuinely clean run; orchestration layers can promote warnings to hard gates when product quality requires it.

→ [Producer adapter guide](docs/producer-adapters.md)

---

## How It Works

Trace stores every run as a directory of plain files with a consistent protocol layout:

```text
trace-run/
  run.json                # Run manifest
  timeline.jsonl          # Chronological event stream
  artifacts/index.json    # Self-describing artifact index
  artifacts/<id>/payload/ # Copied artifact payloads
  summary.json            # Aggregated run summary
  evidence.md             # Human-readable evidence report
```

### Architecture

```
trace/
├── cli.py                 # CLI entry point
├── src/
│   ├── trace_core.py      # Core TraceRun library
│   ├── commands/          # CLI command implementations
│   └── schemas/           # Protocol schema definitions
├── schemas/               # Versioned JSON schemas
└── probe/                 # Test assets
```

### Protocol Schemas

Trace enforces consistency with versioned JSON schemas:

| Schema | Description |
| --- | --- |
| `trace-manifest-1.0.json` | Top-level run manifest |
| `timeline-1.0.json` | Timeline event entry |
| `artifact-index-1.0.json` | Artifact registry index |
| `summary-1.0.json` | Run summary |
| `evidence-bundle-1.0.json` | Evidence bundle format |

### Producer Integration

Producer adapters may write the JSONL/manifest protocol directly. Python producers should use optional import or subprocess boundaries, staying non-strict by default; Harness and Trial use TypeScript-native protocol writers validated by `trace inspect`.

Python producer copies of `trace_capture.py` are synchronized from the Chariot workspace template with `python3 tools/chariot/sync/sync_trace_capture.py --check` or `--write`. This keeps Relay, Scout, Course, and Scribe runtime-independent from the sibling `trace` repo while avoiding helper drift.

### Why Plain Files?

- **Zero infrastructure** — No database, no queue, no daemon.
- **Inspectable** — Any text editor or CLI can read a run.
- **Sanitizable** — `redact` strips paths and identifiers before sharing.
- **Replayable** — Timeline data suits AI-driven replay analysis.
- **Composable** — Multiple runs can be merged, compared, or fed into audit tools.

## Contributing

Contributions are welcome. Open an issue or pull request on [GitHub](https://github.com/cosmo-wise/trace).

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

<!-- Badge reference links -->
[version-shield]: https://img.shields.io/badge/version-0.1.0-blue
[version-url]: https://github.com/cosmo-wise/trace/releases
[license-shield]: https://img.shields.io/badge/license-Apache%202.0-blue
[license-url]: https://github.com/cosmo-wise/trace/blob/main/LICENSE
[python-shield]: https://img.shields.io/badge/python-%3E%3D3.11-3776AB?logo=python
[python-url]: https://python.org
[build-shield]: https://img.shields.io/badge/build-passing-brightgreen
[build-url]: #
