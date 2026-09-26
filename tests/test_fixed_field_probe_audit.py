"""Synthetic saved-array composition and paired-label controls; no native work."""

import copy
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from test_clear_coil_field_audit import raw_state, synthetic_snapshot
from test_protected_fine_native import raw_arrays

from fusion_baselines import fixed_field_probe_audit as audit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
REAL_COMPOSE = audit.numerical.composed_metrics


def seed_snapshot(nbase=6):
    snapshot = synthetic_snapshot(nbase, 5 if nbase == 6 else 7)
    seed = {
        k: copy.deepcopy(snapshot[k])
        for k in ("schema_version", "nfp", "nbase", "order", "names", "base_coefficients")
    }
    seed["physical"] = [
        {k: v for k, v in row.items() if k != "current"} for row in snapshot["physical"]
    ]
    seed["sources"] = dict(reference=dict(input="synthetic", wout="synthetic"))
    snapshot["sources"] = copy.deepcopy(seed["sources"]["reference"])
    snapshot["seed_geometry"] = copy.deepcopy(seed)
    snapshot["initialization_work"] = dict(seed_A_calls=1, seed_A_points=256)
    return seed, snapshot


def inputs(
    monkeypatch,
    level_index=0,
    *,
    nbase=6,
    x=None,
    control=False,
    normal=0.3,
    vector=0.4,
    objective=0.5,
    flux_factor=1.0,
):
    seed, snapshot = seed_snapshot(nbase)
    case = dict(
        label=f"reference-n{nbase}-N",
        method="N",
        nbase=nbase,
        order=seed["order"],
        seed_label=f"n{nbase}-shape-d100mm",
        target="reference",
    )
    level = audit.numerical.levels()[level_index]
    x = np.asarray(seed["base_coefficients"]).ravel() if x is None else np.asarray(x)
    snapshot["base_coefficients"] = x.reshape(nbase, 3, 2 * seed["order"] + 1).tolist()
    initialization = dict(
        seed_unit_flux=0.125 if level["ncoil"] == 256 else 0.124,
        names=seed["names"],
        seed_x=np.asarray(seed["base_coefficients"]).ravel(),
        ncoil=level["ncoil"],
        initialization_work=snapshot["initialization_work"],
    )
    metrics = dict(
        JN=objective,
        JV=vector**2 / 2,
        scale=snapshot["scale"],
        B2_scale=1.0,
        unit_flux=snapshot["unit_flux"] * flux_factor,
        target_flux=snapshot["target_flux"],
        flux=snapshot["target_flux"] * flux_factor,
        current=25000.0,
        normal_rms=normal,
        normal_max=0.4,
        vector_rms=vector,
        boundary_B_rms=1.0,
        lengths=[2.0] * nbase,
        kappa_max=[5.0] * nbase,
        coil_distance=0.1,
        surface_distance=0.1,
        geometry_penalty=0.0,
        J=objective,
        frozen_scale=level_index != 0,
    )
    spec = dict(kind="diagnostic", case=case, grid={k: v for k, v in level.items() if k != "index"})
    arrays = raw_arrays(spec, {}, snapshot)
    target = dict(
        ninner=level["ninner"],
        B2_scale=1.0,
        target_flux=snapshot["target_flux"],
        inner_points=arrays["inner_points"].copy(),
        inner_target=arrays["inner_target"].copy(),
    )

    def compose(snap, data, raw, active, method, grid):
        assert snap == snapshot and raw is arrays and active is target
        assert method == "N" and grid == level
        return {k: copy.deepcopy(v) for k, v in metrics.items() if k != "frozen_scale"}

    monkeypatch.setattr(audit.numerical, "composed_metrics", compose)
    monkeypatch.setattr(audit, "_initializer", lambda s, d, n, g: 0.125 if n == 256 else 0.124)
    monkeypatch.setattr(audit, "_direct", lambda s, r, n: dict.fromkeys(audit.DIRECT, 0.0))
    historical = dict(state=dict(x=x.tolist(), value=objective, metrics=copy.deepcopy(metrics)))
    return dict(
        seed=seed,
        x=x,
        case=case,
        level=level,
        snapshot=snapshot,
        initialization=initialization,
        metrics=metrics,
        arrays=arrays,
        input_data=dict(synthetic=True),
        target=target,
        control_bundle=historical if control else None,
        control_snapshot=copy.deepcopy(snapshot) if control else None,
    )


