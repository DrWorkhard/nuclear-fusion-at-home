"""Independent finest-mesh source, exact historical prefix and full spatial audit."""

import argparse
import json
from pathlib import Path

from mesh_nonlocal_inputs import checked, frozen_inputs, load_mesh, source_code_bindings
from run_mesh_fine_completion import predecessors

from fusion_baselines.mesh_nonlocal_audit import audit_scan
from fusion_baselines.mesh_nonlocal_scan import reference
from fusion_baselines.mesh_prefix_audit import audit_prefix
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable finest-mesh audit required")
    root = Path(__file__).resolve().parents[1]
    source = json.loads(args.source.read_text())
    previous, old_scan = predecessors(root)
    original_path, original = frozen_inputs(root)
    if (source["status"] != "completed" or source["mesh"] != original["meshes"][5]["mesh"]
            or source["old_scan"] != old_scan or source["predecessor"] != previous
            or source["intrinsic_source"] != reference(original_path)
            or source["historical_source_code"] != source_code_bindings(root, original)
            or source["hard_timeout_seconds"] != 1200):
        raise ValueError("unchanged terminal finest mesh and full source lineage required")
    for ref in [source["protocol"], *source["code"], source["log"]]:
        checked(ref)
    worker = json.loads(checked(source["worker"]).read_text())
    checked(worker["code"])
    new, old = [json.loads(checked(ref).read_text()) for ref in (worker["scan"], old_scan)]
    if (worker["mesh"] != source["mesh"] or worker["intrinsic_source"] != source["intrinsic_source"]
            or new["caps"] != dict(seconds=1200, sat_pairs=4000000)):
        raise ValueError("worker physical source or preregistered cap changed")
    space_check(root, 2*GIB)
    report = dict(repository=git_state(root), source=reference(args.source), status="running",
                  all_pass=False, finest_nonlocal_screen_pass=False,
                  full_engineering_admission=False,
                  code=[reference(root/p) for p in ("scripts/audit_mesh_fine_completion.py",
                      "scripts/run_mesh_fine_completion.py", "scripts/mesh_nonlocal_inputs.py",
                      "src/fusion_baselines/mesh_prefix_audit.py",
                      "src/fusion_baselines/mesh_nonlocal_audit.py",
                      "src/fusion_baselines/tetra_partition_audit.py",
                      "src/fusion_baselines/tetra_witness_audit.py")])
    try:
        report["prefix"] = audit_prefix(old, new)
        write_json_atomic(args.output, report)
        points, cells, tags = load_mesh(source["mesh"])
        report["spatial"] = audit_scan(points, cells, tags, new)
        spatial = report["spatial"]
        report["classification_checks"] = dict(
            complete=source["complete_scan"] == worker["complete_scan"] == spatial["complete"],
            physical=source["nonlocal_screen_pass"] == worker["nonlocal_screen_pass"] ==
            spatial["nonlocal_screen_pass"],
            exitcode=source["returncode"] == (0 if spatial["nonlocal_screen_pass"] else 2))
        passed = (report["prefix"]["all_pass"] and spatial["all_pass"]
                  and all(report["classification_checks"].values()))
        report.update(status="completed", all_pass=passed, finest_nonlocal_screen_pass=bool(
            passed and spatial["complete"] and spatial["nonlocal_screen_pass"]))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
