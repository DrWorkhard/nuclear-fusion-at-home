"""Qualify full-bundle counting on a shared, promoted real-coil problem."""

import argparse
import contextlib
import hashlib
import importlib.metadata
import inspect
import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares, minimize
from simsopt import load
from simsopt.field import BiotSavart, coils_via_symmetries
from simsopt.geo import CurveXYZFourier, SurfaceRZFourier
from simsopt.solve.augmented_lagrangian import augmented_lagrangian_method
from stellcoilbench.case_loader import load_case
from stellcoilbench.coil_optimization import _optimization_loop as loop

from fusion_baselines.affine_coordinates import AffineCoordinates
from fusion_baselines.budgeted_oracle import BudgetedOracle, BudgetExhausted, NamedVectorBackend
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.refined_curvature import make_refined_penalty

SOURCE_SHA = "7ae1b1968b8ca34fa94cc0e67cfad41577219ed43bcd902b695c7b7cc04ecd2e"


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


class CapturedContext(BaseException):
    def __init__(self, context):
        self.context = context


def prepare(root, raw, *, guarded_curvature=False):
    start = time.monotonic()
    source = root / "fixtures/rejected-lpqa-warmstart/field.json"
    source_bytes = source.read_bytes()
    if (
        not source_bytes.endswith(b"\n")
        or hashlib.sha256(source_bytes[:-1]).hexdigest() != SOURCE_SHA
    ):
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
    regularizations = [c.regularization for c in source_field.coils[:4]]
    coils = coils_via_symmetries(
        curves,
        [c.current for c in source_field.coils[:4]],
        2,
        True,
        regularizations=regularizations,
    )
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
    terms = dict(config.coil_objective_terms)
    if guarded_curvature:
        terms.update(length_threshold=219.9, flux_threshold=8e-9)
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
    guard = None
    if guarded_curvature:
        index = next(i for i, term in ctx.constraint_idx_to_term.items()
                     if term == "coil_curvature")
        ctx.c_list[index] = make_refined_penalty(
            [c.curve for c in ctx.Jf.field.coils[:4]], 0.99 * ctx.th["curvature_threshold"])
        guard = {"component_index": index, "curvature_resolution": 1600,
                 "curvature_target_reactor": 0.99, "length_target_reactor": 219.9,
                 "flux_target": 8e-9, "field_quadrature_unchanged": 200}
    backend = NamedVectorBackend(ctx.Jf, ctx.c_list, scales)
    return (
        ctx,
        backend,
        {
            "source": reference(source),
            "source_parent_sha256": SOURCE_SHA,
            "source_transformation": "one terminal LF appended to archived producer bytes",
            "surface": reference(surface_path),
            "case": reference(case_path),
            "promotion": reference(raw / "promotion.npz"),
            "promotion_relative_B_difference": error,
            "regularizations_preserved": [float(c.regularization) for c in coils[:4]]
            == [float(c.regularization) for c in source_field.coils[:4]],
            "shared_preparation_seconds": time.monotonic() - start,
            "degrees_of_freedom": backend.names,
            "scales": scales,
            "guarded_search_targets": guard,
            "thresholds": ctx.th,
            "constraint_terms": ctx.constraint_idx_to_term,
            "preparation_is_shared_and_outside_per_arm_budget": True,
        },
    )


