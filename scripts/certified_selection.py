"""Select the latest geometry-certified checkpoint of a completed coil fit (#109).

Re-reads a completed `scripts/fit_coils.py` run (recording v3) and certifies its
best-so-far points at fixed completed-bundle checkpoints, backward from the run's
selected point, with the shared continuous geometry check. Before any intermediate
point it must reproduce the run's selected snapshot and recorded geometry exactly.
The first certified point is written as `selected-snapshot.json`; run
`scripts/check_coils.py --snapshot` on it for the full checks. Selection is never
acceptance.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fusion_baselines import certified_selection as cs  # noqa: E402
from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402

RUN_FILES = ("seed.json", "inputs.json", "search.json", "result.json", "selected-snapshot.json",
             "vectors.f64")


def bounds(geometry):
    level = geometry["levels"][-1]
    g = level["geometry"]
    return dict(status=geometry["status"], ncoil=level["ncoil"], coil_lower=g["coil_lower"],
                length_upper=max(g["length_upper"]), plasma_lower=g["plasma_lower"],
                curvature_upper=max(c["maximum_upper_bound"] for c in level["curvature"]))


def run(source, output, wout, target_id, every=500, seconds=1800):
    check.need(isinstance(every, int) and every >= 1, "positive integer checkpoint spacing")
    check.need(np.isfinite(seconds) and 0 < seconds <= fit.MAX_CHECK_SECONDS,
               "certification budget at most 1800 s")
    check.need(all(os.environ.get(k) == "1" for k in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
        "MKL_NUM_THREADS")), "one-thread execution required")
    check.need(fit.shutil.disk_usage(ROOT).free >= fit.START_RESERVE,
               "3 GiB initial disk reserve required")
    started = time.monotonic()
    record = fit.Recorder(output, started+seconds)
    report = dict(kind="certified-selection", completed=False, outcome=None,
                  physical_admission=False, step4_pass=False, provenance=build_run_record(ROOT),
                  source_run=str(source), every=every, check_seconds=seconds, rule=cs.RULE,
                  gates={}, certificates=[], selected=None)
    try:
        data, _, sources, report["portable_target"] = check.portable_intake(
            wout, record.guard, target_id)
        code = [Path(__file__), *sorted((ROOT/"src/fusion_baselines").glob("*.py"))]
        sources.update({str(p.resolve()): check.digest(p) for p in code})
        for name in RUN_FILES:
            check.bind(source/name, check.digest(source/name), sources)
        report["sources_before"] = dict(sources)
        result = cs.read_json(source/"result.json")
        check.need(result.get("completed") is True and result.get("kind") == "normalized-coil-fit",
                   "completed fit_coils run required")
        check.need(result["portable_target"]["wout_sha256"]
                   == report["portable_target"]["wout_sha256"],
                   "the run's own target Wout required")
        seed = cs.read_json(source/"seed.json")
        check.snapshot_identity(seed, target_id)
        points = cs.checkpoints(source, every)
        record.guard()
        final = points[-1][1]
        check.need(final["index"] == result["search"]["selected"]["index"],
                   "recomputed selection differs from the run's")
        rebuilt = cs.canonical(cs.snapshot(seed, final, cs.vector(source, final["x_ref"])))
        same = rebuilt == cs.read_json(source/"selected-snapshot.json")
        report["gates"]["selected_snapshot_reproduced"] = same
        check.need(same, "rebuilt selected snapshot differs from the run's")
        search = result["search"]
        per_bundle = search["search_s"]/search["bundles_completed"]
        geometries = {}

        def certify(row):
            record.guard()
            snapshot = rebuilt if row is final else cs.canonical(
                cs.snapshot(seed, row, cs.vector(source, row["x_ref"])))
            check.snapshot_identity(snapshot, target_id)
            began = time.monotonic()
            geometry = cs.canonical(check.geometry(snapshot, data, record.guard))
            if row is final:
                same = geometry == result["geometry"]
                report["gates"]["recorded_geometry_reproduced"] = same
                check.need(same, "recomputed geometry differs from the run's record")
            geometries[row["index"]] = geometry, snapshot
            return dict(bounds(geometry), elapsed_s=time.monotonic()-began,
                        estimated_search_s=row["index"]*per_bundle,
                        search_elapsed_end_s=row.get("search_elapsed_end_s"))

        chosen = cs.select(points, certify, report["certificates"])
        report["outcome"] = "none certified" if chosen is None else "certified"
        if chosen is not None:
            geometry, snapshot = geometries[chosen["index"]]
            report["selected"] = dict(index=chosen["index"], metrics=chosen["metrics"],
                                      x_ref=chosen["x_ref"], geometry=geometry)
            record.save("selected-snapshot.json", snapshot)
        report["sources_after"] = {p: check.digest(p) for p in sources}
        check.need(sources == report["sources_after"], "source changed during execution")
        record.guard()
        report["completed"] = True
    except TimeoutError as exc:
        report.update(outcome=report["outcome"] or "none certified within budget",
                      error=f"TimeoutError: {exc}")
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    record.finish(report, started)
    print(json.dumps(dict(completed=report["completed"], outcome=report["outcome"],
                          output=str(output), certificates=len(report["certificates"]),
                          selected=None if report["selected"] is None
                          else report["selected"]["index"], physical_admission=False)))
    return 0 if report["completed"] and report["outcome"] == "certified" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, help="completed fit_coils.py output")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--target", choices=check.REGISTERED)
    target.add_argument("--target-spec", type=Path, help="frozen target specification (#115)")
    parser.add_argument("--wout", required=True, type=Path, help="the run's target Wout")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--every", type=int, default=500,
                        help="checkpoint spacing in completed bundles (default 500)")
    parser.add_argument("--seconds", type=float, default=1800,
                        help="certification budget, at most 1800 s")
    args = parser.parse_args()
    raise SystemExit(run(args.run.resolve(), args.output.resolve(), args.wout.resolve(),
                         check.load_target_spec(args.target_spec.resolve()) if args.target_spec
                         else args.target, args.every, args.seconds))
