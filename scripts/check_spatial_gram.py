"""Independent closed-form check of the additional Gauss-Newton spatial term."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.flux_metrics import quadratic_flux
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.spatial_flux import lift_flux


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(__file__).resolve().parents[1]
    source = root / "evidence/spatial-flux-local-vjp-v1.json"
    data = json.loads(source.read_text())
    if not data["all_pass"]:
        raise ValueError("passing local-point qualification required")
    records = []
    for case in data["cases"]:
        path = Path(case["arrays"]["path"])
        if sha256_file(path) != case["arrays"]["sha256"]:
            raise ValueError("qualification array hash mismatch")
        with np.load(path, allow_pickle=False) as a:
            z, dz, k = a["z"], a["dz"], float(a["scale"])
            if z@z/2 <= float(a["threshold"]):
                raise ValueError("Gram formula requires the active smooth branch")
            _, jac = lift_flux(z, dz, scale=k)
            u = dz.T@z
            closed = k*k/4*((z@z)*(dz.T@dz)-np.outer(u, u))
            difference = jac.T@jac-k*k*np.outer(u, u)
            err = float(np.max(np.abs(difference-closed)))/max(1., float(np.max(np.abs(closed))))
            eig = np.linalg.eigvalsh((difference+difference.T)/2)
            phi = quadratic_flux(a["field"], a["normal"])
            phi_err = float(abs(phi-z@z/2)/phi)
        checks = {"closed_form": err <= 1e-10,
                  "positive_semidefinite_screen": bool(eig[0] >= -1e-10*max(1., max(abs(eig)))),
                  "independent_raw_quadrature": phi_err <= 1e-10}
        records.append({"name": case["name"], "arrays": reference(path), "checks": checks,
            "gram_difference_error": err, "minimum_eigenvalue": float(eig[0]),
            "maximum_eigenvalue": float(eig[-1]), "raw_quadrature_relative_error": phi_err,
            "pass": all(checks.values())})
    result = {"schema_version": 1, "repository": git_state(root), "source": reference(source),
        "protocol": reference(root / "docs/optimization/SPATIAL_GRAM_CHECK.md"),
        "code": [reference(Path(__file__)),
                 reference(root / "src/fusion_baselines/spatial_flux.py"),
                 reference(root / "src/fusion_baselines/flux_metrics.py")],
        "cases": records, "all_pass": len(records) == 2 and all(r["pass"] for r in records),
        "additional_physics_calls": 0, "directed_rounding": False}
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
