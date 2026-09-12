"""Evaluate the complete registered fresh-QI matrix without replacing author outputs."""

import argparse
import json
from pathlib import Path

import netCDF4
import numpy as np
from inventory_qi_producers import reference
from run_jac_scaled_study import require_committed
from run_qi_resolution import checked

from fusion_baselines.clebsch_field import compare_fields
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.qi_field_grid import fidelity, nested_errors, sample
from fusion_baselines.qi_resolution import MATRIX, boundary_errors
from fusion_baselines.resource_guard import GIB, space_check

KEYS = ("psi", "g", "bt", "bp", "lt", "lp", "iota", "et", "ep", "mod_b")


def save(path, arrays):
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    return reference(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable field reports required")
    root = Path(__file__).resolve().parents[1]
    study = json.loads(args.study.read_text())
    inventory = json.loads(checked(study["inventory"]).read_text())
    expected = [(c["case"], ns, a) for c in inventory["cases"] for ns, a in MATRIX]
    if study["status"] != "completed" or [(r["case"], r["ns"], r["angular"])
                                           for r in study["cells"]] != expected:
        raise ValueError("all16 terminal matrix cells required, including failures")
    code = [root / p for p in ("scripts/evaluate_qi_resolution.py",
                               "src/fusion_baselines/qi_field_grid.py",
                               "src/fusion_baselines/clebsch_field.py",
                               "src/fusion_baselines/vmec_trace.py",
                               "src/fusion_baselines/qi_resolution.py")]
    for p in code:
        require_committed(root, p)
    for ref in [study["protocol"], *study["code"], *study["solver"]["sources"]]:
        checked(ref)
    old_path = root / "evidence/qi-clebsch-v1.json"
    old = json.loads(old_path.read_text())
    report = dict(repository=git_state(root), status="running", study=reference(args.study),
                  protocol=study["protocol"], original_screen=reference(old_path),
                  code=[reference(p) for p in code], old_replay=[], old_fields=[], cells=[],
                  all_arithmetic_screens_pass=False, absolute_drift_certified=False)
    args.raw.mkdir(parents=True)
    try:
        for row in old["grids"]:
            values = sample(checked(row["wout"]), row["surface"], row["resolution"])
            with np.load(checked(row["arrays"]), allow_pickle=False) as stored:
                errors = {k: float(np.max(abs(values[k] - stored[k])) /
                                   max(1, float(np.max(abs(stored[k]))))) for k in values
                          if k in stored}
            report["old_replay"].append(dict(case=row["case"], surface=row["surface"],
                                             resolution=row["resolution"], errors=errors))
            if max(errors.values()) > 1e-12:
                raise ValueError("old24-grid matrix replay failed")
        historical = {}
        for case in inventory["cases"]:
            for s in (0.25, 0.5, 0.75):
                values = sample(checked(case["wout"]), s, 128)
                path = args.raw / f"old-{case['case']}-s{s}.npz"
                report["old_fields"].append(dict(case=case["case"], surface=s,
                                                  wout=case["wout"], arrays=save(path, values)))
                historical[case["case"], s] = values
        for number, cell in enumerate(study["cells"]):
            space_check(root, 2 * GIB)
            row = dict(case=cell["case"], ns=cell["ns"], angular=cell["angular"], grids=[],
                       status="pending", numerically_converged=cell["numerically_converged"])
            report["cells"].append(row)
            if not cell["numerically_converged"]:
                row.update(status="unavailable", reason="solver cell not converged")
                write_json_atomic(args.output, report)
                continue
            wout = checked(cell["wout"])
            effective = json.loads(checked(cell["effective"]).read_text())
            with netCDF4.Dataset(wout) as ds:
                row["boundary_errors"] = boundary_errors(ds, effective)
                new_volume = float(ds["volume_p"][...])
            with netCDF4.Dataset(checked(cell["historical_wout"])) as ds:
                old_volume = float(ds["volume_p"][...])
            row["volume_error"] = abs(new_volume - old_volume) / abs(old_volume)
            if max(row["boundary_errors"].values()) > 1e-12:
                raise ValueError("new equilibrium changed fixed author boundary")
            for s in (0.25, 0.5, 0.75):
                coarse, coarse_errors = None, {}
                for n in (64, 128):
                    values = sample(wout, s, n)
                    native, clebsch, errors, checks = compare_fields(
                        **{k: values[k] for k in KEYS})
                    values.update(native=native, clebsch=clebsch)
                    grid = dict(surface=s, resolution=n, errors=errors, checks=checks,
                                physical_screen_pass=all(checks.values()),
                                arrays=save(args.raw / f"cell-{number}-s{s}-n{n}.npz", values))
                    if coarse is not None:
                        grid["nested_errors"] = nested_errors(coarse, values)
                        grid["error_refinement"] = {k: abs(errors[k] - coarse_errors[k])
                                                     for k in ("poloidal", "toroidal",
                                                               "cartesian", "magnitude")}
                        grid["fidelity"] = fidelity(values, historical[cell["case"], s])
                    coarse, coarse_errors = values, errors
                    row["grids"].append(grid)
                write_json_atomic(args.output, report)
            row.update(status="completed", physical_screen_pass=all(
                g["physical_screen_pass"] for g in row["grids"]))
            row["arithmetic_screen_pass"] = all(
                max(g.get("nested_errors", {"none": 0}).values()) <= 1e-12
                and max(g.get("error_refinement", {"none": 0}).values()) <= 1e-5
                for g in row["grids"])
            row["fidelity_screen_pass"] = row["volume_error"] <= 1e-3 and all(
                max(g.get("fidelity", {"none": 0}).values()) <= 1e-3 for g in row["grids"])
            print(row["case"], row["ns"], row["angular"], row["physical_screen_pass"],
                  row["arithmetic_screen_pass"], row["fidelity_screen_pass"], flush=True)
            write_json_atomic(args.output, report)
        report.update(status="completed", all_arithmetic_screens_pass=all(
            r.get("arithmetic_screen_pass", False) for r in report["cells"]),
            all_physical_screens_pass=all(r.get("physical_screen_pass", False)
                                          for r in report["cells"]))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_arithmetic_screens_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
