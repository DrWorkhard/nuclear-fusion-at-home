import netCDF4
import numpy as np
import pytest
from test_vmec_trace import _torus

from fusion_baselines.clebsch_field import sample_coordinates
from fusion_baselines.qi_field_grid import fidelity, nested_errors, relative_max, sample


def fixture(path):
    _torus(path)
    with netCDF4.Dataset(path, "r+") as ds:
        ds.createVariable("phi", "f8", ("radial",))[:] = np.linspace(0, 2 * np.pi, 5)
        for name, values in (("gmnc", [-0.24, -0.032]), ("bsupumnc", [2, 0.1]),
                             ("bsupvmnc", [3, -0.2])):
            ds.createVariable(name, "f8", ("radial", "mode"))[:] = np.tile(values, (5, 1))
        ds["lmns"][:, 1] = 0.1 * np.arange(5)


@pytest.mark.parametrize("surface", [0.25, 0.5, 0.75])
def test_matrix_reader_against_independent_old_loop(tmp_path, surface):
    path = tmp_path / "wout.nc"
    fixture(path)
    old, _ = sample_coordinates(path, surface, 32)
    new = sample(path, surface, 32)
    np.testing.assert_allclose(new["radius"], 3 + 0.4 * np.cos(new["theta"]), atol=1e-14)
    np.testing.assert_allclose(new["height"], 0.4 * np.sin(new["theta"]), atol=1e-14)
    for key in old:
        np.testing.assert_allclose(old[key], new[key], rtol=1e-14, atol=1e-14)
    fine = sample(path, surface, 64)
    assert max(nested_errors(new, fine).values()) < 1e-14
    assert all(v == 0 for v in fidelity(new, new).values())


def test_nonfinite_coefficients_rejected(tmp_path):
    path = tmp_path / "wout.nc"
    fixture(path)
    with netCDF4.Dataset(path, "r+") as ds:
        ds["gmnc"][2, 0] = np.nan
    with pytest.raises(ValueError, match="nonfinite"):
        sample(path, 0.5, 64)


def test_relative_comparison_not_allowed_zero_scale():
    with pytest.raises(ValueError, match="nonzero"):
        relative_max([1], [0])


def test_nonnested_arrays_rejected():
    with pytest.raises(ValueError):
        nested_errors({"g": np.ones((3, 3))}, {"g": np.ones((8, 8))})


@pytest.mark.parametrize("mode,value", [("xm", 0), ("xn_nyq", 0.5)])
def test_duplicate_or_fractional_modes_rejected(tmp_path, mode, value):
    path = tmp_path / "wout.nc"
    fixture(path)
    with netCDF4.Dataset(path, "r+") as ds:
        ds[mode][1] = value
    with pytest.raises(ValueError, match="mode pairs"):
        sample(path, 0.5, 64)
