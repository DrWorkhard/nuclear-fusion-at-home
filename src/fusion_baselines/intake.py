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
        summary = {
            "nfp": _scalar(dataset, "nfp"),
            "mpol": _scalar(dataset, "mpol"),
            "ntor": _scalar(dataset, "ntor"),
            "ns": _scalar(dataset, "ns"),
            "aspect": _scalar(dataset, "aspect"),
            "volume_m3": _scalar(dataset, "volume_p", "volume"),
            "beta_total": _scalar(dataset, "betatotal"),
            "free_boundary": bool(_scalar(dataset, "lfreeb")),
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


def summarize_equilibrium_manifest(
    manifest: dict[str, Any], data_root: Path
) -> dict[str, Any]:
    """Validate and summarize a VMEC equilibrium without case-id dispatch."""
    errors = validate_manifest(manifest, data_root)
    if errors:
        raise ValueError("Invalid manifest: " + "; ".join(errors))
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
    boozer_path = _file_for_role(manifest, "boozer_output", data_root)
    files = {
        item["role"]: {
            "path": str((data_root / item["path"]).resolve()),
            "sha256": sha256_file((data_root / item["path"]).resolve()),
        }
        for item in manifest["files"]
    }
    result = {
        "schema_version": 1,
        "case_id": manifest["case_id"],
        "kind": manifest["kind"],
        "source": manifest["source"],
        "conventions": manifest["conventions"],
        "files": files,
        "vmec": vmec,
        "expected_actual": comparisons,
        "expected_metadata_matches": all(item["matches"] for item in comparisons.values()),
    }
    if boozer_path is not None:
        result["boozer"] = _boozer_summary(boozer_path)
    return result
