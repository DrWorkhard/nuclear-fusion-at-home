"""Normalized six-coil fitting with headroom; selection is never acceptance."""

import copy
import functools
import hashlib
import io
import json
import shutil
import time

import numpy as np

MAX_BYTES, START_RESERVE, LIVE_RESERVE = 256*1024**2, 3*1024**3, 2*1024**3
PROBE_STEPS = (1.25e-6, 6.25e-7)
SOLVER_OPTIONS = dict(maxiter=2**31-1, maxfun=2**31-1, maxls=20, ftol=0., gtol=1e-9)


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


def names():
    return [
        name for axis in "xyz" for name in
        [f"{axis}c(0)"] + [f"{axis}{kind}({m})" for m in range(1, 6) for kind in "sc"]
    ]


def canonical_gradient(curves, derivative):
    result = []
    for curve in curves:
        labels = list(curve.local_dof_names)
        if list(curve.local_full_dof_names) != names() or sorted(labels) != sorted(names()):
            raise ValueError("complete named order-five free coordinates required")
        values = np.asarray(derivative(curve), dtype=float)
        if values.shape != (33,) or not np.isfinite(values).all():
            raise ValueError("finite named local gradient required")
        result.extend(values[[labels.index(name) for name in names()]])
    if len(result) != 198:
        raise ValueError("six base curves required")
    return np.asarray(result)


