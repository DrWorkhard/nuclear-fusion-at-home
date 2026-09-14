"""Fail-closed independent arithmetic, source, domain and improvement admission."""

import argparse
import copy
import json
from pathlib import Path

import netCDF4
import numpy as np
from audit_qi_clebsch import recheck
from current_diagnostic_inputs import checked, reference
from plasma_inputs import root_path, sources

from fusion_baselines.contour_topology import two_root_winding
from fusion_baselines.plasma_action_audit import independent_actions
from fusion_baselines.plasma_design import HOLD_PITCHES, HOLD_SURFACES, LEVELS, PITCHES, SURFACES
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.qi_resolution import boundary_errors, effective_input


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(ref):
    return json.loads(checked(ref).read_text())


def bind_tree(value):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            checked(value)
        else:
            for child in value.values():
                bind_tree(child)
    elif isinstance(value, list):
        for child in value:
            bind_tree(child)


def finite_close(a, b, rtol=1e-12, atol=1e-14):
    a, b = np.asarray(a), np.asarray(b)
    return bool(
        a.shape == b.shape
        and np.isfinite(a).all()
        and np.isfinite(b).all()
        and np.allclose(a, b, rtol=rtol, atol=atol)
    )


def invariant(q):
    # Deliberately not the producer's bounce_field function.
    return 1.0082953902491054 + q * (1.5870966275564338 - 1.0082953902491054)


def input_identity(original, actual, x, ns):
    require(ns in (201, 401), "registered radial grid")
    require(
        np.shape(x) == (4,) and np.isfinite(x).all() and max(abs(np.array(x))) <= 0.001,
        "four finite bounded changes",
    )
    expected = copy.deepcopy(original)
    for k, (kind, m, n) in enumerate((("rbc", 1, 1), ("zbs", 1, 1), ("rbc", 2, 0), ("zbs", 2, 0))):
        rows = [v for v in expected[kind] if v["m"] == m and v["n"] == n]
        require(len(rows) == 1, "unique physical mode identity")
        rows[0]["value"] = rows[0]["value"] + x[k]
    require(
        actual == effective_input(expected, ns, 2), "unauthorized physical/numerical input change"
    )


