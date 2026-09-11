"""Additional frozen native-metric/linking screens for both direct-pilot candidates."""

import argparse
import inspect
import json
from pathlib import Path

import numpy as np
from simsopt import load
from simsopt.field import coils_via_symmetries
from simsopt.geo import ArclengthVariation, CurveXYZFourier, LinkingNumber, MeanSquaredCurvature

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError("input hash mismatch")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("holdout", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(__file__).resolve().parents[1]
    holdout = json.loads(args.holdout.read_text())
    study = json.loads(checked(holdout["study"]).read_text())
    if (
        holdout["status"] != "completed"
        or not holdout["all_repeats"]
        or study["status"] != "completed"
        or not study["qualification_pass"]
        or len(holdout["candidates"]) != 2
    ):
        raise ValueError("completed all-repeat holdout required")
    thresholds = study["preparation"]["thresholds"]
    result = {
        "schema_version": 1,
        "repository": git_state(root),
        "holdout": reference(args.holdout),
        "protocol": reference(root / "docs/optimization/DIRECT_SLSQP_PILOT_PROTOCOL.md"),
        "code": reference(Path(__file__)),
        "thresholds": thresholds,
        "native_sources": [
            reference(Path(inspect.getfile(cls))) for cls in (MeanSquaredCurvature, CurveXYZFourier)
        ],
        "candidates": [],
        "status": "running",
        "full_engineering_admission": False,
        "used_for_optimizer_feedback": False,
    }
    try:
        for candidate in holdout["candidates"]:
            field = load(str(checked(candidate["field"])))
            if len(field.coils) != 16:
                raise ValueError("sixteen physical coils required")
            levels = []
            for resolution in (200, 800, 3200):
                curves = []
                for coil in field.coils[:4]:
                    original = coil.curve
                    order = (len(original.local_full_x) // 3 - 1) // 2
                    curve = CurveXYZFourier(resolution, order)
                    curve.local_full_x = original.local_full_x.copy()
                    curves.append(curve)
                level = {
                    "resolution": resolution,
                    "msc": [float(MeanSquaredCurvature(c).J()) for c in curves],
                    "arclength_variation": [float(ArclengthVariation(c).J()) for c in curves],
                }
                if resolution in (200, 800):
                    coils = coils_via_symmetries(
                        curves,
                        [c.current for c in field.coils[:4]],
                        2,
                        True,
                        regularizations=[c.regularization for c in field.coils[:4]],
                    )
                    level["linking_number"] = float(LinkingNumber([c.curve for c in coils]).J())
                levels.append(level)
            checks = {}
            for metric, threshold_key in (
                ("msc", "msc_threshold"),
                ("arclength_variation", "arclength_variation_threshold"),
            ):
                values = np.asarray([level[metric] for level in levels])
                checks[metric + "_finite"] = bool(np.all(np.isfinite(values)))
                checks[metric + "_all_levels_pass"] = bool(
                    np.all(values <= thresholds[threshold_key])
                )
                error = np.abs(values[-1] - values[-2]) / np.maximum(1.0, np.abs(values[-1]))
                checks[metric + "_refinement"] = bool(np.max(error) <= 1e-6)
            checks["linking_zero_all_levels"] = all(
                level["linking_number"] == 0 for level in levels[:2]
            )
            result["candidates"].append(
                {
                    "method": candidate["method"],
                    "field": candidate["field"],
                    "levels": levels,
                    "checks": checks,
                    "pass": all(checks.values()),
                }
            )
            write_json_atomic(args.output, result)
        result.update(status="completed", all_pass=all(c["pass"] for c in result["candidates"]))
    except Exception as error:
        result.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
