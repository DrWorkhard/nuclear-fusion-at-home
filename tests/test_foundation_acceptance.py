"""Foundation process qualification must never turn an invalid design into a pass."""

import copy
import json
import sys
from pathlib import Path

import pytest
from test_current_gn_workflow import setup_gn

from fusion_baselines.foundation_acceptance import (
    UNSUPPORTED,
    assess,
    audit_candidate,
    audit_test_xml,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_current_start_gn as old_audit
import audit_foundation_acceptance as acceptance
import audit_foundation_cycle as audit
import run_current_start_gn as old_driver
import run_foundation_acceptance as runner
import run_foundation_cycle as driver
from current_diagnostic_inputs import reference

ROOT = Path(__file__).resolve().parents[1]


def test_two_short_synthetic_cycles_and_independent_mapping_audit(tmp_path, monkeypatch):
    setup_gn(tmp_path, monkeypatch, "budget")
    for name in (
        "native_setup",
        "DirectConstraintBackend",
        "versions",
        "qualified_source",
        "require_committed",
    ):
        monkeypatch.setattr(driver, name, getattr(old_driver, name))
    for name in ("qualified_source", "require_committed"):
        monkeypatch.setattr(audit, name, getattr(old_audit, name))
    study, raw = tmp_path / "study", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["run", str(study), str(raw)])
    assert driver.main() == 0
    path = study / "summary.json"
    record = json.loads(path.read_text())
    assert record["bundle_limit"] == 24
    for ref in record["arms"]:
        arm = acceptance.read_ref(ref)
        assert arm["counters"]["attempts"] == 24
        assert arm["status"] == "budget_exhausted"
    monkeypatch.setattr(sys, "argv", ["audit", str(study), str(tmp_path / "audit.json")])
    assert audit.main() == 0
    # Changing only the recorded physical owner permutation cannot be accepted.
    record["source_indices_in_target_order"][0:2] = record["source_indices_in_target_order"][1::-1]
    path.write_text(json.dumps(record))
    monkeypatch.setattr(sys, "argv", ["audit", str(study), str(tmp_path / "bad.json")])
    assert audit.main() == 2
    assert not json.loads((tmp_path / "bad.json").read_text())["checks"]["mapping"]


def historical_candidate():
    base = ROOT / "evidence/current-start-gn-v1-validation"
    records = [
        json.loads((base / f"{p}.json").read_text())
        for p in ("holdout", "curvature", "clearance", "native")
    ]
    h, k, c, n = records
    study = acceptance.read_ref(h["study"])
    return [
        h["candidates"][0],
        k["fields"][1],
        c["candidates"][0],
        n["candidates"][0],
        h["candidates"][0]["field"],
        study["preparation"]["thresholds"]["a0"],
        study["preparation"]["thresholds"],
    ]


def test_independent_arithmetic_accepts_correct_physical_rejection():
    result = audit_candidate(*historical_candidate())
    assert result["all_pass"]
    assert not result["bounded_candidate_pass"]
    assert result["raw_fine_flux"] > result["flux_limit"] == 1e-8


@pytest.mark.parametrize(
    "fault",
    ["flux", "native", "clearance", "curvature", "resolution", "field", "nan", "engineering"],
)
def test_changed_physics_flags_levels_or_mapping_rejected(fault):
    data = historical_candidate()
    h, k, c, n = data[:4]
    if fault == "flux":
        h["checks"]["flux_cut_in"] = True
        h["bounded_geometry_flux_screen_pass"] = True
    elif fault == "native":
        n["levels"][-1]["msc"][0] = 1e6
    elif fault == "clearance":
        c["continuous_centerline_lower_bound_reactor_m"] = 2.0
    elif fault == "curvature":
        k["levels"][-1]["curves"][0]["classification"] = "fail"
    elif fault == "resolution":
        h["flux"].pop()
    elif fault == "field":
        k["field"] = {**k["field"], "sha256": "0" * 64}
    elif fault == "nan":
        h["flux"][0]["mean_B_magnitude_T"] = float("nan")
    else:
        h["full_engineering_admission_pass"] = True
    assert not audit_candidate(*data)["all_pass"]


def test_source_tree_missing_and_corrupt_hash_rejected(tmp_path):
    path = tmp_path / "source.json"
    path.write_text("{}")
    record = dict(nested=[reference(path)])
    assert acceptance.bind_tree(record) == 1
    path.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="hash"):
        acceptance.bind_tree(record)
    path.unlink()
    with pytest.raises(FileNotFoundError):
        acceptance.bind_tree(record)


