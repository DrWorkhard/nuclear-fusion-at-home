"""Read base Fourier parameters and physical currents without a native deserializer."""

import numpy as np


def serialized_state(document):
    objects = document["simsopt_objs"]
    field = objects[document["graph"]["value"]]
    if field["@class"] != "BiotSavart" or len(field["coils"]) != 16:
        raise ValueError("sixteen-coil BiotSavart serialization required")

    def vector(owner):
        obj = objects[objects[owner]["dofs"]["value"]]
        x = np.asarray(obj["x"]["data"], dtype=float)
        if x.ndim != 1 or not np.isfinite(x).all():
            raise ValueError("finite one-dimensional serialized DOFs required")
        return x

    def current(owner, ancestors=()):
        if owner in ancestors:
            raise ValueError("cyclic current graph")
        obj = objects[owner]
        branch = (*ancestors, owner)
        if obj["@class"] == "Current":
            values = vector(owner)
            if values.shape != (1,):
                raise ValueError("scalar Current DOF required")
            value = float(values[0])
        elif obj["@class"] == "ScaledCurrent":
            value = float(obj["scale"]) * current(obj["current_to_scale"]["value"], branch)
        elif obj["@class"] == "CurrentSum":
            value = current(obj["current_a"]["value"], branch) + current(
                obj["current_b"]["value"], branch
            )
        else:
            raise ValueError("unsupported current expression")
        if not np.isfinite(value):
            raise ValueError("nonfinite physical current")
        return value

    coils = [objects[ref["value"]] for ref in field["coils"]]
    bases, regularizations, owners = [], [], []
    for coil in coils[:4]:
        name = coil["curve"]["value"]
        if objects[name]["@class"] != "CurveXYZFourier":
            raise ValueError("direct base Fourier curve required")
        x = vector(name)
        if x.shape != (51,):
            raise ValueError("order8 base coefficients required")
        owners.append(name)
        bases.append(x)
        value = coil["regularization"]
        value = float(value["data"] if isinstance(value, dict) else value)
        if not np.isfinite(value) or value < 0:
            raise ValueError("finite nonnegative regularization required")
        regularizations.append(value)
    if len(set(owners)) != 4:
        raise ValueError("four distinct base curve owners required")
    return dict(
        coefficients=np.asarray(bases),
        currents=np.array([current(c["current"]["value"]) for c in coils]),
        base_regularizations=np.asarray(regularizations),
    )
