"""Normalized six-coil fitting with headroom; selection is never acceptance."""

import copy
import functools
import hashlib
import inspect
import io
import json
import shutil
import struct
import time

import numpy as np

MAX_BYTES, START_RESERVE, LIVE_RESERVE = 1024**3, 3*1024**3, 2*1024**3
# Wall-clock caps; arms compared with each other must still share one budget.
MAX_SEARCH_SECONDS, MAX_CHECK_SECONDS = 4*3600, 1800
# Output kept free during search so the selected candidate can still be checked (#90).
CHECK_STORAGE_RESERVE = 48*1024**2


class StorageLimit(OSError):
    """The output ceiling for the current phase was reached; prior records are intact."""
PROBE_STEPS = (1.25e-6, 6.25e-7)
SOLVER_OPTIONS = dict(maxiter=2**31-1, maxfun=2**31-1, maxls=20, ftol=0., gtol=1e-9)
RECORDING_FORMAT = "fusion-coil-recording-v3"
# v3 stores each coordinate/gradient vector once as little-endian float64 in this file;
# trial and iterate JSON reference it by byte offset, count and SHA-256 (#90).
VECTOR_STORE = "vectors.f64"
EVALUATION_COST_SCOPE = "model.evaluate and post-evaluation guard; excludes trial-file writes"
OBJECTIVE_WEIGHTS = dict(flux_per_area=1., length=1., coil_distance=1000.,
                         surface_distance=1000., curvature=.01)
# Optional interior objective (method of #12). Its surfaces lie between the checked
# s = 0.25/0.5/0.75 surfaces, so no objective point is an acceptance point.
INTERIOR_OBJECTIVE = dict(surfaces=(.125, .375, .625, .875), resolution=16, shift=.5)
# Construction margins keep sampled fits inside the unchanged acceptance limits
# (length 3.5 m, coil-coil 0.06 m, coil-plasma 0.08 m, curvature 12/m).
# "halved" moves each margin halfway to its limit (issue #70). A preset is the only
# source of the penalty thresholds and selection length cap that are used and recorded.
MARGINS = {
    "current": dict(length=3.44, selection_length=3.45, coil_distance=0.07,
                    surface_distance=0.09, curvature=10.),
    "halved": dict(length=3.47, selection_length=3.475, coil_distance=0.065,
                   surface_distance=0.085, curvature=11.),
}
# Sampled acceptance limits for selection eligibility; independent of the margin preset.
SAMPLED_LIMITS = dict(sampled_length_max_m=3.5, sampled_curvature_max_per_m=12.,
                      sampled_coil_distance_min_m=.06, sampled_surface_distance_min_m=.08,
                      current_max_A=500000.)


def margin_preset(name="current"):
    if name not in MARGINS:
        raise ValueError("registered construction margins required")
    return dict(MARGINS[name], name=name)


def penalty_settings(margins="current"):
    """Objective penalty thresholds derived from one registered margin preset."""
    margin = margin_preset(margins)
    return dict(length_max_m=margin["length"], coil_distance_min_m=margin["coil_distance"],
                surface_distance_min_m=margin["surface_distance"],
                curvature_threshold_per_m=margin["curvature"], curvature_p=2)


def selection_settings(margins="current"):
    """Preset selection length cap plus the unchanged sampled acceptance limits."""
    return dict(length_max_m=margin_preset(margins)["selection_length"], **SAMPLED_LIMITS)


FLUX_OBJECTIVES = ("local", "mean-abs")
MEAN_ABS_EPSILON = 1e-4


