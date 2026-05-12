"""Evidence bundling — package a trace run directory into a portable archive."""

from __future__ import annotations

import json
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from trace_core.hash import hash_file
from trace_core.protocol import read_json


def bundle_run(
    run_dir: Path,
    output_path: Path,
    *,
    compress: bool = True,
    include_manifest: bool = True,
) -> Path:
    """Package a trace run directory into a .tar.gz bundle.

    When include_manifest is True, writes a sidecar .manifest.json file
    with the bundle's hash (computed from the complete archive).
    Returns the path to the created bundle.
    """
    name = str(output_path)
    if not name.endswith(".tar.gz") and not name.endswith(".tgz"):
        output_path = output_path.with_suffix("").with_suffix(".tar.gz")

    mode = "w:gz" if compress else "w"
    run_id = _get_run_id(run_dir)

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)

        # Stage a manifest placeholder so it's included in the tar
        manifest_placeholder = {
            "bundle_id": f"{run_id}-bundle",
            "source_run_id": run_id,
            "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "redacted": False,
            "hash": {"algorithm": "sha256", "value": ""},
        }
        manifest_path = staging / "bundle-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest_placeholder, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        # Build the tar archive
        with tarfile.open(output_path, mode) as tar:
            tar.add(run_dir, arcname=run_dir.name)
            if include_manifest:
                tar.add(manifest_path, arcname="bundle-manifest.json")

    # Write sidecar manifest with the real hash of the completed archive
    if include_manifest:
        bundle_hash = hash_file(output_path)
        manifest = dict(manifest_placeholder)
        manifest["hash"] = {"algorithm": "sha256", "value": bundle_hash}
        manifest_path_sidecar = output_path.with_suffix(".manifest.json")
        manifest_path_sidecar.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return output_path


def _get_run_id(run_dir: Path) -> str:
    """Extract run_id from a trace run directory."""
    run_json = run_dir / "run.json"
    if run_json.exists():
        try:
            data = read_json(run_json)
            return data.get("run_id", run_dir.name)
        except (json.JSONDecodeError, ValueError):
            return run_dir.name
    return run_dir.name
