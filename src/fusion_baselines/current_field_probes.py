"""Fixed central affine probes in explicitly identified current columns only."""

import numpy as np


def central_probes(x, columns, field):
    x, columns = np.asarray(x, dtype=float), np.asarray(columns)
    if (
        x.shape != (207,)
        or not np.isfinite(x).all()
        or columns.shape != (3,)
        or columns.dtype.kind not in "iu"
        or len(set(columns.tolist())) != 3
        or np.any(columns < 0)
        or np.any(columns >= len(x))
    ):
        raise ValueError("207 finite parameters and three explicit current columns required")
    h = 0.001
    before = np.asarray(field(x.copy()), dtype=float).copy()
    if before.size == 0 or before.shape[-1] != 3 or not np.isfinite(before).all():
        raise ValueError("finite Cartesian field grid required")
    pairs, proposals = [], []
    for column in columns:
        fields, points = [], []
        for sign in (1, -1):
            probe = x.copy()
            probe[column] += sign * h
            value = np.asarray(field(probe), dtype=float).copy()
            if value.shape != before.shape or not np.isfinite(value).all():
                raise ValueError("consistent finite affine probe field required")
            fields.append(value)
            points.append(probe.copy())
        pairs.append(fields)
        proposals.append(points)
    pairs, proposals = np.asarray(pairs), np.asarray(proposals)
    slopes = (pairs[:, 0] - pairs[:, 1]) / (2 * h)
    errors = np.array(
        [
            [
                float(
                    np.max(abs(pairs[i, j] - (before + sign * h * slopes[i])))
                    / max(1, float(np.max(abs(pairs[i, j]))))
                )
                for j, sign in enumerate((1, -1))
            ]
            for i in range(3)
        ]
    )
    return dict(
        before=before,
        pairs=pairs,
        slopes=slopes,
        proposals=proposals,
        errors=errors,
        h=h,
        field_requests=7,
        affine_pass=bool(np.max(errors) <= 1e-12),
    )
