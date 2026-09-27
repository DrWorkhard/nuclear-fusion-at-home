"""Bounded nonconvex local-normalized fits on saved six-current responses."""

import argparse
import hashlib
import io
import json
import shutil
import time
from pathlib import Path

import explore_independent_currents as current
import numpy as np

from fusion_baselines.boundary_control_metrics import boundary_metrics
from fusion_baselines.provenance import git_state, sha256_file

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = "artifacts/independent-currents-v1/run/"
RESULT = PREVIOUS+"result.json"
BASIS = {
    "n6-circle-d100mm": "a41fdcc029b2ed7169cfb7e42514202316004ce0c73581a70cb72e1db1be7676",
    "n6-shape-d100mm": "921ef7f266064cc3f7289f213ea8d5b1706c4eebdbe5ea56eeb376cd953fac6b",
}
INPUTS = {
    **current.INPUTS,
    RESULT: "54ce6a3f405e7f3f87d747c46937c574cfd23e0414809e5f2da83021861c7bf6",
    "scripts/explore_independent_currents.py":
        "511efdcc7190abd52c794d325112e659b4fd04fc0cf86e71d245cae05b8e0312",
    **{PREVIOUS+case+"-0-basis.npz": digest for case, digest in BASIS.items()},
}
SECONDS, BUNDLES, EQUALITY_TOL = 240, 400, 1e-10


class Response:
    def __init__(self, arrays, normalization):
        self.arrays, self.norm = arrays, normalization
        self.B, self.A = arrays["B"], arrays["A"]
        M, phi, c, weights, _, _ = current.quadratic_system(
            self.B, arrays["normals"], self.A, arrays["loop_tangent"],
            normalization["B2_scale"], normalization["target_flux"])
        for key, rebuilt in (("M", M), ("phi", phi), ("c", c), ("weights", weights)):
            if not np.allclose(arrays[key], rebuilt, rtol=1e-12, atol=1e-14):
                raise ValueError(f"stored basis reconstruction mismatch: {key}")
        self.M, self.c, self.phi, self.weights = M, c, phi, weights
        self.normal = arrays["normals"]/np.linalg.norm(arrays["normals"], axis=1)[:, None]

    def evaluate(self, q):
        q = np.asarray(q, dtype=float)
        if q.shape != (6,) or not np.isfinite(q).all() or np.any(abs(q) > 5):
            raise ValueError("six finite currents inside the unchanged box required")
        B = self.B@q
        magnitude = np.linalg.norm(B, axis=1)
        if np.any(magnitude <= 0) or not np.isfinite(magnitude).all():
            raise ValueError("zero or nonfinite field: local objective undefined")
        unit = B/magnitude[:, None]
        ratio = np.sum(self.normal*unit, axis=1)
        value = .5*float(self.weights@(ratio**2))
        covector = ((self.weights*ratio/magnitude)[:, None]
                    * (self.normal-ratio[:, None]*unit))
        gradient = np.einsum("ni,nij->j", covector, self.B)
        metrics = boundary_metrics(B, self.arrays["normals"])
        equality = abs(float(self.c@q)-1)
        metrics.update(local_objective=value, raw_objective=.5*float((self.M@q)@(self.M@q)),
                       equality_error=equality, measured_flux=float(self.phi@q),
                       max_abs_current=float(1e5*np.max(abs(q))), current_limit_met=True,
                       base_currents=(1e5*q).tolist(), base_reversed=np.flatnonzero(q < 0).tolist(),
                       flux_limit_met=equality <= 1e-6,
                       normal_limit_met=metrics["normal_rms"] <= 1e-4,
                       normal_max_limit_met=metrics["normal_max"] <= 1e-3,
                       selection_feasible=equality <= EQUALITY_TOL)
        if not np.isfinite(gradient).all() or not np.isclose(
                value, .5*metrics["normal_rms"]**2, rtol=1e-12, atol=1e-14):
            raise ValueError("local objective/gradient metric identity failed")
        return value, gradient, metrics


