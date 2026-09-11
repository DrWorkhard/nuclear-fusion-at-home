import numpy as np
import pytest

from fusion_baselines.smooth_bounds import smooth_extremum, soft_squared_clearance


def test_conservative_bounds_constant_offset_and_permutation():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    for upper in (False, True):
        bound, weights = smooth_extremum(x, 2.0, upper=upper)
        if upper:
            assert x.max() <= bound <= x.max() + np.log(len(x)) / 2
        else:
            assert x.min() - np.log(len(x)) / 2 <= bound <= x.min()
        assert weights.sum() == pytest.approx(1.0) and np.all(weights >= 0)
        shifted, _ = smooth_extremum(x + 17.0, 2.0, upper=upper)
        assert shifted == pytest.approx(bound + 17.0)
        permuted, pw = smooth_extremum(x[::-1], 2.0, upper=upper)
        assert permuted == pytest.approx(bound)
        np.testing.assert_allclose(pw[::-1], weights)
        constant, cw = smooth_extremum(np.ones(8) * 3, 4.0, upper=upper)
        assert constant == pytest.approx(3 + (1 if upper else -1) * np.log(8) / 4)
        np.testing.assert_array_equal(cw, np.ones(8) / 8)


def test_extremum_gradients_and_inverse_temperature_scaling():
    x, direction = np.array([0.1, 0.2, 0.4]), np.array([0.3, -0.2, 0.7])
    for upper in (False, True):
        bound, weights = smooth_extremum(x, 7.0, upper=upper)
        plus = smooth_extremum(x + 1e-6 * direction, 7.0, upper=upper)[0]
        minus = smooth_extremum(x - 1e-6 * direction, 7.0, upper=upper)[0]
        assert (plus - minus) / 2e-6 == pytest.approx(weights @ direction, rel=1e-8)
        assert smooth_extremum(3 * x, 7 / 3, upper=upper)[0] == pytest.approx(3 * bound)


def test_squared_distance_bound_and_point_gradients_including_coincidence():
    rng = np.random.default_rng(71)
    a, b = rng.normal(size=(3, 3)), rng.normal(size=(5, 3))
    da, db = rng.normal(size=a.shape), rng.normal(size=b.shape)
    bound, ga, gb = soft_squared_clearance(a, b, beta=3.0, scale=2.0)
    assert bound <= 4 * np.min(np.sum((a[:, None, :] - b[None, :, :]) ** 2, axis=2))
    plus = soft_squared_clearance(a + 1e-6 * da, b + 1e-6 * db, beta=3.0, scale=2.0)[0]
    minus = soft_squared_clearance(a - 1e-6 * da, b - 1e-6 * db, beta=3.0, scale=2.0)[0]
    assert (plus - minus) / 2e-6 == pytest.approx(np.sum(ga * da) + np.sum(gb * db), rel=1e-8)
    np.testing.assert_allclose(ga.sum(axis=0) + gb.sum(axis=0), 0.0, atol=1e-14)
    z, ga, gb = soft_squared_clearance(np.zeros((1, 3)), np.zeros((1, 3)))
    assert z == 0 and not ga.any() and not gb.any()


@pytest.mark.parametrize("x,beta", [([], 1.0), ([np.nan], 1.0), ([1.0], 0.0), ([1.0], np.inf)])
def test_bad_extremum_inputs(x, beta):
    with pytest.raises(ValueError):
        smooth_extremum(x, beta, upper=True)
