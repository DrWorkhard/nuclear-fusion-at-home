"""Closed exact current-source curvature qualification for a new classical search."""

import json

import numpy as np
from current_diagnostic_inputs import checked, reference
from geometric_curvature_inputs import arrays, sources
from geometric_descent_inputs import source_arrays
from run_jac_scaled_study import require_committed


def qualified_source(root):
    paths = [
        root / "evidence" / f"geometric-curvature-v1{suffix}.json" for suffix in ("", "-audit")
    ]
    study, audit = [json.loads(p.read_text()) for p in paths]
    selected, frozen, bindings = sources(root)
    if (
        study["status"] != "completed"
        or not study["all_pass"]
        or not study["usefulness_pass"]
        or audit["status"] != "completed"
        or not audit["all_pass"]
        or audit["source"] != reference(paths[0])
        or study["prerequisites"] != bindings
        or len(study["cases"]) != 2
        or selected[1]["label"] != "slsqp"
        or selected[1]["field"]["sha256"]
        != "bb3dc24e817765b8505f539e2e2ca64f4189e280ae0643be3cddcca163f49028"
    ):
        raise ValueError("closed independently qualified frozen SLSQP curvature source required")
    for path in paths:
        require_committed(root, path)
    for ref in [study["protocol"], *study["code"], *audit["code"], *study["installed"]["sources"]]:
        checked(ref)
    row, source, data = study["cases"][1], selected[1], frozen[1]
    if row["source"] != source or not row["all_pass"] or not row["usefulness_pass"]:
        raise ValueError("fixed current-minimum source changed")
    native = arrays(row["local_arrays"])["D"]
    require_committed(root, checked(row["local_arrays"]))
    inverse = np.argsort(row["source_indices_in_target_order"])
    current = source_arrays(source)
    values = np.array([arrays(ref)["values"] for ref in data["bundles"]])
    qualified = dict(
        points=data["points"],
        values=values,
        jacobian=current["jacobian"],
        native_matrix=native[:, inverse],
    )
    return (
        source,
        qualified,
        dict(
            study=reference(paths[0]),
            audit=reference(paths[1]),
            frozen_bindings=bindings,
            native_matrix=row["local_arrays"],
        ),
    )
