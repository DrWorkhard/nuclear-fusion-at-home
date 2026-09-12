"""Wait for successful fresh native integration, then run the unchanged AL study."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.resource_guard import GIB, guarded_run, space_check


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def native_ready(record):
    if record["status"] in {"error", "failed"}:
        raise ValueError("fresh native integration failed; no automatic search")
    if record["status"] != "completed":
        return False
    if not record.get("all_pass") or record.get("copied_solver_outputs") is not False:
        raise ValueError("completed fresh native integration did not pass")
    expected = {"fresh-vmecpp-w7x", "fresh-vmec852-w7x", "strict-six-test-integration"}
    selected = [r for r in record["steps"] if r["name"] in expected]
    if (
        len(selected) != len(expected)
        or {r["name"] for r in selected} != expected
        or any(r["status"] != "passed" for r in selected)
    ):
        raise ValueError("required fresh solver/test phases missing")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("driver_output", type=Path)
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--after-native", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    for path in (args.driver_output, args.study, args.raw):
        if path.exists():
            raise FileExistsError(f"new immutable output required: {path}")
    args.driver_output.mkdir(parents=True)
    original = json.loads((root / "evidence/natural-auglag-pilot-v1/summary.json").read_text())
    report = dict(
        schema_version=1,
        repository=git_state(root),
        status="waiting_for_native",
        steps=[],
        protocol=reference(root / "docs/optimization/NATURAL_AUGLAG_RECOVERY_PROTOCOL.md"),
        native_summary_path=str(args.after_native.resolve()),
        code=reference(Path(__file__)),
        original_math_code=original["code"],
        study_path=str(args.study.resolve()),
        raw_path=str(args.raw.resolve()),
    )

    def checkpoint():
        write_json_atomic(args.driver_output / "summary.json", report)

    def run(name, arguments):
        path = args.driver_output / f"{len(report['steps']) + 1:02}-{name}.log"
        row = dict(name=name, command=[sys.executable, *map(str, arguments)], status="running")
        report["steps"].append(row)
        checkpoint()
        print(f"AL recovery: {name}", flush=True)
        with path.open("xb") as log:
            row.update(
                guarded_run(
                    row["command"],
                    cwd=root,
                    env=os.environ,
                    stdout=log,
                    space_root=root,
                    reserve_bytes=2 * GIB,
                )
            )
        row.update(log=reference(path), status="passed" if row["returncode"] == 0 else "failed")
        checkpoint()
        if row["returncode"]:
            raise RuntimeError(f"{name} failed: {row['returncode']}")

    try:
        checkpoint()
        started = time.monotonic()
        while not native_ready(json.loads(args.after_native.read_text())):
            if time.monotonic() - started > 7200:
                raise TimeoutError("two-hour native prerequisite wait exhausted; no search started")
            time.sleep(2)
        report["native_prerequisite"] = reference(args.after_native)
        report["disk_preflight"] = space_check(root, 2 * GIB)
        for ref in original["code"] + original["solver_sources"]:
            if sha256_file(Path(ref["path"])) != ref["sha256"]:
                raise ValueError(f"original math/solver source changed: {ref['path']}")
        report["status"] = "running"
        run("two-fresh-arms", ["scripts/run_natural_auglag_pilot.py", args.study, args.raw])
        pilot_audit = args.driver_output / "pilot-audit.json"
        run(
            "independent-pilot-audit",
            ["scripts/audit_natural_auglag_pilot.py", args.study, pilot_audit],
        )
        recovery_audit = args.driver_output / "recovery-audit.json"
        run(
            "historical-prefix-audit",
            ["scripts/audit_natural_auglag_recovery.py", args.study, pilot_audit, recovery_audit],
        )
        report.update(
            status="completed",
            all_pass=True,
            physical_feasibility_certified=False,
            holdouts_pending=True,
            recovery_audit=reference(recovery_audit),
        )
    except Exception as error:
        report.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        active_error = sys.exc_info()[0] is not None
        try:
            checkpoint()
        except OSError as error:
            print(f"Recovery checkpoint failed; prior state retained: {error}", file=sys.stderr)
            if not active_error:
                raise


if __name__ == "__main__":
    main()
