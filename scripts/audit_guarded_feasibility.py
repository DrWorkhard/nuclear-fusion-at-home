"""Audit guarded construction accounting and independently reload saved best arrays."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.oracle_audit import audit_ledger
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(__file__).resolve().parents[1]
    summary_path = args.study / "summary.json"
    study = json.loads(summary_path.read_text())
    if study["status"] != "completed" or not study["qualification_pass"]:
        raise ValueError("require completed repeat-qualified study")
    checked(study["protocol"])
    checked(study["curvature_gradient_qualification"])
    for source in study["code"] + study["installed_sources"] + [
            study["least_squares_source"]] + study["least_squares_support_sources"]:
        checked(source)
    target = study["preparation"]["guarded_search_targets"]
    checks = {
        "two_trf_repeats": study["methods"] == ["trf"] and len(study["arms"]) == 2,
        "declared_targets": target == {"component_index": 4, "curvature_resolution": 1600,
            "curvature_target_reactor": 0.99, "length_target_reactor": 219.9,
            "flux_target": 8e-9, "field_quadrature_unchanged": 200},
        "single_shared_normalization": study["normalization"]["shared_counters"]["attempts"] == 1,
        "normalization": study["normalization"]["factor"]
            == 1 / study["normalization"]["initial_norm"],
        "regularization_preserved": study["preparation"]["regularizations_preserved"],
        "unchanged_promotion_field": study["preparation"]["promotion_relative_B_difference"]
            <= 1e-10,
    }
    arms, loaded = [], []
    for ref in study["arms"]:
        path = checked(ref)
        arm = json.loads(path.read_text())
        loaded.append(arm)
        with np.load(checked(arm["best"]["arrays"]), allow_pickle=False) as arrays:
            ac = {k: bool(v) for k, v in audit_ledger(arm, arrays["x"], arrays["values"],
                                                     3000).items()}
        checked(arm["best"]["field"])
        arms.append({"arm": reference(path), "checks": ac, "pass": all(ac.values())})
    checks["repeat_identities"] = [(a["method"], a["repeat"]) for a in loaded] == [
        ("trf", 1), ("trf", 2)]
    if len(loaded) == 2:
        first, second = loaded
        checks["repeat_counters"] = first["counters"] == second["counters"]
        checks["repeat_history"] = len(first["evaluations"]) == len(second["evaluations"]) and all(
            a["x_sha256"] == b["x_sha256"]
            and np.allclose(a["values"], b["values"], rtol=1e-12, atol=1e-14)
            for a, b in zip(first["evaluations"], second["evaluations"], strict=True))
    result = {"schema_version": 1, "repository": git_state(root),
        "study": reference(summary_path), "code": [reference(Path(__file__)),
            reference(root / "src/fusion_baselines/oracle_audit.py")],
        "checks": checks, "arms": arms,
        "all_pass": all(checks.values()) and all(a["pass"] for a in arms),
        "limits": "Accounting/source audit only; no feasibility claim or additional physics calls."}
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
