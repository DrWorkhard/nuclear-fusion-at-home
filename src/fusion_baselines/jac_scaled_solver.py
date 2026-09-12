"""Explicit one-option TRF variant; never modify the legacy solver or its globals."""

from scipy.optimize import least_squares

from fusion_baselines.staged_auglag import LS_OPTIONS

EFFECTIVE_OPTIONS = {**LS_OPTIONS, "x_scale": "jac"}


def jac_scaled_least_squares(fun, x0, *, jac, **options):
    if options != LS_OPTIONS:
        raise ValueError("the complete original TRF options are required")
    return least_squares(fun, x0, jac=jac, **EFFECTIVE_OPTIONS)
