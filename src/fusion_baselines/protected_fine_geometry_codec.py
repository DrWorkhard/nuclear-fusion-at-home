"""Lossless single-mask codec for numeric-only fine geometry snapshot storage.

This boundary verifies the mask and numeric transport, not the completeness or
physical truth of the geometry record; those belong to the independent auditor.
All returned arrays are fresh. Unencoded arrays retain dtype, shape and C-order
element bytes (their memory layout/strides are not part of the storage contract).
"""

import re

import numpy as np

from fusion_baselines.protected_fine_plan import (
    _same,
    validate_case,
    validate_geometry_level,
)
from fusion_baselines.protected_run_snapshots import MAX_ARRAYS, MAX_BYTES

_MASK = "curvature_available"
_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,95}\Z")


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _descriptor(case, level):
    validate_case(case)
    validate_geometry_level(level)
    return dict(
        codec="protected-geometry-mask-v1",
        key=_MASK,
        original_dtype="bool",
        shape=[4 * case["nbase"], level["ncoil"]],
    )


def _arrays(raw, shape, *, encoded):
    _need(
        type(raw) is dict and 0 < len(raw) <= MAX_ARRAYS and _MASK in raw,
        "bounded named geometry arrays with curvature mask required",
    )
    result, size = {}, 0
    for key, array in raw.items():
        _need(type(key) is str and _KEY.fullmatch(key), "plain geometry array key required")
        _need(type(array) is np.ndarray, "exact NumPy geometry arrays required")
        _need(array.dtype.metadata is None, "geometry dtype metadata cannot survive storage")
        size += array.nbytes
        _need(size <= MAX_BYTES and array.ndim <= 8, "bounded geometry arrays required")
        if key == _MASK:
            dtype = np.dtype(np.uint8) if encoded else np.dtype(bool)
            _need(array.dtype == dtype and array.shape == tuple(shape),
                  "exact geometry mask dtype and physical grid shape required")
            if encoded:
                _need(np.all((array == 0) | (array == 1)), "binary uint8 geometry mask required")
            else:
                byte_values = array.view(np.uint8)
                _need(np.all((byte_values == 0) | (byte_values == 1)),
                      "canonical boolean mask storage required for lossless encoding")
            result[key] = array.astype(bool if encoded else np.uint8, order="C", copy=True)
        else:
            _need(array.dtype.kind in "iuf" and np.isfinite(array).all(),
                  "other geometry arrays must remain finite numeric arrays")
            result[key] = array.copy(order="C")
    return result


def encode_geometry(raw, case, level):
    """Return (numeric arrays, exact mask descriptor), without any storage I/O."""
    descriptor = _descriptor(case, level)
    return _arrays(raw, descriptor["shape"], encoded=False), descriptor


def decode_geometry(arrays, descriptor, case, level):
    """Verify the exact descriptor/uint8 mask and restore fresh boolean samples."""
    expected = _descriptor(case, level)
    _need(_same(descriptor, expected), "exact registered geometry mask descriptor required")
    return _arrays(arrays, expected["shape"], encoded=True)
