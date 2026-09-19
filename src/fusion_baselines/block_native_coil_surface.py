"""Memory-bounded execution of the unchanged native fixed-surface CP formula.

No surface point, physical curve or kernel request is omitted. All output
buffers are synchronously copied to the host and kernel results are never
cached. This is a separate reference execution, not a new Sparse formula.
"""

import copy
from contextlib import contextmanager

import jax
import numpy as np
from scipy.spatial.distance import cdist
from simsopt._core.derivative import Derivative, derivative_dec
from simsopt._core.optimizable import Optimizable
from simsopt.geo.curveobjectives import cs_distance_pure

QUANTITIES = ("J", "position", "tangent", "minimum", "position_vjp", "tangent_vjp")
# Stable callables, constructed once per process. Block coordinates and normals
# are dynamic arguments, never captured by per-block closures or fresh JITs.
VALUE_KERNEL = jax.jit(cs_distance_pure)
POSITION_KERNEL = jax.jit(jax.grad(cs_distance_pure, argnums=0))
TANGENT_KERNEL = jax.jit(jax.grad(cs_distance_pure, argnums=1))


def finite(value):
    raw = np.asarray(value)
    if raw.dtype.kind not in "iuf" or not np.isfinite(raw).all():
        raise ValueError("finite real numerical data without coercion required")
    result = np.asarray(raw, dtype=np.float64)
    if not np.isfinite(result).all():
        raise ValueError("finite float64 representation required")
    return result


def host_copy(value, shape):
    """Synchronize before returning a separate finite float64 host buffer."""
    ready = jax.block_until_ready(value)
    result = np.array(ready, copy=True)
    if (
        result.shape != shape
        or result.dtype != np.dtype("float64")
        or not np.isfinite(result).all()
    ):
        raise ValueError("finite float64 native output with exact shape required")
    return result


