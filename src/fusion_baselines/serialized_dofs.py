"""Map archived SIMSON DOFs without relying on process-local object numbering."""

import numpy as np


def named_serialized_values(document, names):
    objects = document["simsopt_objs"]
    values = []
    if len(names) != len(set(names)):
        raise ValueError("duplicate global DOF names")
    for name in names:
        owner, local = name.split(":", 1)
        dofs = objects[objects[owner]["dofs"]["value"]]
        labels = dofs["names"]
        data = dofs["x"]["data"]
        free = dofs["free"]["data"]
        if len(labels) != len(set(labels)) or not len(labels) == len(data) == len(free):
            raise ValueError("malformed serialized DOFs")
        index = labels.index(local)
        if free[index] is not True:
            raise ValueError("requested DOF is fixed")
        values.append(data[index])
    result = np.asarray(values, dtype=float)
    if result.shape != (len(names),) or not np.all(np.isfinite(result)):
        raise ValueError("invalid serialized DOF values")
    return result


def base_coil_owners(document):
    objects = document["simsopt_objs"]
    field = objects[document["graph"]["value"]]
    if field["@class"] != "BiotSavart" or len(field["coils"]) != 16:
        raise ValueError("expected a sixteen-coil BiotSavart field")
    owners = []

    def leaves(name, path=(), ancestors=()):
        if name in ancestors:
            raise ValueError("cyclic current graph")
        obj = objects[name]
        kind = obj["@class"]
        if kind == "Current":
            return [(path, name)]
        attributes = {"ScaledCurrent": ["current_to_scale"],
                      "CurrentSum": ["current_a", "current_b"]}.get(kind)
        if attributes is None:
            raise ValueError("unsupported current expression")
        result = []
        for attribute in attributes:
            result.extend(leaves(obj[attribute]["value"], (*path, attribute), (*ancestors, name)))
        return result

    for ref in field["coils"][:4]:
        coil = objects[ref["value"]]
        curve, current = coil["curve"]["value"], coil["current"]["value"]
        if objects[curve]["@class"] != "CurveXYZFourier":
            raise ValueError("expected direct base Fourier curve")
        owners.append((curve, leaves(current)))
    return owners


def dof_permutation(source_names, target_names, owner_map):
    """Return source indices in target order, requiring a complete bijection."""
    if len(source_names) != len(set(source_names)) or len(target_names) != len(set(target_names)):
        raise ValueError("duplicate DOF names")
    translated = []
    for name in source_names:
        owner, local = name.split(":", 1)
        translated.append(owner_map[owner] + ":" + local)
    if len(translated) != len(set(translated)) or set(translated) != set(target_names):
        raise ValueError("DOF mapping is not a complete bijection")
    positions = {name: index for index, name in enumerate(translated)}
    return np.array([positions[name] for name in target_names], dtype=int)
