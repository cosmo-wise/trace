"""Tests for trace hashing utilities."""

from __future__ import annotations

import tempfile
from pathlib import Path

from trace_core.hash import hash_file, hash_directory, verify_hashes


def test_hash_file() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("hello world")
        path = Path(f.name)
    digest = hash_file(path)
    assert len(digest) == 64  # sha256 hex
    path.unlink()


def test_hash_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "a.txt").write_text("content a", encoding="utf-8")
        (d / "b.txt").write_text("content b", encoding="utf-8")
        result = hash_directory(d)
        assert "sha256" in result["algorithm"]
        assert len(result["files"]) == 2


def test_verify_hashes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "f.txt").write_text("data", encoding="utf-8")
        digest = hash_file(d / "f.txt")
        mismatches = verify_hashes(d, {"f.txt": digest})
        assert len(mismatches) == 0


def test_verify_hashes_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "f.txt").write_text("data", encoding="utf-8")
        mismatches = verify_hashes(d, {"f.txt": "0000000000000000000000000000000000000000000000000000000000000000"})
        assert len(mismatches) == 1