def recording_settings(task_id, margins="current", ncoil=256, n=64, offset=0,
                       interior_weight=0., flux_objective="local"):
    """Prospective fixed-target settings; no inferred plasma or equilibrium trajectory."""
    interior = interior_weight > 0
    # Interior-specific settings add no keys for boundary-only runs.
    extra = dict(interior_objective=dict(INTERIOR_OBJECTIVE)) if interior else {}
    if flux_objective != "local":  # Opt-in; default runs keep their recorded bytes.
        extra["flux_objective"] = dict(
            name=flux_objective, epsilon=MEAN_ABS_EPSILON,
            definition="0.5*mean_i(sqrt(e_i^2+eps^2))^2, e_i=B.n/|B| per boundary point")
    return dict(format=RECORDING_FORMAT, task_id=task_id,
                objective_weights=dict(OBJECTIVE_WEIGHTS, **(
                    dict(interior=float(interior_weight)) if interior else {})), **extra,
                constraints=dict(margin_preset=margins,
                                 penalties=penalty_settings(margins),
                                 selection=selection_settings(margins), coefficient_bounds=None),
                search_resolution=dict(boundary_phi=n, boundary_theta=n, boundary_offset=offset,
                                       boundary_phi_extent_turns=.5, coil_nodes=ncoil,
                                       flux_loop_nodes=ncoil, geometry_phi=128,
                                       geometry_theta=128, geometry_phi_extent_turns=1.),
                elapsed_scope=EVALUATION_COST_SCOPE,
                search_timing=dict(clock="time.monotonic; seconds",
                    origin="after startup, before minimize",
                    start="before vector and attempt publication",
                    end="after model evaluation/post-guard, before terminal publication",
                    callback="before iterate publication"),
                resource_limits=dict(output_bytes=MAX_BYTES, initial_reserve_bytes=START_RESERVE,
                                     live_reserve_bytes=LIVE_RESERVE),
                selection_rule=("lowest flux_objective + interior_objective"
                                if interior or flux_objective != "local" else "lowest normal_rms")
                + " among completed eligible startup-seed/search",
                current_convention="1e5 A base current scaled by target_flux/unit_flux",
                target_policy="fixed seed target, signed flux and B2_scale throughout run")


def interior_target(data):
    """Objective-only interior points and VMEC field from an open, already bound Wout."""
    from fusion_baselines import wout_target

    points, field = [], []
    for surface in INTERIOR_OBJECTIVE["surfaces"]:
        row = wout_target.sample(data, surface, INTERIOR_OBJECTIVE["resolution"],
                                 INTERIOR_OBJECTIVE["shift"])
        points.append(np.stack((row["radius"]*np.cos(row["phi"]), row["radius"]*np.sin(row["phi"]),
                                row["height"]), axis=-1).reshape(-1, 3))
        field.append(row["native"].reshape(-1, 3))
    return dict(points=np.concatenate(points), target=np.concatenate(field))


def mode_map(entries):
    result = {}
    for entry in entries:
        m, n, value = entry["m"], entry["n"], float(entry["value"])
        if int(m) != m or int(n) != n or not np.isfinite(value) or (m, n) in result:
            raise ValueError("unique finite integer Fourier modes required")
        result[m, n] = value
    return result


def loop_geometry(data, count):
    """Exact Fourier phi=0 section; tangent is d(position)/dt, t=theta/(2pi)."""
    if type(count) is not int or count < 4:
        raise ValueError("at least four loop points required")
    theta = 2 * np.pi * np.arange(count) / count
    r, z, rt, zt = (np.zeros(count) for _ in range(4))
    for (m, _), value in mode_map(data["rbc"]).items():
        r += value * np.cos(m * theta)
        rt -= 2 * np.pi * m * value * np.sin(m * theta)
    for (m, _), value in mode_map(data["zbs"]).items():
        z += value * np.sin(m * theta)
        zt += 2 * np.pi * m * value * np.cos(m * theta)
    points = np.column_stack((r, np.zeros(count), z))
    tangents = np.column_stack((rt, np.zeros(count), zt))
    if not np.isfinite([points, tangents]).all() or np.any(r <= 0):
        raise ValueError("finite positive-R loop required")
    return points, tangents


ORDERS = (5, 8)  # Registered six-coil Fourier orders; order 5 is the public starter class.


def names(order=5):
    if order not in ORDERS:
        raise ValueError(f"registered coil Fourier order required: {ORDERS}")
    return [
        name for axis in "xyz" for name in
        [f"{axis}c(0)"] + [f"{axis}{kind}({m})" for m in range(1, order+1) for kind in "sc"]
    ]


def canonical_gradient(curves, derivative, order=5):
    local, result = names(order), []
    for curve in curves:
        labels = list(curve.local_dof_names)
        if list(curve.local_full_dof_names) != local or sorted(labels) != sorted(local):
            raise ValueError("complete named free coordinates of the registered order required")
        values = np.asarray(derivative(curve), dtype=float)
        if values.shape != (len(local),) or not np.isfinite(values).all():
            raise ValueError("finite named local gradient required")
        result.extend(values[[labels.index(name) for name in local]])
    if len(result) != 6*len(local):
        raise ValueError("six base curves required")
    return np.asarray(result)


