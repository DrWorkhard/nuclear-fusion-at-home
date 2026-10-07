"""Step 3 period actions on actual coil-field lines launched from target surfaces.

The action kernels below are unchanged from plasma_design.py at 56181dc.
Labels s/alpha are TARGET launch labels, not demonstrated realized flux labels.
A passing diagnostic never establishes confinement or physical benefit transfer.
"""

import numpy as np
from scipy.integrate import solve_ivp

from fusion_baselines.bounce_action import bounce_wells

SURFACES = (0.1, 0.25, 0.5, 0.75, 0.9)
HOLD_PITCHES = (0.03, 0.1, 0.3, 0.5, 0.7, 0.9, 0.97)


class IncompleteActionDomain(ValueError):
    """Missing/extra/censored wells or a crossed registered period family."""


def bounce_field(q):
    if q not in HOLD_PITCHES:
        raise ValueError("registered invariant required")
    return 1.0082953902491054 + q * (1.5870966275564338 - 1.0082953902491054)

def action_statistics(actions):
    a = np.asarray(actions, dtype=float)
    if (
        a.ndim != 2
        or a.shape[1] != 2
        or a.shape[0] < 4
        or not np.isfinite(a).all()
        or np.any(a <= 0)
    ):
        raise ValueError("positive actions on every alpha and both period families required")
    mean = a.mean(axis=0)
    variance = (((a - mean) / mean) ** 2).mean(axis=0)
    envelope = (a.max(axis=0) - a.min(axis=0)) / mean
    return dict(
        mean=mean.tolist(),
        variance=variance.tolist(),
        envelope=envelope.tolist(),
        score=float(variance.mean()),
    )

def period_actions(trace, q):
    """Reject missing/extra/censored or period-crossing wells, rather than drop them."""
    b, length = np.asarray(trace["B"]), np.asarray(trace["length"])
    phi, alpha = np.asarray(trace["phi"]), np.asarray(trace["alpha"])
    if b.shape != length.shape or b.shape != (len(phi), len(alpha)):
        raise ValueError("complete matching trace arrays required")
    if (
        not np.isfinite(phi).all()
        or not np.isfinite(alpha).all()
        or np.any(np.diff(phi) <= 0)
        or abs(phi[0]) > 1e-14
        or abs(phi[-1] - 2 * np.pi) > 1e-12
    ):
        raise ValueError("two complete nfp2 field periods required")
    actions, bounds, phi_bounds = [], [], []
    for j in range(len(alpha)):
        wells = bounce_wells(length[:, j], b[:, j], bounce_field(q))
        if len(wells) != 2 or any(not w.complete for w in wells):
            raise IncompleteActionDomain("exactly two uncensored wells required on every line")
        edges = [[w.left, w.right] for w in wells]
        angles = np.interp(np.asarray(edges).ravel(), length[:, j], phi).reshape(2, 2)
        if any(
            lo < p * np.pi - 1e-12 or hi > (p + 1) * np.pi + 1e-12
            for p, (lo, hi) in enumerate(angles)
        ):
            raise IncompleteActionDomain("well family crosses its registered field period")
        actions.append([w.action for w in wells])
        bounds.append(edges)
        phi_bounds.append(angles.tolist())
    return dict(
        actions=actions,
        bounds=bounds,
        phi_bounds=phi_bounds,
        bounce_field=bounce_field(q),
        **action_statistics(actions),
    )


def trace_coils(field, target, s, ideal, guard=lambda: None, rtol=1e-9, atol=1e-11):
    """Integrate dR/dphi, dZ/dphi and dl/dphi in the direct, frozen-current field.

    The target PEST theta at phi=0 defines identical label conventions in both
    arms. No target path or target iota is substituted for the coil trajectory.
    """
    phi, alpha = ideal["phi"], ideal["alpha"]
    count = len(alpha)
    radius, z = target.rz(s, ideal["theta"][0], np.zeros(count))
    initial = np.concatenate((radius, z, np.zeros(count)))

    def rhs(angle, state):
        guard()
        radius, z = state[:count], state[count:2*count]
        if not np.isfinite(state).all() or np.any(radius <= 0):
            raise ValueError("nonfinite or nonpositive-R coil trajectory")
        c, sine = np.cos(angle), np.sin(angle)
        points = np.column_stack((radius*c, radius*sine, z))
        field.set_points(np.ascontiguousarray(points))
        B = field.B().copy()
        guard()
        radial, toroidal = B[:, 0]*c+B[:, 1]*sine, -B[:, 0]*sine+B[:, 1]*c
        magnitude = np.linalg.norm(B, axis=1)
        if not np.isfinite(B).all() or np.any(abs(toroidal) <= 1e-6*magnitude):
            raise ValueError("toroidal field too small for phi-parametrized trace")
        return np.concatenate((radius*radial/toroidal, radius*B[:, 2]/toroidal,
                               radius*magnitude/abs(toroidal)))

    solved = solve_ivp(rhs, (float(phi[0]), float(phi[-1])), initial, method="DOP853",
                       t_eval=phi, rtol=rtol, atol=atol, max_step=2*np.pi/200)
    if not solved.success or solved.y.shape != (3*count, len(phi)):
        raise ValueError("incomplete coil trace: "+solved.message)
    radius, z, length = np.split(solved.y.T, 3, axis=1)
    xyz = np.stack((radius*np.cos(phi[:, None]), radius*np.sin(phi[:, None]), z), axis=-1)
    fields = []
    for first in range(0, xyz.size//3, 128):
        guard()
        field.set_points(np.ascontiguousarray(xyz.reshape(-1, 3)[first:first+128]))
        fields.append(field.B().copy())
        guard()
    B = np.linalg.norm(np.concatenate(fields), axis=1).reshape(radius.shape)
    return dict(B=B, length=length, phi=phi.copy(), alpha=alpha.copy(), xyz=xyz,
                evaluations=np.array(solved.nfev))


def measure(trace):
    """Retain every failed pitch; incomplete domains never receive an aggregate score."""
    rows, errors = [], []
    for q in HOLD_PITCHES:
        try:
            rows.append(dict(q=q, **period_actions(trace, q)))
        except ValueError as exc:
            errors.append(dict(q=q, error=str(exc)))
    return dict(cells=rows, errors=errors,
                score=None if errors else float(np.mean([r["score"] for r in rows])))
