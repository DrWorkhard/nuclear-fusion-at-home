"""Pure fixed-budget protected low-mode descent; no native or filesystem work.

``certify(original_seed, candidate)`` and ``evaluate(candidate)`` receive private
flat float64 copies. ``record(event)`` must persist its private JSON-compatible
copy synchronously or raise. A proposal reservation always precedes certificate
work, and a field reservation always precedes field work. Exceptions stop the
search; returned negative geometry certificates alone permit backtracking.
"""

import copy
import math

import numpy as np

MAX_PROPOSALS = 116
MAX_FIELD_TRIALS = 20
BACKTRACK_STEPS = 16
START_STEP = 1e-3
ARMIJO = 1e-4
CURRENT_LIMIT = 500000.0


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _class(nbase, order):
    _require(
        type(nbase) is type(order) is int and (nbase, order) in ((6, 5), (8, 7)),
        "registered n6/M5 or n8/M7 class required",
    )
    return nbase, 3, 2 * order + 1


def weights(nbase, order):
    """Flat P diagonal; the coordinate scale is sqrt(P), not P again."""
    shape = _class(nbase, order)
    modes = np.r_[0, np.repeat(np.arange(1, order + 1), 2)]
    values = np.where(modes <= 2, 1.0 / (1 + modes**2) ** 2, 0.0)
    return np.broadcast_to(values, shape).copy().ravel()


def directions(nbase, order):
    """Two fixed physical FD directions using S=sqrt(P), Euclidean norm1."""
    scale = np.sqrt(weights(nbase, order))
    indices = np.arange(len(scale)) + 1
    result = np.stack([function(indices) * scale for function in (np.sin, np.cos)])
    return result / np.linalg.norm(result, axis=1)[:, None]


def _array(value, shape):
    array = np.asarray(value)
    _require(
        array.shape == shape and array.dtype.kind in "iuf" and np.isfinite(array).all(),
        "complete finite real canonical vector required",
    )
    return np.array(array, dtype=float, copy=True)


