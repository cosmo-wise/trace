from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path
from typing import Any

_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_slug(value: str, *, fallback: str = "item") -> str:
    slug = _SAFE_RE.sub("-", value.strip()).strip(".-_")
    return slug[:80] or fallback


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(child.stat().st_size for child in path.rglob("*") if child.is_file())


def copy_payload(source: Path, payload_dir: Path) -> tuple[str | None, list[dict[str, Any]]]:
    payload_dir.mkdir(parents=True, exist_ok=True)
    if source.is_file():
        target = payload_dir / sanitize_slug(source.name, fallback="artifact")
        shutil.copy2(source, target)
        return file_sha256(target), [_file_entry(target, payload_dir)]

    files: list[dict[str, Any]] = []
    for child in sorted(source.rglob("*")):
        if not child.is_file():
            continue
        rel = child.relative_to(source)
        safe_rel = Path(*[sanitize_slug(part, fallback="part") for part in rel.parts])
        target = payload_dir / safe_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(child, target)
        files.append(_file_entry(target, payload_dir))
    return None, files


def _file_entry(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(base).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": file_sha256(path),
    }
