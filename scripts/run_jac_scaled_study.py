"""Require closed, committed recovery holdouts before the registered scaled study."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from run_coil_holdouts import validate_phase

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.resource_guard import GIB, guarded_run, space_check


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"prerequisite hash mismatch: {path}")
    return path


def require_closed(record):
    if (
        record.get("status") != "completed"
        or record.get("all_four_phases_completed") is not True
        or [r["name"] for r in record["steps"]] != ["holdout", "curvature", "clearance", "native"]
        or any(r["status"] != "completed" for r in record["steps"])
        or record.get("used_for_optimizer_feedback") is not False
    ):
        raise ValueError("all four original holdout phases must be completed")


def require_committed(root, path):
    relative = path.resolve().relative_to(root)
    content = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root)
    if hashlib.sha256(content).hexdigest() != sha256_file(path):
        raise ValueError(f"prerequisite must be committed unchanged: {relative}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    for path in (args.output, args.study, args.raw):
        if path.exists():
            raise FileExistsError(f"new immutable output required: {path}")
    prior = root / "evidence/natural-auglag-recovery-v1-validation/summary.json"
    record = json.loads(prior.read_text())
    require_closed(record)
    expected_study = root / "evidence/natural-auglag-recovery-v1/summary.json"
    if record["study"] != reference(expected_study):
        raise ValueError("the unchanged original recovery must precede this variant")
    for phase in record["steps"]:
        path = checked(phase["result"])
        validate_phase(phase["name"], json.loads(path.read_text()), phase["returncode"])
        checked(phase["source"])
        checked(phase["log"])
        require_committed(root, path)
    prefix_path = root / "evidence/natural-auglag-recovery-driver-v1/recovery-audit.json"
    prefix = json.loads(prefix_path.read_text())
    if prefix["all_pass"] is not True or prefix["study"] != reference(expected_study):
        raise ValueError("passing original-prefix recovery audit required")
    require_committed(root, prior)
    detail = root / "docs/optimization/NATURAL_AUGLAG_RECOVERY_RESULTS.md"
    require_committed(root, detail)
    args.output.mkdir(parents=True)
    report = dict(
        repository=git_state(root),
        code=reference(Path(__file__)),
        prior_validation=reference(prior),
        prior_documentation=reference(detail),
        prior_prefix_audit=reference(prefix_path),
        status="running",
        steps=[],
        physical_feasibility_certified=False,
        holdouts_pending=True,
    )

    def checkpoint():
        write_json_atomic(args.output / "summary.json", report)

    audit = args.output / "audit.json"
    phases = [
        ("two-scaled-arms", ["scripts/run_natural_auglag_jac.py", args.study, args.raw]),
        ("independent-audit", ["scripts/audit_natural_auglag_jac.py", args.study, audit]),
    ]
    try:
        report["disk_preflight"] = space_check(root, 2 * GIB)
        checkpoint()
        for name, arguments in phases:
            log = args.output / f"{name}.log"
            row = dict(
                name=name,
                command=[sys.executable, *map(str, arguments)],
                status="running",
                source=reference(root / arguments[0]),
            )
            report["steps"].append(row)
            checkpoint()
            print(f"Scaled AL: {name}", flush=True)
            with log.open("xb") as stream:
                row.update(
                    guarded_run(
                        row["command"],
                        cwd=root,
                        env=os.environ,
                        stdout=stream,
                        space_root=root,
                        reserve_bytes=2 * GIB,
                    )
                )
            row.update(log=reference(log), status="passed" if row["returncode"] == 0 else "failed")
            checkpoint()
            if row["returncode"]:
                raise RuntimeError(f"{name} failed: {row['returncode']}")
        report.update(status="completed", all_pass=True, audit=reference(audit))
    except Exception as error:
        report.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        active_error = sys.exc_info()[0] is not None
        try:
            checkpoint()
        except OSError as error:
            print(f"Scaled-study checkpoint failed: {error}", file=sys.stderr)
            if not active_error:
                raise


if __name__ == "__main__":
    main()
