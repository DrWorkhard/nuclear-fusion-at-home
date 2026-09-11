"""Counted, identity-checked residual representations for a controlled pilot."""

import hashlib
import time

import numpy as np

from .local_field_jacobian import local_field_jacobian
from .spatial_flux import lift_flux, normal_weights, spatial_flux


class ResidualRepresentation:
    def __init__(self, backend, spatial=False):
        self.base = backend
        self.global_objective = backend.global_objective
        self.objectives = backend.objectives
        self.spatial = spatial
        self.common_records = []
        self.work = {"common_bundles": 0, "extra_single_point_B_calls": 0,
                     "extra_single_point_VJP_calls": 0, "extra_full_field_requests": 0,
                     "common_seconds": 0.0, "spatial_seconds": 0.0}
        self.max_merit_error = self.max_gradient_error = 0.0
        flux = self.objectives[0]
        if spatial:
            if flux is not self.global_objective or flux.definition != "quadratic flux":
                raise ValueError("require the qualified quadratic-flux objective")
            if np.any(flux.target):
                raise ValueError("nonzero target not qualified")
            self.normal = flux.surface.normal().copy()
            self.points = flux.surface.gamma().reshape(-1, 3).copy()
            self.weights = normal_weights(self.normal)

    def __call__(self, x):
        self.work["common_bundles"] += 1
        started = time.monotonic()
        values, jac = self.base(x)
        self.work["common_seconds"] += time.monotonic()-started
        self.common_records.append({"x_sha256": hashlib.sha256(x.tobytes()).hexdigest(),
                                    "values": values.tolist(), "merit": float(values@values/2)})
        if not self.spatial:
            return values, jac
        started = time.monotonic()
        flux = self.global_objective
        field = flux.field
        field.set_points(self.points)
        self.work["extra_full_field_requests"] += 1
        z = spatial_flux(field.B().reshape(self.normal.shape), self.normal)
        if z@z/2 >= flux.threshold:
            # Precharge planned work; any exception terminates the pilot, never a retry.
            self.work["extra_single_point_B_calls"] += len(z)
            self.work["extra_single_point_VJP_calls"] += len(z)
            dz = local_field_jacobian(field, flux, self.points, self.weights)
        else:
            dz = np.zeros((len(z), len(x)))
        r, dr = lift_flux(z, dz, scale=float(self.base.scales[0]), threshold=flux.threshold)
        lifted_values, lifted_jac = np.concatenate((r, values[1:])), np.vstack((dr, jac[1:]))
        merit_error = abs(lifted_values@lifted_values-values@values)/max(
            np.finfo(float).tiny, float(values@values))
        gradient = jac.T@values
        gradient_error = float(np.max(np.abs(lifted_jac.T@lifted_values-gradient)))/max(
            1.0, float(np.max(np.abs(gradient))))
        self.max_merit_error = max(self.max_merit_error, float(merit_error))
        self.max_gradient_error = max(self.max_gradient_error, gradient_error)
        self.work["spatial_seconds"] += time.monotonic()-started
        if merit_error > 1e-10 or gradient_error > 1e-10:
            raise ValueError("spatial representation changed the scalar merit or gradient")
        return lifted_values, lifted_jac