def state(monkeypatch, *, nbase=6, x=None, control=False, normal=0.3, vector=0.4, objective=0.5):
    return audit.audit_state(
        [
            audit.audit_model(
                **inputs(
                    monkeypatch,
                    i,
                    nbase=nbase,
                    x=x,
                    control=control and i == 0,
                    normal=normal,
                    vector=vector,
                    objective=objective,
                )
            )
            for i in range(6)
        ]
    )


def paired(monkeypatch, nbase=6):
    seed, _ = seed_snapshot(nbase)
    x = np.asarray(seed["base_coefficients"]).ravel().copy()
    x[0] += 0.002
    gradient, direction = np.zeros_like(x), np.zeros_like(x)
    gradient[0], direction[0] = 1.0, -1.0
    proposed = x.copy()
    proposed[0] -= 0.001
    control = state(monkeypatch, nbase=nbase, x=x, control=True)
    proposal = state(
        monkeypatch, nbase=nbase, x=proposed, normal=0.299, vector=0.399, objective=0.49
    )
    pred_index, trial_index, mi, pi = (93, 94, 2, 10) if nbase == 6 else (49, 50, 4, 11)
    rhs = 0.5 + 1e-4 * 0.001 * -1.0
    context = dict(
        case=control["case"],
        control_manifest_index=mi,
        proposal_manifest_index=pi,
        predecessor=dict(
            index=pred_index,
            x=x.tolist(),
            accepted=True,
            evaluation=dict(x=x.tolist(), gradient=gradient.tolist(), value=0.5),
        ),
        proposal=dict(
            index=trial_index,
            x=proposed.tolist(),
            parent_index=pred_index,
            accepted=False,
            evaluation=None,
            reason="geometry-rejected",
            alpha=0.001,
            backtrack=0,
            direction=direction.tolist(),
            directional_derivative=-1.0,
            armijo_rhs=rhs,
        ),
        proposal_field_observed=False,
        immediate_saved_predecessor_verified=True,
        original_proposal_bits_verified=True,
        predecessor_gradient=gradient.tolist(),
        direction=direction.tolist(),
        alpha=0.001,
        saved_directional_derivative=-1.0,
        gradient_dot_direction_relative_tolerance=5e-15,
        predecessor_objective=0.5,
        armijo_constant=1e-4,
        armijo_rhs=rhs,
    )
    return control, proposal, context


def replace_metric(row, key, value):
    row["metrics"][key] = value
    row["metric_checks"][key] = audit._comparison(value, value)
    if row["control_replay"] is not None:
        row["control_replay"][key] = audit._comparison(value, value)
    row["diagnostic_flux"] = audit._flux(row["metrics"])
    row["absolute_gates"] = audit._gates(row["metrics"])
    row["numerical_pass"] = row["diagnostic_flux"]["passed"]


@pytest.mark.parametrize("nbase", [6, 8])
def test_complete_model_state_and_pair_are_diagnostic_only(monkeypatch, nbase):
    control, proposal, context = paired(monkeypatch, nbase)
    result = audit.compare_pair(control, proposal, context)
    assert result["normal_rms"]["resolved_diagnostic_gain"] is True
    assert result["vector_rms"]["resolved_diagnostic_gain"] is True
    assert result["armijo"]["counterfactual_armijo_pass"] is True
    assert all(result[k] is False for k in audit.SCOPE)
    assert all(row["absolute_gates"]["normal_rms"] is False for row in control["models"])
    assert control["work"] == dict(
        initializer_scalar_checks=6,
        metric_reconstructions=6,
        direct_statistics=36,
        direct_vectors=2304,
        direct_scalar_components=6912,
        diagnostic_flux_checks=6,
    )
    assert len(control["refinements"]["checks"]) == 5
    assert control["models"][2]["initializer_check"]["actual"] == 0.124
    assert control["models"][2]["snapshot"]["seed_unit_flux"] == 0.125


