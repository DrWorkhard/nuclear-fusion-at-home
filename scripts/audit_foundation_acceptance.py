"""Independent source-bound closure of the explicitly limited foundation milestones."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from current_diagnostic_inputs import checked, reference
from run_coil_holdouts import validate_phase
from run_jac_scaled_study import require_closed

from fusion_baselines.foundation_acceptance import (
    assess,
    audit_candidate,
    audit_test_xml,
)
from fusion_baselines.integration_audit import audit_integration_xml
from fusion_baselines.operational_preservation import approved_change
from fusion_baselines.provenance import git_state, write_json_atomic

BASE = "5971fee"
PROTOCOL = "docs/validation/FOUNDATION_ACCEPTANCE_PROTOCOL.md"
PHASES = ("regression", "ruff", "docs", "scientific", "warning", "cycle", "cycle-audit", "holdouts")
PRIOR = {
    "native": "evidence/fresh-native-integration-v2/summary.json",
    "archive": "evidence/fresh-native-integration-v2-archive.json",
    "physics": "evidence/fresh-native-integration-v2-physics-audit.json",
    "warning": "evidence/netcdf-import-warning-v1.json",
}


def preservation(root):
    """Check every tracked historical file, not just the latest experiment."""
    allowed = {"AGENTS.md", "README.md", "docs/README.md", "docs/STATUS.md", "docs/PROJECT_PLAN.md"}
    allowed.update(
        f"docs/{p}/README.md"
        for p in (
            "optimization",
            "geometry",
            "qi",
            "engineering",
            "validation",
            "squid_c",
            "logbook",
        )
    )
    allowed.update(f"docs/logbook/{p}.md" for p in ("FINDINGS", "DECISIONS", "VALIDATION_LOG"))
    delta = subprocess.check_output(
        ["git", "diff", "--no-renames", "--name-status", BASE, "--"], cwd=root, text=True
    )
    changes = [row.split("\t", 1) for row in delta.splitlines()]
    operational = [row[1] for row in changes if row[0] == "M"
                   and approved_change(root, BASE, row[1])]
    blocked = [
        row for row in changes if row[0] != "A"
        and not (row[0] == "M" and (row[1] in allowed or row[1] in operational))
    ]
    revision = subprocess.check_output(["git", "rev-parse", BASE], cwd=root, text=True).strip()
    tag = subprocess.check_output(
        ["git", "rev-parse", "foundation-pre-scope-2026-09-13"], cwd=root, text=True
    ).strip()
    files = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE], cwd=root, text=True
    ).splitlines()
    return dict(
        base_commit=revision,
        preservation_tag=tag,
        historical_tracked_files=len(files),
        operational_maintenance_version=1,
        approved_operational_changes=operational,
        allowed_modified=[row[1] for row in changes if row[0] == "M" and row not in blocked],
        blocked_changes=blocked,
        all_pass=not blocked and revision == tag,
    )


def external_state(root):
    result = {}
    for name in ("stellcoilbench", "simsopt", "vmecpp", "vmecpp-validation", "stellopt-v251"):
        path = root / "external" / name
        delta = subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=path)
        untracked = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"], cwd=path, text=True
        ).splitlines()
        result[name] = dict(
            repository=git_state(path),
            tracked_delta_sha256=hashlib.sha256(delta).hexdigest(),
            untracked=[reference(path / p) for p in untracked if (path / p).is_file()],
        )
    return result


def bind_tree(value):
    """Check every nested explicit content reference; metadata paths alone are not sources."""
    count = 0
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            checked(value)
            return 1
        for item in value.values():
            count += bind_tree(item)
    elif isinstance(value, list):
        count += sum(bind_tree(item) for item in value)
    return count


def read_ref(ref):
    return json.loads(checked(ref).read_text())


def same_source(record, expected):
    """Identity is checked path/content; optional size metadata must also be correct."""
    actual_path, expected_path = checked(record), checked(expected)
    return (
        actual_path.resolve() == expected_path.resolve()
        and record["sha256"] == expected["sha256"]
        and ("bytes" not in record or record["bytes"] == actual_path.stat().st_size)
    )


def native_checks(prior):
    native, archive, physics = (prior[k] for k in ("native", "archive", "physics"))
    for row in archive["files"]:
        checked(row["archive"])
    comparison = physics["fixed_boundary_63_variable_summary"]
    return dict(
        all_21=len(native["steps"]) == 21
        and all(r["status"] == "passed" for r in native["steps"])
        and native["status"] == "completed"
        and native["all_pass"] is True,
        archived=archive["all_pass"] is True
        and len(archive["files"]) == 11
        and all(r["archive"]["sha256"] == r["original"]["sha256"] for r in archive["files"]),
        strict_six=archive["strict_xml_audit"]["all_pass"] is True
        and archive["strict_xml_audit"]["test_count"] == 6,
        protected=physics["assessment"]["project_w7x_regression_gate_pass"] is True
        and physics["assessment"]["protected_realspace_geometry_and_field_pass"] is True
        and physics["convergence"]["both_reach_requested_level"] is True,
        retained_60_of_63=comparison["passed"] == 60
        and comparison["checked"] == 63
        and comparison["overall_pass"] is False
        and {r["variable"] for r in comparison["failed"]} == {"pres", "presf", "chipf"},
        scope=archive["global_physics_certified"] is False
        and native["full_global_physics_qualification"] is False,
    )


def warning_check(current, prior):
    bind_tree(current)
    # Exact fresh-process observations; unknown warnings cannot inherit the exception.
    return (
        current["sources"] == prior["sources"]
        and current["cases"] == prior["cases"]
        and [c["returncode"] for c in current["cases"]] == [0, 0, 1]
        and current["expected_behavior_reproduced"] is True
        and current["native_abi_certified"] is False
        and current["environment_changed"] is False
    )


def audit_holdouts(report, study_ref, audit_ref):
    require_closed(report)
    bind_tree(report)
    if report["study"] != study_ref or report["audit"] != audit_ref:
        raise ValueError("holdouts bound to another study/audit")
    study = read_ref(study_ref)
    reports = {}
    for phase in report["steps"]:
        reports[phase["name"]] = read_ref(phase["result"])
        validate_phase(phase["name"], reports[phase["name"]], phase["returncode"])
        bind_tree(reports[phase["name"]])
    h, k, c, n = (reports[key] for key in ("holdout", "curvature", "clearance", "native"))
    href = report["steps"][0]["result"]
    if (
        h["study"] != study_ref
        or c["holdout"] != href
        or n["holdout"] != href
        or k["input_records"] != [href, study_ref]
        or k["construction_protocol"] != study["protocol"]
        or n["thresholds"] != study["preparation"]["thresholds"]
    ):
        raise ValueError("independent phase inputs or unchanged thresholds not bound")
    if not (
        h["all_repeats"] is True
        and h["used_for_optimizer_feedback"] is False
        and n["used_for_optimizer_feedback"] is False
        and k["full_engineering_admission"] is False
        and n["full_engineering_admission"] is False
        and report["full_engineering_admission"] is False
    ):
        raise ValueError("holdout scope/feedback changed")
    if k["fields"][0]["field"] != study["preparation"]["source"]:
        raise ValueError("historical warmstart curvature control misidentified")
    rows = []
    for i, ref in enumerate(study["arms"]):
        arm = read_ref(ref)
        if h["candidates"][i]["arm"] != ref:
            raise ValueError("candidate-to-arm mapping changed")
        rows.append(
            audit_candidate(
                h["candidates"][i],
                k["fields"][i + 1],
                c["candidates"][i],
                n["candidates"][i],
                arm["best"]["field"],
                study["preparation"]["thresholds"]["a0"],
                study["preparation"]["thresholds"],
            )
        )
    aggregate = h["all_pass"] is all(
        c["bounded_geometry_flux_screen_pass"] for c in h["candidates"]
    ) and n["all_pass"] is all(c["pass"] for c in n["candidates"])
    return dict(
        candidates=rows,
        aggregate_flags=aggregate,
        all_pass=aggregate and len(rows) == 2 and all(r["all_pass"] for r in rows),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable foundation audit required")
    root = Path(__file__).resolve().parents[1]
    result = dict(
        status="running",
        all_pass=False,
        step1_pass=False,
        step2_pass=False,
        run=reference(args.run),
        code=reference(Path(__file__)),
        additional_field_calls=0,
    )
    try:
        from run_foundation_acceptance import CODE, phase_commands

        run = json.loads(args.run.read_text())
        expected_code = [reference(root / p) for p in CODE]
        if (
            run["status"] != "completed"
            or run["protocol"] != reference(root / PROTOCOL)
            or run["code"] != expected_code
            or [s["name"] for s in run["steps"]] != list(PHASES)
            or any(s["status"] != "completed" or s["returncode"] != 0 for s in run["steps"])
        ):
            raise ValueError("complete registered phases/code/protocol required")
        result["references_checked"] = bind_tree(run)
        expected_commands = phase_commands(root, args.run.parent, Path(run["raw_directory"]))
        if [s["command"] for s in run["steps"]] != [r[1] for r in expected_commands]:
            raise ValueError("registered phase commands changed")
        phases = {p["name"]: p for p in run["steps"]}
        tests = audit_test_xml(checked(phases["regression"]["result"]))
        log = checked(phases["regression"]["log"]).read_text()
        matches = re.findall(r"(\d+) warnings? in", log)
        result["regression"] = dict(**tests, warnings=int(matches[-1]) if matches else None)
        scientific = read_ref(phases["scientific"]["result"])
        bind_tree(scientific)
        integration = audit_integration_xml(checked(scientific["report"]))
        if run["prior_evidence"] != {k: reference(root / v) for k, v in PRIOR.items()}:
            raise ValueError("preserved native sources changed")
        prior = {k: read_ref(ref) for k, ref in run["prior_evidence"].items()}
        native = native_checks(prior)
        if not same_source(prior["archive"]["report"], run["prior_evidence"]["native"]):
            raise ValueError("archived native report mismatch")
        cycle_ref, audit_ref = (phases[key]["result"] for key in ("cycle", "cycle-audit"))
        cycle, cycle_audit = read_ref(cycle_ref), read_ref(audit_ref)
        bind_tree(cycle)
        bind_tree(cycle_audit)
        cycle_pass = (
            cycle_audit["all_pass"] is True
            and cycle_audit["study"] == cycle_ref
            and bool(cycle_audit["checks"])
            and all(cycle_audit["checks"].values())
            and len(cycle_audit["arms"]) == 2
            and all(
                r["all_pass"] is True and all(r["checks"].values()) for r in cycle_audit["arms"]
            )
            and cycle["qualification_pass"] is True
            and cycle["bundle_limit"] == 24
        )
        holds = audit_holdouts(read_ref(phases["holdouts"]["result"]), cycle_ref, audit_ref)
        retained = preservation(root)
        retained["external_unchanged"] = external_state(root) == run["external_before"]
        step1 = dict(
            regression=tests["all_pass"],
            scientific=scientific["all_pass"] is True
            and scientific["returncode"] == 0
            and integration["all_pass"]
            and scientific["test_report_audit"] == integration
            and scientific["required_data"]
            == {"FUSION_REQUIRE_QI_DATA": "1", "FUSION_REQUIRE_W7X_DATA": "1"},
            warning=warning_check(read_ref(phases["warning"]["result"]), prior["warning"]),
            preserved_native=all(native.values()),
            source_and_derivatives=cycle_pass,
            holdout_audit=holds["all_pass"],
            preservation=retained["all_pass"]
            and run["preservation_before"]["all_pass"]
            and retained["external_unchanged"],
            checks=True,
        )
        step2 = dict(cycle=cycle_pass, holdout_audit=holds["all_pass"], provenance=True)
        result.update(
            status="completed",
            step1_gates=step1,
            step2_gates=step2,
            native_checks=native,
            holdouts=holds,
            preservation=retained,
            **assess(step1, step2, run["unsupported_capabilities"]),
        )
    except Exception as exc:
        result.update(status="error", error=f"{type(exc).__name__}: {exc}")
    write_json_atomic(args.output, result)
    print(
        json.dumps(
            {k: result[k] for k in ("status", "step1_pass", "step2_pass", "all_pass")}
            | ({"error": result["error"]} if "error" in result else {})
        )
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
