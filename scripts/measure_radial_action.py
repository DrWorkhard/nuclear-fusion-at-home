"""Execute the four-case fixed-invariant radial-action pilot without overwrite."""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

from fusion_baselines.bounce_action import bounce_wells
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.radial_action import match_intervals, radial_sign_screen
from fusion_baselines.vmec_trace import trace_geometry

STEPS = [0.04, 0.02, 0.01]
RADII = [0.46, 0.48, 0.49, 0.5, 0.51, 0.52, 0.54]
NPHI = [801, 1601, 3201]
Q = [0.1, 0.3, 0.5, 0.7, 0.9]


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def wells_on_line(trace, alpha, bstar):
    wells = bounce_wells(trace["length"][:, alpha], trace["B"][:, alpha], bstar)
    return [{
        **well.record(),
        "phi_interval": np.interp(
            [well.left, well.right], trace["length"][:, alpha], trace["phi"]
        ).tolist(),
    } for well in wells]


def run_case(name, nfp, wout, destination, raw, provenance):
    start = time.monotonic()
    result = {**provenance, "case": name, "wout": reference(wout), "status": "running",
              "scientific_maximum_J_admission": False, "traces": [], "cells": []}
    traces = {}
    try:
        for level, nphi in enumerate(NPHI):
            for s in RADII:
                print(f"{name}: level={level} s={s}", flush=True)
                trace = trace_geometry(wout, s, nphi, 8, 4)
                traces[level, s] = trace
                path = raw / name / f"trace-{level}-s{s}.npz"
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    np.savez_compressed(stream, **trace)
                result["traces"].append({"level": level, "nphi": nphi, "s": s,
                    "coordinate_residual_max": trace["coordinate_residual_max"], **reference(path)})
            if level == 0:
                lower = max(float(t["B"].min(axis=0).max()) for t in traces.values())
                upper = min(float(t["B"].max(axis=0).min()) for t in traces.values())
                if not lower < upper:
                    raise ValueError("empty common sampled Bstar interval")
                result["coarse_common_interval"] = [lower, upper]
                result["bounce_fields"] = [lower + q * (upper - lower) for q in Q]
            write_json_atomic(destination, result)
        window = np.array([1, 3]) * 2 * np.pi / nfp
        for q, bstar in zip(Q, result["bounce_fields"], strict=True):
            for alpha in range(8):
                cell = {"q": q, "Bstar": bstar, "alpha_index": alpha,
                        "wells": [], "families": [], "matching_pass": False}
                result["cells"].append(cell)
                all_wells = {}
                for key, trace in traces.items():
                    wells = wells_on_line(trace, alpha, bstar)
                    all_wells[key] = [w for w in wells if w["complete"]]
                    cell["wells"].append({"level": key[0], "s": key[1], "wells": wells})
                anchor = [w for w in all_wells[0, 0.5]
                          if window[0] <= np.mean(w["phi_interval"]) <= window[1]]
                try:
                    mappings = {key: match_intervals(
                        [w["phi_interval"] for w in anchor],
                        [w["phi_interval"] for w in wells], window).tolist()
                        for key, wells in all_wells.items()}
                except ValueError as error:
                    cell["matching_error"] = str(error)
                    continue
                cell["matching_pass"] = True
                cell["matches"] = [{"level": key[0], "s": key[1], "indices": mapping}
                                   for key, mapping in mappings.items()]
                for family, well in enumerate(anchor):
                    selected = {key: wells[mappings[key][family]]["action"]
                                for key, wells in all_wells.items()}

                    def action(level, s, selected=selected):
                        key = (level, round(s, 2))
                        return selected[key]
                    stencil = np.array([[[action(level, 0.5 - h), action(level, 0.5 + h)]
                                         for h in STEPS] for level in range(3)])
                    a0 = action(2, 0.5)
                    cell["families"].append({"anchor": well, "action_stencil": stencil.tolist(),
                        "finest_anchor_action": a0, **radial_sign_screen(stencil, a0)})
        families = [f for c in result["cells"] for f in c["families"]]
        result["summary"] = {
            "cells": len(result["cells"]),
            "matching_failed_cells": sum(not c["matching_pass"] for c in result["cells"]),
            "matched_families": len(families),
            "sign_counts": dict(Counter(f["sign"] for f in families)),
            "refinement_failed_families": sum(not f["refinement_pass"] for f in families),
        }
        result["status"] = "completed"
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic() - start
        write_json_atomic(destination, result)
    print(name, result["summary"], flush=True)


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=root / "evidence/qi-radial-action-v1")
    parser.add_argument("--raw", type=Path, default=root / "artifacts/qi-radial-action-v1")
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("preserve existing output/raw directories")
    finite_path = root / "evidence/qi-finite-beta-inventory-v1.json"
    vacuum_path = root / "references/goodman_qi_transfer_cases.json"
    finite = json.loads(finite_path.read_text())
    vacuum = json.loads(vacuum_path.read_text())
    cases = []
    for nfp in (2, 3):
        path = root / f"external/data/qifiles-v1/Files/configurations/nfp{nfp}/vacuum"
        cases.append((f"nfp{nfp}-vacuum", nfp, path / f"wout_QI_nfp{nfp}.nc",
                      vacuum["cases"][f"nfp{nfp}"]["wout_sha256"]))
        case = next(c for c in finite["cases"] if c["case"] == f"nfp{nfp}_beta_2.00")
        cases.append((f"nfp{nfp}-beta2", nfp,
                      root / "external/data/qifiles-finite-beta-v1" / case["wout_member"],
                      finite["archive"]["members"][case["wout_member"]]["sha256"]))
    for _, _, path, digest in cases:
        if sha256_file(path) != digest:
            raise ValueError(f"input hash mismatch: {path}")
    provenance = {
        "schema_version": 1, "repository": git_state(root), "host": host_state(),
        "input_references": [reference(finite_path), reference(vacuum_path)],
        "protocol": reference(root / "docs/qi/QI_RADIAL_ACTION_PROTOCOL.md"),
        "steps": STEPS, "radii": RADII, "nphi": NPHI, "nalpha": 8, "periods": 4,
        "code": [reference(path) for path in (Path(__file__),
            root / "src/fusion_baselines/radial_action.py",
            root / "src/fusion_baselines/bounce_action.py",
            root / "src/fusion_baselines/vmec_trace.py")],
    }
    for name, nfp, path, _ in cases:
        run_case(name, nfp, path, args.output / f"{name}.json", args.raw, provenance)


if __name__ == "__main__":
    main()