@pytest.mark.parametrize(
    "mutation",
    [
        "seed_x",
        "init_names",
        "ncoil",
        "work",
        "x",
        "names",
        "matrix",
        "current",
        "seed_geometry",
        "target_flux",
        "b2",
        "target_points",
        "target_values",
        "metric_keys",
        "raw_keys",
        "frozen",
        "bool_metric",
        "nan_metric",
        "init_flux",
    ],
)
def test_model_poisoning_rejected(monkeypatch, mutation):
    h = inputs(monkeypatch)
    if mutation == "seed_x":
        h["initialization"]["seed_x"][0] += 0.01
    elif mutation == "init_names":
        h["initialization"]["names"] = ["wrong"]
    elif mutation == "ncoil":
        h["initialization"]["ncoil"] = 512
    elif mutation == "work":
        h["initialization"]["initialization_work"] = dict(seed_A_calls=True, seed_A_points=256)
    elif mutation == "x":
        h["x"] = h["x"].copy()
        h["x"][0] += 0.01
    elif mutation == "names":
        h["snapshot"]["names"] = ["wrong"]
    elif mutation == "matrix":
        h["snapshot"]["physical"][0]["matrix"][0][0] += 1e-13
    elif mutation == "current":
        h["snapshot"]["physical"][0]["current"] += 0.001
    elif mutation == "seed_geometry":
        h["snapshot"]["seed_geometry"]["nbase"] = 8
    elif mutation == "target_flux":
        h["target"]["target_flux"] *= 2
    elif mutation == "b2":
        h["target"]["B2_scale"] *= 2
    elif mutation == "target_points":
        h["target"]["inner_points"][0, 0] += 0.01
    elif mutation == "target_values":
        h["target"]["inner_target"][0, 0] += 0.01
    elif mutation == "metric_keys":
        h["metrics"].pop("normal_max")
    elif mutation == "raw_keys":
        h["arrays"].pop("boundary_A")
    elif mutation == "frozen":
        h["metrics"]["frozen_scale"] = 0
    elif mutation == "bool_metric":
        h["metrics"]["current"] = True
    elif mutation == "nan_metric":
        h["metrics"]["normal_rms"] = math.nan
    elif mutation == "init_flux":
        h["initialization"]["seed_unit_flux"] += 1e-8
    with pytest.raises((ValueError, KeyError)):
        audit.audit_model(**h)


@pytest.mark.parametrize("bad", [True, -1e-12, math.nan, math.inf, 5.00001e-10])
def test_direct_error_values_cannot_alias_or_exceed_limit(monkeypatch, bad):
    h = inputs(monkeypatch)
    monkeypatch.setattr(audit, "_direct", lambda *a: dict.fromkeys(audit.DIRECT, bad))
    with pytest.raises(ValueError):
        audit.audit_model(**h)


def test_missing_direct_statistic_is_not_complete(monkeypatch):
    h = inputs(monkeypatch)
    monkeypatch.setattr(audit, "_direct", lambda *a: {"boundary_B": 0.0})
    with pytest.raises(ValueError):
        audit.audit_model(**h)


@pytest.mark.parametrize("key", ["scale", "JN", "current", "normal_rms"])
def test_historical_control_replay_detects_mismatch(monkeypatch, key):
    h = inputs(monkeypatch, control=True)
    h["control_bundle"]["state"]["metrics"][key] *= 1.1
    with pytest.raises(ValueError):
        audit.audit_model(**h)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "extra",
        "order",
        "pass_bool",
        "scope",
        "work",
        "metric_check",
        "direct",
        "initializer",
        "flux",
        "snapshot",
    ],
)
def test_incomplete_or_forged_model_reports_do_not_qualify(monkeypatch, fault):
    report = state(monkeypatch)
    rows = report["models"]
    if fault == "missing":
        rows.pop()
    elif fault == "extra":
        rows.append(copy.deepcopy(rows[-1]))
    elif fault == "order":
        rows[1], rows[2] = rows[2], rows[1]
    elif fault == "pass_bool":
        rows[0]["numerical_pass"] = 1
    elif fault == "scope":
        rows[0]["physical_admission"] = True
    elif fault == "work":
        rows[0]["work"]["direct_statistics"] = 5
    elif fault == "metric_check":
        rows[0]["metric_checks"]["J"]["passed"] = 1
    elif fault == "direct":
        rows[0]["direct_errors"].pop("loop_A")
    elif fault == "initializer":
        rows[0]["initializer_check"]["independent"] = 0.0
    elif fault == "flux":
        rows[0]["diagnostic_flux"]["passed"] = 1
    elif fault == "snapshot":
        rows[2]["snapshot"]["scale"] *= 1.001
    with pytest.raises(ValueError):
        audit.audit_state(rows)


def test_flux_failure_retained_and_disqualifies_both_labels(monkeypatch):
    control, proposal, context = paired(monkeypatch)
    row = proposal["models"][4]
    replace_metric(row, "flux", row["metrics"]["target_flux"] * (1 + 2e-6))
    proposal = audit.audit_state(proposal["models"])
    assert proposal["diagnostic_flux_pass"] is False and proposal["numerical_pass"] is False
    result = audit.compare_pair(control, proposal, context)
    assert not result["normal_rms"]["resolved_diagnostic_gain"]
    assert not result["vector_rms"]["resolved_diagnostic_gain"]


