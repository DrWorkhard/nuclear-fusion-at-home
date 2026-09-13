"""Registered curvature-informed arm with frozen-event startup and counted failures."""

import hashlib
import time
import warnings

import numpy as np
from current_diagnostic_inputs import reference
from qualify_fixed_currents import error
from scipy.optimize import BFGS, NonlinearConstraint, minimize

from fusion_baselines.affine_coordinates import AffineCoordinates
from fusion_baselines.batched_field_jacobian import batched_field_jacobian
from fusion_baselines.budgeted_oracle import BudgetExhausted
from fusion_baselines.counted_field_views import CountedBatchField, increment
from fusion_baselines.gauss_newton_backend import GaussNewtonBackend
from fusion_baselines.inequality_oracle import InequalityOracle
from fusion_baselines.provenance import write_json_atomic
from fusion_baselines.spatial_flux import spatial_flux

OPTIONS = dict(
    gtol=1e-12,
    xtol=1e-12,
    barrier_tol=1e-10,
    initial_tr_radius=0.1,
    initial_constr_penalty=1.0,
    initial_barrier_parameter=1e-3,
    initial_barrier_tolerance=1e-3,
    factorization_method="QRFactorization",
    sparse_jacobian=False,
    maxiter=10000,
    verbose=0,
)


def save(path, **arrays):
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    return reference(path)


def control():
    result = minimize(
        lambda x: (0.5 * ((x[0] - 2) ** 2 + (x[1] + 1) ** 2), x - np.array([2.0, -1.0])),
        [0.0, 0.0],
        jac=True,
        hess=lambda x: np.eye(2),
        method="trust-constr",
        constraints=NonlinearConstraint(
            lambda x: np.array([1 - x[0], x[1]]),
            0.0,
            np.inf,
            jac=lambda x: np.diag([-1.0, 1.0]),
            hess=lambda x, v: np.zeros((2, 2)),
        ),
        options=OPTIONS,
    )
    return dict(
        x=result.x.tolist(),
        optimality=float(result.optimality),
        constraint_violation=float(result.constr_violation),
        all_pass=bool(
            np.max(abs(result.x - [1, 0])) <= 1e-5
            and result.optimality <= 1e-8
            and result.constr_violation <= 1e-8
        ),
    )


class CountedGN:
    def __init__(self, direct):
        self.direct, self.work, self.last = direct, {}, {}
        self.backend = GaussNewtonBackend(
            self.evaluate_direct, self.spatial, native_residual=self.native_residual
        )

    def evaluate_direct(self, x):
        self.last = dict(x=np.asarray(x).copy())
        values, jacobian, metrics = self.direct.evaluate(x)
        self.last.update(values=values.copy(), jacobian=jacobian.copy())
        return values, jacobian, metrics

    def spatial(self):
        increment(self.work, "assembly_requests")
        z, d = batched_field_jacobian(
            CountedBatchField(self.direct.field, self.work),
            self.direct.global_objective,
            self.direct.points,
            self.direct.weights,
        )
        self.last.update(batch_z=z.copy(), D=d.copy())
        increment(self.work, "assembly_completed")
        return z, d

    def native_residual(self):
        if not np.array_equal(self.direct.field.get_points_cart_ref(), self.direct.points):
            raise ValueError("GN observation points changed")
        increment(self.work, "native_covector_B_requests")
        b = self.direct.field.B().reshape(self.direct.normal.shape).copy()
        increment(self.work, "native_covector_B_completed")
        self.last["native_B"] = b
        z = spatial_flux(b, self.direct.normal)
        self.last["native_z"] = z.copy()
        return z


