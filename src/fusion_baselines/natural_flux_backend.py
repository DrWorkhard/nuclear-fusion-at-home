"""Retain qualified native z/batched Dz for staged least-squares composition."""

import numpy as np

from fusion_baselines.gauss_newton_backend import GaussNewtonBackend
from fusion_baselines.natural_auglag import augmented_residual


class NaturalFluxBackend:
    def __init__(self, direct, spatial, native_residual, *, flux_scale=1e-6):
        self.last_x = self.bundle = self.z = self.dz = None
        self.compositions, self.flux_scale = 0, flux_scale

        def captured_spatial():
            z, dz = spatial()
            self.dz = np.asarray(dz, dtype=float).copy()
            return z, dz

        def captured_native():
            self.z = np.asarray(native_residual(), dtype=float).copy()
            return self.z

        self.gn = GaussNewtonBackend(
            direct, captured_spatial, flux_scale, native_residual=captured_native
        )

    def evaluate(self, x):
        self.last_x = self.bundle = self.z = self.dz = None
        values, jacobian, metrics = self.gn.evaluate(x)
        self.last_x = np.asarray(x, dtype=float).copy()
        self.bundle = values.copy(), jacobian.copy()
        return values, jacobian, metrics

    def residual_for(self, x, multipliers, rho):
        if self.last_x is None or not np.array_equal(x, self.last_x):
            raise ValueError("complete matching physical bundle required")
        self.compositions += 1
        values, jacobian = self.bundle
        return augmented_residual(
            self.z, self.dz, values[1:], jacobian[1:], multipliers, rho, flux_scale=self.flux_scale
        )
