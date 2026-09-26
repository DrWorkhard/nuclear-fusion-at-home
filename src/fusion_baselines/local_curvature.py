"""Registered padded binary64 homotopy bounds, not interval proofs or admission.

Pure geometry only. The state layer owns names, original seed/report provenance,
physical-copy identity, unchanged non-curvature gates and publication budgets.
This producer does not read project data or import its independent checker.
"""

import json
import math
import time

import numpy as np

EPS = 1024 * 2.0**-52
CAPS = dict(t_depth=14, lambda_depth=10, evaluations=16383)
MAX_NODE_BYTES = 256
MAX_REPORT_BYTES = 8 * 1024**2


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _finite(value):
    if not math.isfinite(value):
        raise ArithmeticError("nonfinite local curvature arithmetic")
    return value


def _sum(values):
    return _finite(math.fsum(_finite(value) for value in values))


def _pad(*values):
    return _finite(EPS * max(1.0, _sum(abs(value) for value in values)))


def _upper(*values):
    return _finite(_sum(values) + _pad(*values))


def _lower(first, *losses):
    return _finite(_sum((first, *(-value for value in losses))) - _pad(first, *losses))


def _no_boolean(value):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("boolean coefficients or matrix entries are not real inputs")
    if isinstance(value, (list, tuple, np.ndarray)):
        if isinstance(value, np.ndarray) and value.ndim == 0:
            _no_boolean(value.item())
        else:
            for item in value:
                _no_boolean(item)


def _input(value, label, shape=None):
    _no_boolean(value)
    array = np.asarray(value)
    _need(array.dtype.kind in "iuf", "real numerical " + label + " required")
    _need(array.ndim == 2 and array.shape[0] == 3, "three Cartesian rows: " + label)
    _need(shape is None or array.shape == shape, "matched shape: " + label)
    _need(np.isfinite(array).all(), "finite " + label + " required")
    try:
        with np.errstate(over="raise", invalid="raise"):
            copied = np.array(array, dtype=np.float64, copy=True)
    except (FloatingPointError, OverflowError) as error:
        raise ValueError("finite binary64 " + label + " required") from error
    _need(np.isfinite(copied).all(), "finite binary64 " + label + " required")
    return tuple(tuple(float(v) for v in row) for row in copied)


def _rectangle(path):
    _need(
        type(path) is str and len(path) <= 48 and len(path) % 2 == 0, "bounded dyadic path required"
    )
    indices, depths = dict(t=0, l=0), dict(t=0, l=0)
    for at in range(0, len(path), 2):
        axis, child = path[at : at + 2]
        _need(axis in ("t", "l") and child in ("0", "1"), "dyadic axis/child required")
        indices[axis] = 2 * indices[axis] + int(child)
        depths[axis] += 1
    _need(depths["t"] <= 14 and depths["l"] <= 10, "registered dyadic depth limits")
    endpoints = {
        axis: (indices[axis] / 2 ** depths[axis], (indices[axis] + 1) / 2 ** depths[axis])
        for axis in ("t", "l")
    }
    t0, t1 = endpoints["t"]
    l0, l1 = endpoints["l"]
    return (t0 + t1) / 2, (l0 + l1) / 2, (t1 - t0) / 2, (l1 - l0) / 2, l0, l1, depths


