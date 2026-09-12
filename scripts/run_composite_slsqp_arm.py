"""Additive registered SLSQP arm; search flow unchanged, start qualification explicit."""

import time

import numpy as np
from run_direct_slsqp_pilot import reference
from scipy.optimize import minimize

from fusion_baselines.affine_coordinates import AffineCoordinates
from fusion_baselines.budgeted_oracle import BudgetExhausted
from fusion_baselines.composite_start_gate import (
    composite_gate,
    reference_checks,
    startup_replay,
)
from fusion_baselines.inequality_oracle import InequalityOracle
from fusion_baselines.provenance import write_json_atomic


def run_arm(backend, ctx, x0, directory, output, repeat, *, qualified,
            source_permutation, failed_arm, budget=2048):
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
        "gradient_gate_profile": "qualified_pairs_plus_original_nonpair_fd",
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
        values, jacobian = request(x0)
        direction = qualified["direction"].copy()
        initial = directory / "initial.npz"
        with initial.open("xb") as stream:
            np.savez_compressed(stream, x=x0, values=values, jacobian=jacobian,
                                direction=direction)
        record["initial_arrays"] = reference(initial)
        record["initial_reference"] = reference_checks(x0, values, jacobian, qualified)
        if not all(record["initial_reference"][k+"_pass"] for k in ("x", "values", "jacobian")):
            raise ValueError("independently qualified full start replay failed")
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
        record["startup_replay"] = startup_replay(
            x0, direction, source_permutation, oracle.records, failed_arm)
        record.update(composite_gate(screens[-1]["normalized_errors"],
                                     record["initial_reference"], record["startup_replay"]))
        if not record["gradient_screen_pass"]:
            raise ValueError("qualified composite start gate failed")
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
