"""Inventory tracked upstream LPQA metadata without loading or simulating coils."""

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check
from fusion_baselines.submission_inventory import extract, screen, shortlist

PIN = "c7949edc4ea6378fc3be633304c69c288c3b79b5"
SUBTREE = "submissions/LandremanPaul2021_QA/"


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable inventory required")
    root = Path(__file__).resolve().parents[1]
    source = root / "external/stellcoilbench"
    state = git_state(source)
    if state["commit"] != PIN or state["dirty"]:
        raise ValueError("clean pinned source required")
    disk = space_check(root, 2 * GIB)
    tree = subprocess.check_output(["git", "ls-tree", "-r", "-z", PIN, "--", SUBTREE], cwd=source)
    files = {}
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, kind, digest = metadata.decode().split()
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ValueError("only regular tracked source files supported")
        files[path.decode()] = digest
    paths = sorted(path for path in files if Path(path).name == "results.json")
    rows = []
    for path in paths:
        full = source / path
        content = full.read_bytes()
        blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
        if blob != files[path]:
            raise ValueError(f"metadata bytes differ from pinned Git blob: {path}")
        base = dict(source=reference(full), git_blob=blob, bytes=len(content))
        try:
            row = {**base, **extract(json.loads(content))}
            parent = Path(path).parent
            names = [parent / "biot_savart_optimized.json"]
            if type(row["order"]) is int and row["order"] > 0:
                names.insert(0, parent / f"order_{row['order']}" / "biot_savart_optimized.json")
            available = [
                dict(path=str(source / name), git_blob=files[str(name)])
                for name in names
                if str(name) in files
            ]
            row["available_endpoint_files"] = available
            row["endpoint_field"] = available[0] if available else None
            row["checks"] = screen(row)
            row["metadata_screen_pass"] = all(row["checks"].values())
        except (ValueError, TypeError, AttributeError, KeyError) as error:
            row = {**base, "parse_error": f"{type(error).__name__}: {error}"}
        rows.append(row)
    selected = shortlist(rows)
    for row in rows:
        if row["source"]["path"] in selected:
            ref = row["endpoint_field"]
            content = Path(ref["path"]).read_bytes()
            blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
            if blob != ref["git_blob"]:
                raise ValueError("selected endpoint field differs from pinned blob")
            row["selected_field"] = reference(Path(ref["path"]))
    counts = dict(
        reports=len(rows),
        parse_errors=sum("parse_error" in row for row in rows),
        metadata_screen_pass=sum(row.get("metadata_screen_pass", False) for row in rows),
        reported_zero_flux=sum(row.get("reported_zero_flux", False) for row in rows),
        schema=dict(Counter(row.get("schema", "parse_error") for row in rows)),
        exclusions=dict(
            Counter(
                key for row in rows for key, value in row.get("checks", {}).items() if not value
            )
        ),
    )
    result = dict(
        schema_version=1,
        repository=git_state(root),
        external=state,
        protocol=reference(root / "docs/optimization/UPSTREAM_LPQA_INVENTORY_PROTOCOL.md"),
        code=[
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/submission_inventory.py"),
        ],
        threshold_semantics_source=reference(
            root / "external/simsopt/src/simsopt/objectives/fluxobjective.py"
        ),
        disk_preflight=disk,
        status="completed",
        counts=counts,
        rows=rows,
        shortlist=selected,
        additional_physics_calls=0,
        physical_feasibility_certified=False,
        source_tree_sha256=hashlib.sha256(tree).hexdigest(),
    )
    write_json_atomic(args.output, result)
    print(json.dumps({"counts": counts, "shortlist": selected}))


if __name__ == "__main__":
    main()
