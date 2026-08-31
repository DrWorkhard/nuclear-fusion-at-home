"""Validation for baseline data manifests without case-specific solver code."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fusion_baselines.provenance import sha256_file

KINDS = {"w7x", "open_qi", "squid_c"}
FILE_ROLES = {
    "boozer_output",
    "coils",
    "currents",
    "fixed_boundary_vmec_input",
    "fixed_boundary_vmec_output",
    "free_boundary_vmec_input",
    "free_boundary_vmec_output",
    "metadata",
    "mgrid_recipe",
    "profiles",
    "solver_controls",
    "vmec_input",
    "vmec_output",
}
REQUIRED_TOP_LEVEL = {"schema_version", "case_id", "kind", "source", "files", "conventions"}
SQUID_C_REQUIRED_TOP_LEVEL = {"equilibria", "reference_metrics", "scale", "symmetry"}
SQUID_C_REQUIRED_FILE_ROLES = {
    "coils",
    "currents",
    "fixed_boundary_vmec_input",
    "fixed_boundary_vmec_output",
    "free_boundary_vmec_input",
    "free_boundary_vmec_output",
    "metadata",
    "mgrid_recipe",
    "profiles",
    "solver_controls",
}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class ManifestError(ValueError):
    """Raised when a baseline manifest violates the intake contract."""


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _is_filled_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.startswith("REQUIRED")


def _validate_squid_c_v2(data: dict[str, Any], seen_roles: set[str]) -> list[str]:
    errors: list[str] = []
    absent_top_level = sorted(SQUID_C_REQUIRED_TOP_LEVEL - data.keys())
    if absent_top_level:
        errors.append(f"missing SQuID-C fields: {', '.join(absent_top_level)}")

    source = data.get("source", {})
    for name in ("authority", "license", "retrieved_at"):
        if not _is_filled_string(source.get(name)):
            errors.append(f"source.{name} must be filled and not be a template placeholder")

    conventions = data.get("conventions", {})
    for name in (
        "length_unit",
        "field_unit",
        "coordinate_system",
        "current_sign",
        "toroidal_angle",
        "poloidal_angle",
        "minor_radius_definition",
    ):
        if not _is_filled_string(conventions.get(name)):
            errors.append(f"conventions.{name} must be filled")

    missing_roles = sorted(SQUID_C_REQUIRED_FILE_ROLES - seen_roles)
    if missing_roles:
        errors.append(f"missing SQuID-C file roles: {', '.join(missing_roles)}")

    equilibria = data.get("equilibria")
    if not isinstance(equilibria, dict):
        errors.append("equilibria must be an object")
    else:
        required_equilibria = {
            "fixed_boundary": (False, "fixed_boundary_vmec_input", "fixed_boundary_vmec_output"),
            "coil_generated_free_boundary": (
                True,
                "free_boundary_vmec_input",
                "free_boundary_vmec_output",
            ),
        }
        for name, (free_boundary, input_role, output_role) in required_equilibria.items():
            equilibrium = equilibria.get(name)
            if not isinstance(equilibrium, dict):
                errors.append(f"equilibria.{name} must be an object")
                continue
            required_fields = {
                "code",
                "version",
                "free_boundary",
                "nfp",
                "mpol",
                "ntor",
                "ns",
                "convergence_tolerances",
                "input_role",
                "output_role",
            }
            missing = sorted(required_fields - equilibrium.keys())
            if missing:
                errors.append(f"equilibria.{name} missing fields: {', '.join(missing)}")
            for field in ("code", "version"):
                if not _is_filled_string(equilibrium.get(field)):
                    errors.append(f"equilibria.{name}.{field} must be filled")
            for field in ("nfp", "mpol", "ntor", "ns"):
                value = equilibrium.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                    errors.append(f"equilibria.{name}.{field} must be a positive integer")
            if (
                not isinstance(equilibrium.get("convergence_tolerances"), dict)
                or not equilibrium["convergence_tolerances"]
            ):
                errors.append(f"equilibria.{name}.convergence_tolerances must be an object")
            if equilibrium.get("free_boundary") is not free_boundary:
                errors.append(f"equilibria.{name}.free_boundary must be {free_boundary}")
            if equilibrium.get("input_role") != input_role:
                errors.append(f"equilibria.{name}.input_role must be {input_role}")
            if equilibrium.get("output_role") != output_role:
                errors.append(f"equilibria.{name}.output_role must be {output_role}")

    scale = data.get("scale")
    if not isinstance(scale, dict):
        errors.append("scale must be an object")
    else:
        for name in ("effective_minor_radius_m", "on_axis_field_T"):
            value = scale.get(name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                errors.append(f"scale.{name} must be a positive number")
        if not _is_filled_string(scale.get("definition")):
            errors.append("scale.definition must be filled")

    symmetry = data.get("symmetry")
    if not isinstance(symmetry, dict):
        errors.append("symmetry must be an object")
    else:
        for name in ("nfp", "unique_coil_count", "full_coil_count"):
            value = symmetry.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"symmetry.{name} must be a positive integer")
        if not isinstance(symmetry.get("stellarator_symmetry"), bool):
            errors.append("symmetry.stellarator_symmetry must be boolean")
        if not _is_filled_string(symmetry.get("expansion_rule")):
            errors.append("symmetry.expansion_rule must be filled")

    reference_metrics = data.get("reference_metrics")
    if not isinstance(reference_metrics, dict) or not reference_metrics:
        errors.append("reference_metrics must be a non-empty object")
    else:
        required_metrics = {
            "coil_normal_field_max_abs",
            "coil_normal_field_mean_abs",
            "coil_table",
            "iota_profile",
            "pressure_profile",
            "quasi_isodynamic_metric",
            "volume_averaged_beta",
        }
        missing_metrics = sorted(required_metrics - reference_metrics.keys())
        if missing_metrics:
            errors.append(f"missing SQuID-C reference metrics: {', '.join(missing_metrics)}")

    if isinstance(equilibria, dict) and isinstance(symmetry, dict):
        for name in ("fixed_boundary", "coil_generated_free_boundary"):
            equilibrium = equilibria.get(name)
            if isinstance(equilibrium, dict) and equilibrium.get("nfp") != symmetry.get("nfp"):
                errors.append(f"equilibria.{name}.nfp must match symmetry.nfp")
    return errors


def validate_manifest(data: dict[str, Any], base_dir: Path, verify_files: bool = True) -> list[str]:
    """Validate structure and optionally file existence and content hashes."""
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")
    schema_version = data.get("schema_version")
    if schema_version not in {1, 2}:
        errors.append("schema_version must be 1 or 2")
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
    declared_items: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(files):
        prefix = f"files[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        role = item.get("role")
        if role not in FILE_ROLES:
            errors.append(f"{prefix}.role must be one of {sorted(FILE_ROLES)}")
        else:
            if role in seen_roles and schema_version == 2:
                errors.append(f"{prefix}.role duplicates {role}")
            seen_roles.add(role)
            declared_items[role] = item
        relative = item.get("path")
        expected_hash = item.get("sha256")
        if not relative or not expected_hash:
            errors.append(f"{prefix} must contain path and sha256")
            continue
        if schema_version == 2:
            if not isinstance(expected_hash, str) or not SHA256_PATTERN.fullmatch(expected_hash):
                errors.append(f"{prefix}.sha256 must be 64 lowercase hexadecimal characters")
            expected_bytes = item.get("bytes")
            if (
                not isinstance(expected_bytes, int)
                or isinstance(expected_bytes, bool)
                or expected_bytes < 0
            ):
                errors.append(f"{prefix}.bytes must be a non-negative integer")
            origin = item.get("origin")
            if origin not in {"authoritative", "derived"}:
                errors.append(f"{prefix}.origin must be authoritative or derived")
            elif origin == "authoritative":
                if not _is_filled_string(item.get("source_url")):
                    errors.append(f"{prefix}.source_url must identify the authoritative artifact")
            else:
                derived_from = item.get("derived_from")
                if not isinstance(derived_from, list) or not derived_from:
                    errors.append(f"{prefix}.derived_from must be a non-empty role list")
                if not _is_filled_string(item.get("recipe")):
                    errors.append(f"{prefix}.recipe must be a non-empty string")
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
            elif schema_version == 2 and candidate.stat().st_size != item.get("bytes"):
                errors.append(f"{prefix}.bytes does not match: {relative}")

    if schema_version == 2:
        for role, item in declared_items.items():
            if item.get("origin") != "derived" or not isinstance(item.get("derived_from"), list):
                continue
            for parent_role in item["derived_from"]:
                if parent_role not in declared_items:
                    errors.append(f"file role {role} derives from undeclared role {parent_role}")

    vmec_roles = {
        "fixed_boundary_vmec_input",
        "fixed_boundary_vmec_output",
        "free_boundary_vmec_input",
        "free_boundary_vmec_output",
        "vmec_input",
        "vmec_output",
    }
    if not (vmec_roles & seen_roles):
        errors.append("at least one VMEC input or output file is required")
    if data.get("kind") == "squid_c":
        if schema_version != 2:
            errors.append("SQuID-C manifests must use schema_version 2")
        else:
            errors.extend(_validate_squid_c_v2(data, seen_roles))
    return errors
