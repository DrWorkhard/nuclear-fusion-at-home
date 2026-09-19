"""Independent complete-matrix audit of geometry-only exterior coil starts."""

import argparse
import json
from pathlib import Path

import numpy as np
from clear_coil_initialization_inputs import sources
from current_diagnostic_inputs import checked, reference

from fusion_baselines import clear_coil_geometry_audit as independent
from fusion_baselines.provenance import git_state, write_json_atomic

ROOT = Path(__file__).resolve().parents[1]
SCOPE = dict(
    field_calls=0,
    gradient_calls=0,
    equilibrium_solves=0,
    field_pass=False,
    transfer_pass=False,
    step4_pass=False,
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(ref):
    require(Path(ref["path"]).is_absolute(), "absolute immutable reference required")
    return json.loads(checked(ref).read_text())


def bind_tree(value, seen=None):
    if seen is None:
        seen = set()
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            key = (value["path"], value["sha256"])
            require(Path(key[0]).is_absolute(), "absolute provenance required")
            if key not in seen:
                checked(value)
                seen.add(key)
        else:
            for child in value.values():
                bind_tree(child, seen)
    elif isinstance(value, list):
        for child in value:
            bind_tree(child, seen)


def split(ref):
    meta = read(ref["metadata"])
    with np.load(checked(ref["arrays"]), allow_pickle=False) as stored:
        require(not (set(meta) & set(stored.files)), "array/metadata key collision")
        for key in stored.files:
            value = stored[key].copy()
            require(
                value.dtype.kind in "biuf" and np.isfinite(value).all(),
                "finite real numerical geometry arrays",
            )
            meta[key] = value
    return meta


def compare_tree(actual, expected, label):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected), f"{label}: keys")
        for key, value in expected.items():
            compare_tree(actual[key], value, f"{label}.{key}")
    elif type(expected) in (str, bool, int):
        require(type(actual) is type(expected) and actual == expected, f"{label}: identity")
    else:
        exact = isinstance(expected, np.ndarray) and expected.dtype.kind in "biu"
        independent.compare(actual, expected, label, exact=exact)


def levels():
    return [
        dict(
            target=target,
            nphi=n,
            ntheta=n,
            offset=offset,
            label=f"{target}-n{n}-shift{int(2 * offset)}",
        )
        for target in ("reference", "selected")
        for n, offset in ((256, 0), (512, 0), (512, 0.5))
    ]


