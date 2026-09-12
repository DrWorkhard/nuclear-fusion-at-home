from copy import deepcopy

import numpy as np
import pytest

from fusion_baselines.prefix_audit import audit_exact_prefix


@pytest.mark.parametrize("change", [None, "hash", "ulp", "short", "nan", "status", "order"])
def test_prefix_is_exact_not_small_difference_permission(change):
    old = [dict(attempt=i, status="completed", x_sha256=str(i), values=[1.0] * 138) for i in (1, 2)]
    new = deepcopy(old)
    if change == "hash":
        new[1]["x_sha256"] = "changed"
    elif change == "ulp":
        new[1]["values"][0] = np.nextafter(1.0, 2.0)
    elif change == "short":
        new.pop()
    elif change == "nan":
        new[1]["values"][0] = float("nan")
    elif change == "status":
        new[1]["status"] = "error"
    elif change == "order":
        new.reverse()
    result = audit_exact_prefix(new, old, length=2)
    assert result["all_pass"] is (change is None)
    if change == "ulp":
        assert result["first_mismatch"] == 2
        assert 0 < result["max_absolute_value_difference"] < 1e-15
