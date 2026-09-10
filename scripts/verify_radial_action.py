"""Retrospective independent quadrature and serialized-stencil audit."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.action_quadrature import quadrature_action
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.radial_action import radial_sign_screen


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def verify(path):
    data = json.loads(path.read_text())
    if data["status"] != "completed":
        raise ValueError("input run not complete")
    traces = {}
    for record in data["traces"]:
        raw = Path(record["path"])
        if sha256_file(raw) != record["sha256"]:
            raise ValueError(f"raw hash mismatch: {raw}")
        with np.load(raw) as arrays:
            traces[record["level"], record["s"]] = {
                name: arrays[name].copy() for name in ("length", "B", "phi")}
    errors, cell_results = [], []
    worst_action, worst_derivative, checked = 0.0, 0.0, 0
    for cell in data["cells"]:
        alpha, bstar = cell["alpha_index"], cell["Bstar"]
        integrated = {}
        for record in cell["wells"]:
            key = (record["level"], record["s"])
            trace = traces[key]
            complete = []
            for well in record["wells"]:
                action = quadrature_action(trace["length"][:, alpha], trace["B"][:, alpha],
                                           well["left"], well["right"], bstar)
                relative = abs(action / well["action"] - 1)
                worst_action = max(worst_action, relative)
                checked += 1
                if not np.isfinite(relative) or relative > 1e-6:
                    errors.append(f"action mismatch: {relative}")
                if well["complete"]:
                    complete.append(action)
            integrated[key] = complete
        if not cell["matching_pass"]:
            cell_results.append({"q": cell["q"], "alpha": alpha, "matching_pass": False})
            continue
        mappings = {(r["level"], r["s"]): r["indices"] for r in cell["matches"]}
        for index, family in enumerate(cell["families"]):
            values = {key: row[mappings[key][index]] for key, row in integrated.items()}
            stencil = np.array([[[values[level, round(0.5 - h, 2)],
                                   values[level, round(0.5 + h, 2)]] for h in data["steps"]]
                                for level in range(3)])
            screen = radial_sign_screen(stencil, values[2, 0.5], data["steps"])
            difference = abs(screen["estimate"] - family["estimate"])
            worst_derivative = max(worst_derivative, difference)
            same = (screen["sign"] == family["sign"]
                    and screen["refinement_pass"] == family["refinement_pass"])
            stencil_matches = bool(np.allclose(
                stencil, family["action_stencil"], rtol=1e-6, atol=0))
            if not same or not stencil_matches or difference > 1e-5:
                errors.append("derivative/stencil/classification mismatch")
            cell_results.append({"q": cell["q"], "alpha": alpha, "family": index,
                "classification_matches": same, "stencil_matches": stencil_matches,
                "normalized_derivative_difference": difference, "independent_screen": screen})
    return {"input": reference(path), "wells_checked": checked,
            "max_relative_action_difference": worst_action,
            "max_normalized_derivative_difference": worst_derivative,
            "cells_and_families": cell_results, "errors": errors,
            "pass": not errors and checked > 0}


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = {"schema_version": 1, "prospective": False, "repository": git_state(root),
              "method": "128-point Gauss-Legendre per linear segment; frozen raw traces",
              "action_relative_tolerance": 1e-6, "normalized_derivative_tolerance": 1e-5,
              "limits": "Independent integration, not independent equilibrium or trace geometry.",
              "code": [reference(p) for p in (Path(__file__),
                  root / "src/fusion_baselines/action_quadrature.py",
                  root / "src/fusion_baselines/radial_action.py")], "cases": []}
    for name in ("nfp2-vacuum", "nfp2-beta2", "nfp3-vacuum", "nfp3-beta2"):
        case = verify(root / f"evidence/qi-radial-action-v1/{name}.json")
        result["cases"].append(case)
        print(name, case["pass"], case["wells_checked"], flush=True)
    result["all_pass"] = all(c["pass"] for c in result["cases"])
    write_json_atomic(args.output, result)
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
