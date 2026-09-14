"""Independent, fail-closed provenance and numerical audit of the paired coil pilot.

This auditor imports neither the native coil producer nor the optimization runner.
Archived independently qualified VMEC grids provide the immutable interior target.
Search accounting and scalar selection are reconstructed from every attempted call.
"""

import argparse
import json
import math
from pathlib import Path

import numpy as np
from coupled_coil_inputs import sources
from current_diagnostic_inputs import checked, reference

from fusion_baselines import coupled_coil_audit as independent
from fusion_baselines.provenance import git_state, write_json_atomic


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(ref):
    require(Path(ref["path"]).is_absolute(), "absolute immutable reference required")
    return json.loads(checked(ref).read_text())


def arrays(ref):
    require(Path(ref["path"]).is_absolute(), "absolute raw-array reference required")
    with np.load(checked(ref), allow_pickle=False) as archive:
        result = {key: archive[key].copy() for key in archive.files}
    require(
        all(np.isfinite(value).all() for value in result.values()), "finite raw arrays required"
    )
    return result


def bind_tree(value):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            require(Path(value["path"]).is_absolute(), "absolute provenance path required")
            checked(value)
        else:
            for item in value.values():
                bind_tree(item)
    elif isinstance(value, list):
        for item in value:
            bind_tree(item)


def close(actual, expected, label, rtol=5e-10, atol=1e-14):
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape, f"{label}: array shape mismatch")
    require(np.isfinite(actual).all() and np.isfinite(expected).all(), f"{label}: nonfinite")
    require(np.allclose(actual, expected, rtol=rtol, atol=atol), f"{label}: mismatch")


def relative_components(actual, expected, label):
    """Protocol's maximum-component relative metric, without an absolute escape."""
    actual, expected = np.asarray(actual), np.asarray(expected)
    require(actual.shape == expected.shape and actual.size > 0, f"{label}: shape")
    require(np.isfinite(actual).all() and np.isfinite(expected).all(), f"{label}: nonfinite")
    denominator = float(np.max(abs(expected)))
    require(denominator > 0, f"{label}: positive finite field scale required")
    error = float(np.max(abs(actual - expected)) / denominator)
    require(error <= 5e-10, f"{label}: direct field/potential error {error}")
    return error


def indices(size):
    require(type(size) is int and size >= 64, "at least64 field points required")
    return np.linspace(0, size - 1, 64, dtype=int)


def canonical_seed(nbase, order):
    require((nbase, order) in ((6, 5), (8, 7)), "registered coil class required")
    values = np.zeros((nbase, 3, 2 * order + 1))
    for i in range(nbase):
        angle = (i + 0.5) * (2 * np.pi) / (4 * nbase)
        values[i, 0, 0], values[i, 1, 0] = math.cos(angle), math.sin(angle)
        values[i, 0, 2], values[i, 1, 2] = 0.35 * math.cos(angle), 0.35 * math.sin(angle)
        values[i, 2, 1] = -0.35
    return values.ravel()


def qualification_coordinates(seed):
    k = np.arange(1, len(seed) + 1, dtype=float)
    direction = [v / np.linalg.norm(v) for v in (np.sin(k), np.cos(k))]
    return (
        [seed.copy()]
        + [seed + sign * step * d for d in direction for step in (1e-5, 5e-6) for sign in (1, -1)]
        + [seed.copy()]
    )


