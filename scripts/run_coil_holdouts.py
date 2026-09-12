"""Run all four existing coil holdouts sequentially; retain physical rejections."""

import argparse
import json
import os
import sys
from pathlib import Path

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.resource_guard import GIB, guarded_run, space_check


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def validate_phase(name, record, returncode):
    """Completion and admission are different; rejection must not hide later checks."""
    if name in {"holdout", "native"}:
        if record.get("status") != "completed" or len(record.get("candidates", [])) != 2:
            raise ValueError("completed two-candidate report required")
        if type(record.get("all_pass")) is not bool:
            raise ValueError("explicit physical result required")
        expected = 0 if record["all_pass"] else 2
        if returncode != expected:
            raise ValueError("physical flag and process exit disagree")
    elif name == "curvature":
        if returncode != 0 or record.get("status") != "completed" or len(record["fields"]) != 3:
            raise ValueError("complete three-field curvature report required")
        if any(len(row["levels"]) != 7 for row in record["fields"]):
            raise ValueError("all seven curvature levels required")
    elif name == "clearance":
        if returncode != 0 or len(record.get("candidates", [])) != 2:
            raise ValueError("two-candidate clearance report required")
    else:
        raise ValueError("unregistered phase")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("audit", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable validation directory required")
    root = Path(__file__).resolve().parents[1]
    summary = args.study / "summary.json"
    study, audit = json.loads(summary.read_text()), json.loads(args.audit.read_text())
    if (
        study["status"] != "completed"
        or study["qualification_pass"] is not True
        or len(study["arms"]) != 2
        or audit["all_pass"] is not True
        or audit["study"] != reference(summary)
    ):
        raise ValueError("qualified two-arm study with bound passing independent audit required")
    args.output.mkdir(parents=True)
    report = dict(
        repository=git_state(root),
        code=reference(Path(__file__)),
        study=reference(summary),
        audit=reference(args.audit),
        status="running",
        steps=[],
        full_engineering_admission=False,
        used_for_optimizer_feedback=False,
    )

    def checkpoint():
        write_json_atomic(args.output / "summary.json", report)

    holdout = args.output / "holdout.json"
    phases = [
        (
            "holdout",
            ["scripts/validate_normalized_candidates.py", args.study, holdout, "--all-repeats"],
        ),
        (
            "curvature",
            [
                "scripts/bound_continuous_curvature.py",
                args.output / "curvature.json",
                "--holdout",
                holdout,
                "--study",
                summary,
            ],
        ),
        (
            "clearance",
            ["scripts/bound_continuous_coil_clearance.py", holdout, args.output / "clearance.json"],
        ),
        (
            "native",
            ["scripts/validate_direct_native_constraints.py", holdout, args.output / "native.json"],
        ),
    ]
    try:
        report["disk_preflight"] = space_check(root, 2 * GIB)
        checkpoint()
        for name, arguments in phases:
            path, log = args.output / f"{name}.json", args.output / f"{name}.log"
            row = dict(
                name=name,
                command=[sys.executable, *map(str, arguments)],
                status="running",
                source=reference(root / arguments[0]),
            )
            report["steps"].append(row)
            checkpoint()
            print(f"Coil validation: {name}", flush=True)
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
            row["log"] = reference(log)
            checkpoint()
            data = json.loads(path.read_text())
            validate_phase(name, data, row["returncode"])
            row.update(status="completed", result=reference(path))
            checkpoint()
        report.update(status="completed", all_four_phases_completed=True)
    except Exception as error:
        report.update(
            status="error",
            all_four_phases_completed=False,
            error=f"{type(error).__name__}: {error}",
        )
        raise
    finally:
        active_error = sys.exc_info()[0] is not None
        try:
            checkpoint()
        except OSError as error:
            print(f"Validation checkpoint failed: {error}", file=sys.stderr)
            if not active_error:
                raise


if __name__ == "__main__":
    main()
