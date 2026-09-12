"""Verify completed fresh-native provenance and archive newly generated raw outputs."""

import argparse
import json
import shutil
from pathlib import Path

from fusion_baselines.integration_audit import audit_integration_xml
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path), bytes=path.stat().st_size)


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"source hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if args.raw.exists() or args.manifest.exists():
        raise FileExistsError("new archive and manifest required")
    report = json.loads(args.report.read_text())
    if report["status"] != "completed" or report["all_pass"] is not True:
        raise ValueError("completed successful fresh integration required")
    if report["copied_solver_outputs"] is not False or report["system_installation_permitted"]:
        raise ValueError("unexpected reconstruction policy")
    fresh = Path(report["fresh_checkout"])
    names = [r["name"] for r in report["steps"]]
    if len(names) != len(set(names)) or len(names) != 21:
        raise ValueError("exact unique phase count required")
    for row in report["steps"]:
        if row["status"] != "passed" or row["returncode"] != 0:
            raise ValueError("failed phase")
        checked(row["log"])
        if row["minimum_observed_free_bytes"] < report["disk_reserve_bytes"]:
            raise ValueError("reserve was not maintained")
    for ref in report["code"]:
        checked(ref)
    strict_path = checked(report["strict_integration"])
    strict = json.loads(strict_path.read_text())
    xml = checked(strict["report"])
    checked(strict["log"])
    for ref in strict["code"]:
        checked(ref)
    xml_audit = audit_integration_xml(xml)
    if not strict["all_pass"] or not xml_audit["all_pass"]:
        raise ValueError("strict six-test audit failed")
    native_path = fresh / "evidence/w7x-vmec2000-v852-reference.json"
    native = json.loads(native_path.read_text())
    if (
        native["execution"]["mode"] != "fresh"
        or not native["execution"]["normal_termination_marker"]
    ):
        raise ValueError("fresh native execution missing")
    if max(native["metrics"][k] for k in ("fsqr", "fsqz", "fsql")) > 1e-12:
        raise ValueError("native residual threshold failed")
    checked(native["binary"])
    checked(native["input"])
    paths = [checked(report["fresh_binary"]), checked(report["input"]), native_path]
    for dirname in ("artifacts/vmecpp/w7x-stellcoilbench", "artifacts/vmec2000/w7x-v852-reference"):
        paths.extend(p for p in sorted((fresh / dirname).iterdir()) if p.is_file())
    for ref in report["wouts"]:
        checked(ref)
    for name, ref in native["outputs"].items():
        path = fresh / "artifacts/vmec2000/w7x-v852-reference" / name
        if sha256_file(path) != ref["sha256"] or path.stat().st_size != ref["bytes"]:
            raise ValueError("native auxiliary output hash mismatch")
    space_check(args.raw.parent, 2 * GIB + sum(p.stat().st_size for p in paths))
    args.raw.mkdir(parents=True)
    records = []
    for path in paths:
        if not path.resolve().is_relative_to(fresh.resolve()):
            raise ValueError("unexpected path outside fresh checkout")
        target = args.raw / path.relative_to(fresh)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        source_ref, target_ref = reference(path), reference(target)
        if (
            source_ref["sha256"] != target_ref["sha256"]
            or source_ref["bytes"] != target_ref["bytes"]
        ):
            raise ValueError("archive copy mismatch")
        records.append(dict(original=source_ref, archive=target_ref))
    result = dict(
        schema_version=1,
        repository=git_state(Path(__file__).resolve().parents[1]),
        report=reference(args.report),
        code=reference(Path(__file__)),
        all_pass=True,
        strict_xml_audit=xml_audit,
        files=records,
        archive_after_completed_execution=True,
        original_reports_modified=False,
        original_checkout_retained=True,
        minimum_observed_free_bytes=min(r["minimum_observed_free_bytes"] for r in report["steps"]),
        native_execution=native["execution"],
        native_metrics=native["metrics"],
        fresh_project_status=git_state(fresh),
        global_physics_certified=False,
    )
    write_json_atomic(args.manifest, result)
    print(json.dumps({"archive_verified": True, "files": len(records)}))


if __name__ == "__main__":
    main()
