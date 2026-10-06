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


def test_interval_gauss_flux_matches_exact_irregular_spline_area():
    from fusion_baselines.flux_labels import interval_flux_integrals

    theta = np.sort(np.random.default_rng(4810).uniform(0, 2*np.pi, 160))
    for modulation in (0., .2):
        radius = .2*(1+modulation*np.cos(2*theta))
        rz = np.column_stack((1.+radius*np.cos(theta), radius*np.sin(theta)))
        spline, _ = polar_contour(rz, [1., 0.])
        area = 0.
        for coefficients, width in zip(spline.c.T, np.diff(spline.x), strict=True):
            polynomial = np.polynomial.Polynomial(coefficients[::-1])
            area += .5*(polynomial*polynomial).integ()(width)
        result = interval_flux_integrals(UniformY(), spline, [1., 0.])
        assert result['line_flux'] == pytest.approx(-area, abs=1e-12)
        assert result['area_flux'] == pytest.approx(-area, abs=1e-12)
        assert result['stokes_abs_error'] < 1e-12
        if not modulation:
            assert area == pytest.approx(np.pi*.2**2, abs=1e-12)


def test_interval_method_controls_produce_json_serializable_reports():
    import json
    import runpy
    from pathlib import Path

    driver = runpy.run_path(str(Path(__file__).resolve().parents[1]
                               /'scripts/diagnose_flux_quadrature.py'))
    rows = json.loads(json.dumps(driver['controls'](lambda: None), allow_nan=False))
    assert len(rows) == 2 and all(row['passed'] for row in rows)


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


def test_late_trace_is_saved_before_deadline_rejection(tmp_path):
    import runpy
    import time
    from pathlib import Path

    from fusion_baselines.coil_fit import Recorder

    driver = runpy.run_path(str(Path(__file__).resolve().parents[1]
                               /"scripts/measure_flux_labels.py"))
    record = Recorder(tmp_path/"late", time.monotonic()-1)
    path = np.arange(12).reshape(3, 4)
    hit = np.arange(10).reshape(2, 5)
    with pytest.raises(TimeoutError):
        driver["save_trace"](record, 0, path, hit)
    with np.load(tmp_path/"late/line-0.npz", allow_pickle=False) as arrays:
        np.testing.assert_array_equal(arrays["path"], path)
        np.testing.assert_array_equal(arrays["hits"], hit)


def test_half_period_pooling_requires_vector_rotation_parity():
    import runpy
    from pathlib import Path

    driver = runpy.run_path(str(Path(__file__).resolve().parents[1]
                               /"scripts/measure_flux_labels.py"))

    class Toroidal:
        def set_points(self, points):
            self.points = points

        def A(self):
            return self.points.copy()

        def B(self):
            x, y, z = self.points.T
            return np.column_stack((-y, x, .1+z))

    points = np.array([[1., .1, .2], [.8, -.2, .3]])
    assert max(driver["half_period_symmetry"](Toroidal(), points).values()) == 0
    with pytest.raises(ValueError, match="symmetry"):
        driver["half_period_symmetry"](UniformY(), points)


def test_launch_correction_preserves_physical_ray_and_rejects_unbounded_steps():
    from fusion_baselines.flux_labels import scaled_launch, secant_scale

    np.testing.assert_allclose(scaled_launch([1.2, .1], [1., 0.], 1.02), [1.204, .102])
    assert secant_scale(1., .72, 1.02, .749) == pytest.approx(1.0206896551724138)
    for args in [(1., .72, 1., .73), (1., .72, 1.02, .70), (1., .72, 1.02, .721)]:
        with pytest.raises(ValueError):
            secant_scale(*args)
    with pytest.raises(ValueError):
        scaled_launch([1.2, .1], [1., 0.], 1.06)