def projected_direction(c, function):
    direction = function(np.arange(6)+1)
    direction -= c*float(c@direction)/float(c@c)
    length = np.linalg.norm(direction)
    if not np.isfinite(length) or length <= 1e-12:
        raise ValueError("fixed flux-null directional probe is degenerate")
    return direction/length


def search(response, start, anchor, stem, save, guard, minimize):
    attempts, completed, best, probes, replay = 0, 0, None, [], {}
    startup_pass = False

    def evaluate(q, role):
        nonlocal attempts, completed, best
        guard()
        if attempts >= BUNDLES:
            raise StopIteration("400 total objective/gradient bundles consumed")
        index = attempts
        attempts += 1
        row = dict(index=index, role=role, q=np.asarray(q).tolist(), status="attempted")
        name = f"{stem}-trial-{index:03}"
        save(name+"-attempt.json", row)
        try:
            value, gradient, metrics = response.evaluate(q)
            row.update(value=value, gradient=gradient.tolist(), metrics=metrics, status="completed")
            guard()
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            save(name+".json", row, diagnostic=True)
            raise
        save(name+".json", row)
        guard()
        completed += 1
        if (role in ("seed", "search") and metrics["selection_feasible"]
                and (best is None or metrics["normal_rms"] < best["metrics"]["normal_rms"])):
            best = row
        return value, gradient

    try:
        value, gradient = evaluate(start, "seed")
        if best is None:
            raise ValueError("source-bound start is not equality/box feasible")
        seed_metrics = best["metrics"]
        keys = ("normal_rms", "normal_max", "min_b", "area_mean_b", "parameter_mean_b",
                "area_mean_abs_ratio", "raw_quadratic_flux", "local_flux", "raw_objective",
                "measured_flux")
        replay = {key: bool(np.isclose(seed_metrics[key], anchor[key], rtol=1e-10, atol=1e-12))
                  for key in keys}
        if not all(replay.values()):
            raise ValueError("source-bound native control/start metric replay failed")
        for label, function in (("sin", np.sin), ("cos", np.cos)):
            direction = projected_direction(response.c, function)
            derivative = float(gradient@direction)
            for h in (1e-5, 5e-6):
                fd = (evaluate(start+h*direction, "probe")[0]
                      - evaluate(start-h*direction, "probe")[0])/(2*h)
                error = abs(fd-derivative)
                probes.append(dict(direction=label, vector=direction.tolist(), h=h,
                                   analytic=derivative, finite_difference=fd, error=error,
                                   passed=error <= 1e-7 or
                                   error <= 1e-4*max(abs(fd), abs(derivative))))
        repeated, repeated_gradient = evaluate(start, "repeat")
        startup_pass = (repeated == value and np.array_equal(repeated_gradient, gradient)
                        and all(row["passed"] for row in probes))
        if not startup_pass:
            raise ValueError("directional derivative or exact-repeat check failed")
        guard()
        solved = minimize(lambda q: evaluate(q, "search"), start.copy(), jac=True, method="SLSQP",
                          bounds=[(-5., 5.)]*6, constraints=[dict(type="eq",
                          fun=lambda q: float(response.c@q)-1, jac=lambda q: response.c)],
                          options=dict(maxiter=200, ftol=1e-12))
        guard()
        status = dict(reason="solver-return", success=bool(solved.success),
                      message=str(solved.message), iterations=int(solved.nit),
                      objective_calls=int(solved.nfev), gradient_calls=int(solved.njev))
    except (TimeoutError, StopIteration) as exc:
        status = dict(reason="budget", error=str(exc))
    except Exception as exc:
        status = dict(reason="failure", error=f"{type(exc).__name__}: {exc}")
    return dict(status=status, startup_pass=startup_pass, startup_replay=replay,
                directional_checks=probes, attempted=attempts, completed=completed,
                selected=best, convex_optimality_claim=False, physical_admission=False)


