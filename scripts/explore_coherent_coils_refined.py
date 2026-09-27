"""Source-bound paired retry changing only the two startup finite-difference steps."""

import argparse
import copy
import hashlib
import time
from contextlib import contextmanager
from pathlib import Path

import explore_coherent_coils as paired
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
previous = paired.previous
PROBE_STEPS = (1.25e-6, 6.25e-7)
DIAGNOSTIC = "artifacts/coherent-derivative-scale-v1/run/result.json"
FAILED = "artifacts/coherent-coils-v1/run/result.json"
INPUTS = {
    **paired.INPUTS,
    DIAGNOSTIC: "fc0f32fed25f72451a71d8293252303430fc7e93f62c177f7ef7a80b5fedfb99",
    FAILED: "b371d45a07c5ed197b2c9fd56112d66474448036c29f29b4232a31dafeb813a2",
    "scripts/explore_coherent_coils.py":
        "b5d1b8af0b077e751547d5d6f92fb16477609f0f0e9ebaee20ca31b81289f33c",
    "tests/test_explore_coherent_coils.py":
        "c0ccd28ee5cef78ad26c6faa7d1221cd828581722e4a6154675c125f14b0a1b7",
    "scripts/check_coherent_derivative_scale.py":
        "68fc5ddc90ca22df375ee734f69693f8be626b4b10fdc8134d68e4fb029e0486",
    "tests/test_check_coherent_derivative_scale.py":
        "c540760aeb1fff25faf04ec286e8832751347cefbf392054a613f0cdd2769a11",
}
ORIGINAL_SEARCH, ORIGINAL_INPUTS = previous.search, paired.INPUTS
ORIGINAL_FINGERPRINTS, ORIGINAL_SEED_INPUTS = paired.fingerprints, paired.seed_inputs


def validate_diagnostic(report, anchors):
    if (not report["completed"] or not report["sources_unchanged"] or not report["exact_repeat"]
            or report["bundles_attempted"] != 30 or report["bundles_completed"] != 30
            or report["model_configuration"] != "control" or report["coefficient_box_m"] != .02
            or report["tolerances"] != dict(absolute=1e-7, relative=1e-4, combination="OR")
            or set(report["seed_replay"]) != set(anchors)):
        raise ValueError("complete unchanged-threshold diagnostic and exact repeat required")
    for key, value in anchors.items():
        row = report["seed_replay"][key]
        if (not row["passed"] or row["expected"] != value or not np.isfinite(row["actual"])
                or not np.isclose(row["actual"], value, rtol=1e-10, atol=1e-12)):
            raise ValueError("original shape52 diagnostic anchor mismatch")
    for label, function in (("sin", np.sin), ("cos", np.cos)):
        direction = function(np.arange(198)+1)
        direction /= np.linalg.norm(direction)
        for h in PROBE_STEPS:
            rows = [r for r in report["comparisons"] if (r["direction"], r["h"]) == (label, h)]
            if len(rows) != 1 or not np.array_equal(rows[0]["vector"], direction):
                raise ValueError("unique same-direction selected diagnostic step required")
            components = rows[0]["components"]
            if set(components) != {"total", "flux", "geometry"}:
                raise ValueError("all three diagnostic components required")
            for row in components.values():
                actual = (row["plus"]-row["minus"])/(2*h)
                error = abs(actual-row["analytic"])
                if (not np.isfinite([actual, row["analytic"], error]).all()
                        or actual != row["finite_difference"] or error != row["error"]
                        or not row["threshold_met"] or not (
                            error <= 1e-7 or error <= 1e-4*max(abs(actual), abs(row["analytic"])))):
                    raise ValueError("selected diagnostic component fails original threshold")


def seed_inputs(source):
    seed, anchors = ORIGINAL_SEED_INPUTS(source)
    failed = source[FAILED]
    if (failed["completed"] or not failed["sources_unchanged"]
            or failed["seed_anchors"] != anchors):
        raise ValueError("same failed paired run and original anchors required")
    validate_diagnostic(source[DIAGNOSTIC], anchors)
    return seed, anchors


