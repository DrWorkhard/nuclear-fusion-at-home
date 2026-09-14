"""Independent follow-up selection, model certificate and unchanged physical admission."""

import argparse
import json
from pathlib import Path

import audit_plasma_design as old
import netCDF4
import numpy as np
from balanced_plasma_inputs import sources
from current_diagnostic_inputs import checked, reference
from plasma_inputs import root_path

from fusion_baselines.balanced_plasma import dual_certificate
from fusion_baselines.plasma_action_audit import independent_actions
from fusion_baselines.plasma_design import HOLD_PITCHES, HOLD_SURFACES, LEVELS
from fusion_baselines.provenance import git_state, write_json_atomic

require = old.require
read = old.read


def runtime_identity(phase, expected_phase, predecessor):
    require(
        phase["phase"] == expected_phase
        and phase["step3_pass"] is False
        and phase["thread_environment"]
        == {
            name: "1"
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        }
        and phase["versions"] == predecessor["versions"],
        "phase/environment provenance",
    )


def wide(row):
    if "wide" not in row:
        require(
            bool(row.get("error")) and row["native"]["status"] != "completed",
            "missing valid broad work",
        )
        return None
    report = read(row["wide"])
    if report["status"] == "completed":
        require("error" not in row, "cannot falsely exclude completed broad measurement")
        result = old.measurement(
            row["wide"], row["native"]["wout"], HOLD_SURFACES, HOLD_PITCHES, (801, 16, 0)
        )
        require(old.finite_close(row["wide_score"], result["score"]), "broad selection score")
        return result
    require(
        report["status"] == "error"
        and bool(row.get("error"))
        and [r["s"] for r in report["traces"]] == list(HOLD_SURFACES),
        "retained failed domain coverage",
    )
    failed, complete = [], []
    for tr in report["traces"]:
        with np.load(checked(tr["arrays"]), allow_pickle=False) as archive:
            trace = {k: archive[k] for k in archive.files}
        old.trace_source_identity(trace, row["native"]["wout"], tr["s"])
        for q in HOLD_PITCHES:
            try:
                result = independent_actions(trace, old.invariant(q))
            except ValueError:
                failed.append((tr["s"], q))
                continue
            complete.append((tr["s"], q))
            cell = next(c for c in report["cells"] if (c["s"], c["q"]) == complete[-1])
            require(
                old.finite_close(result["actions"], cell["actions"], rtol=1e-6),
                "valid partial-domain action",
            )
    require(
        failed
        and failed == [(e["s"], e["q"]) for e in report["errors"]]
        and complete == [(c["s"], c["q"]) for c in report["cells"]],
        "independent failed-cell enumeration",
    )
    return None


def checks(row, value, baseline, base_value):
    if value is None:
        require("construction" not in row, "failed domain cannot have positive construction gates")
        return None
    n, bn = row["native"]["measurement"]["score"], baseline["native"]["measurement"]["score"]
    m, bm = row["native"]["metadata"], baseline["native"]["metadata"]
    values = np.array([n, bn, value["score"], base_value["score"]])
    finite = bool(
        np.isfinite(values).all() and np.all(values >= 0) and bn > 0 and base_value["score"] > 0
    )
    result = dict(
        finite=finite,
        narrow=finite and n <= 0.995 * bn,
        wide=finite and value["score"] <= 0.985 * base_value["score"],
        mean=bool(np.max(abs(value["mean"] / base_value["mean"] - 1)) <= 0.02),
        envelope=bool(
            np.all(
                value["envelope"]
                <= np.maximum(1.1 * base_value["envelope"], base_value["envelope"] + 0.002)
            )
        ),
        geometry=bool(
            abs(m["volume"] / bm["volume"] - 1) <= 0.01
            and np.max(abs(np.array(m["iota"]) - bm["iota"])) <= 0.02
        ),
    )
    require(result == row["construction"], "independent construction classification")
    return result


