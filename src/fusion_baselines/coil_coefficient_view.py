"""Explicit named Fourier coefficients and independent serialized symmetry transforms."""

import math

import numpy as np

from fusion_baselines.serialized_dofs import base_coil_owners, named_serialized_values


def base_arrays(document, names, vector, *, direction=False):
    named_serialized_values(document, names)  # Validate labels/free masks independently of vector.
    vector = np.asarray(vector, dtype=float)
    if vector.shape != (len(names),) or not np.isfinite(vector).all():
        raise ValueError("finite named vector required")
    indices, objects, result = {n: i for i, n in enumerate(names)}, document["simsopt_objs"], []
    for owner, _ in base_coil_owners(document):
        data = objects[objects[owner]["dofs"]["value"]]
        values = np.asarray(data["x"]["data"], dtype=float).copy()
        if direction:
            values[:] = 0
        for k, (label, free) in enumerate(zip(data["names"], data["free"]["data"], strict=True)):
            if free:
                values[k] = vector[indices[owner + ":" + label]]
        if values.shape != (51,):
            raise ValueError("registered order8 curves required")
        result.append(values.reshape(3, 17))
    return np.asarray(result)


def serialized_physical_coefficients(document, bases):
    """Scalar rotations/reflections from JSON, not runtime native rotation matrices."""
    objects = document["simsopt_objs"]
    owners = [r[0] for r in base_coil_owners(document)]
    bases = np.asarray(bases, dtype=float)
    if len(set(owners)) != 4 or bases.shape != (4, 3, 17) or not np.isfinite(bases).all():
        raise ValueError("four distinct finite order8 base coefficient sets required")

    def transform(owner, ancestors=()):
        if owner in ancestors:
            raise ValueError("cyclic curve graph")
        if owner in owners:
            return bases[owners.index(owner)].copy()
        obj = objects[owner]
        if obj["@class"] != "RotatedCurve" or type(obj["flip"]) is not bool:
            raise ValueError("unsupported serialized curve transform")
        phi = float(obj["phi"])
        if not np.isfinite(phi):
            raise ValueError("finite toroidal rotation required")
        x, y, z = transform(obj["curve"]["value"], (*ancestors, owner))
        sign = -1 if obj["flip"] else 1
        return np.array([math.cos(phi)*x - math.sin(phi)*y,
                         sign*(math.sin(phi)*x + math.cos(phi)*y), sign*z])

    field = objects[document["graph"]["value"]]
    return np.array([transform(objects[c["value"]]["curve"]["value"]) for c in field["coils"]])