def test_refinement_failure_remains_negative_even_with_coarse_gain(monkeypatch):
    control, proposal, context = paired(monkeypatch)
    replace_metric(proposal["models"][2], "normal_rms", 0.28)
    proposal = audit.audit_state(proposal["models"])
    assert not proposal["refinements"]["passed"]
    result = audit.compare_pair(control, proposal, context)
    assert not result["normal_rms"]["resolved_diagnostic_gain"]


def test_metric_specific_margins_and_tradeoff_labels(monkeypatch):
    control, proposal, context = paired(monkeypatch)
    replace_metric(proposal["models"][3], "normal_rms", 0.2993)
    replace_metric(proposal["models"][3], "normal_max", 0.5)
    proposal = audit.audit_state(proposal["models"])
    result = audit.compare_pair(control, proposal, context)
    assert result["normal_rms"]["margin"] == pytest.approx(0.0012001)
    assert result["normal_rms"]["resolved_diagnostic_gain"] is False
    assert result["vector_rms"]["resolved_diagnostic_gain"] is True
    assert result["tradeoffs"][3]["normal_max_delta"] < 0


@pytest.mark.parametrize("which", ["normal_rms", "vector_rms"])
def test_margin_equality_and_zero_delta_cannot_pass(which):
    indices, pairs, final = (
        ([0, 1, 2, 3], [(0, 1), (1, 2), (2, 3)], [2, 3])
        if which == "normal_rms"
        else ([0, 4, 5], [(0, 4), (4, 5)], [5])
    )
    control = dict(numerical_pass=True, models=[dict(metrics={which: 1e-7}) for _ in range(6)])
    proposal = dict(numerical_pass=True, models=[dict(metrics={which: 0.0}) for _ in range(6)])
    result = audit._gain(control, proposal, which, indices, pairs, final)
    assert result["deltas"][0] == result["margin"] and not result["resolved_diagnostic_gain"]
    for row in proposal["models"]:
        row["metrics"][which] = 1e-7
    assert not audit._gain(control, proposal, which, indices, pairs, final)[
        "resolved_diagnostic_gain"
    ]


@pytest.mark.parametrize(
    "fault",
    [
        "case",
        "parent",
        "gradient",
        "direction",
        "inactive",
        "alpha",
        "rhs",
        "constant",
        "pred_value",
        "observed",
        "accepted",
    ],
)
def test_original_armijo_context_poisoning_rejected(monkeypatch, fault):
    control, proposal, context = paired(monkeypatch)
    if fault == "case":
        context["case"] = dict(context["case"], target="selected")
    elif fault == "parent":
        context["proposal"]["parent_index"] -= 1
    elif fault == "gradient":
        context["predecessor_gradient"][0] *= 2
    elif fault == "direction":
        context["direction"][0] *= 2
    elif fault == "inactive":
        context["direction"][5] = 1e-30
        context["proposal"]["direction"][5] = 1e-30
    elif fault == "alpha":
        context["alpha"] *= 0.5
    elif fault == "rhs":
        context["armijo_rhs"] += 1e-15
    elif fault == "constant":
        context["armijo_constant"] *= 2
    elif fault == "pred_value":
        context["predecessor_objective"] += 1e-15
    elif fault == "observed":
        context["proposal_field_observed"] = True
    elif fault == "accepted":
        context["proposal"]["accepted"] = 0
    with pytest.raises(ValueError):
        audit.compare_pair(control, proposal, context)


@pytest.mark.parametrize("above", [False, True])
def test_counterfactual_armijo_is_exact_saved_rhs_without_tolerance(monkeypatch, above):
    control, proposal, context = paired(monkeypatch)
    value = math.nextafter(context["armijo_rhs"], math.inf) if above else context["armijo_rhs"]
    replace_metric(proposal["models"][0], "J", value)
    proposal = audit.audit_state(proposal["models"])
    result = audit.compare_pair(control, proposal, context)
    assert result["armijo"]["counterfactual_armijo_pass"] is (not above)
    assert result["armijo"]["historical_step_accepted"] is False


def test_counterfactual_uses_actual_native_scalar_when_reconstruction_straddles_rhs(monkeypatch):
    control, proposal, context = paired(monkeypatch)
    rhs = context["armijo_rhs"]
    row = proposal["models"][0]
    replace_metric(row, "J", rhs)
    row["metric_checks"]["J"] = audit._comparison(math.nextafter(rhs, math.inf), rhs)
    proposal = audit.audit_state(proposal["models"])
    result = audit.compare_pair(control, proposal, context)
    assert result["armijo"]["counterfactual_armijo_pass"] is False
    assert result["armijo"]["independent_armijo_pass"] is True


