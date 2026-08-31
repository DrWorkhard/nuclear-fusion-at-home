"""Case-independent extraction of equilibrium metadata from manifest-declared files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import netCDF4
import numpy as np

from fusion_baselines.manifest import validate_manifest
from fusion_baselines.provenance import sha256_file


def _scalar(dataset: netCDF4.Dataset, *names: str) -> float | int | None:
    for name in names:
        if name in dataset.variables:
            return np.asarray(dataset.variables[name][...]).item()
    return None


def _array(dataset: netCDF4.Dataset, *names: str) -> np.ndarray | None:
    for name in names:
        if name in dataset.variables:
            return np.asarray(dataset.variables[name][...])
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
        free_boundary_value = _scalar(dataset, "lfreeb")
        summary = {
            "nfp": _scalar(dataset, "nfp"),
            "mpol": _scalar(dataset, "mpol"),
            "ntor": _scalar(dataset, "ntor"),
            "ns": _scalar(dataset, "ns"),
            "aspect": _scalar(dataset, "aspect"),
            "volume_m3": _scalar(dataset, "volume_p", "volume"),
            "beta_total": _scalar(dataset, "betatotal"),
            "free_boundary": bool(free_boundary_value) if free_boundary_value is not None else None,
        }
        if iota is not None and iota.size:
            finite = iota[np.isfinite(iota)]
            summary["iota_axis"] = float(finite[0]) if finite.size else None
            summary["iota_edge"] = float(finite[-1]) if finite.size else None
            summary["iota_min"] = float(np.min(finite)) if finite.size else None
            summary["iota_max"] = float(np.max(finite)) if finite.size else None
    return summary


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
            comparisons = {}
            for name in ("nfp", "mpol", "ntor", "ns", "free_boundary"):
                comparisons[name] = {
                    "expected": expected[name],
                    "actual": summary[name],
                    "matches": expected[name] == summary[name],
                }
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
    if boozer_path is not None:
        result["boozer"] = _boozer_summary(boozer_path)
    return result
