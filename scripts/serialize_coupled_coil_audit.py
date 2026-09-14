"""Typed output recovery for the six preserved negative coil-pilot validations.

The original numerical auditor and all source bindings remain unchanged. NumPy
scalars are normalized, and admission is recomputed after normalization. A changed
decision is NOT silently accepted by this serialization-recovery adapter.
"""

import argparse
import json
from pathlib import Path

import audit_coupled_coil_pilot as legacy
import numpy as np
from current_diagnostic_inputs import checked, reference
from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import git_state, write_json_atomic

ROOT = Path(__file__).resolve().parents[1]
FAILURE = "evidence/coupled-coil-pilot-v1/validation-output-failure.json"
TEST = "tests/test_coupled_coil_serialization.py"


def typed(value, path="$", conversions=None):
    """Exact scalar conversion with explicit paths; reject lossy/unsupported data."""
    if conversions is None:
        conversions = []
    if isinstance(value, np.generic):
        builtin = value.item()
        if isinstance(builtin, np.generic):
            raise TypeError(f"no exact builtin scalar conversion at {path}: {type(value).__name__}")
        try:
            json.dumps(value, allow_nan=False)
            unsupported = False
        except (TypeError, ValueError):
            unsupported = True
        conversions.append(dict(path=path, numpy_type=str(type(value)),
                                python_type=type(builtin).__name__,
                                legacy_json_unsupported=unsupported))
        return typed(builtin, path, conversions)
    if isinstance(value, np.ndarray):
        return typed(value.tolist(), path, conversions)
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise TypeError("only exact string JSON keys are permitted")
        return {key: typed(item, f"{path}.{key}", conversions) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [typed(item, f"{path}[{i}]", conversions) for i, item in enumerate(value)]
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float and np.isfinite(value):
        return value
    raise TypeError(f"nonfinite or unsupported value at {path}: {type(value).__name__}")


def recover(report, run):
    required = dict(arithmetic_and_source_pass=True, validation_complete=True,
                    all_pass=False, entry_pass=False, transfer_pass=False, step4_pass=False)
    if (report.get("phase") != "validation" or report.get("status") != "completed"
            or any(report.get(key) is not value for key, value in required.items())):
        raise ValueError("completed negative numerical validation required before output recovery")
    conversions = []
    normalized = typed(report, conversions=conversions)
    snapshot = legacy.read(run["snapshot"])
    fields = normalized["field_rows"]
    pairs = [(row["coarse"], row["fine"]) for row in normalized["refinements"]]
    corrected = legacy.independent.entry_gates(
        snapshot, fields[:4], fields[4:], normalized["flux"]["checks"],
        normalized["geometry"], pairs, [True] * len(fields))
    if (corrected["checks"] != normalized["gates"]
            or corrected["entry_pass"] != normalized["entry_pass"]
            or normalized["all_pass"] != normalized["entry_pass"]):
        raise ValueError("normalized classification differs; separate scientific review required")
    normalized["typed_gate_recheck"] = dict(
        legacy_gates=normalized["gates"].copy(), normalized_gates=corrected["checks"],
        identical=True, entry_pass=corrected["entry_pass"])
    normalized["scalar_normalization"] = dict(
        count=len(conversions), paths=conversions,
        legacy_unsupported_count=sum(row["legacy_json_unsupported"] for row in conversions),
        general_false_negative_bug_remains_in_legacy=True)
    json.dumps(normalized, allow_nan=False)
    return normalized


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.run.is_absolute() or args.output.exists():
        raise ValueError("absolute original run and fresh output required")
    for path in (Path(__file__), ROOT / TEST, ROOT / FAILURE):
        require_committed(ROOT, path)
    failure = json.loads((ROOT / FAILURE).read_text())
    run_ref = reference(args.run)
    if run_ref not in failure["raw_runs"]:
        raise ValueError("recovery is restricted to the six preserved original validation runs")
    for ref in failure["raw_runs"]:
        checked(ref)
    result = dict(status="error", phase="validation", arithmetic_and_source_pass=False,
                  validation_complete=False, all_pass=False, entry_pass=False,
                  transfer_pass=False, step4_pass=False)
    try:
        run = json.loads(args.run.read_text())
        report = legacy.audit(run, ROOT)
        try:
            json.dumps(report, allow_nan=False)
            legacy_error = None
        except TypeError as exc:
            legacy_error = f"TypeError: {exc}"
        result.update(recover(report, run))
        result["legacy_serialization_error_reproduced"] = legacy_error
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result.update(run=run_ref, validation=run_ref, failure_manifest=reference(ROOT / FAILURE),
                  legacy_auditor=reference(Path(legacy.__file__)),
                  output_adapter=reference(Path(__file__)), adapter_tests=reference(ROOT / TEST),
                  repository=git_state(ROOT))
    json.dumps(result, allow_nan=False)
    write_json_atomic(args.output, result)
    print(json.dumps({k: result.get(k) for k in
                      ("status", "arithmetic_and_source_pass", "entry_pass", "error")}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
