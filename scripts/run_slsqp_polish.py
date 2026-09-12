"""Registered SLSQP polishing using the unchanged budget-parametric arm kernel."""

import argparse
import inspect
import json
import os
from pathlib import Path

import numpy as np
import scipy.optimize._slsqplib as slsqp_binary
from prepare_upstream_start import prepare
from run_direct_slsqp_pilot import checked, reference, run_arm
from run_jac_scaled_study import require_committed
from scipy.optimize._slsqp_py import _minimize_slsqp
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.selected_start import initial_error, mapped_start
from fusion_baselines.serialized_field_state import serialized_state


class SelectedBackend(DirectConstraintBackend):
    def reset_start_guard(self, x, values):
        self.expected_x, self.expected_values = x.copy(), values.copy()
        self.start_verified, self.initial_replay_error = False, None

    def evaluate(self, x):
        if not self.start_verified and not np.array_equal(x, self.expected_x):
            raise ValueError("first counted request must be the selected physical start")
        values, jacobian, metrics = super().evaluate(x)
        if not self.start_verified:
            self.initial_replay_error = initial_error(values, self.expected_values)
            self.start_verified = True
        return values, jacobian, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.study.exists() or args.raw.exists():
        raise FileExistsError("new immutable polishing study required")
    root = Path(__file__).resolve().parents[1]
    old_path = root / "evidence/upstream-start-study-v1/summary.json"
    audit_path = root / "evidence/upstream-start-study-v1-audit.json"
    holdout_path = root / "evidence/upstream-start-study-v1-validation/summary.json"
    old, audit, holdout = [json.loads(p.read_text()) for p in (old_path, audit_path, holdout_path)]
    if (old["status"] != "completed" or not old["qualification_pass"] or not audit["all_pass"]
            or audit["study"] != reference(old_path) or not holdout["all_four_phases_completed"]
            or holdout["study"] != reference(old_path)):
        raise ValueError("completed independently audited source construction/holdouts required")
    qi_path = root / "evidence/qi-fresh-resolution-v1-evaluation.json"
    qi_audit_path = root / "evidence/qi-fresh-resolution-v1-evaluation-audit.json"
    qi, qi_audit = [json.loads(p.read_text()) for p in (qi_path, qi_audit_path)]
    if (qi["status"] != "completed" or not qi_audit["all_pass"]
            or qi_audit["source"] != reference(qi_path)):
        raise ValueError("fresh QI matrix/evaluation must be closed first")
    code = [root / p for p in (
        "scripts/run_slsqp_polish.py", "src/fusion_baselines/selected_start.py",
        "scripts/run_direct_slsqp_pilot.py", "scripts/prepare_upstream_start.py",
        "src/fusion_baselines/inequality_oracle.py", "src/fusion_baselines/affine_coordinates.py")]
    protocol = root / "docs/optimization/SLSQP_POLISH_PROTOCOL.md"
    for path in [*code, protocol, old_path, audit_path, holdout_path, qi_path, qi_audit_path]:
        require_committed(root, path)
    qualification = json.loads(checked(old["qualification"]).read_text())
    for ref in [*qualification["code"], *qualification["installed_sources"]]:
        checked(ref)
    selected_ref = old["arms"][0]
    selected = json.loads(checked(selected_ref).read_text())
    if (selected["best"]["field"]["sha256"] !=
            "6ee2a013254b2f30195291dfd4d13c6a166d06d5286cb966db92a2646db2fb5f"
            or selected["best"]["arrays"]["sha256"] !=
            "31dab61fb28d060c9e9f6c21905396cc469dad738c6931928dfe39fa4e250d14"):
        raise ValueError("registered AL-selected state changed")
    args.study.mkdir(parents=True)
    args.raw.mkdir(parents=True)
    report = dict(repository=git_state(root), host=host_state(), status="running",
                  qualification_pass=False, methods=["slsqp"], arms=[],
                  protocol=reference(protocol),
                  code=[reference(p) for p in code], qualified_backend_code=qualification["code"],
                  source_study=reference(old_path), source_audit=reference(audit_path),
                  source_holdouts=reference(holdout_path), selected_source=selected_ref,
                  closed_qi=reference(qi_path), closed_qi_audit=reference(qi_audit_path),
                  solver_sources=[reference(Path(inspect.getfile(inspect.unwrap(_minimize_slsqp)))),
                                  reference(Path(slsqp_binary.__file__))],
                  solver_options=dict(method="SLSQP", ftol=1e-10, maxiter=100000,
                                      jacobian="analytic", bundle_limit=2048),
                  source_construction_bundles_per_path=1033, hybrid_cap_per_path=3081,
                  flux_scale=1e-6, construction_tolerance=1e-8,
                  thread_environment={k: os.environ.get(k) for k in (
                      "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")})
    try:
        ctx, preparation = prepare(root, args.raw)
        for k in ("surface", "case", "thresholds", "guarded_search_targets", "canonical_total"):
            if preparation[k] != old["preparation"][k]:
                raise ValueError("registered physical problem changed")
        source = json.loads(checked(selected["best"]["field"]).read_text())
        target = json.loads(checked(preparation["normalized_start"]).read_text())
        with np.load(checked(selected["best"]["arrays"]), allow_pickle=False) as saved:
            x0, permutation, owners = mapped_start(
                source, target, old["preparation"]["degrees_of_freedom"],
                preparation["degrees_of_freedom"], saved["x"])
            expected_values = saved["values"].copy()
        ctx.Jf.x = x0.copy()
        start_field = args.raw / "polish_start.json"
        ctx.Jf.field.save(str(start_field))
        actual = serialized_state(json.loads(start_field.read_text()))
        expected = serialized_state(source)
        if any(not np.array_equal(actual[k], expected[k]) for k in expected):
            raise ValueError("mapped physical coefficients/currents/regularizations changed")
        full = SurfaceRZFourier.from_vmec_input(str(checked(preparation["surface"])),
                                               range="full torus", nphi=64, ntheta=64)
        backend = SelectedBackend(ctx, full)
        report.update(preparation=preparation, labels=backend.labels,
                      source_indices_in_target_order=permutation.tolist(), owner_map=owners,
                      physical_start=reference(start_field), initial_replays=[])
        write_json_atomic(args.study / "summary.json", report)
        runs = []
        for repeat in (1, 2):
            backend.reset_start_guard(x0, expected_values)
            path = args.study / f"slsqp-{repeat}.json"
            runs.append(run_arm(backend, ctx, x0, args.raw / path.stem, path, repeat, budget=2048))
            report["initial_replays"].append(backend.initial_replay_error)
            report["arms"].append(reference(path))
            write_json_atomic(args.study / "summary.json", report)
        a, b = runs
        checks = dict(same_counters=a["counters"] == b["counters"],
                      same_stop=a["status"] == b["status"] and a["stop_reason"] == b["stop_reason"],
                      gradient_screens=all(r["gradient_screen_pass"] for r in runs),
                      same_work=a["work"] == b["work"],
                      identical_complete_histories=len(a["evaluations"]) == len(b["evaluations"])
                      and all(x["x_sha256"] == y["x_sha256"] and x["values"] == y["values"]
                              for x, y in zip(a["evaluations"], b["evaluations"], strict=True)),
                      same_best=a["best"]["x_sha256"] == b["best"]["x_sha256"])
        report.update(status="completed", checks=checks, qualification_pass=all(checks.values()))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.study / "summary.json", report)
    return 0 if report["qualification_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
