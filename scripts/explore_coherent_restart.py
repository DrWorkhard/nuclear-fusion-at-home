"""Matched trial598 restarts with original absolute bounds and masked startup probes."""

import argparse
import copy
import hashlib
import json
import shutil
import time
from contextlib import contextmanager
from pathlib import Path

import explore_coherent_coils as paired
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
previous = paired.previous
RESULT = "artifacts/coherent-coils-v2/run/result.json"
SNAPSHOT = "artifacts/coherent-coils-v2/run/coherent/selected-snapshot.json"
TRIAL = "artifacts/coherent-coils-v2/run/coherent/trial-598.json"
GEOMETRY = "artifacts/coherent-coils-v2/geometry/result.json"
INPUTS = {
    **paired.INPUTS,
    RESULT: "328ccd9727e406a72b50016aa03d93f4ac4b0e57f7f57a11686050d7c088cf2b",
    SNAPSHOT: "e05ed6c3b497aa332c3ebfac1f1b9d5d63ec82fc6196f7bbd4ff8d238597176b",
    TRIAL: "59dee3d83fcc3dbeeca04de839adde9f8bdad0fa72311ae1169d3949209983d4",
    GEOMETRY: "b5cb05410b7cae25ebd28d1ad10a02bc760795989519206cd778cee481ff18ce",
    "scripts/explore_coherent_coils.py":
        "b5d1b8af0b077e751547d5d6f92fb16477609f0f0e9ebaee20ca31b81289f33c",
    "scripts/explore_coherent_coils_refined.py":
        "7746f18ab52aba6d998bd80f5c602043df6f7840297f49e4996ca7b672f582cc",
    "tests/test_explore_coherent_coils_refined.py":
        "4988707789deff351beaee41cb2bd52a211abc577fa0156cc4ee436589c3e5ee",
}
ARMS, PROBE_STEPS = ("control", "expanded-low"), (1.25e-6, 6.25e-7)
BUNDLES, ARM_SECONDS, SECONDS = 1200, 450, 1200
ORIGINAL_EXPAND = previous.expand


def bounds(center, arm):
    if arm not in ARMS or np.shape(center) != (198,) or not np.isfinite(center).all():
        raise ValueError("fixed arm and finite original198-coordinate center required")
    widths = np.full(198, .02)
    widths[previous.active_indices("low2")] = .08 if arm == "control" else .12
    return center-widths, center+widths


def masked_directions(start, lower, upper):
    if (any(np.shape(x) != (198,) for x in (start, lower, upper))
            or not np.isfinite([start, lower, upper]).all()
            or np.any(start < lower) or np.any(start > upper) or np.any(lower >= upper)):
        raise ValueError("finite exact start inside the original absolute box required")
    free = np.minimum(start-lower, upper-start) > 2*max(PROBE_STEPS)
    if np.count_nonzero(free) < 2:
        raise ValueError("at least two free startup coordinates required")
    directions = {}
    for label, function in (("sin", np.sin), ("cos", np.cos)):
        vector = function(np.arange(198)+1)*free
        length = np.linalg.norm(vector)
        if not np.isfinite(length) or length == 0:
            raise ValueError("nondegenerate masked startup direction required")
        vector /= length
        if any(np.any(start+sign*h*vector < lower) or np.any(start+sign*h*vector > upper)
               for h in PROBE_STEPS for sign in (-1, 1)):
            raise ValueError("masked central probe would leave the common control box")
        directions[label] = vector
    return free, directions


@contextmanager
def absolute_box(start, lower, upper):
    if previous.expand is not ORIGINAL_EXPAND:
        raise ValueError("pinned expand helper required; nested/concurrent override forbidden")

    def expand(values, original, indices):
        values = np.asarray(values, dtype=float)
        if (not np.array_equal(indices, np.arange(198)) or not np.array_equal(original, start)
                or values.shape != (198,) or not np.isfinite(values).all()
                or np.any(values < lower) or np.any(values > upper)):
            raise ValueError("all198 named coordinates inside the original absolute box required")
        return values.copy()

    previous.expand = expand
    try:
        yield
    finally:
        previous.expand = ORIGINAL_EXPAND


