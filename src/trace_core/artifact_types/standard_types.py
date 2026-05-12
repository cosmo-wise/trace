"""Standard artifact types in the trace evidence protocol.

Types describe the technical format or category of an artifact.
"""

STANDARD_TYPES: dict[str, str] = {
    "code": "Source code file",
    "config": "Configuration file (YAML, JSON, TOML)",
    "screenshot": "PNG or image-based screenshot",
    "log": "Text log file",
    "trace-event": "Trace event data (JSON)",
    "report": "Structured report (JSON, Markdown)",
    "test-result": "Test execution result (JUnit, TAP)",
    "coverage": "Coverage report",
    "diff": "Diff or patch output",
    "manifest": "Manifest or index file",
    "artifact-bundle": "Archive of multiple artifacts",
    "evidence": "Evidence assertion or attestation",
    "metadata": "Run or task metadata",
}

__all__ = ["STANDARD_TYPES"]
