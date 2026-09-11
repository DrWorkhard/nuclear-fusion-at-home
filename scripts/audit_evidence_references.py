"""Hash-audit a declared set of evidence files, including historical code/doc paths."""

import argparse
import json
from collections import Counter
from pathlib import Path

from fusion_baselines.evidence_integrity import reference_records, resolve_reference
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", type=Path, nargs="+")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(__file__).resolve().parents[1]
    mapping_path = root / "manifests/documentation-layout-v1.json"
    mapping = json.loads(mapping_path.read_text())
    relocations = {item["from"]: item["to"] for item in mapping["moves"]}
    records, cache = [], {}
    for path in args.inputs:
        data = json.loads(path.read_text())
        repository = data.get("repository", {})
        recorded_root, revision = repository.get("path", str(root)), repository.get("commit")
        for ref in reference_records(data):
            key = (ref["path"], ref["sha256"], recorded_root, revision)
            if key not in cache:
                cache[key] = resolve_reference(ref, root, recorded_root, revision, relocations)
            records.append({"evidence": str(path), **cache[key]})
    counts = dict(Counter(r["status"] for r in records))
    result = {
        "schema_version": 1,
        "repository": git_state(root),
        "inputs": [reference(p) for p in args.inputs],
        "mapping": reference(mapping_path),
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/evidence_integrity.py"),
        ],
        "records": records,
        "status_counts": counts,
        "unique_reference_contexts": len(cache),
        "all_pass": bool(records) and not counts.get("unresolved", 0),
        "scope": "explicit path/sha256 pairs in listed JSON inputs, not recursive linked reports",
        "scientific_results_recomputed": False,
    }
    write_json_atomic(args.output, result)
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "status_counts": counts,
                "unique_reference_contexts": len(cache),
            }
        )
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
