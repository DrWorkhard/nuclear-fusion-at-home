"""Explicit solver/physical coordinate conversion with an exact affine pullback."""

import numpy as np


class AffineCoordinates:
    def __init__(self, origin, scale):
        self._origin = np.asarray(origin, dtype=float).copy()
        if (self._origin.ndim != 1 or not self._origin.size
                or not np.all(np.isfinite(self._origin))
                or np.ndim(scale) != 0 or not np.isfinite(scale) or scale <= 0):
            raise ValueError("finite origin and positive scalar scale required")
        self.scale = float(scale)

    def _vector(self, vector):
        vector = np.asarray(vector, dtype=float)
        if vector.shape != self._origin.shape or not np.all(np.isfinite(vector)):
            raise ValueError("coordinate/gradient shape or finiteness mismatch")
        return vector

    def physical(self, solver):
        physical = self._origin + self.scale * self._vector(solver)
        return self._vector(physical).copy()

    def solver(self, physical):
        solver = (self._vector(physical) - self._origin) / self.scale
        return self._vector(solver).copy()

    def gradient(self, physical_gradient):
        return self._vector(self.scale * self._vector(physical_gradient)).copy()
