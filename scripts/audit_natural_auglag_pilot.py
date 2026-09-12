"""Independent arithmetic, work and named-field audit of the staged AL study."""

import argparse
import json
from pathlib import Path

import numpy as np

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
    parser.add_argument(
        "--interrupted-v1",
        action="store_true",
        help="postmortem only: never qualify the incomplete original study",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit output required")
    root = Path(__file__).resolve().parents[1]
    summary = args.study / "summary.json"
    study = json.loads(summary.read_text())
    incident = None
    if args.interrupted_v1:
        incident_path = root / "evidence/resource-interruption-2026-09-12.json"
        incident = json.loads(incident_path.read_text())["natural_al_run"]
        if (
            summary.resolve() != (root / incident["report"]).resolve()
            or sha256_file(summary) != incident["sha256"]
            or study["status"] != "running"
            or len(study["arms"]) != 1
        ):
            raise ValueError("only the hash-pinned interrupted v1 study is allowed")
        for key, digest in (
            ("completed_arm", "completed_arm_sha256"),
            ("partial_arm", "partial_arm_sha256"),
        ):
            if sha256_file(root / incident[key]) != incident[digest]:
                raise ValueError("interrupted evidence hash mismatch")
    elif study["status"] != "completed":
        raise ValueError("completed staged natural-AL study required")
    if study["methods"] != ["natural-auglag"]:
        raise ValueError("natural-AL study required")
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
    result = dict(
        schema_version=1,
        repository=git_state(root),
        study=reference(summary),
        arms=records,
        repeated=bool(repeated),
        additional_physics_calls=0,
        physical_feasibility_certified=False,
        all_pass=bool(repeated and all(r["all_pass"] for r in records)),
        code=[
            reference(root / p)
            for p in (
                "scripts/audit_natural_auglag_pilot.py",
                "src/fusion_baselines/natural_auglag_audit.py",
                "src/fusion_baselines/inequality_audit.py",
                "src/fusion_baselines/prefix_audit.py",
                "src/fusion_baselines/serialized_dofs.py",
            )
        ],
    )
    if incident is not None:
        partial = json.loads((root / incident["partial_arm"]).read_text())
        length = incident["last_persisted_second_arm_bundles"]
        prefix = audit_exact_prefix(arms[0]["evaluations"], partial["evaluations"], length=length)
        result.update(
            scope="postmortem_complete_arm_and_saved_prefix_only",
            incident=reference(incident_path),
            partial_arm=reference(root / incident["partial_arm"]),
            partial_prefix=prefix,
            postmortem_integrity_pass=bool(
                len(records) == 1
                and records[0]["all_pass"]
                and prefix["all_pass"]
                and partial["status"] == "running"
                and len(partial["evaluations"]) == partial["counters"]["attempts"] == length
                and "best" not in partial
            ),
            all_pass=False,
            study_complete=False,
        )
    write_json_atomic(args.output, result)
    print(
        json.dumps({k: result[k] for k in ("all_pass", "postmortem_integrity_pass") if k in result})
    )
    if incident is not None:
        return 0 if result["postmortem_integrity_pass"] else 2
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
