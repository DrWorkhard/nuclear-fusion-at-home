"""Registered low-mode startup screens and exact numerical-bundle replay.

No native work or physical acceptance. Historical full-space FD helpers are
intentionally not reused: these eight probes have different directions.
"""

import numpy as np

from fusion_baselines.protected_coil_search import _array, _class, _state, directions, weights
from fusion_baselines.protected_search_journal import _encode


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def points(seed, nbase, order):
    """Ten ordered states; inactive seed bits are retained even for signed zero."""
    size = int(np.prod(_class(nbase, order)))
    seed = _array(seed, (size,))
    active = weights(nbase, order) > 0
    states = [seed.copy()]
    for direction in directions(nbase, order):
        for step in (1e-5, 5e-6):
            for sign in (1, -1):
                state = seed.copy()
                state[active] += sign * step * direction[active]
                states.append(state)
    return states + [seed.copy()]


def derivative_screen(seed, nbase, order, rows, independent_values=None):
    """Check both directions/steps without implying independent physical truth.

    Rows use controller states: x/value/gradient/metrics. Optional values must be
    supplied by separate raw-array reconstruction; this function cannot verify
    their provenance. Exact raw-array/snapshot replay is a separate check below.
    """
    expected = points(seed, nbase, order)
    _need(type(rows) is list and len(rows) == 10, "ten ordered startup states required")
    states = [_state(row, x) for row, x in zip(rows, expected, strict=True)]
    repeat = _encode(states[0]) == _encode(states[-1])
    values = np.array([r["value"] for r in states])
    alternatives = [("recorded", values)]
    independent_repeat = None
    if independent_values is not None:
        independent = _array(independent_values, (10,))
        _need(np.allclose(values, independent, rtol=5e-10, atol=1e-12),
              "independently reconstructed startup objectives disagree")
        alternatives.append(("independent", independent))
        independent_repeat = independent[0].tobytes() == independent[-1].tobytes()
    checks = []
    for k, direction in enumerate(directions(nbase, order)):
        analytic = float(np.dot(states[0]["gradient"], direction))
        _need(np.isfinite(analytic), "finite directional derivative required")
        for j, step in enumerate((1e-5, 5e-6)):
            index = 1 + 4 * k + 2 * j
            with np.errstate(over="raise", invalid="raise"):
                represented = (expected[index] - expected[index + 1]) / (2 * step)
            _need(np.linalg.norm(represented - direction) <= 1e-8,
                  "representable startup probe direction required")
            for label, data in alternatives:
                with np.errstate(over="raise", invalid="raise"):
                    fd = float((data[index] - data[index + 1]) / (2 * step))
                error = abs(fd - analytic)
                relative = error / max(abs(fd), abs(analytic), 1e-30)
                checks.append(dict(direction=k, step=step, objective=label, analytic=analytic,
                                   finite_difference=fd, absolute_error=error,
                                   relative_error=relative,
                                   passed=bool(error <= 1e-8 or relative <= 2e-4)))
    return dict(derivative_pass=all(r["passed"] for r in checks), exact_state_repeat=repeat,
                startup_screen_pass=repeat and independent_repeat is not False
                and all(r["passed"] for r in checks), checks=checks,
                exact_independent_value_repeat=independent_repeat,
                independently_supplied_values=independent_values is not None,
                raw_arrays_replayed=False, physical_admission=False, step4_pass=False)


def exact_bundle_replay(actual, expected):
    """Exact numerical data, not NPZ container identity or a repeated whole search.

    Each bundle has state, snapshot and arrays only, excluding timestamps and
    storage-reference paths. State/snapshot JSON types and signed zero matter;
    arrays must match finite numeric dtype, shape and C-order element bytes.
    This equality helper does not establish bundle completeness: the caller must
    first bind a complete admitted reference and enforce the native bundle schema.
    """
    for value in (actual, expected):
        _need(type(value) is dict and set(value) == {"state", "snapshot", "arrays"},
              "exact numerical replay bundle schema required")
        _need(type(value["arrays"]) is dict and bool(value["arrays"]),
              "complete named replay arrays required")
    for key in ("state", "snapshot"):
        _need(_encode(actual[key]) == _encode(expected[key]), "exact replay " + key)
    _need(set(actual["arrays"]) == set(expected["arrays"]), "exact replay array keys")
    for key, expected_array in expected["arrays"].items():
        a, b = np.asarray(actual["arrays"][key]), np.asarray(expected_array)
        _need(type(key) is str and a.dtype.kind in "iuf" and b.dtype.kind in "iuf"
              and np.isfinite(a).all() and np.isfinite(b).all(), "finite real replay arrays")
        _need(a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes(),
              "exact replay array " + key)
    return dict(exact_bundle_replay=True, whole_search_repeated=False,
                bundle_schema_verified=False,
                physical_admission=False, step4_pass=False)
