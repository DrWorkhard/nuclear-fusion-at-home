"""Four bounded local-flux searches with stronger construction penalties.

The original physical gates are unchanged. Sampled-feasible selections are
exploratory candidates, not certified geometry or accepted fusion designs.
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

import explore_normalized_coils as common
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCREEN = "artifacts/coil-start-screen-v1/run/result.json"
GEOMETRY = "artifacts/clear-coil-initialization-v1/sets/"
CASES = ("n6-circle-d100mm", "n6-shape-d100mm")
INPUTS = {
    SCREEN: "6ef5c6c9824847e2eba6fbacc96c5abca3268032ff7760451f5b4d732132a89d",
    common.INPUT: common.HASHES[common.INPUT],
    "scripts/explore_normalized_coils.py":
        "9303dcbce1d1add0b4753db4ae087b384651ac0e2b7efa22447e3def17187781",
    GEOMETRY+CASES[0]+"/snapshot.json":
        "829ea3573b6e46771d771810420c0e378a07f4bb16363305376f4b6d39856de6",
    GEOMETRY+CASES[1]+"/snapshot.json":
        "90fe6f84395d319d45ac39fab832a2b3908f0d16d7638e971e2a4602a3ef65d1",
}
BUNDLES, ARM_SECONDS, OVERALL_SECONDS = 240, 300, 1800
BOX = .02


def fingerprints():
    result = common.fingerprints(ROOT)
    paths = [Path(__file__).resolve(), *(ROOT/p for p in INPUTS)]
    paths += [Path(importlib.import_module(m).__file__).resolve() for m in
              ("simsopt.geo.curve", "simsopt.field.magneticfield", "simsopt.objectives.utilities",
               "fusion_baselines.clear_coil_geometry_audit")]
    result.update({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    return result


def active_indices(mode):
    if mode not in ("full", "low2"):
        raise ValueError("full or low2 mode required")
    return np.array([i for i in range(198) if mode == "full" or i % 11 < 5], dtype=int)


def expand(values, original, indices):
    values = np.asarray(values, dtype=float)
    if (values.shape != indices.shape or not np.isfinite(values).all()
            or np.any(values < original[indices]-BOX)
            or np.any(values > original[indices]+BOX)):
        raise ValueError("finite active coordinates inside the original coefficient box required")
    full = original.copy()
    full[indices] = values
    return full


def magnetic_seed(geometry, report, case):
    from fusion_baselines.clear_coil_geometry_audit import validate_snapshot as geometry_valid
    from fusion_baselines.coupled_coil_audit import validate_snapshot

    geometry_valid(geometry)
    rows = [r for r in report["rows"] if (r["case"], r["n"], r["nodes"], r["shift"])
            == (case, 64, 256, 0.)]
    if (not report["completed"] or not report["sources_unchanged"] or len(rows) != 1
            or not rows[0]["checks_pass"] or geometry["case"]["label"] != case
            or geometry["sources"]["reference"]["input"]["sha256"] != INPUTS[common.INPUT]):
        raise ValueError("completed matched static geometry/field source required")
    metrics, norm = rows[0]["metrics"], report["normalization"]
    seed = {key: copy.deepcopy(geometry[key]) for key in
            ("schema_version", "nfp", "nbase", "order", "names", "base_coefficients", "physical")}
    seed.update(target_flux=norm["target_flux"], B2_scale=norm["B2_scale"],
                unit_flux=metrics["unit_flux"], seed_unit_flux=metrics["unit_flux"],
                scale=metrics["scale"])
    for row in seed["physical"]:
        row["current"] = 1e5*seed["scale"]*(-1 if row["flip"] else 1)
    validate_snapshot(seed)
    if metrics["base_current"] != 1e5*seed["scale"]:
        raise ValueError("source physical current differs from its fresh normalization")
    return seed, {key: metrics[key] for key in
                  ("unit_flux", "scale", "normal_rms", "flux_normalized_raw")}


class Model(common.Model):
    def __init__(self, seed, data, record, indices, **resolution):
        from simsopt.geo import CurveCurveDistance, LpCurveCurvature
        from simsopt.objectives import QuadraticPenalty

        from fusion_baselines.coupled_coil_audit import physical_curves
        from fusion_baselines.sparse_coil_surface import SparseCurveSurfaceDistance

        self.indices = indices
        super().__init__(seed, data, "local", record, **resolution)
        physical = [coil.curve for coil in self.coils]
        self.cc = CurveCurveDistance(physical, .07, num_basecurves=24)
        self.cp = SparseCurveSurfaceDistance(physical, self.cp.points, self.cp.normals,
                                            minimum_distance=.09)
        self.geometry = (sum(QuadraticPenalty(term, 3.5, "max") for term in self.lengths)
                         + 1000*self.cc + 1000*self.cp
                         + 1e-2*sum(LpCurveCurvature(c, 2, threshold=10) for c in self.curves))
        own = physical_curves(seed, resolution.get("ncoil", 256))
        self.identity_error = max(float(np.max(abs(np.asarray([getattr(c, method)()
            for c in physical])-own[key]))) for method, key in
            (("gamma", "positions"), ("gammadash", "tangents")))
        if self.identity_error > 1e-12:
            raise ValueError("native/independent initial physical coil mapping differs")

    def set_x(self, x):
        x = np.asarray(x, dtype=float)
        if (x.shape != (198,) or not np.array_equal(
                x, expand(x[self.indices], self.x0, self.indices))):
            raise ValueError("inactive coefficients must remain fixed at this start")
        for curve, row in zip(self.curves, x.reshape(6, 33), strict=True):
            if list(curve.local_full_dof_names) != common.names():
                raise ValueError("native named coefficient order changed")
            curve.local_full_x = row.copy()


def search(model, record, anchors, minimize):
    rows, best, feasible, checks, replay = [], None, None, [], {}
    initial = model.x0[model.indices].copy()

    def evaluate(values, role):
        nonlocal best, feasible
        record.guard()
        if record.bundles >= BUNDLES:
            raise StopIteration("240 total coarse bundles consumed")
        index = record.bundles
        record.bundles += 1
        record.active = dict(bundle=index, role=role)
        row = dict(index=index, role=role, active_values=np.asarray(values).tolist(),
                   status="attempted", native_before=copy.deepcopy(record.counts))
        record.save(f"trial-{index:03}-attempt.json", row)
        try:
            x = expand(values, model.x0, model.indices)
            row["x"] = x.tolist()
            value, gradient, metrics = model.evaluate(x)
            row.update(value=value, gradient=gradient.tolist(), metrics=metrics,
                       status="completed", deadline_met=time.monotonic() < record.deadline)
            record.guard()
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            row["native_after"] = copy.deepcopy(record.counts)
            record.save(f"trial-{index:03}.json", row)
        record.guard()
        rows.append(row)
        if role in ("startup-seed", "search"):
            if best is None or value < best["value"]:
                best = row
            if (metrics["sampled_geometry_limits_met"] and metrics["current_limit_met"]
                    and (feasible is None or metrics["normal_rms"]
                         < feasible["metrics"]["normal_rms"])):
                feasible = row
        return value, gradient[model.indices]

    startup_pass = False
    try:
        start_value, start_gradient = evaluate(initial, "startup-seed")
        replay = {key: dict(expected=value, actual=rows[0]["metrics"][key], passed=bool(
            np.isclose(value, rows[0]["metrics"][key], rtol=1e-10, atol=1e-12)))
            for key, value in anchors.items()}
        if not all(row["passed"] for row in replay.values()):
            raise ValueError("case-specific static seed replay failed")
        for label, function in (("sin", np.sin), ("cos", np.cos)):
            direction = function(np.arange(len(initial))+1)
            direction /= np.linalg.norm(direction)
            derivative = float(start_gradient@direction)
            for h in (1e-5, 5e-6):
                fd = (evaluate(initial+h*direction, "probe")[0]
                      - evaluate(initial-h*direction, "probe")[0])/(2*h)
                error = abs(fd-derivative)
                checks.append(dict(direction=label, h=h, analytic=derivative, fd=fd, error=error,
                                   passed=error <= 1e-7
                                   or error <= 1e-4*max(abs(fd), abs(derivative))))
        repeat, gradient = evaluate(initial, "startup-repeat")
        startup_pass = (repeat == start_value and np.array_equal(gradient, start_gradient)
                        and all(row["passed"] for row in checks))
        if not startup_pass:
            raise ValueError("directional derivative or exact-repeat check failed")
        result = minimize(lambda z: evaluate(z, "search"), initial, jac=True, method="L-BFGS-B",
                          bounds=list(zip(initial-BOX, initial+BOX, strict=True)),
                          options=dict(maxiter=230, maxfun=230, maxls=20, ftol=1e-12, gtol=1e-9))
        status = dict(reason="solver-return", success=bool(result.success),
                      message=str(result.message))
    except (TimeoutError, StopIteration) as exc:
        status = dict(reason="budget", error=str(exc))
    except Exception as exc:
        status = dict(reason="failure", error=f"{type(exc).__name__}: {exc}")
    chosen = feasible if feasible is not None else (rows[0] if rows else None)
    model.set_x(model.x0 if chosen is None else np.asarray(chosen["x"]))
    return dict(status=status, startup_pass=startup_pass, seed_replay=replay,
                derivative_checks=checks, bundles_attempted=record.bundles,
                bundles_completed=len(rows), lowest_objective=best, lowest_feasible_rms=feasible,
                fine_selected=chosen,
                fine_selection="sampled-feasible" if feasible else "seed-fallback",
                physical_admission=False)


def fine(seed, data, indices, chosen, record, shift):
    from fusion_baselines.boundary_control_metrics import boundary_metrics
    from fusion_baselines.coupled_coil_audit import filament_field_and_potential, physical_curves

    record.guard()
    record.save(f"fine-{shift}-attempt.json", dict(selected_index=chosen["index"], shift=shift))
    model = Model(seed, data, record, indices, n=128, ncoil=512, offset=shift)
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


def run(output):
    from scipy.optimize import minimize

    from fusion_baselines.provenance import git_state

    started = time.monotonic()
    if shutil.disk_usage(ROOT).free < common.START_RESERVE:
        raise OSError("3 GiB initial reserve required")
    for name, digest in INPUTS.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"fixed source changed: {name}")
    source = {name: json.loads((ROOT/name).read_text(encoding="utf-8"))
              for name in INPUTS if name.endswith(".json")}
    storage = [0]
    overall = common.Recorder(output, started+OVERALL_SECONDS, storage)
    report = dict(kind="constrained-coil-exploration", sources_before=fingerprints(),
                  repository=git_state(ROOT), arms=[], physical_admission=False,
                  limits=dict(bundles_per_arm=BUNDLES, startup_bundles=10,
                              search_seconds=ARM_SECONDS, overall_seconds=OVERALL_SECONDS,
                              output_bytes=common.MAX_BYTES, coefficient_box_m=BOX))
    overall.save("inputs.json", report)
    for case in CASES:
        seed, anchors = magnetic_seed(source[GEOMETRY+case+"/snapshot.json"], source[SCREEN], case)
        for mode in ("full", "low2"):
            label = case+"-"+mode
            deadline = min(started+OVERALL_SECONDS, time.monotonic()+ARM_SECONDS)
            record = common.Recorder(output/label, deadline, storage)
            record.counts["independent_BA"] = dict(attempted=0, completed=0)
            indices = active_indices(mode)
            result = dict(case=case, mode=mode, active_indices=indices.tolist(), fine=[],
                          active_names=[seed["names"][i] for i in indices], status="attempted")
            report["arms"].append(result)
            record.save("seed.json", seed)
            try:
                overall.guard()
                model = Model(seed, source[common.INPUT], record, indices)
                result["seed_identity_error"] = model.identity_error
                result.update(search(model, record, anchors, minimize))
                record.save("search.json", result)
                record.deadline = started+OVERALL_SECONDS
                if result["startup_pass"] and result["status"]["reason"] != "failure":
                    for shift in (0., .5):
                        record.active = dict(fine_shift=shift)
                        result["fine"].append(fine(seed, source[common.INPUT], indices,
                                                   result["fine_selected"], record, shift))
            except Exception as exc:
                result["execution_error"] = f"{type(exc).__name__}: {exc}"
            finally:
                result["counts"] = record.counts
                record.save("result.json", result)
                overall.save("progress.json", report)
    report["sources_after"] = fingerprints()
    report["sources_unchanged"] = report["sources_before"] == report["sources_after"]
    report["elapsed_s"] = time.monotonic()-started
    report["completed"] = (report["sources_unchanged"] and report["elapsed_s"] < OVERALL_SECONDS
                           and all(not r.get("execution_error") and r.get("startup_pass")
                                   and len(r["fine"]) == 2 for r in report["arms"]))
    overall.save("result.json", report)
    print(json.dumps(dict(output=str(output), completed=report["completed"])))
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output.resolve()))
