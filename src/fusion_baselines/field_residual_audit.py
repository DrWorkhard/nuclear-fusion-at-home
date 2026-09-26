"""Independent stdlib reconstruction of the registered saved-field diagnosis.

This module imports neither the NumPy producer nor the original metric code.
It checks one paired boundary grid, not the caller's file/state/source identity,
physical feasibility, a coil-class lower bound, or future optimizer progress.
"""

import math
import numbers

_REL = 5e-10
_ABS = 1e-12
_METRICS = {"normal_rms", "JN", "boundary_B_rms"}
_RESIDUAL = {
    "control_norm", "proposal_norm", "delta_norm", "secant_norm", "projection_resolved",
    "alignment", "aligned_fraction", "alpha", "beta", "fit_norm", "fit_fraction",
    "fit_limit_ratio", "orthogonality", "pythagoras_error",
}
_PROJECTION = {
    "alignment", "aligned_fraction", "alpha", "beta", "fit_norm", "fit_fraction",
    "fit_limit_ratio", "orthogonality", "pythagoras_error",
}
_SPLIT = {
    "numerator_norm_squared", "denominator_norm_squared", "cross_term",
    "control_numerator_term", "control_denominator_term", "delta_squared_norm",
    "energy_identity_error", "vector_identity_error",
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _finite(value):
    if not math.isfinite(value):
        raise ArithmeticError("nonfinite diagnostic arithmetic")
    return value


def _number(value, label):
    _need(isinstance(value, numbers.Real) and not isinstance(value, bool),
          f"{label}: real non-boolean scalar required")
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"{label}: finite binary64 value required") from error
    _need(math.isfinite(result), f"{label}: finite value required")
    return result


def _sequence(value, label):
    _need(not isinstance(value, (str, bytes, bytearray, dict)),
          f"{label}: numeric sequence required")
    try:
        result = list(value)
    except TypeError as error:
        raise ValueError(f"{label}: numeric sequence required") from error
    _need(len(result) > 0, f"{label}: nonempty sequence required")
    return result


def _vectors(value, label):
    result = []
    rows = _sequence(value, label)
    _need(len(rows) <= 16384, f"{label}: at most 16384 boundary rows required")
    for index, row in enumerate(rows):
        row = _sequence(row, f"{label}[{index}]")
        _need(len(row) == 3, f"{label}[{index}]: exactly three components required")
        result.append(tuple(_number(v, f"{label}[{index}]") for v in row))
    return result


def _sum(terms):
    try:
        return _finite(math.fsum(_finite(v) for v in terms))
    except OverflowError as error:
        raise ArithmeticError("diagnostic summation overflow") from error


def _dot(left, right):
    return _sum(a * b for a, b in zip(left, right, strict=True))


def _norm(values):
    return _finite(math.hypot(*values))


def _square(value):
    return _finite(value * value)


def _identity(error, scale, label):
    limit = _finite(_ABS + _REL * _finite(scale))
    if abs(_finite(error)) > limit:
        raise ArithmeticError(f"{label}: registered arithmetic identity failed")