def fingerprints():
    result = ORIGINAL_FINGERPRINTS()
    paths = [Path(__file__).resolve(), *(ROOT/name for name in INPUTS)]
    result.update({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    return result


@contextmanager
def refined_startup():
    if (previous.search is not ORIGINAL_SEARCH or paired.INPUTS is not ORIGINAL_INPUTS
            or paired.fingerprints is not ORIGINAL_FINGERPRINTS
            or paired.seed_inputs is not ORIGINAL_SEED_INPUTS):
        raise ValueError("pinned orchestration required; nested/concurrent overrides forbidden")
    previous.search, paired.INPUTS = search, INPUTS
    paired.fingerprints, paired.seed_inputs = fingerprints, seed_inputs
    try:
        yield
    finally:
        previous.search, paired.INPUTS = ORIGINAL_SEARCH, ORIGINAL_INPUTS
        paired.fingerprints, paired.seed_inputs = ORIGINAL_FINGERPRINTS, ORIGINAL_SEED_INPUTS


def search(model, record, anchors, minimize):
    # Literal pinned search, with explicit module references and only new probe steps.
    rows, best, feasible, checks, replay = [], None, None, [], {}
    initial = model.x0[model.indices].copy()

    def evaluate(values, role):
        nonlocal best, feasible
        record.guard()
        if record.bundles >= previous.BUNDLES:
            raise StopIteration("240 total coarse bundles consumed")
        index = record.bundles
        record.bundles += 1
        record.active = dict(bundle=index, role=role)
        row = dict(index=index, role=role, active_values=np.asarray(values).tolist(),
                   status="attempted", native_before=copy.deepcopy(record.counts))
        record.save(f"trial-{index:03}-attempt.json", row)
        try:
            x = previous.expand(values, model.x0, model.indices)
            row["x"] = x.tolist()
            value, gradient, metrics = model.evaluate(x)
            row.update(value=value, gradient=gradient.tolist(), metrics=metrics,
                       status="completed", deadline_met=time.monotonic() < record.deadline)
            record.guard()
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            row["native_after"] = copy.deepcopy(record.counts)
            record.save(f"trial-{index:03}.json", row)
        record.guard()
        rows.append(row)
        if role in ("startup-seed", "search"):
            if best is None or value < best["value"]:
                best = row
            if (metrics["sampled_geometry_limits_met"] and metrics["current_limit_met"]
                    and (feasible is None or metrics["normal_rms"]
                         < feasible["metrics"]["normal_rms"])):
                feasible = row
        return value, gradient[model.indices]

    startup_pass = False
    try:
        start_value, start_gradient = evaluate(initial, "startup-seed")
        replay = {key: dict(expected=value, actual=rows[0]["metrics"][key], passed=bool(
            np.isclose(value, rows[0]["metrics"][key], rtol=1e-10, atol=1e-12)))
            for key, value in anchors.items()}
        if not all(row["passed"] for row in replay.values()):
            raise ValueError("case-specific static seed replay failed")
        for label, function in (("sin", np.sin), ("cos", np.cos)):
            direction = function(np.arange(len(initial))+1)
            direction /= np.linalg.norm(direction)
            derivative = float(start_gradient@direction)
            for h in PROBE_STEPS:
                fd = (evaluate(initial+h*direction, "probe")[0]
                      - evaluate(initial-h*direction, "probe")[0])/(2*h)
                error = abs(fd-derivative)
                checks.append(dict(direction=label, h=h, analytic=derivative, fd=fd, error=error,
                                   passed=error <= 1e-7
                                   or error <= 1e-4*max(abs(fd), abs(derivative))))
        repeat, gradient = evaluate(initial, "startup-repeat")
        startup_pass = (repeat == start_value and np.array_equal(gradient, start_gradient)
                        and all(row["passed"] for row in checks))
        if not startup_pass:
            raise ValueError("directional derivative or exact-repeat check failed")
        result = minimize(lambda z: evaluate(z, "search"), initial, jac=True, method="L-BFGS-B",
                          bounds=list(zip(initial-previous.BOX, initial+previous.BOX, strict=True)),
                          options=dict(maxiter=230, maxfun=230, maxls=20, ftol=1e-12, gtol=1e-9))
        status = dict(reason="solver-return", success=bool(result.success),
                      message=str(result.message))
    except (TimeoutError, StopIteration) as exc:
        status = dict(reason="budget", error=str(exc))
    except Exception as exc:
        status = dict(reason="failure", error=f"{type(exc).__name__}: {exc}")
    chosen = feasible if feasible is not None else (rows[0] if rows else None)
    model.set_x(model.x0 if chosen is None else np.asarray(chosen["x"]))
    return dict(status=status, startup_pass=startup_pass, seed_replay=replay,
                derivative_checks=checks, bundles_attempted=record.bundles,
                bundles_completed=len(rows), lowest_objective=best, lowest_feasible_rms=feasible,
                fine_selected=chosen,
                fine_selection="sampled-feasible" if feasible else "seed-fallback",
                physical_admission=False, startup_steps=list(PROBE_STEPS))


def run(output):
    with refined_startup():
        return paired.run(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output.resolve()))
