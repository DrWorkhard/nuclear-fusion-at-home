"""Sequential frozen six-mesh study; requires closed coil search and all four holdouts."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from mesh_nonlocal_inputs import checked, frozen_inputs, source_code_bindings
from run_jac_scaled_study import require_committed

from fusion_baselines.mesh_nonlocal_scan import reference
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check

CODE = (
    "scripts/run_mesh_nonlocal.py", "scripts/mesh_nonlocal_worker.py",
    "scripts/mesh_nonlocal_inputs.py", "src/fusion_baselines/mesh_nonlocal_scan.py",
    "src/fusion_baselines/tetra_broad_phase.py", "src/fusion_baselines/tetra_nonoverlap.py",
    "src/fusion_baselines/evidence_integrity.py",
)


def closed_predecessor(root):
    paths = [root / p for p in (
        "evidence/slsqp-composite-v1/summary.json", "evidence/slsqp-composite-v1-audit.json",
        "evidence/slsqp-composite-v1-validation/summary.json")]
    study, audit, holdout = [json.loads(p.read_text()) for p in paths]
    if (study["status"] != "completed" or not study["qualification_pass"]
            or len(study["arms"]) != 2
            or not audit["all_pass"] or audit["study"] != reference(paths[0])
            or holdout["status"] != "completed" or not holdout["all_four_phases_completed"]
            or holdout["study"] != reference(paths[0]) or holdout["audit"] != reference(paths[1])):
        raise ValueError("closed independently audited composite study and all holdouts required")
    for path in paths:
        require_committed(root, path)
    for step in holdout["steps"]:
        checked(step["result"])
    if [s["name"] for s in holdout["steps"]] != ["holdout", "curvature", "clearance", "native"]:
        raise ValueError("all four original holdout phases required")
    return [reference(p) for p in paths]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.study.exists() or args.raw.exists():
        raise FileExistsError("new immutable six-mesh study required")
    root = Path(__file__).resolve().parents[1]
    previous = closed_predecessor(root)
    source_path, source = frozen_inputs(root)
    protocol = root / "docs/engineering/MESH_NONLOCAL_PROTOCOL.md"
    retry = root / "docs/engineering/MESH_NONLOCAL_RETRY_PROTOCOL.md"
    for path in [protocol, retry, source_path, *(root / p for p in CODE)]:
        require_committed(root, path)
    disk = space_check(root, 3*GIB)
    args.study.mkdir(parents=True)
    args.raw.mkdir(parents=True)
    report = dict(repository=git_state(root), status="running", all_six_terminal=False,
                  all_nonlocal_screens_pass=False, source=reference(source_path),
                  predecessor=previous, protocol=reference(protocol), disk_preflight=disk,
                  retry_protocol=reference(retry),
                  historical_source_code=source_code_bindings(root, source),
                  code=[reference(root / p) for p in CODE],
                  meshes=[dict(index=i, mesh=r["mesh"], target_h_m=r["target_h_m"],
                               status="not_started") for i, r in enumerate(source["meshes"])],
                  complete_engineering_admission=False)
    output = args.study / "summary.json"
    def checkpoint():
        write_json_atomic(output, report)
    try:
        checkpoint()
        for row in report["meshes"]:
            space_check(root, 2*GIB)
            i = row["index"]
            worker_out, raw = args.study / f"mesh-{i}.json", args.raw / f"mesh-{i}"
            log = args.study / f"mesh-{i}.log"
            command = [sys.executable, "scripts/mesh_nonlocal_worker.py", str(i),
                       str(worker_out), str(raw)]
            row.update(status="running", command=command, hard_timeout_seconds=1200)
            checkpoint()
            print("Nonlocal mesh", i, row["target_h_m"], flush=True)
            with log.open("xb") as stream:
                try:
                    completed = subprocess.run(command, cwd=root, env=os.environ, stdout=stream,
                                               stderr=subprocess.STDOUT, timeout=1200, check=False)
                    row.update(returncode=completed.returncode, status="process_failed")
                except subprocess.TimeoutExpired:
                    row.update(status="timeout", returncode=None)
            row["log"] = reference(log)
            if worker_out.exists():
                row["worker"] = reference(worker_out)
                worker = json.loads(worker_out.read_text())
                if (worker["status"] == "completed" and row["returncode"] == (
                        0 if worker["nonlocal_screen_pass"] else 2)):
                    row.update(status="completed", complete_scan=worker["complete_scan"],
                               nonlocal_screen_pass=worker["nonlocal_screen_pass"])
            checkpoint()
        report.update(status="completed", all_six_terminal=True,
                      all_nonlocal_screens_pass=all(r.get("nonlocal_screen_pass", False)
                                                    for r in report["meshes"]))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        checkpoint()
    return 0 if report["all_nonlocal_screens_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
