"""Two registered SLSQP polishing repeats after independent fixed-start qualification."""

import argparse
import inspect
import json
import os
from pathlib import Path

import numpy as np
import scipy.optimize._slsqplib as slsqp_binary
from prepare_upstream_start import prepare
from run_composite_slsqp_arm import run_arm
from run_direct_slsqp_pilot import checked, reference
from run_jac_scaled_study import require_committed
from scipy.optimize._slsqp_py import _minimize_slsqp
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_field_state import serialized_state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.study.exists() or args.raw.exists():
        raise FileExistsError("new immutable composite polishing required")
    root = Path(__file__).resolve().parents[1]
    qp = root / "evidence/polish-start-derivatives-v1.json"
    ap = root / "evidence/polish-start-derivatives-v1-audit.json"
    q, audit = (json.loads(p.read_text()) for p in (qp, ap))
    if (q["status"] != "completed" or not q["all_pass"] or not audit["all_pass"]
            or audit["source"] != reference(qp)
            or q["source_field"]["sha256"] !=
            "65b9b85e942fa3ce54467ad29c319b92f1c2756489df4f668e563aa49d5836eb"
            or q["arrays"]["sha256"] !=
            "9ee89d4ca82a9d104b8d5bf5e2b814bd12962cdcd1f4bc0385099527879250ad"):
        raise ValueError("fixed independently qualified source required")
    failed = json.loads(checked(q["failed_study"]).read_text())
    failed_arm = json.loads(checked(q["failed_arm"]).read_text())
    for ref in [*q["code"], *q["qualified_backend_code"], *q["installed_sources"],
                *audit["code"], failed["source_study"], failed["source_audit"],
                failed["source_holdouts"], q["failure_audit"]]:
        checked(ref)
    code = [root / p for p in (
        "scripts/run_composite_polish.py", "scripts/run_composite_slsqp_arm.py",
        "src/fusion_baselines/composite_start_gate.py", "scripts/prepare_upstream_start.py",
        "src/fusion_baselines/selected_start.py", "src/fusion_baselines/inequality_oracle.py",
        "src/fusion_baselines/affine_coordinates.py", "src/fusion_baselines/direct_constraints.py")]
    protocol = root / "docs/optimization/SLSQP_COMPOSITE_PROTOCOL.md"
    for p in [qp, ap, protocol, *code, checked(q["failed_study"]), checked(q["failed_arm"])]:
        require_committed(root, p)
    source_doc = json.loads(checked(q["source_field"]).read_text())
    args.study.mkdir(parents=True)
    args.raw.mkdir(parents=True)
    report = dict(repository=git_state(root), host=host_state(), status="running",
                  qualification_pass=False, methods=["slsqp"], arms=[],
                  protocol=reference(protocol), qualification=reference(qp),
                  qualification_audit=reference(ap), failed_study=q["failed_study"],
                  failed_arm=q["failed_arm"], source_study=failed["source_study"],
                  source_audit=failed["source_audit"], source_holdouts=failed["source_holdouts"],
                  code=[reference(p) for p in code],
                  solver_sources=[reference(Path(inspect.getfile(inspect.unwrap(_minimize_slsqp)))),
                                  reference(Path(slsqp_binary.__file__))],
                  solver_options=dict(method="SLSQP", ftol=1e-10, maxiter=100000,
                                      jacobian="analytic", bundle_limit=2048),
                  source_construction_bundles_per_path=1033, nominal_hybrid_cap_per_path=3081,
                  prior_diagnostic_work=dict(failed_startup_bundles=9,
                                             additional_native_qualification_bundles=1,
                                             native_position_requests=16,
                                             complex_pair_value_evaluations=7,
                                             complex_squared_distance_samples=33600000,
                                             audit_squared_distance_samples=4800000,
                                             audit_directional_distance_samples=9600000),
                  flux_scale=1e-6, construction_tolerance=1e-8,
                  thread_environment={k: os.environ.get(k) for k in (
                      "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")})
    try:
        ctx, prep = prepare(root, args.raw)
        if any(prep[k] != failed["preparation"][k] for k in (
                "surface", "case", "thresholds", "guarded_search_targets", "canonical_total")):
            raise ValueError("fixed physical problem changed")
        target_doc = json.loads(checked(prep["normalized_start"]).read_text())
        with np.load(checked(q["arrays"]), allow_pickle=False) as data:
            x0, p, owners = mapped_start(source_doc, target_doc, q["source_names"],
                                         prep["degrees_of_freedom"], data["x"])
            qualified = dict(x=x0.copy(), values=data["values"].copy(),
                             jacobian=data["jacobian"][:, p].copy(),
                             direction=data["directions"][0, p].copy())
        ctx.Jf.x = x0.copy()
        start_path = args.raw / "physical_start.json"
        ctx.Jf.field.save(str(start_path))
        actual = serialized_state(json.loads(start_path.read_text()))
        expected = serialized_state(source_doc)
        if any(not np.array_equal(actual[k], expected[k]) for k in actual):
            raise ValueError("physical start state changed")
        full = SurfaceRZFourier.from_vmec_input(str(checked(prep["surface"])), range="full torus",
                                               nphi=64, ntheta=64)
        backend = DirectConstraintBackend(ctx, full)
        report.update(preparation=prep, labels=backend.labels,
                      source_indices_in_target_order=p.tolist(), owner_map=owners,
                      physical_start=reference(start_path))
        write_json_atomic(args.study / "summary.json", report)
        arms = []
        for repeat in (1, 2):
            path = args.study / f"slsqp-{repeat}.json"
            arms.append(run_arm(backend, ctx, x0, args.raw / path.stem, path, repeat,
                                qualified=qualified, source_permutation=p,
                                failed_arm=failed_arm, budget=2048))
            report["arms"].append(reference(path))
            write_json_atomic(args.study / "summary.json", report)
        a, b = arms
        checks = dict(composite_gates=all(r["gradient_screen_pass"] for r in arms),
                      same_counters=a["counters"] == b["counters"],
                      same_stop=(a["status"], a["stop_reason"]) == (b["status"], b["stop_reason"]),
                      same_work=a["work"] == b["work"],
                      same_best=a["best"]["x_sha256"] == b["best"]["x_sha256"],
                      identical_complete_histories=len(a["evaluations"]) == len(b["evaluations"])
                      and all(u["x_sha256"] == v["x_sha256"] and u["values"] == v["values"]
                              for u, v in zip(a["evaluations"], b["evaluations"], strict=True)))
        report.update(status="completed", checks=checks, qualification_pass=all(checks.values()))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.study / "summary.json", report)
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