def derivative_audit(rows, seed, own_values=None):
    expected = qualification_coordinates(seed)
    require(len(rows) == 10, "all ten qualification bundles required")
    require(
        all(
            r.get("status") == "completed" and np.array_equal(r["x"], x)
            for r, x in zip(rows, expected, strict=True)
        ),
        "ordered qualification coordinates",
    )
    j = np.asarray([r["J"] for r in rows], dtype=float)
    gradient = np.asarray([r["gradient"] for r in rows], dtype=float)
    require(
        j.shape == (10,)
        and gradient.shape == (10, len(seed))
        and np.isfinite(j).all()
        and np.isfinite(gradient).all(),
        "finite qualification bundles",
    )
    own = j if own_values is None else np.asarray(own_values, dtype=float)
    require(own.shape == j.shape and np.isfinite(own).all(), "independent qualification objectives")
    results = []
    k = np.arange(1, len(seed) + 1, dtype=float)
    for i, v in enumerate((np.sin(k), np.cos(k))):
        analytic = float(gradient[0] @ (v / np.linalg.norm(v)))
        for q, step in enumerate((1e-5, 5e-6)):
            at = 1 + 4 * i + 2 * q
            for label, values in (("recorded", j), ("independent", own)):
                fd = float((values[at] - values[at + 1]) / (2 * step))
                error = abs(fd - analytic)
                relative = error / max(abs(fd), abs(analytic), 1e-30)
                results.append(
                    dict(
                        direction=i,
                        step=step,
                        objective=label,
                        analytic=analytic,
                        finite_difference=fd,
                        absolute_error=error,
                        relative_error=relative,
                        passed=bool(error <= 1e-8 or relative <= 2e-4),
                    )
                )
    repeat = bool(j[0] == j[-1] and np.array_equal(gradient[0], gradient[-1]) and own[0] == own[-1])
    return dict(
        rows=results, exact_repeat=repeat, passed=repeat and all(r["passed"] for r in results)
    )


def search_selection(rows, seed):
    require(isinstance(rows, list) and 1 <= len(rows) <= 128, "one to128 attempted bundles")
    require(np.array_equal(rows[0]["x"], seed), "first search attempt must be unperturbed seed")
    eligible = []
    for i, row in enumerate(rows):
        require(
            type(row.get("index")) is int and row["index"] == i, "contiguous attempt accounting"
        )
        x = np.asarray(row["x"], dtype=float)
        require(x.shape == seed.shape and np.isfinite(x).all(), "finite canonical attempted point")
        require(np.all(abs(x - seed) <= 0.12 + 2e-16), "registered coefficient box exceeded")
        require(
            row.get("status") in ("completed", "failed", "attempted"), "attempt status required"
        )
        if row["status"] == "completed":
            require(np.shape(row.get("J")) == () and np.isfinite(row["J"]), "finite completed J")
            gradient = np.asarray(row["gradient"], dtype=float)
            require(
                gradient.shape == seed.shape and np.isfinite(gradient).all(), "complete gradient"
            )
            eligible.append(i)
        else:
            require(
                i == len(rows) - 1, "failed/incomplete final attempt cannot be followed by work"
            )
            require("J" not in row or row["J"] is None, "no fabricated objective for failed call")
    require(bool(eligible), "at least one persisted completed search bundle required")
    return min(eligible, key=lambda i: (rows[i]["J"], i))


def bundle_work(row, *, attempted=True):
    if attempted:
        attempt = read(row["attempt"])
        require(
            attempt["index"] == row["index"]
            and attempt["status"] == "attempted"
            and np.array_equal(attempt["x"], row["x"]),
            "original immutable attempt identity",
        )
        require(np.isfinite(attempt["started_monotonic"]), "finite attempt timestamp")
    else:
        attempt = dict(started_monotonic=row["started_monotonic"])
    if row["status"] == "completed":
        start, finish, elapsed = [
            row[k] for k in ("started_monotonic", "completed_monotonic", "elapsed_seconds")
        ]
        require(
            np.isfinite([start, finish, elapsed]).all()
            and attempt["started_monotonic"] <= start <= finish
            and elapsed >= finish - start,
            "ordered complete bundle timing",
        )
        require(
            row["supplementary_field_work"]
            == dict(boundary_A_calls=1, inner_A_calls=1, loop_B_calls=1),
            "three separately counted supplementary field values",
        )
    return attempt


