"""Current-normalized fields initialized directly from admitted clear geometry.

The old construction arithmetic is inherited unchanged. This adapter only owns
initialization, the fixed-surface sparse penalty, provenance and native-call
accounting. Exact admission/hash binding of the input document belongs to the
separate workflow; a structurally valid geometry is not by itself an admission.
"""

import copy
import json
import time
from pathlib import Path

import numpy as np

from fusion_baselines.coupled_coils import (
    CoupledCoils,
    canonical_names,
    load_target,
    local_names,
    physical_rows,
)


def geometry_seed(document):
    """Validate the exact currentless schema and return an isolated document."""
    keys = {
        "schema_version",
        "kind",
        "nfp",
        "nbase",
        "order",
        "names",
        "base_coefficients",
        "physical",
        "case",
        "sources",
        "parameter_orientation",
    }
    if not isinstance(document, dict) or set(document) != keys:
        raise ValueError("complete geometry-only snapshot schema required")
    if (
        type(document["schema_version"]) is not int
        or document["schema_version"] != 1
        or type(document["nfp"]) is not int
        or document["nfp"] != 2
        or document["kind"] != "geometry-only"
        or document["parameter_orientation"] != "alpha=-2*pi*t"
    ):
        raise ValueError("geometry-only nfp2 schema1 with clockwise parameters required")
    nbase, order = document["nbase"], document["order"]
    if type(nbase) is not int or type(order) is not int or (nbase, order) not in ((6, 5), (8, 7)):
        raise ValueError("registered six/order5 or eight/order7 class required")
    expected_case = dict(
        label=f"n{nbase}-shape-d100mm",
        nbase=nbase,
        order=order,
        method="shape",
        d=0.10,
        K=order - 1,
        r_floor=float(0.06 / (2 * np.sin(np.pi / (4 * nbase))) + 0.025),
    )
    if document["case"] != expected_case or any(
        type(document["case"][key]) is not type(value) for key, value in expected_case.items()
    ):
        raise ValueError("selected shaped100mm geometry case required")
    if document["names"] != canonical_names(nbase, order):
        raise ValueError("exact canonical physical DOF names required")
    coefficients = np.asarray(document["base_coefficients"])
    if (
        coefficients.dtype.kind not in "iuf"
        or coefficients.shape != (nbase, 3, 2 * order + 1)
        or not np.isfinite(coefficients).all()
    ):
        raise ValueError("complete finite real Fourier coefficient tensor required")
    physical = document["physical"]
    expected = [
        {k: v for k, v in row.items() if k != "current"} for row in physical_rows(nbase, 1.0)
    ]
    if not isinstance(physical, list) or len(physical) != len(expected):
        raise ValueError("all currentless physical coil copies required")
    for actual, row in zip(physical, expected, strict=True):
        if (
            not isinstance(actual, dict)
            or set(actual) != set(row)
            or actual != row
            or type(actual["base_index"]) is not int
            or type(actual["period"]) is not int
            or type(actual["flip"]) is not bool
        ):
            raise ValueError("exact currentless physical symmetry mapping required")
    sources = document["sources"]
    if not isinstance(sources, dict) or set(sources) != {"reference", "selected"}:
        raise ValueError("both original geometry target sources required")
    for target in sources.values():
        if not isinstance(target, dict) or set(target) != {"input", "wout"}:
            raise ValueError("complete geometry input/wout source identities required")
        for ref in target.values():
            if (
                not isinstance(ref, dict)
                or set(ref) != {"path", "sha256"}
                or not isinstance(ref["path"], str)
                or not Path(ref["path"]).is_absolute()
                or not isinstance(ref["sha256"], str)
                or len(ref["sha256"]) != 64
                or any(c not in "0123456789abcdef" for c in ref["sha256"])
            ):
                raise ValueError("absolute hash-bound geometry sources required")
    # A plain finite JSON document is retained, not a mutable caller alias.
    return json.loads(json.dumps(document, allow_nan=False))