class BlockNativeCurveSurfaceDistance(Optimizable):
    """Equal-sized complete surface blocks and unchanged native curve VJPs.

    ``progress_callback`` receives independent JSON-compatible records with
    phase reservations and actual in-memory attempted/completed counters. On a
    hard interruption the last durable work is only a lower bound: the reserved
    upper work bounds unobserved execution; no exact completion is inferred.
    """

    def __init__(
        self, curves, points, normals, minimum_distance=0.08, block_size=256, progress_callback=None
    ):
        curves = list(curves)
        points, normals = finite(points), finite(normals)
        threshold = finite(minimum_distance)
        if (
            points.ndim != 2
            or points.shape[1] != 3
            or len(points) < 4
            or normals.shape != points.shape
            or threshold.shape != ()
            or threshold <= 0
            or not curves
        ):
            raise ValueError("nonempty curves and matched regular surface data required")
        if (
            type(block_size) is not int
            or block_size <= 0
            or block_size > len(points)
            or len(points) % block_size
        ):
            raise ValueError("positive equal block size must completely partition the surface")
        area = np.linalg.norm(normals, axis=1)
        if not np.isfinite(area).all() or np.any(area <= 0):
            raise ValueError("finite nonzero unnormalized surface normals required")
        if not jax.config.x64_enabled:
            raise ValueError("native JAX float64 must already be enabled")
        if progress_callback is not None and not callable(progress_callback):
            raise ValueError("callable progress callback required")
        self.curves = list(curves)
        self.points, self.normals = points.copy(), normals.copy()
        self.points.setflags(write=False)
        self.normals.setflags(write=False)
        # Exact node coincidence validation only. This set does not cull pairs,
        # approximate distances or participate in the reported full minimum.
        self._surface_nodes = set(map(tuple, self.points))
        self.minimum_distance, self.block_size = float(threshold), block_size
        self.nblocks = len(points) // block_size
        self._weight = float(block_size / len(points))
        self._kernels = dict(J=VALUE_KERNEL, position=POSITION_KERNEL, tangent=TANGENT_KERNEL)
        self._work = {key: dict(attempted=0, completed=0) for key in QUANTITIES}
        self._progress_callback, self._progress_index = progress_callback, 0
        super().__init__(depends_on=self.curves)

    def kernel_work(self):
        return copy.deepcopy(self._work)

    def _emit(self, event):
        if self._progress_callback is not None:
            self._progress_callback(copy.deepcopy(event))

    @contextmanager
    def _phase(self, curve_index, phase, **reserve):
        reservation = {key: reserve.get(key, 0) for key in QUANTITIES}
        before = self.kernel_work()
        upper = {
            key: {counter: value + reservation[key] for counter, value in row.items()}
            for key, row in before.items()
        }
        event = dict(
            index=self._progress_index,
            curve_index=curve_index,
            phase=phase,
            status="reserved",
            reservation=reservation,
            work_before=before,
            work=before,
            upper_work=upper,
        )
        self._progress_index += 1
        try:
            self._emit(event)
            yield
            if self._work != upper:
                raise RuntimeError("completed phase must exactly consume its kernel reservation")
            event.update(status="completed", work=self.kernel_work())
            self._emit(event)
        except Exception as error:
            event.update(
                status="error", work=self.kernel_work(), error=f"{type(error).__name__}: {error}"
            )
            try:
                self._emit(event)
            except Exception as recording_error:
                event["recording_error"] = f"{type(recording_error).__name__}: {recording_error}"
            raise

    def _curve_data(self, curve):
        position, tangent = finite(curve.gamma()).copy(), finite(curve.gammadash()).copy()
        if (
            position.ndim != 2
            or position.shape[1] != 3
            or len(position) < 4
            or tangent.shape != position.shape
        ):
            raise ValueError("complete matched Cartesian curve samples required")
        speed = np.linalg.norm(tangent, axis=1)
        if not np.isfinite(speed).all() or np.any(speed <= 0):
            raise ValueError("nonzero finite curve speed required")
        if any(tuple(p) in self._surface_nodes for p in position):
            raise ValueError("coincident curve/surface node has undefined distance gradient")
        return position, tangent

    def _blocks(self):
        for first in range(0, len(self.points), self.block_size):
            yield (
                self.points[first : first + self.block_size],
                self.normals[first : first + self.block_size],
            )

    def _native(self, quantity, position, tangent, points, normals):
        self._work[quantity]["attempted"] += 1
        result = self._kernels[quantity](position, tangent, points, normals, self.minimum_distance)
        shape = () if quantity == "J" else position.shape
        result = host_copy(result, shape)
        self._work[quantity]["completed"] += 1
        return result

    def _curve_vjp(self, curve, quantity, weights):
        method = (
            curve.dgamma_by_dcoeff_vjp
            if quantity == "position_vjp"
            else curve.dgammadash_by_dcoeff_vjp
        )
        self._work[quantity]["attempted"] += 1
        result = method(weights)
        if not isinstance(result, Derivative):
            raise ValueError("native curve VJP must return a Derivative")
        copied = {}
        for key, value in result.data.items():
            if np.ndim(value) != 1:
                raise ValueError("one-dimensional native coefficient covector required")
            copied[key] = host_copy(value, np.shape(value))
        result = Derivative(copied)
        self._work[quantity]["completed"] += 1
        return result

    def J(self):
        total = 0.0
        for i, curve in enumerate(self.curves):
            position, tangent = self._curve_data(curve)
            with self._phase(i, "J", J=self.nblocks):
                for points, normals in self._blocks():
                    total += self._weight * float(
                        self._native("J", position, tangent, points, normals)
                    )
                if not np.isfinite(total):
                    raise ValueError("nonfinite total native CP integral")
        return float(total)

    @derivative_dec
    def dJ(self):
        total = Derivative({})
        for i, curve in enumerate(self.curves):
            position, tangent = self._curve_data(curve)
            with self._phase(
                i, "dJ", position=self.nblocks, tangent=self.nblocks, position_vjp=1, tangent_vjp=1
            ):
                dg, dv = np.zeros_like(position), np.zeros_like(tangent)
                for points, normals in self._blocks():
                    dg += self._weight * self._native(
                        "position", position, tangent, points, normals
                    )
                    dv += self._weight * self._native("tangent", position, tangent, points, normals)
                if not np.isfinite([dg, dv]).all():
                    raise ValueError("nonfinite accumulated native CP covectors")
                total += self._curve_vjp(curve, "position_vjp", dg)
                total += self._curve_vjp(curve, "tangent_vjp", dv)
                if any(not np.isfinite(value).all() for value in total.data.values()):
                    raise ValueError("nonfinite summed native coefficient covector")
        return total

    def shortest_distance(self):
        minimum = np.inf
        for i, curve in enumerate(self.curves):
            position, _ = self._curve_data(curve)
            with self._phase(i, "minimum", minimum=self.nblocks):
                for points, _ in self._blocks():
                    self._work["minimum"]["attempted"] += 1
                    distances = host_copy(cdist(position, points), (len(position), len(points)))
                    if np.any(distances <= 0):
                        raise ValueError("nonpositive pair distance in full native minimum")
                    value = float(distances.min())
                    self._work["minimum"]["completed"] += 1
                    minimum = min(minimum, value)
        if not np.isfinite(minimum):
            raise ValueError("finite global curve/surface minimum required")
        return float(minimum)

    return_fn_map = {"J": J, "dJ": dJ}
