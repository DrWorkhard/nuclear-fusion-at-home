"""Audit the separately declared composite gate; never turn an old FD failure green."""

import numpy as np


def composite_gradient_gate(forward_errors, qualification, diagnostic_sha256):
    errors = np.asarray(forward_errors, dtype=float)
    if errors.shape != (138,) or not np.all(np.isfinite(errors)) or np.any(errors < 0):
        raise ValueError("138 finite nonnegative forward errors required")
    pair_pass = (
        qualification.get("status") == "completed"
        and qualification.get("all_pass") is True
        and qualification.get("diagnostic", {}).get("sha256") == diagnostic_sha256
    )
    states = qualification.get("states", [])
    pair_pass &= len(states) == 2 and {s.get("name") for s in states} == {"original", "selected119"}
    for state in states:
        real_errors = np.asarray(state.get("real_value_errors", []), dtype=float)
        pair_pass &= (
            real_errors.shape == (120,)
            and np.all(np.isfinite(real_errors))
            and np.all(real_errors >= 0)
            and np.all(real_errors <= 1e-10)
        )
        pair_pass &= state.get("checks", {}).get("zero_current_columns") is True
        directions = state.get("directions", [])
        pair_pass &= len(directions) == 2 and {d.get("seed") for d in directions} == {47, 48}
        for direction in directions:
            analytic = np.asarray(direction.get("analytic", []), dtype=float)
            steps = direction.get("steps", [])
            valid = analytic.shape == (120,) and np.all(np.isfinite(analytic))
            pair_pass &= valid and [s.get("h") for s in steps] == [1e-12, 1e-20, 1e-28]
            first = None
            for step in steps:
                measured = np.asarray(step.get("directional_derivative", []), dtype=float)
                if not valid or measured.shape != (120,) or not np.all(np.isfinite(measured)):
                    pair_pass = False
                    continue
                first = measured.copy() if first is None else first
                discrepancy = np.abs(measured - analytic) / np.maximum(1.0, np.abs(analytic))
                stability = np.abs(measured - first) / np.maximum(1.0, np.abs(first))
                pair_pass &= np.max(discrepancy) <= 1e-9 and np.max(stability) <= 1e-10
    nonpair = np.r_[errors[:6], errors[126:]]
    nonpair_pass = bool(np.max(nonpair) <= 1e-6)
    return {
        "original_all_row_forward_difference_pass": bool(np.max(errors) <= 1e-6),
        "nonpair_forward_difference_pass": nonpair_pass,
        "independent_pair_pass": bool(pair_pass),
        "accepted": nonpair_pass and bool(pair_pass),
    }
