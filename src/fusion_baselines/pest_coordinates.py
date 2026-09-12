"""Fixed-origin straight-field-angle inversion; not a global bijectivity proof."""

import numpy as np


def coefficients(m, n, lam):
    m, n, lam = (np.asarray(v, dtype=float) for v in (m, n, lam))
    if (m.ndim != 1 or not len(m) or n.shape != m.shape or lam.shape != m.shape
            or not all(np.isfinite(v).all() for v in (m, n, lam))
            or not np.array_equal(m, np.rint(m)) or not np.array_equal(n, np.rint(n))
            or np.any(m < 0) or len(np.unique(np.column_stack((m, n)), axis=0)) != len(m)):
        raise ValueError("finite coefficients with unique integer physical modes required")
    return m, n, lam


def angles(theta, phi):
    theta, phi = np.broadcast_arrays(np.asarray(theta, dtype=float), np.asarray(phi, dtype=float))
    if theta.size == 0 or not np.isfinite(theta).all() or not np.isfinite(phi).all():
        raise ValueError("nonempty finite broadcastable angles required")
    return theta, phi


def lambda_series(theta, phi, m, n, lam):
    m, n, lam = coefficients(m, n, lam)
    theta, phi = angles(theta, phi)
    phase = m[:, None] * theta.ravel() - n[:, None] * phi.ravel()
    cosine = np.cos(phase)
    return tuple(v.reshape(theta.shape) for v in
                 (lam @ np.sin(phase), (m * lam) @ cosine, (-n * lam) @ cosine))


def invert_theta(u, phi, m, n, lam):
    """At most50 clipped Newton updates, retaining failed/singular sampled points."""
    m, n, lam = coefficients(m, n, lam)
    u, phi = angles(u, phi)
    theta = u.copy()
    folded = np.zeros(u.shape, dtype=bool)
    iterations = np.zeros(u.shape, dtype=int)
    for step in range(51):
        shift, lt, lp = lambda_series(theta, phi, m, n, lam)
        residual, denominator = theta + shift - u, 1 + lt
        folded |= denominator <= 1e-8
        passed = (~folded) & (abs(residual) <= 1e-12)
        active = (~folded) & (~passed)
        if not np.any(active) or step == 50:
            break
        delta = np.zeros(u.shape)
        np.divide(residual, denominator, out=delta, where=active)
        theta -= np.clip(delta, -0.5, 0.5)
        iterations += active
    return dict(theta=theta, phi=phi, u=u, lam=shift, lt=lt, lp=lp,
                residual=residual, denominator=denominator, passed=passed,
                encountered_nonpositive_jacobian=folded, iterations=iterations)


def transform_tangents(et, ep, lt, lp):
    et, ep = np.asarray(et, dtype=float), np.asarray(ep, dtype=float)
    lt, lp = np.asarray(lt, dtype=float), np.asarray(lp, dtype=float)
    if (et.shape != ep.shape or et.ndim < 1 or et.shape[-1] != 3
            or lt.shape != et.shape[:-1] or lp.shape != lt.shape
            or not all(np.isfinite(v).all() for v in (et, ep, lt, lp))
            or np.any(1 + lt <= 1e-8)):
        raise ValueError("matched finite tangents and positive sampled Jacobian required")
    eu = et / (1 + lt)[..., None]
    return eu, ep - eu * lp[..., None]