class CountedField:
    """Narrow field proxy: every requested value/VJP is retained, even on error.

    A callback receives independent event copies before and after native work.
    Callback failures propagate; no native work begins if its attempted record
    cannot be persisted. A native cache hit remains a counted requested call.
    A persisted attempted event is only a pre-dispatch observation: interruption
    may happen during the native call, so its false native_started flag is never
    proof of zero work. Every attempted event consumes an attempted-call slot.
    """

    def __init__(self, native, name, events, callback=None):
        self._native, self._name = native, name
        self._events, self._callback = events, callback
        self._point_count = 0

    def set_points(self, points):
        points = np.asarray(points)
        if (
            points.dtype.kind not in "iuf"
            or points.ndim != 2
            or points.shape[1] != 3
            or not len(points)
            or not np.isfinite(points).all()
        ):
            raise ValueError("finite nonempty real Cartesian field points required")
        self._native.set_points(np.ascontiguousarray(points, dtype=float).copy())
        self._point_count = len(points)

    def _emit(self, event):
        if self._callback is not None:
            self._callback(copy.deepcopy(event))

    def _call(self, quantity, *args):
        event = dict(
            index=len(self._events),
            field=self._name,
            quantity=quantity,
            points=self._point_count,
            status="attempted",
            started_monotonic=time.monotonic(),
            native_started=False,
            native_completed=False,
        )
        self._events.append(event)
        try:
            self._emit(event)
            if not self._point_count:
                raise ValueError("field points must be set before native work")
            event["native_started"] = True
            result = getattr(self._native, quantity)(*args)
            event.update(
                native_completed=True, status="completed", completed_monotonic=time.monotonic()
            )
            self._emit(event)
            return result
        except Exception as exc:
            event.update(
                status="error",
                error=f"{type(exc).__name__}: {exc}",
                failed_monotonic=time.monotonic(),
            )
            # Preserve the primary error if recording that error also fails.
            try:
                self._emit(event)
            except Exception as recording_error:
                event["recording_error"] = f"{type(recording_error).__name__}: {recording_error}"
            raise

    def B(self):
        return self._call("B")

    def A(self):
        return self._call("A")

    def B_vjp(self, weights):
        return self._call("B_vjp", weights)

    def A_vjp(self, weights):
        return self._call("A_vjp", weights)


