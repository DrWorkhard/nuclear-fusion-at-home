"""Two bounded exploratory Goodman coil fits; no physical acceptance decision.

Each arm has at most 80 coarse bundles INCLUDING ten startup bundles and 300s
for startup/search. Fine checks share the overall 900s limit; they freeze the
chosen coarse current. Run serially with one native thread and an external cap.
"""

import argparse
import copy
import hashlib
import importlib
import io
import json
import shutil
import time
from pathlib import Path

import numpy as np

SEED = ("artifacts/clear-coil-field-start-v1/reference-n6/operations/"
        "qualification-N-00-snapshot.json")
INPUT = "evidence/plasma-design-v2/reference-input-401.json"
REFERENCE = SEED.replace("-snapshot.json", ".json")
HASHES = {
    SEED: "4c29c1f7afb67f290bd3c7c2ec23829e5f386e7e8c299f8d40a0e0f4e2f03830",
    INPUT: "57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f",
    REFERENCE: "264f345594ed2effa987f836e3e3167623db233024bf454da917b0c129dcde8f",
}
SEED_ANCHORS = dict(unit_flux=-0.01065067732193652, scale=2.9496646632221735,
                    normal_rms=0.2760512774968315, flux_normalized_raw=0.039344660151591306)
MAX_BUNDLES, ARM_SECONDS, OVERALL_SECONDS = 80, 300, 900
MAX_BYTES, START_RESERVE, LIVE_RESERVE = 256 * 1024**2, 3 * 1024**3, 2 * 1024**3


def fingerprints(root):
    modules = ("simsoptpp", "simsopt.field.biotsavart", "simsopt.field.coil",
               "simsopt.geo.curvexyzfourier", "simsopt.geo.surfacerzfourier",
               "simsopt.geo.curveobjectives", "simsopt.objectives.fluxobjective",
               "simsopt._core.optimizable", "simsopt._core.derivative",
               "scipy.optimize._lbfgsb_py", "scipy.optimize._lbfgsb",
               "fusion_baselines.coupled_coils", "fusion_baselines.coupled_coil_audit",
               "fusion_baselines.filament_field", "fusion_baselines.curvature_bounds",
               "fusion_baselines.boundary_control_metrics", "fusion_baselines.sparse_coil_surface")
    paths = [Path(importlib.import_module(name).__file__).resolve() for name in modules]
    paths += [Path(__file__).resolve(), *(root / p for p in HASHES)]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


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


def combine_flux(arm, q, dq, area, b2, target, phi, dphi):
    """Analytic chain rule; local flux is invariant to the shared current scale."""
    if (arm not in ("raw", "local") or not np.isfinite([q, area, b2, target, phi]).all()
            or area <= 0 or b2 <= 0 or target == 0 or abs(phi) <= 1e-12
            or q < 0 or not np.isfinite(dq).all() or not np.isfinite(dphi).all()):
        raise ValueError("finite nondegenerate flux inputs required")
    if q <= 1e-10:
        raise ValueError("native SquaredFlux dJ truncation region; stop without zero gradient")
    if arm == "local":
        return q / area, dq / area
    value = (target / phi)**2 * q / (area * b2)
    return value, (target / phi)**2 * dq / (area * b2) - 2 * value / phi * dphi


