"""Independently quadrature-check every recorded well against its hashed raw trace."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import sha256_file, write_json_atomic


def verify(path):
    data = json.loads(path.read_text())
    nodes, weights = np.polynomial.legendre.leggauss(128)
    errors = []
    checked = 0
    worst = 0.0
    for level in data["levels"]:
        traces = {}
        for surface, trace in zip(data["surfaces"], level["traces"], strict=True):
            raw = Path(trace["path"])
            if sha256_file(raw) != trace["sha256"]:
                raise ValueError(f"raw trace hash mismatch: {raw}")
            with np.load(raw) as arrays:
                traces[surface] = (arrays["B"].copy(), arrays["length"].copy())
        for cell in level["cells"]:
            b, length = traces[cell["s"]]
            for alpha, wells in enumerate(cell["wells_by_alpha"]):
                for well in wells:
                    left, right = well["left"], well["right"]
                    knots = np.concatenate(
                        (
                            [left],
                            length[(length[:, alpha] > left) & (length[:, alpha] < right), alpha],
                            [right],
                        )
                    )
                    midpoints = (knots[1:] + knots[:-1]) / 2
                    halfwidth = np.diff(knots) / 2
                    points = midpoints[:, None] + halfwidth[:, None] * nodes
                    field = np.interp(points.ravel(), length[:, alpha], b[:, alpha]).reshape(
                        points.shape
                    )
                    radicand = 1 - field / cell["bounce_field"]
                    if np.min(radicand) < -1e-12:
                        errors.append("reported well includes a forbidden field interval")
                    action = float(np.sum(halfwidth * (np.sqrt(np.maximum(radicand, 0)) @ weights)))
                    relative = abs(action / well["action"] - 1)
                    worst = max(worst, relative)
                    checked += 1
                    if not np.isfinite(relative) or relative > 1e-6:
                        errors.append(f"quadrature disagreement: {relative}")
    return {
        "input": {"path": str(path.resolve()), "sha256": sha256_file(path)},
        "wells_checked": checked,
        "max_relative_quadrature_discrepancy": worst,
        "tolerance": 1e-6,
        "errors": errors,
        "pass": not errors and checked > 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("verification output already exists")
    result = {
        "schema_version": 1,
        "method": "independent 128-point Gauss-Legendre per linear segment",
        "evaluation_code": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__)),
        },
        "cases": [verify(path) for path in args.inputs],
    }
    result["all_pass"] = all(case["pass"] for case in result["cases"])
    write_json_atomic(args.output, result)
    print(json.dumps(result, indent=2))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