def run_arm(method, repeat, backend, ctx, x0, raw, output, provenance, *, budget=150,
            coordinate_scale=None):
    oracle = BudgetedOracle(backend, budget, len(x0))
    coordinates = AffineCoordinates(x0, coordinate_scale) if coordinate_scale is not None else None
    state = {"x": x0.copy()}
    directory = raw / f"{method}-{repeat}"
    directory.mkdir()
    started = time.monotonic()
    record = {**provenance, "method": method, "repeat": repeat, "status": "running"}
    record["coordinate_map"] = {
        "kind": "affine" if coordinates else "identity",
        "scale": coordinate_scale if coordinates else 1.0,
        "physical_origin_sha256": hashlib.sha256(x0.tobytes()).hexdigest(),
        "oracle_records_physical_coordinates": True,
    }
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
            return coordinates.solver(state["x"]) if coordinates else state["x"].copy()

        @x.setter
        def x(self, x):
            state["x"] = coordinates.physical(x) if coordinates else np.asarray(x).copy()

        def J(self):
            return request(state["x"])[0][self.index]

        def dJ(self):
            gradient = request(state["x"])[1][self.index]
            return coordinates.gradient(gradient) if coordinates else gradient

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
                values, jacobian = request(coordinates.physical(x) if coordinates else x)
                gradient = jacobian.T @ values
                return float(values @ values / 2), (
                    coordinates.gradient(gradient) if coordinates else gradient
                )

            solution = minimize(
                objective,
                coordinates.solver(x0) if coordinates else x0.copy(),
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
        elif method == "trf":
            def residual(y):
                return request(coordinates.physical(y))[0]

            def jacobian(y):
                return request(coordinates.physical(y))[1] * coordinates.scale

            solution = least_squares(
                residual, coordinates.solver(x0), jac=jacobian, method="trf",
                tr_solver="exact", loss="linear", x_scale=1.0, max_nfev=100000,
                ftol=1e-15, xtol=1e-15, gtol=1e-15)
            record["solver_return"] = {
                "success": bool(solution.success), "message": str(solution.message),
                "nfev": int(solution.nfev), "njev": int(solution.njev),
                "optimality": float(solution.optimality)}
        elif method == "auglag":
            with (directory / "solver.log").open("x") as stream, contextlib.redirect_stdout(stream):
                augmented_lagrangian_method(
                    f=None,
                    equality_constraints=[Component(i) for i in range(len(backend.objectives))],
                    MAXITER=100,
                    MAXITER_lag=20,
                    mu_init=10,
                    verbose=False,
                )
        else:
            raise ValueError(f"unknown method: {method}")
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
    parser.add_argument("--normalized-feasibility", action="store_true")
    parser.add_argument("--affine-feasibility", action="store_true")
    parser.add_argument("--guarded-curvature", action="store_true")
    args = parser.parse_args()
    args.affine_feasibility = args.affine_feasibility or args.guarded_curvature
    args.normalized_feasibility = args.normalized_feasibility or args.affine_feasibility
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("oracle qualification directories already exist")
    root = Path(__file__).resolve().parents[1]
    provenance = {
        "schema_version": 1,
        "repository": git_state(root),
        "host": host_state(),
        "protocol": reference(
            root
            / "docs"
            / (
                "GUARDED_FEASIBILITY_PROTOCOL.md" if args.guarded_curvature else
                "AFFINE_FEASIBILITY_PROTOCOL.md" if args.affine_feasibility else
                "NORMALIZED_FEASIBILITY_PROTOCOL.md"
                if args.normalized_feasibility
                else "OPTIMIZATION_ORACLE_PROTOCOL.md"
            )
        ),
        "base_oracle_protocol": reference(root / "docs/OPTIMIZATION_ORACLE_PROTOCOL.md"),
        "normalized_feasibility": args.normalized_feasibility,
        "affine_feasibility": args.affine_feasibility,
        "guarded_curvature": args.guarded_curvature,
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/budgeted_oracle.py"),
            reference(root / "src/fusion_baselines/affine_coordinates.py"),
            reference(root / "src/fusion_baselines/refined_curvature.py"),
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
    provenance["least_squares_source"] = reference(Path(inspect.getfile(least_squares)))
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
        if args.guarded_curvature:
            qualification = root / "evidence/guarded-curvature-gradient-v1.json"
            qualified = json.loads(qualification.read_text())
            if not qualified["all_pass"] or len(qualified["cases"]) != 2:
                raise ValueError("active refined-curvature gradient qualification required")
            for source in qualified["code"] + [qualified["protocol"]]:
                if sha256_file(Path(source["path"])) != source["sha256"]:
                    raise ValueError("curvature qualification source/protocol changed")
            report["curvature_gradient_qualification"] = reference(qualification)
        ctx, backend, preparation = prepare(
            root, args.raw, guarded_curvature=args.guarded_curvature)
        report["preparation"] = preparation
        x0 = ctx.Jf.x.copy()
        if args.normalized_feasibility:
            shared = BudgetedOracle(backend, 1, len(x0))
            values, _ = shared.evaluate(x0)
            norm = float(np.linalg.norm(values))
            if not np.isfinite(norm) or norm <= 0:
                raise ValueError("initial common vector norm must be finite and positive")
            factor = 1 / norm
            backend.scales *= factor
            report["normalization"] = {
                "initial_norm": norm,
                "factor": factor,
                "shared_counters": shared.counters(),
                "shared_evaluations": shared.records,
                "normalized_scales": backend.scales.tolist(),
            }
        write_json_atomic(args.output / "summary.json", report)
        report["arms"] = []
        report["methods"] = ["trf"] if args.guarded_curvature else ["lbfgsb", "auglag"]
        checks = {}
        for method in report["methods"]:
            pair = []
            for repeat in [1, 2]:
                ctx.Jf.x = x0.copy()
                path = args.output / f"{method}-{repeat}.json"
                arm = run_arm(
                    method,
                    repeat,
                    backend,
                    ctx,
                    x0,
                    args.raw,
                    path,
                    provenance,
                    budget=(3000 if args.guarded_curvature else
                            1500 if args.normalized_feasibility else 150),
                    coordinate_scale=0.01 if args.affine_feasibility else None,
                )
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
