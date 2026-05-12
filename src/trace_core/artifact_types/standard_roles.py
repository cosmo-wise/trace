"""Standard artifact roles in the trace evidence protocol.

Roles describe the semantic purpose of an artifact within a run.
"""

STANDARD_ROLES: dict[str, str] = {
    "source": "Original input file or resource before any transformation",
    "output": "Generated or produced artifact (code, config, report)",
    "evidence": "Evidence artifact supporting a claim or gate decision",
    "log": "Execution log output",
    "report": "Structured report (summary, audit, analysis)",
    "config": "Configuration file used during the run",
    "screenshot": "Visual capture of a browser or UI state",
    "baseline": "Reference baseline used for comparison",
    "diff": "Difference or patch between two versions",
    "trace": "Trace-internal metadata artifact",
}

__all__ = ["STANDARD_ROLES"]
