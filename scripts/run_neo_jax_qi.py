"""Run a pinned local effective-ripple calculation on a Goodman QI wout."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path

import booz_xform as bx
import numpy as np
from neo_jax import NeoConfig, run_neo


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wout", type=Path, required=True)
    parser.add_argument("--published-profile", type=Path, required=True)
    parser.add_argument("--boozmn", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mboz", type=int, default=40)
    parser.add_argument("--nboz", type=int, default=40)
    args = parser.parse_args()

    published = np.loadtxt(args.published_profile)
    target_s = published[:, 0]

    transform = bx.Booz_xform()
    transform.verbose = False
    transform.read_wout(str(args.wout))
    transform.mboz = args.mboz
    transform.nboz = args.nboz
    s_in = np.asarray(transform.s_in)
    indices = np.asarray(
        [int(np.argmin(np.abs(s_in - value))) for value in target_s],
        dtype=np.int32,
    )
    transform.compute_surfs = indices
    transform.run()
    args.boozmn.parent.mkdir(parents=True, exist_ok=True)
    transform.write_boozmn(str(args.boozmn))

    config = NeoConfig(
        theta_n=64,
        phi_n=64,
        npart=40,
        multra=2,
        acc_req=0.02,
        nstep_per=20,
        nstep_min=200,
        nstep_max=500,
    )
    started = time.perf_counter()
    results = run_neo(str(args.boozmn), config=config, use_jax=True, progress=True)
    elapsed = time.perf_counter() - started

    calculated = np.asarray(results.epsilon_effective, dtype=float)
    # The published plotting routine explicitly raises column 3 to 3/2.
    reference = np.asarray(published[:, 2], dtype=float) ** 1.5
    relative_error = np.abs(calculated - reference) / reference
    ratios = calculated / reference
    diagnostics = [dict(item.diagnostics) for item in results]

    record = {
        "schema_version": 1,
        "claim_class": "local_solver_execution_with_failed_paper_crosscheck",
        "software": {
            "neo_jax": version("neo-jax"),
            "booz_xform": version("booz-xform"),
            "python": platform.python_version(),
        },
        "inputs": {
            "wout_sha256": sha256(args.wout),
            "published_profile_sha256": sha256(args.published_profile),
            "generated_boozmn_sha256": sha256(args.boozmn),
            "mboz": args.mboz,
            "nboz": args.nboz,
            "requested_s": target_s.tolist(),
            "selected_wout_half_grid_indices_zero_based": indices.tolist(),
            "selected_s": s_in[indices].tolist(),
        },
        "config": config.__dict__,
        "runtime_seconds": elapsed,
        "results": {
            "s": np.asarray(results.s, dtype=float).tolist(),
            "epsilon_effective_3_2": calculated.tolist(),
            "published_epsilon_effective_3_2": reference.tolist(),
            "calculated_over_published": ratios.tolist(),
            "median_calculated_over_published": float(np.median(ratios)),
            "maximum_relative_error": float(np.max(relative_error)),
            "all_finite": bool(np.all(np.isfinite(calculated))),
            "approximation_used": [
                bool(item.get("approximation_used", False)) for item in diagnostics
            ],
            "paper_crosscheck_passed": bool(np.max(relative_error) <= 0.1),
        },
        "interpretation_limits": [
            "The release contains only an edge boozmn file, so a new radial "
            "Boozer transform was generated from the published wout.",
            "The published NEO control deck and radial boozmn file are absent.",
            "Selected VMEC half-grid surfaces differ from requested published "
            "surfaces by at most 0.00125 in normalized toroidal flux.",
            "A successful local solver run is not a reproduction when the paper crosscheck fails.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, default=str) + "\n")
    print(json.dumps(record, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
