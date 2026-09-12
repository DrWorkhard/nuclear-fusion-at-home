"""Bind the four author inputs/Wouts and distinguish producer from iteration style."""

import argparse
import json
import subprocess
from pathlib import Path

import f90nml
import netCDF4
import numpy as np

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic

INPUTS = {
    "nfp2-vacuum": "qifiles-v1/Files/configurations/nfp2/vacuum/input.QI_nfp2",
    "nfp2-beta2": "qifiles-finite-beta-v1/Files/configurations/nfp2/beta/input.nfp2_beta_2.00",
    "nfp3-vacuum": "qifiles-v1/Files/configurations/nfp3/vacuum/input.QI_nfp3",
    "nfp3-beta2": "qifiles-finite-beta-v1/Files/configurations/nfp3/beta/input.nfp3_beta_2.00",
}


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("immutable new inventory required")
    root = Path(__file__).resolve().parents[1]
    rows = []
    for case, relative in INPUTS.items():
        input_path = root / "external/data" / relative
        source = root / f"evidence/qi-radial-action-v1/{case}.json"
        old = json.loads(source.read_text())
        wout = Path(old["wout"]["path"])
        if reference(wout) != old["wout"]:
            raise ValueError("historical Wout changed")
        nml = f90nml.read(input_path)["indata"]
        with netCDF4.Dataset(wout) as ds:
            scalars = {k: np.asarray(ds[k][...]).item() for k in (
                "version_", "ns", "nfp", "mpol", "ntor", "niter", "ftolv",
                "fsqr", "fsqz", "fsql", "ier_flag", "signgs")}
            scalars["edge_flux"] = float(ds["phi"][-1])
        matched = all(scalars[k] == nml[k] for k in ("nfp", "mpol", "ntor"))
        matched &= scalars["ns"] == nml["ns_array"][-1]
        matched &= scalars["edge_flux"] == nml["phiedge"]
        rows.append(dict(case=case, source=reference(source), input=reference(input_path),
                         wout=reference(wout), metadata=scalars,
                         input_controls={k: nml[k] for k in (
                             "nfp", "mpol", "ntor", "ns_array", "ftol_array", "niter_array",
                             "phiedge", "ncurr", "curtor", "pres_scale", "am", "ac",
                             "pmass_type", "pcurr_type", "delt", "nstep")},
                         dimensions_and_flux_match=bool(matched)))
    code = """
import hashlib, importlib.metadata, json, pathlib, vmecpp
d = importlib.metadata.distribution('vmecpp')
files = [pathlib.Path(vmecpp.__file__)]
files += [pathlib.Path(d.locate_file(p)) for p in d.files if str(p).endswith('.so')]
print(json.dumps(dict(version=d.version, iteration_styles=[v.value for v in vmecpp.IterationStyle],
    sources=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])))
"""
    command = [str(root / "environments/vmecpp/.venv/bin/python"), "-c", code]
    process = subprocess.run(command, capture_output=True, text=True, check=True, cwd=root)
    sources = [root / p for p in (
        "external/stellopt-v251/VMEC2000/Sources/General/vmec_params.f",
        "external/stellopt-v251/PARVMEC/Sources/General/vmec_params.f",
        "external/vmecpp/src/vmecpp/cpp/vmecpp/vmec/output_quantities/output_quantities.cc",
        "external/vmecpp/src/vmecpp/cpp/vmecpp/common/sizes/sizes.cc",
        "external/simsopt/src/simsopt/mhd/vmec_diagnostics.py")]
    result = dict(repository=git_state(root), code=reference(Path(__file__)), cases=rows,
                  vmecpp=json.loads(process.stdout), probe=dict(command=command,
                  returncode=process.returncode, stderr=process.stderr),
                  illustrative_sources=[reference(p) for p in sources],
                  checkout=git_state(root / "external/vmecpp"),
                  all_dimensions_and_flux_match=all(r["dimensions_and_flux_match"] for r in rows),
                  all_author_wouts_version_9=all(r["metadata"]["version_"] == 9 for r in rows),
                  exact_historical_producer_identified=False, new_equilibria=0)
    write_json_atomic(args.output, result)
    print(json.dumps({k: result[k] for k in (
        "all_dimensions_and_flux_match", "all_author_wouts_version_9")}))
    return 0 if result["all_dimensions_and_flux_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