def search_clock(run):
    clock = run["search_clock"]
    require(
        clock["check_interval"] == 0.5
        and clock["timeout_seconds"] == 600
        and clock["termination_grace_seconds"] == 5,
        "fixed parent clock policy",
    )
    marker = read(clock["marker"])
    start, stop = clock["start_monotonic"], clock["parent_stop_monotonic"]
    require(
        start == marker["monotonic"]
        and stop == run["terminal"]["parent_stop_monotonic"]
        and np.isfinite([start, stop]).all()
        and 0 <= stop - start <= 605.5,
        "bound search clock including at most5s termination grace",
    )
    previous = start
    for row in run["rows"]:
        attempt = bundle_work(row)
        began = attempt["started_monotonic"]
        require(previous <= began <= start + 600.5, "ordered attempt inside counted wall budget")
        if row["status"] == "completed":
            previous = row["completed_monotonic"]
            require(previous <= min(stop, start + 600.5), "persisted bundle within wall guard")
        else:
            previous = began
    reason = run["terminal"]["reason"]
    require(
        reason
        in (
            "solver_return",
            "evaluation_budget",
            "evaluation_failure",
            "wall_budget",
            "parent_timeout",
            "parent_failure",
            "worker_failure",
        ),
        "terminal reason",
    )
    if reason == "evaluation_budget":
        require(len(run["rows"]) == 128, "128 attempts required for evaluation-budget terminal")
    if reason == "solver_return":
        require(
            run["terminal"]["nfev"] == len(run["rows"])
            and run["terminal"]["njev"] == len(run["rows"]),
            "solver reported call counts",
        )
    require(run["attempted_bundles"] == len(run["rows"]), "complete attempted-call accounting")
    return dict(elapsed_seconds=stop - start, attempted_bundles=len(run["rows"]), reason=reason)


def target_arrays(binding, case, n):
    require(n in (16, 32, 64), "registered interior resolution required")
    record = binding["target_archives"][case["target"]]
    require(record["wout"] == binding["targets"][case["target"]]["wout"], "archived target Wout")
    points, fields = [], []
    for s in (0.25, 0.5, 0.75):
        rows = [r for r in record["fields"] if r["s"] == s and r["n"] == 64]
        require(len(rows) == 1, "unique qualified64 target grid per radius")
        raw = arrays(rows[0]["arrays"])
        stride = 64 // n
        phi, radius, height = [raw[k][::stride, ::stride] for k in ("phi", "radius", "height")]
        xyz = np.stack((radius * np.cos(phi), radius * np.sin(phi), height), axis=-1)
        b = raw["bt"][..., None] * raw["et"] + raw["bp"][..., None] * raw["ep"]
        close(raw["native"], b, "archived Cartesian field")
        points.append(xyz.reshape(-1, 3))
        fields.append(b[::stride, ::stride].reshape(-1, 3))
    return np.concatenate(points), np.concatenate(fields)


def target_identity(binding, case):
    data = read(binding["targets"][case["target"]]["input"])
    require(
        data["nfp"] == 2
        and data["mpol"] == 5
        and data["ntor"] == 10
        and data["ns_array"][-1] == 401
        and data["lasym"] is False
        and data["lfreeb"] is False
        and data["pres_scale"] == 0
        and data["curtor"] == 0,
        "original401 nfp2 vacuum target required",
    )
    close(abs(data["phiedge"]), np.pi / 100, "physical edge flux", rtol=0, atol=1e-15)
    points, b = target_arrays(binding, case, 16)
    bphi = b.reshape(3, 16, 16, 3)[:, 0, :, 1]
    require(
        np.all(bphi != 0) and np.all(np.sign(bphi) == np.sign(bphi.flat[0])),
        "common nonzero toroidal target sign on all radii",
    )
    p, t = independent.loop(data, 1024)
    area = float(0.5 * np.mean(p[:, 0] * t[:, 2] - p[:, 2] * t[:, 0]))
    require(np.isfinite(area) and area != 0, "nondegenerate oriented R/Z contour")
    flux = float(-np.sign(area) * np.sign(bphi.flat[0]) * abs(data["phiedge"]))
    b2 = float(np.mean(np.sum(b**2, axis=1)))
    require(np.isfinite(b2) and b2 > 0, "frozen original16-grid field scale")
    return data, points, b, flux, b2


