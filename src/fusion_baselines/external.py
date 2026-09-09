"""Verification of pinned external repositories and benchmark inputs."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from fusion_baselines.provenance import sha256_file


def _head(path: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def verify_external_spec(project_root: Path, spec_path: Path) -> list[str]:
    """Verify repository revision and file hashes from an external-data spec."""
    spec: dict[str, Any] = json.loads(spec_path.read_text())
    errors: list[str] = []
    project_root = project_root.resolve()
    repository = (project_root / spec["repository"]["path"]).resolve()
    if not repository.is_relative_to(project_root):
        return ["repository path escapes project root"]
    actual_commit = _head(repository)
    expected_commit = spec["repository"]["commit"]
    if actual_commit != expected_commit:
        errors.append(f"repository commit is {actual_commit!r}; expected {expected_commit}")
    if actual_commit is not None:
        status = subprocess.run(
            ["git", "-C", str(repository), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
        if status.returncode or status.stdout.strip():
            errors.append("repository has unverified working-tree changes")
    for item in spec["files"]:
        candidate = (project_root / item["path"]).resolve()
        if not candidate.is_relative_to(project_root):
            errors.append(f"file path escapes project root: {item['path']}")
            continue
        if not candidate.is_file():
            errors.append(f"missing file: {item['path']}")
        else:
            actual_hash = sha256_file(candidate)
            if actual_hash != item["sha256"]:
                errors.append(
                    f"hash mismatch for {item['path']}: {actual_hash}; expected {item['sha256']}"
                )
    return errors
