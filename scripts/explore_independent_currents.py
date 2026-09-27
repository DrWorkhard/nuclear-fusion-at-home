"""Fixed-geometry six-current convex exploration; no reactor-design acceptance."""

import argparse
import importlib
import io
import json
import shutil
import time
from pathlib import Path

import explore_coil_starts as geometry_tools
import numpy as np

from fusion_baselines.boundary_control_metrics import boundary_metrics
from fusion_baselines.provenance import git_state, sha256_file

ROOT = Path(__file__).resolve().parents[1]
SCREEN = "artifacts/coil-start-screen-v1/run/result.json"
CASES = ("n6-circle-d100mm", "n6-shape-d100mm")
INPUTS = {
    SCREEN: "6ef5c6c9824847e2eba6fbacc96c5abca3268032ff7760451f5b4d732132a89d",
    geometry_tools.TARGET: geometry_tools.INPUTS[geometry_tools.TARGET],
    "scripts/explore_coil_starts.py":
        "f587e81065c4e529bacc4f62d04051768026c19d19edcb548a7dbd9bc3bd2464",
    **{geometry_tools.PREFIX+case+"/snapshot.json": geometry_tools.CASES[case] for case in CASES},
}
SECONDS, MAX_BYTES, BOUND = 180, 64*1024**2, 5.
ACTIVE_TOL = 1e-8
KKT_TOLS = dict(equality=1e-10, box=1e-10, stationarity=1e-8,
                dual_sign=1e-10, complementarity=1e-9, duality_gap=1e-8)


def physical_currents(q, snapshot):
    q = np.asarray(q, dtype=float)
    if q.shape != (6,) or not np.isfinite(q).all():
        raise ValueError("six explicit finite base currents in 100 kA units required")
    return np.array([1e5*q[row["base_index"]]*(-1 if row["flip"] else 1)
                     for row in snapshot["physical"]])


def set_currents(coils, q, snapshot):
    expected = physical_currents(q, snapshot)
    for base in range(6):
        coils[base].current.local_full_x = np.array([1e5*q[base]])
    if not np.array_equal([coil.current.get_value() for coil in coils], expected):
        raise ValueError("native physical current mapping differs")
    return expected


def quadratic_system(B, normals, A, tangents, b2, target):
    B, normals, A, tangents = map(np.asarray, (B, normals, A, tangents))
    if (B.ndim != 3 or B.shape[1:] != (3, 6) or normals.shape != B.shape[:2]
            or A.ndim != 3 or A.shape[1:] != (3, 6) or tangents.shape != A.shape[:2]
            or not all(np.isfinite(x).all() for x in (B, normals, A, tangents))
            or not np.isfinite([b2, target]).all() or b2 <= 0 or target == 0):
        raise ValueError("complete finite six-column field/potential response required")
    area = np.linalg.norm(normals, axis=1)
    if not len(area) or np.any(area <= 0):
        raise ValueError("regular nonempty boundary normals required")
    weights = area/area.sum()
    M = np.einsum("ni,nij->nj", normals/area[:, None], B)*np.sqrt(weights/b2)[:, None]
    phi = np.mean(np.sum(A*tangents[:, :, None], axis=1), axis=0)
    c = phi/target
    if not np.isfinite(M).all() or not np.isfinite(c).all() or np.linalg.norm(c) == 0:
        raise ValueError("nondegenerate flux response required")
    _, _, vh = np.linalg.svd(c[None, :], full_matrices=True)
    nullspace = vh[1:].T
    singular = np.linalg.svd(M@nullspace, compute_uv=False)
    singular = np.pad(singular, (0, 5-len(singular)))
    tolerance = max(M.shape)*np.finfo(float).eps*singular[0]
    rank = int(np.sum(singular > tolerance))
    conditioning = dict(singular_values=singular.tolist(), rank=rank, rank_tolerance=tolerance,
                        condition_number=float(singular[0]/singular[-1]) if rank == 5 else None)
    return M, phi, c, weights, nullspace, conditioning


