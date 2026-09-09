import netCDF4
import numpy as np
import pytest

from fusion_baselines.vmec_trace import trace_geometry


def _torus(path):
    with netCDF4.Dataset(path, "w") as d:
        d.createDimension("radial", 5)
        d.createDimension("mode", 2)
        for name, value in {"ns": 5, "nfp": 1, "lasym__logical__": 0}.items():
            d.createVariable(name, "i4").assignValue(value)
        for name, values in {
            "xm": [0, 1],
            "xn": [0, 0],
            "xm_nyq": [0, 1],
            "xn_nyq": [0, 0],
        }.items():
            d.createVariable(name, "f8", ("mode",))[:] = values
        for name, values in {
            "rmnc": [3, 0.4],
            "zmns": [0, 0.4],
            "lmns": [0, 0],
            "bmnc": [2, 0],
        }.items():
            d.createVariable(name, "f8", ("radial", "mode"))[:] = np.tile(values, (5, 1))
        d.createVariable("iotas", "f8", ("radial",))[:] = 0.7


def test_circular_torus_geometry_derivatives(tmp_path):
    path = tmp_path / "wout.nc"
    _torus(path)
    result = trace_geometry(path, 0.5, 101, 8, 2)
    theta = result["alpha"][None, :] + 0.7 * result["phi"][:, None]
    speed = np.sqrt((3 + 0.4 * np.cos(theta)) ** 2 + (0.4 * 0.7) ** 2)
    np.testing.assert_allclose(result["theta"], theta, atol=1e-12)
    np.testing.assert_allclose(result["speed"], speed, rtol=1e-12)
    np.testing.assert_allclose(result["B"], 2, atol=1e-12)
    assert result["coordinate_residual_max"] < 1e-10
    assert np.all(np.diff(result["length"], axis=0) > 0)


def test_lambda_inversion_and_invalid_data(tmp_path):
    path = tmp_path / "wout.nc"
    _torus(path)
    with netCDF4.Dataset(path, "r+") as d:
        d["lmns"][:, 1] = 0.1
    result = trace_geometry(path, 0.5, 101, 8, 2)
    target = result["alpha"][None, :] + 0.7 * result["phi"][:, None]
    np.testing.assert_allclose(result["theta"] + 0.1 * np.sin(result["theta"]), target, atol=1e-10)
    with pytest.raises(ValueError, match="outside interpolation"):
        trace_geometry(path, 0.99, 101, 8, 2)
    with netCDF4.Dataset(path, "r+") as d:
        d["bmnc"][:, 0] = np.nan
    with pytest.raises(ValueError, match="nonfinite"):
        trace_geometry(path, 0.5, 101, 8, 2)
