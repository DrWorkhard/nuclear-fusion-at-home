"""Require both fixed historical prefixes and unchanged mathematical/solver sources."""

import argparse
import json
from pathlib import Path

from fusion_baselines.prefix_audit import audit_exact_prefix
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


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
    parser.add_argument("pilot_audit", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable recovery audit required")
    root = Path(__file__).resolve().parents[1]
    old_path = root / "evidence/natural-auglag-pilot-v1/summary.json"
    incident_path = root / "evidence/resource-interruption-2026-09-12.json"
    incident = json.loads(incident_path.read_text())["natural_al_run"]
    if sha256_file(old_path) != incident["sha256"]:
        raise ValueError("original study hash changed")
    old = json.loads(old_path.read_text())
    new_path = args.study / "summary.json"
    new = json.loads(new_path.read_text())
    audit = json.loads(args.pilot_audit.read_text())
    checks = dict(
        completed=new["status"] == "completed",
        qualified=new["qualification_pass"] is True,
        independent_pilot_audit=audit["all_pass"] is True,
        audit_bound=checked(audit["study"]) == new_path.resolve(),
        same_math_code=old["code"] == new["code"],
        same_solver_code=old["solver_sources"] == new["solver_sources"],
        same_options=old["solver_options"] == new["solver_options"],
        same_threads=old["thread_environment"] == new["thread_environment"],
        original_protocol=old["protocol"] == new["protocol"],
        two_arms=len(new["arms"]) == 2,
    )
    for ref in new["code"] + new["solver_sources"]:
        checked(ref)
    prefixes = []
    if checks["two_arms"]:
        for repeat, (key, hash_key, length) in enumerate(
            (
                ("completed_arm", "completed_arm_sha256", 1033),
                ("partial_arm", "partial_arm_sha256", 700),
            ),
            1,
        ):
            historic_path = root / incident[key]
            if sha256_file(historic_path) != incident[hash_key]:
                raise ValueError("original arm hash changed")
            historic = json.loads(historic_path.read_text())
            fresh_path = checked(new["arms"][repeat - 1])
            fresh = json.loads(fresh_path.read_text())
            prefix = audit_exact_prefix(
                historic["evaluations"], fresh["evaluations"], length=length
            )
            checks[f"repeat{repeat}_historical_prefix"] = (
                prefix["all_pass"] and fresh["repeat"] == repeat
            )
            prefixes.append(
                dict(
                    repeat=repeat,
                    original=reference(historic_path),
                    fresh=reference(fresh_path),
                    **prefix,
                )
            )
    result = dict(
        schema_version=1,
        repository=git_state(root),
        study=reference(new_path),
        pilot_audit=reference(args.pilot_audit),
        incident=reference(incident_path),
        protocol=reference(root / "docs/optimization/NATURAL_AUGLAG_RECOVERY_PROTOCOL.md"),
        checks=checks,
        prefixes=prefixes,
        all_pass=all(checks.values()),
        additional_physics_calls=0,
        physical_feasibility_certified=False,
        original_study_reclassified_as_complete=False,
        code=reference(Path(__file__)),
    )
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
