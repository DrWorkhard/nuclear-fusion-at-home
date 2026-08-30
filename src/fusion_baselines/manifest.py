"""Validation for baseline data manifests without case-specific solver code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fusion_baselines.provenance import sha256_file

KINDS = {"w7x", "open_qi", "squid_c"}
FILE_ROLES = {"vmec_input", "vmec_output", "coils", "currents", "profiles", "metadata"}
REQUIRED_TOP_LEVEL = {"schema_version", "case_id", "kind", "source", "files", "conventions"}


class ManifestError(ValueError):
    """Raised when a baseline manifest violates the intake contract."""


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def validate_manifest(data: dict[str, Any], base_dir: Path, verify_files: bool = True) -> list[str]:
    """Validate structure and optionally file existence and content hashes."""
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("kind") not in KINDS:
        errors.append(f"kind must be one of {sorted(KINDS)}")

    source = data.get("source")
    if not isinstance(source, dict) or not source.get("url") or not source.get("citation"):
        errors.append("source must contain non-empty url and citation")

    conventions = data.get("conventions")
    required_conventions = {"length_unit", "field_unit", "coordinate_system", "current_sign"}
    if not isinstance(conventions, dict):
        errors.append("conventions must be an object")
    else:
        absent = sorted(required_conventions - conventions.keys())
        if absent:
            errors.append(f"missing conventions: {', '.join(absent)}")

    files = data.get("files")
    if not isinstance(files, list) or not files:
        errors.append("files must be a non-empty list")
        return errors

    seen_roles: set[str] = set()
    for index, item in enumerate(files):
        prefix = f"files[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        role = item.get("role")
        if role not in FILE_ROLES:
            errors.append(f"{prefix}.role must be one of {sorted(FILE_ROLES)}")
        else:
            seen_roles.add(role)
        relative = item.get("path")
        expected_hash = item.get("sha256")
        if not relative or not expected_hash:
            errors.append(f"{prefix} must contain path and sha256")
            continue
        if verify_files:
            candidate = (base_dir / relative).resolve()
            try:
                candidate.relative_to(base_dir.resolve())
            except ValueError:
                errors.append(f"{prefix}.path escapes the manifest directory")
                continue
            if not candidate.is_file():
                errors.append(f"{prefix}.path does not exist: {relative}")
            elif sha256_file(candidate) != expected_hash:
                errors.append(f"{prefix}.sha256 does not match: {relative}")

    if not ({"vmec_input", "vmec_output"} & seen_roles):
        errors.append("at least one VMEC input or output file is required")
    return errors
