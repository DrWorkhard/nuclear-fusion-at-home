"""Versioned field acceptance from saved coil-check runs: v1 (original) and v2.

acceptance-v2 replaces only the boundary field-error limits with thresholds calibrated
so that the best 10% of a public benchmark pass (docs/validation/ACCEPTANCE_V2.md).
Interior, flux, current, geometry and numerical cross-checks are unchanged. Every
verdict reports v1 and v2 side by side; neither is physical acceptance or Step 4.
"""

import json
from pathlib import Path

import numpy as np

V1 = dict(version="acceptance-v1", boundary_rms_max=1e-4, boundary_max_max=1e-3,
          interior_vector_rms_max=0.01)
# Frozen 2026-10-13. A change needs a new version, never an edit of these values.
V2 = dict(version="acceptance-v2", boundary_mean_max=0.0018, boundary_max_max=0.013,
          interior_vector_rms_max=0.01,
          calibration=dict(dataset="proxima-fusion/coilstellaration",
                           revision="286a268c664938519af6ceacfb4ec8143f64e20e",
                           file="results/eval-part-0.parquet",
                           sha256="5425524969d6ae7f844195e00bae0ec313228aadb27d905549791f6251695a37",
                           statistic="DESC mean and max of |B.n|/|B| on the plasma boundary",
                           cases=8058, passing=820, common_percentile=0.1287))
SHIFTS = (0.0, 0.5)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def boundary_errors(npz_path):
    """Plain mean, maximum and area-weighted RMS of |B.n|/|B| on the saved fine grid."""
    with np.load(npz_path) as data:
        normals = np.asarray(data["normals"], dtype=float).reshape(-1, 3)
        field = np.asarray(data["B"], dtype=float)
    need(field.shape == normals.shape and len(field) > 0, "matching nonempty B and normals")
    weights = np.linalg.norm(normals, axis=1)
    strength = np.linalg.norm(field, axis=1)
    need(np.all(weights > 0) and np.all(strength > 0) and np.isfinite(field).all(),
         "finite nonzero field and normals")
    error = np.abs(np.sum(field*normals, axis=1)/weights)/strength
    return dict(mean=float(error.mean()), max=float(error.max()),
                area_rms=float(np.sqrt(np.sum(weights*error**2)/np.sum(weights))))


def evaluate(run_dir):
    """Return v1 and v2 verdicts for one completed fit or check run directory."""
    run_dir = Path(run_dir)
    report = json.loads((run_dir/"result.json").read_text(encoding="utf-8"))
    need(report.get("completed") is True, "completed run required")
    fine = {round(float(row["shift"]), 1): row for row in report["fine"]}
    need(set(fine) == set(SHIFTS), "fine checks at shifts 0.0 and 0.5 required")
    need(len(report["interior"]) == 3, "three interior levels required")
    boundary = []
    for shift in SHIFTS:
        row, stats = fine[shift], boundary_errors(run_dir/f"fine-{shift:.1f}.npz")
        recorded = row["metrics"]["normal_rms"]
        need(abs(stats["area_rms"]-recorded) <= 1e-9*recorded,
             "saved arrays must reproduce the recorded boundary RMS")
        boundary.append(dict(shift=shift, **stats, checks_pass=bool(row["checks_pass"]),
                             flux_limit_met=bool(row["metrics"]["flux_limit_met"]),
                             current_limit_met=bool(row["metrics"]["current_limit_met"])))
    interior = [float(row["metrics"]["vector_rms"]) for row in report["interior"]]
    shared = dict(
        numerical_checks=all(b["checks_pass"] for b in boundary)
        and all(bool(row["checks_pass"]) for row in report["interior"]),
        flux_and_current=all(b["flux_limit_met"] and b["current_limit_met"] for b in boundary),
        continuous_geometry=report["geometry"]["status"] == "pass")
    interior_pass = max(interior) <= V2["interior_vector_rms_max"]
    v1_boundary = all(b["area_rms"] <= V1["boundary_rms_max"]
                      and b["max"] <= V1["boundary_max_max"] for b in boundary)
    v2_boundary = all(b["mean"] <= V2["boundary_mean_max"]
                      and b["max"] <= V2["boundary_max_max"] for b in boundary)
    return dict(run=str(run_dir), boundary=boundary, interior_vector_rms=interior,
                shared_checks=shared,
                v1=dict(version=V1["version"], boundary=v1_boundary, interior=interior_pass,
                        passed=all(shared.values()) and v1_boundary and interior_pass),
                v2=dict(version=V2["version"], boundary=v2_boundary, interior=interior_pass,
                        passed=all(shared.values()) and v2_boundary and interior_pass),
                physical_admission=False, step4_pass=False)