def fine(snapshot, target, norm, q, shift, stem, save, guard, counts):
    from simsopt.field import BiotSavart

    from fusion_baselines.coupled_coil_audit import boundary, filament_field_and_potential, loop

    def call(name, function, *args):
        guard()
        counts[name]["attempted"] += 1
        value = function(*args)
        counts[name]["completed"] += 1
        guard()
        return value

    def sample(field, name, points):
        blocks = []
        for first in range(0, len(points), 128):
            field.set_points(np.ascontiguousarray(points[first:first+128]))
            blocks.append(call(name, getattr(field, name)).copy())
        return np.concatenate(blocks)

    guard()
    name = stem+f"-fine-{shift}"
    save(name+"-attempt.json", dict(q=q.tolist(), shift=shift))
    coils, own, identity = current.geometry_tools.native_coils(snapshot, 512)
    currents = current.set_currents(coils, q, snapshot)
    field = BiotSavart(coils)
    surface = boundary(target, 128, 128, shift=bool(shift))
    points, normals = surface["points"].reshape(-1, 3), surface["normal"].reshape(-1, 3)
    lp, tangent = loop(target, 512)
    B, A = sample(field, "B", points), sample(field, "A", lp)
    loop_B = sample(field, "B", lp)
    bi, ai = np.linspace(0, len(points)-1, 64, dtype=int), np.linspace(0, 511, 64, dtype=int)
    own_B, own_A = call("independent_BA", filament_field_and_potential,
                       np.concatenate((points[bi], lp[ai])), own["positions"],
                       own["tangents"], currents)
    errors = dict(B=current.geometry_tools.error(own_B[:64], B[bi]),
                  A=current.geometry_tools.error(own_A[64:], A[ai]),
                  loop_B=current.geometry_tools.error(own_B[64:], loop_B[ai]), **identity)
    buffer = io.BytesIO()
    np.savez_compressed(buffer, B=B, A=A, loop_B=loop_B, points=points, normals=normals,
                        loop_points=lp, loop_tangent=tangent, q=q, currents=currents,
                        positions=own["positions"], tangents=own["tangents"],
                        B_indices=bi, A_indices=ai, independent_B=own_B[:64],
                        independent_A=own_A[64:], independent_loop_B=own_B[64:])
    save(name+".npz", buffer.getvalue())
    metrics = boundary_metrics(B, normals)
    flux = float(np.mean(np.sum(A*tangent, axis=1)))
    metrics.update(local_objective=.5*metrics["normal_rms"]**2,
                   raw_objective=metrics["raw_quadratic_flux"]
                   / (metrics["mean_area_jacobian"]*norm["B2_scale"]),
                   measured_flux=flux, flux_relative_error=abs(flux/norm["target_flux"]-1),
                   max_abs_current=float(1e5*np.max(abs(q))), base_currents=(1e5*q).tolist(),
                   base_reversed=np.flatnonzero(q < 0).tolist(),
                   current_limit_met=bool(np.max(abs(q)) <= 5),
                   normal_limit_met=metrics["normal_rms"] <= 1e-4,
                   normal_max_limit_met=metrics["normal_max"] <= 1e-3)
    metrics["flux_limit_met"] = metrics["flux_relative_error"] <= 1e-6
    row = dict(q=q.tolist(), n=128, nodes=512, shift=shift, metrics=metrics, errors=errors,
               checks_pass=max(errors.values()) <= 1e-12, physical_admission=False,
               arrays_sha256=hashlib.sha256(buffer.getvalue()).hexdigest())
    save(name+".json", row)
    guard()
    if not row["checks_pass"]:
        raise ValueError("fine native/independent B/A/loop-B check failed")
    return row


def fingerprints():
    result = current.fingerprints()
    paths = [Path(__file__).resolve(), *(ROOT/name for name in INPUTS)]
    result.update({str(path): sha256_file(path) for path in paths})
    return result


