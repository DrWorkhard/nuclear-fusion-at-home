"""Independent old-loop field replay, input/solver audit and saved-array arithmetic."""

import argparse
import json
from pathlib import Path

import f90nml
import netCDF4
import numpy as np
from audit_qi_clebsch import recheck
from inventory_qi_producers import reference
from run_qi_resolution import checked

from fusion_baselines.clebsch_field import sample_coordinates
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.qi_resolution import MATRIX, author_input_checks, check_effective


def saved_errors(data, edge, expected):
    errors, identity = recheck(data, edge)
    return errors, identity and errors == expected


def direct_fidelity(data, old):
    result = {}
    for key in ("mod_b", "et", "ep"):
        result[key] = float(abs(data[key] - old[key]).max() / abs(old[key]).max())
    result["rz"] = float(max(abs(data[k] - old[k]).max() for k in ("radius", "height")) /
                          max(abs(old[k]).max() for k in ("radius", "height")))
    result["iota"] = float(abs(data["iota"].item() - old["iota"].item()))
    return result


def loop_errors(data, independent, stride):
    return {k: float(abs((data[k][::stride, ::stride] if independent[k].ndim >= 2
                         else data[k]) - independent[k]).max() /
                     max(1, float(abs(independent[k]).max()))) for k in independent}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("immutable new audit required")
    root = Path(__file__).resolve().parents[1]
    evaluation = json.loads(args.source.read_text())
    study = json.loads(checked(evaluation["study"]).read_text())
    inventory = json.loads(checked(study["inventory"]).read_text())
    expected = [(c["case"], ns, a) for c in inventory["cases"] for ns, a in MATRIX]
    for r in (evaluation, study):
        if r["status"] != "completed" or [(v["case"], v["ns"], v["angular"])
                                           for v in r["cells"]] != expected:
            raise ValueError("complete frozen matrix required")
        for ref in r["code"]:
            checked(ref)
    checked(evaluation["protocol"])
    for ref in study["solver"]["sources"]:
        checked(ref)
    historical = {(r["case"], r["surface"]): r for r in evaluation["old_fields"]}
    author_cases = {r["case"]: r for r in inventory["cases"]}
    if len(historical) != 12 or len(evaluation["old_fields"]) != 12:
        raise ValueError("twelve unique historical fine fields required")
    old_report = json.loads(checked(evaluation["original_screen"]).read_text())
    old_checks = []
    for row in evaluation["old_fields"]:
        if row["wout"] != author_cases[row["case"]]["wout"]:
            raise ValueError("historical field redirected from author case")
        native, _ = sample_coordinates(checked(row["wout"]), row["surface"], 32)
        with np.load(checked(row["arrays"]), allow_pickle=False) as data:
            error = loop_errors(data, native, 4)
        old_checks.append(dict(case=row["case"], surface=row["surface"], errors=error,
                               pass_replay=max(error.values()) <= 1e-12))
    # All24 original qualification entries remain ordered and must retain their hashes.
    expected_replay = [(r["case"], r["surface"], r["resolution"]) for r in old_report["grids"]]
    replay_valid = [(r["case"], r["surface"], r["resolution"])
                    for r in evaluation["old_replay"]] == expected_replay
    replay_valid &= all(max(r["errors"].values()) <= 1e-12 for r in evaluation["old_replay"])
    rows, new_calls = [], 0
    for cell, measured in zip(study["cells"], evaluation["cells"], strict=True):
        source = checked(cell["input"])
        original = json.loads(checked(cell["original"]).read_text())
        effective = json.loads(checked(cell["effective"]).read_text())
        checks = dict(author_input=all(author_input_checks(f90nml.read(source)["indata"],
                                                          original).values()),
                      effective=check_effective(original, effective, cell["ns"], cell["angular"]),
                      author_identity=cell["input"] == author_cases[cell["case"]]["input"]
                      and cell["historical_wout"] == author_cases[cell["case"]]["wout"])
        row = dict(case=cell["case"], ns=cell["ns"], angular=cell["angular"], checks=checks,
                   grids=[], physical_screen_pass=False)
        rows.append(row)
        if not cell["numerically_converged"]:
            checks["failure_preserved"] = measured["status"] == "unavailable"
            continue
        wout = checked(cell["wout"])
        with netCDF4.Dataset(wout) as ds:
            residuals = [float(ds[k][...]) for k in ("fsqr", "fsqz", "fsql")]
            checks["residuals"] = all(np.isfinite(v) and 0 <= v <= 1e-12 for v in residuals)
            solver = json.loads(checked(cell["solver"]).read_text())
            checks["solver_summary"] = solver["status"] == "completed" and all(
                solver["residuals"][k] == float(ds[k][...]) for k in ("fsqr", "fsqz", "fsql"))
            checks["dimensions"] = int(ds["ns"][...]) == cell["ns"] and all(
                int(ds[k][...]) == effective[k] for k in ("nfp", "mpol", "ntor"))
            edge, volume = float(ds["phi"][-1]), float(ds["volume_p"][...])
            checks["edge_flux"] = abs(edge - effective["phiedge"]) <= 1e-12 * abs(
                effective["phiedge"])
            for key, wkey in (("rbc", "rmnc"), ("zbs", "zmns")):
                coefficients = {(v["m"], v["n"]): v["value"] for v in effective[key]}
                actual = {(int(m), round(float(n) / effective["nfp"])): float(v) for m, n, v
                          in zip(ds["xm"][:], ds["xn"][:], ds[wkey][-1], strict=True)}
                error = max(abs(actual.get(k, 0) - coefficients.get(k, 0)) for k in
                            actual.keys() | coefficients.keys()) / max(
                                1, max(abs(v) for v in coefficients.values()))
                checks[key] = error <= 1e-12 and error == measured["boundary_errors"][key]
        with netCDF4.Dataset(checked(cell["historical_wout"])) as ds:
            old_volume = float(ds["volume_p"][...])
        volume_error = abs(volume - old_volume) / abs(old_volume)
        checks["volume_arithmetic"] = volume_error == measured["volume_error"]
        expected_grids = [(s, n) for s in (0.25, 0.5, 0.75) for n in (64, 128)]
        if [(g["surface"], g["resolution"]) for g in measured["grids"]] != expected_grids:
            raise ValueError("all six field grids required for every converged cell")
        coarse, earlier_errors, independent = {}, {}, {}
        for grid in measured["grids"]:
            s, n = grid["surface"], grid["resolution"]
            with np.load(checked(grid["arrays"]), allow_pickle=False) as arrays:
                data = {k: arrays[k] for k in arrays.files}
            if n == 64:
                independent, _ = sample_coordinates(wout, s, 32)
                new_calls += 1
            loop = loop_errors(data, independent, n // 32)
            errors, same = saved_errors(data, edge, grid["errors"])
            flags = {k: bool(np.isfinite(v) and (v > 0.1 if k in ("wrong_sign", "missing_2pi")
                                                else v <= 1e-3)) for k, v in errors.items()}
            gchecks = dict(independent_loop=max(loop.values()) <= 1e-12,
                           arithmetic=bool(same and flags == grid["checks"]),
                           classification=all(flags.values()) == grid["physical_screen_pass"])
            phi, theta = np.meshgrid(2 * np.pi * np.arange(n) / (n * effective["nfp"]),
                                     2 * np.pi * np.arange(n) / n, indexing="ij")
            gchecks["complete_angle_grid"] = (np.array_equal(data["phi"], phi)
                                              and np.array_equal(data["theta"], theta))
            if n == 128:
                nested = {k: float(abs((data[k][::2, ::2] if v.ndim >= 2 else data[k]) - v).max()
                                  / max(1, float(abs(v).max()))) for k, v in coarse.items()}
                refinement = {k: abs(errors[k] - earlier_errors[k]) for k in
                              ("poloidal", "toroidal", "cartesian", "magnitude")}
                with np.load(checked(historical[cell["case"], s]["arrays"]),
                             allow_pickle=False) as old:
                    differences = direct_fidelity(data, old)
                gchecks.update(nested_arithmetic=nested == grid["nested_errors"],
                               refinement_arithmetic=refinement == grid["error_refinement"],
                               fidelity_arithmetic=differences == grid["fidelity"])
            coarse, earlier_errors = data, errors
            row["grids"].append(dict(surface=s, resolution=n, checks=gchecks, loop_errors=loop,
                                      physical_screen_pass=all(flags.values())))
        row["physical_screen_pass"] = all(g["physical_screen_pass"] for g in row["grids"])
        checks["physical_classification"] = row["physical_screen_pass"] == measured[
            "physical_screen_pass"]
        # Aggregations must reflect their own metrics, even when the physical result is negative.
        arithmetic_screen = all(max(g.get("nested_errors", {"none": 0}).values()) <= 1e-12
                                and max(g.get("error_refinement", {"none": 0}).values()) <= 1e-5
                                for g in measured["grids"])
        fidelity_screen = volume_error <= 1e-3 and all(
            max(g.get("fidelity", {"none": 0}).values()) <= 1e-3 for g in measured["grids"])
        checks["aggregate_screens"] = (arithmetic_screen == measured["arithmetic_screen_pass"]
                                       and fidelity_screen == measured["fidelity_screen_pass"])
    aggregates = evaluation["all_arithmetic_screens_pass"] == all(
        r.get("arithmetic_screen_pass", False) for r in evaluation["cells"])
    aggregates &= evaluation["all_physical_screens_pass"] == all(
        r["physical_screen_pass"] for r in rows)
    passed = aggregates and replay_valid and all(r["pass_replay"] for r in old_checks) and all(
        all(r["checks"].values()) and all(all(g["checks"].values()) for g in r["grids"])
        for r in rows)
    report = dict(repository=git_state(root), source=reference(args.source),
        code=[reference(root / p) for p in (
            "scripts/audit_qi_resolution.py", "scripts/audit_qi_clebsch.py",
            "src/fusion_baselines/clebsch_field.py", "src/fusion_baselines/vmec_trace.py",
            "src/fusion_baselines/qi_resolution.py")],
        all_pass=bool(passed), cells=rows, historical_loop_checks=old_checks,
        old24_replay_bookkeeping=bool(replay_valid), new_wout_loop_field_calls=new_calls,
        aggregate_classifications=bool(aggregates),
        historical_loop_field_calls=12, new_equilibria=0, absolute_drift_certified=False)
    write_json_atomic(args.output, report)
    print(json.dumps({"all_pass": report["all_pass"], "new_wout_loop_field_calls": new_calls}))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