def kkt_certificate(M, c, q):
    """Independent first-order checks and a convex supporting-plane lower bound."""
    M, c, q = map(np.asarray, (M, c, q))
    if (M.ndim != 2 or M.shape[1] != 6 or c.shape != (6,) or q.shape != (6,)
            or not all(np.isfinite(x).all() for x in (M, c, q))):
        raise ValueError("finite six-current quadratic programme required")
    residual, g = M@q, M.T@(M@q)
    value = .5*float(residual@residual)
    lower, upper = q <= -BOUND+ACTIVE_TOL, q >= BOUND-ACTIVE_TOL
    free = ~(lower | upper)
    denominator = float(c[free]@c[free])
    if denominator > 0:
        multiplier = -float(c[free]@g[free])/denominator
    else:
        lo, hi = -np.inf, np.inf
        for i in np.flatnonzero(lower | upper):
            sign = 1 if lower[i] else -1
            a, b = sign*c[i], -sign*g[i]
            if a > 0:
                lo = max(lo, b/a)
            elif a < 0:
                hi = min(hi, b/a)
        multiplier = float(np.clip(0., lo, hi)) if lo <= hi else float((lo+hi)/2)
    r = g+multiplier*c
    alpha, beta = np.where(lower, r, 0.), np.where(upper, -r, 0.)
    scale = max(1., float(np.max(abs(g))), float(np.max(abs(multiplier*c))))
    dual_lower = value-float(g@q)-multiplier-BOUND*float(abs(r).sum())
    errors = dict(equality=abs(float(c@q)-1), box=max(0., float(np.max(abs(q)))-BOUND),
                  stationarity=float(np.max(abs(r-alpha+beta)))/scale,
                  dual_sign=max(0., float(-min(alpha.min(), beta.min())))/scale,
                  complementarity=max(float(np.max(abs(alpha*(q+BOUND)))),
                                      float(np.max(abs(beta*(BOUND-q)))))/scale,
                  duality_gap=abs(value-dual_lower)/max(1., abs(value)))
    return dict(passed=all(np.isfinite(v) and v <= KKT_TOLS[k] for k, v in errors.items()),
                errors=errors, tolerances=KKT_TOLS, active_tolerance=ACTIVE_TOL,
                equality_multiplier=multiplier, lower_multipliers=alpha.tolist(),
                upper_multipliers=beta.tolist(), lower_active=np.flatnonzero(lower).tolist(),
                upper_active=np.flatnonzero(upper).tolist(), objective=value,
                convex_lower_bound=dual_lower, interval_arithmetic=False,
                gap_interpretation="supporting-plane gap with numerical primal tolerance")


def polish_active_set(M, c, q, certificate):
    """One nonsingular linear solve; never change or regularize the active set."""
    lower, upper = certificate["lower_active"], certificate["upper_active"]
    active = np.array(lower+upper, dtype=int)
    free = np.setdiff1d(np.arange(6), active)
    result = dict(selected=False, lower_fixed=lower, upper_fixed=upper,
                  condition_ceiling=1/np.finfo(float).eps)
    if not len(free) or np.linalg.norm(c[free]) == 0:
        return dict(result, reason="no flux-bearing free coordinates")
    candidate = np.asarray(q).copy()
    candidate[lower], candidate[upper] = -BOUND, BOUND
    H = M.T@M
    K = np.block([[H[np.ix_(free, free)], c[free, None]],
                  [c[None, free], np.zeros((1, 1))]])
    rhs = np.r_[-H[np.ix_(free, active)]@candidate[active], 1-c[active]@candidate[active]]
    condition = float(np.linalg.cond(K))
    result["condition"] = condition if np.isfinite(condition) else None
    if not np.isfinite(condition) or condition >= result["condition_ceiling"]:
        return dict(result, reason="singular or numerically singular KKT system; no truncation")
    try:
        solution = np.linalg.solve(K, rhs)
    except np.linalg.LinAlgError as exc:
        return dict(result, reason=str(exc))
    candidate[free] = solution[:-1]
    checked = kkt_certificate(M, c, candidate)
    same = checked["lower_active"] == lower and checked["upper_active"] == upper
    return dict(result, q=candidate.tolist(), certificate=checked, same_active_set=same,
                linear_residual=float(np.max(abs(K@solution-rhs)))/max(1., float(np.max(abs(rhs)))),
                selected=bool(same and checked["passed"]), reason="one active-set linear solve")