def snapshot_identity(snapshot, row, case, binding, target_flux, b2):
    independent.validate_snapshot(snapshot)
    require(
        snapshot["nbase"] == case["nbase"]
        and snapshot["order"] == case["order"]
        and snapshot["method"] == case["method"],
        "snapshot design class/method identity",
    )
    require(
        np.array_equal(np.asarray(snapshot["base_coefficients"]).ravel(), row["x"]),
        "snapshot canonical geometry must equal selected ledger coordinates",
    )
    require(snapshot["sources"] == binding["targets"][case["target"]], "snapshot target provenance")
    require(
        snapshot["construction"]
        == dict(ncoil=128, nphi=32, ntheta=32, ninner=16, offset=0, nloop=256),
        "original construction grid and loop normalization identity",
    )
    close(snapshot["B2_scale"], b2, "frozen original B2", rtol=1e-13, atol=0)
    require(snapshot["target_flux"] == target_flux, "oriented target physical flux")
    require(
        snapshot["seed_unit_flux"] != 0
        and np.sign(snapshot["unit_flux"]) == np.sign(snapshot["seed_unit_flux"]),
        "no unit-current orientation flip",
    )


def direct_arrays(snapshot, raw, ncoil):
    output = {}
    for prefix in ("boundary", "inner", "loop"):
        p = raw[f"{prefix}_points"]
        selection = indices(len(p))
        magnetic, potential = independent.direct_field(snapshot, p[selection], ncoil=ncoil)
        for kind, field in (("B", magnetic), ("A", potential)):
            key = f"{prefix}_{kind}"
            output[key] = relative_components(raw[key][selection], field, key)
    return output


def field_row(
    row,
    snapshot,
    data,
    binding,
    case,
    *,
    ncoil=128,
    nphi=32,
    ntheta=32,
    ninner=16,
    offset=0,
    objective=True,
    direct=True,
):
    require(row.get("status") == "completed", "completed raw field row required")
    raw = arrays(row["arrays"])
    surface = independent.boundary(data, nphi, ntheta, shift=offset == 0.5)
    for key, expected in (
        ("boundary_points", surface["points"].reshape(-1, 3)),
        ("boundary_normals", surface["unitnormal"].reshape(-1, 3)),
        ("boundary_weights", surface["weights"].ravel()),
    ):
        close(raw[key], expected, key)
    points, target = target_arrays(binding, case, ninner)
    close(raw["inner_points"], points, "VMEC native interior point identity", rtol=1e-12)
    close(raw["inner_target"], target, "archived VMEC vector target", rtol=1e-12)
    lp, lt = independent.loop(data, 256)
    close(raw["loop_points"], lp, "analytic loop coordinates")
    close(raw["loop_tangents"], lt, "analytic loop tangent")
    curves = independent.physical_curves(snapshot, ncoil)
    for key, expected in (
        ("coil_positions", curves["positions"]),
        ("coil_tangents", curves["tangents"]),
        ("coil_currents", curves["currents"]),
    ):
        close(raw[key], expected, key)
    base_speed = np.linalg.norm(curves["tangents"][: case["nbase"]], axis=-1)
    base_curvature = (
        np.linalg.norm(
            np.cross(curves["tangents"][: case["nbase"]], curves["second"][: case["nbase"]]),
            axis=-1,
        )
        / base_speed**3
    )
    close(row["metrics"]["lengths"], base_speed.mean(axis=1), "base coil lengths")
    close(row["metrics"]["kappa_max"], base_curvature.max(axis=1), "base coil curvature")
    metric = independent.metrics(
        raw["boundary_B"], raw["boundary_normals"], raw["boundary_weights"], snapshot["B2_scale"]
    )
    metric.update(
        independent.inner_metrics(raw["inner_B"], raw["inner_target"], snapshot["B2_scale"])
    )
    for key in ("JN", "normal_rms", "normal_max", "JV", "vector_rms"):
        close(row["metrics"][key], metric[key], key)
    for key in ("scale", "B2_scale", "target_flux"):
        require(row["metrics"][key] == snapshot[key], f"fixed physical {key}")
    require(row["metrics"]["current"] == 100000 * snapshot["scale"], "actual physical current")
    flux = float(np.mean(np.sum(raw["loop_A"] * raw["loop_tangents"], axis=1)))
    close(row["metrics"]["flux"], flux, "actual analytic loop integral")
    close(row["metrics"]["unit_flux"] * snapshot["scale"], flux, "actual unit-flux accounting")
    if objective:
        require(row["metrics"]["frozen_scale"] is False, "construction normalization required")
        close(flux, snapshot["target_flux"], "construction calibrated flux", rtol=1e-12, atol=0)
        geo = independent.geometry_penalties(snapshot, data, ncoil=ncoil)
        close(row["metrics"]["geometry_penalty"], geo["total"], "independent geometry penalty")
        value = metric["JN"] + (0.05 * metric["JV"] if case["method"] == "V" else 0) + geo["total"]
        close(row["J"], value, "own actual composite objective")
        metric.update(J=value, geometry=geo)
    else:
        require(
            row["metrics"]["frozen_scale"] is True, "fine diagnostics must freeze physical current"
        )
    metric["direct_errors"] = direct_arrays(snapshot, raw, ncoil) if direct else {}
    return metric


