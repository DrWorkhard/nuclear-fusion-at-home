import copy

import numpy as np
import pytest

from fusion_baselines.current_normalization import (
    CANONICAL_TOTAL,
    fixed_serialized_total,
    normalize_currents,
)


def test_common_scale_and_fixed_sum():
    source = np.array([3.0, 4.0, 2.0, 1.0])
    values, factor = normalize_currents(source)
    assert factor == CANONICAL_TOTAL / 10
    assert sum(values) == CANONICAL_TOTAL
    np.testing.assert_allclose(values, source * factor, rtol=1e-15)
    assert np.array_equal(source, [3, 4, 2, 1])


@pytest.mark.parametrize("source", [[1, 2, 3], [0] * 4, [-1] * 4, [1, 2, 3, np.nan]])
def test_invalid_source_rejected(source):
    with pytest.raises(ValueError):
        normalize_currents(source)


@pytest.mark.parametrize("total", [0, -1, np.inf, np.nan])
def test_invalid_target_rejected(total):
    with pytest.raises(ValueError):
        normalize_currents([1] * 4, total)


def test_fixed_authoritative_dof_not_constructor():
    document = {"simsopt_objs": {
        "c": {"@class": "Current", "current": -999, "dofs": {"value": "d"}},
        "d": {"free": {"data": [False]}, "x": {"data": [CANONICAL_TOTAL]}},
    }}
    assert fixed_serialized_total(document) == CANONICAL_TOTAL
    changed = copy.deepcopy(document)
    changed["simsopt_objs"]["d"]["free"]["data"] = [True]
    with pytest.raises(ValueError):
        fixed_serialized_total(changed)
    changed = copy.deepcopy(document)
    changed["simsopt_objs"]["duplicate"] = changed["simsopt_objs"]["c"].copy()
    with pytest.raises(ValueError):
        fixed_serialized_total(changed)