def solve_qp(M, c, initial):
    from scipy.optimize import minimize

    if BOUND*float(abs(c).sum()) < 1:
        raise ValueError("flux equality infeasible in the declared current box")
    result = minimize(lambda q: .5*float((M@q)@(M@q)), initial,
                      jac=lambda q: M.T@(M@q), method="SLSQP", bounds=[(-BOUND, BOUND)]*6,
                      constraints=[dict(type="eq", fun=lambda q: float(c@q)-1, jac=lambda q: c)],
                      options=dict(maxiter=200, ftol=1e-14))
    raw = kkt_certificate(M, c, result.x)
    polish = (dict(selected=False, reason="raw point certifies") if raw["passed"]
              else polish_active_set(M, c, result.x, raw))
    q, checked = ((polish["q"], polish["certificate"]) if polish["selected"]
                  else (result.x.tolist(), raw))
    return dict(q=q, solver_success=bool(result.success), message=str(result.message),
                raw_q=result.x.tolist(), raw_certificate=raw, polish=polish,
                selected="active-set-polish" if polish["selected"] else "slsqp",
                solver_options=dict(method="SLSQP", maxiter=200, ftol=1e-14),
                iterations=int(result.nit), evaluations=int(result.nfev),
                gradient_evaluations=int(result.njev), certificate=checked)


def fingerprints():
    result = geometry_tools.fingerprints()
    paths = [Path(__file__).resolve(), *(ROOT/name for name in INPUTS)]
    paths += [Path(importlib.import_module(m).__file__).resolve() for m in
              ("scipy.optimize._slsqp_py", "scipy.optimize._slsqplib", "scipy.optimize._minimize")]
    result.update({str(path): sha256_file(path) for path in paths})
    return result


def save_output(output, name, value, guard, diagnostic=False):
    if not diagnostic:
        guard()
    payload = value if isinstance(value, bytes) else (
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True)+"\n").encode("utf-8")
    if sum(p.stat().st_size for p in output.iterdir())+len(payload) > MAX_BYTES:
        raise OSError("64 MiB output ceiling")
    if not diagnostic:
        guard()
    with (output/name).open("xb") as stream:
        if stream.write(payload) != len(payload):
            raise OSError("short output write; publication incomplete")
    if not diagnostic:
        guard()


def publish_result(output, report, guard, started):
    try:
        save_output(output, "result.json", report, guard)
        guard()
    except (TimeoutError, OSError) as exc:
        report.update(completed=False, publication_error=f"{type(exc).__name__}: {exc}",
                      elapsed_s=time.monotonic()-started)
        if (output/"result.json").exists():
            (output/"result.json").rename(output/"rejected-late-result.json")
        # Only failure diagnostics bypass the expired clock, never scientific work.
        marker = dict(completed=False, error=report["publication_error"],
                      elapsed_s=report["elapsed_s"])
        save_output(output, "late-publication.json", marker, guard, diagnostic=True)
        save_output(output, "result.json", report, guard, diagnostic=True)
    return 0 if report["completed"] else 1


