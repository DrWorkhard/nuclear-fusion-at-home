"""Restricted geometric well continuation and empirical radial-sign screens."""

import numpy as np


def match_intervals(anchor, candidate, window):
    """Match all anchors uniquely; reject untracked central-window wells."""
    anchor = np.asarray(anchor, dtype=float)
    candidate = np.asarray(candidate, dtype=float)
    window = np.asarray(window, dtype=float)
    if window.shape != (2,) or not np.all(np.isfinite(window)) or window[1] <= window[0]:
        raise ValueError("invalid central window")
    for intervals in (anchor, candidate):
        if (intervals.ndim != 2 or intervals.shape[1] != 2 or not len(intervals)
                or not np.all(np.isfinite(intervals))
                or np.any(intervals[:, 1] <= intervals[:, 0])):
            raise ValueError("invalid or empty well intervals")
    if np.any((anchor.mean(axis=1) < window[0]) | (anchor.mean(axis=1) > window[1])):
        raise ValueError("anchor outside central window")
    overlap = np.minimum(anchor[:, None, 1], candidate[None, :, 1]) - np.maximum(
        anchor[:, None, 0], candidate[None, :, 0])
    widths = anchor[:, 1] - anchor[:, 0]
    short = np.minimum(widths[:, None], np.diff(candidate, axis=1).ravel()[None, :])
    displacement = np.max(np.abs(anchor[:, None, :] - candidate[None, :, :]), axis=2)
    edges = (overlap > 0.5 * short) & (displacement < 0.25 * widths[:, None])
    if np.any(edges.sum(axis=1) != 1) or np.any(edges.sum(axis=0) > 1):
        raise ValueError("ambiguous or missing well continuation")
    indices = np.argmax(edges, axis=1)
    central = (candidate.mean(axis=1) >= window[0]) & (candidate.mean(axis=1) <= window[1])
    if not set(np.flatnonzero(central)).issubset(set(indices)):
        raise ValueError("unmatched central well birth")
    return indices


def radial_sign_screen(actions, anchor_action, steps=(0.04, 0.02, 0.01)):
    """actions[level,step,minus/plus]; empirical allowances are not rigorous bounds."""
    actions = np.asarray(actions, dtype=float)
    steps = np.asarray(steps, dtype=float)
    if (actions.shape != (3, 3, 2) or not np.all(np.isfinite(actions))
            or np.any(actions <= 0) or not np.isfinite(anchor_action) or anchor_action <= 0
            or steps.shape != (3,) or not np.all(np.isfinite(steps))
            or np.any(steps <= 0) or np.any(np.diff(steps) >= 0)):
        raise ValueError("invalid action stencil")
    derivatives = (actions[:, :, 1] - actions[:, :, 0]) / (2 * steps[None, :])
    normalized = derivatives / anchor_action
    estimate = float(normalized[-1, -1])
    trace = float(abs(normalized[-1, -1] - normalized[-2, -1]))
    radial = float(abs(normalized[-1, -1] - normalized[-1, -2]))
    tolerance = max(0.01, 0.05 * abs(estimate))
    stable = trace <= tolerance and radial <= tolerance
    allowance = 4 * (trace + radial)
    classification = "unresolved"
    if stable and estimate + allowance < 0:
        classification = "negative"
    elif stable and estimate - allowance > 0:
        classification = "positive"
    return {
        "derivatives": derivatives.tolist(),
        "normalized_derivatives": normalized.tolist(),
        "estimate": estimate, "trace_change": trace, "radial_change": radial,
        "tolerance": tolerance, "empirical_allowance": allowance,
        "refinement_pass": stable, "sign": classification,
    }
