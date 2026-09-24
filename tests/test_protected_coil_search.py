"""Synthetic controller qualification; no real coil or native field calculation."""

import copy
import json
import math

import numpy as np
import pytest

from fusion_baselines import protected_coil_search as controller


def state(x, value=None, current=200000.0, gradient=None):
    g = np.zeros(len(x)) if gradient is None else np.array(gradient, copy=True)
    if gradient is None:
        g[0] = 1.0
    return dict(x=np.array(x, copy=True), value=float(x[0]) if value is None else value,
                gradient=g, metrics=dict(current=current))


def certificate(certified=True):
    return dict(certified=certified, calculation_complete=True,
                status="certified" if certified else "uncertified")


def linear_run(size=198, certify=None, evaluate=None, initial=None, record=None):
    seed = np.zeros(size)
    events = []
    result = controller.search(seed, state(seed) if initial is None else initial,
                               certify or (lambda origin, x: certificate()),
                               evaluate or state, record or events.append)
    return seed, result, events


@pytest.mark.parametrize("nbase,order", [(6, 5), (8, 7)])
def test_weights_and_fd_directions_against_scalar_formula(nbase, order):
    expected = []
    for _ in range(nbase * 3):
        for k in range(2 * order + 1):
            m = (k + 1) // 2
            expected.append((1 + m*m)**-2 if m <= 2 else 0.0)
    np.testing.assert_array_equal(controller.weights(nbase, order), expected)
    assert sum(v > 0 for v in expected) == nbase * 15
    for actual, function in zip(controller.directions(nbase, order), (math.sin, math.cos),
                                strict=True):
        raw = [function(k+1) * math.sqrt(p) for k, p in enumerate(expected)]
        norm = math.sqrt(sum(v*v for v in raw))
        np.testing.assert_allclose(actual, [v/norm for v in raw], rtol=5e-14, atol=1e-15)


