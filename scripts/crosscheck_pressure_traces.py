"""Second-tracer audit of the frozen four-case radial-action pilot."""

import argparse
import contextlib
import io
import json
import time
import warnings
from pathlib import Path

import numpy as np
import scipy
from evaluate_published_maximum_j import VmecAdapter, load_published_functions
from measure_radial_action import wells_on_line

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.radial_action import match_intervals, radial_sign_screen


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def run_case(path, raw_root, tracer):
    data = json.loads(path.read_text())
    if data["status"] != "completed":
        raise ValueError("pilot not completed")
    wout = Path(data["wout"]["path"])
    if sha256_file(wout) != data["wout"]["sha256"]:
        raise ValueError("wout hash mismatch")
    vmec, traces = VmecAdapter(wout), {}
    result = {"case": data["case"], "input": reference(path), "traces": [], "cells": []}
    for old in data["traces"]:
        key = (old["level"], old["s"])
        print(f"{data['case']}: metric trace {key}", flush=True)
        diagnostic = io.StringIO()
        with warnings.catch_warnings(record=True) as caught, contextlib.redirect_stdout(diagnostic):
            warnings.simplefilter("always")
            values = tracer(vmec, phi_start=0, nphi=old["nphi"], alpha0=0,
                            nalpha=data["nalpha"], nfpinc=data["periods"],
                            snorm=old["s"], verbose=False)
        if "error" in diagnostic.getvalue().lower():
            raise ValueError(f"published trace error: {diagnostic.getvalue()}")
        length = values.ls - values.ls[0]
        length *= np.sign(length[-1])[None, :]
        if not np.all(np.isfinite(length)) or np.any(np.diff(length, axis=0) <= 0):
            raise ValueError("invalid second-tracer length")
        if not np.all(np.isfinite(values.B)) or np.any(values.B <= 0):
            raise ValueError("invalid second-tracer B")
        trace = {"B": values.B, "length": length, "phi": values.phis, "alpha": values.alphas}
        traces[key] = trace
        raw = raw_root / data["case"] / f"trace-{key[0]}-s{key[1]}.npz"
        raw.parent.mkdir(parents=True, exist_ok=True)
        with raw.open("xb") as stream:
            np.savez_compressed(stream, **trace)
        prior = Path(old["path"])
        if sha256_file(prior) != old["sha256"]:
            raise ValueError("pilot raw hash mismatch")
        with np.load(prior) as arrays:
            coordinates = bool(all(np.allclose(trace[name], arrays[name], rtol=0, atol=1e-12)
                                   for name in ("phi", "alpha")))
            b_error = float(np.max(np.abs(values.B / arrays["B"] - 1)))
            l_error = float(np.max(np.abs(length - arrays["length"])) / arrays["length"].max())
        result["traces"].append({"level": key[0], "s": key[1], "raw": reference(raw),
            "stdout": diagnostic.getvalue(), "warnings": [str(w.message) for w in caught],
            "coordinates_match": coordinates, "relative_B_difference": b_error,
            "normalized_length_difference": l_error,
            "pass": coordinates and b_error <= 1e-8 and l_error <= 1e-3})
    for cell in data["cells"]:
        audit = {"q": cell["q"], "alpha_index": cell["alpha_index"], "wells": [], "families": []}
        result["cells"].append(audit)
        actions = {}
        for record in cell["wells"]:
            key = (record["level"], record["s"])
            trace = traces[key]
            current = [w for w in wells_on_line(trace, cell["alpha_index"], cell["Bstar"])
                       if w["complete"]]
            expected = [w for w in record["wells"] if w["complete"]]
            check = {"level": key[0], "s": key[1], "pass": False}
            audit["wells"].append(check)
            try:
                mapping = match_intervals([w["phi_interval"] for w in expected],
                                          [w["phi_interval"] for w in current],
                                          [trace["phi"][0], trace["phi"][-1]])
            except ValueError as error:
                check["error"] = str(error)
                continue
            actions[key] = [current[i]["action"] for i in mapping]
            discrepancy = max(abs(a / b["action"] - 1)
                              for a, b in zip(actions[key], expected, strict=True))
            check["relative_action_difference"] = discrepancy
            check["pass"] = discrepancy <= 1e-3
        if not cell["matching_pass"] or len(actions) != len(traces):
            audit["pass"] = False
            continue
        mappings = {(r["level"], r["s"]): r["indices"] for r in cell["matches"]}
        for family, old in enumerate(cell["families"]):
            selected = {key: row[mappings[key][family]] for key, row in actions.items()}
            stencil = np.array([[[selected[level, round(0.5 - h, 2)],
                                   selected[level, round(0.5 + h, 2)]] for h in data["steps"]]
                                for level in range(3)])
            screen = radial_sign_screen(stencil, selected[2, 0.5], data["steps"])
            difference = abs(screen["estimate"] - old["estimate"])
            tolerance = max(1e-3, 0.01 * abs(old["estimate"]))
            combined = old["empirical_allowance"] + 4 * difference
            robust = (old["sign"] == "unresolved"
                      or (old["sign"] == "negative" and old["estimate"] + combined < 0)
                      or (old["sign"] == "positive" and old["estimate"] - combined > 0))
            audit["families"].append({"family": family, "second_tracer_screen": screen,
                "original_sign": old["sign"], "absolute_derivative_difference": difference,
                "tolerance": tolerance, "combined_empirical_allowance": combined,
                "original_resolved_sign_survives": robust,
                "pass": difference <= tolerance and robust})
        audit["pass"] = all(c["pass"] for c in audit["wells"] + audit["families"])
    result["pass"] = all(c["pass"] for c in result["traces"] + result["cells"])
    print(data["case"], result["pass"], flush=True)
    return result


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=root / "evidence/qi-pressure-trace-v1.json")
    parser.add_argument("--raw", type=Path, default=root / "artifacts/qi-pressure-trace-v1")
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("preserve prior cross-check output/raw data")
    source = root / "external/data/qifiles-v1/Files/plots/plot_elephants/PltElephants.py"
    refs = json.loads((root / "references/goodman_qi_transfer_cases.json").read_text())
    if sha256_file(source) != refs["published_metric_code"]["maximum_j_plot_code_sha256"]:
        raise ValueError("published source hash mismatch")
    tracer, _ = load_published_functions(source)
    result = {"schema_version": 1, "status": "running", "cases": [],
        "repository": git_state(root), "numpy": np.__version__, "scipy": scipy.__version__,
        "protocol": reference(root / "docs/QI_PRESSURE_TRACE_PROTOCOL.md"),
        "code": [reference(p) for p in (Path(__file__), source,
            root / "scripts/evaluate_published_maximum_j.py",
            root / "scripts/measure_radial_action.py",
            root / "src/fusion_baselines/radial_action.py",
            root / "src/fusion_baselines/bounce_action.py")]}
    start = time.monotonic()
    try:
        for case in ("nfp2-vacuum", "nfp2-beta2", "nfp3-vacuum", "nfp3-beta2"):
            result["cases"].append(run_case(
                root / f"evidence/qi-radial-action-v1/{case}.json", args.raw, tracer))
            write_json_atomic(args.output, result)
        result["status"] = "completed"
        result["all_pass"] = all(c["pass"] for c in result["cases"])
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}", all_pass=False)
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic() - start
        write_json_atomic(args.output, result)
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
