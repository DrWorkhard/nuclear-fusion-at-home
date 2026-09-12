"""Algebraic action-drift coordinate control, not an absolute orbit integrator."""

import numpy as np


def phase_drift(action_gradient, phase_gradient, *, slope=0.0):
    """For alpha=beta+c(s-s0), transform both covectors and contract k with u.

    Inputs use component order (s, alpha). The dimensional m*v/(q*psi_a)
    factor and bounce time are deliberately not supplied or inferred.
    """
    action = np.asarray(action_gradient, dtype=float)
    phase = np.asarray(phase_gradient, dtype=float)
    if action.shape != (2,) or phase.shape != (2,):
        raise ValueError("two components (s, alpha) required")
    if not (np.isfinite(action).all() and np.isfinite(phase).all() and np.isfinite(slope)):
        raise ValueError("finite gradients and slope required")
    a_s, a_alpha = action
    k_s, k_alpha = phase
    transformed_action = np.array([a_s + slope * a_alpha, a_alpha])
    transformed_phase = np.array([k_s + slope * k_alpha, k_alpha])
    drift = np.array([transformed_action[1], -transformed_action[0]])
    return dict(
        action_gradient=transformed_action,
        phase_gradient=transformed_phase,
        drift=drift,
        contraction=float(transformed_phase @ drift),
    )
