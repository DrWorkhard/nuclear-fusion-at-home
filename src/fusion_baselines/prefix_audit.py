"""Exact-prefix test with discrepancy diagnostics, never a post-hoc tolerance."""

import numpy as np


def audit_exact_prefix(new, old, *, length):
    if type(length) is not int or length < 1:
        raise ValueError("positive fixed prefix length required")
    enough = len(new) >= length and len(old) >= length
    mismatches, max_absolute, max_normalized = [], 0.0, 0.0
    for index, (a, b) in enumerate(zip(new[:length], old[:length], strict=False), 1):
        va, vb = np.asarray(a.get("values"), dtype=float), np.asarray(b.get("values"), dtype=float)
        valid = va.shape == vb.shape == (138,) and np.isfinite(va).all() and np.isfinite(vb).all()
        same = (
            valid
            and a["status"] == b["status"] == "completed"
            and a["attempt"] == b["attempt"] == index
            and a["x_sha256"] == b["x_sha256"]
            and np.array_equal(va, vb)
        )
        if not same:
            mismatches.append(index)
        if valid:
            delta = np.abs(va - vb)
            max_absolute = max(max_absolute, float(delta.max()))
            max_normalized = max(max_normalized, float((delta / np.maximum(1, np.abs(vb))).max()))
    return dict(
        required_length=length,
        sufficient_records=enough,
        mismatch_count=len(mismatches),
        first_mismatch=mismatches[0] if mismatches else None,
        max_absolute_value_difference=max_absolute,
        max_normalized_value_difference=max_normalized,
        all_pass=bool(enough and not mismatches),
    )
