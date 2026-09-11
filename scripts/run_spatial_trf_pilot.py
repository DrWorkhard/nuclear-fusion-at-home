"""Controlled short TRF pilot; equal proposal cap, explicitly unequal derivative work."""

import argparse
import hashlib
import inspect
import json
from pathlib import Path

from qualify_optimization_oracle import prepare, repeat_check, run_arm
from scipy.optimize import least_squares

from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.spatial_backend import ResidualRepresentation


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("pilot outputs must be new")
    root = Path(__file__).resolve().parents[1]
    old_path = root / "evidence/guarded-feasibility-v1/summary.json"
    old = json.loads(old_path.read_text())
    q_path = root / "evidence/spatial-flux-local-vjp-v1.json"
    qualified = json.loads(q_path.read_text())
    if not qualified["all_pass"] or len(qualified["cases"]) != 2:
        raise ValueError("local-point spatial qualification required")
    for source in qualified["code"] + qualified["installed_sources"]:
        checked(source)
    solver = Path(inspect.getfile(inspect.unwrap(least_squares)))
    report = {"schema_version": 1, "repository": git_state(root), "host": host_state(),
        "protocol": reference(root / "docs/SPATIAL_TRF_PILOT_PROTOCOL.md"),
        "qualification": reference(q_path), "parent_study": reference(old_path),
        "code": [reference(Path(__file__)),
            reference(root / "src/fusion_baselines/spatial_backend.py"), *qualified["code"]],
        "solver_sources": [reference(solver), reference(solver.parent / "trf.py"),
                           reference(solver.parent / "common.py")],
        "status": "running", "qualification_pass": False, "arms": [],
        "methods": ["scalar", "spatial"], "equal_computational_work": False,
        "work_count_interpretation": "Exact on success; spatial row calls precharged as an "
                                     "upper bound if row assembly fails.",
        "versions": qualified["versions"]}
    args.raw.mkdir(parents=True)
    try:
        ctx, backend, preparation = prepare(root, args.raw, guarded_curvature=True)
        report["preparation"] = preparation
        x0 = ctx.Jf.x.copy()
        # No extra deserialization before prepare; require exact source basis, not an assumption.
        if (preparation["degrees_of_freedom"] != old["preparation"]["degrees_of_freedom"]
                or hashlib.sha256(x0.tobytes()).hexdigest()
                != old["normalization"]["shared_evaluations"][0]["x_sha256"]):
            raise ValueError("initial physical point/basis does not match the frozen parent")
        backend.scales *= old["normalization"]["factor"]
        report["normalization"] = {"factor": old["normalization"]["factor"],
                                   "source": reference(old_path), "additional_shared_bundles": 0}
        checks = {}
        write_json_atomic(args.output / "summary.json", report)
        for representation in report["methods"]:
            directory = args.raw / representation
            directory.mkdir()
            pair = []
            for repeat in (1, 2):
                ctx.Jf.x = x0.copy()
                counted = ResidualRepresentation(backend, spatial=representation == "spatial")
                output = args.output / f"{representation}-{repeat}.json"
                provenance = {k: v for k, v in report.items()
                              if k not in ("arms", "status", "qualification_pass")}
                provenance["representation"] = representation
                print(f"Starting {representation} repeat={repeat}", flush=True)
                arm = run_arm("trf", repeat, counted, ctx, x0, directory, output, provenance,
                              budget=128, coordinate_scale=0.01)
                arm["representation_work"] = counted.work
                arm["original_common_evaluations"] = counted.common_records
                arm["maximum_merit_identity_error"] = counted.max_merit_error
                arm["maximum_gradient_identity_error"] = counted.max_gradient_error
                write_json_atomic(output, arm)
                report["arms"].append(reference(output))
                write_json_atomic(args.output / "summary.json", report)
                if arm["status"] == "error":
                    raise ValueError(f"pilot arm failed: {arm.get('error')}")
                pair.append(arm)
            checks[representation] = repeat_check(*pair)
            checks[representation]["same_derivative_work"] = all(
                pair[0]["representation_work"][key] == pair[1]["representation_work"][key]
                for key in ("common_bundles", "extra_single_point_B_calls",
                            "extra_single_point_VJP_calls", "extra_full_field_requests"))
        report.update(status="completed", repeat_checks=checks,
                      qualification_pass=all(all(c.values()) for c in checks.values()))
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.output / "summary.json", report)
    print(json.dumps({"qualification_pass": report["qualification_pass"]}))
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
