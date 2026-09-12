"""Explicit fixed-total-current normalization, without changing coil geometry."""

import numpy as np

CANONICAL_TOTAL = 1250075.624635464


def normalize_currents(currents, total=CANONICAL_TOTAL):
    currents = np.asarray(currents, dtype=float)
    if (
        currents.shape != (4,)
        or not np.isfinite(currents).all()
        or not np.isfinite(total)
        or total <= 0
        or currents.sum() <= 0
    ):
        raise ValueError("four finite currents with positive sum and target required")
    factor = total / float(currents.sum())
    normalized = factor * currents
    normalized[3] = total - sum(normalized[:3])
    if not np.isfinite(normalized).all():
        raise ValueError("nonfinite normalized currents")
    return normalized, factor


def fixed_serialized_total(document):
    """Read the sole fixed scalar Current from authoritative serialized DOFs."""
    objects, fixed = document["simsopt_objs"], []
    for obj in objects.values():
        if obj.get("@class") == "Current":
            dofs = objects[obj["dofs"]["value"]]
            if dofs["free"]["data"] == [False]:
                values = np.asarray(dofs["x"]["data"], dtype=float)
                if values.shape != (1,) or not np.isfinite(values).all():
                    raise ValueError("finite fixed scalar Current required")
                fixed.append(float(values[0]))
    if len(fixed) != 1:
        raise ValueError("exactly one fixed scalar Current required")
    return fixed[0]
