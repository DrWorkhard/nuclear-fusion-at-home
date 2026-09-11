"""Run the preregistered expanded action and contour screens without overwrite."""

import argparse
import json
import time
from pathlib import Path

import netCDF4
import numpy as np

from fusion_baselines.bounce_action import action_envelope, bounce_wells
from fusion_baselines.contour_topology import surface_field, two_root_winding
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.vmec_trace import trace_geometry

SURFACES = [0.1, 0.25, 0.5, 0.75, 0.9]
PITCHES = [0.01, 0.03, 0.1, 0.3, 0.5, 0.7, 0.9, 0.97, 0.99]
TRACE_LEVELS = [(801, 32, 2), (1601, 32, 2), (3201, 32, 2), (3201, 64, 2)]
CONTOUR_LEVELS = [(128, 256), (256, 512), (512, 1024)]


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def compare_levels(previous, current, *, compare_actions):
    checks = []
    for old, new in zip(previous["cells"], current["cells"], strict=True):
        if (old["s"], old["bounce_field"]) != (new["s"], new["bounce_field"]):
            raise ValueError("mismatched comparison cells")
        a, b = old["envelope"], new["envelope"]
        change = abs(a - b) if a is not None and b is not None else None
        tolerance = max(0.002, 0.05 * a) if a is not None else None
        check = {
            "s": new["s"],
            "q": new["q"],
            "bounce_field": new["bounce_field"],
            "envelope_change": change,
            "envelope_tolerance": tolerance,
            "pass": change is not None and change <= tolerance,
        }
        if compare_actions:
            counts_match = old["complete_wells_per_alpha"] == new["complete_wells_per_alpha"]
            relative = None
            if counts_match and old["complete_alpha_coverage"] == 1:
                relative = max(
                    abs(y / x - 1)
                    for aa, bb in zip(old["actions_by_alpha"], new["actions_by_alpha"], strict=True)
                    for x, y in zip(aa, bb, strict=True)
                )
            check.update(
                well_counts_match=counts_match,
                max_relative_action_change=relative,
            )
            check["pass"] &= counts_match and relative is not None and relative <= 1e-3
        checks.append(check)
    return {"checks": checks, "pass": all(c["pass"] for c in checks)}


def run_case(root, case, destination, raw_root, provenance):
    start = time.monotonic()
    source = root / f"evidence/qi-measurement-v1/{case}.json"
    frozen = json.loads(source.read_text())
    wout = Path(frozen["inputs"]["wout"]["path"])
    if sha256_file(wout) != frozen["inputs"]["wout"]["sha256"]:
        raise ValueError("wout hash mismatch")
    lower, upper = frozen["coarse_common_interval"]
    fields = [lower + q * (upper - lower) for q in PITCHES]
    result = {
        **provenance,
        "case": case,
        "status": "running",
        "v1_evidence": reference(source),
        "wout": reference(wout),
        "surfaces": SURFACES,
        "q": PITCHES,
        "bounce_fields": fields,
        "frozen_v1_common_interval": [lower, upper],
        "action_levels": [],
        "contour_levels": [],
        "scientific_QI_qualification_pass": False,
    }
    try:
        for level, resolution in enumerate(TRACE_LEVELS):
            record = {"resolution": list(resolution), "traces": [], "cells": []}
            for s in SURFACES:
                print(f"{case}: action level={level} s={s}", flush=True)
                trace = trace_geometry(wout, s, *resolution)
                raw = raw_root / case / f"trace-{level}-s{s}.npz"
                raw.parent.mkdir(parents=True, exist_ok=True)
                with raw.open("xb") as stream:
                    np.savez_compressed(
                        stream, **{k: trace[k] for k in ["B", "length", "alpha", "phi"]}
                    )
                record["traces"].append({"s": s, **reference(raw)})
                for q, bstar in zip(PITCHES, fields, strict=True):
                    wells = [
                        bounce_wells(trace["length"][:, a], trace["B"][:, a], bstar)
                        for a in range(resolution[1])
                    ]
                    record["cells"].append(
                        {
                            "s": s,
                            "q": q,
                            "bounce_field": bstar,
                            **action_envelope(wells),
                            "actions_by_alpha": [
                                [w.action for w in line if w.complete] for line in wells
                            ],
                        }
                    )
            result["action_levels"].append(record)
            write_json_atomic(destination, result)
        result["action_comparisons"] = [
            compare_levels(old, new, compare_actions=index == 1)
            for index, (old, new) in enumerate(
                zip(
                    result["action_levels"][:-1],
                    result["action_levels"][1:],
                    strict=True,
                )
            )
        ]
        result["action_screen_pass"] = all(c["pass"] for c in result["action_comparisons"]) and all(
            c["complete_alpha_coverage"] == 1
            for level in result["action_levels"]
            for c in level["cells"]
        )
        for level, resolution in enumerate(CONTOUR_LEVELS):
            record = {"resolution": list(resolution), "surfaces": [], "cells": []}
            for s in SURFACES:
                print(f"{case}: contour level={level} s={s}", flush=True)
                field = surface_field(wout, s, *resolution)
                raw = raw_root / case / f"surface-{level}-s{s}.npz"
                with raw.open("xb") as stream:
                    np.savez_compressed(stream, B=field)
                record["surfaces"].append({"s": s, **reference(raw)})
                for q, bstar in zip(PITCHES, fields, strict=True):
                    record["cells"].append(
                        {
                            "s": s,
                            "q": q,
                            "bounce_field": bstar,
                            **two_root_winding(field, bstar),
                        }
                    )
            result["contour_levels"].append(record)
            write_json_atomic(destination, result)
        result["contour_classifications_stable"] = all(
            len({level["cells"][i]["classification"] for level in result["contour_levels"]}) == 1
            for i in range(len(SURFACES) * len(PITCHES))
        )
        result["contour_screen_pass"] = result["contour_classifications_stable"] and all(
            c["pass"] for level in result["contour_levels"] for c in level["cells"]
        )
        result["all_bounded_screens_pass"] = (
            result["action_screen_pass"] and result["contour_screen_pass"]
        )
        result["status"] = "completed"
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic() - start
        write_json_atomic(destination, result)
    return result["all_bounded_screens_pass"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("evidence/qi-coverage-v2"))
    parser.add_argument("--raw", type=Path, default=Path("artifacts/qi-coverage-v2"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("output/raw directory already exists; preserve prior evidence")
    provenance = {
        "schema_version": 1,
        "repository": git_state(root),
        "host": host_state(),
        "versions": {"numpy": np.__version__, "netCDF4": netCDF4.__version__},
        "protocol": reference(root / "docs/qi/QI_COVERAGE_TOPOLOGY_PROTOCOL.md"),
        "code": [
            reference(path)
            for path in [
                Path(__file__),
                root / "src/fusion_baselines/bounce_action.py",
                root / "src/fusion_baselines/vmec_trace.py",
                root / "src/fusion_baselines/contour_topology.py",
            ]
        ],
    }
    passed = []
    for case in ["nfp1", "nfp2", "nfp3"]:
        passed.append(run_case(root, case, args.output / f"{case}.json", args.raw, provenance))
    print(json.dumps({"case_passes": passed, "scientific_QI_qualification_pass": False}))
    return 0 if all(passed) else 2


if __name__ == "__main__":
    raise SystemExit(main())
