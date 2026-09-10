"""Qualify full-bundle counting on a shared, promoted real-coil problem."""

import argparse
import contextlib
import importlib.metadata
import inspect
import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from simsopt import load
from simsopt.field import BiotSavart, coils_via_symmetries
from simsopt.geo import CurveXYZFourier, SurfaceRZFourier
from simsopt.solve.augmented_lagrangian import augmented_lagrangian_method
from stellcoilbench.case_loader import load_case
from stellcoilbench.coil_optimization import _optimization_loop as loop

from fusion_baselines.budgeted_oracle import BudgetedOracle, BudgetExhausted, NamedVectorBackend
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic

SOURCE_SHA = "7ae1b1968b8ca34fa94cc0e67cfad41577219ed43bcd902b695c7b7cc04ecd2e"


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


class CapturedContext(BaseException):
    def __init__(self, context):
        self.context = context


def prepare(root, raw):
    start = time.monotonic()
    source = root / "artifacts/runs/lpqa-engineering-v1p1-lbfgsb/biot_savart_optimized.json"
    if sha256_file(source) != SOURCE_SHA:
        raise ValueError("warm-start field hash mismatch")
    source_field = load(str(source))
    surface_path = root / "external/stellcoilbench/plasma_surfaces/input.LandremanPaul2021_QA"
    surface = SurfaceRZFourier.from_vmec_input(
        str(surface_path), range="half period", nphi=32, ntheta=32
    )
    curves = []
    for coil in source_field.coils[:4]:
        old = np.asarray(coil.curve.local_full_x).reshape(3, 9)
        curve = CurveXYZFourier(200, 8)
        padded = np.zeros((3, 17))
        padded[:, :9] = old
        curve.local_full_x = padded.ravel()
        curves.append(curve)
    coils = coils_via_symmetries(curves, [c.current for c in source_field.coils[:4]], 2, True)
    promoted = BiotSavart(coils)
    points = surface.gamma().reshape(-1, 3)[:64].copy()
    source_field.set_points(points)
    promoted.set_points(points)
    old_b, new_b = source_field.B().copy(), promoted.B().copy()
    error = float(
        np.max(np.linalg.norm(new_b - old_b, axis=1)) / np.max(np.linalg.norm(old_b, axis=1))
    )
    if error > 1e-10:
        raise ValueError(f"Fourier promotion changed field: {error}")
    with (raw / "promotion.npz").open("xb") as stream:
        np.savez_compressed(stream, points=points, source_B=old_b, promoted_B=new_b)
    case_path = root / "cases/lpqa_engineering_v1p1_lbfgsb.yaml"
    config = load_case(case_path)
    terms = config.coil_objective_terms
    original = loop._run_optimization_step

    def capture(ctx):
        raise CapturedContext(ctx)

    loop._run_optimization_step = capture
    try:
        with (raw / "preparation.log").open("x") as stream, contextlib.redirect_stdout(stream):
            try:
                loop._optimize_coils_loop_impl(
                    surface,
                    out_dir=raw / "setup",
                    ncoils=4,
                    order=8,
                    initial_coils=coils,
                    coil_objective_terms=terms,
                    algorithm="L-BFGS-B",
                    verbose=False,
                    save_coils_surface_vtk=False,
                    save_initial_state=False,
                    **{key: value for key, value in terms.items() if key.endswith("_threshold")},
                )
            except CapturedContext as caught:
                ctx = caught.context
            else:
                raise RuntimeError("optimizer context capture did not execute")
    finally:
        loop._run_optimization_step = original
    scales = [ctx.constraint_scaling.get(i, 1.0) for i in range(len(ctx.c_list))]
    backend = NamedVectorBackend(ctx.Jf, ctx.c_list, scales)
    return (
        ctx,
        backend,
        {
            "source": reference(source),
            "surface": reference(surface_path),
            "case": reference(case_path),
            "promotion": reference(raw / "promotion.npz"),
            "promotion_relative_B_difference": error,
            "shared_preparation_seconds": time.monotonic() - start,
            "degrees_of_freedom": backend.names,
            "scales": scales,
            "thresholds": ctx.th,
            "constraint_terms": ctx.constraint_idx_to_term,
            "preparation_is_shared_and_outside_per_arm_budget": True,
        },
    )


