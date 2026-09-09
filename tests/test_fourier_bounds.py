import numpy as np
import pytest

from fusion_baselines.fourier_bounds import periodic_bilinear_error_bound


def test_constant_and_directional_cosine_bounds():
    assert periodic_bilinear_error_bound([2], [0], [0], (8, 16)) == 0
    bound = periodic_bilinear_error_bound([2, 0.5], [0, 0], [0, 3], (8, 16))
    assert bound == pytest.approx(0.5 * 9 * (2 * np.pi / 16) ** 2 / 8)
    coarse = periodic_bilinear_error_bound([0.3, -0.7], [1, 2], [2, -3], (16, 32))
    fine = periodic_bilinear_error_bound([0.3, -0.7], [1, 2], [2, -3], (32, 64))
    assert fine == pytest.approx(coarse / 4)


def test_bound_contains_unsampled_exact_extremum():
    # min of cos(3 theta) + 0.4*cos(5 zeta) is -1.4, but odd grids miss it.
    theta, zeta = np.meshgrid(np.arange(31) * 2 * np.pi / 31, np.arange(53) * 2 * np.pi / 53)
    sampled = 2 + np.cos(3 * theta) + 0.4 * np.cos(5 * zeta)
    bound = periodic_bilinear_error_bound([2, 1, 0.4], [0, 3, 0], [0, 0, 5], (31, 53))
    assert sampled.min() > 0.6
    assert sampled.min() - bound <= 0.6
    assert sampled.max() + bound >= 3.4


def test_invalid_bound_inputs():
    for c, m, n, shape in [
        ([np.nan], [0], [0], (8, 8)),
        ([1], [0.5], [0], (8, 8)),
        ([1], [0], [0], (8.5, 8)),
        ([1], [0, 1], [0], (8, 8)),
    ]:
        with pytest.raises(ValueError):
            periodic_bilinear_error_bound(c, m, n, shape)
