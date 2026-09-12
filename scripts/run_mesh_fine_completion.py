"""Separate bounded finest-mesh study with closed QI/mesh predecessor bindings."""

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

CODE = ("scripts/run_mesh_fine_completion.py", "scripts/mesh_fine_completion_worker.py",
        "scripts/mesh_nonlocal_inputs.py", "src/fusion_baselines/mesh_nonlocal_scan.py",
        "src/fusion_baselines/tetra_broad_phase.py", "src/fusion_baselines/tetra_nonoverlap.py",
        "src/fusion_baselines/evidence_integrity.py")


def predecessors(root):
    paths = [root/p for p in ("evidence/mesh-nonlocal-v2/summary.json",
                              "evidence/mesh-nonlocal-v2-audit.json",
                              "evidence/qi-pest-fidelity-v1.json",
                              "evidence/qi-pest-fidelity-v1-audit.json")]
    mesh, ma, qi, qa = [json.loads(p.read_text()) for p in paths]
    if (mesh["status"] != "completed" or not mesh["all_six_terminal"]
            or ma["status"] != "completed" or not ma["all_pass"]
            or ma["study"] != reference(paths[0]) or qi["status"] != "completed"
            or qa["status"] != "completed" or not qa["all_pass"]
            or qa["source"] != reference(paths[2])):
        raise ValueError("closed bound independent mesh/QI audits required")
    if ([r["nonlocal_screen_pass"] for r in mesh["meshes"]] != [True]*5+[False]
            or [r["complete_scan"] for r in mesh["meshes"]] != [True]*5+[False]):
        raise ValueError("exactly the original finest incomplete row required")
    worker = json.loads(checked(mesh["meshes"][5]["worker"]).read_text())
    scan = json.loads(checked(worker["scan"]).read_text())
    if scan["status"] != "pair_cap" or scan["sat_calls"] != 2000000:
        raise ValueError("original two-million-pair capped source required")
    for path in paths:
        require_committed(root, path)
    return [reference(p) for p in paths], worker["scan"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable finest-mesh study paths required")
    root = Path(__file__).resolve().parents[1]
    previous, old_scan = predecessors(root)
    intrinsic, source = frozen_inputs(root)
    protocol = root/"docs/engineering/MESH_FINE_COMPLETION_PROTOCOL.md"
    for path in [protocol, *(root/p for p in CODE)]:
        require_committed(root, path)
    args.output.mkdir(parents=True)
    report = dict(repository=git_state(root), status="running", mesh=source["meshes"][5]["mesh"],
                  intrinsic_source=reference(intrinsic), old_scan=old_scan, predecessor=previous,
                  historical_source_code=source_code_bindings(root, source),
                  code=[reference(root/p) for p in CODE], protocol=reference(protocol),
                  hard_timeout_seconds=1200, full_engineering_admission=False,
                  disk_preflight=space_check(root, 3*GIB))
    summary, log = args.output/"summary.json", args.output/"worker.log"
    worker = args.output/"worker.json"
    command = [sys.executable, "scripts/mesh_fine_completion_worker.py", str(worker), str(args.raw)]
    report["command"] = command
    write_json_atomic(summary, report)
    try:
        with log.open("xb") as stream:
            try:
                result = subprocess.run(command, cwd=root, env=os.environ, stdout=stream,
                                        stderr=subprocess.STDOUT, timeout=1200, check=False)
                report.update(status="process_failed", returncode=result.returncode)
            except subprocess.TimeoutExpired:
                report.update(status="timeout", returncode=None)
        report["log"] = reference(log)
        if worker.exists():
            report["worker"] = reference(worker)
            data = json.loads(worker.read_text())
            if data["status"] == "completed" and report["returncode"] == (
                    0 if data["nonlocal_screen_pass"] else 2):
                report.update(status="completed", complete_scan=data["complete_scan"],
                              nonlocal_screen_pass=data["nonlocal_screen_pass"])
    finally:
        write_json_atomic(summary, report)
    return 0 if report.get("nonlocal_screen_pass", False) else 2


if __name__ == "__main__":
    raise SystemExit(main())