@pytest.mark.parametrize("fault", ["missing_control", "promoted_state", "false_qualified"])
def test_pair_cannot_promote_or_substitute_aggregate_reports(monkeypatch, fault):
    control, proposal, context = paired(monkeypatch)
    if fault == "missing_control":
        control = state(monkeypatch, x=control["models"][0]["x"])
    elif fault == "promoted_state":
        proposal["physical_admission"] = True
    else:
        proposal["numerical_pass"] = 1
    with pytest.raises(ValueError):
        audit.compare_pair(control, proposal, context)


def test_actual_composed_metrics_are_reused_and_raw_loop_flux_is_reconstructed(monkeypatch):
    h = inputs(monkeypatch)
    data, snap, target, arrays = raw_state()
    seed = h["seed"]
    seed["base_coefficients"] = copy.deepcopy(snap["base_coefficients"])
    snap.update(
        seed_geometry=copy.deepcopy(seed),
        sources=seed["sources"]["reference"],
        initialization_work=dict(seed_A_calls=1, seed_A_points=256),
    )
    own = REAL_COMPOSE(snap, data, arrays, target, "N", h["level"])
    metrics = {key: own[key] for key in audit.METRICS - {"frozen_scale"}}
    metrics["frozen_scale"] = False
    target["target_flux"] = snap["target_flux"]
    h.update(
        seed=seed,
        x=np.asarray(snap["base_coefficients"]).ravel(),
        snapshot=snap,
        input_data=data,
        target=target,
        arrays=arrays,
        metrics=metrics,
    )
    h["initialization"]["seed_x"] = np.asarray(seed["base_coefficients"]).ravel()
    monkeypatch.setattr(audit.numerical, "composed_metrics", REAL_COMPOSE)
    result = audit.audit_model(**h)
    assert result["diagnostic_flux"]["flux"] == pytest.approx(snap["target_flux"], rel=1e-14)
    h["arrays"]["loop_A"] *= 1.001
    with pytest.raises(ValueError):
        audit.audit_model(**h)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_construction",
        "fine_construction",
        "bool_construction",
        "extra_construction",
        "schema",
    ],
)
def test_snapshot_requires_exact_registered_coarse_construction(monkeypatch, fault):
    h = inputs(monkeypatch, 2)
    if fault == "missing_construction":
        h["snapshot"].pop("construction")
    elif fault == "fine_construction":
        h["snapshot"]["construction"]["ncoil"] = 512
    elif fault == "bool_construction":
        h["snapshot"]["construction"]["offset"] = False
    elif fault == "extra_construction":
        h["snapshot"]["construction"]["extra"] = 0
    else:
        h["snapshot"]["schema_version"] = True
    with pytest.raises((ValueError, KeyError)):
        audit.audit_model(**h)


def test_coarse_normalization_preserves_original_tighter_flux_tolerance(monkeypatch):
    h = inputs(monkeypatch, flux_factor=1 + 2e-12)
    assert audit._flux(h["metrics"])["passed"] is True
    with pytest.raises(ValueError):
        audit.audit_model(**h)


def test_guard_blocks_each_later_numerical_phase(monkeypatch):
    for stop in range(1, 9):
        h = inputs(monkeypatch)
        events = []
        calls = [0]

        def guard(calls=calls, stop=stop):
            calls[0] += 1
            if calls[0] == stop:
                raise TimeoutError("synthetic deadline")

        original = audit.numerical.composed_metrics
        monkeypatch.setattr(
            audit,
            "_initializer",
            lambda s, d, n, g, events=events: events.append("initializer") or 0.125,
        )
        monkeypatch.setattr(
            audit.numerical,
            "composed_metrics",
            lambda *args, events=events, original=original: (
                events.append("compose") or original(*args)
            ),
        )
        monkeypatch.setattr(
            audit,
            "_direct",
            lambda *args, events=events: (
                events.append("direct") or dict.fromkeys(audit.DIRECT, 0.0)
            ),
        )
        with pytest.raises(TimeoutError):
            audit.audit_model(**h, guard=guard)
        expected = (
            []
            if stop <= 2
            else ["initializer"]
            if stop <= 4
            else (["initializer", "compose"] if stop <= 6 else ["initializer", "compose", "direct"])
        )
        assert events == expected


def test_pair_cannot_compare_different_original_source_identities(monkeypatch):
    control, proposal, context = paired(monkeypatch)
    for row in proposal["models"]:
        row["snapshot"]["sources"]["input"] = "different-input"
        row["snapshot"]["seed_geometry"]["sources"]["reference"]["input"] = "different-input"
    proposal = audit.audit_state(proposal["models"])
    with pytest.raises(ValueError):
        audit.compare_pair(control, proposal, context)
