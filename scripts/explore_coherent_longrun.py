"""Two wall-clock-limited restarts; reuse the normalized model and fine checker."""

import argparse
import copy
import json
import math
import os
import time
from contextlib import contextmanager
from pathlib import Path

import explore_coherent_restart as restart
import numpy as np
import screen_coherent_interior as screen

from fusion_baselines.provenance import git_state

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "artifacts/coherent-restart-v1/run/result.json"
RESULT_SHA = "fe4ffe0a4b0908fc9bd2736643b87b8908f53d9417c0801af119db075c5d1317"
ARMS = {"same-box": (.12, .02), "wider-box": (.16, .04)}
ARM_SECONDS, TOTAL_SECONDS = 300, 660
SOLVER_OPTIONS = dict(maxiter=2**31-1, maxfun=2**31-1, maxls=20, ftol=1e-12, gtol=1e-9)


def bounds(center, arm):
    screen.need(arm in ARMS and np.shape(center) == (198,) and np.isfinite(center).all(),
                "named arm and finite shape52 center required")
    low, high = ARMS[arm]
    widths = np.full(198, high)
    widths[restart.previous.active_indices("low2")] = low
    return center-widths, center+widths


@contextmanager
def wall_clock_search():
    """Remove only the old bundle cap in this isolated, serial experiment process."""
    before = restart.BUNDLES
    screen.need(before == 1200, "unmodified restart settings required")
    restart.BUNDLES = math.inf
    try:
        yield
    finally:
        restart.BUNDLES = before


def solver_adapter(minimize):
    def solve(function, initial, **kwargs):
        # SciPy requires integer ceilings; the 300 s guard is the stopping budget.
        # Keep tolerances/method unchanged and disclose these nonbinding ceilings.
        kwargs["options"] = SOLVER_OPTIONS.copy()
        return minimize(function, initial, **kwargs)
    return solve


def geometry(snapshot, data, guard):
    from fusion_baselines.clear_coil_field_audit import json_value
    from fusion_baselines.coupled_coil_audit import geometry_certificates
    from fusion_baselines.curvature_bounds import classify_enclosure, curvature_enclosure

    levels = []
    for nc, ns, nk in ((1024, 512, 1024), (2048, 1024, 4096)):
        guard()
        g = geometry_certificates(snapshot, data, nc, ns, ns)
        guard()
        curvature = [curvature_enclosure(c, nk) for c in snapshot["base_coefficients"]]
        states = [classify_enclosure(c, 12) for c in curvature]
        passed = (max(g["length_upper"]) <= 3.5 and g["coil_lower"] >= .06
                  and g["plasma_lower"] >= .08 and all(s == "pass" for s in states))
        witness = (any(s == "fail" for s in states)
                   or min(p["sampled"] for p in g["coil_pairs"]) < .06
                   or min(p["sampled"] for p in g["plasma_distances"]) < .08)
        levels.append(dict(ncoil=nc, nsurface=ns, ncurvature=nk, geometry=g,
                           curvature=curvature, status="pass" if passed else
                           "fail" if witness else "unresolved"))
        guard()
        if passed or witness:
            break
    return json_value(dict(status=levels[-1]["status"], levels=levels, interval_arithmetic=False,
                           complete_self_disjointness=False, physical_admission=False))


def run(output):
    from scipy.optimize import minimize

    started = time.monotonic()
    screen.need(all(os.environ.get(k) == "1" for k in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
        "MKL_NUM_THREADS")), "one-thread execution required")
    screen.need(screen.shutil.disk_usage(ROOT).free >= 3*1024**3, "3 GiB reserve required")
    data, _, states, sources = screen.intake(RESULT, RESULT_SHA)
    seed = copy.deepcopy(states[-1]["snapshot"])
    center = np.ravel(states[1]["snapshot"]["base_coefficients"])
    start = np.ravel(seed["base_coefficients"])
    saved = screen.read_json(RESULT)["arms"][1]["fine_selected"]
    screen.need(saved["index"] == 1198 and np.array_equal(saved["x"], start),
                "exact expanded-low trial1198 required")
    anchors = {key: saved["metrics"][key] for key in (
        "unit_flux", "scale", "normal_rms", "flux_normalized_raw", "flux_objective",
        "geometry_penalty", "min_b", "coil_distance", "surface_distance")}
    free, directions = restart.masked_directions(start, *bounds(center, "same-box"))
    sources = screen.fingerprints(sources)
    for path in (Path(__file__), ROOT/"tests/test_explore_coherent_longrun.py"):
        sources[str(path.resolve())] = screen.digest(path)
    record = restart.paired.Recorder(output, started+TOTAL_SECONDS, [0])
    report = dict(kind="wall-clock-coherent-restarts", completed=False, arms=[],
                  sources_before=sources, repository=git_state(ROOT), seed=seed,
                  start_index=1198, absolute_center=center.tolist(),
                  masked_startup_indices=np.flatnonzero(free).tolist(),
                  solver_options=SOLVER_OPTIONS, bundle_cap=None,
                  arm_seconds=ARM_SECONDS, total_seconds=TOTAL_SECONDS,
                  physical_admission=False, step4_pass=False)
    record.save("inputs.json", report)
    try:
        with wall_clock_search():
            for arm in ARMS:
                record.guard()
                arm_started = time.monotonic()
                worker = restart.paired.Recorder(output/arm,
                    min(record.deadline, time.monotonic()+ARM_SECONDS), record.storage)
                worker.counts["independent_BA"] = dict(attempted=0, completed=0)
                lower, upper = bounds(center, arm)
                row = dict(arm=arm, fine=[], lower_bounds=lower.tolist(),
                           upper_bounds=upper.tolist(), active_names=seed["names"],
                           active_count=198, physical_admission=False)
                report["arms"].append(row)
                with restart.absolute_box(start, lower, upper):
                    model = restart.previous.Model(seed, data, worker, np.arange(198))
                    # Reuse the tested startup/replay/selection routine. Its old
                    # diagnostic label says trial598; anchors here bind trial1198.
                    row.update(restart.search(model, worker, anchors, lower, upper,
                                             directions, solver_adapter(minimize)))
                    row["search_elapsed_s"] = time.monotonic()-arm_started
                    worker.deadline = record.deadline
                    worker.save("search.json", row)
                    if not row["startup_pass"] or row["status"]["reason"] == "failure":
                        raise ValueError(f"{arm} search failed; retain failed prefix")
                    for shift in (0., .5):
                        row["fine"].append(restart.previous.fine(
                            seed, data, np.arange(198), row["fine_selected"], worker, shift))
                    snapshot = screen.read_json(worker.output/"selected-snapshot.json")
                    row["snapshot_sha256"] = screen.digest(worker.output/"selected-snapshot.json")
                    row["geometry"] = geometry(snapshot, data, record.guard)
                    row["native_counts"] = worker.counts
                    worker.save("result.json", row)
        report["sources_after"] = {p: screen.digest(p) for p in sources}
        report["sources_unchanged"] = sources == report["sources_after"]
        report["completed"] = report["sources_unchanged"] and len(report["arms"]) == 2
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["elapsed_s"] = time.monotonic()-started
    code = restart.paired.publish(record, report, started)
    print(json.dumps(dict(completed=report["completed"], output=str(output))))
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    raise SystemExit(run(parser.parse_args().output.resolve()))
