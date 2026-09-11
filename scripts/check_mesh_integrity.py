"""Run intrinsic integrity checks on the six frozen structured diagnostic meshes."""

import argparse
import json
import time
from pathlib import Path

import meshio
import numpy as np

from fusion_baselines.mesh_integrity import audit_tetrahedra
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("mesh audit output exists")
    root = Path(__file__).resolve().parents[1]
    result = {
        "schema_version": 1,
        "status": "running",
        "repository": git_state(root),
        "protocol": reference(root / "docs/engineering/MESH_INTEGRITY_PROTOCOL.md"),
        "code": [
            reference(Path(__file__)),
            reference(root / "src/fusion_baselines/mesh_integrity.py"),
        ],
        "versions": {"numpy": np.__version__, "meshio": meshio.__version__},
        "manifests": [],
        "meshes": [],
    }
    start = time.monotonic()
    try:
        for directory in ["lpqa-v1p1-structured", "lpqa-v1p1-structured-fine"]:
            manifest = root / f"artifacts/structural/{directory}/structured_mesh_manifest.json"
            result["manifests"].append(reference(manifest))
            for item in json.loads(manifest.read_text())["meshes"]:
                path = Path(item["path"])
                if sha256_file(path) != item["sha256"]:
                    raise ValueError("mesh hash mismatch")
                print(f"mesh integrity: {path}", flush=True)
                mesh = meshio.read(path)
                if any(block.type != "tetra" for block in mesh.cells):
                    raise ValueError("only linear tetrahedral meshes supported")
                cells = np.vstack([block.data for block in mesh.cells])
                tags = np.concatenate(mesh.cell_data["gmsh:physical"])
                audit = audit_tetrahedra(mesh.points, cells, tags)
                result["meshes"].append(
                    {
                        "mesh": reference(path),
                        "target_h_m": item["target_h_m"],
                        **audit,
                    }
                )
                write_json_atomic(args.output, result)
        result.update(
            status="completed",
            all_pass=len(result["meshes"]) == 6 and all(mesh["pass"] for mesh in result["meshes"]),
        )
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}", all_pass=False)
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic() - start
        write_json_atomic(args.output, result)
    print(
        json.dumps({"all_pass": result["all_pass"], "elapsed_seconds": result["elapsed_seconds"]})
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
