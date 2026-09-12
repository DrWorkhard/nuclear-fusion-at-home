"""Symbolic current graph audit: three explicit scaled leaves and a fixed total."""

import numpy as np

from fusion_baselines.current_normalization import CANONICAL_TOTAL, fixed_serialized_total


def current_map(document, names):
    objects = document["simsopt_objs"]
    field = objects[document["graph"]["value"]]
    if field["@class"] != "BiotSavart" or len(field["coils"]) != 16:
        raise ValueError("original sixteen-coil current graph required")
    coils = [objects[r["value"]] for r in field["coils"]]
    owners = []
    for coil in coils[:3]:
        scaled = objects[coil["current"]["value"]]
        if scaled["@class"] != "ScaledCurrent" or scaled["scale"] != 1e7:
            raise ValueError("explicit canonical1e7 current scaling required")
        owner = scaled["current_to_scale"]["value"]
        leaf = objects[owner]
        if leaf["@class"] != "Current" or objects[leaf["dofs"]["value"]]["free"]["data"] != [True]:
            raise ValueError("three independent free scalar Current leaves required")
        owners.append(owner)
    if len(set(owners)) != 3 or len(set(names)) != len(names) or len(names) != 207:
        raise ValueError("unique207 named DOFs with three separate currents required")
    columns = np.array([names.index(f"{owner}:x0") for owner in owners], dtype=int)

    def expression(owner, ancestors=()):
        if owner in ancestors:
            raise ValueError("cyclic current expression")
        obj, path = objects[owner], (*ancestors, owner)
        if obj["@class"] == "Current":
            dofs = objects[obj["dofs"]["value"]]
            if dofs["free"]["data"] == [False]:
                return np.zeros(3), float(dofs["x"]["data"][0])
            if owner not in owners:
                raise ValueError("undeclared free current leaf")
            return np.eye(3)[owners.index(owner)], 0.
        if obj["@class"] == "ScaledCurrent":
            a, b = expression(obj["current_to_scale"]["value"], path)
            return obj["scale"]*a, obj["scale"]*b
        if obj["@class"] == "CurrentSum":
            a, b = expression(obj["current_a"]["value"], path)
            c, d = expression(obj["current_b"]["value"], path)
            return a+c, b+d
        raise ValueError("unsupported current expression")

    rows = [expression(c["current"]["value"]) for c in coils]
    matrix, constant = np.array([r[0] for r in rows]), np.array([r[1] for r in rows])
    signs = np.repeat([1, -1, 1, -1], 4)
    expected = signs[:, None]*np.tile(np.vstack((1e7*np.eye(3), -1e7*np.ones(3))), (4, 1))
    offset = signs*np.tile([0., 0., 0., CANONICAL_TOTAL], 4)
    if (fixed_serialized_total(document) != CANONICAL_TOTAL
            or not np.array_equal(matrix, expected) or not np.array_equal(constant, offset)):
        raise ValueError("current expression violates canonical fixed sum or symmetry")
    return dict(columns=columns, owners=owners, matrix=matrix, constant=constant,
                scale=1e7, total=CANONICAL_TOTAL)