def _json(value):
    if isinstance(value, np.ndarray):
        return _json(value.tolist())
    if isinstance(value, np.generic):
        value = value.item()
    if type(value) is dict:
        _require(all(type(key) is str for key in value), "string JSON keys required")
        return {key: _json(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json(item) for item in value]
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    raise ValueError("finite JSON-compatible callback result required")


def _scalar(value):
    _require(not isinstance(value, (bool, np.bool_)), "boolean is not a real scalar")
    array = _array(value, ())
    return float(array)


def _state(value, expected_x):
    _require(
        type(value) is dict and set(value) == {"x", "value", "gradient", "metrics"},
        "exact evaluator state schema required",
    )
    x = _array(value["x"], expected_x.shape)
    _require(x.tobytes() == expected_x.tobytes(), "evaluated state differs from requested bits")
    gradient = _array(value["gradient"], expected_x.shape)
    objective = _scalar(value["value"])
    _require(
        type(value["metrics"]) is dict and "current" in value["metrics"],
        "physical current metric required",
    )
    _scalar(value["metrics"]["current"])
    return _json(dict(x=x, value=objective, gradient=gradient, metrics=value["metrics"]))


def _certificate(value):
    _require(
        type(value) is dict
        and type(value.get("certified")) is bool
        and type(value.get("calculation_complete")) is bool,
        "explicit boolean geometric certificate required",
    )
    certified = value["certified"]
    _require(
        value.get("status") == ("certified" if certified else "uncertified")
        and (not certified or value["calculation_complete"]),
        "consistent completed positive geometric certificate required",
    )
    return _json(value)


def _direction(gradient, diagonal, shape):
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        raw = (-diagonal * gradient).reshape(shape)
        amplitudes = np.hypot(raw[..., 1::2], raw[..., 2::2])
        axes = abs(raw[..., 0]) + amplitudes.sum(axis=-1)
        bound = float(np.hypot(np.hypot(axes[:, 0], axes[:, 1]), axes[:, 2]).max())
        _require(math.isfinite(bound), "nonfinite direction normalization")
        if bound == 0:
            return None
        direction = (raw / bound).ravel()
        slope = float(np.dot(gradient, direction))
        _require(
            np.isfinite(direction).all() and math.isfinite(slope) and slope < 0,
            "finite strictly descending normalized direction required",
        )
    return direction, slope


def search(seed, initial, certify, evaluate, record):
    """Run exactly the registered fixed search policy, with no tuning arguments.

    Initial evaluation is external work and must match the unchanged seed.
    ``trials`` contains proposals only, indexed from0. ``selected_index=None``
    denotes the initial seed; otherwise it names an accepted proposal. Selection
    retains the earliest equal value. Reported completion is algorithmic, never
    physical admission. Field and geometry callbacks are independently budgeted.
    """
    seed_input = np.asarray(seed)
    classes = {198: (6, 5), 360: (8, 7)}
    _require(seed_input.ndim == 1 and seed_input.size in classes, "registered full flat seed")
    nbase, order = classes[seed_input.size]
    seed = _array(seed, seed_input.shape)
    current = initial = _state(initial, seed)
    _require(
        abs(_scalar(initial["metrics"]["current"])) <= CURRENT_LIMIT,
        "initial physical current must satisfy unchanged gate",
    )
    _require(
        all(callable(callback) for callback in (certify, evaluate, record)),
        "certificate, evaluation and synchronous record callbacks required",
    )
    diagonal = weights(nbase, order)
    active = diagonal > 0
    counters = dict(
        geometry_attempted=0, geometry_completed=0, field_attempted=0, field_completed=0, accepted=0
    )
    trials, accepted_indices = [], []
    selected, selected_index, parent_index = initial, None, None
    iteration, stage, pending = 0, "start", None

    def emit(kind, **payload):
        record(_json(dict(event=kind, **payload)))

    def finish(reason):
        result = _json(
            dict(
                initial=initial,
                trials=trials,
                selected_index=selected_index,
                selected=selected,
                accepted_indices=accepted_indices,
                reason=reason,
                counters=counters,
            )
        )
        emit("search_complete", result=result)
        return result

    try:
        emit("search_started", initial=initial, counters=counters)
        while True:
            if counters["geometry_attempted"] >= MAX_PROPOSALS:
                return finish("geometry-budget")
            if counters["field_attempted"] >= MAX_FIELD_TRIALS:
                return finish("field-budget")
            stage = "direction"
            gradient = _array(current["gradient"], seed.shape)
            descent = _direction(gradient, diagonal, _class(nbase, order))
            if descent is None:
                return finish("null-direction")
            direction, slope = descent
            admitted = False
            for backtrack in range(BACKTRACK_STEPS):
                if counters["geometry_attempted"] >= MAX_PROPOSALS:
                    return finish("geometry-budget")
                if counters["field_attempted"] >= MAX_FIELD_TRIALS:
                    return finish("field-budget")
                alpha = math.ldexp(START_STEP, -backtrack)
                x = seed.copy()
                with np.errstate(over="raise", invalid="raise"):
                    x[active] = np.asarray(current["x"])[active] + alpha * direction[active]
                _require(np.isfinite(x).all(), "finite proposed canonical coefficients required")
                rhs = current["value"] + ARMIJO * alpha * slope
                _require(math.isfinite(rhs), "finite Armijo bound required")
                pending = _json(
                    dict(
                        index=len(trials),
                        iteration=iteration,
                        backtrack=backtrack,
                        alpha=alpha,
                        parent_index=parent_index,
                        x=x,
                        direction=direction,
                        directional_derivative=slope,
                        armijo_rhs=rhs,
                        counters_before=counters,
                        certificate=None,
                        evaluation=None,
                        accepted=False,
                        current_pass=None,
                        armijo_pass=None,
                    )
                )
                stage = "certificate-reservation"
                emit(
                    "proposal_attempt",
                    trial=pending,
                    counters=counters,
                    reservation=dict(geometry=1, field=0),
                )
                counters["geometry_attempted"] += 1
                stage = "certificate"
                certificate_result = certify(seed.copy(), x.copy())
                counters["geometry_completed"] += 1
                pending["certificate"] = _certificate(certificate_result)
                emit(
                    "certificate_result",
                    index=pending["index"],
                    certificate=pending["certificate"],
                    counters=counters,
                )
                if not pending["certificate"]["certified"]:
                    pending["reason"] = "geometry-rejected"
                else:
                    admitted = True
                    stage = "field-reservation"
                    emit(
                        "field_attempt",
                        index=pending["index"],
                        x=x,
                        counters=counters,
                        reservation=dict(geometry=0, field=1),
                    )
                    counters["field_attempted"] += 1
                    stage = "field"
                    evaluated = evaluate(x.copy())
                    counters["field_completed"] += 1
                    evaluation = _state(evaluated, x)
                    pending["evaluation"] = evaluation
                    pending["current_pass"] = (
                        abs(_scalar(evaluation["metrics"]["current"])) <= CURRENT_LIMIT
                    )
                    pending["armijo_pass"] = evaluation["value"] <= rhs
                    pending["accepted"] = pending["current_pass"] and pending["armijo_pass"]
                    pending["reason"] = (
                        "accepted"
                        if pending["accepted"]
                        else "current-rejected"
                        if not pending["current_pass"]
                        else "armijo-rejected"
                    )
                    if pending["accepted"]:
                        counters["accepted"] += 1
                pending["counters_after"] = copy.deepcopy(counters)
                stage = "trial-publication"
                emit("trial_result", trial=pending)
                trials.append(copy.deepcopy(pending))
                if pending["accepted"]:
                    current, parent_index = pending["evaluation"], pending["index"]
                    accepted_indices.append(parent_index)
                    if current["value"] < selected["value"]:
                        selected, selected_index = current, parent_index
                    break
            else:
                return finish("line-search-failed" if admitted else "certificate-limited")
            iteration += 1
    except Exception as error:
        # An error record is best-effort; failure to record must never authorize
        # more work or replace the original exception with a synthetic result.
        try:
            emit(
                "search_error",
                stage=stage,
                error_type=type(error).__name__,
                error=str(error),
                counters=counters,
                trial=pending,
            )
        except Exception as recording_error:
            error.add_note(
                f"error record failed: {type(recording_error).__name__}: {recording_error}"
            )
        raise
