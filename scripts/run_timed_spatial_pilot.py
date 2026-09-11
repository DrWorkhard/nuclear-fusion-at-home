"""Two-repeat equal-wall-clock pilot using qualified batched spatial derivatives."""

import argparse
import hashlib
import inspect
import json
import time
from pathlib import Path
from unittest.mock import patch

import numpy as np
import qualify_optimization_oracle as runner
from scipy.optimize import least_squares

from fusion_baselines.batched_field_jacobian import batched_field_jacobian
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.spatial_backend import ResidualRepresentation
from fusion_baselines.spatial_flux import normal_weights
from fusion_baselines.timed_oracle import TimedOracle


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    return path


def common_prefix_check(first, second):
    n = min(len(first["evaluations"]), len(second["evaluations"]))
    checks = {
        "nonempty_prefix": n > 0,
        "same_status": first["status"] == second["status"],
        "same_time_stop_reason": first["timing"]["time_denials"]
        == second["timing"]["time_denials"],
        "both_gradients_pass": first["gradient_screen_pass"] and second["gradient_screen_pass"],
        "same_prefix": all(
            a["x_sha256"] == b["x_sha256"]
            and np.allclose(a["values"], b["values"], rtol=1e-12, atol=1e-14)
            for a, b in zip(first["evaluations"][:n], second["evaluations"][:n], strict=True)
        ),
    }
    return {
        "checks": checks,
        "common_prefix_length": n,
        "terminal_counts": [len(a["evaluations"]) for a in (first, second)],
        "pass": all(checks.values()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new timed-study outputs required")
    root = Path(__file__).resolve().parents[1]
    q_path = root / "evidence/spatial-flux-batched-v1-retry1.json"
    qualified = json.loads(q_path.read_text())
    if not qualified["all_pass"] or len(qualified["cases"]) != 2:
        raise ValueError("batched derivative qualification required")
    for source in qualified["code"] + qualified["installed_sources"]:
        checked(source)
    parent_path = root / "evidence/guarded-feasibility-v1/summary.json"
    parent = json.loads(parent_path.read_text())
    solver = Path(inspect.getfile(inspect.unwrap(least_squares)))
    report = {
        "schema_version": 1,
        "repository": git_state(root),
        "host": host_state(),
        "protocol": reference(root / "docs/optimization/TIMED_SPATIAL_PILOT_PROTOCOL.md"),
        "qualification": reference(q_path),
        "parent_study": reference(parent_path),
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/timed_oracle.py"),
            reference(root / "src/fusion_baselines/spatial_backend.py"),
            *qualified["code"],
        ],
        "solver_sources": [
            reference(solver),
            reference(solver.parent / "trf.py"),
            reference(solver.parent / "common.py"),
        ],
        "status": "running",
        "qualification_pass": False,
        "arms": [],
        "methods": ["scalar", "batched"],
        "per_arm_seconds": 300,
        "versions": qualified["versions"],
        "work_counts_exact_for_successful_arms_only": True,
    }
    args.raw.mkdir(parents=True)
    try:
        ctx, backend, preparation = runner.prepare(root, args.raw, guarded_curvature=True)
        report["preparation"] = preparation
        x0 = ctx.Jf.x.copy()
        if (
            backend.names != parent["preparation"]["degrees_of_freedom"]
            or hashlib.sha256(x0.tobytes()).hexdigest()
            != parent["normalization"]["shared_evaluations"][0]["x_sha256"]
        ):
            raise ValueError("initial physical point and basis must match parent")
        backend.scales *= parent["normalization"]["factor"]
        report["normalization"] = {"factor": parent["normalization"]["factor"]}
        start = time.monotonic()
        values, _ = backend(x0)
        points, normal = ctx.Jf.surface.gamma().reshape(-1, 3), ctx.Jf.surface.normal()
        batched_field_jacobian(ctx.Jf.field, ctx.Jf, points, normal_weights(normal))
        report["shared_warmup"] = {
            "full_common_bundles": 1,
            "batched_coil_contractions": 16,
            "geometry_derivative_requests": 32,
            "current_vjp_calls": 16,
            "seconds": time.monotonic() - start,
            "initial_values": values.tolist(),
        }
        checks = {}
        write_json_atomic(args.output / "summary.json", report)
        for representation in report["methods"]:
            directory = args.raw / representation
            directory.mkdir()
            pair = []
            for repeat in (1, 2):
                ctx.Jf.x = x0.copy()
                counted = ResidualRepresentation(
                    backend, spatial=representation == "batched", derivative_method="batched"
                )
                holder = []

                def factory(b, limit, dimension, holder=holder):
                    oracle = TimedOracle(b, limit, dimension, 300.0)
                    holder.append(oracle)
                    return oracle

                output = args.output / f"{representation}-{repeat}.json"
                provenance = {
                    k: v
                    for k, v in report.items()
                    if k not in ("arms", "status", "qualification_pass")
                }
                provenance["representation"] = representation
                print(f"Starting {representation} repeat={repeat}: 300 seconds", flush=True)
                with patch.object(runner, "BudgetedOracle", factory):
                    arm = runner.run_arm(
                        "trf",
                        repeat,
                        counted,
                        ctx,
                        x0,
                        directory,
                        output,
                        provenance,
                        budget=300000,
                        coordinate_scale=0.01,
                    )
                arm["timing"] = holder[0].timing()
                arm["timing"]["early_return_end_to_end_upper_bound"] = (
                    arm["timing"]["time_denials"] == 0
                )
                arm["representation_work"] = counted.work
                arm["original_common_evaluations"] = counted.common_records
                arm["maximum_merit_identity_error"] = counted.max_merit_error
                arm["maximum_gradient_identity_error"] = counted.max_gradient_error
                write_json_atomic(output, arm)
                report["arms"].append(reference(output))
                write_json_atomic(args.output / "summary.json", report)
                if arm["status"] == "error":
                    raise ValueError(f"arm failed: {arm.get('error')}")
                pair.append(arm)
            checks[representation] = common_prefix_check(*pair)
        report.update(
            status="completed",
            repeat_checks=checks,
            qualification_pass=all(c["pass"] for c in checks.values()),
        )
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.output / "summary.json", report)
    print(json.dumps({"qualification_pass": report["qualification_pass"]}))
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