def seed_inputs(source):
    from fusion_baselines.coupled_coil_audit import validate_snapshot

    center_seed, _ = paired.seed_inputs(source)
    seed, trial = copy.deepcopy(source[SNAPSHOT]), source[TRIAL]
    validate_snapshot(seed)
    result, geometry = source[RESULT], source[GEOMETRY]
    arms = [row for row in result["arms"] if row["arm"] == "coherent"]
    rows = [row for row in geometry["rows"] if row["label"] == "coherent"]
    if (not all(r["completed"] and r["sources_unchanged"] for r in (result, geometry))
            or len(arms) != 1 or arms[0]["fine_selected"] != trial
            or not arms[0]["startup_pass"] or len(arms[0]["fine"]) != 2
            or not all(row["checks_pass"] for row in arms[0]["fine"])
            or len(rows) != 1 or not rows[0]["eligible"]
            or rows[0]["snapshot"]["sha256"] != INPUTS[SNAPSHOT]
            or not rows[0]["levels"][-1]["combined_scoped_pass"]
            or geometry["source"]["sha256"] != INPUTS[RESULT]
            or (trial["index"], trial["role"], trial["status"], trial["deadline_met"])
            != (598, "search", "completed", True)
            or seed["names"] != center_seed["names"] or seed["names"] != arms[0]["active_names"]
            or not np.array_equal(np.ravel(seed["base_coefficients"]), trial["x"])
            or any(seed[k] != center_seed[k] for k in ("target_flux", "B2_scale"))
            or any(seed[k] != trial["metrics"][k] for k in ("scale", "unit_flux"))
            or trial["metrics"]["current"] != 1e5*seed["scale"]):
        raise ValueError("exact checked trial598 geometry/current/source association required")
    center = np.ravel(center_seed["base_coefficients"]).copy()
    lower, upper = bounds(center, "control")
    if not np.array_equal(lower, arms[0]["lower_bounds"]) or not np.array_equal(
            upper, arms[0]["upper_bounds"]):
        raise ValueError("control must retain original absolute shape52-centered bounds")
    anchors = {k: trial["metrics"][k] for k in ("unit_flux", "scale", "normal_rms",
        "flux_normalized_raw", "flux_objective", "geometry_penalty", "min_b",
        "coil_distance", "surface_distance")}
    return seed, center, anchors


def search(model, record, anchors, lower, upper, directions, minimize):
    rows, best, feasible, checks, replay = [], None, None, [], {}
    initial = model.x0.copy()

    def evaluate(x, role):
        nonlocal best, feasible
        record.guard()
        if record.bundles >= BUNDLES:
            raise StopIteration("1200 total coarse bundles consumed")
        index = record.bundles
        record.bundles += 1
        record.active = dict(bundle=index, role=role)
        row = dict(index=index, role=role, x=np.asarray(x).tolist(), status="attempted",
                   native_before=copy.deepcopy(record.counts))
        name = f"trial-{index:04}"
        record.save(name+"-attempt.json", row)
        try:
            value, gradient, metrics = model.evaluate(x)
            row.update(value=value, gradient=gradient.tolist(), metrics=metrics, status="completed")
            record.guard()
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            row["native_after"] = copy.deepcopy(record.counts)
            record.save(name+".json", row)
        record.guard()
        rows.append(row)
        if role in ("startup-seed", "search"):
            if best is None or value < best["value"]:
                best = row
            if (metrics["sampled_geometry_limits_met"] and metrics["current_limit_met"]
                    and (feasible is None or metrics["normal_rms"]
                         < feasible["metrics"]["normal_rms"])):
                feasible = row
        return value, gradient

    startup_pass = False
    try:
        value, gradient = evaluate(initial, "startup-seed")
        replay = {k: dict(expected=v, actual=rows[0]["metrics"][k], passed=bool(
            np.isclose(v, rows[0]["metrics"][k], rtol=1e-10, atol=1e-12)))
            for k, v in anchors.items()}
        if not all(row["passed"] for row in replay.values()):
            raise ValueError("exact trial598 seed replay failed")
        for label, direction in directions.items():
            analytic = float(gradient@direction)
            for h in PROBE_STEPS:
                fd = (evaluate(initial+h*direction, "probe")[0]
                      - evaluate(initial-h*direction, "probe")[0])/(2*h)
                error = abs(fd-analytic)
                finite = bool(np.isfinite([fd, analytic, error]).all())
                checks.append(dict(direction=label, h=h, analytic=analytic if finite else None,
                                   fd=fd if finite else None, error=error if finite else None,
                                   finite=finite, passed=finite and (error <= 1e-7 or
                                   error <= 1e-4*max(abs(fd), abs(analytic)))))
                if not finite:
                    raise ValueError("nonfinite derived startup derivative arithmetic")
        repeat, repeated_gradient = evaluate(initial, "startup-repeat")
        startup_pass = (repeat == value and np.array_equal(repeated_gradient, gradient)
                        and all(row["passed"] for row in checks))
        if not startup_pass:
            raise ValueError("masked startup derivative or exact-repeat check failed")
        record.guard()
        solved = minimize(lambda x: evaluate(x, "search"), initial, jac=True, method="L-BFGS-B",
                          bounds=list(zip(lower, upper, strict=True)), options=dict(
                              maxiter=1190, maxfun=1190, maxls=20, ftol=1e-12, gtol=1e-9))
        record.guard()
        status = dict(reason="solver-return", success=bool(solved.success),
                      message=str(solved.message))
    except (TimeoutError, StopIteration) as exc:
        status = dict(reason="budget", error=str(exc))
    except Exception as exc:
        status = dict(reason="failure", error=f"{type(exc).__name__}: {exc}")
    chosen = feasible if feasible is not None else (rows[0] if rows else None)
    model.set_x(initial if chosen is None else np.asarray(chosen["x"]))
    return dict(status=status, startup_pass=startup_pass, seed_replay=replay,
                derivative_checks=checks, bundles_attempted=record.bundles,
                bundles_completed=len(rows),
                lowest_objective=best, lowest_feasible_rms=feasible, fine_selected=chosen,
                fine_selection="sampled-feasible" if feasible else "seed-fallback",
                startup_steps=list(PROBE_STEPS), physical_admission=False)


