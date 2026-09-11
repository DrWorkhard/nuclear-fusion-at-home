"""Compare independently reconstructed geometric traces to frozen v1 raw traces."""

import argparse
import json
import time
from pathlib import Path

import numpy as np

from fusion_baselines.bounce_action import bounce_wells
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.vmec_trace import trace_geometry


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def case_check(path):
    data = json.loads(path.read_text())
    wout = Path(data["inputs"]["wout"]["path"])
    if sha256_file(wout) != data["inputs"]["wout"]["sha256"]:
        raise ValueError("wout hash mismatch")
    checks = []
    for level in data["levels"][:3]:
        nphi, nalpha, periods = level["resolution"]
        if [nphi, nalpha, periods] not in [[401, 16, 2], [801, 16, 2], [1601, 16, 2]]:
            raise ValueError("unexpected v1 resolution")
        for s, raw_info in zip(data["surfaces"], level["traces"], strict=True):
            print(f"independent trace: {data['case']} s={s} nphi={nphi}", flush=True)
            raw = Path(raw_info["path"])
            if sha256_file(raw) != raw_info["sha256"]:
                raise ValueError("raw trace hash mismatch")
            independent = trace_geometry(wout, s, nphi, nalpha, periods)
            with np.load(raw) as arrays:
                field_error = float(np.max(np.abs(independent["B"] / arrays["B"] - 1)))
                length_error = float(
                    np.max(np.abs(independent["length"] - arrays["length"]))
                    / np.max(arrays["length"])
                )
            cell_checks = []
            for cell in [c for c in level["cells"] if c["s"] == s]:
                maximum = 0.0
                topology = True
                coverage = True
                for alpha, stored in enumerate(cell["wells_by_alpha"]):
                    current = [
                        w
                        for w in bounce_wells(
                            independent["length"][:, alpha],
                            independent["B"][:, alpha],
                            cell["bounce_field"],
                        )
                        if w.complete
                    ]
                    expected = [w for w in stored if w["complete"]]
                    coverage &= bool(current) and bool(expected)
                    if len(current) != len(expected):
                        topology = False
                        continue
                    for actual, old in zip(current, expected, strict=True):
                        maximum = max(maximum, abs(actual.action / old["action"] - 1))
                cell_checks.append(
                    {
                        "bounce_field": cell["bounce_field"],
                        "max_relative_action_difference": maximum,
                        "well_counts_match": topology,
                        "full_alpha_coverage": coverage,
                        "pass": topology and coverage and maximum <= 1e-3,
                    }
                )
            check = {
                "s": s,
                "resolution": level["resolution"],
                "max_relative_B_difference": field_error,
                "normalized_cumulative_length_difference": length_error,
                "coordinate_residual_max": independent["coordinate_residual_max"],
                "cells": cell_checks,
                "pass": field_error <= 1e-8
                and length_error <= 1e-3
                and all(c["pass"] for c in cell_checks),
            }
            checks.append(check)
    return {
        "case": data["case"],
        "v1_evidence": reference(path),
        "checks": checks,
        "pass": len(checks) == 9 and all(c["pass"] for c in checks),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("cross-check output already exists")
    root = Path(__file__).resolve().parents[1]
    started = time.monotonic()
    result = {
        "schema_version": 1,
        "status": "running",
        "cases": [],
        "repository": git_state(root),
        "protocol": reference(root / "docs/qi/QI_TRACE_CROSSCHECK_PROTOCOL.md"),
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/vmec_trace.py"),
            reference(root / "src/fusion_baselines/bounce_action.py"),
        ],
        "thresholds": {"relative_B": 1e-8, "normalized_length": 1e-3, "relative_action": 1e-3},
    }
    try:
        for case in ["nfp1", "nfp2", "nfp3"]:
            result["cases"].append(case_check(root / f"evidence/qi-measurement-v1/{case}.json"))
            write_json_atomic(args.output, result)
        result["status"] = "completed"
        result["all_pass"] = all(case["pass"] for case in result["cases"])
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}", all_pass=False)
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic() - started
        write_json_atomic(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
