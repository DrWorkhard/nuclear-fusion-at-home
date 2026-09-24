"""Adversarial tests of recorded policy, explicitly not field or geometry truth."""

import copy
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from test_protected_coil_search import certificate, linear_run, state

from fusion_baselines import protected_coil_search as controller
from fusion_baselines import protected_coil_search_audit as verifier


def check(seed, report, events):
    return verifier.audit(list(seed), report["initial"], report, events)


def trace(case, size=198):
    options, calls = {}, 0

    def numbered_certificate(origin, x):
        nonlocal calls
        calls += 1
        if case == "geometry-budget":
            take = calls % 15 == 0
        elif case == "both-budgets":
            take = calls % 6 == 0 or calls == 116
        else:
            take = calls <= 100 and calls % 10 == 0
        return certificate(take)

    def numbered_field(x):
        nonlocal calls
        calls += 1
        return state(x, value=float(x[0]) if calls <= 4 else 1.0)

    if case in ("geometry-budget", "both-budgets", "geometry-last-rejection"):
        options["certify"] = numbered_certificate
    elif case == "field-last-rejection":
        options["evaluate"] = numbered_field
    elif case == "certificate-limited":
        options["certify"] = lambda origin, x: certificate(False)
    elif case == "current-rejected":
        options["evaluate"] = lambda x: state(x, current=math.nextafter(500000., math.inf))
    elif case == "armijo-rejected":
        options["evaluate"] = lambda x: state(x, value=1.0)
    elif case == "null-direction":
        options["initial"] = state(np.zeros(size), gradient=np.zeros(size))
    elif case == "tie":
        options["initial"] = state(np.zeros(size), value=1e20)
        options["evaluate"] = lambda x: state(x, value=1e20)
    elif case == "general-gradient":
        gradient = np.sin(np.arange(size) + .3) * np.linspace(.1, 3., size)
        options["evaluate"] = lambda x: state(x, value=float(x @ gradient), gradient=gradient)
        options["initial"] = options["evaluate"](np.zeros(size))
    else:
        assert case == "field-budget"
    seed, report, events = linear_run(size, **options)
    return seed.tolist(), report, events


@pytest.mark.parametrize("size", [198, 360])
@pytest.mark.parametrize("case,reason", [
    ("field-budget", "field-budget"), ("geometry-budget", "geometry-budget"),
    ("both-budgets", "geometry-budget"),
    ("geometry-last-rejection", "certificate-limited"),
    ("field-last-rejection", "line-search-failed"),
    ("certificate-limited", "certificate-limited"),
    ("current-rejected", "line-search-failed"), ("armijo-rejected", "line-search-failed"),
    ("null-direction", "null-direction"), ("tie", "field-budget"),
    ("general-gradient", "field-budget"),
])
def test_all_stops_and_budget_priority(size, case, reason):
    seed, report, events = trace(case, size)
    before = json.dumps([seed, report, events], sort_keys=True)
    verdict = check(seed, report, events)
    assert verdict["control_flow_pass"], verdict
    assert verdict["reason"] == report["reason"] == reason
    assert verdict["proposals_checked"] == len(report["trials"])
    assert verdict["events_checked"] == len(events)
    assert verdict["counters"] == report["counters"]
    assert before == json.dumps([seed, report, events], sort_keys=True)
    for key in ("field_values_verified", "gradients_verified", "geometry_certificates_verified",
                "source_identity_verified", "physical_admission", "step4_pass"):
        assert verdict[key] is False


def rewrite(value, key, transform):
    """Change all redundant copies coherently; do not just break report/event equality."""
    if isinstance(value, dict):
        for name, item in value.items():
            if name == key:
                value[name] = transform(item)
            else:
                rewrite(item, key, transform)
    elif isinstance(value, list):
        for item in value:
            rewrite(item, key, transform)


@pytest.mark.parametrize("key,transform", [
    ("alpha", lambda v: v * 2),
    ("iteration", lambda v: v + 1),
    ("index", lambda v: v + 1),
    ("backtrack", lambda v: v + 1),
    ("parent_index", lambda v: 0),
    ("direction", lambda v: [v[0] * 2, *v[1:]]),
    ("directional_derivative", lambda v: v / 2),
    ("armijo_rhs", lambda v: math.nextafter(v, math.inf)),
    ("geometry_completed", lambda v: v + 1),
    ("field_attempted", lambda v: v + 1),
    ("accepted_indices", lambda v: v[::-1]),
    ("selected_index", lambda v: 0),
    ("accepted", lambda v: not v if type(v) is bool else v),
    ("current_pass", lambda v: False if v is not None else None),
    ("armijo_pass", lambda v: False if v is not None else None),
    ("calculation_complete", lambda v: False),
    ("certified", lambda v: "yes"),
    ("reservation", lambda v: dict(geometry=0, field=0)),
    ("reason", lambda v: "converged"),
    ("current", lambda v: math.nextafter(500000., math.inf)),
    ("value", lambda v: True),
])
def test_consistently_forged_policy_is_rejected(key, transform):
    seed, report, events = trace("field-budget")
    rewrite([report, events], key, transform)
    verdict = check(seed, report, events)
    assert not verdict["control_flow_pass"], (key, verdict)
    assert verdict["physical_admission"] is False


