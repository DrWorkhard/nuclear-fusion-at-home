import numpy as np
import pytest

from fusion_baselines.curvature_bounds import classify_enclosure, curvature_enclosure, derivatives


def ellipse(a=2, b=1, phase=0.0):
    c = np.zeros((3, 3))
    c[0, 1:] = [-a*np.sin(phase), a*np.cos(phase)]
    c[1, 1:] = [b*np.cos(phase), b*np.sin(phase)]
    return c


def test_analytical_fourier_derivatives():
    t = np.array([0, 0.13, 0.5, 0.99])
    values = derivatives(ellipse(2, 2), t)
    for k in (1, 2, 3):
        expected = (2*(2*np.pi)**k) * np.stack([
            np.cos(2*np.pi*t + k*np.pi/2), np.sin(2*np.pi*t + k*np.pi/2), np.zeros_like(t)], axis=1)
        np.testing.assert_allclose(values[k-1], expected, atol=1e-11)


def test_circle_bounds_refine_and_transform():
    c = ellipse(2, 2)
    widths = []
    for n in [40, 80, 160]:
        bound = curvature_enclosure(c, n)
        assert bound["regularity_resolved"]
        assert bound["maximum_lower_bound"] == pytest.approx(0.5, abs=1e-14)
        assert bound["maximum_upper_bound"] >= 0.5
        widths.append(bound["maximum_upper_bound"] - 0.5)
    assert widths[0] > widths[1] > widths[2]
    assert classify_enclosure(bound, 0.51) == "pass"
    transformed = 10 * np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]]) @ c
    transformed[:, 0] = [42, 0.2, -7]
    scaled = curvature_enclosure(transformed, 160)
    assert scaled["maximum_upper_bound"] == pytest.approx(bound["maximum_upper_bound"] / 10)


def test_ellipse_peak_between_coarse_nodes_cannot_be_false_pass():
    # Shift both maxima between the combined node/midpoint grid of N=40.
    c = ellipse(2, 1, np.pi / 80)
    coarse = curvature_enclosure(c, 40)
    assert coarse["maximum_lower_bound"] < 2
    assert coarse["maximum_upper_bound"] >= 2
    limit = (coarse["maximum_lower_bound"] + 2) / 2
    assert classify_enclosure(coarse, limit) == "unresolved"
    fine = curvature_enclosure(c, 80)
    assert fine["maximum_lower_bound"] == pytest.approx(2)
    assert fine["maximum_upper_bound"] >= 2
    assert classify_enclosure(fine, limit) == "fail"


def test_stationary_curves_and_bad_inputs_fail_closed():
    stationary = np.zeros((3, 3))
    assert classify_enclosure(curvature_enclosure(stationary, 40), 1) == "unresolved"
    stationary[0, 2] = 1
    assert not curvature_enclosure(stationary, 40)["regularity_resolved"]
    for c in [np.zeros((2, 3)), np.full((3, 3), np.nan), np.zeros((3, 4))]:
        with pytest.raises(ValueError):
            curvature_enclosure(c, 40)
    for n in [0, 3, 4.5, True]:
        with pytest.raises(ValueError):
            curvature_enclosure(ellipse(), n)
