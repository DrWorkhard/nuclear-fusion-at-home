"""Screen maximum-J and omnigenity using the published Goodman et al. routines."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

import netCDF4
import numpy as np
from scipy.interpolate import UnivariateSpline


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


class Struct:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class WoutAdapter:
    """Match the array orientation exposed by the legacy SIMSOPT Vmec wrapper."""

    transposed = {
        "lmns",
        "rmnc",
        "gmnc",
        "zmns",
        "bmnc",
        "bsupvmnc",
        "bsubumnc",
        "bsubvmnc",
        "bsubsmns",
    }

    def __init__(self, path: Path):
        with netCDF4.Dataset(path) as dataset:
            for name, variable in dataset.variables.items():
                value = np.asarray(variable[:]).copy()
                if value.ndim == 0:
                    value = value.item()
                elif name in self.transposed:
                    value = value.T
                setattr(self, name, value)
            self.lasym = bool(np.asarray(dataset["lasym__logical__"][:]).item())


class VmecAdapter:
    def __init__(self, path: Path):
        self.wout = WoutAdapter(path)

    def run(self) -> None:
        pass


def load_published_functions(path: Path):
    """Compile only the scientific definitions, excluding plotting side effects."""
    wanted = {
        "J_B",
        "Tree",
        "TracedFieldline",
        "fzero_residuals_function",
        "get_roots",
    }
    tree = ast.parse(path.read_text(), filename=str(path))
    selected = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in wanted
    ]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {
        "np": np,
        "Struct": Struct,
        "UnivariateSpline": UnivariateSpline,
    }
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["TracedFieldline"], namespace["J_B"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wout", type=Path)
    parser.add_argument("published_script", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ns", type=int, default=10)
    parser.add_argument("--nbj", type=int, default=10)
    parser.add_argument("--nphi", type=int, default=401)
    parser.add_argument("--nalpha", type=int, default=10)
    parser.add_argument("--nfpinc", type=int, default=2)
    args = parser.parse_args()

    trace, evaluate_j = load_published_functions(args.published_script)
    vmec = VmecAdapter(args.wout)
    surfaces = np.linspace(0.05, 0.95, args.ns)
    traced = [
        trace(
            vmec,
            phi_start=0,
            nphi=args.nphi,
            alpha0=0,
            nalpha=args.nalpha,
            nfpinc=args.nfpinc,
            snorm=float(surface),
            verbose=False,
        )
        for surface in surfaces
    ]
    global_bmin = max(float(np.min(values.B)) for values in traced)
    global_bmax = min(float(np.max(values.B)) for values in traced)
    bounce_fields = np.linspace(1.01 * global_bmin, 0.99 * global_bmax, args.nbj)

    means = np.full((args.ns, args.nbj), np.nan)
    relative_spreads = np.full_like(means, np.nan)
    for surface_index, values in enumerate(traced):
        for bounce_index, bounce_field in enumerate(bounce_fields):
            j_values = np.asarray(evaluate_j(values, bounce_field, args.nfpinc))
            j_values = j_values[np.isfinite(j_values)]
            if j_values.size:
                means[surface_index, bounce_index] = float(np.mean(j_values))
                denominator = max(abs(float(np.mean(j_values))), np.finfo(float).tiny)
                relative_spreads[surface_index, bounce_index] = float(
                    (np.max(j_values) - np.min(j_values)) / denominator
                )

    radial_differences = np.diff(means, axis=0)
    valid_slopes = np.isfinite(radial_differences)
    maximum_j = radial_differences < 0
    valid_spreads = relative_spreads[np.isfinite(relative_spreads)]
    result = {
        "schema_version": 1,
        "metric": "published_J_routine_maximum_J_screen",
        "definition": {
            "maximum_j_fraction": "fraction of valid adjacent radial mean-J differences < 0",
            "relative_J_spread": "(max_alpha J - min_alpha J) / abs(mean_alpha J)",
        },
        "resolution": {
            "ns": args.ns,
            "nBj": args.nbj,
            "nphi": args.nphi,
            "nalpha": args.nalpha,
            "nfpinc": args.nfpinc,
        },
        "surface_grid": surfaces.tolist(),
        "bounce_field_grid": bounce_fields.tolist(),
        "maximum_j_fraction": float(np.sum(maximum_j & valid_slopes) / np.sum(valid_slopes)),
        "relative_J_spread_median": float(np.median(valid_spreads)),
        "relative_J_spread_max": float(np.max(valid_spreads)),
        "valid_mean_J_fraction": float(np.mean(np.isfinite(means))),
        "finite": bool(valid_spreads.size and np.any(valid_slopes)),
        "inputs": {
            "wout_sha256": sha256(args.wout),
            "published_script_sha256": sha256(args.published_script),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["finite"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