class Recorder:
    def __init__(self, output, deadline, storage=None):
        self.output, self.deadline = output, deadline
        self.output.mkdir(parents=True, exist_ok=False)
        self.counts = {name: dict(attempted=0, completed=0)
                       for name in ("B", "A", "B_vjp", "A_vjp", "independent_B")}
        self.bundles, self.bytes, self.active = 0, 0, None
        self.storage = [0] if storage is None else storage

    def guard(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError("declared elapsed-time limit reached")
        if shutil.disk_usage(self.output).free < LIVE_RESERVE:
            raise OSError("live disk reserve exhausted")

    def save(self, name, value):
        payload = value if isinstance(value, bytes) else (
            json.dumps(value, allow_nan=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        path = self.output / name
        difference = len(payload) - (path.stat().st_size if path.exists() else 0)
        if self.storage[0] + len(payload) > MAX_BYTES:
            raise OSError("declared output-byte limit reached")
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(payload)
        temporary.replace(path)
        self.bytes += difference
        self.storage[0] += difference

    def call(self, name, function, *args):
        self.guard()
        self.counts[name]["attempted"] += 1
        self.save("progress.json",
                  dict(native=self.counts, bundles=self.bundles, active=self.active))
        answer = function(*args)
        self.counts[name]["completed"] += 1
        self.save("progress.json",
                  dict(native=self.counts, bundles=self.bundles, active=self.active))
        self.guard()
        return answer


def tracked_field(field_class, coils, record):
    class Tracked(field_class):
        def B(self):
            return record.call("B", super().B)

        def A(self):
            return record.call("A", super().A)

        def B_vjp(self, weights):
            return record.call("B_vjp", super().B_vjp, weights)

        def A_vjp(self, weights):
            return record.call("A_vjp", super().A_vjp, weights)
    return Tracked(coils)


class Model:
    def __init__(self, seed, data, arm, record, ncoil=256, n=64, offset=0):
        from simsopt.field import BiotSavart, Current, coils_via_symmetries
        from simsopt.geo import (
            CurveCurveDistance,
            CurveLength,
            CurveXYZFourier,
            LpCurveCurvature,
            SurfaceRZFourier,
        )
        from simsopt.objectives import QuadraticPenalty, SquaredFlux

        from fusion_baselines.coupled_coils import loop_geometry
        from fusion_baselines.sparse_coil_surface import SparseCurveSurfaceDistance

        self.seed, self.data, self.arm, self.record = seed, data, arm, record
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
            self.surface, self.field, definition="local" if arm == "local" else "quadratic flux",
            threshold=0.0)
        physical = [c.curve for c in self.coils]
        self.lengths = [CurveLength(c) for c in self.curves]
        self.cc = CurveCurveDistance(physical, 0.06, num_basecurves=24)
        self.cp = SparseCurveSurfaceDistance(
            physical, geometry_surface.gamma().reshape(-1, 3),
            geometry_surface.normal().reshape(-1, 3), minimum_distance=0.08)
        self.geometry = (sum(QuadraticPenalty(term, 3.5, "max") for term in self.lengths)
                         + 1000*self.cc + 1000*self.cp
                         + 1e-4*sum(LpCurveCurvature(c, 2, threshold=10) for c in self.curves))

    def set_x(self, x):
        x = np.asarray(x, dtype=float)
        if (x.shape != (198,) or not np.isfinite(x).all()
                or np.any(x < self.x0-0.01) or np.any(x > self.x0+0.01)):
            raise ValueError("finite 198-vector inside the fixed coefficient box required")
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
        dphi = (canonical_gradient(self.curves, self.loop_field.A_vjp(
            self.loop_tangent/len(self.loop_tangent))) if self.arm == "raw" else np.zeros(198))
        value, gradient = combine_flux(self.arm, q, dq, self.area, self.seed["B2_scale"],
                                      self.seed["target_flux"], phi, dphi)
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


def run_search(model, record, minimize):
    rows, best, checks, anchors = [], None, [], {}

    def evaluate(x, role):
        nonlocal best
        record.guard()
        if record.bundles >= MAX_BUNDLES:
            raise StopIteration("80 total coarse bundles consumed")
        index = record.bundles
        record.bundles += 1
        record.active = dict(bundle=index, role=role)
        row = dict(index=index, role=role, x=np.asarray(x).tolist(), status="attempted",
                   native_before=copy.deepcopy(record.counts))
        record.save(f"trial-{index:03}-attempt.json", row)
        value, gradient, metrics = model.evaluate(x)
        row.update(value=value, gradient=gradient.tolist(), metrics=metrics, status="completed",
                   native_after=copy.deepcopy(record.counts),
                   deadline_met=time.monotonic() < record.deadline)
        record.save(f"trial-{index:03}.json", row)
        rows.append(row)
        record.guard()
        if role in ("startup-seed", "search") and (best is None or value < best["value"]):
            best = row
        return value, gradient

    try:
        start_value, start_gradient = evaluate(model.x0, "startup-seed")
        anchors = {key: dict(expected=value, actual=rows[0]["metrics"][key],
                            passed=bool(np.isclose(rows[0]["metrics"][key], value,
                                                   rtol=1e-10, atol=1e-12)))
                   for key, value in SEED_ANCHORS.items()}
        if not all(row["passed"] for row in anchors.values()):
            raise ValueError("source-bound original seed replay failed")
        for label, function in (("sin", np.sin), ("cos", np.cos)):
            direction = function(np.arange(198)+1)
            direction /= np.linalg.norm(direction)
            analytic = float(start_gradient @ direction)
            for h in (1e-5, 5e-6):
                plus = evaluate(model.x0+h*direction, "startup-probe")[0]
                minus = evaluate(model.x0-h*direction, "startup-probe")[0]
                fd = (plus-minus)/(2*h)
                error = abs(fd-analytic)
                passed = error <= 1e-7 or error <= 1e-4*max(abs(fd), abs(analytic))
                checks.append(dict(direction=label, h=h, analytic=analytic, finite_difference=fd,
                                   error=error, passed=passed))
        repeat, gradient = evaluate(model.x0, "startup-repeat")
        repeated = repeat == start_value and np.array_equal(gradient, start_gradient)
        if not repeated or not all(row["passed"] for row in checks):
            raise ValueError("startup derivative or exact-repeat check failed")
        result = minimize(lambda x: evaluate(x, "search"), model.x0.copy(), jac=True,
                          method="L-BFGS-B", bounds=list(zip(model.x0-0.01, model.x0+0.01,
                                                            strict=True)),
                          options=dict(maxiter=70, maxfun=70, maxls=20, ftol=1e-12, gtol=1e-9))
        status = dict(reason="solver-return", success=bool(result.success),
                      message=str(result.message))
    except (StopIteration, TimeoutError) as error:
        status = dict(reason="budget", error=str(error))
    except Exception as error:
        status = dict(reason="failure", error=f"{type(error).__name__}: {error}")
    finally:
        model.set_x(model.x0 if best is None else np.asarray(best["x"]))
    startup_pass = (len(checks) == 4 and all(row["passed"] for row in checks)
                    and all(row["deadline_met"] for row in rows
                            if row["role"] != "search")) and any(
        row["role"] == "startup-repeat" and row["value"] == rows[0]["value"]
        and row["gradient"] == rows[0]["gradient"] for row in rows)
    return dict(status=status, startup_pass=startup_pass, derivative_checks=checks,
                seed_replay=anchors,
                bundles_attempted=record.bundles, bundles_completed=len(rows),
                selected=best, physical_admission=False)


def fine_endpoint(seed, data, arm, chosen, record, shift):
    from fusion_baselines.boundary_control_metrics import boundary_metrics
    from fusion_baselines.coupled_coil_audit import physical_curves
    from fusion_baselines.filament_field import filament_field

    record.guard()
    record.save(f"fine-{shift}-attempt.json", dict(shift=shift, selected_index=chosen["index"]))
    model = Model(seed, data, arm, record, ncoil=512, n=128, offset=shift)
    model.set_x(chosen["x"])
    scale = chosen["metrics"]["scale"]
    points = model.points.reshape(-1, 3)
    pieces = []
    try:
        for start in range(0, len(points), 128):
            model.field.set_points(points[start:start+128])
            pieces.append(scale*model.field.B().copy())
    finally:
        model.field.set_points(points)
    field = np.concatenate(pieces)
    metrics = boundary_metrics(field.reshape(model.points.shape), model.normals)
    phi = model.unit_flux()
    derived = copy.deepcopy(seed)
    derived.update(base_coefficients=np.asarray(chosen["x"]).reshape(6, 3, 11).tolist(),
                   scale=scale, unit_flux=chosen["metrics"]["unit_flux"])
    for row in derived["physical"]:
        row["current"] = 1e5*scale*(-1 if row["flip"] else 1)
    curves = physical_curves(derived, 512)
    indices = np.linspace(0, len(points)-1, 64, dtype=int)
    independent = record.call("independent_B", filament_field, points[indices],
                              curves["positions"], curves["tangents"], curves["currents"])
    error = float(np.max(np.linalg.norm(independent-field[indices], axis=1))
                  / max(1., float(np.max(np.linalg.norm(field[indices], axis=1)))))
    metrics.update(model.geometry_metrics(), current=1e5*scale, frozen_scale=scale,
                   current_limit_met=abs(1e5*scale) <= 500000,
                   target_flux=seed["target_flux"], measured_flux=scale*phi,
                   flux_relative_error=abs(scale*phi-seed["target_flux"])/abs(seed["target_flux"]),
                   independent_B_error=error, independent_B_pass=error <= 1e-12,
                   normal_limit_met=metrics["normal_rms"] <= 1e-4,
                   normal_max_limit_met=metrics["normal_max"] <= 1e-3,
                   physical_admission=False, inner_vector_checked=False)
    record.guard()
    buffer = io.BytesIO()
    np.savez_compressed(buffer, points=points, normals=model.normals, B=field,
                        independent_indices=indices, independent_B=independent)
    record.guard()
    record.save(f"fine-{shift}.npz", buffer.getvalue())
    result = dict(shift=shift, nphi=128, ntheta=128, ncoil=512, nloop=512, metrics=metrics,
                  arrays_sha256=hashlib.sha256(buffer.getvalue()).hexdigest())
    record.save(f"fine-{shift}.json", result)
    record.guard()
    if not metrics["independent_B_pass"]:
        raise ValueError("independent endpoint field crosscheck failed; outputs retained")
    return result


def main():
    from scipy.optimize import minimize

    from fusion_baselines.provenance import git_state

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    start, sources = time.monotonic(), {}
    if shutil.disk_usage(root).free < START_RESERVE:
        raise OSError("3 GiB starting reserve required")
    for name, digest in HASHES.items():
        raw = (root/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f"source hash mismatch: {name}")
        sources[name] = json.loads(raw)
    storage = [0]
    overall = Recorder(args.output, start+OVERALL_SECONDS, storage)
    summary = dict(kind="exploratory-normalized-coils", source_hashes=HASHES,
                   repository=git_state(root), simsopt=git_state(root/"external/simsopt"),
                   source_fingerprints_before=fingerprints(root),
                   limits=dict(total_coarse_bundles_per_arm=80, startup_bundles=10,
                               arm_search_seconds=300, overall_seconds=900, output_bytes=MAX_BYTES),
                   arms=[], physical_admission=False, step4_pass=False)
    overall.save("summary.json", summary)
    for arm in ("raw", "local"):
        recorder = Recorder(args.output/arm,
                            min(start+OVERALL_SECONDS, time.monotonic()+ARM_SECONDS), storage)
        result = dict(arm=arm, status="attempted", fine=[])
        summary["arms"].append(result)
        try:
            overall.guard()
            model = Model(sources[SEED], sources[INPUT], arm, recorder)
            result.update(run_search(model, recorder, minimize))
            recorder.save("search.json", result)
            recorder.deadline = start+OVERALL_SECONDS
            if (result["startup_pass"] and result["selected"] is not None
                    and result["status"]["reason"] != "failure"):
                for shift in (0, 0.5):
                    recorder.active = dict(fine_shift=shift)
                    result["fine"].append(fine_endpoint(
                        sources[SEED], sources[INPUT], arm, result["selected"], recorder, shift))
        except Exception as error:
            result["execution_error"] = f"{type(error).__name__}: {error}"
        finally:
            result.update(native_counts=recorder.counts,
                          output_bytes_before_result=recorder.bytes)
            recorder.save("result.json", result)
            overall.save("summary.json", summary)
    summary["source_fingerprints_after"] = fingerprints(root)
    summary["sources_unchanged"] = (summary["source_fingerprints_before"]
                                     == summary["source_fingerprints_after"])
    summary["elapsed_seconds"] = time.monotonic()-start
    summary["overall_deadline_met"] = summary["elapsed_seconds"] < OVERALL_SECONDS
    overall.save("summary.json", summary)
    print(json.dumps(dict(output=str(args.output),
                          arms=[a.get("status") for a in summary["arms"]])))
    return int(not summary["sources_unchanged"] or not summary["overall_deadline_met"]
               or any(a.get("execution_error") or not a.get("startup_pass")
                   or a["status"]["reason"] == "failure" for a in summary["arms"]))


if __name__ == "__main__":
    raise SystemExit(main())
