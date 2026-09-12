"""Independent unchanged arm arithmetic with explicit alternate-start qualification binding."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fusion_baselines.auglag_profile_audit import audit_jac_profile
from fusion_baselines.inequality_audit import audit_inequality_arm
from fusion_baselines.natural_auglag_audit import audit_stages
from fusion_baselines.prefix_audit import audit_exact_prefix
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"input hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit output required")
    root = Path(__file__).resolve().parents[1]
    summary = args.study / "summary.json"
    study = json.loads(summary.read_text())
    if study["status"] != "completed" or study["methods"] != ["natural-auglag-jac"]:
        raise ValueError("completed Jacobian-scaled AL study required")
    control_path = root / "evidence/natural-auglag-jac-control-v1.json"
    control = json.loads(control_path.read_text())
    qpath = root / "evidence/upstream-start-qualification-v1.json"
    apath = root / "evidence/upstream-start-qualification-v1-audit.json"
    qualification = json.loads(qpath.read_text())
    qualification_audit = json.loads(apath.read_text())
    expected_code = control["code"] + [reference(root / p) for p in (
        "scripts/run_upstream_start.py", "scripts/prepare_upstream_start.py",
        "src/fusion_baselines/current_normalization.py")]
    if (
        study["start_id"] != "upstream-first-ranked-normalized-v1"
        or study["qualification"] != reference(qpath)
        or study["qualification_audit"] != reference(apath)
        or qualification["all_pass"] is not True
        or qualification_audit["all_pass"] is not True
        or qualification_audit["source"] != reference(qpath)
        or study["protocol"] != qualification["protocol"]
        or study["protocol"] != reference(root / "docs/optimization/UPSTREAM_START_PROTOCOL.md")
        or study["code"] != expected_code
        or study["qualified_backend_code"] != qualification["code"]
        or study["solver_sources"] != control["solver_sources"]
        or any(study["preparation"][k] != qualification["preparation"][k] for k in (
            "source", "current_factor", "canonical_total", "physical_currents", "surface", "case",
            "thresholds", "guarded_search_targets", "degrees_of_freedom"))
    ):
        raise ValueError("registered source, qualification, solver or physical profile changed")
    for ref in [study["protocol"], *study["code"], *study["solver_sources"],
                *qualification["code"], *qualification["installed_sources"]]:
        checked(ref)
    with np.load(checked(qualification["arrays"]), allow_pickle=False) as initial:
        qualified_x_hash = hashlib.sha256(initial["x"].tobytes()).hexdigest()
    arms, records = [], []
    for ref in study["arms"]:
        arm = json.loads(checked(ref).read_text())
        arms.append(arm)
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as data:
            checks = audit_inequality_arm(
                arm, data["x"], data["values"], expected_limit=1033, stop_profile="staged_al"
            )
            doc = json.loads(checked(arm["best"]["field"]).read_text())
            checks["named_field_identity"] = np.array_equal(
                data["x"], named_serialized_values(doc, study["preparation"]["degrees_of_freedom"])
            )
        checks["qualified_start_vector"] = arm["evaluations"][0]["x_sha256"] == qualified_x_hash
        checks.update(audit_stages(arm))
        n = arm["counters"]["attempts"]
        expected = dict(
            assemblies=n,
            assembly_attempts=n,
            failed_assemblies=0,
            native_covector_B_requests=n,
            coil_contractions=16 * n,
            geometry_derivative_requests=32 * n,
            current_VJP_requests=16 * n,
        )
        native = dict(
            evaluations=n,
            jacobian_evaluations=n,
            B_grid_requests=n,
            B_vjp_requests=n,
            position_requests=16 * n,
            position_derivative_requests=16 * n,
            curvature_requests=4 * n,
            curvature_derivative_requests=4 * n,
            native_metric_requests=12 * n,
            native_gradient_requests=12 * n,
            coil_pair_samples=4800000 * n,
            plasma_pair_samples=3276800 * n,
        )
        identities = arm["gn_identity_checks"]
        checks["native_and_spatial_work"] = arm["work"] == native and arm["gn_work"] == expected
        checks["all_coupled_identities"] = len(identities) == n and all(
            np.isfinite(row[k]) and 0 <= row[k] <= 1e-10
            for row in identities
            for k in (
                "field_relative_error",
                "gradient_normalized_error",
                "batch_field_relative_error",
                "projection_normalized_error",
            )
        )
        finest = arm["gradient_checks"][-1]
        exact, actual = np.asarray(finest["analytic"]), np.asarray(finest["finite_difference"])
        errors = np.abs(actual - exact) / np.maximum(1, np.abs(exact))
        checks["independent_gradient_screen"] = bool(
            [r["eps"] for r in arm["gradient_checks"]] == [1e-5, 1e-6, 1e-7, 1e-8]
            and exact.shape == actual.shape == (138,)
            and np.isfinite(errors).all()
            and errors.max() <= 1e-6
            and np.array_equal(errors, finest["normalized_errors"])
        )
        checks = {k: bool(v) for k, v in checks.items()}
        records.append(dict(arm=ref, checks=checks, all_pass=all(checks.values())))
    repeated = len(arms) == 2 and len(arms[0]["evaluations"]) == len(arms[1]["evaluations"])
    if repeated:
        repeated = audit_exact_prefix(
            arms[0]["evaluations"], arms[1]["evaluations"], length=len(arms[0]["evaluations"])
        )["all_pass"]
        repeated &= all(
            arms[0][k] == arms[1][k]
            for k in (
                "counters",
                "status",
                "stop_reason",
                "work",
                "gn_work",
                "stages",
                "residual_compositions",
            )
        )
    profile = audit_jac_profile(study, arms)
    result = dict(
        schema_version=1,
        repository=git_state(root),
        study=reference(summary),
        control=reference(control_path),
        qualification=reference(qpath),
        qualification_audit=reference(apath),
        profile_checks=profile,
        arms=records,
        repeated=bool(repeated),
        additional_physics_calls=0,
        physical_feasibility_certified=False,
        all_pass=bool(repeated and all(profile.values()) and all(r["all_pass"] for r in records)),
        code=[
            reference(root / p)
            for p in (
                "scripts/audit_upstream_study.py",
                "src/fusion_baselines/auglag_profile_audit.py",
                "src/fusion_baselines/natural_auglag_audit.py",
                "src/fusion_baselines/inequality_audit.py",
                "src/fusion_baselines/prefix_audit.py",
                "src/fusion_baselines/serialized_dofs.py",
            )
        ],
    )
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
