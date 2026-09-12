"""Empirical chain-rule check for a radially shifted field-line label."""

import numpy as np


def gauge_chain_rule(base_derivative, shifted_derivative, alpha_actions, anchor_action, slope):
    actions = np.asarray(alpha_actions, dtype=float)
    if (
        actions.shape != (2, 2)
        or not np.isfinite(actions).all()
        or np.any(actions <= 0)
        or not np.isfinite([base_derivative, shifted_derivative, anchor_action, slope]).all()
        or anchor_action <= 0
        or slope not in (-1, 1)
    ):
        raise ValueError("finite positive action stencil and fixed nonzero gauge slope required")
    derivatives = (actions[:, 1] - actions[:, 0]) / (2 * np.array([0.01, 0.005]))
    predicted = base_derivative + slope * derivatives[-1]
    error = abs(shifted_derivative - predicted) / anchor_action
    allowance = max(0.01, 0.05 * abs(shifted_derivative / anchor_action))
    alpha_change = abs(derivatives[-1] - derivatives[0]) / anchor_action
    alpha_allowance = max(0.01, 0.05 * abs(derivatives[-1] / anchor_action))
    return dict(
        alpha_derivatives=derivatives.tolist(),
        predicted_derivative=float(predicted),
        normalized_chain_error=float(error),
        chain_allowance=allowance,
        alpha_change=float(alpha_change),
        alpha_allowance=alpha_allowance,
        chain_pass=bool(error <= allowance),
        alpha_refinement_pass=bool(alpha_change <= alpha_allowance),
    )
