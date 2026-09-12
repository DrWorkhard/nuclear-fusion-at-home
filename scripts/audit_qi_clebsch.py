"""Recompute signed-flux comparisons from archived point arrays, without field helper."""

import argparse
import json
from pathlib import Path

import netCDF4
import numpy as np

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"diagnostic source changed: {path}")
    return path


def recheck(data, edge_flux):
    psi = -edge_flux / (2 * np.pi)
    g, bt, bp = data["g"], data["bt"], data["bp"]
    tp, tt = psi * (1 + data["lt"]), psi * (data["iota"] - data["lp"])
    native, clebsch = np.empty_like(data["native"]), np.empty_like(data["clebsch"])
    for axis in range(3):
        native[..., axis] = bt * data["et"][..., axis] + bp * data["ep"][..., axis]
        clebsch[..., axis] = (tt * data["et"][..., axis] + tp * data["ep"][..., axis]) / g
    magnitude = np.sqrt(np.sum(native**2, axis=-1))
    error = dict(
        toroidal=float(np.max(np.abs(g * bp - tp)) / np.max(np.abs(tp))),
        poloidal=float(np.max(np.abs(g * bt - tt)) / max(abs(psi), np.max(np.abs(tt)))),
        cartesian=float(np.max(np.sqrt(np.sum((native - clebsch)**2, axis=-1))) /
                        magnitude.max()),
        magnitude=float(np.max(np.abs(magnitude - data["mod_b"])) / data["mod_b"].max()),
        wrong_sign=float(np.max(np.abs(g * bp + tp)) / np.max(np.abs(tp))),
        missing_2pi=float(np.max(np.abs(g * bp - 2 * np.pi * tp)) / np.max(np.abs(tp))),
    )
    return error, bool(
        np.array_equal(native, data["native"]) and np.array_equal(clebsch, data["clebsch"])
        and data["psi"].item() == psi)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit output required")
    root = Path(__file__).resolve().parents[1]
    report = json.loads(args.source.read_text())
    for ref in [report["protocol"], report["convention_source"], *report["code"]]:
        checked(ref)
    expected = [(case, s, n) for case in
                ("nfp2-vacuum", "nfp2-beta2", "nfp3-vacuum", "nfp3-beta2")
                for s in (0.25, 0.5, 0.75) for n in (16, 32)]
    if report["status"] != "completed" or [(r["case"], r["surface"], r["resolution"])
                                            for r in report["grids"]] != expected:
        raise ValueError("all24 fixed grids required")
    rows = []
    for row in report["grids"]:
        source_case = json.loads(checked(row["source"]).read_text())
        if row["wout"] != source_case["wout"]:
            raise ValueError("original physical case changed")
        with netCDF4.Dataset(checked(row["wout"])) as dataset:
            edge = float(dataset["phi"][-1])
            nfp = int(dataset["nfp"][...])
        with np.load(checked(row["arrays"]), allow_pickle=False) as data:
            errors, identity = recheck(data, edge)
            n = row["resolution"]
            phi, theta = np.meshgrid(2 * np.pi * np.arange(n) / (n * nfp),
                                     2 * np.pi * np.arange(n) / n, indexing="ij")
            identity &= np.array_equal(phi, data["phi"]) and np.array_equal(theta, data["theta"])
        checks = {k: bool(np.isfinite(v) and (v > 0.1 if k in ("wrong_sign", "missing_2pi")
                                            else v <= 1e-3)) for k, v in errors.items()}
        same = errors == row["errors"] and checks == row["checks"]
        rows.append(dict(case=row["case"], surface=row["surface"], resolution=n,
                         arithmetic_and_grid_identity=bool(same and identity),
                         independently_passed=all(checks.values()), errors=errors))
    result = dict(
        repository=git_state(root), source=reference(args.source), grids=rows,
        all_pass=all(r["arithmetic_and_grid_identity"] for r in rows),
        physical_screen_pass=all(r["independently_passed"] for r in rows),
        new_field_evaluations=0, absolute_drift_certified=False,
        code=reference(Path(__file__)),
    )
    write_json_atomic(args.output, result)
    print(json.dumps({k: result[k] for k in ("all_pass", "physical_screen_pass")}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
