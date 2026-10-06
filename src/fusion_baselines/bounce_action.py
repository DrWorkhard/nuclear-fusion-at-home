"""Reduced one-way bounce actions for a piecewise-linear positive B(l)."""

from dataclasses import asdict, dataclass

import numpy as np


@dataclass
class Well:
    left: float
    right: float
    action: float
    complete: bool

    def record(self):
        return asdict(self)


def linear_segment_action(length: float, q_left: float, q_right: float) -> float:
    """Exact integral of sqrt(q), for nonnegative linear q on a segment."""
    if not np.all(np.isfinite([length, q_left, q_right])) or min(length, q_left, q_right) < 0:
        raise ValueError("length and endpoint radicands must be finite and nonnegative")
    a, b = np.sqrt(q_left), np.sqrt(q_right)
    if a + b == 0:
        return 0.0
    return float(length * (2 / 3) * (q_left + a * b + q_right) / (a + b))


def bounce_wells(length, field, bounce_field: float) -> list[Well]:
    """Return every connected trapped interval, including boundary-censored wells.

    B is linear between samples. Exact threshold contacts separate intervals.
    Samples at a boundary equal to Bstar are valid turning points; samples below
    Bstar at that boundary identify an incomplete well.
    """
    length = np.asarray(length, dtype=float)
    field = np.asarray(field, dtype=float)
    if length.ndim != 1 or length.shape != field.shape or length.size < 2:
        raise ValueError("length and field must be equal one-dimensional arrays of >=2 samples")
    if not np.all(np.isfinite(length)) or not np.all(np.isfinite(field)):
        raise ValueError("nonfinite trace")
    if np.any(np.diff(length) <= 0) or np.any(field <= 0):
        raise ValueError("length must increase strictly and field must be positive")
    if not np.isfinite(bounce_field) or bounce_field <= 0:
        raise ValueError("bounce field must be finite and positive")
    q = 1 - field / bounce_field
    wells: list[Well] = []
    for index, (qa, qb) in enumerate(zip(q[:-1], q[1:], strict=True)):
        if max(qa, qb) <= 0:
            continue
        left, right = length[index : index + 2]
        if qa < 0:
            left += (right - left) * (-qa) / (qb - qa)
        elif qb < 0:
            right = left + (right - left) * qa / (qa - qb)
        action = linear_segment_action(right - left, max(qa, 0), max(qb, 0))
        censored_left = index == 0 and qa > 0
        censored_right = index == len(q) - 2 and qb > 0
        if wells and qa > 0 and wells[-1].right == left:
            wells[-1].right = float(right)
            wells[-1].action += action
            wells[-1].complete &= not censored_right
        else:
            wells.append(
                Well(float(left), float(right), action, not (censored_left or censored_right))
            )
    return wells


def action_envelope(wells_by_alpha: list[list[Well]]) -> dict:
    """Conservative envelope across wells, retaining missing-alpha coverage."""
    if not wells_by_alpha:
        raise ValueError("at least one field line is required")
    complete = [[well for well in wells if well.complete] for wells in wells_by_alpha]
    actions = [well.action for wells in complete for well in wells]
    coverage = sum(bool(wells) for wells in complete) / len(complete)
    result = {
        "complete_wells_per_alpha": [len(wells) for wells in complete],
        "censored_well_count": sum(not w.complete for wells in wells_by_alpha for w in wells),
        "complete_alpha_coverage": coverage,
        "envelope": None,
        "action_min": min(actions) if actions else None,
        "action_max": max(actions) if actions else None,
    }
    if actions and coverage == 1:
        result["envelope"] = float((max(actions) - min(actions)) / np.mean(actions))
    return result
