"""Scalar primal-dual certificate for a stored box LP; no optimization calls."""

import math

import numpy as np


def certificate(c, a, b, s, inequality, lower, upper):
    c, a, b, s, m, lower, upper = (
        np.asarray(v, dtype=float) for v in (c, a, b, s, inequality, lower, upper)
    )
    if (
        c.ndim != 1
        or len(c) == 0
        or b.ndim != 1
        or len(b) == 0
        or a.shape != (len(b), len(c))
        or any(v.shape != c.shape for v in (s, lower, upper))
        or m.shape != b.shape
        or not all(np.isfinite(v).all() for v in (c, a, b, s, m, lower, upper))
    ):
        raise ValueError("complete finite matching box LP certificate arrays required")

    def dot(x, y):
        return math.fsum(float(u * v) for u, v in zip(x, y, strict=True))

    ax = [dot(row, s) for row in a]
    at_m = [dot(column, m) for column in a.T]
    primal = dot(c, s)
    dual = dot(b, m) - math.fsum(map(float, lower)) + math.fsum(map(float, upper))
    scale = max(1.0, abs(primal), abs(dual))
    residuals = dict(
        primal=max(
            [0.0]
            + [
                (value - float(rhs)) / max(1.0, abs(float(rhs)))
                for value, rhs in zip(ax, b, strict=True)
            ]
            + [float(-1 - x) for x in s]
            + [float(x - 1) for x in s]
        ),
        dual_sign=max(
            [0.0] + list(map(float, m)) + list(map(float, -lower)) + list(map(float, upper))
        ),
        stationarity=max(
            abs(float(c[j]) - at_m[j] - float(lower[j]) - float(upper[j]))
            / max(1.0, abs(float(c[j])))
            for j in range(len(c))
        ),
        complementarity=max(
            [abs(float(mu) * (float(rhs) - value)) for mu, rhs, value in zip(m, b, ax, strict=True)]
            + [abs(float(mu) * (float(x) + 1)) for mu, x in zip(lower, s, strict=True)]
            + [abs(float(mu) * (1 - float(x))) for mu, x in zip(upper, s, strict=True)]
        )
        / scale,
        gap=abs(primal - dual) / scale,
    )
    if not all(math.isfinite(v) for v in (*residuals.values(), primal, dual)):
        raise ValueError("nonfinite independently summed LP certificate")
    checks = {key: value <= 1e-9 for key, value in residuals.items()}
    return dict(
        residuals=residuals,
        checks=checks,
        all_pass=all(checks.values()),
        primal_objective=primal,
        dual_objective=dual,
    )
