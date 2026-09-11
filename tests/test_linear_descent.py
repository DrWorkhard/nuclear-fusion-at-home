import numpy as np
import pytest

from fusion_baselines.linear_descent import assess_step, linear_model


def test_sign_scale_and_known_two_dimensional_problem():
    values, jacobian = np.array([0.0, -1.0]), np.array([[-1.0, 2.0], [1.0, 1.0]])
    c, a, b = linear_model(values, jacobian, 1.0)
    np.testing.assert_array_equal(c, [-1, 2])
    np.testing.assert_array_equal(a, [[-1, -1]])
    np.testing.assert_array_equal(b, [-1])
    result = assess_step(values, jacobian, 1.0, [1, 0], 1.0)
    assert result["primal_pass"] and result["predicted_objective_change"] == -1
    assert result["linear_values"] == [-1, 0]
    assert not assess_step(values, jacobian, 1.0, [0, 0], 1.0)["primal_pass"]
    assert not assess_step(values, jacobian, 1.0, [2, 0], 1.0)["primal_pass"]
    scaled = assess_step(values, jacobian, 2.0, [0.5, 0], 0.5)
    assert scaled["linear_values"] == result["linear_values"]


@pytest.mark.parametrize(
    "values,jacobian,scale",
    [
        ([0], [[1]], 1),
        ([0, 1], [[1]], 1),
        ([0, np.nan], [[1], [1]], 1),
        ([0, 1], [[1], [np.inf]], 1),
        ([0, 1], [[1], [1]], 0),
    ],
)
def test_invalid_models_rejected(values, jacobian, scale):
    with pytest.raises(ValueError):
        linear_model(values, jacobian, scale)
