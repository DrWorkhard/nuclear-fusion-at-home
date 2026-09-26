"""Bounded saved-field residual arithmetic, not fields or feasible coil designs.

The caller owns provenance, matched grid identities, saved-metric comparisons,
deadlines and publication. No project arrays, native model or independent checker
are imported here. Inputs are copied; results contain only plain JSON scalars.
"""

import math

import numpy as np

MAX_POINTS = 16384
ATOL, RTOL = 1e-12, 5e-10


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _types(value):
    if isinstance(value, (list, tuple)):
        for item in value:
            _types(item)
    elif isinstance(value, np.ndarray):
        _need(value.dtype.kind in "iuf", "real numeric array without boolean aliases")
    else:
        _need(
            isinstance(value, (int, float, np.integer, np.floating))
            and not isinstance(value, (bool, np.bool_)),
            "real numbers without boolean, string or complex aliases",
        )


def _array(value, shape=None):
    _types(value)
    raw = np.asarray(value)
    _need(raw.dtype.kind in "iuf", "real numeric input")
    if shape is not None:
        _need(raw.shape == shape, "matched field, normal and weight shapes")
    else:
        _need(raw.ndim == 2 and raw.shape[1] == 3, "Cartesian field matrix required")
        _need(1 <= len(raw) <= MAX_POINTS, "one to 16384 field points required")
    result = np.array(raw, dtype=np.float64, copy=True, order="C")
    _need(np.isfinite(result).all(), "finite binary64 input required")
    return result


def _scalar(value):
    value = float(value)
    _need(math.isfinite(value), "finite residual arithmetic required")
    return value


def _dot(left, right, weights):
    return _scalar(np.sum(weights * left * right))


def _identity(error, scale, label):
    error, scale = _scalar(error), _scalar(scale)
    _need(scale >= 0 and abs(error) <= ATOL + RTOL * scale, label + " identity failed")


def _fit(control, proposal, weights, *, normal):
    difference = proposal - control
    a = _dot(control, control, weights)
    b = _dot(proposal, proposal, weights)
    c = _dot(control, difference, weights)
    d = _dot(difference, difference, weights)
    cn, pn, dn = math.sqrt(a), math.sqrt(b), math.sqrt(d)
    resolved = dn > ATOL * max(cn, pn, 1.0)
    result = dict(
        control_norm=cn,
        proposal_norm=pn,
        delta_norm=pn - cn,
        secant_norm=dn,
        projection_resolved=resolved,
        alignment=None,
        aligned_fraction=None,
        alpha=None,
        beta=None,
        fit_norm=None,
        fit_fraction=None,
        fit_limit_ratio=None,
        orthogonality=None,
        pythagoras_error=None,
    )
    if not resolved:
        return result
    alpha = _scalar(-c / d)
    fitted = control + alpha * difference
    fitted_squared = _dot(fitted, fitted, weights)
    fitted_norm = math.sqrt(fitted_squared)
    orthogonality = _dot(fitted, difference, weights)
    pythagoras_error = _scalar(abs(a - (fitted_squared + alpha * alpha * d)))
    _identity(orthogonality, fitted_norm * dn, "orthogonality")
    _identity(pythagoras_error, a, "Pythagoras")
    alignment = _scalar(-(c / cn) / dn) if cn > 0 else None
    result.update(
        alignment=alignment,
        aligned_fraction=_scalar(alignment * alignment) if cn > 0 else None,
        alpha=alpha,
        beta=_scalar(alpha - 1),
        fit_norm=fitted_norm,
        fit_fraction=_scalar(fitted_norm / cn) if cn > 0 else None,
        fit_limit_ratio=_scalar(fitted_norm / 1e-4) if normal else None,
        orthogonality=orthogonality,
        pythagoras_error=pythagoras_error,
    )
    return result


