"""Explicit physical graph mapping and a fail-closed first counted bundle guard."""

import numpy as np

from fusion_baselines.serialized_dofs import (
    base_coil_owners,
    dof_permutation,
    named_serialized_values,
)


def mapped_start(source, target, source_names, target_names, stored_x):
    named = named_serialized_values(source, source_names)
    if not np.array_equal(named, stored_x):
        raise ValueError("selected source array differs from named serialization")
    owners = {}

    def bind(old, new):
        if old in owners and owners[old] != new:
            raise ValueError("shared physical owner has inconsistent target mapping")
        owners[old] = new

    for (curve, leaves), (new_curve, new_leaves) in zip(
        base_coil_owners(source), base_coil_owners(target), strict=True
    ):
        bind(curve, new_curve)
        for (path, owner), (new_path, new_owner) in zip(leaves, new_leaves, strict=True):
            if path != new_path:
                raise ValueError("physical current-expression topology changed")
            bind(owner, new_owner)
    permutation = dof_permutation(source_names, target_names, owners)
    return named[permutation], permutation, owners


def initial_error(values, expected):
    values, expected = np.asarray(values), np.asarray(expected)
    if (values.shape != expected.shape or values.shape != (138,)
            or not np.isfinite(values).all() or not np.isfinite(expected).all()):
        raise ValueError("complete finite138-value initial state required")
    error = float(np.max(abs(values - expected) / np.maximum(1, abs(expected))))
    if error > 1e-12:
        raise ValueError(f"initial physical source replay failed: {error}")
    return error
