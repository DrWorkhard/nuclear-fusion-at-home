import numpy as np
import pytest

from fusion_baselines.direct_constraints import map_full_gradient


def test_named_full_gradient_respects_free_flags_and_global_permutation():
    answer = map_full_gradient(["b", "a", "unused"], ["a", "fixed", "b"], ["b", "a"], [2, 100, 3])
    np.testing.assert_array_equal(answer, [3, 2, 0])
    # Even a same-named global column is not an excuse to differentiate a fixed local DOF.
    answer = map_full_gradient(["a", "fixed"], ["a", "fixed"], ["a"], [2, 100])
    np.testing.assert_array_equal(answer, [2, 0])


@pytest.mark.parametrize(
    "global_names,full_names,free_names,gradient",
    [
        (["a", "a"], ["a"], ["a"], [1]),
        (["a"], ["a", "a"], ["a"], [1, 2]),
        (["a"], ["a"], ["a", "a"], [1]),
        (["a"], ["a", "b"], ["b"], [1, 2]),
        (["a", "b"], ["a"], ["b"], [1]),
        (["a"], ["a"], ["a"], [np.nan]),
        (["a"], ["a"], ["a"], [[1]]),
    ],
)
def test_invalid_full_gradient_mapping(global_names, full_names, free_names, gradient):
    with pytest.raises(ValueError):
        map_full_gradient(global_names, full_names, free_names, gradient)
