"""Independent completed-trajectory control-flow audit, not a physical verifier.

Uses scalar arithmetic and stored callback returns, with no import of the
producer, NumPy, native libraries or filesystem. Field/gradient/certificate
truth and provenance require the later separate source/physical audits.
"""

import copy
import json
import math
import struct


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _number(value):
    _need(type(value) in (int, float) and math.isfinite(value), "finite real JSON number")
    return float(value)


def _finite_tree(value):
    if type(value) is dict:
        _need(all(type(key) is str for key in value), "string JSON keys")
        for item in value.values():
            _finite_tree(item)
    elif type(value) is list:
        for item in value:
            _finite_tree(item)
    elif type(value) in (int, float):
        _number(value)
    else:
        _need(value is None or type(value) in (str, bool), "JSON-compatible trace")


def _exact(actual, expected, label):
    def encode(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    _need(encode(actual) == encode(expected), label)


def _vector(values, size):
    _need(type(values) is list and len(values) == size, "full canonical vector")
    return [_number(value) for value in values]


def _bits(actual, expected, label):
    _need(len(actual) == len(expected), label)
    _need(all(struct.pack("!d", a) == struct.pack("!d", b)
              for a, b in zip(actual, expected, strict=True)), label)


def _state(value, x):
    _need(type(value) is dict and set(value) == {"x", "value", "gradient", "metrics"},
          "exact evaluation schema")
    _bits(_vector(value["x"], len(x)), x, "evaluation coordinates")
    _number(value["value"])
    _vector(value["gradient"], len(x))
    _need(type(value["metrics"]) is dict and "current" in value["metrics"], "current metric")
    _number(value["metrics"]["current"])


def _close(actual, expected, label):
    _need(math.isclose(_number(actual), expected, rel_tol=5e-12, abs_tol=1e-12), label)


def _direction(gradient, order):
    width = 2 * order + 1
    modes = [((k % width) + 1) // 2 for k in range(len(gradient))]
    raw = [-g / (1 + m*m)**2 if m <= 2 else 0.0
           for g, m in zip(gradient, modes, strict=True)]
    axes = []
    for start in range(0, len(raw), width):
        axis = abs(raw[start])
        for k in range(1, width, 2):
            axis += math.hypot(raw[start+k], raw[start+k+1])
        axes.append(axis)
    bound = max(math.hypot(*axes[i:i+3]) for i in range(0, len(axes), 3))
    _need(math.isfinite(bound), "finite D0 normalization")
    if bound == 0:
        return None, modes
    return [value / bound for value in raw], modes


def _certificate(value):
    _need(type(value) is dict and type(value.get("certified")) is bool
          and type(value.get("calculation_complete")) is bool, "certificate schema")
    certified = value["certified"]
    _need(value.get("status") == ("certified" if certified else "uncertified")
          and (not certified or value["calculation_complete"]), "certificate consistency")
    return certified


def audit(seed, initial, report, events):
    """Return an explicitly limited verdict; corrupt/incomplete traces fail closed."""
    scope = dict(field_values_verified=False, gradients_verified=False,
                 geometry_certificates_verified=False, source_identity_verified=False,
                 physical_admission=False, step4_pass=False)
    try:
        details = _audit(seed, initial, report, events)
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError) as error:
        return dict(control_flow_pass=False, error=str(error), **scope)
    return dict(control_flow_pass=True, **details, **scope)


def _audit(seed, initial, report, events):
    _finite_tree([seed, initial, report, events])
    _need(type(seed) is list and len(seed) in (198, 360), "registered seed class")
    seed = _vector(seed, len(seed))
    order = 5 if len(seed) == 198 else 7
    _state(initial, seed)
    _need(abs(initial["metrics"]["current"]) <= 500000, "initial current gate")
    _need(type(report) is dict and set(report) == {
        "initial", "trials", "selected_index", "selected", "accepted_indices", "reason", "counters"
    }, "report schema")
    _exact(report["initial"], initial, "initial state identity")
    trials = report["trials"]
    _need(type(trials) is list and len(trials) <= 116, "proposal budget/schema")
    _need(type(events) is list and len(events) <= 466, "event budget/schema")
    position = 0

    def event(kind, **payload):
        nonlocal position
        _need(position < len(events), "missing event")
        _exact(events[position], dict(event=kind, **payload), f"event {position}: {kind}")
        position += 1

    counts = dict(geometry_attempted=0, geometry_completed=0,
                  field_attempted=0, field_completed=0, accepted=0)
    current = selected = initial
    parent = selected_index = None
    accepted, index, iteration, backtrack, admitted = [], 0, 0, 0, False
    event("search_started", initial=initial, counters=counts)
    while True:
        if backtrack == 16:
            reason = "line-search-failed" if admitted else "certificate-limited"
            break
        if counts["geometry_attempted"] == 116:
            reason = "geometry-budget"
            break
        if counts["field_attempted"] == 20:
            reason = "field-budget"
            break
        independent, modes = _direction(current["gradient"], order)
        if independent is None:
            reason = "null-direction"
            break
        _need(index < len(trials), "missing trial before termination")
        trial = trials[index]
        _need(type(trial) is dict and set(trial) == {
            "index", "iteration", "backtrack", "alpha", "parent_index", "x", "direction",
            "directional_derivative", "armijo_rhs", "counters_before", "certificate",
            "evaluation", "accepted", "current_pass", "armijo_pass", "reason", "counters_after"
        }, "trial schema")
        for key, expected in dict(index=index, iteration=iteration, backtrack=backtrack,
                                  parent_index=parent).items():
            _exact(trial[key], expected, f"trial {key}")
        alpha = math.ldexp(0.001, -backtrack)
        _exact(trial["alpha"], alpha, "backtracking step")
        direction = _vector(trial["direction"], len(seed))
        for actual, expected, m in zip(direction, independent, modes, strict=True):
            _close(actual, expected, "independent direction")
            _need(m <= 2 or actual == 0, "inactive direction must vanish")
        slope = sum(g*d for g, d in zip(current["gradient"], direction, strict=True))
        _close(trial["directional_derivative"], slope, "directional derivative")
        _need(slope < 0 and trial["directional_derivative"] < 0, "strict descent")
        proposal = [current["x"][k] + alpha * direction[k] if modes[k] <= 2 else seed[k]
                    for k in range(len(seed))]
        _bits(_vector(trial["x"], len(seed)), proposal, "proposal coordinate bits")
        rhs = current["value"] + 1e-4 * alpha * trial["directional_derivative"]
        _exact(trial["armijo_rhs"], rhs, "Armijo bound")
        _exact(trial["counters_before"], counts, "counters before")
        pending = copy.deepcopy(trial)
        for key in ("reason", "counters_after"):
            pending.pop(key)
        pending.update(certificate=None, evaluation=None, accepted=False,
                       current_pass=None, armijo_pass=None)
        event("proposal_attempt", trial=pending, counters=counts,
              reservation=dict(geometry=1, field=0))
        counts["geometry_attempted"] += 1
        positive = _certificate(trial["certificate"])
        counts["geometry_completed"] += 1
        event("certificate_result", index=index, certificate=trial["certificate"], counters=counts)
        evaluation, current_pass, armijo_pass, take = None, None, None, False
        decision = "geometry-rejected"
        if positive:
            admitted = True
            event("field_attempt", index=index, x=trial["x"], counters=counts,
                  reservation=dict(geometry=0, field=1))
            counts["field_attempted"] += 1
            evaluation = trial["evaluation"]
            _state(evaluation, proposal)
            counts["field_completed"] += 1
            current_pass = abs(evaluation["metrics"]["current"]) <= 500000
            armijo_pass = evaluation["value"] <= rhs
            take = current_pass and armijo_pass
            decision = "accepted" if take else (
                "current-rejected" if not current_pass else "armijo-rejected")
            counts["accepted"] += int(take)
        for key, expected in dict(evaluation=evaluation, current_pass=current_pass,
                                  armijo_pass=armijo_pass, accepted=take, reason=decision,
                                  counters_after=counts).items():
            _exact(trial[key], expected, f"decision {key}")
        event("trial_result", trial=trial)
        if take:
            current, parent = evaluation, index
            accepted.append(index)
            if current["value"] < selected["value"]:
                selected, selected_index = current, index
            iteration, backtrack, admitted = iteration + 1, 0, False
        else:
            backtrack += 1
        index += 1
    _need(index == len(trials), "trailing trial after stop")
    for key, expected in dict(selected=selected, selected_index=selected_index,
                              accepted_indices=accepted, reason=reason, counters=counts).items():
        _exact(report[key], expected, f"final {key}")
    event("search_complete", result=report)
    _need(position == len(events), "trailing events")
    return dict(reason=reason, proposals_checked=index, events_checked=position,
                counters=copy.deepcopy(counts))
