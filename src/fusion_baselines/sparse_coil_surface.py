"""Memory-bounded, native-equivalent fixed-surface coil distance penalty.

The KDTree is only a conservatively padded broadphase. The original unpadded
hinge, parameter-area weights and physical-copy sum are preserved. No surface
derivatives, geometric admission, fields, or optimization are provided here.
"""

import numpy as np
from scipy.spatial import cKDTree
from simsopt._core.derivative import derivative_dec
from simsopt._core.optimizable import Optimizable


def finite(value):
    raw = np.asarray(value)
    if raw.dtype.kind not in "iuf":
        raise ValueError("real numerical geometry without coercion required")
    result = np.asarray(raw, dtype=float)
    if not np.isfinite(result).all():
        raise ValueError("finite geometry required")
    return result


class SparseCurveSurfaceDistance(Optimizable):
    """Same discrete integral and curve VJPs as SIMSOPT CurveSurfaceDistance.

    ``points`` and ``normals`` are copied and frozen. Normals are the unnormalized
    derivatives' cross products on the original parameter grid, NOT unit normals
    or weights normalized to sum one. Callers must construct a new term for a
    different surface; this class cannot supply a surface/co-design derivative.
    """

    def __init__(self, curves, points, normals, minimum_distance=0.08):
        points, normals = finite(points), finite(normals)
        threshold = finite(minimum_distance)
        if (points.ndim != 2 or points.shape[1] != 3 or len(points) < 4
                or normals.shape != points.shape or threshold.shape != ()
                or threshold <= 0 or not curves):
            raise ValueError("nonempty curves, matched surface points/normals and positive cutoff")
        area = np.linalg.norm(normals, axis=1)
        if np.any(area <= 0) or not np.isfinite(area).all():
            raise ValueError("regular unnormalized surface normals required")
        self.curves = list(curves)
        self.points, self.normals, self.area = points.copy(), normals.copy(), area.copy()
        for array in (self.points, self.normals, self.area):
            array.setflags(write=False)
        self.minimum_distance = float(threshold)
        self._tree = cKDTree(self.points, copy_data=True)
        self._geometry_cache = None
        super().__init__(depends_on=self.curves)

    def recompute_bell(self, parent=None):
        self._geometry_cache = None

    def _compute(self):
        if self._geometry_cache is not None:
            return self._geometry_cache
        value, shortest, active_pairs, max_neighbors = 0.0, np.inf, 0, 0
        position_covectors, tangent_covectors, counts = [], [], []
        for curve in self.curves:
            positions, tangents = finite(curve.gamma()), finite(curve.gammadash())
            if (positions.ndim != 2 or positions.shape[1] != 3 or len(positions) < 4
                    or tangents.shape != positions.shape):
                raise ValueError("complete matching Cartesian curve samples required")
            speed = np.linalg.norm(tangents, axis=1)
            if np.any(speed <= 0) or not np.isfinite(speed).all():
                raise ValueError("nonzero finite curve speed required")
            distances = self._tree.query(positions, k=1, eps=0, workers=1)[0]
            if not np.isfinite(distances).all() or np.any(distances <= 0):
                raise ValueError("coincident coil/surface nodes have undefined distance gradient")
            shortest = min(shortest, float(distances.min()))
            pad = 128 * np.finfo(float).eps * max(
                1.0, float(abs(positions).max()), float(abs(self.points).max()),
                self.minimum_distance)
            radius = self.minimum_distance + pad
            normalization = float(len(positions) * len(self.points))
            dg, dv = np.zeros_like(positions), np.zeros_like(tangents)
            # One curve node at a time: even an entirely active surface cannot
            # create an Nc*Ns vector/AD temporary. No neighbor cap or truncation.
            for i, position in enumerate(positions):
                ids = self._tree.query_ball_point(
                    position, radius, eps=0, workers=1, return_sorted=True)
                max_neighbors = max(max_neighbors, len(ids))
                if not ids:
                    continue
                delta = position - self.points[ids]
                distance = np.linalg.norm(delta, axis=1)
                if np.any(distance <= 0) or not np.isfinite(distance).all():
                    raise ValueError("finite nonzero active pair distance required")
                gap = np.maximum(self.minimum_distance - distance, 0.0)
                area = self.area[ids]
                weighted_gap = area * gap / normalization
                gap_integral = float(np.sum(weighted_gap * gap))
                value += float(speed[i] * gap_integral)
                dg[i] = -2 * speed[i] * np.sum(
                    (weighted_gap / distance)[:, None] * delta, axis=0)
                dv[i] = gap_integral * tangents[i] / speed[i]
                active_pairs += int(np.count_nonzero(gap > 0))
            if not np.isfinite(dg).all() or not np.isfinite(dv).all():
                raise ValueError("nonfinite distance covectors")
            position_covectors.append(dg)
            tangent_covectors.append(dv)
            counts.append(len(positions))
        if not np.isfinite([value, shortest]).all():
            raise ValueError("nonfinite coil/surface integral or minimum")
        self._geometry_cache = dict(
            value=float(value), shortest_distance=float(shortest),
            position_covectors=position_covectors, tangent_covectors=tangent_covectors,
            stats=dict(active_pairs=active_pairs, maximum_neighbors=max_neighbors,
                       surface_points=len(self.points), physical_curves=len(self.curves),
                       curve_points=counts, nodewise=True))
        return self._geometry_cache

    def J(self):
        return self._compute()["value"]

    @derivative_dec
    def dJ(self):
        cached = self._compute()
        return sum(curve.dgamma_by_dcoeff_vjp(dg) + curve.dgammadash_by_dcoeff_vjp(dv)
                   for curve, dg, dv in zip(self.curves, cached["position_covectors"],
                                           cached["tangent_covectors"], strict=True))

    def shortest_distance(self):
        return self._compute()["shortest_distance"]

    def stats(self):
        result = dict(self._compute()["stats"])
        result["curve_points"] = result["curve_points"].copy()
        return result

    return_fn_map = {"J": J, "dJ": dJ}
