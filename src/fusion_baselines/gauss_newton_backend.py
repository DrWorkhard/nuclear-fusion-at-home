"""Attach an explicitly qualified raw-flux GN matrix to each full direct bundle."""

import numpy as np


class GaussNewtonBackend:
    def __init__(self, direct, spatial, flux_scale=1e-6):
        if not np.isfinite(flux_scale) or flux_scale <= 0:
            raise ValueError("positive finite flux scale required")
        self.direct, self.spatial, self.flux_scale = direct, spatial, flux_scale
        self.last_x = self.last_hessian = None
        self.records = []
        self.spatial_attempts = 0
        self.failed_bundle = self.failed_metrics = None

    def evaluate(self, x):
        self.last_x = self.last_hessian = None
        self.failed_bundle = self.failed_metrics = None
        x = np.asarray(x, dtype=float).copy()
        values, jacobian, metrics = self.direct(x)
        self.spatial_attempts += 1
        z, dz = [np.asarray(a, dtype=float) for a in self.spatial()]
        values, jacobian = np.asarray(values, dtype=float), np.asarray(jacobian, dtype=float)
        if (x.ndim != 1 or x.size == 0 or z.ndim != 1 or z.size == 0
                or dz.shape != (len(z), len(x)) or values.ndim != 1 or values.size < 2
                or jacobian.shape != (len(values), len(x))
                or not all(np.all(np.isfinite(a)) for a in (x, values, jacobian, z, dz))):
            raise ValueError("invalid full direct/spatial bundle")
        phi = float(z @ z / (2*self.flux_scale))
        gradient = dz.T @ z / self.flux_scale
        field_error = abs(phi-values[0]) / max(1e-300, abs(values[0]))
        gradient_error = float(np.max(
            np.abs(gradient-jacobian[0]) / np.maximum(1, np.abs(jacobian[0]))))
        hessian = dz.T @ dz / self.flux_scale
        if (not np.all(np.isfinite(hessian)) or not np.isfinite(field_error)
                or field_error > 1e-10 or gradient_error > 1e-10):
            self.failed_bundle = dict(x=x.copy(), values=values.copy(),
                                      jacobian=jacobian.copy(), z=z.copy(), dz=dz.copy())
            self.failed_metrics = dict(field_relative_error=float(field_error),
                                       gradient_normalized_error=gradient_error)
            raise ValueError(f"GN field/gradient identity failed: {self.failed_metrics}")
        self.records.append({"field_relative_error": float(field_error),
                             "gradient_normalized_error": gradient_error})
        self.last_x, self.last_hessian = x.copy(), hessian.copy()
        return values, jacobian, {**metrics, "gauss_newton_identity": self.records[-1].copy()}

    def hessian_for(self, x):
        if self.last_x is None or not np.array_equal(x, self.last_x):
            raise ValueError("request the complete bundle at this point before its GN matrix")
        return self.last_hessian.copy()