def flux_audit(record, snapshot, data):
    require(
        record["status"] == "completed" and record["ncoil"] in (128, 512), "complete flux phase"
    )
    for key in ("scale", "B2_scale", "target_flux"):
        require(record[key] == snapshot[key], f"flux fixed {key}")
    lines, areas = record["lines"], record["areas"]
    require(record["full_bundles"] == 0, "no concealed flux gradient work")
    require([r["ntheta"] for r in lines] == [256, 512, 1024], "all three angular line grids")
    require(
        [(r["nrho"], r["ntheta"]) for r in areas]
        == [(r, n) for r in (16, 32) for n in (256, 512, 1024)],
        "all six signed fan grids",
    )
    expected_calls = [(kind, n) for n in (256, 512, 1024) for kind in ("B", "A")]
    expected_calls += [
        (kind, r * n) for r in (16, 32) for n in (256, 512, 1024) for kind in ("B", "A")
    ]
    require(
        [(r["quantity"], r["points"]) for r in record["native_calls"]] == expected_calls
        and all(r["status"] == "completed" for r in record["native_calls"]),
        "all18 counted native flux field/potential calls",
    )
    values, direct_errors = {}, []
    for row in lines:
        require(row["status"] == "completed", "completed line integral required")
        raw = arrays(row["arrays"])
        p, t = independent.loop(data, row["ntheta"])
        close(raw["points"], p, "flux loop points")
        close(raw["tangents"], t, "flux analytic tangent")
        at = indices(len(p))
        b, a = independent.direct_field(snapshot, p[at], ncoil=record["ncoil"])
        direct_errors.extend(
            [
                relative_components(raw["B"][at], b, "flux line B"),
                relative_components(raw["A"][at], a, "flux line A"),
            ]
        )
        value = float(np.mean(np.sum(raw["A"] * t, axis=1)))
        close(row["flux"], value, "line flux arithmetic")
        values[row["ntheta"]] = value
    target = snapshot["target_flux"]
    denominator = abs(target)
    angular = max(abs(values[n] - values[1024]) / denominator for n in (256, 512))
    checks = []
    for row in areas:
        require(row["status"] == "completed", "completed signed fan integral required")
        raw = arrays(row["arrays"])
        p, normal = independent.fan_area(data, row["nrho"], row["ntheta"])
        close(raw["points"], p, "fan quadrature coordinates")
        close(raw["weighted_normals"], normal, "signed fan weighted Jacobian")
        at = indices(len(p))
        b, a = independent.direct_field(snapshot, p[at], ncoil=record["ncoil"])
        direct_errors.extend(
            [
                relative_components(raw["B"][at], b, "fan B"),
                relative_components(raw["A"][at], a, "fan A"),
            ]
        )
        value = float(np.sum(raw["B"] * normal))
        close(row["flux"], value, "signed area flux arithmetic")
        line = values[row["ntheta"]]
        checks.append(
            dict(
                nrho=row["nrho"],
                ntheta=row["ntheta"],
                area=value,
                line=line,
                relative_error=max(abs(value - target), abs(line - target)) / denominator,
                stokes_error=abs(value - line) / denominator,
                angular_error=angular,
            )
        )
    # Every radial/angular area must agree with the finest one too; a shared
    # line error alone cannot serve as its own area convergence certificate.
    finest = checks[-1]["area"]
    for row in checks:
        row["angular_error"] = max(row["angular_error"], abs(row["area"] - finest) / denominator)
    passed = all(
        r[k] <= 1e-6 for r in checks for k in ("relative_error", "stokes_error", "angular_error")
    )
    return dict(checks=checks, direct_errors=direct_errors, passed=passed)


