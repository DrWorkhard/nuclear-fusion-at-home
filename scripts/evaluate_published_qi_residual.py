"""Evaluate the Goodman et al. QI target from its published code and Boozer data.

This adapter intentionally executes the data release's ``Targets.py`` rather than
silently reimplementing the metric. A minimal Boozer/VMEC interface supplies the
already-published Boozer transform and VMEC profiles, so no legacy VMEC binary is
needed for this regression.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

import netCDF4
import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


class Struct:
    """Compatibility stand-in for the small SIMSOPT attribute container."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class PublishedBoozer:
    """Expose a published boozmn file through the interface used by Targets.py."""

    dataset: dict[str, np.ndarray | float | int]

    def __init__(self, _vmec, _mpol: int, _ntor: int):
        data = self.dataset
        coefficients = np.asarray(data["bmnc_b"])[0]
        self.bx = Struct(
            xm_b=np.asarray(data["ixm_b"]),
            xn_b=np.asarray(data["ixn_b"]),
            bmnc_b=coefficients,
            bmns_b=np.zeros_like(coefficients),
            nfp=int(data["nfp_b"]),
        )

    def register(self, _snorm: float) -> None:
        pass

    def run(self) -> None:
        pass


class PublishedVmec:
    """Supply only the VMEC fields consumed by the published QI target."""

    def __init__(self, wout_path: Path):
        with netCDF4.Dataset(wout_path) as dataset:
            ns = int(np.asarray(dataset["ns"][:]).item())
            iotas = np.asarray(dataset["iotas"][:]).copy()
        self.s_half_grid = (np.arange(ns - 1) + 0.5) / (ns - 1)
        self.wout = Struct(lasym=False, ns=ns, iotas=iotas)

    def run(self) -> None:
        pass


def load_boozer(path: Path) -> dict[str, np.ndarray | float | int]:
    names = ["ixm_b", "ixn_b", "bmnc_b", "nfp_b", "jlist", "ns_b"]
    with netCDF4.Dataset(path) as dataset:
        return {name: np.asarray(dataset[name][:]).copy() for name in names}


def load_published_targets(path: Path):
    simsopt = types.ModuleType("simsopt")
    core = types.ModuleType("simsopt._core")
    util = types.ModuleType("simsopt._core.util")
    util.Struct = Struct
    mhd = types.ModuleType("simsopt.mhd")
    boozer = types.ModuleType("simsopt.mhd.boozer")
    boozer.Boozer = PublishedBoozer
    sys.modules.update(
        {
            "simsopt": simsopt,
            "simsopt._core": core,
            "simsopt._core.util": util,
            "simsopt.mhd": mhd,
            "simsopt.mhd.boozer": boozer,
        }
    )
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("published_qi_targets", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.Boozer = PublishedBoozer
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("boozmn", type=Path)
    parser.add_argument("wout", type=Path)
    parser.add_argument("targets", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--nphi", type=int, default=601)
    parser.add_argument("--nalpha", type=int, default=75)
    parser.add_argument("--nbj", type=int, default=401)
    parser.add_argument("--nphi-out", type=int, default=2000)
    args = parser.parse_args()

    PublishedBoozer.dataset = load_boozer(args.boozmn)
    published = load_published_targets(args.targets)
    jlist = np.asarray(PublishedBoozer.dataset["jlist"])
    ns = int(np.asarray(PublishedBoozer.dataset["ns_b"]).item())
    snorm = float((int(jlist[0]) - 1) / (ns - 1))
    residual = published.QuasiIsodynamicResidual1(
        PublishedVmec(args.wout),
        snorm,
        nphi=args.nphi,
        nalpha=args.nalpha,
        nBj=args.nbj,
        nphi_out=args.nphi_out,
        arr_out=True,
    )
    result = {
        "schema_version": 1,
        "metric": "Goodman_et_al_QuasiIsodynamicResidual1_sum_squares",
        "source": "Zenodo record 7220257 Files/optimization_files/Targets.py",
        "surface_s": snorm,
        "resolution": {
            "nphi": args.nphi,
            "nalpha": args.nalpha,
            "nBj": args.nbj,
            "nphi_out": args.nphi_out,
        },
        "objective": float(np.sum(np.square(residual))),
        "residual_l2": float(np.linalg.norm(residual)),
        "finite": bool(np.all(np.isfinite(residual))),
        "inputs": {
            "boozmn_sha256": sha256(args.boozmn),
            "wout_sha256": sha256(args.wout),
            "targets_sha256": sha256(args.targets),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["finite"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