def selection(rows, values, baseline, base_value, *, skip_baseline=False):
    eligible = []
    for i, (row, value) in enumerate(zip(rows, values, strict=True)):
        if i == 0 and skip_baseline:
            require("construction" not in row, "baseline not a claimed improving candidate")
            continue
        flags = checks(row, value, baseline, base_value)
        if flags and all(flags.values()):
            eligible.append(i)
    return min(eligible, key=lambda i: (values[i]["score"], i)) if eligible else None


def model_check(model, rows, values, baseline, base_value):
    gn, gw, gm = [], [], []
    for k in range(4):
        p, n = rows[2 * k], rows[2 * k + 1]
        pv, nv = values[2 * k], values[2 * k + 1]
        gn.append(
            (p["native"]["measurement"]["score"] - n["native"]["measurement"]["score"])
            / (2e-5 * baseline["native"]["measurement"]["score"])
        )
        gw.append((pv["score"] - nv["score"]) / (2e-5 * base_value["score"]))
        gm.append(((pv["mean"] - nv["mean"]) / (2e-5 * base_value["mean"])).ravel())
    derivatives = np.array(gm).T
    matrix = [[*(1e-4 * np.array(gn)), 1.0], [*(1e-4 * np.array(gw)), 1.0]]
    matrix += [[*(1e-4 * r), 0.0] for r in derivatives]
    matrix += [[*(-1e-4 * r), 0.0] for r in derivatives]
    require(
        all(
            old.finite_close(a, b)
            for a, b in (
                (gn, model["narrow_gradient"]),
                (gw, model["wide_gradient"]),
                (derivatives, model["mean_gradient"]),
                (matrix, model["matrix"]),
            )
        ),
        "central difference and LP matrix identity",
    )
    require(
        model["rhs"] == [0.0] * 2 + [0.01] * 140
        and model["objective"] == [0.0] * 4 + [-1.0]
        and model["bounds"] == [[-1.0, 1.0]] * 4 + [[0.0, None]],
        "fixed LP objective/bounds/buffers",
    )
    require(model["success"] is True and model["status"] == 0, "completed LP")
    certificate = dual_certificate(model)
    require(
        certificate["passed"]
        and old.finite_close(model["proposed_x"], 1e-4 * np.array(model["solution"][:4])),
        "independent primal/dual proposal certificate",
    )
    return certificate


def phase_a(folder, original, binding, predecessor):
    path = folder / "archive.json"
    phase = json.loads(path.read_text())
    runtime_identity(phase, "archive", predecessor)
    old.bind_tree(phase)
    require(
        phase["status"] == "completed"
        and phase["source"] == binding
        and phase["new_solves"] == 0
        and phase["step3_pass"] is False
        and [r["source_index"] for r in phase["rows"]] == list(range(16)),
        "all archived states",
    )
    values = []
    for i, row in enumerate(phase["rows"]):
        print(f"Balanced audit: archive{i}", flush=True)
        require(row["native"] == predecessor["cells"][i], "unaltered archived native record")
        old.equilibrium(row["native"], original)
        values.append(wide(row))
    require(values[0] is not None, "qualified broad baseline")
    chosen = selection(phase["rows"], values, phase["rows"][0], values[0], skip_baseline=True)
    require(phase["selected"] == chosen, "archive selection")
    return phase, values


