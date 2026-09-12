"""Read-only identity checks for exactly the six preregistered old meshes."""

import json
from pathlib import Path

import meshio
import numpy as np

from fusion_baselines.evidence_integrity import resolve_reference
from fusion_baselines.provenance import sha256_file

LEVELS = [0.05, 0.04, 0.03, 0.02, 0.015, 0.01]


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError("frozen mesh source binding mismatch")
    return path


def source_code_bindings(root, source):
    """Historical source only: exact bytes at the report's own recorded revision."""
    repository = source["repository"]
    records = [resolve_reference(ref, root, repository["path"], repository["commit"])
               for ref in source["code"]]
    if not records or any(r["status"] not in {"current", "historical_git"} for r in records):
        raise ValueError("unresolved historical intrinsic source code")
    return records


def frozen_inputs(root):
    path = root / "evidence/mesh-integrity-2026-09-09.json"
    source = json.loads(path.read_text())
    if (source["status"] != "completed" or source["all_pass"] is not True
            or [r["target_h_m"] for r in source["meshes"]] != LEVELS):
        raise ValueError("all six fixed intrinsically qualified levels required")
    declared = [m for ref in source["manifests"]
                for m in json.loads(checked(ref).read_text())["meshes"]]
    if len(declared) != 6:
        raise ValueError("two source manifests must retain all six meshes")
    for row, manifest in zip(source["meshes"], declared, strict=True):
        mesh = checked(row["mesh"])
        if (not row["pass"] or not all(row["checks"].values())
                or str(mesh) != manifest["path"] or row["mesh"]["sha256"] != manifest["sha256"]
                or row["target_h_m"] != manifest["target_h_m"]):
            raise ValueError("source mesh identity/intrinsic result mismatch")
    source_code_bindings(root, source)
    return path, source


def load_mesh(ref):
    mesh = meshio.read(checked(ref))
    if not mesh.cells or any(c.type != "tetra" for c in mesh.cells):
        raise ValueError("only original linear tetrahedra supported")
    cells = np.vstack([c.data for c in mesh.cells])
    tags = np.concatenate(mesh.cell_data["gmsh:physical"])
    if (not np.issubdtype(tags.dtype, np.integer) or set(map(int, tags)) != {1, 2, 3, 4}
            or tags.shape != (len(cells),)):
        raise ValueError("all four original physical coil tags required")
    return mesh.points, cells, tags