def run_arm(method, repeat, backend, ctx, x0, raw, output, provenance):
    oracle = BudgetedOracle(backend, 150, len(x0))
    state = {"x": x0.copy()}
    directory = raw / f"{method}-{repeat}"
    directory.mkdir()
    started = time.monotonic()
    record = {**provenance, "method": method, "repeat": repeat, "status": "running"}
    last_checkpoint = 0

    def checkpoint():
        record.update(
            counters=oracle.counters(),
            evaluations=oracle.records,
            elapsed_seconds=time.monotonic() - started,
        )
        write_json_atomic(output, record)

    def request(x):
        nonlocal last_checkpoint
        answer = oracle.evaluate(x)
        if len(oracle.records) // 25 > last_checkpoint:
            last_checkpoint = len(oracle.records) // 25
            print(f"{method} repeat={repeat}: bundles={len(oracle.records)}", flush=True)
            checkpoint()
        return answer

    class Component:
        def __init__(self, index):
            self.index = index

        @property
        def x(self):
            return state["x"].copy()

        @x.setter
        def x(self, x):
            state["x"] = np.asarray(x).copy()

        def J(self):
            return request(state["x"])[0][self.index]

        def dJ(self):
            return request(state["x"])[1][self.index]

    try:
        direction = np.random.default_rng(42).normal(size=len(x0))
        direction /= np.linalg.norm(direction)
        _, jacobian = request(x0)
        exact = jacobian @ direction
        checks = []
        for eps in [1e-4, 1e-5, 1e-6]:
            plus, _ = request(x0 + eps * direction)
            minus, _ = request(x0 - eps * direction)
            fd = (plus - minus) / (2 * eps)
            error = np.abs(fd - exact) / np.maximum(1.0, np.abs(exact))
            checks.append(
                {
                    "eps": eps,
                    "normalized_errors": error.tolist(),
                    "finite_difference": fd.tolist(),
                    "analytic": exact.tolist(),
                }
            )
        record["gradient_checks"] = checks
        record["gradient_screen_pass"] = max(checks[-1]["normalized_errors"]) <= 1e-6
        if not record["gradient_screen_pass"]:
            raise ValueError("preregistered gradient screen failed")
        state["x"] = x0.copy()
        if method == "lbfgsb":

            def objective(x):
                values, jacobian = request(x)
                return float(values @ values / 2), jacobian.T @ values

            solution = minimize(
                objective,
                x0.copy(),
                jac=True,
                method="L-BFGS-B",
                options={
                    "maxiter": 10000,
                    "maxls": 40,
                    "maxcor": 30,
                    "ftol": 1e-15,
                    "gtol": 1e-15,
                },
            )
            record["solver_return"] = {
                "success": bool(solution.success),
                "message": str(solution.message),
                "nit": int(solution.nit),
                "nfev": int(solution.nfev),
            }
        else:
            with (directory / "solver.log").open("x") as stream, contextlib.redirect_stdout(stream):
                augmented_lagrangian_method(
                    f=None,
                    equality_constraints=[Component(i) for i in range(len(backend.objectives))],
                    MAXITER=100,
                    MAXITER_lag=20,
                    mu_init=10,
                    verbose=False,
                )
        record["status"] = "solver_returned"
    except BudgetExhausted:
        record["status"] = "budget_exhausted"
    except Exception as error:
        record.update(status="error", error=f"{type(error).__name__}: {error}")
    finally:
        if oracle.best is not None:
            best = oracle.best
            backend.global_objective.x = best["x"].copy()
            with (directory / "best.npz").open("xb") as stream:
                np.savez_compressed(stream, x=best["x"], values=best["values"])
            ctx.Jf.field.save(str(directory / "best_field.json"))
            record["best"] = {
                "attempt": best["attempt"],
                "merit": best["merit"],
                "x_sha256": best["x_sha256"],
                "arrays": reference(directory / "best.npz"),
                "field": reference(directory / "best_field.json"),
            }
        record["physical_feasibility_certified"] = False
        checkpoint()
    return record


