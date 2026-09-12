"""Independent reduced QR solution and scalar-sum current residual checks."""

import math

import numpy as np


def qr_fit(z0, matrix):
    z0, matrix = np.asarray(z0, dtype=float), np.asarray(matrix, dtype=float)
    if (z0.ndim != 1 or len(z0) < 3 or matrix.shape != (len(z0), 3)
            or not np.isfinite(z0).all() or not np.isfinite(matrix).all()):
        raise ValueError("finite matching independent current LS arrays required")
    q, r = np.linalg.qr(matrix, mode="reduced")
    largest = float(abs(r).max())
    if largest == 0 or np.any(abs(np.diag(r)) <= 1e-12*largest):
        raise ValueError("independent triangular system has insufficient rank")
    rhs = -np.array([math.fsum(float(a*b) for a, b in zip(v, z0, strict=True)) for v in q.T])
    # Explicit three-step back substitution, not the producer SVD or a second least-squares call.
    delta = np.zeros(3)
    for i in (2, 1, 0):
        delta[i] = (rhs[i]-math.fsum(float(r[i, j]*delta[j]) for j in range(i+1, 3)))/r[i, i]
    residual = np.array([float(z)+math.fsum(float(a*b) for a, b in zip(row, delta, strict=True))
                         for z, row in zip(z0, matrix, strict=True)])
    norm_r = math.sqrt(math.fsum(float(v*v) for v in residual))
    norm_a = math.sqrt(math.fsum(float(v*v) for v in matrix.ravel()))
    gradient = [math.fsum(float(a*b) for a, b in zip(col, residual, strict=True))
                for col in matrix.T]
    normal_error = math.sqrt(math.fsum(v*v for v in gradient))/(norm_a*max(norm_r, 1e-30))
    return dict(delta=delta, residual=residual, normal_error=normal_error,
                objective_after=.5*math.fsum(float(v*v) for v in residual),
                triangular_diagonal=np.diag(r).copy())
