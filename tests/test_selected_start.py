import copy

import numpy as np
import pytest
from test_serialized_dofs import fixture

from fusion_baselines.selected_start import initial_error, mapped_start


def test_named_source_is_permuted_not_lexically_copied():
    doc = fixture()
    names = [f"curve{i}:x" for i in range(4)]
    result, permutation, _ = mapped_start(doc, doc, names, names[::-1], np.arange(4))
    np.testing.assert_array_equal(result, [3, 2, 1, 0])
    np.testing.assert_array_equal(permutation, [3, 2, 1, 0])


def test_wrong_saved_array_rejected():
    names = [f"curve{i}:x" for i in range(4)]
    with pytest.raises(ValueError, match="named serialization"):
        mapped_start(fixture(), fixture(), names, names, [0, 1, 2, 9])


def test_current_topology_change_rejected():
    source, target = fixture(), copy.deepcopy(fixture())
    target["simsopt_objs"]["coil0"]["current"] = {"value": "I0"}
    names = [f"curve{i}:x" for i in range(4)]
    with pytest.raises(ValueError, match="topology"):
        mapped_start(source, target, names, names, np.arange(4))


def test_exact_first_bundle_and_corruption():
    values = np.arange(138, dtype=float)
    assert initial_error(values, values) == 0
    changed = values.copy()
    changed[17] += 1e-7
    with pytest.raises(ValueError, match="replay"):
        initial_error(changed, values)


@pytest.mark.parametrize("bad", [np.zeros(137), np.full(138, np.nan)])
def test_incomplete_nonfinite_initial_values_rejected(bad):
    with pytest.raises(ValueError, match="138"):
        initial_error(bad, np.zeros(138))
