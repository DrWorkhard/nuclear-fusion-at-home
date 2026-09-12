"""Frozen60 QI Wout/radius rows and closed, hash-bound predecessor studies."""

import json
from pathlib import Path

from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import sha256_file
from fusion_baselines.qi_resolution import MATRIX

SURFACES = (.25, .5, .75)


def reference(path):
    return dict(path=str(Path(path).resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError("frozen QI coordinate source hash mismatch")
    return path


def matrix_rows(study, evaluation, inventory):
    expected = [(c["case"], ns, a) for c in inventory["cases"] for ns, a in MATRIX]
    if len(inventory["cases"]) != 4 or len(set(c["case"] for c in inventory["cases"])) != 4:
        raise ValueError("four unique original cases required")
    for report in (study, evaluation):
        if (report["status"] != "completed" or
                [(r["case"], r["ns"], r["angular"]) for r in report["cells"]] != expected):
            raise ValueError("full ordered16-cell QI matrix required")
    old_rows = evaluation["old_fields"]
    if [(r["case"], r["surface"]) for r in old_rows] != [
            (c["case"], s) for c in inventory["cases"] for s in SURFACES]:
        raise ValueError("all12 ordered original Wout/surface pairs required")
    authors = {c["case"]: c for c in inventory["cases"]}
    rows = []
    for r in old_rows:
        if r["wout"] != authors[r["case"]]["wout"]:
            raise ValueError("historical Wout source changed")
        rows.append(dict(kind="historical", cell=None, case=r["case"], surface=r["surface"],
                         wout=r["wout"], old_arrays=r["arrays"]))
    for i, (cell, measured) in enumerate(zip(study["cells"], evaluation["cells"], strict=True)):
        if (not cell["numerically_converged"] or measured["status"] != "completed"
                or cell["historical_wout"] != authors[cell["case"]]["wout"]
                or [(g["surface"], g["resolution"]) for g in measured["grids"]] != [
                    (s, n) for s in SURFACES for n in (64, 128)]):
            raise ValueError("complete unchanged48 fresh Wout/surface pairs required")
        for g in measured["grids"][1::2]:
            rows.append(dict(kind="fresh", cell=i, case=cell["case"], surface=g["surface"],
                             wout=cell["wout"], old_arrays=g["arrays"], ns=cell["ns"],
                             angular=cell["angular"], old_fidelity=g["fidelity"],
                             old_volume_error=measured["volume_error"]))
    return rows


def frozen_sources(root):
    names = ("qi-fresh-resolution-v1.json", "qi-fresh-resolution-v1-evaluation.json",
             "qi-fresh-resolution-v1-evaluation-audit.json")
    paths = [root / "evidence" / n for n in names]
    study, evaluation, audit = [json.loads(p.read_text()) for p in paths]
    if (evaluation["study"] != reference(paths[0]) or not audit["all_pass"]
            or audit["source"] != reference(paths[1])):
        raise ValueError("closed independently audited original QI study required")
    inventory = json.loads(checked(study["inventory"]).read_text())
    rows = matrix_rows(study, evaluation, inventory)
    for row in rows:
        checked(row["wout"])
        checked(row["old_arrays"])
    for report in (study, evaluation, audit):
        for ref in report["code"]:
            checked(ref)
    return rows, [reference(p) for p in paths]


def closed_predecessors(root):
    paths = [root / p for p in ("evidence/slsqp-composite-v1-validation/summary.json",
                                "evidence/mesh-nonlocal-v2/summary.json",
                                "evidence/mesh-nonlocal-v2-audit.json")]
    coils, mesh, audit = [json.loads(p.read_text()) for p in paths]
    if (coils["status"] != "completed" or not coils["all_four_phases_completed"]
            or mesh["status"] != "completed" or not mesh["all_six_terminal"]
            or audit["status"] != "completed" or audit["study"] != reference(paths[1])
            or len(audit["meshes"]) != 6):
        raise ValueError("closed coil holdouts and audited terminal six-mesh study required")
    for path in paths:
        require_committed(root, path)
    return [reference(p) for p in paths]
