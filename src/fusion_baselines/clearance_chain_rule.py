"""Independent real Fourier-loop and weighted chain-rule check; no complex/native calls."""

from itertools import combinations

import numpy as np


def loop_positions(coefficients, resolution=200):
    c = np.asarray(coefficients, dtype=float)
    if (c.ndim != 3 or c.shape[1] != 3 or c.shape[2] < 3 or c.shape[2] % 2 != 1
            or not np.isfinite(c).all() or type(resolution) is not int or resolution < 3):
        raise ValueError("finite Fourier coefficients and integer grid required")
    angles = 2 * np.pi * np.arange(resolution) / resolution
    positions = np.repeat(c[:, None, :, 0], resolution, axis=1)
    for mode in range(1, (c.shape[2]+1)//2):
        positions += c[:, None, :, 2*mode-1] * np.sin(mode*angles)[None, :, None]
        positions += c[:, None, :, 2*mode] * np.cos(mode*angles)[None, :, None]
    return positions


def chain_rule_rows(coefficients, directions, scale, *, resolution=200):
    c, directions = np.asarray(coefficients), np.asarray(directions)
    if (directions.ndim != 4 or directions.shape[1:] != c.shape or len(directions) == 0
            or not np.isscalar(scale) or not np.isfinite(scale) or scale <= 0):
        raise ValueError("matching direction arrays and positive scale required")
    points = loop_positions(c, resolution)
    delta = np.array([loop_positions(d, resolution) for d in directions])
    if len(points) < 2:
        raise ValueError("two or more coils required")
    values, derivatives, anchors = [], [], []
    for i, j in combinations(range(len(points)), 2):
        r = points[i, :, None, :] - points[j, None, :, :]
        # Explicit component arithmetic instead of production's complex sum.
        q = scale*scale * (r[:, :, 0]**2 + r[:, :, 1]**2 + r[:, :, 2]**2)
        anchor = float(q.min())
        weights = np.exp(-512 * (q-anchor))
        denominator = float(weights.sum())
        values.append((anchor - np.log(denominator)/512) / 1.1**2 - 1)
        anchors.append(anchor)
        row = []
        for dp in delta:
            dr = dp[i, :, None, :] - dp[j, None, :, :]
            dq = 2 * scale*scale * (r[:, :, 0]*dr[:, :, 0] + r[:, :, 1]*dr[:, :, 1]
                                    + r[:, :, 2]*dr[:, :, 2])
            row.append(float(np.sum(weights*dq) / denominator / 1.1**2))
        derivatives.append(row)
    result = np.asarray(values), np.asarray(derivatives).T, np.asarray(anchors)
    if not all(np.isfinite(v).all() for v in result):
        raise ValueError("finite chain-rule results required")
    return result
