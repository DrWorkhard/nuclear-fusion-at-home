"""Exploratory Step 3 action comparison on target-labelled, actual coil-field lines."""

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))

from fusion_baselines import coil_bounce as bounce  # noqa: E402
from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402
from fusion_baselines.realized_field import Target  # noqa: E402
from fusion_baselines.vmec_trace import trace_geometry  # noqa: E402


def run(snapshot_path, wout, target_id, output, seconds=600, nphi=801, nalpha=16):
    from simsopt.field import BiotSavart

    check.need(0 < seconds <= 1800 and nphi in (801, 1601) and nalpha in (16, 32),
               "bounded registered diagnostic resolution and budget required")
    check.need(all(os.environ.get(k) == "1" for k in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
        "MKL_NUM_THREADS")), "one-thread execution required")
    check.need(fit.shutil.disk_usage(ROOT).free >= fit.START_RESERVE,
               "3 GiB initial disk reserve required")
    started = time.monotonic()
    record = fit.Recorder(output, started+seconds)
    report = dict(kind="target-launch-coil-bounce", completed=False, target_id=target_id,
                  provenance=build_run_record(ROOT), resolution=[nphi, nalpha, 2],
                  surfaces=[], physical_admission=False, benefit_transfer_confirmed=False,
                  limitation="target launch labels are not verified realized flux coordinates")
    try:
        sources = {}
        spec = check.target_spec(target_id)
        input_path = check.bind(ROOT/spec["input"], spec["input_sha256"], sources)
        check.bind(wout, spec["wout_sha256"], sources)
        check.bind(snapshot_path, check.digest(snapshot_path), sources)
        for path in [Path(__file__), *sorted((ROOT/"src/fusion_baselines").glob("*.py"))]:
            check.bind(path, check.digest(path), sources)
        report["sources_before"] = sources
        record.save("inputs.json", report)
        snapshot = check.read_json(snapshot_path)
        coils, _, checks = check.native_coils(snapshot, 512, target_id)
        report.update(coil_mapping_checks=checks, current_A=1e5*snapshot["scale"],
                      frozen_current=True)
        field = BiotSavart(coils)
        target = Target.from_wout(wout, check.read_json(input_path))
        for s in bounce.SURFACES:
            record.guard()
            ideal = trace_geometry(wout, s, nphi, nalpha, 2)
            record.guard()
            actual = bounce.trace_coils(field, target, s, ideal, record.guard)
            row = dict(s=s, ideal=bounce.measure(ideal), coil=bounce.measure(actual))
            for label, arrays in (("ideal", ideal), ("coil", actual)):
                buffer = io.BytesIO()
                np.savez_compressed(buffer, **arrays)
                name = f"{label}-s{s}.npz"
                record.save(name, buffer.getvalue())
                row[label]["arrays_sha256"] = check.digest(output/name)
            report["surfaces"].append(row)
            record.save("progress-diagnostic.json", report)
        for label in ("ideal", "coil"):
            rows = [r[label] for r in report["surfaces"]]
            report[label+"_wide_score"] = (None if any(r["errors"] for r in rows) else
                float(np.mean([r["score"] for r in rows])))
            narrow = [c for r in report["surfaces"] if r["s"] in (0.25, 0.5, 0.75)
                      for c in r[label]["cells"] if c["q"] in (0.1, 0.3, 0.5, 0.7, 0.9)]
            report[label+"_narrow_score"] = (float(np.mean([c["score"] for c in narrow]))
                                             if len(narrow) == 15 else None)
        report["sources_after"] = {p: check.digest(p) for p in sources}
        check.need(sources == report["sources_after"], "sources changed during diagnostic")
        record.guard()
        report["completed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    record.finish(report, started)
    print(json.dumps({k: v for k, v in report.items() if k in (
        "completed", "error", "ideal_wide_score", "coil_wide_score", "ideal_narrow_score",
        "coil_narrow_score", "elapsed_s", "benefit_transfer_confirmed")}))
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--wout", type=Path, required=True)
    parser.add_argument("--target", choices=tuple(check.TARGETS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--nphi", type=int, choices=(801, 1601), default=801)
    parser.add_argument("--nalpha", type=int, choices=(16, 32), default=16)
    args = parser.parse_args()
    raise SystemExit(run(args.snapshot.resolve(), args.wout.resolve(), args.target,
                         args.output.resolve(), args.seconds, args.nphi, args.nalpha))