def run(output):
    from simsopt.field import BiotSavart

    from fusion_baselines.coupled_coil_audit import boundary, filament_field_and_potential, loop

    started = time.monotonic()
    if output.exists():
        raise FileExistsError("fresh output directory required")
    if shutil.disk_usage(ROOT).free < 3*1024**3:
        raise OSError("3 GiB initial reserve required")
    output.mkdir(parents=True)
    counts = {key: dict(attempted=0, completed=0) for key in ("B", "A", "independent_BA")}

    def guard():
        if time.monotonic()-started >= SECONDS:
            raise TimeoutError("180 s worker ceiling")
        if shutil.disk_usage(output).free < 2*1024**3:
            raise OSError("2 GiB live reserve required")

    def save(name, value):
        save_output(output, name, value, guard)

    def arrays(name, **values):
        buffer = io.BytesIO()
        np.savez_compressed(buffer, **values)
        guard()
        save(name+".npz", buffer.getvalue())
        return sha256_file(output/(name+".npz"))

    def call(name, function, *args):
        guard()
        counts[name]["attempted"] += 1
        answer = function(*args)
        counts[name]["completed"] += 1
        guard()
        return answer

    def sample(field, name, points):
        blocks = []
        for first in range(0, len(points), 128):
            field.set_points(np.ascontiguousarray(points[first:first+128]))
            blocks.append(call(name, getattr(field, name)).copy())
        return np.concatenate(blocks)

    for name, digest in INPUTS.items():
        if sha256_file(ROOT/name) != digest:
            raise ValueError(f"fixed source changed: {name}")
    source = {name: json.loads((ROOT/name).read_text(encoding="utf-8"))
              for name in INPUTS if name.endswith(".json")}
    static = source[SCREEN]
    if not static["completed"] or not static["sources_unchanged"]:
        raise ValueError("completed source-stable static screen required")
    target, norm = source[geometry_tools.TARGET], static["normalization"]
    report = dict(kind="independent-six-base-currents", sources_before=fingerprints(),
                  repository=git_state(ROOT), cases=[], rows=[], counts=counts, completed=False,
                  current_names=[f"base[{i}]/current_100kA" for i in range(6)],
                  normalization=norm, physical_admission=False, geometry_unchanged=True,
                  new_geometry_certificate=False, pressure=False, loads=False)
    save("inputs.json", report)
    try:
        for case in CASES:
            snapshot = source[geometry_tools.PREFIX+case+"/snapshot.json"]
            controls = [r for r in static["rows"] if (r["case"], r["n"], r["nodes"], r["shift"])
                        == (case, 64, 256, 0.)]
            if (len(controls) != 1 or not controls[0]["checks_pass"]
                    or snapshot["case"]["label"] != case
                    or snapshot["sources"]["reference"]["input"]["sha256"]
                    != INPUTS[geometry_tools.TARGET]):
                raise ValueError("matched case and static control required")
            qcontrol = np.full(6, controls[0]["metrics"]["scale"])
            fit, basis_B, basis_A = None, None, None
            for level, (n, nodes, shift) in enumerate(geometry_tools.SCHEDULE):
                guard()
                stem = f"{case}-{level}"
                save(stem+"-attempt.json", dict(case=case, n=n, nodes=nodes, shift=shift))
                coils, own, identity = geometry_tools.native_coils(snapshot, nodes)
                field = BiotSavart(coils)
                surface = boundary(target, n, n, shift=bool(shift))
                points, normals = surface["points"].reshape(-1, 3), surface["normal"].reshape(-1, 3)
                lp, tangent = loop(target, nodes)
                if level == 0:
                    columns_B, columns_A = [], []
                    for q in np.eye(6):
                        set_currents(coils, q, snapshot)
                        columns_B.append(sample(field, "B", points))
                        columns_A.append(sample(field, "A", lp))
                    basis_B, basis_A = np.stack(columns_B, axis=-1), np.stack(columns_A, axis=-1)
                    M, phi, c, weights, Z, conditioning = quadratic_system(
                        basis_B, normals, basis_A, tangent, norm["B2_scale"], norm["target_flux"])
                    digest = arrays(stem+"-basis", B=basis_B, A=basis_A, points=points,
                                    normals=normals, loop_points=lp, loop_tangent=tangent,
                                    positions=own["positions"], tangents=own["tangents"],
                                    physical_currents=np.stack([physical_currents(q, snapshot)
                                                               for q in np.eye(6)], axis=-1),
                                    M=M, phi=phi, c=c, weights=weights, nullspace=Z)
                    guard()
                    solution = solve_qp(M, c, qcontrol)
                    guard()
                    fit = np.asarray(solution["q"])
                    solution.update(case=case, conditioning=conditioning, basis_sha256=digest,
                                    geometry_reference=controls[0]["existing_geometry_audit"],
                                    control_q=qcontrol.tolist())
                    save(case+"-qp.json", solution)
                    report["cases"].append(solution)
                choices = [("control", qcontrol), ("fit", fit)]
                if level == 0:
                    unequal = qcontrol*np.array([.8, .9, 1, 1.1, 1.2, 1.05])
                    choices.insert(1, ("unequal-linearity", unequal))
                for label, q in choices:
                    name = stem+"-"+label
                    save(name+"-attempt.json", dict(q=q.tolist(), case=case, label=label))
                    currents = set_currents(coils, q, snapshot)
                    B, A = sample(field, "B", points), sample(field, "A", lp)
                    bi = np.linspace(0, len(points)-1, 64, dtype=int)
                    ai = np.linspace(0, nodes-1, 64, dtype=int)
                    own_B, own_A = call("independent_BA", filament_field_and_potential,
                                       np.concatenate((points[bi], lp[ai])), own["positions"],
                                       own["tangents"], currents)
                    errors = dict(B=geometry_tools.error(own_B[:64], B[bi]),
                                  A=geometry_tools.error(own_A[64:], A[ai]), **identity)
                    if level == 0:
                        errors.update(linearity_B=geometry_tools.error(basis_B@q, B),
                                      linearity_A=geometry_tools.error(basis_A@q, A))
                    digest = arrays(name, B=B, A=A, points=points, normals=normals, loop_points=lp,
                                    loop_tangent=tangent, q=q, currents=currents,
                                    positions=own["positions"], tangents=own["tangents"],
                                    B_indices=bi, A_indices=ai, independent_B=own_B[:64],
                                    independent_A=own_A[64:])
                    metrics = boundary_metrics(B, normals)
                    flux = float(np.mean(np.sum(A*tangent, axis=1)))
                    contributions = phi*q
                    cancellation = (float(abs(contributions).sum()/abs(contributions.sum()))
                                    if contributions.sum() != 0 else None)
                    metrics.update(raw_objective=metrics["raw_quadratic_flux"]
                                   / (metrics["mean_area_jacobian"]*norm["B2_scale"]),
                                   measured_flux=flux,
                                   flux_relative_error=abs(flux/norm["target_flux"]-1),
                                   current_limit_met=bool(np.max(abs(q)) <= BOUND),
                                   normal_limit_met=metrics["normal_rms"] <= 1e-4,
                                   normal_max_limit_met=metrics["normal_max"] <= 1e-3,
                                   base_current_sum=float(1e5*q.sum()),
                                   base_reversed=np.flatnonzero(q < 0).tolist(),
                                   coarse_flux_contributions=contributions.tolist(),
                                   coarse_flux_cancellation=cancellation)
                    metrics["flux_limit_met"] = metrics["flux_relative_error"] <= 1e-6
                    row = dict(case=case, label=label, n=n, nodes=nodes, shift=shift,
                               metrics=metrics,
                               q=q.tolist(), errors=errors, arrays_sha256=digest,
                               checks_pass=max(errors.values()) <= 1e-12, physical_admission=False)
                    if level == 0 and label == "control":
                        row["control_replay"] = {key: bool(np.isclose(metrics[key],
                            controls[0]["metrics"][old], rtol=1e-10, atol=1e-12)) for key, old in
                            (("normal_rms", "normal_rms"), ("raw_objective", "flux_normalized_raw"),
                             ("measured_flux", "measured_flux"))}
                        row["checks_pass"] &= all(row["control_replay"].values())
                    if level == 0 and label == "fit":
                        row["objective_replay"] = bool(np.isclose(metrics["raw_objective"],
                            solution["certificate"]["objective"], rtol=1e-10, atol=1e-12))
                        row["checks_pass"] &= row["objective_replay"]
                    save(name+".json", row)
                    report["rows"].append(row)
                    guard()
                    if not row["checks_pass"]:
                        raise ValueError("field/linearity control failed; outputs retained")
                if not solution["certificate"]["passed"]:
                    raise ValueError("QP KKT certificate failed; no certified optimum claimed")
        guard()
        report["completed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["sources_after"] = fingerprints()
    report["sources_unchanged"] = report["sources_before"] == report["sources_after"]
    report["elapsed_s"] = time.monotonic()-started
    report["completed"] &= report["sources_unchanged"] and report["elapsed_s"] < SECONDS
    exit_code = publish_result(output, report, guard, started)
    print(json.dumps(dict(output=str(output), completed=report["completed"])))
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output.resolve()))
