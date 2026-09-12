"""Fixed eight-stage classical AL control with explicit physical-bundle accounting."""

import hashlib

import numpy as np

from fusion_baselines.natural_auglag import update_multipliers

LS_OPTIONS = dict(
    method="trf",
    tr_solver="exact",
    loss="linear",
    x_scale=1.0,
    ftol=1e-10,
    xtol=1e-10,
    gtol=1e-10,
    max_nfev=100000,
)


class StageCap(Exception):
    pass


class ConstructionTarget(Exception):
    pass


def solve_stages(
    oracle,
    backend,
    x0,
    initial_values,
    *,
    minimizer,
    stages,
    target_enabled=True,
    progress=lambda: None,
):
    """The supplied backend must retain only the last complete physical bundle.

    Stage records are appended in-place so failures can still be checkpointed.
    Initial qualification bundles are owned/counted by the caller's same oracle.
    """
    x0 = np.asarray(x0, dtype=float).copy()
    y0, lam, rho = np.zeros_like(x0), np.zeros(len(initial_values) - 1), 10.0
    previous = max(1.0, max(0.0, -float(np.min(initial_values[1:]))))
    for number in range(1, 9):
        start = len(oracle.records)
        record = dict(
            stage=number,
            start_attempts=start,
            rho=rho,
            multipliers=lam.tolist(),
            previous_violation=previous,
            requests=[],
            denied=0,
            status="running",
        )
        stages.append(record)
        best = None

        def compose(y, start=start, record=record, lam=lam, rho=rho):
            nonlocal best
            x = x0 + 0.01 * np.asarray(y)
            cached = backend.last_x is not None and np.array_equal(x, backend.last_x)
            if not cached and len(oracle.records) - start >= 128:
                record["denied"] += 1
                raise StageCap
            values, jacobian = oracle.evaluate(x)
            residual, derivative = backend.residual_for(x, lam, rho)
            merit = float(0.5 * residual @ residual)
            point = dict(
                attempt=len(oracle.records),
                x_sha256=hashlib.sha256(x.tobytes()).hexdigest(),
                merit=merit,
            )
            record["requests"].append(point)
            if best is None or merit < best["merit"]:
                best = {
                    **point,
                    "y": np.asarray(y).copy(),
                    "values": values.copy(),
                    "jacobian": jacobian.copy(),
                }
            progress()
            if target_enabled and values[0] <= 0.008 and np.min(values[1:]) >= 0:
                raise ConstructionTarget
            return residual, 0.01 * derivative

        try:
            solution = minimizer(
                lambda y: compose(y)[0], y0, jac=lambda y: compose(y)[1], **LS_OPTIONS
            )
            record.update(
                status="solver_returned",
                solver=dict(
                    status=int(solution.status),
                    success=bool(solution.success),
                    nfev=int(solution.nfev),
                    njev=int(solution.njev),
                ),
            )
        except StageCap:
            record["status"] = "stage_budget_exhausted"
        except ConstructionTarget:
            record["status"] = "construction_target"
        except Exception as error:
            record.update(status="error", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            record["end_attempts"] = len(oracle.records)
        if best is None:
            raise ValueError("empty inner stage cannot select a next point")
        y0 = best["y"].copy()
        g = best["values"][1:]
        violation = max(0.0, -float(np.min(g)))
        updated = update_multipliers(g, lam, rho)
        next_rho = rho * 10 if violation > 0.25 * previous else rho
        record.update(
            selected={k: best[k] for k in ("attempt", "x_sha256", "merit")},
            selected_values=best["values"].tolist(),
            violation=violation,
            updated_multipliers=updated.tolist(),
            next_rho=next_rho,
            lagrangian_gradient_max=float(
                np.max(np.abs(best["jacobian"][0] - best["jacobian"][1:].T @ updated))
            ),
        )
        lam, rho, previous = updated, next_rho, max(violation, 1e-12)
        if record["status"] == "construction_target":
            return "construction_target"
    return "eight_stages_completed"
