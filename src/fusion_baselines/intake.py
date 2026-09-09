"""Case-independent extraction of equilibrium metadata from manifest-declared files."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import netCDF4
import numpy as np

from fusion_baselines.manifest import validate_manifest
from fusion_baselines.provenance import sha256_file


def _scalar(dataset: netCDF4.Dataset, *names: str) -> float | int | None:
    for name in names:
        if name in dataset.variables:
            value = np.ma.asarray(dataset.variables[name][...])
            if value.size != 1 or np.ma.is_masked(value):
                return None
            result = value.item()
            if isinstance(result, (int, float)) and not math.isfinite(result):
                return None
            return result.item() if isinstance(result, np.generic) else result
    return None


def _array(dataset: netCDF4.Dataset, *names: str) -> np.ndarray | None:
    for name in names:
        if name in dataset.variables:
            return np.asarray(
                np.ma.asarray(dataset.variables[name][...], dtype=float).filled(np.nan)
            )
    return None


def _file_for_role(manifest: dict[str, Any], role: str, data_root: Path) -> Path | None:
    matches = [item for item in manifest["files"] if item["role"] == role]
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError(f"Manifest has multiple {role!r} files")
    return (data_root / matches[0]["path"]).resolve()


def _vmec_summary(path: Path) -> dict[str, Any]:
    with netCDF4.Dataset(path) as dataset:
        iota = _array(dataset, "iotaf", "iotas")
        free_boundary_value = _scalar(dataset, "lfreeb__logical__", "lfreeb")
        summary = {
            "nfp": _scalar(dataset, "nfp"),
            "mpol": _scalar(dataset, "mpol"),
            "ntor": _scalar(dataset, "ntor"),
            "ns": _scalar(dataset, "ns"),
            "aspect": _scalar(dataset, "aspect"),
            "volume_m3": _scalar(dataset, "volume_p", "volume"),
            "beta_total": _scalar(dataset, "betatotal"),
            "version": _scalar(dataset, "version_"),
            "ier_flag": _scalar(dataset, "ier_flag"),
            "fsqr": _scalar(dataset, "fsqr"),
            "fsqz": _scalar(dataset, "fsqz"),
            "fsql": _scalar(dataset, "fsql"),
            "free_boundary": (bool(free_boundary_value) if free_boundary_value in (0, 1) else None),
        }
        if iota is not None and iota.size:
            finite = iota[np.isfinite(iota)]
            summary["iota_profile"] = [
                float(value) if np.isfinite(value) else None for value in iota
            ]
            summary["iota_axis"] = float(finite[0]) if finite.size else None
            summary["iota_edge"] = float(finite[-1]) if finite.size else None
            summary["iota_min"] = float(np.min(finite)) if finite.size else None
            summary["iota_max"] = float(np.max(finite)) if finite.size else None
    return summary


def _version_matches(expected: object, actual: object) -> bool:
    if actual is None:
        return False
    try:
        return math.isclose(float(expected), float(actual), rel_tol=0.0, abs_tol=1e-12)
    except (TypeError, ValueError):
        return str(expected).strip() == str(actual).strip()


def _comparison(expected: object, actual: object, matches: bool | None = None) -> dict[str, Any]:
    return {
        "expected": expected,
        "actual": actual,
        "matches": expected == actual if matches is None else matches,
    }


def _squid_equilibrium_checks(
    manifest: dict[str, Any],
    equilibrium_name: str,
    summary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    expected = manifest["equilibria"][equilibrium_name]
    checks = {
        name: _comparison(expected[name], summary[name]) for name in ("nfp", "mpol", "ntor", "ns")
    }
    checks["version"] = _comparison(
        expected["version"],
        summary["version"],
        _version_matches(expected["version"], summary["version"]),
    )
    checks["free_boundary"] = _comparison(expected["free_boundary"], summary["free_boundary"])
    checks["normal_termination"] = _comparison(0, summary["ier_flag"])
    for residual, tolerance in expected["convergence_tolerances"].items():
        actual = summary.get(residual)
        matches = (
            isinstance(actual, (int, float))
            and not isinstance(actual, bool)
            and math.isfinite(actual)
            and 0 <= actual <= tolerance
        )
        checks[residual] = _comparison(f"0 <= value <= {tolerance}", actual, matches)
    return checks


def _squid_reference_checks(
    manifest: dict[str, Any], summary: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    metrics = manifest["reference_metrics"]
    beta_metric = metrics["volume_averaged_beta"]
    beta_interval = beta_metric["acceptance_interval"]
    beta = summary["beta_total"]
    beta_matches = (
        isinstance(beta, (int, float))
        and not isinstance(beta, bool)
        and math.isfinite(beta)
        and beta_interval[0] <= beta
        and (
            beta < beta_interval[1] if beta_metric["upper_exclusive"] else beta <= beta_interval[1]
        )
    )

    iota_metric = metrics["iota_profile"]
    expected_iota = np.asarray(iota_metric["value"], dtype=float)
    actual_iota = np.asarray(summary.get("iota_profile", []), dtype=float)
    same_shape = expected_iota.shape == actual_iota.shape
    max_iota_error = (
        float(np.max(np.abs(actual_iota - expected_iota)))
        if same_shape and actual_iota.size
        else None
    )
    iota_matches = (
        max_iota_error is not None
        and math.isfinite(max_iota_error)
        and max_iota_error <= iota_metric["absolute_tolerance"]
    )
    return {
        "volume_averaged_beta": {
            "expected_interval": beta_interval,
            "upper_exclusive": beta_metric["upper_exclusive"],
            "actual": beta,
            "matches": beta_matches,
        },
        "iota_profile": {
            "expected_points": int(expected_iota.size),
            "actual_points": int(actual_iota.size),
            "absolute_tolerance": iota_metric["absolute_tolerance"],
            "max_absolute_error": max_iota_error,
            "matches": iota_matches,
        },
    }


def _boozer_summary(path: Path) -> dict[str, Any]:
    with netCDF4.Dataset(path) as dataset:
        modes = _array(dataset, "ixm_b")
        return {
            "nfp": _scalar(dataset, "nfp_b", "nfp"),
            "ns": _scalar(dataset, "ns_b", "ns"),
            "mode_count": int(modes.size) if modes is not None else None,
        }


def summarize_equilibrium_manifest(manifest: dict[str, Any], data_root: Path) -> dict[str, Any]:
    """Validate and summarize a VMEC equilibrium without case-id dispatch."""
    errors = validate_manifest(manifest, data_root)
    if errors:
        raise ValueError("Invalid manifest: " + "; ".join(errors))
    if manifest.get("schema_version") == 2 and manifest.get("kind") == "squid_c":
        equilibrium_summaries = {}
        comparisons_by_equilibrium = {}
        for equilibrium_name in ("fixed_boundary", "coil_generated_free_boundary"):
            expected = manifest["equilibria"][equilibrium_name]
            output_role = expected["output_role"]
            wout = _file_for_role(manifest, output_role, data_root)
            if wout is None:
                raise ValueError(f"Manifest has no {output_role}")
            summary = _vmec_summary(wout)
            comparisons = _squid_equilibrium_checks(manifest, equilibrium_name, summary)
            equilibrium_summaries[equilibrium_name] = summary
            comparisons_by_equilibrium[equilibrium_name] = comparisons
        primary_name = "coil_generated_free_boundary"
        vmec = equilibrium_summaries[primary_name]
        comparisons = comparisons_by_equilibrium[primary_name]
        all_metadata_matches = all(
            check["matches"]
            for equilibrium in comparisons_by_equilibrium.values()
            for check in equilibrium.values()
        )
        reference_checks = _squid_reference_checks(manifest, vmec)
    else:
        wout = _file_for_role(manifest, "vmec_output", data_root)
        if wout is None:
            raise ValueError("Manifest has no vmec_output")
        vmec = _vmec_summary(wout)
        expected = manifest.get("equilibrium", {})
        comparisons = {}
        for name in ("nfp", "mpol", "ntor", "ns", "free_boundary"):
            if name in expected:
                comparisons[name] = {
                    "expected": expected[name],
                    "actual": vmec[name],
                    "matches": expected[name] == vmec[name],
                }
        all_metadata_matches = all(item["matches"] for item in comparisons.values())
    boozer_path = _file_for_role(manifest, "boozer_output", data_root)
    files = {}
    for item in manifest["files"]:
        resolved_path = (data_root / item["path"]).resolve()
        record = {
            "path": str(resolved_path),
            "sha256": sha256_file(resolved_path),
            "bytes": resolved_path.stat().st_size,
        }
        for name in ("origin", "source_url", "derived_from", "recipe"):
            if name in item:
                record[name] = item[name]
        files[item["role"]] = record
    result = {
        "schema_version": 1,
        "evaluation_code": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__)),
        },
        "manifest_schema_version": manifest["schema_version"],
        "case_id": manifest["case_id"],
        "kind": manifest["kind"],
        "source": manifest["source"],
        "conventions": manifest["conventions"],
        "files": files,
        "vmec": vmec,
        "expected_actual": comparisons,
        "expected_metadata_matches": all_metadata_matches,
    }
    if manifest.get("schema_version") == 2 and manifest.get("kind") == "squid_c":
        result["equilibria"] = equilibrium_summaries
        result["expected_actual_by_equilibrium"] = comparisons_by_equilibrium
        result["scale"] = manifest["scale"]
        result["symmetry"] = manifest["symmetry"]
        result["reference_metrics"] = manifest["reference_metrics"]
        result["reference_checks"] = reference_checks
        result["intake_checks_pass"] = all_metadata_matches and all(
            check["matches"] for check in reference_checks.values()
        )
        result["scientific_admission_pass"] = False
        result["unevaluated_scientific_checks"] = [
            "input/output lineage and canonical equilibrium state confirmation",
            "coil reconstruction and normal-field error quadrature",
            "coil geometry table, profiles, scale and signed-current conventions",
            "QI objective, maximum-J and finite-pressure validation",
        ]
    if boozer_path is not None:
        result["boozer"] = _boozer_summary(boozer_path)
    return result
