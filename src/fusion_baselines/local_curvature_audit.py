"""Independent arithmetic and complete-tree audit of local curvature reports.

No import of the producer. This checks padded binary64 analytical bounds, not
formal interval arithmetic, fields, or a physical design acceptance decision.
Named input/source identity and whole-state deadlines are the caller's duty.
"""

import json
import math
import numbers
import time

import numpy as np

_E = 1024 * 2.0**-52
_MAXIMA = dict(t_depth=14, lambda_depth=10, evaluations=16383)
_FIELDS = {
    "schema_version", "kind", "caps", "nodes", "attempted", "curvature_pass",
    "stop_reason", "interval_arithmetic", "field_pass", "step4_pass",
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _number(value):
    return isinstance(value, numbers.Real) and not isinstance(value, (bool, np.bool_))


def _array(value, label):
    try:
        data = np.asarray(value, dtype=object)
        _need(all(_number(v) for v in data.flat), f"{label}: real numbers without aliases")
        result = np.array(value, dtype=float, copy=True)
    except (TypeError, OverflowError) as error:
        raise ValueError(f"{label}: finite binary64 array required") from error
    _need(np.isfinite(result).all(), f"{label}: finite values required")
    return result


def _checked(value):
    if not math.isfinite(value):
        raise ArithmeticError("nonfinite bound arithmetic")
    return value


def _pad(terms):
    return _checked(_E * max(1.0, math.fsum(abs(_checked(x)) for x in terms)))


def _up(*terms):
    return _checked(math.fsum(terms) + _pad(terms))


def _down(value, *losses):
    return _checked(math.fsum((value, *(-x for x in losses))) - _pad((value, *losses)))


def _interval(path):
    _need(type(path) is str and len(path) % 2 == 0 and len(path) <= 48,
          "canonical dyadic path required")
    indices, depths = [0, 0], [0, 0]
    for pos in range(0, len(path), 2):
        axis, bit = path[pos:pos + 2]
        _need(axis in "tl" and bit in "01", "invalid dyadic token")
        a = 0 if axis == "t" else 1
        indices[a] = 2 * indices[a] + int(bit)
        depths[a] += 1
    _need(depths[0] <= 14 and depths[1] <= 10, "dyadic depth above registration")
    halves = [math.ldexp(1.0, -d - 1) for d in depths]
    centers = [(2 * i + 1) * h for i, h in zip(indices, halves, strict=True)]
    return centers, halves, depths


class _IndependentCurve:
    """Independent scalar-loop reconstruction from the registered equations."""

    def __init__(self, seed, candidate, matrix):
        self.seed, self.target = _array(seed, "seed"), _array(candidate, "candidate")
        self.matrix = _array(matrix, "matrix")
        _need(self.seed.ndim == 2 and self.seed.shape[0] == 3
              and self.seed.shape[1] >= 3 and self.seed.shape[1] % 2 == 1,
              "three Cartesian axes and odd Fourier width >=3 required")
        _need(self.target.shape == self.seed.shape, "candidate Fourier shape differs")
        _need(self.matrix.shape == (3, 3), "physical matrix must be 3 by 3")
        self.width = self.seed.shape[1]
        self.omega = [2.0 * math.pi * m for m in range(1, (self.width + 1) // 2)]
        self.prepared = False
        self.cache = {}

    def _transform(self, coefficients):
        values, errors = [], []
        for axis in range(3):
            row, uncertainty = [], []
            for mode in range(self.width):
                # Actual M.T, no ideal rotation or symmetry reduction.
                terms = [float(self.matrix[b, axis]) * float(coefficients[b, mode])
                         for b in range(3)]
                row.append(_checked(math.fsum(terms)))
                uncertainty.append(_pad(terms))
            values.append(row)
            errors.append(uncertainty)
        return values, errors

    def _B(self, values, errors, order):
        axis_bounds = []
        for a in range(3):
            terms = []
            for m, omega in enumerate(self.omega, 1):
                sine = abs(values[a][2 * m - 1]) + errors[a][2 * m - 1]
                cosine = abs(values[a][2 * m]) + errors[a][2 * m]
                terms.append(omega**order * _up(math.hypot(sine, cosine)))
            axis_bounds.append(_up(*terms))
        return _up(math.hypot(*axis_bounds))

    def _prepare(self):
        if self.prepared:
            return
        self.s, self.es = self._transform(self.seed)
        end, end_error = self._transform(self.target)
        self.d, self.ed = [], []
        for a in range(3):
            self.d.append([_checked(math.fsum((end[a][j], -self.s[a][j])))
                           for j in range(self.width)])
            self.ed.append([_up(end_error[a][j], self.es[a][j],
                                _pad((end[a][j], self.s[a][j])))
                            for j in range(self.width)])
        self.zero = [[0.0] * self.width for _ in range(3)]
        self.D1, self.D2 = self._B(self.d, self.ed, 1), self._B(self.d, self.ed, 2)
        self.prepared = True

    def _at(self, lam):
        if lam not in self.cache:
            coefficients, errors = [], []
            for a in range(3):
                coefficients.append([_checked(self.s[a][j] + lam * self.d[a][j])
                                     for j in range(self.width)])
                errors.append([_up(self.es[a][j], lam * self.ed[a][j],
                                   _pad((self.s[a][j], lam * self.d[a][j])))
                               for j in range(self.width)])
            derivatives = [self._B(coefficients, errors, k) for k in (2, 3)]
            point_errors = [_up(self._B(self.zero, errors, k),
                                _pad((self._B(coefficients, self.zero, k),)))
                            for k in (1, 2)]
            self.cache[lam] = (coefficients, derivatives, point_errors)
        return self.cache[lam]

    def values(self, path):
        (t, lam), (h, r), _ = _interval(path)
        try:
            self._prepare()
            left, right = self._at(lam - r), self._at(lam + r)
            A = max(left[1][0], right[1][0])
            J = max(left[1][1], right[1][1])
            coefficients, _, (ev, ea) = self._at(lam)
            velocity, acceleration = [], []
            for a in range(3):
                v_terms, a_terms = [], []
                for m, omega in enumerate(self.omega, 1):
                    si, co = math.sin(omega * t), math.cos(omega * t)
                    S, C = coefficients[a][2 * m - 1:2 * m + 1]
                    v_terms.append(omega * (S * co - C * si))
                    a_terms.append(-omega**2 * (S * si + C * co))
                velocity.append(_checked(math.fsum(v_terms)))
                acceleration.append(_checked(math.fsum(a_terms)))
            nv, na = math.hypot(*velocity), math.hypot(*acceleration)
            cross = [math.fsum((velocity[i] * acceleration[j],
                               -velocity[j] * acceleration[i]))
                     for i, j in ((1, 2), (2, 0), (0, 1))]
            Nc = _up(math.hypot(*cross), ev * na, ea * nv, ev * ea, _pad((nv * na,)))
            extent = _up(h * A, r * self.D1)
            v_min, v_max = _down(nv, ev, extent), _up(nv, ev, extent)
            numerator = _up(Nc, h * v_max * J, r * _up(self.D1 * A, v_max * self.D2))
            curvature = None
            if v_min > 0:
                divisor = _down(v_min**3)
                if divisor > 0:
                    curvature = _up(numerator / divisor)
            t_score = h * v_max * J + 36 * v_max**2 * h * A
            l_score = r * (self.D1 * A + v_max * self.D2) + 36 * v_max**2 * r * self.D1
            return [_checked(v_min), curvature, _checked(t_score), _checked(l_score)]
        except (OverflowError, ZeroDivisionError) as error:
            raise ArithmeticError("bound arithmetic failed") from error
        except ValueError as error:
            # fsum(+inf,-inf) and nonfinite transcendental arguments are arithmetic,
            # not schema failures; schema/path checks precede this try block.
            raise ArithmeticError("undefined bound arithmetic") from error


def _caps(value):
    _need(type(value) is dict and set(value) == set(_MAXIMA), "exact cap schema")
    for k, maximum in _MAXIMA.items():
        minimum = 1 if k == "evaluations" else 0
        _need(type(value[k]) is int and minimum <= value[k] <= maximum,
              "caps must be registered maxima or smaller test caps")


def _compare(recorded, expected):
    for index, (got, want) in enumerate(zip(recorded, expected, strict=True)):
        if want is None:
            _need(got is None, "unavailable bound must be null")
        else:
            _need(type(got) is float and math.isfinite(got), "finite float bound required")
            _need(index == 0 or got >= 0.0, "negative curvature bound or split score")
            error = abs(got - want)
            _need(error <= 1e-12 or error <= 5e-12 * abs(want),
                  "independent bound arithmetic differs")


def audit_curve(seed, candidate, matrix, report, *, deadline, clock=time.monotonic):
    """Reject malformed reports; a reproducible negative report may audit successfully."""
    _need(_number(deadline) and math.isfinite(deadline) and deadline >= 0,
          "finite nonnegative absolute deadline")
    _need(callable(clock), "monotonic clock callback required")
    last_clock = None

    def tick():
        nonlocal last_clock
        now = clock()
        _need(_number(now) and math.isfinite(now) and now >= 0,
              "finite nonnegative monotonic clock value")
        _need(last_clock is None or now >= last_clock, "monotonic clock moved backward")
        last_clock = now
        if now >= deadline:
            raise TimeoutError("independent curvature audit deadline")

    tick()
    _need(type(report) is dict and set(report) == _FIELDS, "exact curve report schema")
    _need(type(report["schema_version"]) is int and report["schema_version"] == 1
          and report["kind"] == "local-homotopy-curvature", "report identity")
    _need(all(report[k] is False for k in ("interval_arithmetic", "field_pass", "step4_pass")),
          "nonphysical padded-bound scope required")
    caps = report["caps"]
    _caps(caps)
    _need(type(report["attempted"]) is int and 0 <= report["attempted"] <= caps["evaluations"],
          "bounded integer work counter")
    _need(type(report["curvature_pass"]) is bool, "boolean curvature classification")
    reason = report["stop_reason"]
    _need(reason in ("complete", "evaluation-budget", "deadline"), "known stop reason")
    rows = report["nodes"]
    _need(type(rows) is list and 0 < len(rows) <= caps["evaluations"] + 25,
          "bounded nonempty node list")
    try:
        encoded = json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("finite JSON report required") from error
    _need(len(encoded.encode("utf-8")) + 1 <= 8 * 1024**2, "curve report size exceeded")
    model = _IndependentCurve(seed, candidate, matrix)
    frontier = [""]
    attempted = passed = unresolved = pending = 0
    stopped = False
    for row in rows:
        tick()
        _need(type(row) is list and len(row) == 6, "six-field node required")
        _need(len(json.dumps(row, separators=(",", ":"), allow_nan=False).encode()) <= 256,
              "node byte envelope exceeded")
        _need(bool(frontier), "extra node outside partition")
        path, action, *values = row
        _need(path == frontier.pop(), "canonical complete DFS node order required")
        _, _, depths = _interval(path)
        _need(depths[0] <= caps["t_depth"] and depths[1] <= caps["lambda_depth"],
              "node outside depth cap")
        if action == "pending":
            _need(reason in ("deadline", "evaluation-budget") and all(v is None for v in values),
                  "pending leaf requires resource stop and null values")
            pending += 1
            stopped = True
            continue
        _need(not stopped and attempted < caps["evaluations"], "attempt after stop/cap")
        attempted += 1
        try:
            expected = model.values(path)
        except ArithmeticError:
            _need(action == "arithmetic" and all(v is None for v in values),
                  "arithmetic failure must be an explicit null-valued leaf")
            unresolved += 1
            tick()
            continue
        _need(action != "arithmetic", "reported arithmetic failure not independently reproduced")
        _compare(values, expected)
        tick()
        if action == "deadline":
            _need(reason == "deadline", "deadline leaf requires aggregate deadline failure")
            unresolved += 1
            stopped = True
            continue
        if expected[1] is not None and 0 < expected[1] <= 12.0:
            _need(action == "pass" and values[0] > 0 and 0 < values[1] <= 12.0,
                  "independent strict curvature gate")
            passed += 1
            continue
        t_available, l_available = depths[0] < caps["t_depth"], depths[1] < caps["lambda_depth"]
        if not t_available and not l_available:
            _need(action == "depth", "exhausted depth requires unresolved leaf")
            unresolved += 1
            continue
        use_t = t_available and (not l_available or expected[2] >= expected[3])
        split = "t" if use_t else "l"
        _need(action == "split_" + split, "independent subdivision decision differs")
        frontier.extend((path + split + "1", path + split + "0"))
    _need(not frontier, "missing terminal or pending frontier")
    _need(attempted == report["attempted"], "attempted work count differs")
    if reason == "evaluation-budget":
        _need(attempted == caps["evaluations"] and pending > 0, "unjustified evaluation cap stop")
    if reason == "complete":
        _need(pending == 0 and not stopped, "completed report contains stopped work")
    classification = reason == "complete" and unresolved == 0 and pending == 0
    _need(report["curvature_pass"] is classification, "curvature aggregate differs")
    tick()
    return dict(schema_version=1, kind="local-homotopy-curvature-audit", audit_pass=True,
                curvature_pass=classification, attempted=attempted, nodes_checked=len(rows),
                passing_leaves=passed, unresolved_leaves=unresolved, pending_leaves=pending,
                interval_arithmetic=False, field_pass=False, step4_pass=False)