def _residual(control, proposal, root_weights, *, normal):
    qc = [_finite(w * x) for w, x in zip(root_weights, control, strict=True)]
    qp = [_finite(w * x) for w, x in zip(root_weights, proposal, strict=True)]
    # Difference first, then weighting, to retain the protocol's scalar d=rP-rC.
    d = [_finite(y - x) for x, y in zip(control, proposal, strict=True)]
    qd = [_finite(w * x) for w, x in zip(root_weights, d, strict=True)]
    nc, np, nd = _norm(qc), _norm(qp), _norm(qd)
    a, dd = _square(nc), _square(nd)
    result = {
        "control_norm": nc, "proposal_norm": np, "delta_norm": _finite(np - nc),
        "secant_norm": nd, "projection_resolved": nd > 1e-12 * max(nc, np, 1.0),
        **dict.fromkeys(_PROJECTION),
    }
    if not result["projection_resolved"]:
        return result

    cross = _dot(qc, qd)
    alpha = _finite(-cross / dd)
    fit = [_finite(_sum((c, _finite(alpha * step))))
           for c, step in zip(control, d, strict=True)]
    qfit = [_finite(w * x) for w, x in zip(root_weights, fit, strict=True)]
    nf = _norm(qfit)
    orthogonality = _dot(qfit, qd)
    removed = _finite(_square(alpha) * dd)
    pythagoras = abs(_sum((a, -_square(nf), -removed)))
    _identity(orthogonality, _finite(nf * nd), "orthogonality")
    _identity(pythagoras, a, "Pythagoras")
    result.update({
        "alpha": alpha, "beta": _finite(alpha - 1.0), "fit_norm": nf,
        "fit_limit_ratio": _finite(nf / 1e-4) if normal else None,
        "orthogonality": orthogonality, "pythagoras_error": pythagoras,
    })
    if nc > 0:
        # The two divisions avoid an unnecessary overflow in norm products.
        alignment = _finite((-cross / nc) / nd)
        result.update({"alignment": alignment, "aligned_fraction": _square(alignment),
                       "fit_fraction": _finite(nf / nc)})
    return result


def _split(control, proposal, bn_c, bn_p, magnitude_c, magnitude_p, root_weights):
    u, v, d = [], [], []
    max_error = 0.0
    for c, p, bc, bp, mc, mp in zip(
            control, proposal, bn_c, bn_p, magnitude_c, magnitude_p, strict=True):
        numerator = _finite(_finite(bp - bc) / mc)
        denominator = _finite(bp * _finite(_finite(1.0 / mp) - _finite(1.0 / mc)))
        change = _finite(p - c)
        error = abs(_sum((change, -numerator, -denominator)))
        _identity(error, _sum((abs(change), abs(numerator), abs(denominator))),
                  "numerator/denominator vector")
        max_error = max(max_error, error)
        u.append(numerator)
        v.append(denominator)
        d.append(change)

    def weighted(values):
        return [_finite(w * x) for w, x in zip(root_weights, values, strict=True)]

    qu, qv, qd, qc, qp = (weighted(values) for values in (u, v, d, control, proposal))
    u2, v2, d2 = (_square(_norm(values)) for values in (qu, qv, qd))
    cross = _finite(2.0 * _dot(qu, qv))
    cu, cv = _finite(2.0 * _dot(qc, qu)), _finite(2.0 * _dot(qc, qv))
    a, b = _square(_norm(qc)), _square(_norm(qp))
    energy_error = abs(_sum((b, -a, -cu, -cv, -u2, -v2, -cross)))
    scale = _sum((a, b, u2, v2))
    _identity(energy_error, scale, "normalized energy")
    _identity(_sum((d2, -u2, -v2, -cross)), scale, "squared secant decomposition")
    return {
        "numerator_norm_squared": u2, "denominator_norm_squared": v2,
        "cross_term": cross, "control_numerator_term": cu,
        "control_denominator_term": cv, "delta_squared_norm": _finite(b - a),
        "energy_identity_error": energy_error, "vector_identity_error": max_error,
    }


