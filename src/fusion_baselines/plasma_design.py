"""Registered four-mode plasma design and period-resolved action objective."""

import copy

import numpy as np

from fusion_baselines.bounce_action import bounce_wells
from fusion_baselines.qi_resolution import effective_input, mode_map

MODES = (("rbc", 1, 1), ("zbs", 1, 1), ("rbc", 2, 0), ("zbs", 2, 0))
SURFACES = (0.25, 0.5, 0.75)
PITCHES = (0.1, 0.3, 0.5, 0.7, 0.9)
HOLD_SURFACES = (0.1, 0.25, 0.5, 0.75, 0.9)
HOLD_PITCHES = (0.03, 0.1, 0.3, 0.5, 0.7, 0.9, 0.97)
LEVELS = ((1601, 32, 0.0), (3201, 32, 0.0), (3201, 64, 0.0), (3201, 64, np.pi / 64))


def bounce_field(q):
    if q not in HOLD_PITCHES:
        raise ValueError("registered invariant required")
    return 1.0082953902491054 + q * (1.5870966275564338 - 1.0082953902491054)


def design_input(original, x, ns):
    x = np.asarray(x, dtype=float)
    if x.shape != (4,) or not np.isfinite(x).all() or np.max(abs(x)) > 1e-3:
        raise ValueError("four bounded finite named design changes required")
    if ns not in (201, 401) or original["nfp"] != 2 or original["pres_scale"] != 0:
        raise ValueError("registered two-period vacuum source required")
    result = copy.deepcopy(original)
    if mode_map(original["rbc"])[0, 0] != 1:
        raise ValueError("fixed unit major-radius coefficient required")
    for (kind, m, n), value in zip(MODES, x, strict=True):
        entries = [r for r in result[kind] if (r["m"], r["n"]) == (m, n)]
        if len(entries) != 1:
            raise ValueError("unique registered mode required")
        entries[0]["value"] += float(value)
    return effective_input(result, ns, 2)


def poll_points(center, step):
    center = np.asarray(center, dtype=float)
    if center.shape != (4,) or not np.isfinite(center).all() or step not in (1e-4, 2e-4):
        raise ValueError("registered coordinate poll required")
    return [center + sign * step * np.eye(4)[j] for j in range(4) for sign in (1, -1)]


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
            raise ValueError("exactly two uncensored wells required on every line")
        edges = [[w.left, w.right] for w in wells]
        angles = np.interp(np.asarray(edges).ravel(), length[:, j], phi).reshape(2, 2)
        if any(
            lo < p * np.pi - 1e-12 or hi > (p + 1) * np.pi + 1e-12
            for p, (lo, hi) in enumerate(angles)
        ):
            raise ValueError("well family crosses its registered field period")
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


def choose(records):
    eligible = [i for i, r in enumerate(records) if r["eligible"]]
    if not eligible:
        raise ValueError("no qualified search state")
    return min(eligible, key=lambda i: (records[i]["measurement"]["score"], i))


def improvement_checks(reference, candidate, uncertainty, training_ref, training_candidate):
    values = np.array([reference, candidate, uncertainty, training_ref, training_candidate])
    valid = bool(
        np.isfinite(values).all() and np.all(values >= 0) and reference > 0 and training_ref > 0
    )
    return dict(
        finite=valid,
        training=valid and training_candidate <= 0.995 * training_ref,
        holdout=valid and candidate <= 0.995 * reference,
        resolved=valid and reference - candidate > 5 * uncertainty,
    )
