"""Validation for baseline data manifests without case-specific solver code."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

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
SQUID_C_COIL_COLUMNS = [
    "L_over_a",
    "d_over_a",
    "kappa_times_a",
    "c_over_a",
    "current_MA",
]
SQUID_C_COIL_ROWS = [
    [18.07, 0.595, 1.673, 0.953, 1.586],
    [20.82, 0.524, 1.669, 0.868, 1.532],
    [21.84, 0.512, 1.784, 0.880, 1.422],
    [22.83, 0.488, 2.028, 0.944, 1.313],
    [22.35, 0.488, 2.026, 0.992, 1.216],
]


class ManifestError(ValueError):
    """Raised when a baseline manifest violates the intake contract."""


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _is_filled_string(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not value.strip().upper().startswith("REQUIRED")
    )


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_positive_number(value: object) -> bool:
    return _is_finite_number(value) and value > 0


def _is_absolute_uri(value: object) -> bool:
    if not _is_filled_string(value) or any(character.isspace() for character in value):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return bool(parsed.scheme and (parsed.netloc or parsed.path))


def _is_timezone_aware_iso8601(value: object) -> bool:
    if not _is_filled_string(value):
        return False
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return timestamp.tzinfo is not None and timestamp.utcoffset() is not None


def _validate_interval_metric(
    metrics: dict[str, Any],
    name: str,
    *,
    require_definition: bool = False,
) -> list[str]:
    errors: list[str] = []
    metric = metrics.get(name)
    if not isinstance(metric, dict):
        return [f"reference_metrics.{name} must be an object"]
    value = metric.get("value")
    interval = metric.get("acceptance_interval")
    if not _is_finite_number(value):
        errors.append(f"reference_metrics.{name}.value must be finite")
    if (
        not isinstance(interval, list)
        or len(interval) != 2
        or not all(_is_finite_number(bound) for bound in interval)
        or interval[0] >= interval[1]
        or (_is_finite_number(value) and not interval[0] <= value <= interval[1])
    ):
        errors.append(
            f"reference_metrics.{name}.acceptance_interval must be ordered and contain value"
        )
    if not isinstance(metric.get("upper_exclusive"), bool):
        errors.append(f"reference_metrics.{name}.upper_exclusive must be boolean")
    if not _is_filled_string(metric.get("acceptance_basis")):
        errors.append(
            f"reference_metrics.{name}.acceptance_basis must identify the tolerance source"
        )
    if require_definition and not _is_filled_string(metric.get("definition")):
        errors.append(f"reference_metrics.{name}.definition must be filled")
    return errors


def _validate_derived_lineage(declared_items: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    graph: dict[str, list[str]] = {}
    for role, item in declared_items.items():
        if item.get("origin") != "derived" or not isinstance(item.get("derived_from"), list):
            continue
        parents = item["derived_from"]
        graph[role] = []
        if len(parents) != len(set(parent for parent in parents if isinstance(parent, str))):
            errors.append(f"file role {role} has duplicate derivation parents")
        for parent_role in parents:
            if not _is_filled_string(parent_role):
                errors.append(f"file role {role} has an invalid derivation parent")
            elif parent_role not in declared_items:
                errors.append(f"file role {role} derives from undeclared role {parent_role}")
            else:
                graph[role].append(parent_role)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(role: str) -> None:
        if role in visiting:
            errors.append(f"derived file lineage contains a cycle through role {role}")
            return
        if role in visited:
            return
        visiting.add(role)
        for parent in graph.get(role, []):
            if parent in graph:
                visit(parent)
        visiting.remove(role)
        visited.add(role)

    for role in graph:
        visit(role)
    return errors


def _validate_squid_c_v2(data: dict[str, Any], seen_roles: set[str]) -> list[str]:
    errors: list[str] = []
    absent_top_level = sorted(SQUID_C_REQUIRED_TOP_LEVEL - data.keys())
    if absent_top_level:
        errors.append(f"missing SQuID-C fields: {', '.join(absent_top_level)}")

    source_value = data.get("source", {})
    source = source_value if isinstance(source_value, dict) else {}
    for name in ("authority", "license", "retrieved_at", "citation"):
        if not _is_filled_string(source.get(name)):
            errors.append(f"source.{name} must be filled and not be a template placeholder")
    if not _is_absolute_uri(source.get("url")):
        errors.append("source.url must be an absolute URI")
    if not _is_timezone_aware_iso8601(source.get("retrieved_at")):
        errors.append("source.retrieved_at must be a timezone-aware ISO-8601 timestamp")

    conventions_value = data.get("conventions", {})
    conventions = conventions_value if isinstance(conventions_value, dict) else {}
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
            convergence_tolerances = equilibrium.get("convergence_tolerances")
            if not isinstance(convergence_tolerances, dict):
                errors.append(f"equilibria.{name}.convergence_tolerances must be an object")
            else:
                required_residuals = {"fsqr", "fsqz", "fsql"}
                missing_residuals = sorted(required_residuals - convergence_tolerances.keys())
                if missing_residuals:
                    errors.append(
                        f"equilibria.{name}.convergence_tolerances missing residuals: "
                        + ", ".join(missing_residuals)
                    )
                for residual, tolerance in convergence_tolerances.items():
                    if not _is_filled_string(residual) or not _is_positive_number(tolerance):
                        errors.append(
                            f"equilibria.{name}.convergence_tolerances.{residual} "
                            "must be a positive finite number"
                        )
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
            if not _is_positive_number(value):
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
        errors.extend(
            _validate_interval_metric(
                reference_metrics,
                "volume_averaged_beta",
            )
        )
        errors.extend(
            _validate_interval_metric(
                reference_metrics,
                "coil_normal_field_mean_abs",
                require_definition=True,
            )
        )
        errors.extend(
            _validate_interval_metric(
                reference_metrics,
                "coil_normal_field_max_abs",
                require_definition=True,
            )
        )

        pressure_profile = reference_metrics.get("pressure_profile")
        if not isinstance(pressure_profile, dict) or not _is_filled_string(
            pressure_profile.get("definition")
        ):
            errors.append("reference_metrics.pressure_profile.definition must be filled")

        coil_table = reference_metrics.get("coil_table")
        if not isinstance(coil_table, dict):
            errors.append("reference_metrics.coil_table must be an object")
        else:
            if coil_table.get("columns") != SQUID_C_COIL_COLUMNS:
                errors.append(
                    "reference_metrics.coil_table.columns do not match the frozen contract"
                )
            if coil_table.get("rows") != SQUID_C_COIL_ROWS:
                errors.append(
                    "reference_metrics.coil_table.rows do not match the frozen paper table"
                )
            if not _is_filled_string(coil_table.get("tolerance")):
                errors.append("reference_metrics.coil_table.tolerance must be filled")

        iota_profile = reference_metrics.get("iota_profile")
        if not isinstance(iota_profile, dict):
            errors.append("reference_metrics.iota_profile must be an object")
        else:
            iota_values = iota_profile.get("value")
            if (
                not isinstance(iota_values, list)
                or not iota_values
                or not all(_is_finite_number(value) for value in iota_values)
            ):
                errors.append(
                    "reference_metrics.iota_profile.value must be a non-empty number list"
                )
            if not _is_positive_number(iota_profile.get("absolute_tolerance")):
                errors.append(
                    "reference_metrics.iota_profile.absolute_tolerance must be a positive number"
                )

        qi_metric = reference_metrics.get("quasi_isodynamic_metric")
        if not isinstance(qi_metric, dict):
            errors.append("reference_metrics.quasi_isodynamic_metric must be an object")
        else:
            if not _is_filled_string(qi_metric.get("definition")):
                errors.append("reference_metrics.quasi_isodynamic_metric.definition must be filled")
            if not _is_finite_number(qi_metric.get("value")):
                errors.append(
                    "reference_metrics.quasi_isodynamic_metric.value must be a finite number"
                )
            if not _is_positive_number(qi_metric.get("absolute_tolerance")):
                errors.append(
                    "reference_metrics.quasi_isodynamic_metric.absolute_tolerance must be a "
                    "positive number"
                )

    if isinstance(equilibria, dict) and isinstance(symmetry, dict):
        for name in ("fixed_boundary", "coil_generated_free_boundary"):
            equilibrium = equilibria.get(name)
            if isinstance(equilibrium, dict) and equilibrium.get("nfp") != symmetry.get("nfp"):
                errors.append(f"equilibria.{name}.nfp must match symmetry.nfp")
    if isinstance(symmetry, dict):
        multiplier = 2 if symmetry.get("stellarator_symmetry") is True else 1
        unique_count = symmetry.get("unique_coil_count")
        nfp = symmetry.get("nfp")
        full_count = symmetry.get("full_coil_count")
        if all(
            isinstance(value, int) and not isinstance(value, bool) for value in (unique_count, nfp)
        ):
            expected_full_count = unique_count * nfp * multiplier
            if full_count != expected_full_count:
                errors.append(
                    "symmetry.full_coil_count must match unique_coil_count, nfp, and the "
                    "stellarator-symmetry expansion"
                )
    if isinstance(reference_metrics, dict) and isinstance(symmetry, dict):
        coil_table = reference_metrics.get("coil_table")
        if isinstance(coil_table, dict) and isinstance(coil_table.get("rows"), list):
            if len(coil_table["rows"]) != symmetry.get("unique_coil_count"):
                errors.append(
                    "reference_metrics.coil_table row count must match symmetry.unique_coil_count"
                )
    return errors


def validate_manifest(data: dict[str, Any], base_dir: Path, verify_files: bool = True) -> list[str]:
    """Validate structure and optionally file existence and content hashes."""
    if not isinstance(data, dict):
        return ["manifest must be an object"]
    base_dir = Path(base_dir).resolve()
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")
    schema_version = data.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version
        not in {
            1,
            2,
        }
    ):
        errors.append("schema_version must be 1 or 2")
    kind = data.get("kind")
    if not isinstance(kind, str) or kind not in KINDS:
        errors.append(f"kind must be one of {sorted(KINDS)}")
    if not _is_filled_string(data.get("case_id")):
        errors.append("case_id must be a non-empty string")

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
    resolved_paths: dict[str, Path] = {}
    for index, item in enumerate(files):
        prefix = f"files[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        role = item.get("role")
        if not isinstance(role, str) or role not in FILE_ROLES:
            errors.append(f"{prefix}.role must be one of {sorted(FILE_ROLES)}")
        else:
            if role in seen_roles and schema_version == 2:
                errors.append(f"{prefix}.role duplicates {role}")
            seen_roles.add(role)
            declared_items[role] = item
        relative = item.get("path")
        expected_hash = item.get("sha256")
        valid_path = isinstance(relative, str) and bool(relative.strip())
        if schema_version == 2:
            valid_path = _is_filled_string(relative)
        if not valid_path or not expected_hash:
            errors.append(f"{prefix} must contain path and sha256")
            continue
        try:
            candidate = (base_dir / relative).resolve()
            candidate.relative_to(base_dir)
        except (ValueError, OSError, RuntimeError):
            errors.append(f"{prefix}.path escapes the manifest directory")
            continue
        if isinstance(role, str):
            resolved_paths[role] = candidate
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
            if not isinstance(origin, str) or origin not in {"authoritative", "derived"}:
                errors.append(f"{prefix}.origin must be authoritative or derived")
            elif origin == "authoritative":
                if not _is_absolute_uri(item.get("source_url")):
                    errors.append(f"{prefix}.source_url must identify the authoritative artifact")
            else:
                derived_from = item.get("derived_from")
                if not isinstance(derived_from, list) or not derived_from:
                    errors.append(f"{prefix}.derived_from must be a non-empty role list")
                if not _is_filled_string(item.get("recipe")):
                    errors.append(f"{prefix}.recipe must be a non-empty string")
        if verify_files:
            if not candidate.is_file():
                errors.append(f"{prefix}.path does not exist: {relative}")
            elif sha256_file(candidate) != expected_hash:
                errors.append(f"{prefix}.sha256 does not match: {relative}")
            elif schema_version == 2 and candidate.stat().st_size != item.get("bytes"):
                errors.append(f"{prefix}.bytes does not match: {relative}")

    if schema_version == 2:
        errors.extend(_validate_derived_lineage(declared_items))
        equilibrium_roles = (
            "fixed_boundary_vmec_input",
            "fixed_boundary_vmec_output",
            "free_boundary_vmec_input",
            "free_boundary_vmec_output",
        )
        equilibrium_paths = [
            resolved_paths[role] for role in equilibrium_roles if role in resolved_paths
        ]
        if len(equilibrium_paths) == len(equilibrium_roles) and len(set(equilibrium_paths)) != len(
            equilibrium_paths
        ):
            errors.append("fixed- and free-boundary VMEC artifacts must use distinct paths")

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