def fingerprints():
    result = paired.fingerprints()
    paths = [Path(__file__).resolve(), *(ROOT/name for name in INPUTS)]
    result.update({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    return result


def run(output):
    from scipy.optimize import minimize

    from fusion_baselines.provenance import git_state

    started = time.monotonic()
    if output.exists():
        raise FileExistsError("fresh matched-restart output directory required")
    if shutil.disk_usage(ROOT).free < previous.common.START_RESERVE:
        raise OSError("3 GiB starting reserve required")
    for name, digest in INPUTS.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"source identity changed: {name}")
    source = {name: json.loads((ROOT/name).read_text(encoding="utf-8"))
              for name in INPUTS if name.endswith(".json")}
    seed, center, anchors = seed_inputs(source)
    start = np.ravel(seed["base_coefficients"]).copy()
    free, directions = masked_directions(start, *bounds(center, "control"))
    overall = paired.Recorder(output, started+SECONDS, [0])
    report = dict(kind="matched-absolute-box-coherent-restarts", completed=False, arms=[],
                  sources_before=fingerprints(), repository=git_state(ROOT),
                  physical_admission=False,
                  optimizer_history_reset=True, seed_sha256=INPUTS[SNAPSHOT], seed_anchors=anchors,
                  center_sha256=INPUTS[paired.SNAPSHOT], center=center.tolist(),
                  free_startup_indices=np.flatnonzero(free).tolist(),
                  startup_directions={k: v.tolist() for k, v in directions.items()},
                  startup_mask_distance_m=2*max(PROBE_STEPS),
                  limits=dict(bundles_per_arm=BUNDLES, startup_bundles=10,
                              search_seconds=ARM_SECONDS, overall_seconds=SECONDS,
                              output_bytes=previous.common.MAX_BYTES),
                  solver_options=dict(maxiter=1190, maxfun=1190, maxls=20, ftol=1e-12, gtol=1e-9))
    overall.save("inputs.json", report)
    try:
        for arm in ARMS:
            overall.guard()
            record = paired.Recorder(output/arm, min(started+SECONDS, time.monotonic()+ARM_SECONDS),
                                     overall.storage)
            record.counts["independent_BA"] = dict(attempted=0, completed=0)
            lower, upper = bounds(center, arm)
            result = dict(arm=arm, fine=[], active_names=seed["names"], active_count=198,
                          lower_bounds=lower.tolist(), upper_bounds=upper.tolist(),
                          half_widths_m=((upper-lower)/2).tolist())
            report["arms"].append(result)
            record.save("seed.json", seed)
            record.save("bounds.json", result)
            try:
                with absolute_box(start, lower, upper):
                    record.guard()
                    model = previous.Model(seed, source[previous.common.INPUT], record,
                                           previous.active_indices("full"))
                    record.guard()
                    result["seed_identity_error"] = model.identity_error
                    result.update(search(model, record, anchors, lower, upper,
                                         directions, minimize))
                    record.save("search.json", result)
                    record.deadline = started+SECONDS
                    if result["startup_pass"] and result["status"]["reason"] != "failure":
                        for shift in (0., .5):
                            record.active = dict(fine_shift=shift)
                            result["fine"].append(previous.fine(seed, source[previous.common.INPUT],
                                previous.active_indices("full"), result["fine_selected"], record,
                                shift))
            except Exception as exc:
                result["execution_error"] = f"{type(exc).__name__}: {exc}"
            finally:
                result["counts"] = record.counts
                record.save("result.json", result)
                overall.save("progress.json", report)
        report["completed"] = len(report["arms"]) == 2 and all(not r.get("execution_error")
            and r.get("startup_pass") and len(r["fine"]) == 2 for r in report["arms"])
    except Exception as exc:
        report.update(completed=False, error=f"{type(exc).__name__}: {exc}")
    report["sources_after"] = fingerprints()
    report["sources_unchanged"] = report["sources_before"] == report["sources_after"]
    report["elapsed_s"] = time.monotonic()-started
    report["completed"] &= report["sources_unchanged"] and report["elapsed_s"] < SECONDS
    code = paired.publish(overall, report, started)
    print(json.dumps(dict(output=str(output), completed=report["completed"])))
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output.resolve()))
