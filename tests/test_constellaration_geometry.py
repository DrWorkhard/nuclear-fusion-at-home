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


def check(surface_coordinate=None, wout_coordinate=None, value=np.nan, data=None, wout=None,
          surface_extra_amplitude=0.):
    data = data or {"nfp": 2, "rbc": [{"m": 0, "n": 0, "value": 1.0}],
            "zbs": [{"m": 0, "n": 0, "value": 0.0}]}
    wout = wout or SimpleNamespace(xm=np.array([0]), xn=np.array([0]),
                           rmnc=np.array([[1.0]]), zmns=np.array([[0.0]]))
    if wout_coordinate is not None:
        getattr(wout, ("rmnc", "zmns")[wout_coordinate])[0, -1] = value

    def evaluate_points_rz(surface, points):
        result = np.zeros_like(points)
        result[..., 0], result[..., 1] = SCORER.direct_rz(
            data, points[..., 0], points[..., 1])
        result[..., 1] += surface_extra_amplitude*np.sin(64*points[..., 0])
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
    entries = data["rbc"] + data["zbs"]
    mpol = max(e["m"] for e in entries) + 1
    if surface_extra_amplitude:
        mpol = max(mpol, 65)
    ntor = max(abs(e["n"]) for e in entries)
    coefficients = {key: np.zeros((mpol, 2*ntor+1)) for key in ("rbc", "zbs")}
    for key in coefficients:
        for entry in data[key]:
            coefficients[key][entry["m"], entry["n"]+ntor] = entry["value"]
    if surface_extra_amplitude:
        coefficients["zbs"][64, ntor] += surface_extra_amplitude
    converted = SimpleNamespace(r_cos=coefficients["rbc"], z_sin=coefficients["zbs"],
                                n_field_periods=data["nfp"])
    with patch.dict(sys.modules, modules):
        with np.errstate(invalid="ignore"):
            return SCORER.geometry_check(data, converted, {"scale": 1.0}, wout)


def test_finite_matching_geometry_keeps_zero_residuals():
    assert check() == {"grid": [64, 128], "surface_vs_input": 0.0,
                       "vmec_boundary_vs_input": 0.0,
                       "vmec_boundary_vs_input_theta_flipped": 0.0,
                       "surface_coefficient_bound": 0.0, "vmec_boundary_coefficient_bound": 0.0}


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


@pytest.mark.parametrize("m,n", [(64, 0), (0, 64)])
def test_missing_high_mode_cannot_pass_by_grid_aliasing(m, n):
    data = {"nfp": 2, "rbc": [{"m": 0, "n": 0, "value": 1.0}],
            "zbs": [{"m": m, "n": n, "value": 0.1}]}
    result = check(data=data)
    # The original sampled criterion misses this entire mode.
    assert result["vmec_boundary_vs_input"] < SCORER.GEOMETRY_RTOL
    assert result["surface_coefficient_bound"] == 0.0
    assert result["vmec_boundary_coefficient_bound"] == 0.1
    with pytest.raises(ValueError, match="vmec_boundary_coefficient_bound"):
        SCORER.check_geometry({"R00": 1., "max_abs_difference_to_vmecpp_reader": 0.}, result)


def test_fourier_bound_normalization_and_canonical_sine_sign():
    data = {"nfp": 2,
            "rbc": [{"m": 0, "n": 0, "value": 2.},
                    {"m": 0, "n": -1, "value": 1.},
                    {"m": 0, "n": 1, "value": 2.}],
            "zbs": [{"m": 0, "n": 1, "value": 0.25},
                    {"m": 0, "n": -1, "value": 0.125},
                    {"m": 0, "n": 0, "value": 17.}]}
    assert SCORER.fourier_error_bound(
        data, [0, 0], [0, 2], [1., 1.5], [0., 0.0625], .5) == 0.
    # A missing or extra physical mode contributes even outside the input mode set.
    assert SCORER.fourier_error_bound(
        data, [0, 0, 1], [0, 2, 0], [1., 1.5, .125], [0., .0625, 0.], .5) == .25
    assert SCORER.fourier_error_bound(
        data, [0, 0], [0, 3], [1., 1.5], [0., .0625], .5) == 6.


@pytest.mark.parametrize("field,value", [(0, [0.5]), (1, [np.nan]), (2, [np.inf]),
                                         (3, [0., 1.]), (0, [[0]])])
def test_fourier_bound_rejects_malformed_modes_and_coefficients(field, value):
    data = {"nfp": 2, "rbc": [{"m": 0, "n": 0, "value": 1.}],
            "zbs": [{"m": 0, "n": 0, "value": 0.}]}
    arrays = [[0], [0], [1.], [0.]]
    arrays[field] = value
    with pytest.raises(ValueError):
        SCORER.fourier_error_bound(data, *arrays, 1.)


def test_extra_surface_mode_cannot_hide_on_sampled_grid():
    result = check(surface_extra_amplitude=.1)
    assert result["surface_vs_input"] < SCORER.GEOMETRY_RTOL
    assert result["vmec_boundary_coefficient_bound"] == 0.
    assert result["surface_coefficient_bound"] == .1
    with pytest.raises(ValueError, match="surface_coefficient_bound"):
        SCORER.check_geometry({"R00": 1., "max_abs_difference_to_vmecpp_reader": 0.}, result)


def test_negative_poloidal_mode_flips_sine_only():
    data = {"nfp": 2, "rbc": [{"m": 1, "n": 1, "value": .25}],
            "zbs": [{"m": 1, "n": 1, "value": .125}]}
    assert SCORER.fourier_error_bound(data, [-1], [-2], [.25], [-.125], 1.) == 0.


def test_nonfinite_parser_coordinate_cannot_hide_behind_finite_other_coordinate(tmp_path):
    data = {"lasym": False, "rbs": None, "zbc": None, "nfp": 2,
            "rbc": [{"m": 0, "n": 0, "value": 1.}],
            "zbs": [{"m": 1, "n": 0, "value": .1}]}
    vmec = ModuleType("vmecpp")
    vmec.VmecInput = SimpleNamespace(
        from_file=lambda path: SimpleNamespace(mpol=2, ntor=0,
                                               rbc=np.array([[1.], [0.]]),
                                               zbs=np.array([[0.], [np.nan]])),
        resize_2d_coeff=lambda array, mpol, ntor: array)
    package = ModuleType("constellaration")
    geometry = ModuleType("constellaration.geometry")
    surface = ModuleType("constellaration.geometry.surface_rz_fourier")
    surface.SurfaceRZFourier = SimpleNamespace
    geometry.surface_rz_fourier = surface
    package.geometry = geometry
    with patch.dict(sys.modules, {"vmecpp": vmec, "constellaration": package,
                                 "constellaration.geometry": geometry,
                                 "constellaration.geometry.surface_rz_fourier": surface}):
        with pytest.raises(ValueError, match="non-finite coefficient conversion"):
            SCORER.convert(tmp_path / "unused.json", data)
