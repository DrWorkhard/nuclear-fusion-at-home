"""Summarize published NEO epsilon-effective and SIMPLE alpha-loss outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("neoclassical", type=Path)
    parser.add_argument("particles", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    neo = np.loadtxt(args.neoclassical)
    particles = np.loadtxt(args.particles)
    epsilon_effective_three_halves = neo[:, 2] ** 1.5
    plotted = particles[:, 0] >= 5e-5
    loss_fraction = 1.0 - particles[:, 1] - particles[:, 2]
    nearest_quarter = int(np.argmin(np.abs(neo[:, 0] - 0.25)))
    result = {
        "schema_version": 1,
        "source": "Goodman et al. Zenodo record 7220257 published outputs",
        "neoclassical": {
            "definition": "epsilon_eff^(3/2), matching PltEpsEffs_Losses_Vacc.py",
            "radial_points": int(neo.shape[0]),
            "minimum": float(np.min(epsilon_effective_three_halves)),
            "median": float(np.median(epsilon_effective_three_halves)),
            "maximum": float(np.max(epsilon_effective_three_halves)),
            "nearest_s_to_0p25": float(neo[nearest_quarter, 0]),
            "value_nearest_s_0p25": float(epsilon_effective_three_halves[nearest_quarter]),
        },
        "fast_particles": {
            "definition": "1 - passing_fraction - trapped_fraction for t >= 5e-5 s",
            "particle_count": int(particles[-1, 3]),
            "final_time_s": float(particles[-1, 0]),
            "final_loss_fraction": float(loss_fraction[-1]),
            "maximum_plotted_loss_fraction": float(np.max(loss_fraction[plotted])),
        },
        "inputs": {
            "neoclassical_sha256": sha256(args.neoclassical),
            "particles_sha256": sha256(args.particles),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
