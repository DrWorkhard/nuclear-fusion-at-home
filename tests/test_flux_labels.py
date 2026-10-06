"""Analytic area/flux and incomplete-surface controls for issue #48."""

import numpy as np
import pytest

from fusion_baselines.flux_labels import contour_diagnostics, flux_integrals, polar_contour


class UniformY:
    def set_points(self, points):
        self.points = points

    def A(self):
        return np.column_stack((np.zeros((len(self.points), 2)), -self.points[:, 0]))

    def B(self):
        return np.tile([0., 1., 0.], (len(self.points), 1))


def section(count=160, modulation=0.):
    theta = np.arange(count)*2*np.pi/count+0.012
    radius = .2*(1+modulation*np.cos(2*theta))
    return np.column_stack((1.+radius*np.cos(theta), radius*np.sin(theta)))


def test_signed_flux_matches_analytic_circle_and_nonround_area():
    for modulation in (0., .2):
        spline, _ = polar_contour(section(modulation=modulation), [1., 0.])
        result = flux_integrals(UniformY(), spline, [1., 0.], count=511)
        exact = -np.pi*.2**2*(1+modulation**2/2)
        assert result["line_flux"] == pytest.approx(exact, abs=3e-9)
        assert result["area_flux"] == pytest.approx(exact, abs=3e-9)
        assert result["stokes_abs_error"] < 1e-10


def test_label_and_disjoint_subset_control():
    result = contour_diagnostics(UniformY(), section(), np.array([1., 0.]), -np.pi*.4**2)
    assert result["label"] == pytest.approx(.25, abs=1e-12)
    assert result["max_gap_rad"] == pytest.approx(2*np.pi/160)
    assert all(row["heldout_radius_max_m"] < 1e-12 for row in result["subsets"])


def test_missing_angular_coverage_is_reported_even_when_circle_flux_is_correct():
    theta = np.linspace(0., .5, 40)
    rz = np.column_stack((1.+.2*np.cos(theta), .2*np.sin(theta)))
    _, gap = polar_contour(rz, [1., 0.])
    assert gap > 5.7  # A closed spline alone is not evidence of a closed flux surface.


def test_multivalued_radius_is_detected_by_heldout_residuals():
    rz = section()
    rz[::2] = [1., 0.]+1.1*(rz[::2]-[1., 0.])
    result = contour_diagnostics(UniformY(), rz, np.array([1., 0.]), -np.pi*.4**2)
    assert min(row["heldout_radius_max_m"] for row in result["subsets"]) > .019


@pytest.mark.parametrize("change", ["few", "nan", "duplicate", "axis"])
def test_invalid_contours_fail(change):
    rz = section()
    if change == "few":
        rz = rz[:7]
    elif change == "nan":
        rz[0, 0] = np.nan
    elif change == "duplicate":
        rz[0] = rz[1]
    else:
        rz[0] = [1., 0.]
    with pytest.raises(ValueError):
        polar_contour(rz, [1., 0.])
