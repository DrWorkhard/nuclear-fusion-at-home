"""Independent core-only recomputation of saved quadratic-model qualification."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def load_arrays(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"array hash mismatch: {path}")
    with np.load(path, allow_pickle=False) as data:
        arrays = {k: data[k].copy() for k in data.files}
    if not all(np.all(np.isfinite(v)) for v in arrays.values()):
        raise ValueError("nonfinite raw array")
    return arrays


def check_raw(report):
    checks, states = {}, {}
    for state in report["states"]:
        name, data = state["name"], load_arrays(state["arrays"])
        if name in states:
            raise ValueError("duplicate state")
        states[name] = data
        z, dz, local = data["z"], data["dz"], data["local_dz"]
        checks[name + "/native_matrix"] = bool(
            np.max(np.abs(dz-local)) / max(1, np.max(np.abs(local))) <= 1e-10)
        checks[name + "/native_gradient"] = bool(np.max(
            np.abs(z @ dz / 1e-6 - data["jacobian"][0])
            / np.maximum(1, np.abs(data["jacobian"][0]))) <= 1e-10)
        finest = (data["plus_z"][:, -1] - data["minus_z"][:, -1]) / 2e-6
        exact = data["directions"] @ dz.T
        checks[name + "/finest_directions"] = bool(
            np.max(np.abs(finest-exact) / np.maximum(1, np.abs(exact))) <= 1e-6)
    expected_keys = {("original", 1e-2), ("selected119", 1e-4),
                     ("selected119", 1e-3), ("selected119", 1e-2)}
    seen, numbers = set(), []
    for i, probe in enumerate(report["probes"]):
        key = (probe["state"], probe["radius"])
        if key in seen:
            raise ValueError("duplicate probe")
        seen.add(key)
        base, data = states[probe["state"]], load_arrays(probe["arrays"])
        z, dz, delta, actual = base["z"], base["dz"], data["step"], data["actual_z"]
        checks[f"probe-{i}/step"] = bool(np.array_equal(data["x"] - base["x"], delta))
        # Scalar sums and native reference rows, not the tested prediction helper.
        reference_linear_z = z + base["local_dz"] @ delta
        f0, f1, q = [float(np.sum(v*v) / 2e-6) for v in (z, actual, reference_linear_z)]
        linear = float(np.sum((dz @ delta)*z) / 1e-6)
        linear_error, quad_error = abs(f1-f0-linear), abs(f1-q)
        predicted = {"baseline": f0, "actual": f1, "actual_change": f1-f0,
                     "linear_change": linear, "quadratic_change": q-f0,
                     "linear_absolute_error": linear_error,
                     "quadratic_absolute_error": quad_error}
        checks[f"probe-{i}/reported_numbers"] = all(
            abs(value-probe["prediction"][k]) / max(1, abs(value)) <= 1e-10
            for k, value in predicted.items())
        checks[f"probe-{i}/raw_flux"] = bool(abs(f1-data["values"][0]) / abs(f1) <= 1e-10)
        useful = bool(np.sign(q-f0) == np.sign(f1-f0) and quad_error <= 0.1*linear_error)
        checks[f"probe-{i}/usefulness_flag"] = useful == probe["prediction"]["usefulness_pass"]
        numbers.append({"state": probe["state"], "radius": probe["radius"],
                        "quadratic_to_linear_error_ratio": quad_error/max(linear_error, 1e-300),
                        "usefulness_pass": useful})
    checks["exact_state_and_probe_set"] = set(states) == {"original", "selected119"} and (
        seen == expected_keys and len(report["probes"]) == 4)
    return checks, numbers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit path required")
    report = json.loads(args.input.read_text())
    checks, numbers = check_raw(report)
    result = {"schema_version": 1, "repository": git_state(Path(__file__).parents[1]),
              "input": {"path": str(args.input.resolve()), "sha256": sha256_file(args.input)},
              "code": {"path": str(Path(__file__).resolve()),
                       "sha256": sha256_file(Path(__file__))},
              "checks": checks, "recomputed_probes": numbers, "all_pass": all(checks.values()),
              "scope": "core-only raw-array replay; no new native solves or candidate admission"}
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"], "checks": len(checks)}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