class ClearCoilField(CoupledCoils):
    """Fresh named clear seed; no old circular constructor or hidden A work."""

    def __init__(
        self,
        wout,
        input_json,
        geometry_snapshot,
        method,
        B2_scale,
        ncoil=256,
        nphi=64,
        ntheta=64,
        ninner=32,
        offset=0,
        *,
        event_callback=None,
    ):
        from simsopt.field import BiotSavart, Current, coils_via_symmetries
        from simsopt.geo import CurveCurveDistance, CurveLength, CurveXYZFourier, LpCurveCurvature
        from simsopt.objectives import QuadraticPenalty

        from fusion_baselines.sparse_coil_surface import SparseCurveSurfaceDistance

        self._seed_geometry = geometry_seed(geometry_snapshot)
        nbase, order = (self._seed_geometry[k] for k in ("nbase", "order"))
        if method not in ("N", "V"):
            raise ValueError("registered N or V method required")
        if (
            any(type(n) is not int or n < 4 for n in (ncoil, nphi, ntheta, ninner))
            or ncoil <= 2 * order
            or ninner not in (32, 64)
            or type(offset) not in (int, float)
            or offset not in (0, 0.5)
        ):
            raise ValueError(
                "resolved periodic field grids and archived32/64 inner target required"
            )
        b2 = np.asarray(B2_scale)
        if b2.shape != () or b2.dtype.kind not in "iuf" or not np.isfinite(b2) or b2 <= 0:
            raise ValueError("positive finite caller-bound fixed B2 scale required")
        if event_callback is not None and not callable(event_callback):
            raise ValueError("native event callback must be callable")
        self._fixed_B2_scale = float(b2)
        self.wout, self.input_json = Path(wout), Path(input_json)
        self.nbase, self.order, self.method, self.nfp = nbase, order, method, 2
        self.ncoil, self.nphi, self.ntheta = ncoil, nphi, ntheta
        self.ninner, self.offset = ninner, offset
        self.names, self.local_names = canonical_names(nbase, order), local_names(order)
        self.target = load_target(wout, input_json, ninner)
        if self.target.get("sources") not in self._seed_geometry["sources"].values():
            raise ValueError("loaded target must exactly match a bound geometry target")
        self.input = self.target["input"]
        self.inner_points = np.asarray(self.target["inner_points"], dtype=float).copy()
        self.inner_target = np.asarray(self.target["inner_target"], dtype=float).copy()
        self.target_flux = float(self.target["target_flux"])
        if (
            self.inner_points.shape != (3 * ninner * ninner, 3)
            or self.inner_target.shape != self.inner_points.shape
            or not np.isfinite([self.inner_points, self.inner_target]).all()
            or not np.isfinite(self.target_flux)
            or self.target_flux == 0
        ):
            raise ValueError("complete finite inner target and nonzero physical flux required")
        self.surface = self.boundary_surface(nphi, ntheta, offset=offset)
        self.geometry_surface = self.boundary_surface(128, 128, full_torus=True, offset=0)
        self.boundary_points = self.surface.gamma().reshape(-1, 3).copy()
        normal = self.surface.normal().reshape(-1, 3).copy()
        norm = np.linalg.norm(normal, axis=1)
        if not np.isfinite(norm).all() or np.any(norm <= 0):
            raise ValueError("regular finite target surface required")
        self.boundary_normals = normal / norm[:, None]
        self.boundary_weights = norm / norm.sum()
        self.base_curves = [CurveXYZFourier(ncoil, order) for _ in range(nbase)]
        coefficients = np.asarray(self._seed_geometry["base_coefficients"], dtype=float)
        for curve, values in zip(self.base_curves, coefficients, strict=True):
            if (
                list(curve.local_full_dof_names) != self.local_names
                or list(curve.local_dof_names) != self.local_names
            ):
                raise ValueError(
                    "native local Fourier names/free masks differ from canonical mapping"
                )
            curve.local_full_x = values.ravel().copy()
            if not np.array_equal(curve.local_full_x, values.ravel()):
                raise ValueError("native named Fourier assignment changed seed coefficients")
        self.seed_x = coefficients.ravel().copy()
        self.base_currents = [Current(1e5) for _ in range(nbase)]
        for current in self.base_currents:
            current.fix_all()
        self.coils = coils_via_symmetries(self.base_curves, self.base_currents, 2, True)
        self.curves = [coil.curve for coil in self.coils]
        self.native_calls = []
        self.field, self.inner_field, self.loop_field = [
            CountedField(BiotSavart(self.coils), label, self.native_calls, event_callback)
            for label in ("boundary", "inner", "loop")
        ]
        self.length_terms = [CurveLength(curve) for curve in self.base_curves]
        self.curvature_terms = [
            LpCurveCurvature(curve, 2, threshold=10) for curve in self.base_curves
        ]
        self.cc = CurveCurveDistance(self.curves, 0.06, num_basecurves=4 * nbase)
        self.cs = SparseCurveSurfaceDistance(
            self.curves,
            self.geometry_surface.gamma().reshape(-1, 3),
            self.geometry_surface.normal().reshape(-1, 3),
            minimum_distance=0.08,
        )
        self.geometry = (
            sum(QuadraticPenalty(term, 3.5, "max") for term in self.length_terms)
            + 1000 * self.cc
            + 1000 * self.cs
            + 1e-4 * sum(self.curvature_terms)
        )
        self._cache = None
        self._loop_points, self._loop_tangents = self.loop(256)
        self.loop_field.set_points(self._loop_points)
        initial_a = self.loop_field.A()
        self.seed_unit_flux = float(np.mean(np.sum(initial_a * self._loop_tangents, axis=1)))
        if not np.isfinite(self.seed_unit_flux) or abs(self.seed_unit_flux) <= 1e-12:
            raise ValueError("clear-seed unit-current flux degenerate")
        self.initialization_work = dict(seed_A_calls=1, seed_A_points=256)

    @property
    def B2_scale(self):
        return self._fixed_B2_scale

    def _check_B2(self, value):
        if value is not None and (np.shape(value) != () or value != self.B2_scale):
            raise ValueError("caller-bound B2 scale must remain exactly frozen")

    def diagnostics(self, x, scale, B2_scale):
        self._check_B2(B2_scale)
        return super().diagnostics(x, scale, self.B2_scale)

    def arrays(self, x, scale=None, B2_scale=None):
        self._check_B2(B2_scale)
        return super().arrays(x, scale, self.B2_scale)

    def snapshot(self, x, scale=None, B2_scale=None):
        self._check_B2(B2_scale)
        if scale is not None:
            raise ValueError("retain original construction snapshot for frozen-current diagnostics")
        result = super().snapshot(x, B2_scale=self.B2_scale)
        result["sources"] = copy.deepcopy(result["sources"])
        result["seed_geometry"] = copy.deepcopy(self._seed_geometry)
        result["construction"].update(
            geometry_nphi=128, geometry_ntheta=128, geometry_full_torus=True, geometry_offset=0
        )
        return result
