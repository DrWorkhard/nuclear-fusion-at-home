"""Geometry-residual controls; no ConStellaration or VMEC runtime required."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "constellaration_metrics_geometry",
    Path(__file__).parents[1] / "scripts/constellaration_metrics.py")
SCORER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCORER)


def check(surface_coordinate=None, wout_coordinate=None, value=np.nan):
    data = {"nfp": 2, "rbc": [{"m": 0, "n": 0, "value": 1.0}],
            "zbs": [{"m": 0, "n": 0, "value": 0.0}]}
    wout = SimpleNamespace(xm=np.array([0]), xn=np.array([0]),
                           rmnc=np.array([[1.0]]), zmns=np.array([[0.0]]))
    if wout_coordinate is not None:
        getattr(wout, ("rmnc", "zmns")[wout_coordinate])[0, -1] = value

    def evaluate_points_rz(surface, points):
        result = np.zeros_like(points)
        result[..., 0] = 1.0
        if surface_coordinate is not None:
            result[0, 0, surface_coordinate] = value
        return result

    package = ModuleType("constellaration")
    geometry = ModuleType("constellaration.geometry")
    surface = ModuleType("constellaration.geometry.surface_rz_fourier")
    surface.evaluate_points_rz = evaluate_points_rz
    geometry.surface_rz_fourier = surface
    package.geometry = geometry
    modules = {"constellaration": package, "constellaration.geometry": geometry,
               "constellaration.geometry.surface_rz_fourier": surface}
    with patch.dict(sys.modules, modules):
        with np.errstate(invalid="ignore"):
            return SCORER.geometry_check(data, object(), {"scale": 1.0}, wout)


def test_finite_matching_geometry_keeps_zero_residuals():
    assert check() == {"grid": [64, 128], "surface_vs_input": 0.0,
                       "vmec_boundary_vs_input": 0.0,
                       "vmec_boundary_vs_input_theta_flipped": 0.0}


def test_finite_mismatch_remains_a_reported_diagnostic():
    result = check(surface_coordinate=1, value=0.125)
    assert result["surface_vs_input"] == 0.125
    assert result["vmec_boundary_vs_input"] == 0.0
    assert result["vmec_boundary_vs_input_theta_flipped"] == 0.0


@pytest.mark.parametrize("coordinate", [0, 1], ids=["R", "Z"])
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf], ids=["nan", "inf", "negative_inf"])
def test_nonfinite_surface_coordinate_is_rejected(coordinate, value):
    with pytest.raises(ValueError, match="non-finite geometry residual"):
        check(surface_coordinate=coordinate, value=value)


@pytest.mark.parametrize("coordinate", [0, 1], ids=["R", "Z"])
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf], ids=["nan", "inf", "negative_inf"])
def test_nonfinite_wout_coordinate_is_rejected(coordinate, value):
    with pytest.raises(ValueError, match="non-finite geometry residual"):
        check(wout_coordinate=coordinate, value=value)
