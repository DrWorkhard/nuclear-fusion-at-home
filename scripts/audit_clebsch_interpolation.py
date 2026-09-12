"""Independently recompute endpoint interpolation, products and recorded residual norms."""

import argparse
import json
from pathlib import Path

import numpy as np
from audit_qi_clebsch import checked, reference

from fusion_baselines.provenance import git_state, write_json_atomic


def verify_terms(g, b, h, t, psi, stored):
    def blend(v):
        return (1 - t) * v[0] + t * v[1]

    node = g * b - psi * h
    average = blend(node)
    actual = blend(g) * blend(b) - psi * blend(h)
    scale = max(abs(psi), float(np.max(abs(psi * h))))
    expected = dict(nodes=node, average=average, correction=actual - average, prediction=actual)
    return all(
        np.isfinite(value).all()
        and np.shape(value) == np.shape(stored[key])
        and float(np.max(abs(value - stored[key]))) / scale <= 1e-12
        for key, value in expected.items()
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit output required")
    root = Path(__file__).resolve().parents[1]
    report = json.loads(args.source.read_text())
    original = json.loads(checked(report["source"]).read_text())
    for ref in [report["protocol"], *report["code"]]:
        checked(ref)
    if (report["status"] != "completed" or len(report["grids"]) != 24
            or len(original["grids"]) != 24):
        raise ValueError("completed full24-grid set required")
    rows = []
    for row, old_row in zip(report["grids"], original["grids"], strict=True):
        if (
            any(row[k] != old_row[k] for k in ("case", "surface", "resolution"))
            or row["original_arrays"] != old_row["arrays"]
        ):
            raise ValueError("original ordered grid identity changed")
        checks = {}
        with (
            np.load(checked(row["arrays"]), allow_pickle=False) as data,
            np.load(checked(row["original_arrays"]), allow_pickle=False) as old,
        ):
            t, psi = data["fraction"].item(), data["psi"].item()
            checks["weight"] = t == row["metadata"]["fraction"] and 0 <= t <= 1
            checks["flux"] = psi == old["psi"].item()
            replay = {
                k: float(np.max(abs((1 - t) * data[k][0] + t * data[k][1] - old[k])))
                / max(1, float(np.max(abs(old[k]))))
                for k in ("g", "bt", "bp", "lt", "lp", "iota")
            }
            checks["point_replay"] = (
                max(replay.values()) <= 1e-12 and replay == row["replay_errors"]
            )
            for component, bkey in (("poloidal", "bt"), ("toroidal", "bp")):
                h = data["iota"] - data["lp"] if bkey == "bt" else 1 + data["lt"]
                old_h = old["iota"] - old["lp"] if bkey == "bt" else 1 + old["lt"]
                norm = max(abs(psi) if bkey == "bt" else 0, float(np.max(abs(psi * old_h))))
                stored = {
                    key: data[f"{component}_{key}"]
                    for key in ("nodes", "average", "correction", "prediction")
                }
                checks[f"{component}_terms"] = verify_terms(
                    data["g"], data[bkey], h, t, psi, stored
                )
                actual_old = old["g"] * old[bkey] - psi * old_h
                node_errors = [
                    float(np.max(abs(v)))
                    / max(abs(psi) if bkey == "bt" else 0, float(np.max(abs(psi * hn))))
                    for v, hn in zip(stored["nodes"], h, strict=True)
                ]
                actual = dict(
                    replay_error=float(np.max(abs(stored["prediction"] - actual_old))) / norm,
                    old_residual_norm=float(np.max(abs(actual_old))) / norm,
                    node_errors=node_errors,
                    node_screen_pass=all(v <= 1e-3 for v in node_errors),
                    average_node_norm=float(np.max(abs(stored["average"]))) / norm,
                    product_correction_norm=float(np.max(abs(stored["correction"]))) / norm,
                )
                checks[f"{component}_records"] = actual == row["components"][
                    component
                ] and np.array_equal(actual_old, data[f"{component}_original"])
                checks[f"{component}_replay"] = actual["replay_error"] <= 1e-12
        rows.append(
            dict(
                case=row["case"],
                surface=row["surface"],
                resolution=row["resolution"],
                checks={k: bool(v) for k, v in checks.items()},
                all_pass=all(checks.values()),
            )
        )
    result = dict(
        repository=git_state(root),
        source=reference(args.source),
        grids=rows,
        all_pass=all(r["all_pass"] for r in rows),
        new_field_evaluations=0,
        physical_screen_reclassified=False,
        absolute_drift_certified=False,
        code=reference(Path(__file__)),
    )
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