def analyze_pair(control_B, proposal_B, normals, weights, b2_scale):
    """Independently reconstruct one matched grid using scalar loops and fsum.

    Caller must bind the arrays to immutable original files and verify paired
    points/normals/weights are bit-identical. Inputs are copied; no I/O or native
    operations occur. Schema faults raise ValueError; failed finite arithmetic
    or registered numerical identities raise ArithmeticError.
    """
    bc = _vectors(control_B, "control_B")
    bp = _vectors(proposal_B, "proposal_B")
    n = _vectors(normals, "normals")
    w = [_number(value, "weights") for value in _sequence(weights, "weights")]
    _need(len(bc) == len(bp) == len(n) == len(w), "boundary lengths differ")
    _need(all(value > 0 for value in w), "strictly positive weights required")
    b2 = _number(b2_scale, "b2_scale")
    _need(b2 > 0, "strictly positive b2_scale required")
    total = _sum(w)
    normalized = [_finite(value / total) for value in w]
    _need(all(value > 0 for value in normalized), "normalized weights underflowed")
    root_weights = [math.sqrt(value) for value in normalized]
    root_b2 = math.sqrt(b2)
    magnitudes, normal_components, residuals, metrics = [], [], [], []
    for fields in (bc, bp):
        magnitude, component, normal, objective = [], [], [], []
        for field, raw_normal in zip(fields, n, strict=True):
            mag, normal_mag = _norm(field), _norm(raw_normal)
            _need(mag > 0 and normal_mag > 0, "nonzero field and normal required")
            unit = [_finite(value / normal_mag) for value in raw_normal]
            bn = _dot(field, unit)
            magnitude.append(mag)
            component.append(bn)
            normal.append(_finite(bn / mag))
            objective.append(_finite(bn / root_b2))
        magnitudes.append(magnitude)
        normal_components.append(component)
        residuals.append((normal, objective))
        norms = [_norm([_finite(x * weight) for x, weight in
                        zip(values, root_weights, strict=True)])
                 for values in (normal, objective, magnitude)]
        metrics.append({"normal_rms": norms[0], "JN": _finite(0.5 * _square(norms[1])),
                        "boundary_B_rms": norms[2]})

    result = {
        "metrics": {"control": metrics[0], "proposal": metrics[1],
                    "deltas": {key: _finite(metrics[1][key] - metrics[0][key])
                               for key in _METRICS}},
        "residuals": {
            label: _residual(residuals[0][index], residuals[1][index], root_weights,
                             normal=index == 0)
            for index, label in enumerate(("normal", "objective"))
        },
        "split": _split(residuals[0][0], residuals[1][0], *normal_components,
                         *magnitudes, root_weights),
    }
    _schema(result)
    return result


def _keys(value, keys, label):
    _need(type(value) is dict and set(value) == keys, f"{label}: exact schema required")


def _json_number(value, label):
    _need(type(value) in (int, float), f"{label}: finite JSON number required")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    _need(finite, f"{label}: finite JSON number required")


def _schema(report):
    _keys(report, {"metrics", "residuals", "split"}, "report")
    _keys(report["metrics"], {"control", "proposal", "deltas"}, "metrics")
    for row in report["metrics"].values():
        _keys(row, _METRICS, "metrics row")
        for value in row.values():
            _json_number(value, "metric")
    _keys(report["split"], _SPLIT, "split")
    for value in report["split"].values():
        _json_number(value, "split scalar")
    _keys(report["residuals"], {"normal", "objective"}, "residuals")
    for kind, row in report["residuals"].items():
        _keys(row, _RESIDUAL, "residual row")
        _need(type(row["projection_resolved"]) is bool, "projection status must be boolean")
        for key in _RESIDUAL - _PROJECTION - {"projection_resolved"}:
            _json_number(row[key], key)
        for key in _PROJECTION:
            nullable = (not row["projection_resolved"]
                        or (kind == "objective" and key == "fit_limit_ratio")
                        or (row["control_norm"] == 0
                            and key in {"alignment", "aligned_fraction", "fit_fraction"}))
            if nullable:
                _need(row[key] is None, f"{key}: registered null required")
            else:
                _json_number(row[key], key)


def compare(actual, expected):
    """Require exact structure/status/nulls and registered scalar agreement.

    ``expected`` should be the independently reconstructed report from this
    module, not another copy of a claimed producer result. Returns exactly True
    or raises ValueError; it is not a physical-admission decision.
    """
    _schema(actual)
    _schema(expected)

    def visit(left, right, path):
        if type(right) is dict:
            for key in right:
                visit(left[key], right[key], f"{path}.{key}")
        elif right is None or type(right) is bool:
            _need(left is right, f"{path}: exact null/status mismatch")
        else:
            # OR, not a sum of absolute and relative tolerances.
            difference = abs(left - right)
            _need(difference <= _ABS or difference <= _REL * max(abs(left), abs(right)),
                  f"{path}: independent scalar mismatch")

    visit(actual, expected, "report")
    return True
