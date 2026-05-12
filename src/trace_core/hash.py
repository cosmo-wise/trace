"""Hashing utilities for trace artifact integrity verification."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def hash_file(path: Path, algorithm: str = "sha256") -> str:
    """Compute the hex digest of a file using the specified algorithm."""
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_directory(
    directory: Path,
    algorithm: str = "sha256",
    *,
    relative_to: Path | None = None,
) -> dict[str, Any]:
    """Compute hashes for all files in a directory recursively.

    Returns a dict mapping relative paths to their hashes.
    """
    base = relative_to or directory
    result: dict[str, Any] = {"algorithm": algorithm, "files": {}}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(base))
            result["files"][rel] = hash_file(path, algorithm)
    return result


def verify_hashes(directory: Path, expected: dict[str, str], algorithm: str = "sha256") -> dict[str, str]:
    """Verify file hashes against expected values.

    Returns a dict of mismatched paths -> "expected:got" messages.
    Mismatch is empty dict if all files match.
    """
    mismatches: dict[str, str] = {}
    for rel_path, expected_hash in expected.items():
        full_path = directory / rel_path
        if not full_path.exists():
            mismatches[rel_path] = f"missing:expected {expected_hash}"
            continue
        actual_hash = hash_file(full_path, algorithm)
        if actual_hash != expected_hash:
            mismatches[rel_path] = f"{expected_hash}:{actual_hash}"
    return mismatches