def phase_b(folder, original, binding, archive, base):
    phase = json.loads((folder / "propose.json").read_text())
    runtime_identity(phase, "propose", archive)
    old.bind_tree(phase)
    require(
        archive["selected"] is None
        and phase["archive"] == reference(folder / "archive.json")
        and phase["status"] == "completed"
        and phase["source"] == binding
        and len(phase["rows"]) == phase["new_solves"] == 11,
        "conditional eight differences plus three probes",
    )
    values = []
    for i, row in enumerate(phase["rows"]):
        if i < 8:
            expected = np.zeros(4)
            expected[i // 2] = 1e-5 if i % 2 == 0 else -1e-5
        else:
            expected = 1e-4 * np.array(phase["model"]["solution"][:4]) * (1.0, 0.5, 0.25)[i - 8]
        require(
            np.array_equal(row["native"]["x"], expected) and row["native"]["ns"] == 201,
            "actual named model/probe point",
        )
        old.equilibrium(row["native"], original)
        values.append(wide(row))
        checks(row, values[-1], archive["rows"][0], base)
    require(all(v is not None for v in values[:8]), "eight complete central difference domains")
    certificate = model_check(
        phase["model"], phase["rows"][:8], values[:8], archive["rows"][0], base
    )
    chosen = selection(phase["rows"][8:], values[8:], archive["rows"][0], base)
    chosen = None if chosen is None else chosen + 8
    require(phase["selected"] == chosen, "real three-probe selection")
    return phase, values, certificate


def admission(folder, original, binding, predecessor, owner, owner_path, baseline):
    end = json.loads((folder / "endpoints.json").read_text())
    runtime_identity(end, "endpoints", predecessor)
    old.bind_tree(end)
    require(
        end["status"] == "completed"
        and end["source"] == binding
        and end["selection"] == reference(owner_path)
        and end["selected_index"] == owner["selected"]
        and end["selected"] == owner["rows"][owner["selected"]]
        and end["new_solves"] == len(end["rows"]) == 2
        and end["total_new_solves"] == owner["new_solves"] + 2 <= 13,
        "frozen selection and exact cold budget",
    )
    candidate = end["selected"]["native"]
    for r, label, ns in zip(
        end["rows"], ("selected-repeat", "selected-fine"), (201, 401), strict=True
    ):
        require(
            r["label"] == label and r["native"]["x"] == candidate["x"] and r["native"]["ns"] == ns,
            "cold endpoint identity",
        )
        old.equilibrium(r["native"], original)
        wide(r)
    rows = [
        predecessor["cells"][0],
        candidate,
        predecessor["endpoints"][1],
        end["rows"][1]["native"],
    ]
    with (
        netCDF4.Dataset(checked(candidate["wout"])) as a,
        netCDF4.Dataset(checked(end["rows"][0]["native"]["wout"])) as b,
    ):
        repeat = all(
            np.array_equal(a[k][...], b[k][...])
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
            )
        )
    require(
        len({r["native"]["directory"] for r in end["rows"]} | {candidate["directory"]}) == 3,
        "distinct selected/repeated/fine sources",
    )
    narrow = [old.equilibrium(r, original) for r in rows]
    repeated = old.equilibrium(end["rows"][0]["native"], original)
    repeat &= np.array_equal(narrow[1]["actions"], repeated["actions"])
    validation_path = folder / "validation.json"
    hold = json.loads(validation_path.read_text())
    old.bind_tree(hold)
    adapter = read(hold["study"])
    require(
        adapter["record_kind"] == "balanced-diagnostic-adapter-not-a-two-poll-search"
        and adapter["balanced_endpoints"] == reference(folder / "endpoints.json")
        and adapter["cells"] == rows[:2]
        and adapter["endpoints"] == [end["rows"][0]["native"], rows[2], rows[3]]
        and adapter["search"] == dict(selected=1),
        "explicit diagnostic adapter origin",
    )
    require(
        hold["source"] == binding["legacy"]
        and hold["status"] == "completed"
        and hold["all_phases_completed"] is True
        and hold["used_for_selection"] is False
        and hold["step3_pass"] is False
        and [r["label"] for r in hold["states"]]
        == ["reference-201", "selected-201", "reference-401", "selected-401"],
        "complete no-feedback validation",
    )
    metrics, physics, cross = [], [], []
    for i, state in enumerate(hold["states"]):
        print(f"Balanced audit: final {state['label']}", flush=True)
        require(
            state["wout"] == rows[i]["wout"] and len(state["measurements"]) == 4,
            "four bound holdout grids",
        )
        metrics.append(
            [
                old.measurement(ref, state["wout"], HOLD_SURFACES, HOLD_PITCHES, level)
                for ref, level in zip(state["measurements"], LEVELS, strict=True)
            ]
        )
        physics.append(old.physics(state, rows[i]["metadata"]["edge_flux"]))
        if i >= 2:
            cross.append(old.crosscheck(state, narrow[i], binding["legacy"]["published_tracer"]))
    refs, uncertainty = [], 0.0
    for state in range(4):
        for label, first, second, stride, matched in (
            ("phi", 0, 1, 1, True),
            ("alpha", 1, 2, 2, True),
            ("offset", 2, 3, 1, False),
        ):
            r = old.refinement(metrics[state][first], metrics[state][second], stride, matched)
            refs.append(dict(state=state, kind=label, **r))
            if state >= 2:
                uncertainty += r["score_delta"]
    for state in (0, 1):
        for level in range(4):
            r = old.refinement(metrics[state][level], metrics[state + 2][level])
            refs.append(dict(state=state, kind=f"radial-level{level}", **r))
            if level == 2:
                uncertainty += r["score_delta"]
    a, b = metrics[2][2], metrics[3][2]
    ma, mb = rows[2]["metadata"], rows[3]["metadata"]
    gates = dict(
        new_design=any(x != 0 for x in candidate["x"]),
        repeat=bool(repeat),
        geometry=bool(
            abs(mb["volume"] / ma["volume"] - 1) <= 0.01
            and np.max(abs(np.array(mb["iota"]) - ma["iota"])) <= 0.02
        ),
        physics=all(physics),
        crosscheck=all(cross),
        refinement=all(r["passed"] for r in refs),
        cell_guards=bool(
            np.all(b["envelope"] <= np.maximum(1.1 * a["envelope"], a["envelope"] + 0.002))
            and np.max(abs(b["mean"] / a["mean"] - 1)) <= 0.02
        ),
        training_gain=narrow[1]["score"] <= 0.995 * narrow[0]["score"],
        holdout_gain=b["score"] <= 0.995 * a["score"],
        resolved_gain=a["score"] - b["score"] > 5 * uncertainty,
    )
    return dict(
        gates=gates,
        step3_pass=old.conclusion(gates),
        selected_x=candidate["x"],
        training_scores=[narrow[0]["score"], narrow[1]["score"]],
        holdout_scores=[[r["score"] for r in state] for state in metrics],
        holdout_relative_gain=1 - b["score"] / a["score"],
        observed_uncertainty_sum=uncertainty,
        max_mean_relative_change=float(np.max(abs(b["mean"] / a["mean"] - 1))),
        max_envelope_limit_ratio=float(
            np.max(b["envelope"] / np.maximum(1.1 * a["envelope"], a["envelope"] + 0.002))
        ),
        refinements=refs,
        max_quadrature_error=max(r["max_quadrature_error"] for state in metrics for r in state),
        validation=reference(validation_path),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("archive", "propose", "final"))
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "new immutable balanced audit path")
    folder = args.study.resolve()
    result = dict(
        status="error",
        arithmetic_and_source_pass=False,
        step3_pass=False,
        phase=args.phase,
        global_qi=False,
        sota=False,
        squid_c_ready=False,
    )
    try:
        original, binding, predecessor = sources(root_path())
        archive, values = phase_a(folder, original, binding, predecessor)
        owner, owner_path = archive, folder / "archive.json"
        result.update(
            source=binding,
            archive=reference(owner_path),
            archive_selected=archive["selected"],
            archive_domain_failures=sum(v is None for v in values),
        )
        if args.phase != "archive" and archive["selected"] is None:
            owner, _, certificate = phase_b(folder, original, binding, archive, values[0])
            owner_path = folder / "propose.json"
            result.update(
                proposal=reference(owner_path),
                model_certificate=certificate,
                proposal_selected=owner["selected"],
            )
        if args.phase == "final":
            require(owner["selected"] is not None, "actual selected improving candidate required")
            result.update(
                admission(folder, original, binding, predecessor, owner, owner_path, values[0])
            )
        result.update(status="completed", arithmetic_and_source_pass=True)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result.update(repository=git_state(root_path()), auditor=reference(Path(__file__)))
    write_json_atomic(args.output, result)
    print(json.dumps(result))
    return (
        0
        if result["arithmetic_and_source_pass"] and (args.phase != "final" or result["step3_pass"])
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
