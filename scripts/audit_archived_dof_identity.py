"""Check all completed common-oracle best arrays against their original named SIMSON DOFs."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(record):
    path = Path(record["path"])
    if sha256_file(path) != record["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(__file__).resolve().parents[1]
    records = []
    for name in ("oracle-qualification-v1-retry1", "normalized-feasibility-v1",
                 "affine-feasibility-v1", "guarded-feasibility-v1"):
        path = root / "evidence" / name / "summary.json"
        study = json.loads(path.read_text())
        if study["status"] != "completed" or not study["qualification_pass"]:
            raise ValueError("completed repeat-qualified studies required")
        for ref in study["arms"]:
            arm_path = checked(ref)
            arm = json.loads(arm_path.read_text())
            field_path = checked(arm["best"]["field"])
            arrays_path = checked(arm["best"]["arrays"])
            direct = named_serialized_values(json.loads(field_path.read_text()),
                                             study["preparation"]["degrees_of_freedom"])
            with np.load(arrays_path, allow_pickle=False) as arrays:
                checks = {"exact_named_array_identity": bool(np.array_equal(direct, arrays["x"])),
                    "original_ledger_hash": hashlib.sha256(direct.tobytes()).hexdigest()
                        == arm["best"]["x_sha256"]}
            records.append({"study": reference(path), "arm": reference(arm_path),
                "field": reference(field_path), "arrays": reference(arrays_path),
                "checks": checks, "pass": all(checks.values())})
    result = {"schema_version": 1, "repository": git_state(root), "retrospective": True,
        "code": [reference(Path(__file__)),
                 reference(root / "src/fusion_baselines/serialized_dofs.py")],
        "arms": records, "all_pass": len(records) == 14 and all(r["pass"] for r in records),
        "limits": "Original serialized parameter identity only; not cross-process positional "
                  "replay or feasibility."}
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"], "arms": len(records)}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
