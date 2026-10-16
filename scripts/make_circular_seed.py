"""Neutral six-coil seed for a new target (#115, #114): planar circles centred on the plasma.

Each base coil is a circle of radius `--radius` in the plane of its toroidal angle
phi_i = (i + 1/2) (pi / nfp) / 6, centred on the plasma's phi-section centre given by the
input's m = 0 boundary terms. The output is a public six-coil candidate for
`make_target_spec.py --seed-candidate`; flux normalization then sets the current.
Check its continuous geometry with `check_coils.py` before fitting.
"""

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT/"submissions/length-headroom-six-coil/candidate.json"


def circular_seed(data, radius):
    if not 0 < radius < 1:
        raise ValueError("coil radius between 0 and 1 m required")
    nfp = data["nfp"]
    r0 = {row["n"]: row["value"] for row in data["rbc"] if row["m"] == 0}
    z0 = {row["n"]: row["value"] for row in data["zbs"] if row["m"] == 0}
    candidate = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    width = len(candidate["base_coefficients"][0][0])
    base = []
    for i in range(6):
        phi = (i + 0.5)*(math.pi/nfp)/6
        # VMEC convention: R = sum rbc cos(m theta - n nfp phi), Z = sum zbs sin(...).
        centre_r = sum(v*math.cos(-n*nfp*phi) for n, v in r0.items())
        centre_z = sum(v*math.sin(-n*nfp*phi) for n, v in z0.items())
        x, y, z = ([0.0]*width for _ in range(3))
        # CurveXYZFourier order per axis: c(0), s(1), c(1), s(2), c(2), ...
        x[0], x[2] = centre_r*math.cos(phi), radius*math.cos(phi)
        y[0], y[2] = centre_r*math.sin(phi), radius*math.sin(phi)
        z[0], z[1] = centre_z, radius
        base.append([x, y, z])
    candidate["base_coefficients"] = base
    return candidate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="VMEC++ input JSON of the target")
    parser.add_argument("--radius", type=float, default=0.4, help="coil radius in m")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    seed = circular_seed(json.loads(args.input.read_text(encoding="utf-8")), args.radius)
    args.output.write_text(json.dumps(seed) + "\n", encoding="utf-8")