def common(run, binding):
    require(type(run.get("schema_version")) is int and run["schema_version"] == 1, "pilot schema1")
    require(run.get("phase") in ("qualification", "search", "validation"), "registered phase")
    require(run.get("status") == "completed", "completed phase report required")
    require(run.get("source") == binding, "exact committed source/environment binding")
    require(
        run.get("equilibrium_solves") == 0
        and run.get("threads")
        == {
            key: "1"
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
        "single-thread no-equilibrium-solve pilot",
    )
    case = run["case"]
    expected = [
        dict(
            label=f"{target}-n{nbase}-{method}",
            target=target,
            nbase=nbase,
            order=order,
            method=method,
        )
        for target in ("reference", "selected")
        for nbase, order in ((6, 5), (8, 7))
        for method in ("N", "V")
    ]
    require(case in expected and binding["matrix"] == expected, "registered matrix identity")
    require(
        run.get("transfer_pass") is False and run.get("step4_pass") is False,
        "fit pilot must never claim transfer/step4 admission",
    )
    seed = canonical_seed(case["nbase"], case["order"])
    require(np.array_equal(run["seed_x"], seed), "original exact circular canonical seed")
    require(
        run["names"] == independent.parameter_names(case["nbase"], case["order"]),
        "registered physical DOF names",
    )
    return case, seed


def predecessor(run, kind, binding):
    document = read(run[kind])
    certificate = read(run[f"{kind}_audit"])
    require(
        certificate.get("status") == "completed"
        and certificate.get("phase") == kind
        and certificate.get("arithmetic_and_source_pass") is True
        and certificate.get(f"{kind}_pass") is True
        and certificate.get("run") == run[kind]
        and certificate.get("source") == binding
        and certificate.get("case") == run["case"],
        "bound independently passed predecessor",
    )
    require(
        document["source"] == binding
        and document["case"] == run["case"]
        and document["phase"] == kind,
        "same-cell predecessor identity",
    )
    common(document, binding)
    return document


def qualification(run, binding, case, seed, data, target_flux, b2):
    rows = run["rows"]
    require(
        len(rows) == 10 and [r["index"] for r in rows] == list(range(10)), "ten indexed attempts"
    )
    require(
        run["initialization_work"] == dict(seed_A_calls=1, seed_A_points=256),
        "disclosed one seed orientation call",
    )
    values, reports = [], []
    for row in rows:
        bundle_work(row)
        snapshot = read(row["snapshot"])
        snapshot_identity(snapshot, row, case, binding, target_flux, b2)
        report = field_row(row, snapshot, data, binding, case)
        values.append(report["J"])
        reports.append(report)
    derivative = derivative_audit(rows, seed, values)
    first, last = arrays(rows[0]["arrays"]), arrays(rows[-1]["arrays"])
    require(
        first.keys() == last.keys() and all(np.array_equal(first[k], last[k]) for k in first),
        "exact repeated seed fields/geometry required",
    )
    flux = flux_audit(run["flux"], read(rows[0]["snapshot"]), data)
    require(run["flux"]["ncoil"] == 128, "construction source resolution for qualification flux")
    require(
        run["attempted_bundles"] == 10
        and run["flux_initialization_work"] == dict(seed_A_calls=1, seed_A_points=256),
        "qualification and flux setup work",
    )
    return dict(
        qualification_pass=bool(derivative["passed"] and flux["passed"]),
        derivative=derivative,
        flux=flux,
        field_rows=reports,
        full_bundles=10,
    )


def search(run, binding, case, seed, data, target_flux, b2):
    prior = predecessor(run, "qualification", binding)
    selected = search_selection(run["rows"], seed)
    clock = search_clock(run)
    require(
        run["initialization_work"]
        == run["replay_initialization_work"]
        == dict(seed_A_calls=1, seed_A_points=256),
        "search and fresh replay setup work",
    )
    require(
        type(run["selected"]) is int and run["selected"] == selected,
        "earliest minimum of search ledger only",
    )
    require(
        run["rows"][0]["J"] == prior["rows"][0]["J"]
        and np.array_equal(run["rows"][0]["gradient"], prior["rows"][0]["gradient"]),
        "fresh counted first search bundle equals qualified seed",
    )
    for row in run["rows"]:
        if row["status"] != "completed":
            continue
        snapshot = read(row["snapshot"])
        snapshot_identity(snapshot, row, case, binding, target_flux, b2)
        # Persisted geometry/fields, values and method identity are audited for
        # all calls; direct independent field sums are reserved for selected.
        field_row(row, snapshot, data, binding, case, direct=False)
    row, replay = run["rows"][selected], run["replay"]
    bundle_work(replay, attempted=False)
    require(
        replay["started_monotonic"] >= run["search_clock"]["parent_stop_monotonic"],
        "replay is separate from completed counted search",
    )
    for key in ("x", "gradient"):
        require(np.array_equal(row[key], replay[key]), f"exact selected replay {key}")
    require(
        replay["status"] == "completed"
        and row["J"] == replay["J"]
        and row["metrics"] == replay["metrics"],
        "exact selected value/geometry replay",
    )
    old, fresh = arrays(row["arrays"]), arrays(replay["arrays"])
    require(
        old.keys() == fresh.keys() and all(np.array_equal(old[k], fresh[k]) for k in old),
        "fresh-object exact selected raw-field replay",
    )
    snapshot = read(row["snapshot"])
    require(snapshot == read(replay["snapshot"]), "fresh-object exact physical snapshot replay")
    report = field_row(replay, snapshot, data, binding, case)
    require(
        isinstance(run.get("terminal"), dict), "separate solver/budget/terminal status required"
    )
    return dict(
        search_pass=True,
        selected=selected,
        selected_metrics=report,
        full_bundles=len(run["rows"]),
        completed_bundles=sum(r["status"] == "completed" for r in run["rows"]),
        replay_bundles=1,
        clock=clock,
    )


def refinement(coarse, fine):
    require(np.isfinite([coarse, fine]).all() and min(coarse, fine) >= 0, "finite RMS refinement")
    error = abs(fine - coarse)
    return dict(
        coarse=coarse, fine=fine, delta=error, passed=bool(error <= 0.01 * coarse or error <= 1e-7)
    )


def geometry_audit(record, snapshot, data):
    known = (
        "strictly positive speed not certified between curve nodes",
        "detected coincident non-endpoint filament positions within roundoff",
        "zero-speed filament",
        "degenerate zero-speed curve",
    )
    try:
        geometry = independent.geometry_certificates(snapshot, data)
    except ValueError as exc:
        require(
            str(exc) in known
            and record.get("status") == "uncertified"
            and record.get("certificate_available") is False
            and record.get("error") == f"ValueError: {exc}",
            "only independently reproduced known uncertified geometry is an open gate",
        )
        return dict(
            certificate_available=False, geometry_pass=False, uncertified_error=f"ValueError: {exc}"
        )
    require(record["status"] == "completed", "completed geometric certification")
    require(geometry == read(record["result"]), "independently recomputed geometry certificate")
    return geometry


def validation(run, binding, case, seed, data, target_flux, b2):
    prior = predecessor(run, "search", binding)
    selected = search_selection(prior["rows"], seed)
    require(run["selected"] == selected == prior["selected"], "fixed search selection")
    source_row = prior["rows"][selected]
    require(run["snapshot"] == source_row["snapshot"], "unchanged selected physical snapshot")
    snapshot = read(run["snapshot"])
    snapshot_identity(snapshot, source_row, case, binding, target_flux, b2)
    rows = run["rows"]
    expected = [
        ("boundary", 256, 64, 64, 16, 0),
        ("boundary", 256, 128, 128, 16, 0),
        ("boundary", 512, 128, 128, 16, 0),
        ("boundary", 512, 128, 128, 16, 0.5),
        ("inner", 256, 32, 32, 32, 0),
        ("inner", 256, 32, 32, 64, 0),
        ("inner", 512, 32, 32, 64, 0),
    ]
    actual = [
        tuple(row[k] for k in ("kind", "ncoil", "nphi", "ntheta", "ninner", "offset"))
        for row in rows
    ]
    require(actual == expected, "every registered fine and shifted grid in order")
    require(
        run["full_bundles"] == 0 and len(run["native_initializations"]) == 7,
        "seven value-only diagnostic objects, no gradient bundles",
    )
    for row, init in zip(rows, run["native_initializations"], strict=True):
        require(
            init["label"] == row["label"]
            and init["status"] == "completed"
            and init["work"] == dict(seed_A_calls=1, seed_A_points=256),
            "explicit diagnostic initialization work",
        )
        require(
            [r["quantity"] for r in row["native_calls"]]
            == ["diagnostics", "boundary_A", "inner_A", "loop_B"]
            and row["native_calls"][0]["value_calls"] == 3
            and all(r["status"] == "completed" for r in row["native_calls"]),
            "complete value-only diagnostic and supplementary work ledger",
        )
    reports = []
    for row in rows:
        reports.append(
            field_row(
                row,
                snapshot,
                data,
                binding,
                case,
                **{k: row[k] for k in ("ncoil", "nphi", "ntheta", "ninner", "offset")},
                objective=False,
            )
        )
    flux = flux_audit(run["flux"], snapshot, data)
    require(run["flux"]["ncoil"] == 512, "finest512 source grid for final Stokes checks")
    geometry = geometry_audit(run["geometry"], snapshot, data)
    pairs = [
        (reports[a]["normal_rms"], reports[b]["normal_rms"]) for a, b in ((0, 1), (1, 2), (2, 3))
    ]
    pairs += [(reports[a]["vector_rms"], reports[b]["vector_rms"]) for a, b in ((4, 5), (5, 6))]
    refinements = [refinement(*pair) for pair in pairs]
    gates = independent.entry_gates(
        snapshot, reports[:4], reports[4:], flux["checks"], geometry, pairs, [True] * 7
    )
    return dict(
        validation_complete=True,
        entry_pass=gates["entry_pass"],
        gates=gates["checks"],
        field_rows=reports,
        flux=flux,
        geometry=geometry,
        refinements=refinements,
        value_diagnostic_states=7,
        full_bundles=0,
    )


def audit(run, root):
    binding = sources(root)
    bind_tree(run)
    case, seed = common(run, binding)
    data, _, _, target_flux, b2 = target_identity(binding, case)
    phase = run["phase"]
    function = {"qualification": qualification, "search": search, "validation": validation}[phase]
    answer = function(run, binding, case, seed, data, target_flux, b2)
    passed = answer.get(f"{phase}_pass", answer.get("entry_pass", False))
    return dict(
        status="completed",
        phase=phase,
        source=binding,
        case=case,
        arithmetic_and_source_pass=True,
        all_pass=passed,
        transfer_pass=False,
        step4_pass=False,
        **answer,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(args.run.is_absolute(), "absolute run.json path required")
    require(not args.output.exists(), "fresh immutable audit output required")
    root = Path(__file__).resolve().parents[1]
    result = dict(
        status="error",
        arithmetic_and_source_pass=False,
        all_pass=False,
        qualification_pass=False,
        search_pass=False,
        validation_complete=False,
        entry_pass=False,
        transfer_pass=False,
        step4_pass=False,
    )
    try:
        document = json.loads(args.run.read_text())
        result.update(
            phase=document.get("phase"), source=document.get("source"), case=document.get("case")
        )
        result.update(audit(document, root))
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["run"] = reference(args.run)
    if result.get("phase") in ("qualification", "search", "validation"):
        result[result["phase"]] = result["run"]
    result.update(auditor=reference(Path(__file__)), repository=git_state(root))
    write_json_atomic(args.output, result)
    print(
        json.dumps(
            {k: result.get(k) for k in ("status", "phase", "all_pass", "error", "entry_pass")}
        )
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
