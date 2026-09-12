"""Two frozen complete-bundle SLSQP construction arms; no physical holdout feedback."""

import argparse
import inspect
import json
import os
import time
from pathlib import Path

import numpy as np
from qualify_optimization_oracle import prepare
from scipy.optimize import minimize
from scipy.optimize._slsqp_py import _minimize_slsqp
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.affine_coordinates import AffineCoordinates
from fusion_baselines.budgeted_oracle import BudgetExhausted
from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.inequality_oracle import InequalityOracle
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"qualification input/code mismatch: {path}")
    return path


def run_arm(backend, ctx, x0, directory, output, repeat, *, budget=256):
    directory.mkdir()
    ctx.Jf.x = x0.copy()
    backend.work = dict.fromkeys(backend.work, 0)
    coordinates = AffineCoordinates(x0, 0.01)
    oracle = InequalityOracle(backend.evaluate, budget, len(x0), 137, tolerance=1e-8)
    record = {
        "method": "slsqp",
        "representation": "direct",
        "repeat": repeat,
        "status": "running",
        "coordinate_scale": 0.01,
        "selection_tolerance": 1e-8,
        "gradient_screen_pass": False,
    }
    started, checkpoint_count = time.monotonic(), 0

    def checkpoint():
        record.update(
            counters=oracle.counters(),
            evaluations=oracle.records,
            work=dict(backend.work),
            elapsed_seconds=time.monotonic() - started,
        )
        write_json_atomic(output, record)

    def request(x):
        nonlocal checkpoint_count
        result = oracle.evaluate(x)
        if len(oracle.records) // 25 > checkpoint_count:
            checkpoint_count = len(oracle.records) // 25
            print(
                f"SLSQP repeat={repeat} bundles={len(oracle.records)} "
                f"best={oracle.best['selection_key']}",
                flush=True,
            )
            checkpoint()
        return result

    def objective(y):
        values, jacobian = request(coordinates.physical(y))
        return values[0], coordinates.gradient(jacobian[0])

    def constraints(y):
        return request(coordinates.physical(y))[0][1:]

    def jac_constraints(y):
        return 0.01 * request(coordinates.physical(y))[1][1:]

    try:
        _, jacobian = request(x0)
        direction = np.random.default_rng(46).normal(size=len(x0))
        direction /= np.linalg.norm(direction)
        exact, screens = jacobian @ direction, []
        for eps in (1e-5, 1e-6, 1e-7, 1e-8):
            plus = request(x0 + eps * direction)[0]
            minus = request(x0 - eps * direction)[0]
            fd = (plus - minus) / (2 * eps)
            error = np.abs(fd - exact) / np.maximum(1.0, np.abs(exact))
            screens.append(
                {
                    "eps": eps,
                    "normalized_errors": error.tolist(),
                    "finite_difference": fd.tolist(),
                    "analytic": exact.tolist(),
                }
            )
        record["gradient_checks"] = screens
        record["gradient_screen_pass"] = bool(max(screens[-1]["normalized_errors"]) <= 1e-6)
        if not record["gradient_screen_pass"]:
            raise ValueError("initial physical gradient screen failed")
        solution = minimize(
            objective,
            np.zeros_like(x0),
            method="SLSQP",
            jac=True,
            constraints={"type": "ineq", "fun": constraints, "jac": jac_constraints},
            options={"ftol": 1e-10, "maxiter": 100000, "disp": False},
        )
        record.update(
            status="solver_returned",
            stop_reason="solver_returned",
            solver={
                "success": bool(solution.success),
                "status": int(solution.status),
                "message": str(solution.message),
                "nit": int(solution.nit),
                "nfev": int(solution.nfev),
                "njev": int(solution.njev),
                "physical_terminal_x": coordinates.physical(solution.x).tolist(),
            },
        )
    except BudgetExhausted:
        record.update(status="budget_exhausted", stop_reason="proposal_cap")
    except Exception as error:
        record.update(status="error", stop_reason="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        if oracle.best is not None:
            best = oracle.best
            ctx.Jf.x = best["x"].copy()
            path = directory / "best.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, x=best["x"], values=best["values"])
            field_path = directory / "best_field.json"
            ctx.Jf.field.save(str(field_path))
            record["best"] = {
                k: best[k]
                for k in (
                    "attempt",
                    "x_sha256",
                    "objective",
                    "maximum_violation",
                    "construction_screen_pass",
                    "selection_key",
                    "metrics",
                )
            }
            record["best"].update(arrays=reference(path), field=reference(field_path))
        checkpoint()
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--budget-1024", action="store_true")
    args = parser.parse_args()
    if args.study.exists() or args.raw.exists():
        raise FileExistsError("new immutable study paths required")
    root = Path(__file__).resolve().parents[1]
    budget = 1024 if args.budget_1024 else 256
    qualification_path = root / "evidence/direct-inequality-qualification-v1.json"
    qualification = json.loads(qualification_path.read_text())
    if qualification["status"] != "completed" or not qualification["all_pass"]:
        raise ValueError("passing direct qualification required")
    for ref in qualification["code"] + qualification["installed_sources"]:
        checked(ref)
    source = json.loads(checked(qualification["source_study"]).read_text())
    report = {
        "schema_version": 1,
        "repository": git_state(root),
        "host": host_state(),
        "protocol": reference(root / (
            "docs/optimization/DIRECT_SLSQP_1024_PROTOCOL.md" if args.budget_1024
            else "docs/optimization/DIRECT_SLSQP_PILOT_PROTOCOL.md")),
        "qualification": reference(qualification_path),
        "status": "running",
        "qualification_pass": False,
        "methods": ["slsqp"],
        "arms": [],
        "code": [
            reference(root / p)
            for p in (
                "scripts/run_direct_slsqp_pilot.py",
                "src/fusion_baselines/inequality_oracle.py",
                "src/fusion_baselines/affine_coordinates.py",
            )
        ],
        "qualified_backend_code": qualification["code"],
        "solver_source": reference(Path(inspect.getfile(inspect.unwrap(_minimize_slsqp)))),
        "solver_options": {
            "method": "SLSQP",
            "ftol": 1e-10,
            "maxiter": 100000,
            "jacobian": "analytic",
            "bundle_limit": budget,
        },
        "thread_environment": {
            name: os.environ.get(name)
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
    }
    args.study.mkdir(parents=True)
    args.raw.mkdir(parents=True)
    try:
        ctx, _, preparation = prepare(root, args.raw, guarded_curvature=True)
        if any(
            preparation[key] != source["preparation"][key]
            for key in ("thresholds", "degrees_of_freedom", "guarded_search_targets")
        ):
            raise ValueError("original physical setup changed")
        full = SurfaceRZFourier.from_vmec_input(
            str(checked(preparation["surface"])), range="full torus", nphi=64, ntheta=64
        )
        backend = DirectConstraintBackend(ctx, full, flux_scale=1e-6)
        x0 = ctx.Jf.x.copy()
        case = next(c for c in qualification["cases"] if c["name"] == "original")
        with np.load(checked(case["arrays"]), allow_pickle=False) as saved:
            perm = np.argsort(qualification["source_indices_in_target_order"])
            if not np.array_equal(x0, saved["x"][perm]):
                raise ValueError("physical starting point differs from qualified original")
        report.update(
            preparation=preparation,
            labels=backend.labels,
            flux_scale=backend.flux_scale,
            construction_tolerance=1e-8,
        )
        arms = []
        for repeat in (1, 2):
            output = args.study / f"slsqp-{repeat}.json"
            arms.append(run_arm(backend, ctx, x0, args.raw / f"slsqp-{repeat}", output, repeat,
                                budget=budget))
            report["arms"].append(reference(output))
            write_json_atomic(args.study / "summary.json", report)
        a, b = arms
        checks = {
            "gradient_screens": all(r["gradient_screen_pass"] for r in arms),
            "same_counters": a["counters"] == b["counters"],
            "same_stop": a["status"] == b["status"] and a["stop_reason"] == b["stop_reason"],
            "identical_complete_histories": len(a["evaluations"]) == len(b["evaluations"])
            and all(
                r["x_sha256"] == s["x_sha256"] and r["values"] == s["values"]
                for r, s in zip(a["evaluations"], b["evaluations"], strict=True)
            ),
            "same_best": a["best"]["x_sha256"] == b["best"]["x_sha256"],
            "same_logical_work": a["work"] == b["work"],
        }
        report.update(status="completed", checks=checks, qualification_pass=all(checks.values()))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.study / "summary.json", report)
    print(json.dumps({"qualification_pass": report["qualification_pass"]}))
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
