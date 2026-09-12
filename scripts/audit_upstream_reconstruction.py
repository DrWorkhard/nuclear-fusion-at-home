"""Recheck static source identity, cached fields and fixed admission arithmetic."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_field_state import serialized_state


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"input hash mismatch: {path}")
    return path


def replay_field(points, positions, tangents, currents):
    """Explicit component sum, not the production field helper or native library."""
    result = np.zeros_like(points)
    for i, point in enumerate(points):
        dx = point[None, None, :] - positions
        r2 = np.sum(dx * dx, axis=2)
        if np.any(r2 <= 0) or not np.isfinite(r2).all():
            raise ValueError("invalid source/observation displacement")
        denominator = r2**1.5
        for axis in range(3):
            j, k = (axis + 1) % 3, (axis + 2) % 3
            numerator = tangents[:, :, j] * dx[:, :, k] - tangents[:, :, k] * dx[:, :, j]
            result[i, axis] = (
                1e-7 * np.sum(currents[:, None] * numerator / denominator) / positions.shape[1]
            )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit required")
    root = Path(__file__).resolve().parents[1]
    study = json.loads(args.study.read_text())
    inventory = json.loads(checked(study["inventory"]).read_text())
    if study["status"] != "completed" or len(study["candidates"]) != 5:
        raise ValueError("complete fixed five-candidate reconstruction required")
    if [c["source_metadata"]["path"] for c in study["candidates"]] != inventory["shortlist"]:
        raise ValueError("selected source identity/order changed")
    records = []
    for candidate in study["candidates"]:
        checked(candidate["source_metadata"])
        before = serialized_state(json.loads(checked(candidate["source_field"]).read_text()))
        after = serialized_state(json.loads(checked(candidate["field"]).read_text()))
        checks = {f"unchanged_{key}": np.array_equal(before[key], after[key]) for key in before}
        checks["saved_source_identity"] = candidate["status"] == "completed" and all(
            candidate["identity_checks"].values()
        )
        checks["two_crosschecks"] = [r["resolution"] for r in candidate["independent_fields"]] == [
            200,
            800,
        ]
        checks["saved_fields"] = True
        comparisons = []
        for row in candidate["independent_fields"]:
            with np.load(checked(row["arrays"]), allow_pickle=False) as data:
                own = replay_field(
                    data["points"], data["positions"], data["tangents"], data["currents"]
                )
                native, saved = data["native"], data["independent"]
                denominator = np.maximum(1, np.linalg.norm(native, axis=1))
                error = float(np.max(np.linalg.norm(own - native, axis=1) / denominator))
                repeat_error = float(np.max(np.linalg.norm(own - saved, axis=1) / denominator))
                original_error = float(np.max(np.linalg.norm(saved - native, axis=1) / denominator))
                checks["saved_fields"] &= bool(
                    own.shape == native.shape == (64, 3)
                    and np.isfinite(own).all()
                    and error <= 1e-12
                    and repeat_error <= 1e-12
                    and original_error == row["maximum_normalized_error"]
                    and row["all_pass"] is True
                    and np.array_equal(data["currents"], before["currents"])
                )
                comparisons.append(
                    dict(
                        resolution=row["resolution"],
                        native_normalized_error=error,
                        saved_numpy_normalized_error=repeat_error,
                    )
                )
        flux = candidate["flux"]
        checks["all_grids"] = bool(
            [(r["surface_resolution"], r["coil_quadrature"]) for r in flux]
            == [(32, 200), (64, 200), (128, 200), (128, 800)]
            and sorted(map(int, candidate["geometry"])) == [200, 1000, 5000, 20000]
            and sorted(map(int, candidate["coil_coil"])) == [200, 1000, 5000, 20000]
            and sorted(map(int, candidate["coil_plasma"])) == [64, 128, 256, 512]
        )
        f = [r["unthresholded_quadratic_flux"] for r in flux]
        expected = dict(
            flux_cut_in=f[3] <= 1e-8,
            surface_flux_refinement=abs(f[2] - f[1]) <= max(1e-10, 0.01 * f[1]),
            coil_flux_refinement=abs(f[3] - f[2]) <= max(1e-10, 0.01 * f[2]),
            length=candidate["geometry"]["20000"]["unique_total_length_reactor_m"] <= 220,
            curvature=candidate["geometry"]["20000"]["maximum_curvature_reactor_inverse_m"] <= 1,
            coil_coil_clearance=candidate["coil_coil"]["20000"]["centerline_distance_reactor_m"]
            >= 1.06,
            coil_plasma_clearance=candidate["coil_plasma"]["512"] >= 1.3,
        )
        checks["reported_admission_arithmetic"] = (
            expected == candidate["checks"]
            and all(expected.values()) == candidate["bounded_geometry_flux_screen_pass"]
            and np.isfinite(f).all()
            and min(f) >= 0
        )
        checks = {key: bool(value) for key, value in checks.items()}
        records.append(
            dict(
                field=candidate["field"],
                checks=checks,
                all_pass=all(checks.values()),
                field_replays=comparisons,
            )
        )
    result = dict(
        repository=git_state(root),
        source=dict(path=str(args.study.resolve()), sha256=sha256_file(args.study)),
        candidates=records,
        all_pass=all(r["all_pass"] for r in records),
        new_native_B_calls=0,
        cached_quadrature_field_replays=10,
        physical_feasibility_certified=False,
        code=[
            dict(path=str(path.resolve()), sha256=sha256_file(path))
            for path in (Path(__file__), root / "src/fusion_baselines/serialized_field_state.py")
        ],
        scope="source_parameters_cached_field_arrays_and_admission_arithmetic_not_new_fine_geometry",
    )
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
