"""Retrospective domain diagnosis; does not change the frozen screen outcomes."""

import argparse
import json
from pathlib import Path

import netCDF4
import numpy as np

from fusion_baselines.fourier_bounds import periodic_bilinear_error_bound
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.vmec_trace import _interpolate


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked_path(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"input hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("diagnostic output exists")
    root = Path(__file__).resolve().parents[1]
    result = {
        "schema_version": 1,
        "prospective": False,
        "repository": git_state(root),
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/fourier_bounds.py"),
            reference(root / "src/fusion_baselines/vmec_trace.py"),
        ],
        "cases": [],
        "screen_outcomes_modified": False,
        "limits": "Bounds apply to radially interpolated Fourier B in ordinary float arithmetic.",
    }
    for case in ["nfp1", "nfp2", "nfp3"]:
        path = root / f"evidence/qi-coverage-v2/{case}.json"
        data = json.loads(path.read_text())
        if data["status"] != "completed":
            raise ValueError("coverage experiment not complete")
        wout = checked_path(data["wout"])
        bounds = []
        with netCDF4.Dataset(wout) as d:
            full = np.linspace(0, 1, int(d["ns"][...]))
            half = (full[:-1] + full[1:]) / 2
            for raw in data["contour_levels"][-1]["surfaces"]:
                with np.load(checked_path(raw)) as arrays:
                    field = arrays["B"]
                coeff = _interpolate(half, d["bmnc"][1:], raw["s"])
                error = periodic_bilinear_error_bound(
                    coeff,
                    d["xm_nyq"][:],
                    d["xn_nyq"][:] / int(d["nfp"][...]),
                    field.shape,
                )
                lower, upper = float(field.min()) - error, float(field.max()) + error
                bounds.append(
                    {
                        "s": raw["s"],
                        "raw": raw,
                        "sampled_B_min": float(field.min()),
                        "sampled_B_max": float(field.max()),
                        "interpolation_error_bound": error,
                        "continuous_B_lower_bound": lower,
                        "continuous_B_upper_bound": upper,
                        "cells": [
                            {
                                "q": q,
                                "bounce_field": bstar,
                                "domain": "energetically_inaccessible"
                                if bstar < lower
                                else "passing_everywhere"
                                if bstar > upper
                                else "not_excluded_by_bounds",
                            }
                            for q, bstar in zip(data["q"], data["bounce_fields"], strict=True)
                        ],
                    }
                )
        result["cases"].append({"case": case, "evidence": reference(path), "bounds": bounds})
    write_json_atomic(args.output, result)


if __name__ == "__main__":
    main()