class CurveModel:
    """Private real coefficients; transformation arithmetic is attempted lazily.

    bound(path) returns [Vminus, Kupper, T, H]. Kupper is None when a
    nonpositive speed/denominator prevents division. ArithmeticError means the
    entire bound is unavailable; the traversal records an all-null failure leaf.
    Matrix input is M, so each physical coefficient is transformed by M.T.
    """

    def __init__(self, seed, candidate, matrix):
        self._seed = _input(seed, "seed")
        width = len(self._seed[0])
        _need(width >= 3 and width % 2 == 1, "nonconstant odd Fourier width required")
        self._candidate = _input(candidate, "candidate", (3, width))
        self._matrix = _input(matrix, "matrix", (3, 3))
        self._width = width
        self._prepared = False
        self._lambda_cache, self._endpoint_cache, self._center_error_cache = {}, {}, {}

    def _transform(self, coefficients):
        values, errors = [], []
        for axis in range(3):
            row, error = [], []
            for k in range(self._width):
                products = tuple(
                    _finite(self._matrix[j][axis] * coefficients[j][k]) for j in range(3)
                )
                row.append(_sum(products))
                error.append(_pad(*products))
            values.append(row)
            errors.append(error)
        return values, errors

    def _derivative_bound(self, coefficients, errors, order):
        axes = []
        for axis in range(3):
            terms = []
            for mode, omega in enumerate(self._omega, start=1):
                sine, cosine = 2 * mode - 1, 2 * mode
                amplitude = _upper(
                    math.hypot(
                        _finite(abs(coefficients[axis][sine]) + errors[axis][sine]),
                        _finite(abs(coefficients[axis][cosine]) + errors[axis][cosine]),
                    )
                )
                terms.append(_finite(omega**order * amplitude))
            axes.append(_upper(*terms))
        return _upper(math.hypot(*axes))

    def _prepare(self):
        if self._prepared:
            return
        self._omega = tuple(_finite(2 * math.pi * m) for m in range(1, (self._width - 1) // 2 + 1))
        self._s, self._es = self._transform(self._seed)
        target, et = self._transform(self._candidate)
        self._d, self._ed = [], []
        for axis in range(3):
            row, errors = [], []
            for k in range(self._width):
                s, t = self._s[axis][k], target[axis][k]
                row.append(_finite(t - s))
                errors.append(_upper(et[axis][k], self._es[axis][k], _pad(t, s)))
            self._d.append(row)
            self._ed.append(errors)
        self._zero = [[0.0] * self._width for _ in range(3)]
        self._d1 = self._derivative_bound(self._d, self._ed, 1)
        self._d2 = self._derivative_bound(self._d, self._ed, 2)
        self._prepared = True

    def _at_lambda(self, value):
        if value in self._lambda_cache:
            return self._lambda_cache[value]
        coefficients, errors = [], []
        for axis in range(3):
            row, error = [], []
            for k in range(self._width):
                s, delta = self._s[axis][k], _finite(value * self._d[axis][k])
                row.append(_finite(s + delta))
                error.append(
                    _upper(self._es[axis][k], _finite(value * self._ed[axis][k]), _pad(s, delta))
                )
            coefficients.append(row)
            errors.append(error)
        self._lambda_cache[value] = coefficients, errors
        return coefficients, errors

    def _endpoint_bounds(self, value):
        if value not in self._endpoint_cache:
            coefficients, errors = self._at_lambda(value)
            self._endpoint_cache[value] = (
                self._derivative_bound(coefficients, errors, 2),
                self._derivative_bound(coefficients, errors, 3),
            )
        return self._endpoint_cache[value]

    def _center_errors(self, value):
        if value not in self._center_error_cache:
            coefficients, errors = self._at_lambda(value)
            ev = _upper(
                self._derivative_bound(self._zero, errors, 1),
                _pad(self._derivative_bound(coefficients, self._zero, 1)),
            )
            ea = _upper(
                self._derivative_bound(self._zero, errors, 2),
                _pad(self._derivative_bound(coefficients, self._zero, 2)),
            )
            self._center_error_cache[value] = ev, ea
        return self._center_error_cache[value]

    def _center(self, coefficients, parameter):
        velocity, acceleration = [], []
        for axis in range(3):
            first, second = [], []
            for mode, omega in enumerate(self._omega, start=1):
                angle = _finite(omega * parameter)
                sine, cosine = math.sin(angle), math.cos(angle)
                cs, cc = coefficients[axis][2 * mode - 1 : 2 * mode + 1]
                first.append(_finite(omega * _sum((cs * cosine, -cc * sine))))
                second.append(_finite(-(omega**2) * _sum((cs * sine, cc * cosine))))
            velocity.append(_sum(first))
            acceleration.append(_sum(second))
        return velocity, acceleration

    def bound(self, path):
        tc, lc, h, r, l0, l1, _ = _rectangle(path)
        try:
            self._prepare()
            endpoints = [self._endpoint_bounds(value) for value in (l0, l1)]
            a_bound = max(bounds[0] for bounds in endpoints)
            j_bound = max(bounds[1] for bounds in endpoints)
            center, _ = self._at_lambda(lc)
            v, a = self._center(center, tc)
            nv, na = _finite(math.hypot(*v)), _finite(math.hypot(*a))
            ev, ea = self._center_errors(lc)
            cross = [_sum((v[i] * a[j], -v[j] * a[i])) for i, j in ((1, 2), (2, 0), (0, 1))]
            nc = _upper(math.hypot(*cross), ev * na, ea * nv, ev * ea, _pad(nv * na))
            error = _upper(h * a_bound, r * self._d1)
            vminus, vplus = _lower(nv, ev, error), _upper(nv, ev, error)
            numerator = _upper(
                nc, h * vplus * j_bound, r * _upper(self._d1 * a_bound, vplus * self._d2)
            )
            t_weight = _finite(h * vplus * j_bound + 36 * vplus**2 * h * a_bound)
            l_weight = _finite(
                r * (self._d1 * a_bound + vplus * self._d2) + 36 * vplus**2 * r * self._d1
            )
            curvature = None
            if vminus > 0:
                denominator = _lower(vminus**3)
                if denominator > 0:
                    curvature = _upper(numerator / denominator)
            return [vminus, curvature, t_weight, l_weight]
        except (OverflowError, ZeroDivisionError, FloatingPointError) as error:
            raise ArithmeticError("unavailable local curvature bound arithmetic") from error


def _caps(caps):
    caps = CAPS.copy() if caps is None else caps
    _need(type(caps) is dict and set(caps) == set(CAPS), "exact registered cap keys")
    for key, value in caps.items():
        _need(
            type(value) is int and (1 if key == "evaluations" else 0) <= value <= CAPS[key],
            "positive evaluation/nonnegative depth caps cannot exceed registration",
        )
    return caps.copy()


def _encode(value):
    return (
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
        + "\n"
    ).encode("utf-8")


def _node(path, action, numbers):
    node = [path, action, *numbers]
    _need(len(_encode(node)) <= MAX_NODE_BYTES, "local curvature node exceeds 256 bytes")
    return node


def certify_curve(seed, candidate, matrix, *, deadline, clock=time.monotonic, caps=None):
    """Complete DFS frontier; a timed or bounded negative result never passes.

    Schema/clock/serialization errors raise instead of creating a certificate.
    Only attempted bound arithmetic errors become ordinary negative leaves.
    """
    _need(
        type(deadline) in (int, float) and math.isfinite(deadline) and deadline >= 0,
        "finite nonnegative absolute deadline required",
    )
    _need(callable(clock), "monotonic clock required")
    limits = _caps(caps)
    model = CurveModel(seed, candidate, matrix)
    stack, nodes, attempted, last_clock = [""], [], 0, None

    def expired():
        nonlocal last_clock
        now = clock()
        _need(
            type(now) in (int, float) and math.isfinite(now) and now >= 0,
            "finite nonnegative clock value required",
        )
        _need(last_clock is None or now >= last_clock, "monotonic clock moved backward")
        last_clock = now
        return now >= deadline

    def pending():
        while stack:
            nodes.append(_node(stack.pop(), "pending", [None] * 4))

    reason = "complete"
    while stack:
        if expired():
            reason = "deadline"
            pending()
            break
        if attempted == limits["evaluations"]:
            reason = "evaluation-budget"
            pending()
            break
        path = stack.pop()
        attempted += 1
        arithmetic = False
        try:
            numbers = model.bound(path)
        except ArithmeticError:
            numbers, arithmetic = [None] * 4, True
        if expired():
            nodes.append(_node(path, "arithmetic" if arithmetic else "deadline", numbers))
            reason = "deadline"
            pending()
            break
        if arithmetic:
            nodes.append(_node(path, "arithmetic", numbers))
            continue
        vminus, curvature, t_weight, l_weight = numbers
        if vminus > 0 and curvature is not None and 0 < curvature <= 12:
            action = "pass"
        else:
            depths = _rectangle(path)[-1]
            t_available = depths["t"] < limits["t_depth"]
            l_available = depths["l"] < limits["lambda_depth"]
            if not t_available and not l_available:
                action = "depth"
            else:
                axis = "t" if t_available and (not l_available or t_weight >= l_weight) else "l"
                action = "split_" + axis
                stack.extend((path + axis + "1", path + axis + "0"))
        nodes.append(_node(path, action, numbers))
    result = dict(
        schema_version=1,
        kind="local-homotopy-curvature",
        caps=limits,
        nodes=nodes,
        attempted=attempted,
        curvature_pass=reason == "complete"
        and all(row[1] in ("pass", "split_t", "split_l") for row in nodes),
        stop_reason=reason,
        interval_arithmetic=False,
        field_pass=False,
        step4_pass=False,
    )
    _need(len(_encode(result)) <= MAX_REPORT_BYTES, "local curvature curve report exceeds 8 MiB")
    if expired():
        result.update(stop_reason="deadline", curvature_pass=False)
        _need(
            len(_encode(result)) <= MAX_REPORT_BYTES, "local curvature failure report exceeds 8 MiB"
        )
    return result
