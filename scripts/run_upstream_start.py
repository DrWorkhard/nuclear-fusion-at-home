"""Registered alternate-start study using the unchanged qualified AL arm kernel."""

import argparse
import json
import os
from pathlib import Path

import numpy as np
from prepare_upstream_start import prepare
from run_jac_scaled_study import require_committed
from run_natural_auglag_jac import analytic_control, checked, reference, run_arm
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.jac_scaled_solver import EFFECTIVE_OPTIONS
from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.serialized_field_state import serialized_state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.study.exists() or args.raw.exists():
        raise FileExistsError("new immutable study/raw paths required")
    root = Path(__file__).resolve().parents[1]
    qpath = root / "evidence/upstream-start-qualification-v1.json"
    apath = root / "evidence/upstream-start-qualification-v1-audit.json"
    qualification, audit = json.loads(qpath.read_text()), json.loads(apath.read_text())
    if (not qualification["all_pass"] or not audit["all_pass"]
            or audit["source"] != reference(qpath)):
        raise ValueError("passing bound alternate-start qualification and audit required")
    prerequisites = (qpath, apath, Path(__file__),
                     root / "docs/optimization/UPSTREAM_START_RESULTS.md")
    for path in prerequisites:
        require_committed(root, path)
    control_path = root / "evidence/natural-auglag-jac-control-v1.json"
    control = json.loads(control_path.read_text())
    code = control["code"] + [reference(root / p) for p in (
        "scripts/run_upstream_start.py", "scripts/prepare_upstream_start.py",
        "src/fusion_baselines/current_normalization.py")]
    for ref in [*code, *control["solver_sources"], *qualification["code"],
                *qualification["installed_sources"], qualification["protocol"]]:
        checked(ref)
    args.study.mkdir(parents=True)
    args.raw.mkdir(parents=True)
    report = dict(
        repository=git_state(root), host=host_state(), status="running", qualification_pass=False,
        protocol=qualification["protocol"], start_id="upstream-first-ranked-normalized-v1",
        qualification=reference(qpath), qualification_audit=reference(apath),
        control=reference(control_path), code=code, qualified_backend_code=qualification["code"],
        solver_sources=control["solver_sources"], solver_options=EFFECTIVE_OPTIONS,
        methods=["natural-auglag-jac"], arms=[], flux_scale=1e-6, construction_tolerance=1e-8,
        thread_environment={k: os.environ.get(k) for k in
                            ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")},
    )
    try:
        report["analytic_control"] = analytic_control()
        if not report["analytic_control"]["pass_control"]:
            raise ValueError("unchanged analytic control failed")
        ctx, prep = prepare(root, args.raw)
        expected = qualification["preparation"]
        if any(prep[k] != expected[k] for k in (
            "source", "current_factor", "canonical_total", "physical_currents", "surface", "case",
            "thresholds", "guarded_search_targets", "degrees_of_freedom")):
            raise ValueError("qualified physical start or named basis changed")
        actual_state = serialized_state(json.loads(checked(prep["normalized_start"]).read_text()))
        old_state = serialized_state(json.loads(checked(expected["normalized_start"]).read_text()))
        for key, values in actual_state.items():
            if not np.array_equal(values, old_state[key]):
                raise ValueError("qualified serialized source parameters changed")
        full = SurfaceRZFourier.from_vmec_input(
            str(checked(prep["surface"])), range="full torus", nphi=64, ntheta=64)
        direct, x0 = DirectConstraintBackend(ctx, full), ctx.Jf.x.copy()
        with np.load(checked(qualification["arrays"]), allow_pickle=False) as arrays:
            if not np.array_equal(x0, arrays["x"]):
                raise ValueError("qualified named start vector changed")
        report.update(preparation=prep, labels=direct.labels)
        write_json_atomic(args.study / "summary.json", report)
        runs = []
        for repeat in (1, 2):
            output = args.study / f"natural-auglag-jac-{repeat}.json"
            runs.append(run_arm(direct, ctx, x0, args.raw / output.stem, output, repeat))
            report["arms"].append(reference(output))
            write_json_atomic(args.study / "summary.json", report)
        a, b = runs
        checks = dict(
            gradient_screens=all(r["gradient_screen_pass"] for r in runs),
            same_counters=a["counters"] == b["counters"], same_stages=a["stages"] == b["stages"],
            same_stop=a["status"] == b["status"] and a["stop_reason"] == b["stop_reason"],
            identical_complete_histories=len(a["evaluations"]) == len(b["evaluations"])
            and all(x["x_sha256"] == y["x_sha256"] and x["values"] == y["values"]
                    for x, y in zip(a["evaluations"], b["evaluations"], strict=True)),
            same_best=a["best"]["x_sha256"] == b["best"]["x_sha256"],
            same_work=a["work"] == b["work"] and a["gn_work"] == b["gn_work"],
        )
        report.update(status="completed", checks=checks, qualification_pass=all(checks.values()))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.study / "summary.json", report)
    print(json.dumps({"qualification_pass": report["qualification_pass"]}))
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
