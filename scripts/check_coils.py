"""Run the shared fine-field, geometry and interior checks on one coil set, without fitting.

Accepts a native snapshot or a public candidate. With --wout, the reference401
interior target is rebuilt from that Wout and accepted only if it reproduces the
public starter's samples, so the checks run outside the maintainer's workspace.
"""

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


def run(output, snapshot=None, candidate=None, wout=None, seconds=600):
    check.need((snapshot is None) != (candidate is None), "exactly one snapshot or candidate")
    check.need(np.isfinite(seconds) and 0 < seconds <= 1800, "check budget at most 1800 s")
    check.need(all(os.environ.get(k) == "1" for k in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
        "MKL_NUM_THREADS")), "one-thread execution required")
    check.need(fit.shutil.disk_usage(ROOT).free >= fit.START_RESERVE,
               "3 GiB initial disk reserve required")
    started = time.monotonic()
    record = fit.Recorder(output, started+seconds)
    report = dict(kind="coil-check-only", completed=False, physical_admission=False,
                  step4_pass=False, provenance=build_run_record(ROOT), check_seconds=seconds,
                  fine=[], interior=[])
    try:
        if wout is None:
            data, targets, sources = check.intake(record.guard)
        else:
            data, targets, sources, report["portable_target"] = check.portable_intake(
                wout, record.guard)
        if candidate is not None:
            path = check.bind(candidate, check.digest(candidate), sources)
            seed = check.candidate_snapshot(check.read_json(path), data)
        else:
            path = check.bind(snapshot, check.digest(snapshot), sources)
            seed = check.read_json(path)
            check.snapshot_identity(seed)
        report["sources_before"] = dict(sources)
        record.save("seed.json", seed)
        chosen = dict(index=-1, x=np.asarray(seed["base_coefficients"]).ravel(),
                      metrics=dict(scale=seed["scale"], unit_flux=seed["unit_flux"]))
        for shift in (0., .5):
            report["fine"].append(fit.fine(seed, data, chosen, record, shift))
        selected = check.read_json(output/"selected-snapshot.json")
        check.snapshot_identity(selected)
        report["geometry"] = check.geometry(selected, data, record.guard)
        interior = check.Recorder(output/"interior", record.deadline, record.storage)
        for i, (n, nodes) in enumerate(check.LEVELS):
            row, arrays = check.screen_level(selected, data, targets[n], n, nodes, interior)
            buffer = io.BytesIO()
            np.savez_compressed(buffer, **arrays)
            interior.write(f"level-{i}.npz", buffer.getvalue())
            row["arrays_sha256"] = check.digest(interior.output/f"level-{i}.npz")
            interior.write(f"level-{i}.json", row)
            report["interior"].append(row)
            check.need(row["checks_pass"], "interior numerical check failed")
        report["interior_refinements"] = check.refinements(report["interior"])
        report["sources_after"] = {p: check.digest(p) for p in sources}
        check.need(sources == report["sources_after"], "source changed during execution")
        record.guard()
        report["completed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["native_counts"] = record.counts
    record.finish(report, started)
    summary = dict(completed=report["completed"], output=str(output), physical_admission=False)
    if report["completed"]:
        summary.update(
            normal_rms=[row["metrics"].get("normal_rms") for row in report["fine"]],
            normal_max=[row["metrics"].get("normal_max") for row in report["fine"]],
            interior_rms=[row["metrics"].get("vector_rms") for row in report["interior"]],
            geometry=report["geometry"]["status"])
    print(json.dumps(summary))
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--snapshot", type=Path)
    source.add_argument("--candidate", type=Path, help="public six-coil candidate JSON")
    parser.add_argument("--wout", type=Path, help="portable reference401 Wout")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seconds", type=float, default=600)
    args = parser.parse_args()
    paths = [None if p is None else p.resolve() for p in (args.snapshot, args.candidate, args.wout)]
    raise SystemExit(run(args.output.resolve(), *paths, args.seconds))
