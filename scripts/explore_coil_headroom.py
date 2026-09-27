"""Restart the wider fit with construction length margin; acceptance is unchanged."""

import argparse
import io
import json
import os
import time
from pathlib import Path

import explore_coherent_longrun as prior
import numpy as np

from fusion_baselines.provenance import git_state

s, restart = prior.screen, prior.restart
ROOT = prior.ROOT
SOURCE = ROOT / "artifacts/coherent-longrun-v2/run/result.json"
SOURCE_SHA = "f0fe739a8eee398961278012686c8c778fae0832e3e4ade7c84ae5a212cb9a1a"
PENALTY_LENGTH, SELECT_LENGTH = 3.44, 3.45
SEARCH_SECONDS, TOTAL_SECONDS = 300, 360


class Model(restart.previous.Model):
    def __init__(self, *args, **kwargs):
        from simsopt.geo import LpCurveCurvature
        from simsopt.objectives import QuadraticPenalty

        super().__init__(*args, **kwargs)
        # Only the construction objective changes. Shared metrics still use 3.5 m.
        self.geometry = (sum(QuadraticPenalty(term, PENALTY_LENGTH, "max")
                             for term in self.lengths)
                         + 1000*self.cc + 1000*self.cp
                         + 1e-2*sum(LpCurveCurvature(c, 2, threshold=10) for c in self.curves))


def select(rows, completed):
    """Prospective selection, excluding probes and deadline-interrupted points."""
    eligible = []
    for row in rows:
        if (row.get("status") != "completed" or row.get("role") not in ("search", "startup-seed")
                or not 0 <= row["index"] < completed):
            continue
        metrics = row["metrics"]
        lengths = np.asarray(metrics["lengths"])
        s.need(lengths.shape == (6,) and np.isfinite(lengths).all()
               and np.isfinite(metrics["normal_rms"]), "finite six-coil selection required")
        if (metrics["sampled_geometry_limits_met"] and metrics["current_limit_met"]
                and max(lengths) <= SELECT_LENGTH):
            eligible.append(row)
    s.need(bool(eligible), "no completed candidate meets construction length margin")
    return min(eligible, key=lambda r: (r["metrics"]["normal_rms"], r["index"]))


def run(output):
    from scipy.optimize import minimize

    started = time.monotonic()
    s.need(all(os.environ.get(k) == "1" for k in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
        "MKL_NUM_THREADS")), "one-thread execution required")
    s.need(s.shutil.disk_usage(ROOT).free >= 3*1024**3, "3 GiB initial reserve required")
    record = restart.paired.Recorder(output, started+TOTAL_SECONDS, [0])
    report = dict(kind="construction-length-headroom", completed=False, arms=[],
                  repository=git_state(ROOT), physical_admission=False, step4_pass=False,
                  construction_penalty_length=PENALTY_LENGTH,
                  construction_selection_length=SELECT_LENGTH, acceptance_length=3.5,
                  search_seconds=SEARCH_SECONDS, total_seconds=TOTAL_SECONDS,
                  source=dict(path=str(SOURCE), sha256=SOURCE_SHA))
    try:
        data, targets, states, sources = s.intake(prior.RESULT, prior.RESULT_SHA, record.guard)
        s.bind(SOURCE, SOURCE_SHA, sources)
        previous = s.read_json(SOURCE)
        seed, association = s.selected_snapshot(previous, SOURCE.parent, "wider-box", sources,
                                                 width=4)
        s.need(association["selected_index"] == 1561, "exact wider-box trial1561 required")
        center = np.ravel(states[1]["snapshot"]["base_coefficients"])
        start = np.ravel(seed["base_coefficients"])
        lower, upper = prior.bounds(center, "wider-box")
        _, directions = restart.masked_directions(start, lower, upper)
        chosen_before = previous["arms"][1]["fine_selected"]
        anchors = {k: chosen_before["metrics"][k] for k in (
            "unit_flux", "scale", "normal_rms", "flux_normalized_raw", "flux_objective",
            "min_b", "coil_distance", "surface_distance")}
        # Geometry penalty intentionally differs; replay the unchanged field state.
        sources = s.fingerprints(sources)
        for path in (Path(__file__), ROOT/"tests/test_explore_coil_headroom.py"):
            s.bind(path, s.digest(path), sources)
        report.update(sources_before=sources, seed=seed, seed_association=association,
                      absolute_center=center.tolist(), solver_options=prior.SOLVER_OPTIONS,
                      bundle_cap=None)
        record.save("inputs.json", report)
        arm = dict(arm="headroom", active_names=seed["names"], active_count=198,
                   lower_bounds=lower.tolist(), upper_bounds=upper.tolist(), fine=[], interior=[])
        report["arms"].append(arm)
        worker = restart.paired.Recorder(output/"headroom",
                    min(record.deadline, time.monotonic()+SEARCH_SECONDS), record.storage)
        worker.counts["independent_BA"] = dict(attempted=0, completed=0)
        search_start = time.monotonic()
        with prior.wall_clock_search(), restart.absolute_box(start, lower, upper):
            model = Model(seed, data, worker, np.arange(198))
            arm.update(restart.search(model, worker, anchors, lower, upper, directions,
                                      prior.solver_adapter(minimize)))
            arm["search_elapsed_s"] = time.monotonic()-search_start
            worker.deadline = record.deadline
            worker.save("search.json", arm)
            s.need(arm["startup_pass"] and arm["status"]["reason"] != "failure",
                   "headroom search startup/execution failed; retain prefix")
            rows = [s.read_json(p) for p in sorted(worker.output.glob("trial-*.json"))
                    if not p.name.endswith("-attempt.json")]
            arm["search_selected"] = arm["fine_selected"]
            arm["fine_selected"] = select(rows, arm["bundles_completed"])
            arm["fine_selection"] = "lowest-normal-rms-with-construction-length-margin"
            worker.save("selection.json", dict(index=arm["fine_selected"]["index"],
                rule=arm["fine_selection"], maximum_sampled_length=SELECT_LENGTH))
            for shift in (0., .5):
                arm["fine"].append(restart.previous.fine(
                    seed, data, np.arange(198), arm["fine_selected"], worker, shift))
        snapshot = s.read_json(worker.output/"selected-snapshot.json")
        s.snapshot_identity(snapshot, arm["fine_selected"])
        arm["snapshot_sha256"] = s.digest(worker.output/"selected-snapshot.json")
        arm["geometry"] = prior.geometry(snapshot, data, record.guard)
        interior = s.Recorder(output/"interior", record.deadline)
        for i, (n, nodes) in enumerate(s.LEVELS):
            row, arrays = s.screen_level(snapshot, data, targets[n], n, nodes, interior)
            buffer = io.BytesIO()
            np.savez_compressed(buffer, **arrays)
            interior.write(f"level-{i}.npz", buffer.getvalue())
            row["arrays"] = dict(path=str(interior.output/f"level-{i}.npz"),
                                  sha256=s.digest(interior.output/f"level-{i}.npz"))
            interior.write(f"level-{i}.json", row)
            arm["interior"].append(row)
            s.need(row["checks_pass"], "interior numerical check failed")
        arm["interior_refinements"] = s.refinements(arm["interior"])
        arm["native_counts"], arm["interior_counts"] = worker.counts, interior.counts
        arm["interior_points"] = interior.points
        worker.save("result.json", arm)
        report["sources_after"] = {p: s.digest(p) for p in sources}
        report["sources_unchanged"] = sources == report["sources_after"]
        report["completed"] = report["sources_unchanged"]
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
