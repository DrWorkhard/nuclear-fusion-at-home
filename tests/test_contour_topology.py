import netCDF4
import numpy as np
import pytest

from fusion_baselines.contour_topology import surface_field, two_root_winding


def _grid():
    return np.meshgrid(
        np.arange(128) * 2 * np.pi / 128,
        np.arange(256) * 2 * np.pi / 256,
        indexing="ij",
    )


def test_poloidal_graphs_and_periodic_seam():
    theta, zeta = _grid()
    for phase in [0.173, 0.173 + 1.5 * np.sin(theta)]:
        result = two_root_winding(2 - 0.5 * np.cos(zeta - phase), 2.13)
        assert result["pass"]
        assert result["toroidal_period_winding"] == [0, 0]


def test_helical_winding_is_not_poloidal():
    theta, zeta = _grid()
    for k in [-1, 1, 2]:
        result = two_root_winding(2 - 0.5 * np.cos(zeta - k * theta - 0.173), 2.13)
        assert not result["pass"]
        assert result["classification"] == "nonzero_toroidal_winding"
        assert result["toroidal_period_winding"] == [k, k]


def test_wrong_orientation_multiple_roots_and_exact_contacts():
    theta, zeta = _grid()
    for field in [2 - 0.5 * np.cos(theta - 0.173), 2 - 0.5 * np.cos(2 * zeta - 0.173)]:
        result = two_root_winding(field, 2.13)
        assert not result["pass"]
        assert result["classification"] == "unsupported_root_count"
    for threshold in [1.5, 2.0]:
        result = two_root_winding(2 - 0.5 * np.cos(zeta), threshold)
        assert result["classification"] == "unresolved_vertex_or_tangency"
        assert not result["pass"]


def test_invalid_contour_inputs():
    for field, threshold in [
        (np.ones((4, 4)), np.nan),
        (np.full((4, 4), np.nan), 1),
        (np.ones(4), 1),
        (-np.ones((4, 4)), 1),
    ]:
        with pytest.raises(ValueError):
            two_root_winding(field, threshold)


def test_surface_fourier_radial_interpolation_and_nfp(tmp_path):
    path = tmp_path / "wout.nc"
    with netCDF4.Dataset(path, "w") as d:
        d.createDimension("radial", 5)
        d.createDimension("mode", 2)
        for name, value in {"ns": 5, "nfp": 3, "lasym__logical__": 0}.items():
            d.createVariable(name, "i4").assignValue(value)
        for name, value in {"xm_nyq": [0, 1], "xn_nyq": [0, 3]}.items():
            d.createVariable(name, "f8", ("mode",))[:] = value
        coeff = np.array([[99, 99], [2.125, 0.2], [2.375, 0.2], [2.625, 0.2], [2.875, 0.2]])
        d.createVariable("bmnc", "f8", ("radial", "mode"))[:] = coeff
    actual = surface_field(path, 0.5, 128, 256)
    theta, zeta = _grid()
    np.testing.assert_allclose(actual, 2.5 + 0.2 * np.cos(theta - zeta), atol=1e-14)
    with pytest.raises(ValueError, match="outside interpolation"):
        surface_field(path, 0.99, 128, 256)
