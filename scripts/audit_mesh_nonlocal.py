"""Independent full six-mesh file/source/partition/witness audit, no new collision search."""

import argparse
import json
from pathlib import Path

from mesh_nonlocal_inputs import LEVELS, checked, frozen_inputs, load_mesh

from fusion_baselines.mesh_nonlocal_audit import audit_scan
from fusion_baselines.mesh_nonlocal_scan import reference
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable full mesh audit required")
    root = Path(__file__).resolve().parents[1]
    source = json.loads(args.study.read_text())
    original_path, original = frozen_inputs(root)
    if (source["status"] != "completed" or not source["all_six_terminal"]
            or [r["target_h_m"] for r in source["meshes"]] != LEVELS
            or source["source"] != reference(original_path)
            or [r["index"] for r in source["meshes"]] != list(range(6))):
        raise ValueError("complete terminal six-mesh source ledger required")
    for ref in [source["protocol"], *source["code"], *source["predecessor"]]:
        checked(ref)
    report = dict(repository=git_state(root), study=reference(args.study), status="running",
                  meshes=[], all_pass=False, all_nonlocal_screens_pass=False,
                  code=[reference(root / p) for p in (
                      "scripts/audit_mesh_nonlocal.py", "scripts/mesh_nonlocal_inputs.py",
                      "src/fusion_baselines/mesh_nonlocal_audit.py",
                      "src/fusion_baselines/tetra_partition_audit.py",
                      "src/fusion_baselines/tetra_witness_audit.py")],
                  new_separating_axis_searches=0, new_interior_lp_calls=0,
                  complete_engineering_admission=False)
    try:
        for row, old in zip(source["meshes"], original["meshes"], strict=True):
            space_check(root, 2*GIB)
            if row["mesh"] != old["mesh"] or row["hard_timeout_seconds"] != 1200:
                raise ValueError("original mesh or hard process cap changed")
            checked(row["log"])
            result = dict(index=row["index"], mesh=row["mesh"], target_h_m=row["target_h_m"],
                          status="unavailable", all_pass=False, nonlocal_screen_pass=False)
            report["meshes"].append(result)
            if row["status"] != "completed":
                result["preserved_terminal_failure"] = row["status"]
                if "worker" in row:
                    checked(row["worker"])
                write_json_atomic(args.output, report)
                continue
            worker = json.loads(checked(row["worker"]).read_text())
            if (worker["mesh"] != old["mesh"] or worker["index"] != row["index"]
                    or worker["target_h_m"] != row["target_h_m"]
                    or worker["intrinsic_source"] != source["source"]):
                raise ValueError("worker redirected from original source")
            checked(worker["code"])
            scan = json.loads(checked(worker["scan"]).read_text())
            if scan["caps"] != dict(seconds=1200, sat_pairs=2000000):
                raise ValueError("registered fixed scan caps changed")
            points, cells, tags = load_mesh(old["mesh"])
            result.update(audit_scan(points, cells, tags, scan), status="completed",
                          scan=worker["scan"])
            if (result["complete"] != worker["complete_scan"]
                    or result["nonlocal_screen_pass"] != worker["nonlocal_screen_pass"]
                    or row["complete_scan"] != worker["complete_scan"]
                    or row["nonlocal_screen_pass"] != worker["nonlocal_screen_pass"]
                    or row["returncode"] != (0 if worker["nonlocal_screen_pass"] else 2)):
                raise ValueError("worker/driver/auditor classification mismatch")
            print(row["index"], result["complete"], result["nonlocal_screen_pass"], flush=True)
            write_json_atomic(args.output, report)
        aggregate = all(r["nonlocal_screen_pass"] for r in report["meshes"])
        if aggregate != source["all_nonlocal_screens_pass"]:
            raise ValueError("full matrix physical classification mismatch")
        report.update(status="completed", all_pass=all(r["all_pass"] for r in report["meshes"]),
                      all_nonlocal_screens_pass=aggregate)
    except Exception as error:
        report.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