def run(output):
    started = time.monotonic()
    if output.exists():
        raise FileExistsError("fresh output directory required")
    if shutil.disk_usage(ROOT).free < 3*1024**3:
        raise OSError("3 GiB starting reserve required")
    output.mkdir(parents=True)

    def guard():
        if time.monotonic()-started >= SECONDS:
            raise TimeoutError("240 s local-current worker ceiling")
        if shutil.disk_usage(output).free < 2*1024**3:
            raise OSError("2 GiB live reserve required")

    def save(name, value, diagnostic=False):
        current.save_output(output, name, value, guard, diagnostic=diagnostic)

    for name, digest in INPUTS.items():
        if sha256_file(ROOT/name) != digest:
            raise ValueError(f"source identity changed: {name}")
    source = {name: json.loads((ROOT/name).read_text(encoding="utf-8"))
              for name in INPUTS if name.endswith(".json")}
    previous = source[RESULT]
    if not previous["completed"] or not previous["sources_unchanged"]:
        raise ValueError("complete, source-stable previous current experiment required")
    counts = {name: dict(attempted=0, completed=0) for name in ("B", "A", "independent_BA")}
    report = dict(kind="local-six-current-exploration", sources_before=fingerprints(),
                  repository=git_state(ROOT), arms=[], counts=counts, completed=False,
                  normalization=previous["normalization"], basis_hashes=BASIS,
                  physical_admission=False, convex_optimality_claim=False, geometry_unchanged=True,
                  limits=dict(seconds=SECONDS, bundles_per_arm=BUNDLES, startup_bundles=10,
                              iterations=200, ftol=1e-12, equality_tolerance=EQUALITY_TOL,
                              output_bytes=current.MAX_BYTES))
    save("inputs.json", report)
    from scipy.optimize import minimize

    try:
        for case, digest in BASIS.items():
            case_rows = [r for r in previous["cases"] if r["case"] == case]
            if len(case_rows) != 1 or case_rows[0]["basis_sha256"] != digest:
                raise ValueError("case/basis association changed")
            with np.load(ROOT/(PREVIOUS+case+"-0-basis.npz"), allow_pickle=False) as stored:
                arrays = {key: stored[key].copy() for key in stored.files}
            if arrays["B"].shape != (4096, 3, 6) or arrays["A"].shape != (256, 3, 6):
                raise ValueError("fixed 64-square/256-node response basis required")
            response = Response(arrays, previous["normalization"])
            snapshot = source[current.geometry_tools.PREFIX+case+"/snapshot.json"]
            for start_name, qkey, old_label in (("equal", "control_q", "control"),
                                               ("raw-fit", "q", "fit")):
                guard()
                anchor = [r for r in previous["rows"] if
                          (r["case"], r["label"], r["n"], r["nodes"], r["shift"])
                          == (case, old_label, 64, 256, 0.)]
                if len(anchor) != 1 or not anchor[0]["checks_pass"]:
                    raise ValueError("unique source-bound native start replay required")
                start = np.asarray(case_rows[0][qkey], dtype=float)
                if not np.array_equal(start, anchor[0]["q"]):
                    raise ValueError("starting currents do not match their saved native replay")
                stem = case+"-"+start_name
                arm = dict(case=case, start=start_name, start_q=start.tolist(), fine=[],
                           geometry_reference=case_rows[0]["geometry_reference"])
                report["arms"].append(arm)
                arm.update(search(response, start, anchor[0]["metrics"], stem,
                                  save, guard, minimize))
                save(stem+"-search.json", arm)
                if arm["startup_pass"] and arm["selected"] is not None:
                    for shift in (0., .5):
                        arm["fine"].append(fine(snapshot, source[current.geometry_tools.TARGET],
                            previous["normalization"], np.asarray(arm["selected"]["q"]),
                            shift, stem, save, guard, counts))
                save(stem+"-result.json", arm)
        report["completed"] = all(r["startup_pass"] and len(r["fine"]) == 2
                                  and r["status"]["reason"] != "failure" for r in report["arms"])
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["sources_after"] = fingerprints()
    report["sources_unchanged"] = report["sources_before"] == report["sources_after"]
    report["elapsed_s"] = time.monotonic()-started
    report["completed"] &= report["sources_unchanged"] and report["elapsed_s"] < SECONDS
    code = current.publish_result(output, report, guard, started)
    print(json.dumps(dict(output=str(output), completed=report["completed"])))
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output.resolve()))
