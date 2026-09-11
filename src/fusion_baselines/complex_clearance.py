"""Independent holomorphic Fourier/pair-distance values for complex-step checks."""

from itertools import combinations

import numpy as np


def fourier_positions(coefficients, resolution):
    c = np.asarray(coefficients)
    if (
        c.ndim != 3
        or c.shape[1] != 3
        or c.shape[2] < 3
        or c.shape[2] % 2 != 1
        or not np.all(np.isfinite(c))
        or type(resolution) is not int
        or resolution < 3
    ):
        raise ValueError("finite (coils,3,2*order+1) coefficients and integer grid required")
    phase = (
        2
        * np.pi
        * np.arange(resolution)[:, None]
        / resolution
        * np.arange(1, (c.shape[2] + 1) // 2)
    )
    basis = np.ones((resolution, c.shape[2]))
    basis[:, 1::2], basis[:, 2::2] = np.sin(phase), np.cos(phase)
    return (c @ basis.T).transpose(0, 2, 1)


def clearance_rows(coefficients, scale, *, resolution=200, anchors=None):
    positions = fourier_positions(coefficients, resolution)
    if len(positions) < 2 or not np.isscalar(scale) or not np.isfinite(scale) or scale <= 0:
        raise ValueError("at least two curves and positive scale required")
    pairs = list(combinations(range(len(positions)), 2))
    if anchors is not None:
        anchors = np.asarray(anchors, dtype=float)
        if anchors.shape != (len(pairs),) or not np.all(np.isfinite(anchors)):
            raise ValueError("finite real anchor for each pair required")
    values, used = [], []
    for index, (i, j) in enumerate(pairs):
        r = positions[i][:, None, :] - positions[j][None, :, :]
        squared = scale**2 * np.sum(r * r, axis=-1)  # No conjugation: holomorphic continuation.
        anchor = float(np.real(squared).min()) if anchors is None else anchors[index]
        total = np.sum(np.exp(-512.0 * (squared - anchor)))
        bound = anchor - np.log(total) / 512.0
        values.append(bound / 1.1**2 - 1)
        used.append(anchor)
    values = np.asarray(values)
    if not np.all(np.isfinite(values)):
        raise ValueError("nonfinite complex clearance value")
    return values, np.asarray(used)
