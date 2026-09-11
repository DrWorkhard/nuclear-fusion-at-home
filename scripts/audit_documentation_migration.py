"""Verify historical document hashes and path-only changes in scientific scripts."""

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

from fusion_baselines.documentation import check_documentation
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "manifests/documentation-layout-v1.json"
    manifest = json.loads(manifest_path.read_text())
    revision = manifest["source_commit"]

    def old_bytes(path):
        return subprocess.run(
            ["git", "show", f"{revision}:{path}"], cwd=root, capture_output=True, check=True
        ).stdout

    mappings = {item["from"]: item["to"] for item in manifest["moves"]}

    class UpdatePaths(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str):
                value = node.value
                for old, new in mappings.items():
                    value = value.replace(old, new)
                return ast.copy_location(ast.Constant(value=value), node)
            return node

    records = []
    for entry in manifest["moves"]:
        source_hash = hashlib.sha256(old_bytes(entry["from"])).hexdigest()
        path = root / entry["to"]
        records.append({
            **entry,
            "source_hash_verified": source_hash == entry["source_sha256"],
            "destination_exists": path.is_file(),
            "current_sha256": sha256_file(path) if path.is_file() else None,
            "live_bytes_unchanged": path.is_file() and sha256_file(path) == source_hash,
        })
    scripts = []
    for name in manifest["updated_script_paths"]:
        original = ast.parse(old_bytes(name).decode())
        changed = UpdatePaths().visit(original)
        actual = ast.parse((root / name).read_text())
        scripts.append({"path": name, "current_sha256": sha256_file(root / name),
                        "only_document_path_AST_changes": ast.dump(changed) == ast.dump(actual)})
    structure_errors = check_documentation(root)
    checks = {
        "all_53_destinations_present": len(records) == 53
        and all(r["destination_exists"] for r in records),
        "unique_destinations": len(set(mappings.values())) == len(records),
        "all_original_hashes_verified": all(r["source_hash_verified"] for r in records),
        "all_18_scientific_scripts_only_path_changes": len(scripts) == 18
        and all(s["only_document_path_AST_changes"] for s in scripts),
        "structure_and_file_links": not structure_errors,
    }
    result = {
        "schema_version": 1, "repository": git_state(root), "checks": checks,
        "manifest": {"path": str(manifest_path), "sha256": sha256_file(manifest_path)},
        "code": {"path": str(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__))},
        "documents": records, "scripts": scripts, "structure_errors": structure_errors,
        "all_pass": all(checks.values()), "scientific_results_revalidated": False,
        "unchanged_live_documents": sum(r["live_bytes_unchanged"] for r in records),
        "note": "Historical hashes stay authoritative; live logs/navigation may evolve.",
    }
    write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"],
                      "unchanged_live_documents": result["unchanged_live_documents"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