def test_complete_existing_holdouts_and_missing_phase_rejected():
    report = json.loads((ROOT / "evidence/current-start-gn-v1-validation/summary.json").read_text())
    result = acceptance.audit_holdouts(report, report["study"], report["audit"])
    assert result["all_pass"] and not any(c["bounded_candidate_pass"] for c in result["candidates"])
    report["steps"].pop(1)
    with pytest.raises(ValueError, match="four"):
        acceptance.audit_holdouts(report, report["study"], report["audit"])


def test_exact_gate_sets_and_excluded_capabilities():
    first = dict.fromkeys(
        (
            "regression",
            "scientific",
            "warning",
            "preserved_native",
            "source_and_derivatives",
            "holdout_audit",
            "preservation",
            "checks",
        ),
        True,
    )
    second = dict(cycle=True, holdout_audit=True, provenance=True)
    caps = dict.fromkeys(UNSUPPORTED, False)
    assert assess(first, second, caps)["all_pass"]
    assert not assess({}, second, caps)["step1_pass"]
    assert not assess(first, {}, caps)["step2_pass"]
    for key in first:
        assert not assess({**first, key: False}, second, caps)["step1_pass"]
    for key in caps:
        assert not assess(first, second, {**caps, key: True})["all_pass"]


def test_known_warning_does_not_cover_other_errors():
    old = json.loads((ROOT / acceptance.PRIOR["warning"]).read_text())
    assert acceptance.warning_check(old, old)
    bad = copy.deepcopy(old)
    bad["cases"][1]["stderr"] += "Additional unexpected failure"
    assert not acceptance.warning_check(bad, old)


def test_full_junit_cannot_skip_or_duplicate(tmp_path):
    path = tmp_path / "tests.xml"
    cases = "".join(f'<testcase classname="fixture" name="case{i}"/>' for i in range(700))
    path.write_text(f"<testsuites><testsuite>{cases}</testsuite></testsuites>")
    assert audit_test_xml(path)["all_pass"]
    for extra in (
        '<testcase classname="fixture" name="case0"/>',
        '<testcase name="skip"><skipped/></testcase>',
        '<testcase name="error"><error/></testcase>',
    ):
        path.write_text(f"<testsuites><testsuite>{cases}{extra}</testsuite></testsuites>")
        assert not audit_test_xml(path)["all_pass"]


def test_registered_old_native_exceptions_and_preservation():
    prior = {k: json.loads((ROOT / v).read_text()) for k, v in acceptance.PRIOR.items()}
    assert all(acceptance.native_checks(prior).values())
    prior["physics"]["fixed_boundary_63_variable_summary"]["passed"] = 63
    assert not all(acceptance.native_checks(prior).values())
    assert acceptance.preservation(ROOT)["all_pass"]


def test_orchestrator_records_failure_and_refuses_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "require_committed", lambda *_: None)
    output, raw = tmp_path / "output", tmp_path / "raw"

    def fail(command, **kwargs):
        kwargs["stdout"].write(b"Deliberate subprocess failure, no physical execution.\n")
        return dict(returncode=2)

    monkeypatch.setattr(runner, "guarded_run", fail)
    monkeypatch.setattr(sys, "argv", ["run", str(output), str(raw)])
    with pytest.raises(RuntimeError, match="regression failed"):
        runner.main()
    record = json.loads((output / "run.json").read_text())
    assert record["status"] == "error" and len(record["steps"]) == 1
    assert acceptance.checked(record["steps"][0]["log"]).is_file()
    with pytest.raises(FileExistsError):
        runner.main()


def test_overall_audit_records_incomplete_phase_rejection(tmp_path, monkeypatch):
    path, output = tmp_path / "run.json", tmp_path / "audit.json"
    path.write_text(
        json.dumps(
            dict(
                status="completed",
                protocol=reference(ROOT / acceptance.PROTOCOL),
                code=[reference(ROOT / p) for p in runner.CODE],
                steps=[],
            )
        )
    )
    monkeypatch.setattr(sys, "argv", ["audit", str(path), str(output)])
    assert acceptance.main() == 2
    result = json.loads(output.read_text())
    assert result["status"] == "error" and not result["all_pass"]
    assert not result["step1_pass"] and not result["step2_pass"]