def common(run, binding):
    require(
        type(run.get("schema_version")) is int
        and run["schema_version"] == 1
        and run.get("phase") == "geometry_initialization"
        and run.get("status") == "completed",
        "completed geometry-only schema1 matrix required",
    )
    require(
        run["source"] == binding
        and run["case_matrix"] == independent.cases()
        and binding["matrix"] == independent.cases(),
        "exact source and registered matrix",
    )
    require(
        binding["solver_configuration"]
        == dict(
            method="highs-ds",
            options=dict(
                time_limit=30.0,
                primal_feasibility_tolerance=1e-10,
                dual_feasibility_tolerance=1e-10,
                threads=1,
                parallel=False,
            ),
        ),
        "fixed native single-thread solver configuration",
    )
    require(
        all(type(run.get(k)) is type(v) and run[k] == v for k, v in SCOPE.items()),
        "no field work, invented currents or physics admission",
    )
    require(
        run["threads"]
        == {k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")},
        "single-thread geometry-only matrix",
    )
    require(
        run.get("geometry_pass") is False and run.get("selected") is None,
        "producer must leave independent geometry selection pending",
    )


def work_audit(run):
    clock = run["clock"]
    start, stop = clock["start_monotonic"], clock["parent_stop_monotonic"]
    config = read(run["execution_artifacts"]["config.json"])
    terminal = read(run["execution_artifacts"]["terminal.json"])
    require(
        config["start_monotonic"] == start
        and config["source"] == run["source"]
        and config["threads"] == run["threads"]
        and terminal == run["terminal"],
        "bound parent configuration and terminal records",
    )
    require(
        np.isfinite([start, stop]).all()
        and 0 <= stop - start <= 1805.5
        and clock["timeout_seconds"] == 1800
        and clock["check_interval"] == 0.5
        and clock["lp_timeout_seconds"] == 30
        and clock["termination_grace_seconds"] == 5
        and terminal["parent_stop_monotonic"] == stop
        and terminal["reason"] == "matrix_complete"
        and type(terminal["process"]["returncode"]) is int
        and terminal["process"]["returncode"] == 0
        and terminal["all_registered_attempts"] is True,
        "registered complete parent-guarded matrix timing",
    )
    expected = [
        (case["label"], i, repeat)
        for case in independent.cases()
        for i in range(case["nbase"])
        for repeat in (False, True)
    ]
    rows = run["attempts"]
    require(len(rows) == run["attempted_lps"] == 168, "all84 original and84 repeated attempts")
    previous = start
    for i, (row, identity) in enumerate(zip(rows, expected, strict=True)):
        require(
            row["index"] == i
            and type(row["index"]) is int
            and type(row["base_index"]) is int
            and (row["case"], row["base_index"], row["repeat"]) == identity
            and type(row["repeat"]) is bool,
            "ordered contiguous original/repeated LP ledger",
        )
        original = read(row["attempt"])
        outcome = read(row["outcome"])
        require(
            original["status"] == "attempted"
            and all(
                original[k] == row[k]
                for k in ("index", "case", "base_index", "repeat", "problem", "started_monotonic")
            ),
            "original immutable LP attempt",
        )
        require(
            {k: v for k, v in row.items() if k not in ("attempt", "outcome")} == outcome,
            "unchanged persisted LP outcome",
        )
        require(
            row["status"] in ("completed", "failed")
            and previous <= row["started_monotonic"] <= start + 1800,
            "serial LP attempts within producer budget",
        )
        if row["status"] == "completed":
            require(
                row["started_monotonic"] <= row["completed_monotonic"] <= min(stop, start + 1800),
                "completed LP within parent budget",
            )
            require(
                row["elapsed_seconds"] == row["completed_monotonic"] - row["started_monotonic"]
                and 0 <= row["elapsed_seconds"] < 30,
                "strict per-LP wall-time accounting",
            )
            previous = row["completed_monotonic"]
        else:
            failure = read(row["failure"])
            require(
                row["started_monotonic"] <= row["failed_end_monotonic"] <= min(stop, start + 1800)
                and row["elapsed_seconds"] == row["failed_end_monotonic"] - row["started_monotonic"]
                and 0 <= row["elapsed_seconds"] < 30,
                "failed LP still consumes bounded recorded wall work",
            )
            require(
                set(failure) == {"error", "raised_monotonic"}
                and type(failure["error"]) is str
                and bool(failure["error"])
                and failure["error"] == row["error"]
                and row["started_monotonic"]
                <= failure["raised_monotonic"]
                <= row["failed_end_monotonic"],
                "bound original exception and in-attempt failure time",
            )
            previous = row["failed_end_monotonic"]
    return dict(
        attempted_lps=168,
        original_lps=84,
        repeated_lps=84,
        elapsed_seconds=float(stop - start),
        **SCOPE,
    )


def exact_repeat(first, second):
    keys = (
        "success",
        "status",
        "objective",
        "method",
        "options",
        "warnings",
        "x",
        "slack",
        "inequality_marginals",
        "lower_marginals",
        "upper_marginals",
    )
    return bool(all(k in first and k in second and first[k] == second[k] for k in keys))


def selected_sets(rows):
    result = {}
    for nbase in (6, 8):
        eligible = [
            row
            for row in rows
            if row["case"]["nbase"] == nbase and row.get("geometry_pass") is True
        ]
        result[f"n{nbase}"] = (
            min(
                eligible,
                key=lambda row: (
                    row["sum_base_lengths"],
                    row["case"]["d"],
                    0 if row["case"]["method"] == "circle" else 1,
                ),
            )["case"]["label"]
            if eligible
            else None
        )
    return result


def audit(run, root):
    binding = sources(root)
    common(run, binding)
    bind_tree(run)
    work = work_audit(run)
    inputs = [read(binding["targets"][key]["input"]) for key in ("reference", "selected")]
    require(len(run["surfaces"]) == 6, "both targets and all three surface grids")
    targets = {}
    surface_reports = []
    for row, level in zip(run["surfaces"], levels(), strict=True):
        require(
            row["status"] == "completed" and all(row[k] == v for k, v in level.items()),
            "fixed complete surface grid identity",
        )
        actual = split(row)
        expected = independent.surface(
            inputs[("reference", "selected").index(level["target"])],
            level["nphi"],
            level["ntheta"],
            level["offset"],
        )
        compare_tree(actual, expected, level["label"])
        targets[level["label"]] = expected
        surface_reports.append(
            dict(level, cover=expected["cover"], radius_lower=expected["radius_lower"], passed=True)
        )
    construction = [targets[f"{key}-n256-shift0"] for key in ("reference", "selected")]
    require(len(run["sets"]) == 12, "all registered geometric candidate sets")
    reports = []
    for set_row, case in zip(run["sets"], independent.cases(), strict=True):
        require(
            set_row["case"] == case and len(set_row["coils"]) == case["nbase"],
            "ordered complete set/base identities",
        )
        coil_reports, coefficients = [], []
        for i, row in enumerate(set_row["coils"]):
            phi = (i + 0.5) * np.pi / (2 * case["nbase"])
            require(row["base_index"] == i and row["phi"] == phi, "base radial plane identity")
            center = independent.origin(inputs, phi)
            independent.compare(row["center"], center, "analytic mean section origin")
            disks = independent.envelope(construction, phi, case["d"], case["r_floor"], center)
            compare_tree(split(row["disks"]), disks, "complete conservative disk envelope")
            model = independent.problem(disks, case["K"], center[0], case["r_floor"])
            compare_tree(split(row["problem"]), model, "original unscaled support LP")
            require(len(row["attempts"]) == 2, "one original and one identical LP repeat")
            solutions = []
            for repeated, item in enumerate(row["attempts"]):
                attempt = run["attempts"][item["index"]]
                require(
                    attempt["case"] == case["label"]
                    and attempt["base_index"] == i
                    and attempt["repeat"] is bool(repeated)
                    and item["outcome"] == attempt["outcome"]
                    and attempt["problem"] == row["problem"],
                    "same-problem LP repeat provenance",
                )
                solutions.append(
                    read(attempt["solution"]) if attempt["status"] == "completed" else None
                )
            certs = [
                independent.dual_certificate(model, solution)
                if solution is not None
                else dict(solved=False, passed=False, infeasibility_proven=False)
                for solution in solutions
            ]
            repeated = bool(all(s is not None for s in solutions) and exact_repeat(*solutions))
            report = dict(
                base_index=i,
                lp_certificates=certs,
                exact_repeat=repeated,
                continuous=None,
                export_transfer=None,
                support_coefficients=None,
                available_geometry=False,
            )
            primal = solutions[0].get("x") if solutions[0] is not None else None
            if primal is not None:
                h = np.asarray(primal, dtype=float)[: 2 * case["K"] + 1]
                coef = independent.export_coefficients(h, center, phi, case["order"])
                independent.compare(row["coefficients"], coef, "canonical exported support curve")
                coefficients.append(coef)
                report.update(
                    available_geometry=True,
                    support_coefficients=h.tolist(),
                    continuous=independent.continuous_certificate(
                        model, h, disks, center, case["r_floor"]
                    ),
                )
            else:
                require(row["coefficients"] is None, "no fabricated coil without primal solution")
            coil_reports.append(report)
        result = dict(
            case=case,
            coils=coil_reports,
            distances=[],
            geometry_pass=False,
            available_geometry=len(coefficients) == case["nbase"],
            sum_base_lengths=None,
            analytic_coil_lower=None,
        )
        if result["available_geometry"]:
            snapshot = read(set_row["snapshot"])
            independent.validate_snapshot(snapshot)
            require(
                snapshot["case"] == case and snapshot["sources"] == binding["targets"],
                "exported geometry source and case identity",
            )
            independent.compare(
                snapshot["base_coefficients"], coefficients, "all exported base curves"
            )
            for i, report in enumerate(coil_reports):
                report["export_transfer"] = independent.export_certificate(
                    report["continuous"],
                    report["support_coefficients"],
                    coefficients[i],
                    snapshot["base_coefficients"][i],
                    case["r_floor"],
                    case["d"],
                )
            # Even long or LP-rejected candidates retain every independent direct grid.
            for level in levels():
                direct = independent.distance_certificate(snapshot, targets[level["label"]])
                result["distances"].append(dict(target=level["target"], **direct))
            continuous = [r["continuous"] for r in coil_reports]
            exported = [r["export_transfer"] for r in coil_reports]
            result["sum_base_lengths"] = float(sum(c["length"] for c in continuous))
            radial_lower = min(c["radial_lower"] for c in continuous)
            analytic_lower = float(
                2 * radial_lower * np.sin(np.pi / (4 * case["nbase"]))
                - 2 * max(c["position_error"] + c["coefficient_rounding_pad"] for c in exported)
            )
            result["analytic_coil_lower"] = analytic_lower
            result["geometry_pass"] = bool(
                all(
                    r["exact_repeat"] and all(c["passed"] for c in r["lp_certificates"])
                    for r in coil_reports
                )
                and all(
                    c["support_pass"]
                    and c["length_pass"]
                    and c["curvature_pass"]
                    and c["plasma_pass"]
                    for c in exported
                )
                and analytic_lower >= 0.06
                and all(
                    d["coil_pass"]
                    and d["plasma_pass"]
                    and d["sampled_length_pass"]
                    and d["sampled_curvature_pass"]
                    for d in result["distances"]
                )
            )
        else:
            require(set_row["snapshot"] is None, "no incomplete physical snapshot")
        reports.append(result)
        print(
            json.dumps(dict(case=case["label"], geometry_pass=result["geometry_pass"])), flush=True
        )
    selection = selected_sets(reports)
    accepted = any(r["geometry_pass"] for r in reports)
    return dict(
        status="completed",
        phase="geometry_initialization",
        source=binding,
        arithmetic_and_source_pass=True,
        work=work,
        surface_checks=surface_reports,
        sets=reports,
        selected=selection,
        geometry_pass=accepted,
        all_pass=accepted,
        all_twelve_sets_checked=True,
        both_classes_pass=all(v is not None for v in selection.values()),
        **SCOPE,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        args.run.is_absolute() and not args.output.exists(), "absolute run and fresh audit output"
    )
    result = dict(
        status="error",
        arithmetic_and_source_pass=False,
        all_pass=False,
        geometry_pass=False,
        selected=None,
        **SCOPE,
    )
    try:
        result.update(audit(json.loads(args.run.read_text()), ROOT))
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result.update(
        run=reference(args.run), auditor=reference(Path(__file__)), repository=git_state(ROOT)
    )
    json.dumps(result, allow_nan=False)
    write_json_atomic(args.output, result)
    print(
        json.dumps(
            {
                k: result.get(k)
                for k in (
                    "status",
                    "arithmetic_and_source_pass",
                    "geometry_pass",
                    "selected",
                    "error",
                )
            }
        )
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
