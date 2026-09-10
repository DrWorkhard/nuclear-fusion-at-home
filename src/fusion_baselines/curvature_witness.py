"""Position-only local curvature estimate independent of Fourier derivatives."""

import numpy as np


def circumcircle_curvature(points):
    points = np.asarray(points, dtype=float)
    if points.shape != (3, 3) or not np.all(np.isfinite(points)):
        raise ValueError("three finite 3D points required")
    a, b = points[1] - points[0], points[2] - points[0]
    sides = np.linalg.norm([a, b, b - a], axis=1)
    if np.any(sides == 0) or not np.all(np.isfinite(sides)):
        raise ValueError("distinct finite-distance points required")
    return float(2 * np.linalg.norm(np.cross(a / sides[0], b / sides[1])) / sides[2])
