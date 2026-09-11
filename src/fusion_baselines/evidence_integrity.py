"""Resolve immutable path/hash references without pretending old code is current."""

import hashlib
import re
import subprocess
from pathlib import Path

from fusion_baselines.provenance import sha256_file


def reference_records(value):
    """Yield every explicit path/sha256 pair in a JSON-like object."""
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            yield {"path": value["path"], "sha256": value["sha256"]}
        for item in value.values():
            yield from reference_records(item)
    elif isinstance(value, list):
        for item in value:
            yield from reference_records(item)


def resolve_reference(record, root, recorded_root, revision, relocations=None):
    root, recorded_root = Path(root).resolve(), Path(recorded_root)
    relocations = relocations or {}
    result = {**record, "source_revision": revision, "status": "unresolved"}
    if (
        not isinstance(record["path"], str)
        or not isinstance(record["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", record["sha256"]) is None
    ):
        return {**result, "reason": "malformed path/hash reference"}
    original = Path(record["path"])
    try:
        relative = original.relative_to(recorded_root) if original.is_absolute() else original
        if ".." in relative.parts:
            return {**result, "reason": "unsafe relative path"}
        local = root / relative
    except ValueError:
        relative, local = None, original
    if local.is_file() and sha256_file(local) == record["sha256"]:
        return {**result, "status": "current", "resolved_path": str(local)}
    if relative is not None and str(relative) in relocations:
        moved = root / relocations[str(relative)]
        if moved.is_file() and sha256_file(moved) == record["sha256"]:
            return {**result, "status": "relocated_identical", "resolved_path": str(moved)}
    if (
        relative is not None
        and isinstance(revision, str)
        and re.fullmatch(r"[0-9a-f]{7,40}", revision)
    ):
        archived = subprocess.run(
            ["git", "show", f"{revision}:{relative.as_posix()}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if (
            archived.returncode == 0
            and hashlib.sha256(archived.stdout).hexdigest() == record["sha256"]
        ):
            return {**result, "status": "historical_git", "git_path": relative.as_posix()}
    return {**result, "reason": "no matching current, relocated or recorded-revision bytes"}