def _split(bn_control, bn_proposal, m_control, m_proposal, weights):
    control, proposal = bn_control / m_control, bn_proposal / m_proposal
    difference = proposal - control
    numerator = (bn_proposal - bn_control) / m_control
    denominator = bn_proposal * (1 / m_proposal - 1 / m_control)
    vector_error = abs(difference - (numerator + denominator))
    vector_scale = abs(difference) + abs(numerator) + abs(denominator)
    _need(
        np.isfinite(vector_error).all()
        and np.isfinite(vector_scale).all()
        and np.all(vector_error <= ATOL + RTOL * vector_scale),
        "numerator/denominator vector identity failed",
    )
    a, b = _dot(control, control, weights), _dot(proposal, proposal, weights)
    u, v = _dot(numerator, numerator, weights), _dot(denominator, denominator, weights)
    cross = _scalar(2 * _dot(numerator, denominator, weights))
    cu = _scalar(2 * _dot(control, numerator, weights))
    cv = _scalar(2 * _dot(control, denominator, weights))
    change = _scalar(b - a)
    energy_error = _scalar(abs(change - (cu + cv + u + v + cross)))
    _identity(energy_error, a + b + u + v, "squared-error decomposition")
    return dict(
        numerator_norm_squared=u,
        denominator_norm_squared=v,
        cross_term=cross,
        control_numerator_term=cu,
        control_denominator_term=cv,
        delta_squared_norm=change,
        energy_identity_error=energy_error,
        vector_identity_error=_scalar(vector_error.max()),
    )


def analyze_pair(control_B, proposal_B, normals, weights, b2_scale):
    """Analyze signed residuals of one matched pair; no source/grid admission.

    Cartesian fields/normals have shape (N,3), weights (N,), 1<=N<=16384.
    Normals and positive weights are normalized privately. All scalar changes
    mean proposal minus control. Alpha is control-origin, beta is alpha minus1.
    Nearzero secants have null projection values; objective fit_limit_ratio is
    always null. Invalid inputs, nonfinite arithmetic and failed identities raise
    ValueError. Input mutation, feasible extrapolation and native work are absent.
    """
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            control = _array(control_B)
            proposal = _array(proposal_B, control.shape)
            normal = _array(normals, control.shape)
            weight = _array(weights, (len(control),))
            _types(b2_scale)
            scale = np.asarray(b2_scale)
            _need(scale.shape == () and scale.dtype.kind in "iuf", "real scalar B2 scale")
            b2 = _scalar(scale)
            _need(b2 > 0 and np.all(weight > 0), "positive B2 scale and weights required")
            weight /= _scalar(np.sum(weight))
            _need(np.all(weight > 0), "positive normalized weights required")
            normal_size = np.linalg.norm(normal, axis=1)
            cm, pm = np.linalg.norm(control, axis=1), np.linalg.norm(proposal, axis=1)
            _need(
                np.isfinite([normal_size, cm, pm]).all()
                and np.all(normal_size > 0)
                and np.all(cm > 0)
                and np.all(pm > 0),
                "nonzero finite normals and magnetic fields required",
            )
            normal /= normal_size[:, None]
            cbn, pbn = np.sum(control * normal, axis=1), np.sum(proposal * normal, axis=1)
            normal_fit = _fit(cbn / cm, pbn / pm, weight, normal=True)
            objective_fit = _fit(cbn / math.sqrt(b2), pbn / math.sqrt(b2), weight, normal=False)
            metrics = {}
            for name, magnitude, side in (("control", cm, "control"), ("proposal", pm, "proposal")):
                metrics[name] = dict(
                    normal_rms=normal_fit[side + "_norm"],
                    JN=_scalar(objective_fit[side + "_norm"] ** 2 / 2),
                    boundary_B_rms=math.sqrt(_dot(magnitude, magnitude, weight)),
                )
            metrics["deltas"] = {
                key: _scalar(metrics["proposal"][key] - metrics["control"][key])
                for key in metrics["control"]
            }
            return dict(
                metrics=metrics,
                residuals=dict(normal=normal_fit, objective=objective_fit),
                split=_split(cbn, pbn, cm, pm, weight),
            )
    except (FloatingPointError, OverflowError, ZeroDivisionError) as error:
        raise ValueError("nonfinite or unrepresentable residual arithmetic") from error