class Recorder:
    def __init__(self, output, deadline, storage=None):
        self.output, self.deadline = output, deadline
        self.output.mkdir(parents=True, exist_ok=False)
        self.counts = {name: dict(attempted=0, completed=0)
                       for name in ("B", "A", "B_vjp", "A_vjp", "independent_B", "independent_BA")}
        self.bundles, self.bytes, self.active = 0, 0, None
        self.storage = [0] if storage is None else storage

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
        if self.storage[0]+len(payload) > MAX_BYTES:
            raise OSError("256 MiB aggregate output ceiling including temporary publication")
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
    def __init__(self, seed, data, record, ncoil=256, n=64, offset=0):
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
        self.x0 = np.asarray(seed["base_coefficients"]).ravel()
        expected = [f"coil[{i}]/{name}" for i in range(6) for name in names()]
        if seed["names"] != expected or self.x0.shape != (198,):
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
        self.curves = [CurveXYZFourier(ncoil, 5) for _ in range(6)]
        self.set_x(self.x0)
        currents = [Current(1e5) for _ in range(6)]
        for current in currents:
            current.fix_all()
        self.coils = coils_via_symmetries(self.curves, currents, 2, True)
        self.field = tracked_field(BiotSavart, self.coils, record)
        self.loop_field = tracked_field(BiotSavart, self.coils, record)
        self.loop_points, self.loop_tangent = loop_geometry(data, ncoil)
        self.loop_field.set_points(self.loop_points)
        self.objective = SquaredFlux(
            self.surface, self.field, definition="local",
            threshold=0.0)
        physical = [c.curve for c in self.coils]
        self.lengths = [CurveLength(c) for c in self.curves]
        self.cc = CurveCurveDistance(physical, 0.07, num_basecurves=24)
        self.cp = SparseCurveSurfaceDistance(
            physical, geometry_surface.gamma().reshape(-1, 3),
            geometry_surface.normal().reshape(-1, 3), minimum_distance=0.09)
        self.geometry = (sum(QuadraticPenalty(term, 3.44, "max") for term in self.lengths)
                         + 1000*self.cc + 1000*self.cp
                         + 1e-2*sum(LpCurveCurvature(c, 2, threshold=10) for c in self.curves))

        from fusion_baselines.coupled_coil_audit import physical_curves

        own = physical_curves(seed, ncoil)
        self.identity_error = max(float(np.max(abs(np.asarray([getattr(c, method)()
            for c in physical])-own[key]))) for method, key in
            (("gamma", "positions"), ("gammadash", "tangents")))
        if self.identity_error > 1e-12:
            raise ValueError("native/independent initial physical coil mapping differs")

    def set_x(self, x):
        x = np.asarray(x, dtype=float)
        if x.shape != (198,) or not np.isfinite(x).all():
            raise ValueError("finite named 198-vector required")
        for curve, row in zip(self.curves, x.reshape(6, 33), strict=True):
            if list(curve.local_full_dof_names) != names():
                raise ValueError("native physical coordinate order changed")
            curve.local_full_x = row.copy()

    def geometry_metrics(self):
        lengths = [float(j.J()) for j in self.lengths]
        curvature = [float(np.max(c.kappa())) for c in self.curves]
        cc, cp = float(self.cc.shortest_distance()), float(self.cp.shortest_distance())
        return dict(lengths=lengths, kappa_max=curvature, coil_distance=cc, surface_distance=cp,
                    sampled_geometry_limits_met=max(lengths) <= 3.5 and max(curvature) <= 12
                    and cc >= 0.06 and cp >= 0.08, geometry_certified=False)

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
        dq = canonical_gradient(self.curves, self.objective.dJ(partials=True))
        value, gradient = q / self.area, dq / self.area
        penalty = float(self.geometry.J())
        gradient += canonical_gradient(self.curves, self.geometry.dJ(partials=True))
        scale = self.seed["target_flux"]/phi
        metrics = boundary_metrics(scale*self.field.B().reshape(self.points.shape), self.normals)
        metrics.update(self.geometry_metrics(), flux_objective=float(value),
                       flux_normalized_raw=metrics["raw_quadratic_flux"]
                       / (self.area*self.seed["B2_scale"]),
                       geometry_penalty=penalty,
                       scale=scale, unit_flux=phi, current=1e5*scale,
                       current_limit_met=abs(1e5*scale) <= 500000)
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
    snapshot.update(base_coefficients=np.asarray(chosen["x"]).reshape(6, 3, 11).tolist(),
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
    selected, completed, checks, startup = None, 0, [], False
    started, search_started = time.monotonic(), None
    largest_value = 0.

    def evaluate(x, role):
        nonlocal selected, completed, largest_value
        record.guard()
        index = record.bundles
        record.bundles += 1
        record.active = dict(bundle=index, role=role)
        row = dict(index=index, role=role, x=np.asarray(x).tolist(), status="attempted")
        record.save(f"trial-{index:05}-attempt.json", row)
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
            record.save(f"trial-{index:05}.json", row)
        record.guard()
        if row["status"] == "failed":
            return rejected_value, np.zeros_like(initial)
        largest_value = max(largest_value, value)
        completed += 1
        if (role in ("startup-seed", "search") and metrics["sampled_geometry_limits_met"]
                and metrics["current_limit_met"] and max(metrics["lengths"]) <= 3.45
                and (selected is None or metrics["normal_rms"]
                     < selected["metrics"]["normal_rms"])):
            selected = row
        return value, gradient

    try:
        value, gradient = evaluate(initial, "startup-seed")
        for label, function in (("sin", np.sin), ("cos", np.cos)):
            direction = function(np.arange(198)+1)
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
                          method="L-BFGS-B", options=SOLVER_OPTIONS.copy())
        record.guard()
        status = dict(reason="solver-return", success=bool(solved.success),
                      message=str(solved.message))
    except TimeoutError as exc:
        status = dict(reason="budget", error=str(exc))
    except Exception as exc:
        status = dict(reason="failure", error=f"{type(exc).__name__}: {exc}")
    model.set_x(initial if selected is None else np.asarray(selected["x"]))
    return dict(status=status, startup_pass=startup, derivative_checks=checks,
                solver_options=SOLVER_OPTIONS.copy(),
                startup_s=(search_started if search_started is not None else time.monotonic())
                - started,
                search_s=0 if search_started is None else time.monotonic()-search_started,
                bundles_attempted=record.bundles, bundles_completed=completed,
                selected=selected, physical_admission=False)
