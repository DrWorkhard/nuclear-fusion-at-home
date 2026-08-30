"""Capture and verify the provenance required by the project evidence standard."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest of *path* without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _git(path: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def git_state(path: Path) -> dict[str, Any]:
    """Describe a Git checkout, including whether tracked content is dirty."""
    root = _git(path, "rev-parse", "--show-toplevel")
    if root is None:
        return {"path": str(path.resolve()), "available": False}
    status = _git(path, "status", "--porcelain")
    return {
        "path": root,
        "available": True,
        "commit": _git(path, "rev-parse", "HEAD"),
        "branch": _git(path, "branch", "--show-current"),
        "dirty": bool(status),
    }


def host_state() -> dict[str, Any]:
    """Capture a compact, stable description of the executing host."""
    return {
        "captured_at": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": sys.version,
        "python_executable": sys.executable,
        "logical_cpu_count": os.cpu_count(),
    }


def build_run_record(
    project_root: Path,
    external_roots: dict[str, Path] | None = None,
) -> dict[str, Any]:
    """Create the immutable metadata section shared by all run records."""
    externals = external_roots or {}
    return {
        "schema_version": 1,
        "host": host_state(),
        "repository": git_state(project_root),
        "external_repositories": {
            name: git_state(path) for name, path in sorted(externals.items())
        },
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON via a sibling temporary file to avoid partial run records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)