def lift_order(snapshot, order):
    """Same coil geometry at a higher Fourier order: new modes are exactly zero."""
    from fusion_baselines.coupled_coil_audit import parameter_names

    old = snapshot["order"]
    if order not in ORDERS or order < old:
        raise ValueError("registered order at least the snapshot's order required")
    coefficients = np.zeros((6, 3, 2*order+1))
    coefficients[:, :, :2*old+1] = np.asarray(snapshot["base_coefficients"], dtype=float)
    lifted = dict(snapshot, order=order, names=parameter_names(6, order),
                  base_coefficients=coefficients.tolist())
    lifted["lifted_from_order"] = old
    return lifted


class Recorder:
    def __init__(self, output, deadline, storage=None):
        self.output, self.deadline = output, deadline
        self.output.mkdir(parents=True, exist_ok=False)
        self.counts = {name: dict(attempted=0, completed=0)
                       for name in ("B", "A", "B_vjp", "A_vjp", "independent_B", "independent_BA")}
        self.bundles, self.bytes, self.active = 0, 0, None
        self.storage = [0] if storage is None else storage
        self.limit = None  # None means the full MAX_BYTES ceiling, read at write time.

    def guard(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError("declared elapsed-time limit reached")
        if shutil.disk_usage(self.output).free < LIVE_RESERVE:
            raise OSError("live disk reserve exhausted")

    def save(self, name, value):
        payload = value if isinstance(value, bytes) else (
            json.dumps(value, allow_nan=False, sort_keys=True, indent=2)+"\n").encode("utf-8")
        path = self.output/name
        temporary = path.with_suffix(path.suffix+".tmp")
        if temporary.exists():
            raise FileExistsError("existing failed temporary output must not be overwritten")
        limit = MAX_BYTES if self.limit is None else self.limit
        if self.storage[0]+len(payload) > limit:
            raise StorageLimit(f"{limit} byte output ceiling for this phase reached "
                               "(aggregate including temporary publication)")
        difference = len(payload)-(path.stat().st_size if path.exists() else 0)
        try:
            with temporary.open("xb") as stream:
                if stream.write(payload) != len(payload):
                    raise OSError("short output write; publication incomplete")
            temporary.replace(path)
        except Exception:
            # Retain failed temporary bytes and charge them against the shared cap.
            if temporary.exists():
                retained = temporary.stat().st_size
                self.storage[0] += retained
                self.bytes += retained
            raise
        self.bytes += difference
        self.storage[0] += difference

    def vector(self, values):
        """Append one float64 vector to the run's store and return its reference."""
        values = [float(v) for v in values]
        payload = struct.pack(f"<{len(values)}d", *values)
        limit = MAX_BYTES if self.limit is None else self.limit
        if self.storage[0]+len(payload) > limit:
            raise StorageLimit(f"{limit} byte output ceiling for this phase reached "
                               "(aggregate including temporary publication)")
        path = self.output/VECTOR_STORE
        offset = path.stat().st_size if path.exists() else 0
        with path.open("ab") as stream:
            written = stream.write(payload)
            stream.flush()
        self.storage[0] += written
        self.bytes += written
        if written != len(payload):
            raise OSError("short vector-store write; publication incomplete")
        return dict(store=VECTOR_STORE, offset_bytes=offset, count=len(values),
                    sha256=hashlib.sha256(payload).hexdigest())

    def call(self, name, function, *args):
        self.guard()
        self.counts[name]["attempted"] += 1
        self.save("progress.json",
                  dict(native=self.counts, bundles=self.bundles, active=self.active))
        self.guard()  # A progress write must not start native work after its deadline.
        answer = function(*args)
        self.counts[name]["completed"] += 1
        self.save("progress.json",
                  dict(native=self.counts, bundles=self.bundles, active=self.active))
        self.guard()
        return answer

    def finish(self, report, started):
        report["elapsed_s"] = time.monotonic()-started
        report["deadline_met"] = time.monotonic() < self.deadline
        report["completed"] &= report["deadline_met"]
        self.save("result.json", report)
        if time.monotonic() >= self.deadline:
            report.update(completed=False, deadline_met=False, elapsed_s=time.monotonic()-started)
            self.save("result.json", report)
        return report["completed"]


@functools.cache
def tracked_field_class(field_class):
    """One class/counter per native type: Optimizable equality uses class + ID."""
    class Tracked(field_class):
        def __init__(self, coils, record):
            self.record = record
            super().__init__(coils)

        def B(self):
            return self.record.call("B", super().B)

        def A(self):
            return self.record.call("A", super().A)

        def B_vjp(self, weights):
            return self.record.call("B_vjp", super().B_vjp, weights)

        def A_vjp(self, weights):
            return self.record.call("A_vjp", super().A_vjp, weights)
    Tracked.__name__ = f"ExploratoryTracked_{field_class.__module__}_{field_class.__name__}"
    return Tracked


def tracked_field(field_class, coils, record):
    return tracked_field_class(field_class)(coils, record)


class Model:
    def __init__(self, seed, data, record, ncoil=256, n=64, offset=0, margins="current",
                 interior=None, interior_weight=0., flux_objective="local"):
        if flux_objective not in FLUX_OBJECTIVES:
            raise ValueError("registered flux objective required")
        self.flux_objective = flux_objective
        if not (np.isfinite(interior_weight) and interior_weight >= 0
                and (interior is None) == (interior_weight == 0)):
            raise ValueError("an interior target exactly when the interior weight is positive")
        self.interior_weight = float(interior_weight)
        self.margins = margin_preset(margins)
        self.penalties = penalty_settings(margins)
        from simsopt.field import BiotSavart, Current, coils_via_symmetries
        from simsopt.geo import (
            CurveCurveDistance,
            CurveLength,
            CurveXYZFourier,
            LpCurveCurvature,
            SurfaceRZFourier,
        )
        from simsopt.objectives import QuadraticPenalty, SquaredFlux

        from fusion_baselines.sparse_coil_surface import SparseCurveSurfaceDistance

        self.seed, self.data, self.record = seed, data, record
        self.order = seed.get("order", 5)
        self.x0 = np.asarray(seed["base_coefficients"]).ravel()
        expected = [f"coil[{i}]/{name}" for i in range(6) for name in names(self.order)]
        if seed["names"] != expected or self.x0.shape != (len(expected),):
            raise ValueError("exact six-coil named seed required")

        def surface(count, full=False, shift=0):
            s = SurfaceRZFourier(
                nfp=2, stellsym=True, mpol=4, ntor=10,
                quadpoints_phi=(np.arange(count)+shift)/(count*(1 if full else 2)),
                quadpoints_theta=(np.arange(count)+shift)/count)
            s.local_full_x = np.zeros_like(s.local_full_x)
            for key, setter in (("rbc", s.set_rc), ("zbs", s.set_zs)):
                for row in data[key]:
                    if row["value"] != 0:
                        setter(row["m"], row["n"], row["value"])
            s.local_full_x = s.get_dofs()
            s.fix_all()
            return s

        self.surface, geometry_surface = surface(n, shift=offset), surface(128, full=True)
        self.points, self.normals = self.surface.gamma().copy(), self.surface.normal().copy()
        self.area = float(np.linalg.norm(self.normals, axis=-1).mean())
        self.curves = [CurveXYZFourier(ncoil, self.order) for _ in range(6)]
        self.set_x(self.x0)
        currents = [Current(1e5) for _ in range(6)]
        for current in currents:
            current.fix_all()
        self.coils = coils_via_symmetries(self.curves, currents, 2, True)
        self.field = tracked_field(BiotSavart, self.coils, record)
        self.loop_field = tracked_field(BiotSavart, self.coils, record)
        self.loop_points, self.loop_tangent = loop_geometry(data, ncoil)
        self.loop_field.set_points(self.loop_points)
        self.interior = None
        if interior is not None:
            self.interior = {k: np.ascontiguousarray(interior[k], dtype=float)
                             for k in ("points", "target")}
            if (self.interior["points"].shape != self.interior["target"].shape
                    or not np.isfinite(list(self.interior.values())).all()):
                raise ValueError("finite matching interior points and target required")
            self.interior_field = tracked_field(BiotSavart, self.coils, record)
            self.interior_field.set_points(self.interior["points"])
        # threshold=0 equals released SIMSOPT's SquaredFlux (J >= 0); only the historical fork
        # accepts the argument. Its J < 1e-10 gradient zeroing is rejected below anyway.
        flux_options = dict(definition="local")
        if "threshold" in inspect.signature(SquaredFlux.__init__).parameters:
            flux_options["threshold"] = 0.0
        self.objective = SquaredFlux(self.surface, self.field, **flux_options)
        physical = [c.curve for c in self.coils]
        self.lengths = [CurveLength(c) for c in self.curves]
        penalty = self.penalties
        self.cc = CurveCurveDistance(physical, penalty["coil_distance_min_m"], num_basecurves=24)
        self.cp = SparseCurveSurfaceDistance(
            physical, geometry_surface.gamma().reshape(-1, 3),
            geometry_surface.normal().reshape(-1, 3),
            minimum_distance=penalty["surface_distance_min_m"])
        self.geometry = (sum(QuadraticPenalty(term, penalty["length_max_m"], "max")
                             for term in self.lengths)
                         + OBJECTIVE_WEIGHTS["coil_distance"]*self.cc
                         + OBJECTIVE_WEIGHTS["surface_distance"]*self.cp
                         + OBJECTIVE_WEIGHTS["curvature"]*sum(LpCurveCurvature(
                             c, penalty["curvature_p"],
                             threshold=penalty["curvature_threshold_per_m"])
                             for c in self.curves))

        from fusion_baselines.coupled_coil_audit import physical_curves

        own = physical_curves(seed, ncoil)
        self.identity_error = max(float(np.max(abs(np.asarray([getattr(c, method)()
            for c in physical])-own[key]))) for method, key in
            (("gamma", "positions"), ("gammadash", "tangents")))
        if self.identity_error > 1e-12:
            raise ValueError("native/independent initial physical coil mapping differs")

    def set_x(self, x):
        x = np.asarray(x, dtype=float)
        if x.shape != self.x0.shape or not np.isfinite(x).all():
            raise ValueError("finite named coefficient vector of the seed's size required")
        for curve, row in zip(self.curves, x.reshape(6, -1), strict=True):
            if list(curve.local_full_dof_names) != names(self.order):
                raise ValueError("native physical coordinate order changed")
            curve.local_full_x = row.copy()

    def geometry_metrics(self):
        lengths = [float(j.J()) for j in self.lengths]
        curvature = [float(np.max(c.kappa())) for c in self.curves]
        cc, cp = float(self.cc.shortest_distance()), float(self.cp.shortest_distance())
        return dict(lengths=lengths, kappa_max=curvature, coil_distance=cc, surface_distance=cp,
                    sampled_geometry_limits_met=(
                        max(lengths) <= SAMPLED_LIMITS["sampled_length_max_m"]
                        and max(curvature) <= SAMPLED_LIMITS["sampled_curvature_max_per_m"]
                        and cc >= SAMPLED_LIMITS["sampled_coil_distance_min_m"]
                        and cp >= SAMPLED_LIMITS["sampled_surface_distance_min_m"]),
                    geometry_certified=False)

    def unit_flux(self):
        phi = float(np.mean(np.sum(self.loop_field.A()*self.loop_tangent, axis=1)))
        if (not np.isfinite(phi) or abs(phi) <= 1e-12
                or np.sign(phi) != np.sign(self.seed["seed_unit_flux"])):
            raise ValueError("unit flux degenerate or orientation reversed")
        return phi

    def evaluate(self, x):
        from fusion_baselines.boundary_control_metrics import boundary_metrics

        self.set_x(x)
        phi, q = self.unit_flux(), float(self.objective.J())
        if q <= 1e-10:
            raise ValueError("native SquaredFlux dJ truncation region")
        if self.flux_objective == "local":
            dq = canonical_gradient(self.curves, self.objective.dJ(partials=True), self.order)
            value, gradient = q / self.area, dq / self.area
        else:
            # Acceptance v2 scores the plain per-point mean of |B.n|/|B|; minimize 0.5 m^2 with
            # m the smoothed per-point mean, so the scale stays comparable to the local flux term.
            B = self.field.B()
            normals = self.normals.reshape(-1, 3)
            unit = normals/np.linalg.norm(normals, axis=1)[:, None]
            strength = np.linalg.norm(B, axis=1)
            e = np.sum(B*unit, axis=1)/strength
            smooth = np.sqrt(e**2 + MEAN_ABS_EPSILON**2)
            m = float(np.mean(smooth))
            dm_de = e/smooth/len(e)
            dB = m*dm_de[:, None]*(unit/strength[:, None] - e[:, None]*B/strength[:, None]**2)
            value = .5*m*m
            gradient = canonical_gradient(self.curves, self.field.B_vjp(dB), self.order)
        flux_value = value
        penalty = float(self.geometry.J())
        gradient += canonical_gradient(self.curves, self.geometry.dJ(partials=True), self.order)
        scale = self.seed["target_flux"]/phi
        metrics = boundary_metrics(scale*self.field.B().reshape(self.points.shape), self.normals)
        metrics["selection_value"] = (metrics["normal_rms"] if self.flux_objective == "local"
                                      else float(value))
        if self.interior is not None:
            # 0.5 mean |s B - B_target|^2 / B2 at the flux-normalizing scale s = target/phi(x),
            # differentiated through s like #12; the boundary term is scale-invariant.
            unit = self.interior_field.B().copy()
            b2, count = self.seed["B2_scale"], len(unit)
            residual = scale*unit - self.interior["target"]
            interior = .5*float(np.mean(np.sum(residual**2, axis=1)))/b2
            weights = self.interior_weight*residual/(count*b2)
            contraction = float(np.sum(weights*unit))
            derivative = (self.interior_field.B_vjp(scale*weights)
                          - (scale*contraction/phi)*self.loop_field.A_vjp(
                              self.loop_tangent/len(self.loop_tangent)))
            value += self.interior_weight*interior
            gradient += canonical_gradient(self.curves, derivative, self.order)
            metrics.update(interior_objective=self.interior_weight*interior,
                           interior_objective_rms=float(np.sqrt(2*interior)),
                           selection_value=float(value))
        metrics.update(self.geometry_metrics(), flux_objective=float(flux_value),
                       flux_normalized_raw=metrics["raw_quadratic_flux"]
                       / (self.area*self.seed["B2_scale"]),
                       geometry_penalty=penalty,
                       scale=scale, unit_flux=phi, current=1e5*scale,
                       current_limit_met=abs(1e5*scale) <= SAMPLED_LIMITS["current_max_A"])
        if not np.isfinite(value+penalty) or not np.isfinite(gradient).all():
            raise ValueError("nonfinite objective or gradient")
        return float(value+penalty), gradient, metrics


def fine(seed, data, chosen, record, shift):
    from fusion_baselines.boundary_control_metrics import boundary_metrics
    from fusion_baselines.coupled_coil_audit import filament_field_and_potential, physical_curves

    record.guard()
    record.save(f"fine-{shift}-attempt.json", dict(selected_index=chosen["index"], shift=shift))
    model = Model(seed, data, record, n=128, ncoil=512, offset=shift)
    model.set_x(chosen["x"])
    scale = chosen["metrics"]["scale"]

    def sample(field, points, name):
        blocks = []
        try:
            for first in range(0, len(points), 128):
                field.set_points(np.ascontiguousarray(points[first:first+128]))
                blocks.append(scale*getattr(field, name)().copy())
        finally:
            field.set_points(points)
        return np.concatenate(blocks)

    points = model.points.reshape(-1, 3)
    B = sample(model.field, points, "B")
    A = sample(model.loop_field, model.loop_points, "A")
    snapshot = copy.deepcopy(seed)
    snapshot.update(base_coefficients=np.asarray(chosen["x"]).reshape(6, 3, -1).tolist(),
                    scale=scale, unit_flux=chosen["metrics"]["unit_flux"])
    for row in snapshot["physical"]:
        row["current"] = 1e5*scale*(-1 if row["flip"] else 1)
    own = physical_curves(snapshot, 512)
    bi, ai = np.linspace(0, len(points)-1, 64, dtype=int), np.linspace(0, 511, 64, dtype=int)
    own_B, own_A = record.call("independent_BA", filament_field_and_potential,
                               np.concatenate((points[bi], model.loop_points[ai])),
                               own["positions"], own["tangents"], own["currents"])
    errors = {name: float(np.max(np.linalg.norm(a-b, axis=1)
                                / np.maximum(1., np.linalg.norm(b, axis=1))))
              for name, a, b in (("B", own_B[:64], B[bi]), ("A", own_A[64:], A[ai]))}
    metrics = boundary_metrics(B.reshape(model.points.shape), model.normals)
    measured_flux = float(np.mean(np.sum(A*model.loop_tangent, axis=1)))
    metrics.update(model.geometry_metrics(), current=1e5*scale, frozen_scale=scale,
                   current_limit_met=abs(1e5*scale) <= 500000, measured_flux=measured_flux,
                   flux_relative_error=abs(measured_flux/seed["target_flux"]-1),
                   normal_limit_met=metrics["normal_rms"] <= 1e-4,
                   normal_max_limit_met=metrics["normal_max"] <= 1e-3)
    metrics["flux_limit_met"] = metrics["flux_relative_error"] <= 1e-6
    record.guard()
    buffer = io.BytesIO()
    np.savez_compressed(buffer, points=points, normals=model.normals, B=B, A=A,
                        loop_points=model.loop_points, loop_tangent=model.loop_tangent,
                        positions=own["positions"], tangents=own["tangents"],
                        currents=own["currents"], B_indices=bi, A_indices=ai,
                        independent_B=own_B[:64], independent_A=own_A[64:])
    record.guard()
    record.save(f"fine-{shift}.npz", buffer.getvalue())
    row = dict(shift=shift, n=128, nodes=512, metrics=metrics, independent_errors=errors,
               checks_pass=max(errors.values()) <= 1e-12,
                arrays_sha256=hashlib.sha256(buffer.getvalue()).hexdigest(),
                physical_admission=False)
    record.save(f"fine-{shift}.json", row)
    record.save("selected-snapshot.json", snapshot)
    record.guard()
    if not row["checks_pass"]:
        raise ValueError("independent fine B/A mismatch; outputs retained")
    return row


def search(model, record, minimize):
    """One wall-clock-limited search; probes and incomplete points cannot win."""
    initial = model.x0.copy()
    # Synthetic test models carry no margins; real models record their preset.
    selection = selection_settings(getattr(model, "margins", margin_preset())["name"])
    selected, completed, checks, startup = None, 0, [], False
    started, search_started = time.monotonic(), None
    largest_value = 0.
    x_refs = {}

    def stored(row, refs):
        """On-disk record: vectors are referenced in the store, never repeated inline."""
        return {**{k: v for k, v in row.items() if k not in ("x", "gradient")}, **refs}
    record.limit = MAX_BYTES - CHECK_STORAGE_RESERVE
    last_search_row, solver_iterations = None, 0

    def evaluate(x, role):
        nonlocal selected, completed, largest_value, last_search_row
        record.guard()
        index = record.bundles
        record.bundles += 1
        record.active = dict(bundle=index, role=role)
        attempt_started = time.monotonic()
        row = dict(index=index, role=role, x=np.asarray(x).tolist(), status="attempted",
                   search_elapsed_start_s=None if search_started is None
                   else attempt_started-search_started)
        refs = dict(x_ref=record.vector(row["x"]))
        x_refs[index] = refs["x_ref"]
        record.save(f"trial-{index:05}-attempt.json", stored(row, refs))
        evaluation_started = time.monotonic()
        try:
            value, gradient, metrics = model.evaluate(x)
            record.guard()
            row.update(value=value, gradient=gradient.tolist(), metrics=metrics, status="completed")
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            if role != "search" or not isinstance(exc, (ValueError, FloatingPointError)):
                raise
            # Reject numerical trial failures; resource and programming errors remain fatal.
            # Stay above every completed value, including the line search's starting point.
            rejected_value = largest_value + max(1., abs(largest_value))
            row.update(rejected_value=rejected_value)
        finally:
            # Interrupts retain the attempt only, never a fabricated terminal result.
            if row["status"] != "attempted":
                evaluation_finished = time.monotonic()
                row.update(elapsed_s=evaluation_finished-evaluation_started,
                           elapsed_scope=EVALUATION_COST_SCOPE,
                           search_elapsed_end_s=None if search_started is None
                           else evaluation_finished-search_started)
                if "gradient" in row:
                    refs["gradient_ref"] = record.vector(row["gradient"])
                record.save(f"trial-{index:05}.json", stored(row, refs))
        record.guard()
        if role == "search":
            last_search_row = row
        if row["status"] == "failed":
            return rejected_value, np.zeros_like(initial)
        largest_value = max(largest_value, value)
        completed += 1
        if (role in ("startup-seed", "search") and metrics["sampled_geometry_limits_met"]
                and metrics["current_limit_met"]
                and max(metrics["lengths"]) <= selection["length_max_m"]
                and (selected is None or metrics.get("selection_value", metrics["normal_rms"])
                     < selected["metrics"].get("selection_value",
                                               selected["metrics"]["normal_rms"]))):
            selected = row
        return value, gradient

    def accepted_iterate(xk):
        nonlocal solver_iterations
        record.guard()
        callback_elapsed = time.monotonic()-search_started
        # Link only exact coordinates from the latest returned search evaluation. Do not
        # reevaluate, guess a cached evaluation, or call other trials line-search rejections.
        linked = last_search_row is not None and np.array_equal(xk, last_search_row["x"])
        x_ref = (x_refs[last_search_row["index"]] if linked
                 else record.vector(np.asarray(xk).tolist()))
        record.save(f"iterate-{solver_iterations:05}.json", dict(
            format=RECORDING_FORMAT, iteration=solver_iterations, x_ref=x_ref,
            evaluation_index=last_search_row["index"] if linked else None,
            link_status="exact_latest_evaluation" if linked else "unknown",
            solver_step_status="accepted", search_elapsed_s=callback_elapsed,
            physical_admission=False))
        solver_iterations += 1
        record.guard()

    try:
        value, gradient = evaluate(initial, "startup-seed")
        for label, function in (("sin", np.sin), ("cos", np.cos)):
            direction = function(np.arange(len(initial))+1)
            direction /= np.linalg.norm(direction)
            analytic = float(gradient@direction)
            for h in PROBE_STEPS:
                fd = (evaluate(initial+h*direction, "probe")[0]
                      - evaluate(initial-h*direction, "probe")[0])/(2*h)
                error = abs(fd-analytic)
                if not np.isfinite([fd, analytic, error]).all():
                    raise ValueError("nonfinite startup derivative")
                checks.append(dict(direction=label, h=h, analytic=analytic, fd=fd,
                    error=error, passed=error <= 1e-7
                    or error <= 1e-4*max(abs(fd), abs(analytic))))
        repeat, repeated_gradient = evaluate(initial, "startup-repeat")
        startup = (repeat == value and np.array_equal(gradient, repeated_gradient)
                   and all(row["passed"] for row in checks))
        if not startup:
            raise ValueError("startup derivative or exact-repeat check failed")
        search_started = time.monotonic()
        solved = minimize(lambda x: evaluate(x, "search"), initial, jac=True,
                          method="L-BFGS-B", options=SOLVER_OPTIONS.copy(),
                          callback=accepted_iterate)
        record.guard()
        status = dict(reason="solver-return", success=bool(solved.success),
                      message=str(solved.message))
    except StorageLimit as exc:
        # Like the time budget: stop searching, keep every record and the selection.
        status = dict(reason="storage", error=str(exc))
    except TimeoutError as exc:
        status = dict(reason="budget", error=str(exc))
    except Exception as exc:
        status = dict(reason="failure", error=f"{type(exc).__name__}: {exc}")
    finally:
        record.limit = None  # Checks may use the reserved allowance.
    model.set_x(initial if selected is None else np.asarray(selected["x"]))
    return dict(status=status, startup_pass=startup, derivative_checks=checks,
                recording_format=RECORDING_FORMAT, solver_iterations_recorded=solver_iterations,
                solver_options=SOLVER_OPTIONS.copy(),
                startup_s=(search_started if search_started is not None else time.monotonic())
                - started,
                search_s=0 if search_started is None else time.monotonic()-search_started,
                bundles_attempted=record.bundles, bundles_completed=completed,
                selected=selected, physical_admission=False)
