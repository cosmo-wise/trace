"""Redaction rule definitions for sanitizing evidence before export."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RedactionRule:
    """A single redaction rule: pattern to match and how to replace it."""

    name: str
    pattern: str  # Regex pattern
    replacement: str = "***"
    description: str = ""
    paths: list[str] | None = None  # Limit to specific paths (glob patterns)

    def apply(self, content: str, source_path: str | None = None) -> str:
        """Apply this rule to content, optionally filtered by source path."""
        if self.paths and source_path:
            path_obj = Path(source_path)
            if not any(path_obj.match(pat) for pat in self.paths):
                return content
        return re.sub(self.pattern, self.replacement, content)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pattern": self.pattern,
            "replacement": self.replacement,
            "description": self.description,
            "paths": self.paths,
        }


# Built-in redaction rules
def builtin_rules() -> list[RedactionRule]:
    """Return default redaction rules covering common sensitive patterns."""
    return [
        RedactionRule(
            name="aws-access-key",
            pattern=r"AKIA[0-9A-Z]{16}",
            replacement="AKIA***",
            description="AWS access key ID",
        ),
        RedactionRule(
            name="aws-secret-key",
            pattern=r"(?i)aws[_\-.]secret[_\-.]access[_\-.]key\s*[:=]\s*\S+",
            replacement="aws_secret_access_key=***",
            description="AWS secret access key",
        ),
        RedactionRule(
            name="github-token",
            pattern=r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}",
            replacement="gh***",
            description="GitHub token",
        ),
        RedactionRule(
            name="generic-token",
            pattern=r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?\S{8,}['\"]?",
            replacement=r"\1=***",
            description="Generic credential pattern",
        ),
        RedactionRule(
            name="bearer-auth",
            pattern=r"(?i)bearer\s+[A-Za-z0-9._\-+/]{20,}",
            replacement="Bearer ***",
            description="Bearer authorization header value",
        ),
        RedactionRule(
            name="private-key",
            pattern=r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----",
            replacement="*** PRIVATE KEY ***",
            description="PEM-encoded private key block",
            paths=["*.key", "*.pem", "*.cert"],
        ),
        RedactionRule(
            name="connection-string",
            pattern=r"(?i)(?:postgres|mysql|redis|mongodb)://[^\s]+",
            replacement="***://***",
            description="Database connection string",
        ),
        RedactionRule(
            name="email-address",
            pattern=r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            replacement="***@***",
            description="Email address",
        ),
        RedactionRule(
            name="ip-address",
            pattern=r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            replacement="*.*.*.*",
            description="IPv4 address",
        ),
    ]
