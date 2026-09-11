"""Confirm coarse-grid curvature violations using compiled and position-only paths."""

import argparse
import json
from pathlib import Path

import numpy as np
from simsopt import load
from simsopt.geo import CurveXYZFourier

from fusion_baselines.curvature_witness import circumcircle_curvature
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def resample(curve, points):
    coefficients = curve.local_full_x.copy()
    order = (len(coefficients) // 3 - 1) // 2
    refined = CurveXYZFourier(points, order)
    refined.local_full_x = coefficients
    return refined


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    source = root / "evidence/affine-feasibility-v1-holdout.json"
    holdout = json.loads(source.read_text())
    if holdout["status"] != "completed":
        raise ValueError("require completed holdout")
    result = {"schema_version": 1, "retrospective": True, "repository": git_state(root),
              "holdout": reference(source), "protocol": reference(
                  root / "docs/geometry/CURVATURE_ALIASING_AUDIT.md"),
              "code": [reference(p) for p in (Path(__file__),
                  root / "src/fusion_baselines/curvature_witness.py")], "candidates": []}
    for candidate in holdout["candidates"]:
        field_path = Path(candidate["field"]["path"])
        if sha256_file(field_path) != candidate["field"]["sha256"]:
            raise ValueError("candidate hash mismatch")
        curves = [coil.curve for coil in load(str(field_path)).coils[:4]]
        scale = candidate["a0"]
        maxima = {}
        for n in [200, 20000]:
            values = np.array([resample(c, n).kappa() for c in curves]) / scale
            coil, point = np.unravel_index(np.argmax(values), values.shape)
            maxima[str(n)] = {"curvature": float(values[coil, point]),
                             "coil": int(coil), "t": float(point / n)}
        witness = maxima["20000"]
        estimates = []
        for h in [1e-3, 3e-4, 1e-4, 3e-5, 1e-5, 3e-6]:
            parameter = np.mod(witness["t"] + np.array([-h, 0, h]), 1)
            points = resample(curves[witness["coil"]], parameter.tolist()).gamma().copy()
            value = circumcircle_curvature(points) / scale
            estimates.append({"h": h, "parameter": parameter.tolist(),
                              "device_positions": points.tolist(), "curvature_reactor": value,
                              "relative_difference": abs(value / witness["curvature"] - 1)})
        checks = {
            "independent_derivative_maxima_match": all(abs(maxima[str(n)]["curvature"] /
                candidate["geometry"][str(n)]["maximum_curvature_reactor_inverse_m"] - 1)
                <= 1e-10 for n in [200, 20000]),
            "coarse_grid_passes_but_fine_witness_fails": maxima["200"]["curvature"] <= 1
                < witness["curvature"],
            "position_only_estimates_agree_and_violate": all(
                e["relative_difference"] <= 1e-4 and e["curvature_reactor"] > 1
                for e in estimates[-2:]),
        }
        result["candidates"].append({"method": candidate["method"], "field": reference(field_path),
            "a0": scale, "compiled_maxima": maxima, "position_only_estimates": estimates,
            "checks": checks, "violation_confirmed": all(checks.values())})
    result["all_violations_confirmed"] = all(c["violation_confirmed"] for c in result["candidates"])
    write_json_atomic(args.output, result)
    print(json.dumps({"all_violations_confirmed": result["all_violations_confirmed"]}))
    return 0 if result["all_violations_confirmed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
