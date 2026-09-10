import numpy as np
import pytest

from fusion_baselines.clearance_bounds import periodic_pair_clearance_bound


def test_circle_minima_missed_by_odd_grid_and_refinement():
    lower = []
    for n in [31, 63, 127]:
        t = np.arange(n) * 2 * np.pi / n
        first = np.stack([np.cos(t), np.sin(t)], axis=1)
        second = first + [3.0, 0.0]
        sampled = float(np.linalg.norm(first[:, None] - second[None, :], axis=-1).min())
        assert sampled > 1  # exact continuum clearance is one
        bound = periodic_pair_clearance_bound(sampled, n, 2 * np.pi, 4 * np.pi**2, 5)
        lower.append(bound["continuous_distance_lower_bound"])
        assert lower[-1] <= 1
    assert 0 < lower[0] < lower[1] < lower[2] <= 1


def test_touching_constant_and_scale_covariance():
    n = 31
    t = np.arange(n) * 2 * np.pi / n
    first = np.stack([np.cos(t), np.sin(t)], axis=1)
    second = first + [2.0, 0.0]
    sampled = float(np.linalg.norm(first[:, None] - second[None, :], axis=-1).min())
    assert (
        periodic_pair_clearance_bound(sampled, n, 2 * np.pi, 4 * np.pi**2, 4)[
            "continuous_distance_lower_bound"
        ]
        == 0
    )
    assert periodic_pair_clearance_bound(2, 16, 0, 0, 2)["continuous_distance_lower_bound"] == 2
    original = periodic_pair_clearance_bound(0.3, 100, 4, 8, 3)
    scaled = periodic_pair_clearance_bound(3, 100, 40, 80, 30)
    assert scaled["continuous_distance_lower_bound"] == pytest.approx(
        10 * original["continuous_distance_lower_bound"]
    )


def test_invalid_clearance_bound_inputs():
    for args in [(0.1, 8, np.nan, 1, 2), (0.1, 8, -1, 1, 2), (0.1, 8.5, 1, 1, 2), (3, 8, 1, 1, 2)]:
        with pytest.raises(ValueError):
            periodic_pair_clearance_bound(*args)
