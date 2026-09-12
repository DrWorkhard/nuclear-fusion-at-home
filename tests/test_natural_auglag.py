import numpy as np
import pytest

from fusion_baselines.natural_auglag import augmented_residual, update_multipliers


def test_merit_identity_gradient_and_multiplier_sign():
    z, dz = np.array([0.002, -0.001]), np.array([[1.0, 2.0], [-2.0, 3.0]])
    g, dg, lam, rho = (
        np.array([-0.1, 0.2, 0.4]),
        np.array([[1.0, 0.0], [0.0, 1.0], [2.0, 3.0]]),
        np.array([1.0, 0.0, 5.0]),
        10.0,
    )
    r, j = augmented_residual(z, dz, g, dg, lam, rho)
    positive = np.maximum(0, lam - rho * g)
    expected = z @ z / 2e-6 + (positive @ positive - lam @ lam) / (2 * rho)
    np.testing.assert_allclose(r @ r / 2 - lam @ lam / (2 * rho), expected, rtol=1e-14)
    np.testing.assert_allclose(j.T @ r, dz.T @ z / 1e-6 - dg.T @ positive, rtol=1e-14)
    np.testing.assert_array_equal(update_multipliers(g, lam, rho), positive)
    direction = np.array([0.3, -0.7])
    h = 1e-8
    plus = augmented_residual(z + h * dz @ direction, dz, g + h * dg @ direction, dg, lam, rho)[0]
    minus = augmented_residual(z - h * dz @ direction, dz, g - h * dg @ direction, dg, lam, rho)[0]
    np.testing.assert_allclose((plus - minus) / (2 * h), j @ direction, rtol=1e-8, atol=1e-8)


def test_zero_hinge_has_correct_merit_gradient():
    r, j = augmented_residual([0.0], [[0.0]], [0.1], [[2.0]], [1.0], 10.0)
    np.testing.assert_array_equal(r, [0.0, 0.0])
    np.testing.assert_array_equal(j.T @ r, [0.0])


@pytest.mark.parametrize("bad", [0.0, -1.0, np.nan, np.inf])
def test_invalid_scales_rejected(bad):
    with pytest.raises(ValueError):
        augmented_residual([1.0], [[1.0]], [1.0], [[1.0]], [0.0], bad)
    with pytest.raises(ValueError):
        update_multipliers([1.0], [0.0], bad)


def test_negative_or_nonfinite_multipliers_rejected():
    for lam in ([-1.0], [np.nan]):
        with pytest.raises(ValueError):
            augmented_residual([1.0], [[1.0]], [1.0], [[1.0]], lam, 1.0)
        with pytest.raises(ValueError):
            update_multipliers([1.0], lam, 1.0)
