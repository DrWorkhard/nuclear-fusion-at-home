import numpy as np
import pytest

from fusion_baselines.curvature_witness import circumcircle_curvature


def test_circle_and_scaling():
    angles = np.array([-0.2, 0.0, 0.3])
    points = np.stack([np.zeros(3), 2 * np.cos(angles), 2 * np.sin(angles)], axis=1)
    assert circumcircle_curvature(points) == pytest.approx(0.5, abs=1e-13)
    assert circumcircle_curvature(10 * points + [1, 2, 3]) == pytest.approx(0.05, abs=1e-13)
    assert circumcircle_curvature(points[::-1]) == pytest.approx(0.5, abs=1e-13)


def test_known_parabola_convergence_and_straight_line():
    errors = []
    for h in [0.1, 0.03, 0.01, 0.003]:
        points = [[-h, h*h, 0], [0, 0, 0], [h, h*h, 0]]
        measured = circumcircle_curvature(points)
        assert measured == pytest.approx(2 / (1 + h*h), rel=1e-12)
        errors.append(abs(measured - 2))
    assert all(a > b for a, b in zip(errors[:-1], errors[1:], strict=True))
    assert circumcircle_curvature([[0, 0, 0], [1, 0, 0], [3, 0, 0]]) == 0


def test_degenerate_or_invalid_points():
    for points in (np.zeros((3, 3)), np.ones((2, 3)), np.full((3, 3), np.nan)):
        with pytest.raises(ValueError):
            circumcircle_curvature(points)
