"""Capture and verify the provenance required by the project evidence standard."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _git(path: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def git_state(path: Path) -> dict[str, Any]:
    """Describe a Git checkout; dirty includes tracked changes and untracked files."""
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
