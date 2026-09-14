"""Independent trapped-interval enumeration and Gaussian action quadrature."""

import numpy as np

NODES, WEIGHTS = np.polynomial.legendre.leggauss(64)


def independent_actions(trace, bstar):
    b, length, phi = (np.asarray(trace[k]) for k in ("B", "length", "phi"))
    if (
        b.ndim != 2
        or length.shape != b.shape
        or len(phi) != b.shape[0]
        or not all(np.isfinite(a).all() for a in (b, length, phi))
        or np.any(b <= 0)
        or np.any(np.diff(length, axis=0) <= 0)
        or np.any(np.diff(phi) <= 0)
        or abs(phi[0]) > 1e-14
        or abs(phi[-1] - 2 * np.pi) > 1e-12
        or not np.isfinite(bstar)
        or bstar <= 0
    ):
        raise ValueError("finite positive complete independent trace required")
    actions, edges = [], []
    for col in range(b.shape[1]):
        q = 1 - b[:, col] / bstar
        inside = q > 0
        if inside[0] or inside[-1]:
            raise ValueError("censored well in independent enumeration")
        starts = np.flatnonzero(~inside[:-1] & inside[1:])
        stops = np.flatnonzero(inside[:-1] & ~inside[1:])
        if len(starts) != 2 or len(stops) != 2 or np.any(starts >= stops):
            raise ValueError("two matched period wells required")
        row, limits = [], []
        for family, (i, j) in enumerate(zip(starts, stops, strict=True)):
            left = length[i, col] - q[i] * (length[i + 1, col] - length[i, col]) / (q[i + 1] - q[i])
            right = length[j, col] - q[j] * (length[j + 1, col] - length[j, col]) / (
                q[j + 1] - q[j]
            )
            angles = np.interp([left, right], length[:, col], phi)
            if angles[0] < family * np.pi - 1e-12 or angles[1] > (family + 1) * np.pi + 1e-12:
                raise ValueError("independent period identity failed")
            knots = np.r_[left, length[i + 1 : j + 1, col], right]
            widths = np.diff(knots) / 2
            mid = (knots[1:] + knots[:-1]) / 2
            points = mid[:, None] + widths[:, None] * NODES
            values = np.interp(points.ravel(), length[:, col], b[:, col]).reshape(points.shape)
            integrand = 1 - values / bstar
            if integrand.min() < -1e-12:
                raise ValueError("forbidden interval in independent integral")
            row.append(float(np.sum(widths * (np.sqrt(np.maximum(0, integrand)) @ WEIGHTS))))
            limits.append([float(left), float(right)])
        actions.append(row)
        edges.append(limits)
    a = np.asarray(actions)
    if np.any(a <= 0) or not np.isfinite(a).all():
        raise ValueError("positive independent action required")
    means = np.sum(a, axis=0) / len(a)
    deviations = a - means
    variance = np.einsum("ij,ij->j", deviations, deviations) / (len(a) * means**2)
    return dict(
        actions=a,
        bounds=np.asarray(edges),
        means=means,
        variance=variance,
        score=float(np.sum(variance) / 2),
    )