def run_arm(direct, ctx, qualified, raw, output, repeat, *, budget=2048):
    raw.mkdir()
    x0 = qualified["points"][0].copy()
    ctx.Jf.x = x0.copy()
    direct.work = dict.fromkeys(direct.work, 0)
    counted = CountedGN(direct)
    coordinates = AffineCoordinates(x0, 0.01)
    oracle = InequalityOracle(counted.backend.evaluate, budget, 207, 137, tolerance=1e-8)
    record = dict(
        method="gn-trust",
        representation="direct",
        repeat=repeat,
        status="running",
        coordinate_scale=0.01,
        selection_tolerance=1e-8,
        gradient_screen_pass=False,
        gradient_gate_profile="closed_geometry_current_matrix_plus_sixteen_event_replay",
        iterations=[],
        startup=[],
        hessian_requests=0,
        physical_points=[],
    )
    started, checkpoint_count, target_stop = time.monotonic(), 0, False

    def checkpoint():
        record.update(
            counters=oracle.counters(),
            evaluations=oracle.records,
            work=direct.work.copy(),
            gn_work=counted.work.copy(),
            gn_identity_checks=counted.backend.records,
            elapsed_seconds=time.monotonic() - started,
        )
        write_json_atomic(output, record)

    def backend(point):
        # Every actual attempt, including a failing request, retains its full input.
        record["physical_points"].append(np.asarray(point).tolist())
        return counted.backend.evaluate(point)

    oracle.backend = backend

    def request(point):
        nonlocal checkpoint_count
        result = oracle.evaluate(point)
        if len(oracle.records) // 25 > checkpoint_count:
            checkpoint_count = len(oracle.records) // 25
            print(
                f"Current-start GN repeat={repeat} bundles={len(oracle.records)} "
                f"best={oracle.best['selection_key']}",
                flush=True,
            )
            checkpoint()
        return result

    def objective(y):
        values, jac = request(coordinates.physical(y))
        return values[0], 0.01 * jac[0]

    def hessian(y):
        record["hessian_requests"] += 1
        point = coordinates.physical(y)
        request(point)
        return 0.01**2 * counted.backend.hessian_for(point)

    def callback(y, state):
        nonlocal target_stop
        margin = float(np.min(state.constr[0]))
        target_stop = bool(state.fun <= 0.008 and margin >= 0)
        record["iterations"].append(
            dict(
                iteration=int(state.nit),
                objective=float(state.fun),
                physical_x_sha256=hashlib.sha256(coordinates.physical(y).tobytes()).hexdigest(),
                minimum_margin=margin,
                optimality=float(state.optimality),
                constraint_violation=float(state.constr_violation),
                trust_radius=float(state.tr_radius),
                barrier_parameter=float(state.barrier_parameter),
                construction_target=target_stop,
            )
        )
        return target_stop

    try:
        for i, point in enumerate(qualified["points"]):
            values, jac = request(point)
            check = dict(index=i, values_error=error(values, qualified["values"][i]))
            if i == 0:
                h = counted.backend.hessian_for(point)
                check.update(
                    jacobian_error=error(jac, qualified["jacobian"]),
                    hessian_error=error(h, qualified["hessian"]),
                )
                record["initial_arrays"] = save(
                    raw / "initial.npz", x=point, values=values, jacobian=jac, hessian=h
                )
            check["all_pass"] = bool(
                check["values_error"] <= 1e-12
                and (i != 0 or check["jacobian_error"] <= 1e-12 and check["hessian_error"] <= 1e-10)
            )
            record["startup"].append(check)
            checkpoint()
            if not check["all_pass"]:
                raise ValueError("frozen source full-bundle/native-Gram startup gate failed")
        record["gradient_screen_pass"] = True
        constraints = NonlinearConstraint(
            lambda y: request(coordinates.physical(y))[0][1:],
            0.0,
            np.inf,
            jac=lambda y: 0.01 * request(coordinates.physical(y))[1][1:],
            hess=BFGS(),
            keep_feasible=False,
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                solution = minimize(
                    objective,
                    np.zeros(207),
                    jac=True,
                    hess=hessian,
                    method="trust-constr",
                    constraints=constraints,
                    callback=callback,
                    options=OPTIONS,
                )
            finally:
                record["warnings"] = [str(w.message) for w in caught]
        record.update(
            status="solver_returned",
            stop_reason="construction_target" if target_stop else "solver_returned",
            solver=dict(
                success=bool(solution.success),
                status=int(solution.status),
                message=str(solution.message),
                nit=int(solution.nit),
                nfev=int(solution.nfev),
                njev=int(solution.njev),
                nhev=int(solution.nhev),
                optimality=float(solution.optimality),
                constr_violation=float(solution.constr_violation),
                physical_terminal_x=coordinates.physical(solution.x).tolist(),
            ),
        )
    except BudgetExhausted:
        record.update(status="budget_exhausted", stop_reason="proposal_cap")
    except Exception as exc:
        record.update(status="error", stop_reason="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if record["status"] == "error":
            record["failed_arrays"] = save(raw / "failed.npz", **counted.last)
            if "x" in counted.last:
                ctx.Jf.x = counted.last["x"].copy()
                failed_field = raw / "failed_field.json"
                ctx.Jf.field.save(str(failed_field))
                record["failed_field"] = reference(failed_field)
        if oracle.best is not None:
            best = oracle.best
            ctx.Jf.x = best["x"].copy()
            field = raw / "best_field.json"
            ctx.Jf.field.save(str(field))
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
            record["best"].update(
                field=reference(field),
                arrays=save(raw / "best.npz", x=best["x"], values=best["values"]),
            )
        checkpoint()
    return record
