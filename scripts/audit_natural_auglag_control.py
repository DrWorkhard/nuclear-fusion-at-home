"""Recompute the analytical AL solution and KKT residual without its solver."""

import argparse
import json
from pathlib import Path

from fusion_baselines.auglag_profile_audit import audit_analytic_control
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("control", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable output required")
    root = Path(__file__).resolve().parents[1]
    report = json.loads(args.control.read_text())
    checks = audit_analytic_control(report["analytic_control"])
    checks["control_only"] = bool(
        report["status"] == "control_completed"
        and report["arms"] == []
        and report["qualification_pass"] is False
    )
    refs = [report["protocol"], *report["code"], *report["solver_sources"]]
    checks["recorded_sources_unchanged"] = all(
        sha256_file(Path(ref["path"])) == ref["sha256"] for ref in refs
    )
    result = dict(
        repository=git_state(root),
        source=reference(args.control),
        checks=checks,
        all_pass=all(checks.values()),
        additional_physics_calls=0,
        scope="closed_form_control_only_not_physical_study_qualification",
        code=[
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/auglag_profile_audit.py"),
        ],
    )
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
