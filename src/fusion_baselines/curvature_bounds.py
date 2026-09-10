"""Analytic interval-wide curvature bounds for regular XYZ Fourier curves.

Evaluated in ordinary floating point, not directed-rounding interval arithmetic.
"""

import numpy as np

PAD = 1e-12


def validate_coefficients(coefficients):
    c = np.asarray(coefficients, dtype=float)
    if (c.ndim != 2 or c.shape[0] != 3 or c.shape[1] < 3 or c.shape[1] % 2 != 1
            or not np.all(np.isfinite(c))):
        raise ValueError("finite 3 by (2*order+1) Fourier coefficients required")
    return c


def derivatives(coefficients, parameter):
    """Return r',r'',r''' at arbitrary periodic coordinates, independent of SIMSOPT."""
    c = validate_coefficients(coefficients)
    t = np.asarray(parameter, dtype=float)
    if t.ndim != 1 or not len(t) or not np.all(np.isfinite(t)):
        raise ValueError("nonempty finite parameter vector required")
    omega = 2 * np.pi * np.arange(1, (c.shape[1] + 1) // 2)
    phase = omega[:, None] * np.mod(t, 1)
    sine, cosine = np.sin(phase), np.cos(phase)
    result = []
    for k in (1, 2, 3):
        a, b = (cosine, -sine) if k == 1 else (-sine, -cosine) if k == 2 else (-cosine, sine)
        result.append(((c[:, 1::2] * omega**k) @ a + (c[:, 2::2] * omega**k) @ b).T)
    return np.asarray(result)


def curvature_enclosure(coefficients, resolution):
    c = validate_coefficients(coefficients)
    if type(resolution) is not int or resolution < 4:
        raise ValueError("integer resolution >=4 required")
    n = resolution
    def norm(values):
        return np.linalg.norm(values, axis=-1)
    v, a, j = derivatives(c, np.arange(2 * n) / (2 * n))
    speeds = norm(v)
    if (not np.all(np.isfinite([v, a, j])) or not np.all(np.isfinite(speeds))
            or np.any(speeds <= 0)):
        return {"resolution": n, "regularity_resolved": False,
                "maximum_lower_bound": None, "maximum_upper_bound": None,
                "reason": "nonfinite derivatives or stationary sample"}
    sampled = norm(np.cross(v, a)) / speeds**3
    if not np.all(np.isfinite(sampled)):
        return {"resolution": n, "regularity_resolved": False,
                "maximum_lower_bound": None, "maximum_upper_bound": None,
                "reason": "nonfinite sampled curvature"}
    lower = float(sampled.max())
    record = {"resolution": n, "maximum_lower_bound": lower,
              "witness_parameter": float(np.argmax(sampled) / (2 * n)),
              "maximum_upper_bound": None, "regularity_resolved": False}
    omega = 2 * np.pi * np.arange(1, (c.shape[1] + 1) // 2)
    snap = float(np.sum((norm(c[:, 1::2].T) + norm(c[:, 2::2].T)) * omega**4)) * (1 + PAD)
    h = 1 / (2 * n)
    vm, am, jm = v[1::2], a[1::2], j[1::2]
    J = (norm(jm) + snap * h) * (1 + PAD)
    A = (norm(am) + J * h) * (1 + PAD)
    V = (norm(vm) + A * h) * (1 + PAD)
    minimum = (norm(vm) - A * h) * (1 - PAD)
    record["minimum_speed_lower_bound"] = float(minimum.min())
    if np.any(minimum <= 0) or not np.all(np.isfinite([J, A, V, minimum])):
        record["reason"] = "regularity not certified on all intervals"
        return record
    U = (norm(np.cross(vm, am)) + V * J * h) * (1 + PAD)
    Q = (A * J + V * snap) * (1 + PAD)
    P = (norm(np.cross(vm, jm)) + Q * h) * (1 + PAD)
    W1 = 2 * (np.abs(np.sum(vm * am, axis=1)) + (A*A + V*J)*h) * (1 + PAD)
    W2 = 2 * (A*A + V*J) * (1 + PAD)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        H = (2*(P*P + U*Q)/minimum**6 + 12*U*P*W1/minimum**8
             + 12*U*U*W1*W1/minimum**10 + 3*U*U*W2/minimum**8) * (1 + PAD)
        endpoints = sampled[::2]**2 * (1 + PAD)
        interval_upper = np.maximum(endpoints, np.roll(endpoints, -1)) + H / (8 * n*n)
    if not np.all(np.isfinite(interval_upper)) or not np.isfinite(lower):
        record["reason"] = "nonfinite curvature/error bound"
        return record
    upper = float(np.sqrt(interval_upper.max()) * (1 + PAD))
    if upper < lower:
        raise ValueError("computed upper bound below sampled witness")
    record.update(regularity_resolved=True, maximum_upper_bound=upper,
                  maximum_squared_interpolation_allowance=float((H / (8*n*n)).max()))
    return record


def classify_enclosure(enclosure, limit):
    if not np.isfinite(limit) or limit <= 0:
        raise ValueError("positive finite curvature limit required")
    lower, upper = enclosure["maximum_lower_bound"], enclosure["maximum_upper_bound"]
    if lower is not None and lower > limit:
        return "fail"
    if enclosure["regularity_resolved"] and upper is not None and upper <= limit:
        return "pass"
    return "unresolved"
