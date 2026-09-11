"""Raw flux and conservative finite-sample geometric inequalities, not penalties."""

from itertools import combinations

import numpy as np

from fusion_baselines.smooth_bounds import smooth_extremum, soft_squared_clearance
from fusion_baselines.spatial_flux import normal_weights, spatial_flux


def map_full_gradient(global_names, full_names, free_names, gradient):
    """Map explicit full coefficient derivatives, omitting only declared fixed DOFs."""
    gradient = np.asarray(gradient, dtype=float)
    if (
        len(set(global_names)) != len(global_names)
        or len(set(full_names)) != len(full_names)
        or len(set(free_names)) != len(free_names)
        or not set(free_names) <= set(full_names)
        or not set(free_names) <= set(global_names)
        or gradient.shape != (len(full_names),)
        or not np.all(np.isfinite(gradient))
    ):
        raise ValueError("invalid full/free/global derivative mapping")
    result = np.zeros(len(global_names))
    indices = {name: i for i, name in enumerate(global_names)}
    free = set(free_names)
    for i, name in enumerate(full_names):
        if name in free:
            result[indices[name]] = gradient[i]
    return result


class DirectConstraintBackend:
    """Fixed LPQA qualification setup: one raw objective, 137 g(x)>=0 rows.

    All work counters count requests, including requests served by native caches.
    No linking-number derivative or continuous-geometry admission is implied.
    """

    def __init__(self, context, full_surface, flux_scale=1e-6):
        from simsopt.geo import ArclengthVariation, CurveLength, MeanSquaredCurvature

        self.context, self.global_objective = context, context.Jf
        self.field, self.surface = context.Jf.field, context.Jf.surface
        self.names = list(context.Jf.dof_names)
        self.curves = [c.curve for c in self.field.coils]
        self.bases = self.curves[:4]
        self.fine = list(context.c_list[4].refined)
        self.normal = self.surface.normal().copy()
        self.points = self.surface.gamma().reshape(-1, 3).copy()
        self.weights = normal_weights(self.normal)
        self.plasma_points = full_surface.gamma().reshape(-1, 3).copy()
        self.scale, self.flux_scale = float(context.th["a0"]), float(flux_scale)
        self.msc_limit = float(context.th["msc_threshold"])
        self.arc_limit = float(context.th["arclength_variation_threshold"])
        if (
            len(self.curves) != 16
            or len(self.fine) != 4
            or len(self.names) != 207
            or len(set(self.names)) != len(self.names)
            or self.normal.shape != (32, 32, 3)
            or self.plasma_points.shape != (4096, 3)
            or context.Jf.definition != "quadratic flux"
            or np.any(context.Jf.target)
            or getattr(self.field, "psc_array", None) is not None
            or not np.all(np.isfinite(self.plasma_points))
            or not np.all(
                np.isfinite([self.scale, self.flux_scale, self.msc_limit, self.arc_limit])
            )
            or min(self.scale, self.flux_scale, self.msc_limit, self.arc_limit) <= 0
        ):
            raise ValueError("unsupported direct-constraint physical setup")
        for curve in self.curves + self.fine:
            q = np.asarray(curve.quadpoints)
            expected = 1600 if curve in self.fine else 200
            if len(q) != expected or not np.allclose(
                q, np.arange(expected) / expected, rtol=0, atol=1e-15
            ):
                raise ValueError("unexpected geometry quadrature")
        for base, fine in zip(self.bases, self.fine, strict=True):
            if base.dofs is not fine.dofs or list(base.local_full_dof_names) != list(
                fine.local_full_dof_names
            ):
                raise ValueError("refined curve DOFs/column order not shared with base")
        self.native = [
            cls(c)
            for cls in (CurveLength, MeanSquaredCurvature, ArclengthVariation)
            for c in self.bases
        ]
        indices = {name: i for i, name in enumerate(self.names)}
        self.native_indices = [
            np.array([indices[n] for n in obj.dof_names], dtype=int) for obj in self.native
        ]
        self.pairs = list(combinations(range(16), 2))
        self.labels = (
            ["raw_flux_scaled", "length"]
            + [f"curvature-{i}" for i in range(4)]
            + [f"coil-pair-{i}-{j}" for i, j in self.pairs]
            + [f"plasma-{i}" for i in range(4)]
            + [f"msc-{i}" for i in range(4)]
            + [f"arclength-{i}" for i in range(4)]
        )
        self.work = dict.fromkeys(
            (
                "evaluations",
                "jacobian_evaluations",
                "B_grid_requests",
                "B_vjp_requests",
                "position_requests",
                "position_derivative_requests",
                "curvature_requests",
                "curvature_derivative_requests",
                "native_metric_requests",
                "native_gradient_requests",
                "coil_pair_samples",
                "plasma_pair_samples",
            ),
            0,
        )

    def _map(self, curve, derivative):
        return map_full_gradient(
            self.names, list(curve.full_dof_names), list(curve.dof_names), derivative
        )

    def evaluate(self, x, *, derivatives=True):
        x = np.asarray(x, dtype=float)
        if x.shape != (len(self.names),) or not np.all(np.isfinite(x)):
            raise ValueError("invalid physical proposal")
        if list(self.global_objective.dof_names) != self.names:
            raise ValueError("global parameter ordering changed")
        self.global_objective.x = x.copy()
        self.work["evaluations"] += 1
        self.work["jacobian_evaluations"] += int(derivatives)
        values, jacobian = np.zeros(len(self.labels)), np.zeros((len(self.labels), len(x)))
        self.field.set_points(self.points)
        self.work["B_grid_requests"] += 1
        z = spatial_flux(self.field.B().reshape(self.normal.shape), self.normal)
        phi = float(z @ z / 2)
        values[0] = phi / self.flux_scale
        if derivatives:
            self.work["B_vjp_requests"] += 1
            # Direct unthresholded VJP: do not inherit SquaredFlux's near-zero dJ guard.
            jacobian[0] = self.field.B_vjp(z[:, None] * self.weights)(self.global_objective)
            jacobian[0] /= self.flux_scale
        raw, raw_jac = np.zeros(12), np.zeros((12, len(x)))
        for i, (objective, indices) in enumerate(
            zip(self.native, self.native_indices, strict=True)
        ):
            if not np.array_equal(objective.x, x[indices]):
                raise ValueError("native metric/global parameter identity failed")
            self.work["native_metric_requests"] += 1
            raw[i] = float(objective.J())
            if derivatives:
                self.work["native_gradient_requests"] += 1
                gradient = np.asarray(objective.dJ())
                if gradient.shape != (len(indices),):
                    raise ValueError("native metric derivative shape mismatch")
                raw_jac[i, indices] = gradient
        values[1] = 1 - self.scale * raw[:4].sum() / 219.9
        jacobian[1] = -self.scale * raw_jac[:4].sum(axis=0) / 219.9
        curvature = []
        for i, (base, fine) in enumerate(zip(self.bases, self.fine, strict=True)):
            if not np.array_equal(base.local_full_x, fine.local_full_x):
                raise ValueError("refined state desynchronized")
            self.work["curvature_requests"] += 1
            kappa = fine.kappa() / self.scale
            bound, weights = smooth_extremum(kappa, 512.0, upper=True)
            values[2 + i] = 1 - bound / 0.99
            if derivatives:
                self.work["curvature_derivative_requests"] += 1
                d = weights @ fine.dkappa_by_dcoeff() / self.scale
                jacobian[2 + i] = -self._map(base, d) / 0.99
            curvature.append({"sampled_maximum": float(np.max(kappa)), "smooth_upper": bound})
        self.work["position_requests"] += 16
        positions = [c.gamma().copy() for c in self.curves]
        if derivatives:
            self.work["position_derivative_requests"] += 16
            dpositions = [c.dgamma_by_dcoeff() for c in self.curves]

        def projected(i, grad):
            d = grad.reshape(-1) @ dpositions[i].reshape(-1, dpositions[i].shape[-1])
            return self._map(self.curves[i], d)

        clearances = []
        for row, (i, j) in enumerate(self.pairs, start=6):
            self.work["coil_pair_samples"] += len(positions[i]) * len(positions[j])
            bound, gi, gj = soft_squared_clearance(positions[i], positions[j], scale=self.scale)
            sampled = float(
                np.min(np.sum((positions[i][:, None] - positions[j][None, :]) ** 2, axis=-1))
                * self.scale**2
            )
            values[row] = bound / 1.1**2 - 1
            if derivatives:
                jacobian[row] = (projected(i, gi) + projected(j, gj)) / 1.1**2
            clearances.append(
                {"pair": [i, j], "sampled_squared_minimum": sampled, "smooth_squared_lower": bound}
            )
        plasma = []
        for i in range(4):
            self.work["plasma_pair_samples"] += len(positions[i]) * len(self.plasma_points)
            bound, gi, _ = soft_squared_clearance(
                positions[i], self.plasma_points, scale=self.scale
            )
            sampled = float(
                np.min(np.sum((positions[i][:, None] - self.plasma_points[None, :]) ** 2, axis=-1))
                * self.scale**2
            )
            values[126 + i] = bound / 1.3**2 - 1
            if derivatives:
                jacobian[126 + i] = projected(i, gi) / 1.3**2
            plasma.append(
                {"coil": i, "sampled_squared_minimum": sampled, "smooth_squared_lower": bound}
            )
        values[130:134] = 1 - raw[4:8] / self.msc_limit
        values[134:138] = 1 - raw[8:12] / self.arc_limit
        jacobian[130:134] = -raw_jac[4:8] / self.msc_limit
        jacobian[134:138] = -raw_jac[8:12] / self.arc_limit
        if (
            len(values) != 138
            or not np.all(np.isfinite(values))
            or not np.all(np.isfinite(jacobian))
        ):
            raise ValueError("invalid direct constraint bundle")
        metrics = {
            "raw_flux": phi,
            "lengths_device": raw[:4].tolist(),
            "msc_native": raw[4:8].tolist(),
            "arclength_native": raw[8:12].tolist(),
            "curvature": curvature,
            "coil_clearance": clearances,
            "plasma_clearance": plasma,
            "minimum_constraint_margin": float(values[1:].min()),
            "violated_constraints": [
                self.labels[i] for i in range(1, len(values)) if values[i] < 0
            ],
        }
        return values, jacobian if derivatives else None, metrics