def trace_source_identity(trace, wout, surface):
    """Scalar Fourier/geometry holdouts plus full trapezoidal length reconstruction."""
    require(
        np.shape(trace["speed"]) == trace["B"].shape and np.all(trace["speed"] > 0),
        "positive recorded geometric speed",
    )
    lengths = np.zeros_like(trace["length"])
    lengths[1:] = np.cumsum(
        (trace["speed"][:-1] + trace["speed"][1:]) * np.diff(trace["phi"])[:, None] / 2, axis=0
    )
    require(np.array_equal(lengths, trace["length"]), "full recorded arclength integral")
    with netCDF4.Dataset(checked(wout)) as ds:
        ns = int(ds["ns"][...])
        full = np.linspace(0, 1, ns)
        half = (full[1:] + full[:-1]) / 2

        def radial(key, grid, trim):
            values = np.asarray(ds[key][...])[trim:]
            if values.ndim == 1:
                return np.interp(surface, grid, values)
            return np.array([np.interp(surface, grid, v) for v in values.T])

        r, z = [radial(k, full, 0) for k in ("rmnc", "zmns")]
        lam, b = [radial(k, half, 1) for k in ("lmns", "bmnc")]
        iota = radial("iotas", half, 1)
        m, n, mn, nn = [np.asarray(ds[k][...]) for k in ("xm", "xn", "xm_nyq", "xn_nyq")]
    for i in (0, len(trace["phi"]) // 2, len(trace["phi"]) - 1):
        for j in (0, len(trace["alpha"]) // 2, len(trace["alpha"]) - 1):
            theta, phi = trace["theta"][i, j], trace["phi"][i]
            co, si = np.cos(m * theta - n * phi), np.sin(m * theta - n * phi)
            require(
                abs(theta + np.dot(lam, si) - trace["alpha"][j] - iota * phi) <= 1e-10,
                "scalar field-line root/source",
            )
            slope = (iota + np.dot(n * lam, co)) / (1 + np.dot(m * lam, co))
            radius = np.dot(r, co)
            rp = np.dot(n * r, si) - np.dot(m * r, si) * slope
            zp = -np.dot(n * z, co) + np.dot(m * z, co) * slope
            speed = np.sqrt(radius**2 + rp**2 + zp**2)
            field = np.dot(b, np.cos(mn * theta - nn * phi))
            require(
                finite_close(speed, trace["speed"][i, j], rtol=1e-10)
                and finite_close(field, trace["B"][i, j], rtol=1e-10),
                "scalar field/geometry source",
            )


def measurement(ref, wout, surfaces, pitches, level):
    data = read(ref)
    nphi, nalpha, offset = level
    require(data["status"] == "completed" and data["wout"] == wout, "complete bound measurement")
    require(
        data["surfaces"] == list(surfaces)
        and data["pitches"] == list(pitches)
        and data["resolution"] == [nphi, nalpha, 2]
        and data["offset"] == offset,
        "fixed full measurement domain",
    )
    require(
        [(c["s"], c["q"]) for c in data["cells"]] == [(s, q) for s in surfaces for q in pitches]
        and [t["s"] for t in data["traces"]] == list(surfaces),
        "missing or duplicate domain cell",
    )
    actions, variance, envelope, means, traces, quad_errors = [], [], [], [], [], []
    for j, tr in enumerate(data["traces"]):
        with np.load(checked(tr["arrays"]), allow_pickle=False) as loaded:
            trace = {k: loaded[k] for k in loaded.files}
        require(all(np.isfinite(v).all() for v in trace.values()), "nonfinite raw trace")
        require(
            np.array_equal(trace["phi"], np.linspace(0, 2 * np.pi, nphi))
            and np.array_equal(
                trace["alpha"], np.linspace(0, 2 * np.pi, nalpha, endpoint=False) + offset
            )
            and trace["B"].shape == (nphi, nalpha),
            "raw trace grid identity",
        )
        require(trace["coordinate_residual_max"] <= 1e-10, "field-line inversion residual")
        trace_source_identity(trace, wout, tr["s"])
        traces.append(trace)
        for i, q in enumerate(pitches):
            cell = data["cells"][j * len(pitches) + i]
            require(cell["bounce_field"] == invariant(q), "fixed physical invariant")
            alternate = independent_actions(trace, invariant(q))
            a = np.asarray(cell["actions"])
            require(
                a.shape == (nalpha, 2) and np.isfinite(a).all() and np.all(a > 0),
                "all positive finite actions required",
            )
            error = float(np.max(abs(alternate["actions"] / a - 1)))
            require(
                error <= 1e-6 and finite_close(alternate["bounds"], cell["bounds"]),
                "independent quadrature/turning point mismatch",
            )
            phi_edges = np.array(
                [
                    np.interp(
                        alternate["bounds"][k].ravel(), trace["length"][:, k], trace["phi"]
                    ).reshape(2, 2)
                    for k in range(nalpha)
                ]
            )
            require(finite_close(phi_edges, cell["phi_bounds"]), "period turning-angle mismatch")
            mean = np.sum(a, axis=0) / nalpha
            centered = a - mean
            var = np.einsum("ij,ij->j", centered, centered) / nalpha / mean**2
            env = (a.max(axis=0) - a.min(axis=0)) / mean
            require(
                all(
                    finite_close(x, y)
                    for x, y in (
                        (mean, cell["mean"]),
                        (var, cell["variance"]),
                        (env, cell["envelope"]),
                        (var.mean(), cell["score"]),
                    )
                ),
                "reported objective arithmetic",
            )
            actions.append(a)
            means.append(mean)
            variance.append(var)
            envelope.append(env)
            quad_errors.append(error)
    score = float(np.mean(variance))
    require(finite_close(score, data["score"]), "overall objective arithmetic")
    return dict(
        actions=np.array(actions),
        mean=np.array(means),
        variance=np.array(variance),
        envelope=np.array(envelope),
        score=score,
        traces=traces,
        max_quadrature_error=max(quad_errors),
    )


def equilibrium(row, original, baseline=None):
    bind_tree(row)
    actual, request = read(row["input"]), read(row["request"])
    input_identity(original, actual, row["x"], row["ns"])
    require(
        request["input"] == row["input"]
        and request["x"] == row["x"]
        and request["ns"] == row["ns"]
        and request["modes"] == [["rbc", 1, 1], ["zbs", 1, 1], ["rbc", 2, 0], ["zbs", 2, 0]],
        "worker input identity",
    )
    require(read(request["original"]) == original, "worker original identity")
    if row["status"] != "completed":
        require(
            row["eligible"] is False and bool(row.get("error")), "failed trial cannot be admitted"
        )
        return None
    solver = read(row["solver"])
    require(
        solver["status"] == "completed"
        and solver["converged"] is True
        and solver["version"] == "0.7.3"
        and solver["request"] == row["request"]
        and solver["wout"] == row["wout"]
        and row["returncode"] == 0,
        "solver provenance",
    )
    require(0 < solver["elapsed_seconds"] <= 1805, "cold-start time cap with poll allowance")
    with netCDF4.Dataset(checked(row["wout"])) as ds:
        require(int(ds["ns"][...]) == row["ns"] and int(ds["nfp"][...]) == 2, "solver grid")
        for key in ("fsqr", "fsqz", "fsql"):
            value = float(ds[key][...])
            require(
                np.isfinite(value) and 0 <= value <= 1e-12 and value == solver["residuals"][key],
                "actual force residual",
            )
        errors = boundary_errors(ds, actual)
        require(
            max(errors.values()) <= 1e-12 and errors == row["metadata"]["boundary_errors"],
            "boundary output identity",
        )
        edge = float(ds["phi"][-1])
        require(
            abs(edge - actual["phiedge"]) <= 1e-14 and edge == row["metadata"]["edge_flux"],
            "edge flux",
        )
        volume = float(ds["volume_p"][...])
        iota = np.interp(
            SURFACES, (np.arange(row["ns"] - 1) + 0.5) / (row["ns"] - 1), ds["iotas"][1:]
        )
        require(
            volume > 0
            and finite_close(volume, row["metadata"]["volume"])
            and finite_close(iota, row["metadata"]["iota"]),
            "physical metadata",
        )
    metrics = measurement(
        row["measurement"]["report"], row["wout"], SURFACES, PITCHES, (801, 16, 0)
    )
    require(finite_close(row["measurement"]["score"], metrics["score"]), "search score")
    eligible = baseline is None or (
        abs(volume / baseline["metadata"]["volume"] - 1) <= 0.01
        and np.max(abs(iota - baseline["metadata"]["iota"])) <= 0.02
    )
    require(row["eligible"] is bool(eligible), "construction geometry guard")
    return metrics


def search_identity(study):
    rows, search = study["cells"], study["search"]
    require(
        len(rows) == search["unique_solves"] <= 17
        and search["requests"] == 17
        and len(search["events"]) == 17
        and len(search["rounds"]) == 2,
        "fixed search budget",
    )
    require(
        rows[0]["x"] == [0.0] * 4 and rows[0]["eligible"] is True, "qualified unchanged baseline"
    )
    cache, cursor, center, step = {}, 0, 0, 0.0002

    def consume(point):
        nonlocal cursor
        event = search["events"][cursor]
        key = tuple(point)
        hit = key in cache
        if not hit:
            cache[key] = len(cache)
        index = cache[key]
        require(
            event == dict(x=list(point), cache_hit=hit, record=index)
            and rows[index]["x"] == list(point),
            "poll/event/cache identity",
        )
        cursor += 1
        return index

    consume([0.0] * 4)
    for number, record in enumerate(search["rounds"], 1):
        indices = [center]
        for k in range(4):
            for sign in (1, -1):
                point = list(rows[center]["x"])
                point[k] += sign * step
                indices.append(consume(point))
        selected = min(
            (i for i in indices if rows[i]["eligible"]),
            key=lambda i: (rows[i]["measurement"]["score"], indices.index(i)),
        )
        require(
            record
            == dict(round=number, center=center, step=step, candidates=indices, selected=selected),
            "independent selection replay",
        )
        if selected == center:
            step /= 2
        center = selected
    require(
        search["selected"] == center
        and len(cache) == len(rows)
        and search["cache_hits"] == 17 - len(rows),
        "final selection/cache totals",
    )
    require(study["new_equilibrium_attempts"] == len(rows) + 3 <= 20, "total cold-solve cap")
    return center


def refinement(coarse, fine, stride=1, matched=True):
    delta = abs(fine["score"] - coarse["score"])
    stable = delta <= max(0.05 * abs(coarse["score"]), 1e-12)
    error = (
        float(np.max(abs(fine["actions"][:, ::stride] / coarse["actions"] - 1)))
        if matched
        else None
    )
    return dict(
        score_delta=delta,
        action_relative_error=error,
        passed=bool(stable and (not matched or error <= 1e-3)),
    )


def physics(row, edge):
    require(not row["errors"], "all validation phases must complete")
    require(
        [(f["s"], f["n"]) for f in row["fields"]] == [(s, n) for s in SURFACES for n in (64, 128)],
        "all physical field grids",
    )
    passed, previous = True, None
    for field in row["fields"]:
        with np.load(checked(field["arrays"]), allow_pickle=False) as arrays:
            require(all(np.isfinite(arrays[k]).all() for k in arrays.files), "finite field arrays")
            errors, identity = recheck(arrays, edge)
            n = field["n"]
            phi, theta = np.meshgrid(
                2 * np.pi * np.arange(n) / (2 * n), 2 * np.pi * np.arange(n) / n, indexing="ij"
            )
            require(
                identity
                and np.array_equal(phi, arrays["phi"])
                and np.array_equal(theta, arrays["theta"]),
                "independent field/grid identity",
            )
        require(
            all(finite_close(errors[k], field["errors"][k]) for k in errors),
            "field error arithmetic",
        )
        checks = {
            k: bool(
                np.isfinite(v) and (v > 0.1 if k in ("wrong_sign", "missing_2pi") else v <= 1e-3)
            )
            for k, v in errors.items()
        }
        require(checks == field["checks"], "physical field classification")
        passed &= all(checks.values())
        if n == 128:
            differences = {
                k: abs(errors[k] - previous[k])
                for k in ("poloidal", "toroidal", "cartesian", "magnitude")
            }
            require(
                all(finite_close(v, field["refinement"][k]) for k, v in differences.items()),
                "field refinement arithmetic",
            )
            passed &= max(differences.values()) <= 1e-5
        previous = errors
    require(
        [(r["s"], r["resolution"]) for r in row["contours"]]
        == [(s, [nt, nz]) for nt, nz in ((256, 512), (512, 1024)) for s in HOLD_SURFACES],
        "all contour grids required",
    )
    for contour in row["contours"]:
        with np.load(checked(contour["arrays"]), allow_pickle=False) as arrays:
            b = arrays["B"]
        require(
            list(b.shape) == contour["resolution"]
            and [c["q"] for c in contour["cells"]] == list(HOLD_PITCHES),
            "contour coverage",
        )
        for cell in contour["cells"]:
            recomputed = dict(q=cell["q"], **two_root_winding(b, invariant(cell["q"])))
            require(recomputed == cell, "contour classification mismatch")
            passed &= cell["pass"]
    return bool(passed)


def crosscheck(row, training, expected_source):
    cross = row["crosscheck"]
    require(
        cross["source"] == expected_source and [r["s"] for r in cross["rows"]] == list(SURFACES),
        "independent tracer source/domain",
    )
    passed = True
    for r, local in zip(cross["rows"], training["traces"], strict=True):
        with np.load(checked(r["arrays"]), allow_pickle=False) as arrays:
            published = {k: arrays[k] for k in arrays.files}
        require(
            all(np.isfinite(v).all() for v in published.values())
            and published["B"].shape == local["B"].shape
            and np.array_equal(published["alpha"], local["alpha"])
            and np.array_equal(published["phi"], local["phi"]),
            "published raw trace identity",
        )
        berr = float(np.max(abs(local["B"] / published["B"] - 1)))
        lerr = float(
            np.max(abs(published["length"] - local["length"])) / np.max(published["length"])
        )
        errors = [
            float(
                np.max(
                    abs(
                        independent_actions(published, invariant(q))["actions"]
                        / independent_actions(local, invariant(q))["actions"]
                        - 1
                    )
                )
            )
            for q in PITCHES
        ]
        require(
            finite_close(berr, r["field_relative_error"])
            and finite_close(lerr, r["length_normalized_error"])
            and finite_close(errors, r["action_relative_errors"], rtol=1e-3, atol=1e-6),
            "independent tracer error arithmetic",
        )
        ok = (
            berr <= 1e-8
            and lerr <= 1e-3
            and max(errors) <= 1e-3
            and "error" not in r["stdout"].lower()
        )
        require(r["all_pass"] is bool(ok), "published tracer classification")
        passed &= ok
    require(cross["all_pass"] is bool(passed), "published total classification")
    return bool(passed)


def conclusion(gates):
    required = {
        "new_design",
        "repeat",
        "geometry",
        "physics",
        "crosscheck",
        "refinement",
        "cell_guards",
        "training_gain",
        "holdout_gain",
        "resolved_gain",
    }
    require(
        set(gates) == required and all(type(v) is bool for v in gates.values()),
        "complete genuine gate booleans",
    )
    return all(gates.values())


def audit(study_path, holdout_path):
    original, binding = sources(root_path())
    study, hold = [json.loads(p.read_text()) for p in (study_path, holdout_path)]
    bind_tree(study)
    bind_tree(hold)
    require(
        study["status"] == hold["status"] == "completed"
        and study["source"] == hold["source"] == binding,
        "completed fixed-source producer phases",
    )
    require(
        hold["study"] == reference(study_path)
        and hold["used_for_selection"] is False
        and study["step3_pass"] is False
        and hold["step3_pass"] is False,
        "independent no-feedback admission",
    )
    selected = search_identity(study)
    require(
        study["thread_environment"]
        == {
            name: "1"
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
        "one-thread provenance",
    )
    training = [equilibrium(row, original, study["cells"][0]) for row in study["cells"]]
    require(
        [r["label"] for r in study["endpoints"]]
        == ["selected-repeat", "reference-fine", "selected-fine"],
        "three separate cold endpoints",
    )
    candidate = study["cells"][selected]
    for r, (x, ns) in zip(
        study["endpoints"],
        ((candidate["x"], 201), ([0.0] * 4, 401), (candidate["x"], 401)),
        strict=True,
    ):
        require(
            r["x"] == x and r["ns"] == ns and r["status"] == "completed",
            "endpoint identity/completion",
        )
    ends = [equilibrium(row, original) for row in study["endpoints"]]
    rows = [study["cells"][0], candidate, study["endpoints"][1], study["endpoints"][2]]
    require(
        len({r["directory"] for r in study["cells"] + study["endpoints"]})
        == len(study["cells"]) + 3,
        "distinct cold-start directories",
    )
    repeat = np.array_equal(training[selected]["actions"], ends[0]["actions"])
    with (
        netCDF4.Dataset(checked(candidate["wout"])) as a,
        netCDF4.Dataset(checked(study["endpoints"][0]["wout"])) as b,
    ):
        for k in (
            "rmnc",
            "zmns",
            "lmns",
            "bmnc",
            "gmnc",
            "bsupumnc",
            "bsupvmnc",
            "iotas",
            "phi",
            "fsqr",
            "fsqz",
            "fsql",
            "niter",
        ):
            repeat &= np.array_equal(a[k][...], b[k][...])
    require(
        [r["label"] for r in hold["states"]]
        == ["reference-201", "selected-201", "reference-401", "selected-401"],
        "four validation states",
    )
    metrics, physical, cross = [], [], []
    for row, source_row in zip(hold["states"], rows, strict=True):
        print(f"Plasma audit: {row['label']}", flush=True)
        require(
            row["wout"] == source_row["wout"] and len(row["measurements"]) == 4,
            "bound four holdout levels",
        )
        metrics.append(
            [
                measurement(ref, row["wout"], HOLD_SURFACES, HOLD_PITCHES, level)
                for ref, level in zip(row["measurements"], LEVELS, strict=True)
            ]
        )
        physical.append(physics(row, source_row["metadata"]["edge_flux"]))
    for i in (2, 3):
        cross.append(crosscheck(hold["states"][i], ends[i - 1], binding["published_tracer"]))
    refinements, uncertainty_terms = [], []
    for state in range(4):
        checks = [
            refinement(metrics[state][0], metrics[state][1]),
            refinement(metrics[state][1], metrics[state][2], stride=2),
            refinement(metrics[state][2], metrics[state][3], matched=False),
        ]
        refinements.extend(
            dict(state=state, kind=k, **r)
            for k, r in zip(("phi", "alpha", "offset"), checks, strict=True)
        )
        if state >= 2:
            uncertainty_terms.extend(r["score_delta"] for r in checks)
    for state in (0, 1):
        for level in range(4):
            r = refinement(metrics[state][level], metrics[state + 2][level])
            refinements.append(dict(state=state, kind=f"radial-level{level}", **r))
            if level == 2:
                uncertainty_terms.append(r["score_delta"])
    a, b = metrics[2][2], metrics[3][2]
    uncertainty = sum(uncertainty_terms)
    geometry = abs(rows[3]["metadata"]["volume"] / rows[2]["metadata"]["volume"] - 1) <= 0.01
    geometry &= (
        np.max(abs(np.array(rows[3]["metadata"]["iota"]) - rows[2]["metadata"]["iota"])) <= 0.02
    )
    gates = dict(
        new_design=any(x != 0 for x in candidate["x"]),
        repeat=bool(repeat),
        geometry=bool(geometry),
        physics=all(physical),
        crosscheck=all(cross),
        refinement=all(r["passed"] for r in refinements),
        cell_guards=bool(
            np.all(b["envelope"] <= np.maximum(1.1 * a["envelope"], a["envelope"] + 0.002))
            and np.max(abs(b["mean"] / a["mean"] - 1)) <= 0.02
        ),
        training_gain=training[0]["score"] > 0
        and training[selected]["score"] <= 0.995 * training[0]["score"],
        holdout_gain=a["score"] > 0 and b["score"] <= 0.995 * a["score"],
        resolved_gain=a["score"] - b["score"] > 5 * uncertainty,
    )
    return dict(
        status="completed",
        arithmetic_and_source_pass=True,
        gates=gates,
        step3_pass=conclusion(gates),
        selected_x=candidate["x"],
        training_scores=[training[0]["score"], training[selected]["score"]],
        holdout_scores=[[m["score"] for m in state] for state in metrics],
        holdout_relative_gain=1 - b["score"] / a["score"],
        observed_uncertainty_sum=uncertainty,
        refinements=refinements,
        physics_pass=physical,
        crosscheck_pass=cross,
        max_quadrature_error=max(m["max_quadrature_error"] for state in metrics for m in state),
        global_qi=False,
        maximum_j=False,
        orbit_qualified=False,
        sota=False,
        squid_c_ready=False,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("holdout", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "new immutable audit output")
    result = dict(status="error", arithmetic_and_source_pass=False, step3_pass=False)
    try:
        result.update(audit(args.study.resolve(), args.holdout.resolve()))
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result.update(
        study=reference(args.study),
        holdout=reference(args.holdout),
        repository=git_state(root_path()),
        auditor=reference(Path(__file__)),
    )
    write_json_atomic(args.output, result)
    print(json.dumps(result))
    return 0 if result["step3_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