@pytest.mark.parametrize("size", [198, 360])
def test_linear_descent_budget_exact_repeat_and_event_order(size):
    seed, result, events = linear_run(size)
    _, repeated, again = linear_run(size)
    assert result == repeated and events == again
    assert result["reason"] == "field-budget"
    assert result["counters"] == dict(geometry_attempted=20, geometry_completed=20,
                                      field_attempted=20, field_completed=20, accepted=20)
    assert result["selected_index"] == 19
    assert result["selected"]["value"] < -0.019
    assert np.array_equal(seed, np.zeros(size))
    assert [event["event"] for event in events] == (
        ["search_started"] + ["proposal_attempt", "certificate_result", "field_attempt",
                              "trial_result"] * 20 + ["search_complete"])
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("size,order", [(198, 5), (360, 7)])
def test_original_seed_high_bits_and_private_callback_copies(size, order):
    seed = np.linspace(-0.02, 0.03, size)
    active = controller.weights(size // (3*(2*order+1)), order) > 0
    seed[5] = -0.0
    original = seed.copy()
    seen = []

    def certify(origin, proposed):
        np.testing.assert_array_equal(origin, original)
        assert proposed[~active].tobytes() == original[~active].tobytes()
        seen.append(proposed.copy())
        origin[:] = 999
        proposed[:] = 888
        return certificate()

    def evaluate(proposed):
        result = state(proposed)
        proposed[:] = 777
        return result

    def record(event):
        event.clear()

    result = controller.search(seed, state(seed), certify, evaluate, record)
    assert len(seen) == 20
    assert seed.tobytes() == original.tobytes()
    assert np.asarray(result["selected"]["x"])[~active].tobytes() == original[~active].tobytes()


def test_geometry_rejections_spend_no_field_work():
    calls = []
    _, result, _ = linear_run(certify=lambda origin, x: certificate(False),
                              evaluate=lambda x: calls.append(x))
    assert result["reason"] == "certificate-limited"
    assert result["counters"]["geometry_attempted"] == 16
    assert result["counters"]["field_attempted"] == 0
    assert not calls and result["selected_index"] is None


@pytest.mark.parametrize("current,reason", [(500000.01, "current-rejected"),
                                           (-500000.01, "current-rejected"),
                                           (200000.0, "armijo-rejected")])
def test_rejected_field_points_never_selected(current, reason):
    _, result, _ = linear_run(evaluate=lambda x: state(x, value=1.0, current=current))
    assert result["reason"] == "line-search-failed"
    assert len(result["trials"]) == 16 and not result["accepted_indices"]
    assert {trial["reason"] for trial in result["trials"]} == {reason}
    assert result["selected_index"] is None


@pytest.mark.parametrize("current", [500000.0, -500000.0])
def test_current_boundary_is_inclusive(current):
    _, result, _ = linear_run(evaluate=lambda x: state(x, current=current))
    assert result["counters"]["accepted"] == 20


def test_geometry_budget_independent_of_field_budget():
    calls = 0

    def certify(origin, proposed):
        nonlocal calls
        calls += 1
        return certificate(calls % 15 == 0)

    _, result, _ = linear_run(certify=certify)
    assert result["reason"] == "geometry-budget"
    assert result["counters"]["geometry_attempted"] == 116
    assert result["counters"]["field_attempted"] == result["counters"]["accepted"] == 7


def test_inactive_gradient_is_null_direction():
    initial = state(np.zeros(198), gradient=np.eye(198)[5])
    _, result, events = linear_run(initial=initial)
    assert result["reason"] == "null-direction"
    assert result["trials"] == [] and len(events) == 2


def test_equal_objectives_keep_first_seed_selection():
    initial = state(np.zeros(198), value=1e20)
    _, result, _ = linear_run(initial=initial, evaluate=lambda x: state(x, value=1e20))
    assert result["accepted_indices"] == list(range(20))
    assert result["selected_index"] is None


@pytest.mark.parametrize("where", ["certificate", "field"])
def test_malformed_returns_are_attempted_but_not_completed(where):
    events = []
    options = dict(record=events.append)
    if where == "certificate":
        options["certify"] = lambda origin, x: {"certified": "yes"}
    else:
        options["evaluate"] = lambda x: state(x, value=float("nan"))
    with pytest.raises(ValueError):
        linear_run(**options)
    counts = events[-1]["counters"]
    key = "geometry" if where == "certificate" else "field"
    assert counts[key+"_attempted"] == 1
    assert counts[key+"_completed"] == 0


@pytest.mark.parametrize("kind,stage", [
    ("proposal_attempt", "certificate-reservation"),
    ("certificate_result", "certificate-publication"),
    ("field_attempt", "field-reservation"),
    ("trial_result", "trial-publication"),
    ("search_complete", "completion-publication"),
])
def test_recording_failure_stops_and_identifies_stage(kind, stage):
    events, successful_bytes = [], []

    def record(event):
        if event["event"] == kind:
            raise OSError("synthetic disk failure")
        events.append(event)
        successful_bytes.append(json.dumps(event, sort_keys=True))

    with pytest.raises(OSError, match="synthetic disk failure"):
        linear_run(record=record)
    assert events[-1]["event"] == "search_error"
    assert events[-1]["stage"] == stage
    assert [json.dumps(event, sort_keys=True) for event in events] == successful_bytes
    counts = events[-1]["counters"]
    if kind in ("proposal_attempt", "certificate_result", "field_attempt"):
        assert counts["field_attempted"] == 0


@pytest.mark.parametrize("where", ["certificate", "field"])
def test_callback_exception_not_retried_and_original_error_retained(where):
    events = []

    def fail(*args):
        raise RuntimeError("original callback failure")

    options = dict(record=events.append)
    options["certify" if where == "certificate" else "evaluate"] = fail
    with pytest.raises(RuntimeError, match="original callback failure"):
        linear_run(**options)
    assert events[-1]["stage"] == where
    assert len([e for e in events if e["event"] == "proposal_attempt"]) == 1


def test_record_and_error_record_failure_preserve_original_exception():
    def record(event):
        raise OSError(event["event"])

    with pytest.raises(OSError, match="search_started") as failure:
        linear_run(record=record)
    assert "search_error" in failure.value.__notes__[0]


@pytest.mark.parametrize("fault", ["bool", "nan", "shape", "extra", "current", "gradient"])
def test_invalid_initial_states_rejected(fault):
    initial = state(np.zeros(198))
    if fault == "bool":
        initial["value"] = True
    elif fault == "nan":
        initial["value"] = float("nan")
    elif fault == "shape":
        initial["x"] = np.zeros(197)
    elif fault == "extra":
        initial["physical_admission"] = True
    elif fault == "current":
        initial["metrics"]["current"] = 500001.0
    else:
        initial["gradient"] = np.ones(198, dtype=bool)
    with pytest.raises(ValueError):
        linear_run(initial=initial)


def test_evaluator_cannot_return_changed_coordinate_bits():
    def changed(x):
        value = state(x)
        value["x"][7] = -0.0
        return value

    with pytest.raises(ValueError, match="bits"):
        linear_run(evaluate=changed)


def test_retained_initial_not_aliased_to_result_or_events():
    initial = state(np.zeros(198))
    before = copy.deepcopy(initial)
    _, result, events = linear_run(initial=initial)
    result["initial"]["x"][0] = 77.0
    assert events[0]["initial"]["x"][0] == 0.0
    np.testing.assert_array_equal(initial["x"], before["x"])


@pytest.mark.parametrize("size,order", [(198, 5), (360, 7)])
def test_general_gradient_uses_p_once_and_max_per_coil_d0(size, order):
    gradient = np.sin(np.arange(size) + 0.3) * np.linspace(0.1, 3.0, size)
    width = 2 * order + 1
    raw = [-float(g) / (1 + ((k % width + 1)//2)**2)**2
           if (k % width + 1)//2 <= 2 else 0.0 for k, g in enumerate(gradient)]
    axes = [abs(raw[i]) + sum(math.hypot(raw[i+k], raw[i+k+1])
                             for k in range(1, width, 2))
            for i in range(0, size, width)]
    bound = max(math.hypot(*axes[i:i+3]) for i in range(0, len(axes), 3))
    expected = [v / bound for v in raw]
    seed = np.zeros(size)
    def evaluate(x):
        return state(x, value=float(x @ gradient), gradient=gradient)
    _, result, _ = linear_run(size, initial=evaluate(seed), evaluate=evaluate)
    for trial in result["trials"]:
        np.testing.assert_allclose(trial["direction"], expected, rtol=5e-14, atol=1e-15)
        assert trial["directional_derivative"] == pytest.approx(sum(
            g*d for g, d in zip(gradient, expected, strict=True)), rel=5e-14)
    assert result["counters"]["accepted"] == 20


@pytest.mark.parametrize("bad", [None, [], {"certified": True},
    {"certified": True, "calculation_complete": False, "status": "certified"},
    {"certified": False, "calculation_complete": True, "status": "certified"},
    {"certified": False, "calculation_complete": True, "status": "uncertified", "n": math.inf},
])
def test_invalid_certificates_fail_before_field_dispatch(bad):
    calls, events = [], []
    with pytest.raises(ValueError):
        linear_run(certify=lambda origin, x: bad, evaluate=lambda x: calls.append(x),
                   record=events.append)
    assert not calls
    assert events[-1]["counters"]["geometry_completed"] == 0


@pytest.mark.parametrize("nbase,order", [(6, 7), (8, 5), (6.0, 5), (True, 5)])
def test_nonregistered_class_rejected(nbase, order):
    with pytest.raises(ValueError, match="registered"):
        controller.weights(nbase, order)


def test_negative_incomplete_certificate_conservatively_rejects():
    _, result, _ = linear_run(certify=lambda origin, x: dict(
        certified=False, calculation_complete=False, status="uncertified"))
    assert result["reason"] == "certificate-limited"
    assert result["counters"]["field_attempted"] == 0


def test_current_gate_has_no_floating_tolerance():
    _, result, _ = linear_run(evaluate=lambda x: state(
        x, current=math.nextafter(500000., math.inf)))
    assert not result["accepted_indices"]
    assert all(t["reason"] == "current-rejected" for t in result["trials"])
