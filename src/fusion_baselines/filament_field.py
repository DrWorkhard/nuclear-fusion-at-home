"""Direct periodic filament Biot-Savart sum, independent of native field code."""

import numpy as np


def filament_field(points, positions, tangents, currents):
    """Uniform t in[0,1); tangents are dr/dt, currents in amperes, output tesla."""
    points, positions, tangents, currents = map(
        lambda x: np.asarray(x, dtype=float), (points, positions, tangents, currents)
    )
    if (
        points.ndim != 2
        or points.shape[1:] != (3,)
        or not len(points)
        or positions.ndim != 3
        or positions.shape[-1] != 3
        or min(positions.shape[:2]) <= 0
        or tangents.shape != positions.shape
        or currents.shape != (len(positions),)
        or not all(np.isfinite(a).all() for a in (points, positions, tangents, currents))
    ):
        raise ValueError("finite nonempty points and matched coil quadrature arrays required")
    answer = np.zeros_like(points)
    for nodes, velocity, current in zip(positions, tangents, currents, strict=True):
        delta = points[:, None, :] - nodes[None, :, :]
        distance = np.linalg.norm(delta, axis=-1)
        if np.any(distance == 0):
            raise ValueError("filament field is singular on source nodes")
        answer += (
            1e-7
            * current
            * np.mean(np.cross(velocity[None, :, :], delta) / distance[:, :, None] ** 3, axis=1)
        )
    if not np.isfinite(answer).all():
        raise ValueError("nonfinite filament field")
    return answer
