"""Execute the frozen curvature enclosure qualification on three stored fields."""

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from simsopt import load

from fusion_baselines.curvature_bounds import classify_enclosure, curvature_enclosure
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def physical_copy_check(curve, base_hashes):
    while hasattr(curve, "rotmat"):
        rotation = np.asarray(curve.rotmat)
        if rotation.shape != (3, 3) or not np.allclose(rotation.T @ rotation, np.eye(3),
                                                     rtol=0, atol=1e-12):
            return False
        curve = curve.curve
    return hashlib.sha256(curve.local_full_x.tobytes()).hexdigest() in base_hashes


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    holdout_path = root / "evidence/affine-feasibility-v1-holdout.json"
    summary_path = root / "evidence/affine-feasibility-v1/summary.json"
    holdout = json.loads(holdout_path.read_text())
    summary = json.loads(summary_path.read_text())
    fields = [("rejected-warmstart", summary["preparation"]["source"],
               summary["preparation"]["thresholds"]["a0"])]
    fields += [(c["method"], c["field"], c["a0"]) for c in holdout["candidates"]]
    result = {"schema_version": 1, "retrospective": True, "repository": git_state(root),
              "protocol": reference(root / "docs/CONTINUOUS_CURVATURE_PROTOCOL.md"),
              "input_records": [reference(holdout_path), reference(summary_path)],
              "code": [reference(p) for p in (Path(__file__),
                  root / "src/fusion_baselines/curvature_bounds.py")], "fields": [],
              "full_engineering_admission": False, "directed_rounding": False}
    for name, field_ref, scale in fields:
        path = Path(field_ref["path"])
        if sha256_file(path) != field_ref["sha256"]:
            raise ValueError("field hash mismatch")
        field = load(str(path))
        if len(field.coils) != 16:
            raise ValueError("require sixteen physical coils")
        bases = [c.curve for c in field.coils[:4]]
        hashes = {hashlib.sha256(c.local_full_x.tobytes()).hexdigest() for c in bases}
        if not all(physical_copy_check(c.curve, hashes) for c in field.coils):
            raise ValueError("physical copies are not verified orthogonal copies of the bases")
        record = {"name": name, "field": reference(path), "a0": scale,
                  "orthogonal_copies_verified": True, "levels": []}
        result["fields"].append(record)
        started = time.monotonic()
        for n in [200, 400, 800, 1600, 3200, 6400, 12800]:
            bounds = []
            for c in bases:
                coefficients = c.local_full_x.reshape(3, -1)
                bound = curvature_enclosure(coefficients, n)
                bound["classification"] = classify_enclosure(bound, scale)
                for key in ("maximum_lower_bound", "maximum_upper_bound"):
                    bound[key + "_reactor"] = bound[key] / scale if bound[key] is not None else None
                bounds.append(bound)
            classification = "fail" if any(b["classification"] == "fail" for b in bounds) else (
                "pass" if all(b["classification"] == "pass" for b in bounds) else "unresolved")
            record["levels"].append({"resolution": n, "curves": bounds,
                                     "classification": classification})
            print(name, n, classification, flush=True)
        record["classification"] = record["levels"][-1]["classification"]
        record["elapsed_seconds"] = time.monotonic() - started
    result["status"] = "completed"
    write_json_atomic(args.output, result)


if __name__ == "__main__":
    main()
