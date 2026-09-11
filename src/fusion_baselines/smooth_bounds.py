"""Conservative smooth extrema of finite samples, with exact derivative weights."""

import numpy as np


def smooth_extremum(values, beta, *, upper):
    x = np.asarray(values, dtype=float)
    if (
        x.size == 0
        or not np.all(np.isfinite(x))
        or isinstance(beta, bool)
        or not np.isfinite(beta)
        or beta <= 0
        or type(upper) is not bool
    ):
        raise ValueError("finite nonempty samples, positive beta and boolean direction required")
    signed = x if upper else -x
    maximum = float(np.max(signed))
    exponentials = np.exp(beta * (signed - maximum))
    total = float(np.sum(exponentials))
    bound = maximum + np.log(total) / beta
    return float(bound if upper else -bound), exponentials / total


def soft_squared_clearance(first, second, beta=512.0, scale=1.0):
    a, b = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    if (
        a.ndim != 2
        or b.ndim != 2
        or a.shape[1] != 3
        or b.shape[1] != 3
        or len(a) == 0
        or len(b) == 0
        or not np.all(np.isfinite(a))
        or not np.all(np.isfinite(b))
        or not np.isfinite(scale)
        or scale <= 0
    ):
        raise ValueError("finite nonempty (n,3) point sets and positive scale required")
    difference = a[:, None, :] - b[None, :, :]
    squared = scale * scale * np.sum(difference * difference, axis=2)
    bound, weights = smooth_extremum(squared, beta, upper=False)
    weighted = 2 * scale * scale * weights[:, :, None] * difference
    return bound, weighted.sum(axis=1), -weighted.sum(axis=0)
