"""Fit one native reference401 snapshot, then check it with frozen-current diagnostics."""

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402


def run(snapshot_path, output, seconds=300, check_seconds=120, wout=None, target_id="reference401",
        order=None, task_id=None):
    from scipy.optimize import minimize

    check.need(np.isfinite([seconds, check_seconds]).all()
               and 0 < seconds <= 1800 and 0 < check_seconds <= 1800,
               "positive finite search/check budgets, at most 1800 seconds each")
    check.need(all(os.environ.get(k) == "1" for k in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
        "MKL_NUM_THREADS")), "one-thread execution required")
    check.need(fit.shutil.disk_usage(ROOT).free >= fit.START_RESERVE,
               "3 GiB initial disk reserve required")
    started = time.monotonic()
    record = fit.Recorder(output, started+seconds+check_seconds)
    report = dict(kind="normalized-coil-fit", completed=False, physical_admission=False,
                  step4_pass=False, provenance=build_run_record(ROOT),
                  search_seconds=seconds, check_seconds=check_seconds,
                  recording=fit.recording_settings(task_id or f"fixed-target/{target_id}"),
                  coefficient_bounds=None, solver_options=fit.SOLVER_OPTIONS, fine=[], interior=[])
    try:
        if wout is None:
            check.need(target_id == "reference401", "selected401 requires --wout")
            data, targets, sources = check.intake(record.guard)
        else:
            data, targets, sources, report["portable_target"] = check.portable_intake(
                wout, record.guard, target_id)
        snapshot_path = check.bind(snapshot_path, check.digest(snapshot_path), sources)
        seed = check.read_json(snapshot_path)
        check.snapshot_identity(seed, target_id)
        if order is not None and order != seed["order"]:
            # Same geometry with exactly zero higher modes; recorded as the seed actually fitted.
            seed = fit.lift_order(seed, order)
            check.snapshot_identity(seed, target_id)
        # Record the code actually executed, not every old experiment that produced the seed.
        from importlib import import_module

        modules = ("simsoptpp", "simsopt.field.biotsavart", "simsopt.geo.curveobjectives",
                   "simsopt.geo.curvexyzfourier", "simsopt._core.optimizable",
                   "simsopt.objectives.fluxobjective", "scipy.optimize._lbfgsb_py",
                   "scipy.optimize._lbfgsb")
        paths = [Path(__file__), *sorted((ROOT/"src/fusion_baselines").glob("*.py")),
                 *(Path(import_module(m).__file__) for m in modules)]
        sources.update({str(p.resolve()): check.digest(p) for p in paths})
        report["sources_before"] = sources
        record.save("seed.json", seed)
        record.save("inputs.json", report)
        deadline = record.deadline
        record.deadline = min(deadline, started+seconds)
        report["intake_s"] = time.monotonic()-started
        model = fit.Model(seed, data, record)
        report["model_ready_s"] = time.monotonic()-started
        report["search"] = fit.search(model, record, minimize)
        record.save("search.json", report["search"])
        record.deadline = min(deadline, time.monotonic()+check_seconds)
        search = report["search"]
        check.need(search["startup_pass"] and search["status"]["reason"] != "failure"
                   and search["selected"] is not None,
                   "completed headroom candidate and passing startup required")
        for shift in (0., .5):
            report["fine"].append(fit.fine(seed, data, search["selected"], record, shift))
        snapshot = check.read_json(output/"selected-snapshot.json")
        check.snapshot_identity(snapshot, target_id)
        report["geometry"] = check.geometry(snapshot, data, record.guard)
        interior = check.Recorder(output/"interior", record.deadline, record.storage)
        for i, (n, nodes) in enumerate(check.LEVELS):
            row, arrays = check.screen_level(snapshot, data, targets[n], n, nodes, interior)
            buffer = io.BytesIO()
            np.savez_compressed(buffer, **arrays)
            interior.write(f"level-{i}.npz", buffer.getvalue())
            row["arrays_sha256"] = check.digest(interior.output/f"level-{i}.npz")
            interior.write(f"level-{i}.json", row)
            report["interior"].append(row)
            check.need(row["checks_pass"], "interior numerical check failed")
        report["interior_refinements"] = check.refinements(report["interior"])
        report["interior_native_counts"] = interior.counts
        report["sources_after"] = {p: check.digest(p) for p in sources}
        check.need(sources == report["sources_after"], "source changed during execution")
        record.guard()
        report["completed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["native_counts"] = record.counts
    # A final bounded failure record may be written after the compute deadline.
    record.finish(report, started)
    print(json.dumps(dict(completed=report["completed"], output=str(output),
                          physical_admission=False)))
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--check-seconds", type=float, default=120)
    parser.add_argument("--target", choices=tuple(check.TARGETS), default="reference401")
    parser.add_argument("--wout", type=Path, help="portable reference401 Wout (see docs)")
    parser.add_argument("--order", type=int, choices=(5, 8),
                        help="lift the snapshot to this Fourier order with zero new modes")
    parser.add_argument("--task-id",
                        help="experiment task identity (default: fixed-target/<target>)")
    args = parser.parse_args()
    raise SystemExit(run(args.snapshot.resolve(), args.output.resolve(), args.seconds,
                         args.check_seconds, None if args.wout is None else args.wout.resolve(),
                         args.target, args.order, args.task_id))