def repeat_check(a, b):
    return {
        "same_status": a["status"] == b["status"],
        "same_counters": a["counters"] == b["counters"],
        "same_proposals": [r["x_sha256"] for r in a["evaluations"]]
        == [r["x_sha256"] for r in b["evaluations"]],
        "same_values": len(a["evaluations"]) == len(b["evaluations"])
        and all(
            aa["status"] == bb["status"] == "completed"
            and np.allclose(aa["values"], bb["values"], rtol=1e-12, atol=1e-14)
            for aa, bb in zip(a["evaluations"], b["evaluations"], strict=True)
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("evidence/oracle-qualification-v1"))
    parser.add_argument("--raw", type=Path, default=Path("artifacts/oracle-qualification-v1"))
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("oracle qualification directories already exist")
    root = Path(__file__).resolve().parents[1]
    provenance = {
        "schema_version": 1,
        "repository": git_state(root),
        "host": host_state(),
        "protocol": reference(root / "docs/OPTIMIZATION_ORACLE_PROTOCOL.md"),
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/budgeted_oracle.py"),
        ],
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["numpy", "scipy", "simsopt", "stellcoilbench"]
        },
        "external": {
            name: git_state(root / f"external/{name}") for name in ["simsopt", "stellcoilbench"]
        },
    }
    provenance["installed_sources"] = [
        reference(Path(inspect.getfile(loop))),
        reference(Path(inspect.getfile(augmented_lagrangian_method))),
    ]
    for installed, local in zip(
        provenance["installed_sources"],
        [
            root
            / "external/stellcoilbench/src/stellcoilbench/coil_optimization/_optimization_loop.py",
            root / "external/simsopt/src/simsopt/solve/augmented_lagrangian.py",
        ],
        strict=True,
    ):
        if installed["sha256"] != sha256_file(local):
            raise ValueError("installed optimizer source differs from pinned checkout")
    expected = {
        "simsopt": "a79006b0bc1e6df8ab48de284e3457d39a49b995",
        "stellcoilbench": "c7949edc4ea6378fc3be633304c69c288c3b79b5",
    }
    for name, revision in expected.items():
        if (
            provenance["external"][name]["commit"] != revision
            or provenance["external"][name]["dirty"]
        ):
            raise ValueError("external checkout is not clean and pinned")
    args.raw.mkdir(parents=True)
    report = {**provenance, "status": "running", "qualification_pass": False}
    try:
        ctx, backend, preparation = prepare(root, args.raw)
        report["preparation"] = preparation
        write_json_atomic(args.output / "summary.json", report)
        x0 = ctx.Jf.x.copy()
        report["arms"] = []
        checks = {}
        for method in ["lbfgsb", "auglag"]:
            pair = []
            for repeat in [1, 2]:
                ctx.Jf.x = x0.copy()
                path = args.output / f"{method}-{repeat}.json"
                arm = run_arm(method, repeat, backend, ctx, x0, args.raw, path, provenance)
                pair.append(arm)
                report["arms"].append(reference(path))
                if arm["status"] == "error":
                    raise ValueError(f"arm failed: {arm.get('error')}")
            checks[method] = repeat_check(*pair)
            write_json_atomic(args.output / "summary.json", report)
        report.update(
            status="completed",
            repeat_checks=checks,
            qualification_pass=all(all(check.values()) for check in checks.values()),
        )
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output / "summary.json", report)
    print(json.dumps({"qualification_pass": report["qualification_pass"], "repeat_checks": checks}))
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
