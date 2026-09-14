"""Actual bounded design controls, independent action arithmetic and fail-closed admission."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines.plasma_action_audit import independent_actions
from fusion_baselines.plasma_design import (
    MODES,
    action_statistics,
    bounce_field,
    design_input,
    improvement_checks,
    period_actions,
)
from fusion_baselines.qi_resolution import effective_input

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_plasma_design as audit
import plasma_measurement as measurement
import run_plasma_search as runner
from current_diagnostic_inputs import reference
from plasma_inputs import sources

ROOT = Path(__file__).resolve().parents[1]


def original():
    return dict(
        nfp=2,
        pres_scale=0.0,
        mpol=5,
        ntor=10,
        phiedge=0.1,
        curtor=0.0,
        rbc=[dict(m=0, n=0, value=1.0), dict(m=1, n=1, value=0.01), dict(m=2, n=0, value=0.02)],
        zbs=[dict(m=1, n=1, value=-0.03), dict(m=2, n=0, value=0.04)],
    )


def trace(nphi=801, nalpha=16, offset=0.0):
    phi = np.linspace(0, 2 * np.pi, nphi)
    alpha = np.linspace(0, 2 * np.pi, nalpha, endpoint=False) + offset
    scale = 1 + 0.03 * np.cos(alpha)
    bstar = bounce_field(0.5)
    return dict(
        phi=phi,
        alpha=alpha,
        B=np.broadcast_to(bstar + 0.2 * np.cos(2 * phi[:, None]), (nphi, nalpha)).copy(),
        length=phi[:, None] * scale,
        coordinate_residual_max=np.array(0.0),
    )


@pytest.mark.parametrize("ns", [201, 401])
def test_named_design_changes_only_registered_modes(ns):
    base = original()
    before = copy.deepcopy(base)
    x = [1e-4, -2e-4, 3e-4, -4e-4]
    actual = design_input(base, x, ns)
    assert base == before
    audit.input_identity(base, actual, x, ns)
    assert actual["nfp"] == 2 and actual["phiedge"] == 0.1
    for k, (kind, m, n) in enumerate(MODES):
        source = next(r["value"] for r in base[kind] if (r["m"], r["n"]) == (m, n))
        assert next(r["value"] for r in actual[kind] if (r["m"], r["n"]) == (m, n)) == source + x[k]
    assert design_input(base, [0.0] * 4, ns) == effective_input(base, ns, 2)


@pytest.mark.parametrize("x", [[0.0] * 3, [0.0, 0.0, 0.0, float("nan")], [0.0011, 0.0, 0.0, 0.0]])
def test_invalid_changes_rejected(x):
    with pytest.raises(ValueError):
        design_input(original(), x, 201)


@pytest.mark.parametrize("mutation", ["flux", "unlisted_mode", "numeric", "swap"])
def test_independent_auditor_rejects_other_changes(mutation):
    base, x = original(), [0.0001, 0.0002, 0.0, 0.0]
    actual = design_input(base, x, 201)
    if mutation == "flux":
        actual["phiedge"] *= 1.01
    elif mutation == "unlisted_mode":
        actual["rbc"][0]["value"] *= 1.01
    elif mutation == "numeric":
        actual["ntheta"] //= 2
    else:
        x[0], x[1] = x[1], x[0]
    with pytest.raises(ValueError):
        audit.input_identity(base, actual, x, 201)


def test_duplicate_mode_rejected():
    base = original()
    base["rbc"].append(copy.deepcopy(base["rbc"][1]))
    with pytest.raises(ValueError):
        design_input(base, [0.0] * 4, 201)


def test_two_period_objective_has_known_variance_and_independent_integral():
    raw = trace()
    result = period_actions(raw, 0.5)
    other = independent_actions(raw, bounce_field(0.5))
    assert result["score"] == pytest.approx(0.03**2 / 2, abs=1e-14)
    assert np.max(abs(other["actions"] / result["actions"] - 1)) < 1e-6
    np.testing.assert_allclose(result["bounds"], other["bounds"], atol=1e-14)


@pytest.mark.parametrize("bad", ["censor", "missing", "extra", "nan", "period", "length"])
def test_incomplete_or_nonfinite_domain_cannot_produce_cost(bad):
    raw = trace()
    if bad == "censor":
        raw["B"][0] = 1.0
    elif bad == "missing":
        raw["B"][:] = 2.0
    elif bad == "extra":
        raw["B"][:] = bounce_field(0.5) + 0.2 * np.cos(4 * raw["phi"][:, None])
    elif bad == "nan":
        raw["B"][100, 0] = np.nan
    elif bad == "period":
        raw["phi"] = raw["phi"] * 0.8
    else:
        raw["length"][3] = raw["length"][2]
    with pytest.raises(ValueError):
        period_actions(raw, 0.5)
    with pytest.raises(ValueError):
        independent_actions(raw, bounce_field(0.5))


@pytest.mark.parametrize("improves", [True, False])
def test_poll_budget_cache_and_separate_selection_replay(improves):
    def evaluate(x, index):
        score = float(np.sum((x - np.array([0.0004, 0.0, 0.0, 0.0])) ** 2)) if improves else 1.0
        return dict(x=x.tolist(), eligible=True, measurement=dict(score=score))

    result = runner.search(evaluate)
    study = dict(
        cells=result.pop("records"),
        search=result,
        new_equilibrium_attempts=result["unique_solves"] + 3,
    )
    assert audit.search_identity(study) == result["selected"]
    assert result["requests"] == 17
    assert result["unique_solves"] == (16 if improves else 17)
    assert result["rounds"][1]["step"] == (0.0002 if improves else 0.0001)
    broken = copy.deepcopy(study)
    broken["search"]["events"][1]["cache_hit"] = True
    with pytest.raises(ValueError):
        audit.search_identity(broken)
    broken = copy.deepcopy(study)
    broken["search"]["selected"] = 100
    with pytest.raises(ValueError):
        audit.search_identity(broken)


def test_invalid_baseline_stops_before_search():
    calls = []

    def evaluate(x, index):
        calls.append(index)
        return dict(x=x.tolist(), eligible=False)

    with pytest.raises(ValueError):
        runner.search(evaluate)
    assert calls == [0]


def test_store_and_independently_audit_synthetic_measurement(tmp_path, monkeypatch):
    monkeypatch.setattr(measurement, "trace_geometry", lambda *a, **k: trace())
    monkeypatch.setattr(audit, "trace_source_identity", lambda *a: None)
    wout = tmp_path / "synthetic-input.txt"
    wout.write_text("not a real equilibrium; synthetic trace test only")
    folder = tmp_path / "measurement"
    measurement.measure(wout, folder, surfaces=(0.25,), pitches=(0.5,))
    path = folder / "measurement.json"
    result = audit.measurement(reference(path), reference(wout), (0.25,), (0.5,), (801, 16, 0))
    assert result["score"] == pytest.approx(0.00045)
    report = json.loads(path.read_text())
    report["cells"] = []
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="missing"):
        audit.measurement(reference(path), reference(wout), (0.25,), (0.5,), (801, 16, 0))


def test_failed_cell_does_not_skip_remaining_requested_cells(tmp_path, monkeypatch):
    monkeypatch.setattr(measurement, "trace_geometry", lambda *a, **k: trace())
    calls = []

    def action(raw, q):
        calls.append(q)
        if q == 0.1:
            raise ValueError("registered synthetic failure")
        return period_actions(raw, q)

    monkeypatch.setattr(measurement, "period_actions", action)
    source = tmp_path / "input"
    source.write_text("synthetic")
    with pytest.raises(ValueError):
        measurement.measure(source, tmp_path / "raw", surfaces=(0.25, 0.5), pitches=(0.1, 0.5))
    report = json.loads((tmp_path / "raw/measurement.json").read_text())
    assert (
        calls == [0.1, 0.5, 0.1, 0.5] and len(report["errors"]) == 2 and report["status"] == "error"
    )


def test_score_gain_alone_and_fake_flags_do_not_admit():
    assert not all(improvement_checks(1.0, 0.99, 0.003, 1.0, 0.99).values())
    assert not all(improvement_checks(1.0, 0.999, 0.0, 1.0, 0.9).values())
    assert not all(improvement_checks(1.0, np.nan, 0.0, 1.0, 0.9).values())
    gates = dict.fromkeys(
        (
            "new_design",
            "repeat",
            "geometry",
            "physics",
            "crosscheck",
            "refinement",
            "cell_guards",
            "training_gain",
            "holdout_gain",
            "resolved_gain",
        ),
        True,
    )
    assert audit.conclusion(gates)
    gates["physics"] = False
    assert not audit.conclusion(gates)
    gates["physics"] = "False"
    with pytest.raises(ValueError):
        audit.conclusion(gates)
    gates.pop("physics")
    with pytest.raises(ValueError):
        audit.conclusion(gates)
    with pytest.raises(ValueError):
        action_statistics([[1.0, 1.0], [1.0, np.nan], [1.0, 1.0], [1.0, 1.0]])


def test_refinement_matches_nested_alpha_but_not_shifted_lines():
    coarse = dict(score=0.001, actions=np.ones((1, 4, 2)))
    fine = dict(score=0.001001, actions=np.ones((1, 8, 2)))
    fine["actions"][:, 1::2] = 2
    assert audit.refinement(coarse, fine, stride=2)["passed"]
    assert audit.refinement(coarse, fine, matched=False)["passed"]
    fine["actions"][:, ::2] = 1.01
    assert not audit.refinement(coarse, fine, stride=2)["passed"]


def test_retained_source_binding_readonly():
    source, binding = sources(ROOT, committed=False)
    assert source["nfp"] == 2 and binding["solver"]["version"] == "0.7.3"
    audit.bind_tree(binding)


def test_scalar_trace_source_and_arclength_check_on_preserved_wout():
    report = json.loads((ROOT / "evidence/qi-fresh-resolution-v1.json").read_text())
    row = next(
        r for r in report["cells"] if (r["case"], r["ns"], r["angular"]) == ("nfp2-vacuum", 201, 2)
    )
    from fusion_baselines.vmec_trace import trace_geometry

    raw = trace_geometry(Path(row["wout"]["path"]), 0.25, 65, 4, 2)
    audit.trace_source_identity(raw, row["wout"], 0.25)
    raw["B"][32, 0] *= 1.01
    with pytest.raises(ValueError, match="scalar field/geometry"):
        audit.trace_source_identity(raw, row["wout"], 0.25)
