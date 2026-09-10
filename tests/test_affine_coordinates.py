import numpy as np
import pytest

from fusion_baselines.affine_coordinates import AffineCoordinates
from fusion_baselines.budgeted_oracle import BudgetedOracle, BudgetExhausted


def test_round_trip_and_origin_ownership():
    origin = np.array([1.2, -3.4])
    transform = AffineCoordinates(origin, 0.01)
    origin[:] = 42
    np.testing.assert_array_equal(transform.physical([0, 0]), [1.2, -3.4])
    np.testing.assert_array_equal(transform.solver([1.2, -3.4]), [0, 0])
    np.testing.assert_allclose(transform.solver(transform.physical([0.7, -2.3])), [0.7, -2.3])


def test_quadratic_chain_rule_and_physical_budget_selection():
    matrix = np.array([[2.0, 0.3], [-0.5, 3.0]])
    target = np.array([0.2, -0.8])
    origin = np.array([1.2, -3.4])
    transform = AffineCoordinates(origin, 0.01)
    oracle = BudgetedOracle(lambda x: (matrix @ x - target, matrix), 3, 2)

    def objective(y):
        value, jacobian = oracle.evaluate(transform.physical(y))
        return value @ value / 2, transform.gradient(jacobian.T @ value)

    y = np.array([0.3, -0.7])
    direction = np.array([0.6, 0.8])
    _, gradient = objective(y)
    eps = 1e-4
    plus, _ = objective(y + eps * direction)
    minus, _ = objective(y - eps * direction)
    assert (plus - minus) / (2 * eps) == pytest.approx(gradient @ direction, rel=1e-8)
    assert oracle.counters()["attempts"] == 3
    np.testing.assert_array_equal(oracle.best["x"], transform.physical(y + eps * direction))
    with pytest.raises(BudgetExhausted):
        objective([0, 0])


@pytest.mark.parametrize("origin,scale", [([], 1), ([np.nan], 1), ([0], 0),
    ([0], -1), ([0], np.inf), ([[1]], 1), ([1], [0.01])])
def test_invalid_transform(origin, scale):
    with pytest.raises(ValueError):
        AffineCoordinates(origin, scale)


def test_invalid_proposals_and_gradients():
    transform = AffineCoordinates([0, 0], 0.01)
    for method in (transform.physical, transform.solver, transform.gradient):
        for value in ([1], [1, np.nan]):
            with pytest.raises(ValueError):
                method(value)
