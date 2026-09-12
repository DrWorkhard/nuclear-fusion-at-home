"""Closed current-minimum sources for the subsequent fixed geometric diagnosis."""

import json

import numpy as np
from current_diagnostic_inputs import checked, reference, sources
from run_jac_scaled_study import require_committed

from fusion_baselines.serialized_current_affine import current_map
from fusion_baselines.serialized_dofs import named_serialized_values

FIELD_SHAS = (
    "d73b89913f2bc460e097a92ae58864419db6f5a10e661974ec0e02e26208d572",
    "bb3dc24e817765b8505f539e2e2ca64f4189e280ae0643be3cddcca163f49028",
)


def closed_sources(root):
    paths = [
        root / "evidence" / f"fixed-currents-v1{suffix}.json"
        for suffix in ("", "-audit", "-holdouts", "-holdouts-audit")
    ]
    study, audit, holdouts, fine_audit = [json.loads(path.read_text()) for path in paths]
    originals = sources(root)
    if (
        any(r["status"] != "completed" for r in (study, audit, holdouts, fine_audit))
        or not all(r["all_pass"] for r in (study, audit, fine_audit))
        or not holdouts["all_eight_grids_completed"]
        or audit["source"] != reference(paths[0])
        or holdouts["source"] != reference(paths[0])
        or holdouts["audit"] != reference(paths[1])
        or fine_audit["source"] != reference(paths[2])
        or len(study["cases"]) != 2
        or [r["source"] for r in study["cases"]] != originals
        or [r["field"]["sha256"] for r in study["cases"]] != list(FIELD_SHAS)
    ):
        raise ValueError("exact two closed independently audited current-minimum states required")
    for path in paths:
        require_committed(root, path)
    for report in (study, audit, holdouts, fine_audit):
        for ref in report["code"]:
            checked(ref)
    checked(study["protocol"])
    result = []
    for i, row in enumerate(study["cases"]):
        if (
            not row["all_pass"]
            or not audit["cases"][i]["all_pass"]
            or holdouts["cases"][i]["status"] != "completed"
            or not fine_audit["cases"][i]["all_pass"]
            or holdouts["cases"][i]["field"] != row["field"]
        ):
            raise ValueError("every source current qualification and holdout must be closed")
        for ref in (row["field"], row["arrays"]):
            require_committed(root, checked(ref))
        result.append(
            dict(
                label=originals[i]["label"],
                field=row["field"],
                arrays=row["arrays"],
                names=row["names"],
                preparation=row["preparation"],
            )
        )
    return result, [reference(path) for path in paths]


def source_arrays(source):
    doc = json.loads(checked(source["field"]).read_text())
    mapping = current_map(doc, source["names"])
    with np.load(checked(source["arrays"]), allow_pickle=False) as arrays:
        x, values, jac = (
            arrays[key].copy() for key in ("after_x", "after_values", "after_jacobian")
        )
    if (
        x.shape != (207,)
        or values.shape != (138,)
        or jac.shape != (138, 207)
        or not all(np.isfinite(v).all() for v in (x, values, jac))
        or not np.array_equal(x, named_serialized_values(doc, source["names"]))
    ):
        raise ValueError("complete named finite207/138 current-minimum source required")
    columns = mapping["columns"]
    geometry = np.array([i for i in range(207) if i not in set(columns)], dtype=int)
    if len(geometry) != 204 or np.any(jac[1:, columns] != 0):
        raise ValueError("exactly204 shape DOFs and current-independent geometry required")
    return dict(x=x, values=values, jacobian=jac, geometry=geometry, currents=columns)