@pytest.mark.parametrize("fault", ["inactive-bits", "active-coordinate", "drop-event",
    "swap-events", "extra-event", "missing-trial", "extra-trial", "extra-key", "nonfinite",
    "non-json", "schema-type", "bool-counter", "initial-current", "seed-bits",
])
def test_corrupt_or_incomplete_trace_fails_closed(fault):
    seed, report, events = trace("field-budget")
    if fault in ("inactive-bits", "active-coordinate"):
        def move(x):
            value = list(x)
            value[5 if fault == "inactive-bits" else 0] = -0.0 if fault == "inactive-bits" else 9.
            return value
        rewrite([report["trials"], report["selected"], events[1:]], "x", move)
    elif fault == "drop-event":
        events.pop(2)
    elif fault == "swap-events":
        events[2], events[3] = events[3], events[2]
    elif fault == "extra-event":
        events.append(copy.deepcopy(events[-1]))
    elif fault == "missing-trial":
        report["trials"].pop()
    elif fault == "extra-trial":
        report["trials"].append(copy.deepcopy(report["trials"][-1]))
    elif fault == "extra-key":
        report["converged"] = True
    elif fault == "nonfinite":
        rewrite([report, events], "current", lambda v: float("nan"))
    elif fault == "non-json":
        report["selected"]["metrics"]["unexpected"] = object()
    elif fault == "schema-type":
        report["trials"][0] = None
    elif fault == "bool-counter":
        report["trials"][0]["index"] = False
    elif fault == "initial-current":
        report["initial"]["metrics"]["current"] = 500001.
    else:
        seed[5] = -0.0
    assert not check(seed, report, events)["control_flow_pass"]


def handmade_one_step():
    """Closed-form trace built without any producer or producer helper."""
    seed, gradient = [0.] * 198, [1.] + [0.] * 197
    initial = dict(x=seed.copy(), value=0., gradient=gradient, metrics=dict(current=200000.))
    direction = [-1.] + [0.] * 197
    x = [-0.001] + [0.] * 197
    selected = dict(x=x, value=-.001, gradient=[0.] * 198, metrics=dict(current=200000.))
    zero = dict(geometry_attempted=0, geometry_completed=0,
                field_attempted=0, field_completed=0, accepted=0)
    complete = dict(geometry_attempted=1, geometry_completed=1,
                    field_attempted=1, field_completed=1, accepted=1)
    cert = dict(certified=True, calculation_complete=True, status="certified")
    pending = dict(index=0, iteration=0, backtrack=0, alpha=.001, parent_index=None,
                   x=x, direction=direction, directional_derivative=-1.,
                   armijo_rhs=0.0 + 1e-4 * .001 * -1.0,
                   counters_before=zero, certificate=None, evaluation=None, accepted=False,
                   current_pass=None, armijo_pass=None)
    trial = dict(pending, certificate=cert, evaluation=selected, accepted=True,
                 current_pass=True, armijo_pass=True, reason="accepted", counters_after=complete)
    report = dict(initial=initial, trials=[trial], selected_index=0, selected=selected,
                  accepted_indices=[0], reason="null-direction", counters=complete)
    geometry = dict(zero, geometry_attempted=1, geometry_completed=1)
    events = [dict(event="search_started", initial=initial, counters=zero),
              dict(event="proposal_attempt", trial=pending, counters=zero,
                   reservation=dict(geometry=1, field=0)),
              dict(event="certificate_result", index=0, certificate=cert, counters=geometry),
              dict(event="field_attempt", index=0, x=x, counters=geometry,
                   reservation=dict(geometry=0, field=1)),
              dict(event="trial_result", trial=trial), dict(event="search_complete", result=report)]
    return seed, report, events


def test_closed_form_trace_passes_with_producer_disabled(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("producer must not be called")
    monkeypatch.setattr(controller, "search", forbidden)
    monkeypatch.setattr(controller, "_direction", forbidden)
    verdict = check(*handmade_one_step())
    assert verdict["control_flow_pass"], verdict


def test_decimal_rounded_armijo_bound_is_not_an_exact_machine_record():
    seed, report, events = handmade_one_step()
    rewrite([report, events], "armijo_rhs", lambda v: -1e-7)
    verdict = check(seed, report, events)
    assert not verdict["control_flow_pass"] and verdict["error"] == "Armijo bound"


def test_auditor_imports_and_runs_without_site_packages():
    code = (
        "import json, runpy, sys; m=runpy.run_path(sys.argv[1]); "
        "s,r,e=json.load(sys.stdin); print(json.dumps(m['audit'](s,r['initial'],r,e)))"
    )
    result = subprocess.run([sys.executable, "-I", "-S", "-c", code,
                             str(Path(verifier.__file__).resolve())],
                            input=json.dumps(handmade_one_step()), capture_output=True,
                            text=True, check=True, timeout=20)
    assert json.loads(result.stdout)["control_flow_pass"]


def test_fabricated_physics_is_not_mistaken_for_physical_verification():
    seed, report, events = handmade_one_step()
    # This analytic toy is not a field calculation. It deliberately still passes
    # control flow, even with an untrusted certificate claim in its metadata.
    rewrite([report, events], "certificate", lambda v: (
        None if v is None else dict(v, author="unverified fabricated assertion")))
    verdict = check(seed, report, events)
    assert verdict["control_flow_pass"], verdict
    assert not verdict["geometry_certificates_verified"] and not verdict["physical_admission"]
