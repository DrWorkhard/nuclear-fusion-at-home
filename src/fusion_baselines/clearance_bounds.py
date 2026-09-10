"""Conservative continuum lower bound from complete periodic coil-pair sampling."""

import numpy as np


def periodic_pair_clearance_bound(sampled_minimum, resolution, speed, acceleration, separation):
    values = np.asarray([sampled_minimum, speed, acceleration, separation], dtype=float)
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("distances and derivative bounds must be finite and nonnegative")
    if type(resolution) is not int or resolution < 2:
        raise ValueError("periodic grid resolution must be an integer >=2")
    if sampled_minimum > separation:
        raise ValueError("sampled minimum exceeds declared global separation bound")
    second_derivative = 2 * speed**2 + 2 * separation * acceleration
    error = second_derivative / (4 * resolution**2)
    return {
        "squared_distance_interpolation_error_bound": float(error),
        "continuous_distance_lower_bound": float(np.sqrt(max(0.0, sampled_minimum**2 - error))),
    }
