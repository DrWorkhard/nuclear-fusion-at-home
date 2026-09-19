"""Synthetic construction checks only: no project targets or magnetic calls."""

import json
from decimal import Decimal, localcontext

import numpy as np
import pytest

from fusion_baselines import clear_coil_geometry as construction
from fusion_baselines.coupled_coil_audit import fourier_curves


def torus(radius=.2, major=1.0):
    return dict(nfp=2, mpol=2, ntor=0, lasym=False,
                rbc=[dict(m=0, n=0, value=major), dict(m=1, n=0, value=radius)],
                zbs=[dict(m=1, n=0, value=radius)])


def test_fixed_complete_case_matrix():
    cases = construction.cases()
    assert len(cases) == len({c["label"] for c in cases}) == 12
    assert sum(c["nbase"] for c in cases) == 84
    assert {c["d"] for c in cases} == {.10, .14, .18}
    assert {(c["nbase"], c["order"]) for c in cases} == {(6, 5), (8, 7)}
    for row in cases:
        assert row["K"] == (1 if row["method"] == "circle" else row["order"]-1)
        assert 2*row["r_floor"]*np.sin(np.pi/(4*row["nbase"])) > .06


@pytest.mark.parametrize("offset", [0, .5])
def test_native_full_torus_and_analytic_cover(offset):
    data = torus()
    row = construction.surface(data, 32, 48, offset)
    phi = 2*np.pi*(np.arange(32)+offset)/32
    theta = 2*np.pi*(np.arange(48)+offset)/48
    radius = 1+.2*np.cos(theta)
    expected = np.stack((radius[None, :]*np.cos(phi[:, None]),
                         radius[None, :]*np.sin(phi[:, None]),
                         np.broadcast_to(.2*np.sin(theta), (32, 48))), axis=-1)
    np.testing.assert_allclose(row["points"], expected, atol=1e-14, rtol=0)
    assert row["radius_lower"] > 0 and row["full_torus"] is True
    assert row["cover"] > row["bounds"]["phi"]/64+row["bounds"]["theta"]/96
    fine = construction.surface(data, 64, 96, offset)
    assert fine["cover"] < row["cover"]
    assert row["bounds"]["phi"] == pytest.approx(2*np.pi*1.2)
    assert row["bounds"]["theta"] == pytest.approx(2*np.pi*.2*np.sqrt(2))


def test_analytic_m0_centers_and_untruncated_toroidal_modes():
    data = torus()
    data["ntor"] = 2
    data["rbc"].append(dict(m=0, n=2, value=.1))
    data["zbs"].append(dict(m=0, n=1, value=.03))
    phi = .37
    expected = np.array([1+.1*np.cos(4*phi), -.03*np.sin(2*phi)])
    np.testing.assert_allclose(construction.origin([data, data], phi), expected, atol=1e-15)
    row = construction.surface(data, 48, 32)
    assert row["points"].shape == (48, 32, 3)
    assert row["bounds"]["radius_phi"] == pytest.approx(2*np.pi*2*.2)


@pytest.mark.parametrize("mutation", ["nonfinite", "duplicate", "lasym", "nfp", "m", "n",
                                     "rbs", "zbc"])
def test_bad_surface_inputs_rejected(mutation):
    data = torus()
    if mutation == "nonfinite":
        data["rbc"][0]["value"] = np.nan
    elif mutation == "duplicate":
        data["rbc"].append(data["rbc"][0].copy())
    elif mutation == "lasym":
        data["lasym"] = True
    elif mutation == "nfp":
        data["nfp"] = 3
    elif mutation in ("rbs", "zbc"):
        data[mutation] = [dict(m=1, n=0, value=.1)]
    else:
        data["rbc"][0][mutation] = 10
    with pytest.raises(ValueError):
        construction.derivative_bounds(data)


def test_nonpositive_continuous_radius_rejected():
    with pytest.raises(ValueError, match="radius"):
        construction.surface(torus(radius=.8, major=.9), 8, 8)


def mock_surface(points):
    return dict(points=np.asarray(points, float), cover=.01, radius_lower=.2,
                full_torus=True)


def test_sphere_sections_discard_only_proven_distant_opposite_branch():
    row = mock_surface([[1, .1, 0], [1, -.1, .02], [-1, 0, 0], [1, .5, 0]])
    disks = construction.envelope([row], 0, .2, .3, [1, 0])
    assert disks["grid_index"].tolist() == [0, 1]
    assert disks["target_index"].tolist() == [0, 0]
    assert np.all(disks["radii"] > np.sqrt(.21**2-.1**2))
    np.testing.assert_array_equal(disks["centers"], [[0, 0], [0, .02]])
    assert disks["pads"][0] >= 1e-12


def test_near_tangent_disks_keep_small_positive_outward_radius():
    expanded = .2+.01
    row = mock_surface([[1, expanded, 0], [1, expanded+5e-13, 0],
                        [1, expanded+1e-9, 0]])
    disks = construction.envelope([row], 0, .2, .3, [1, 0])
    assert disks["grid_index"].tolist() == [0, 1]
    assert np.all(disks["radii"] > 1e-7)
    assert np.isfinite(disks["radii"]).all()


def test_oblique_near_tangent_radius_is_outward_against_decimal_reference():
    phi, transverse = .713, .2+.01
    c, s = np.cos(phi), np.sin(phi)
    point = np.array([c-transverse*s, s+transverse*c, .03])
    row = mock_surface([point])
    disks = construction.envelope([row], phi, .2, .3, [1, 0])
    assert disks["grid_index"].tolist() == [0]
    with localcontext() as context:
        context.prec = 60
        normal = -Decimal(float(point[0]))*Decimal(float(s)) \
            + Decimal(float(point[1]))*Decimal(float(c))
        expanded = Decimal(.2)+Decimal(.01)
        true_squared = max(Decimal(0), expanded**2-normal**2)
        assert Decimal(float(disks["radii"][0]))**2 >= true_squared
    assert disks["radii"][0] > 1e-7


def test_radial_discard_includes_padding_and_both_targets():
    expanded = .2+.01
    row = mock_surface([[.3-expanded-1e-12, 0, 0], [.3-expanded-1e-8, 0, 0]])
    disks = construction.envelope([row, row], 0, .2, .3, [1, 0])
    assert disks["target_index"].tolist() == [0, 1]
    assert disks["grid_index"].tolist() == [0, 0]


def test_empty_and_unqualified_envelope_rejected():
    with pytest.raises(ValueError, match="empty"):
        construction.envelope([mock_surface([[-2, 0, 0]])], 0, .1, .3, [1, 0])
    row = mock_surface([[1, 0, 0]])
    row["full_torus"] = False
    with pytest.raises(ValueError, match="full-torus"):
        construction.envelope([row], 0, .1, .3, [1, 0])


@pytest.mark.parametrize("value", [np.nan, np.inf, [1.0], complex(1, 2), "1.0"])
def test_invalid_radius_lower_never_creates_qualified_disks(value):
    row = mock_surface([[1, 0, 0]])
    row["radius_lower"] = value
    with pytest.raises(ValueError):
        construction.envelope([row], 0, .1, .3, [1, 0])


@pytest.mark.parametrize("value", [[1+2j], ["1.0"], [object()], [True], [np.nan]])
def test_no_silent_complex_string_or_boolean_geometry_coercion(value):
    with pytest.raises(ValueError):
        construction.finite(value)


@pytest.mark.parametrize("K", [1, 4, 6])
def test_known_circular_support_lp_primal_dual_exact_repeat(K):
    model = construction.problem(dict(centers=[[0, 0]], radii=[.25]), K, 1.0, .3)
    result = construction.solve(model)
    repeat = construction.solve(model)
    assert result == repeat and result["success"] is True and result["status"] == 0
    x, mu, ml, mh = [np.asarray(result[k]) for k in
                     ("x", "inequality_marginals", "lower_marginals", "upper_marginals")]
    assert np.max(model["A"]@x-model["b"]) <= 1e-10
    assert np.all(x >= model["lower"]-1e-10) and np.all(x <= model["upper"]+1e-10)
    assert np.max(mu) <= 1e-10 and np.min(ml) >= -1e-10 and np.max(mh) <= 1e-10
    np.testing.assert_allclose(model["c"]-model["A"].T@mu-ml-mh, 0, atol=1e-8)
    dual = model["b"]@mu+model["lower"]@ml+model["upper"]@mh
    assert abs(dual-model["c"]@x) <= 1e-8
    assert x[0] == pytest.approx(.25+construction.MARGIN, abs=1e-10)
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    assert result["options"]["threads"] == 1 and result["options"]["parallel"] is False
    assert len(result["warnings"]) == 1
    assert result["warnings"][0]["category"] == "OptimizeWarning"
    assert "passed to HiGHS verbatim" in result["warnings"][0]["message"]


def test_lp_rho_lipschitz_includes_frequency_factor():
    K, nangle = 4, 1024
    model = construction.problem(dict(centers=[[0, 0]], radii=[.25]), K, 1, .3)
    weights = np.repeat(np.arange(1, K+1), 2)
    expected = np.pi/nangle*weights*abs(1-weights**2)
    np.testing.assert_array_equal(model["A"][nangle, 2*K+1:], expected)
    assert model["A"].shape == (2*nangle+1+4*K, 4*K+1)


def test_infeasible_lp_preserves_failure_without_inventing_solution():
    model = construction.problem(dict(centers=[[0, 0]], radii=[4.0]), 1, 1, .3)
    result = construction.solve(model)
    assert result["success"] is False and result["x"] is None
    assert result["status"] == 2
    json.dumps(result, allow_nan=False)


def test_clockwise_translated_circle_exact_named_export():
    phi = .2
    result = construction.export_coefficients([.3, .04, -.02], [1, .1], phi, 5)
    expected = np.zeros((3, 11))
    expected[:, 0] = [.98*np.cos(phi), .98*np.sin(phi), .14]
    expected[:2, 2] = .3*np.array([np.cos(phi), np.sin(phi)])
    expected[2, 1] = -.3
    np.testing.assert_allclose(result, expected, atol=1e-16, rtol=0)


@pytest.mark.parametrize("K,order", [(1, 5), (4, 5), (6, 7)])
def test_exact_shaped_export_positions_derivatives_curvature_and_length(K, order):
    h = np.zeros(2*K+1)
    h[0] = .3
    h[1:] = .002*np.sin(np.arange(1, 2*K+1))/(np.repeat(np.arange(1, K+1), 2)**3)
    phi, center, count = .23, np.array([1.1, -.05]), 1024
    coefficients = construction.export_coefficients(h, center, phi, order)
    curves = fourier_curves(coefficients[None, ...], count)
    alpha = -2*np.pi*np.arange(count)/count
    values, first, second = np.full(count, h[0]), np.zeros(count), np.zeros(count)
    for k in range(1, K+1):
        wave = h[2*k-1]*np.sin(k*alpha)+h[2*k]*np.cos(k*alpha)
        values += wave
        first += k*(h[2*k-1]*np.cos(k*alpha)-h[2*k]*np.sin(k*alpha))
        second -= k*k*wave
    planar = np.column_stack((values*np.cos(alpha)-first*np.sin(alpha),
                              values*np.sin(alpha)+first*np.cos(alpha)))+center
    expected = np.column_stack((planar[:, 0]*np.cos(phi), planar[:, 0]*np.sin(phi),
                                planar[:, 1]))
    np.testing.assert_allclose(curves["positions"][0], expected, rtol=0, atol=2e-15)
    speed = np.linalg.norm(curves["tangents"][0], axis=1)
    curvature = (np.linalg.norm(np.cross(curves["tangents"][0], curves["second"][0]), axis=1)
                 / speed**3)
    np.testing.assert_allclose(speed, 2*np.pi*(values+second), rtol=2e-14, atol=1e-14)
    np.testing.assert_allclose(curvature, 1/(values+second), rtol=3e-14, atol=1e-13)
    assert speed.mean() == pytest.approx(2*np.pi*h[0], abs=2e-15)


@pytest.mark.parametrize("h,center,order", [([.3, 0, 0, 0, .1], [1, 0], 2),
                                         ([.3, 0], [1, 0], 5),
                                         ([.3, 0, np.nan], [1, 0], 5),
                                         ([.3, 0, 0], [1, 0, 0], 5)])
def test_no_implicit_truncation_or_nonfinite_export(h, center, order):
    with pytest.raises(ValueError):
        construction.export_coefficients(h, center, 0, order)


@pytest.mark.parametrize("K,order", [(1, 5), (4, 5), (6, 7)])
def test_export_matches_native_curve_by_explicit_local_names(K, order):
    from simsopt.geo import CurveXYZFourier

    h = np.zeros(2*K+1)
    h[0] = .3
    h[1:] = .002*np.cos(np.arange(1, 2*K+1))/np.repeat(np.arange(1, K+1), 2)**3
    coefficients = construction.export_coefficients(h, [1, .02], .29, order)
    curve = CurveXYZFourier(128, order)
    names = [f"{axis}{term}({m})" for axis in "xyz" for term, m in
             [("c", 0)]+[(term, m) for m in range(1, order+1) for term in "sc"]]
    assert curve.local_full_dof_names == names
    for name, value in zip(names, coefficients.ravel(), strict=True):
        curve.set(name, value)
    independent = fourier_curves(coefficients[None], 128)
    for native, key in ((curve.gamma(), "positions"), (curve.gammadash(), "tangents"),
                        (curve.gammadashdash(), "second")):
        np.testing.assert_allclose(native, independent[key][0], rtol=0, atol=8e-14)


def test_synthetic_torus_full_envelope_lp_never_invokes_magnetic_fields(monkeypatch):
    from simsopt.field import BiotSavart

    def forbidden(*args, **kwargs):
        raise AssertionError("geometry initialization must not construct BiotSavart")

    monkeypatch.setattr(BiotSavart, "__init__", forbidden)
    inputs = [torus(.2), torus(.21)]
    surfaces = [construction.surface(data, 64, 64) for data in inputs]
    phi, d, floor = .2, .10, .3
    center = construction.origin(inputs, phi)
    disks = construction.envelope(surfaces, phi, d, floor, center)
    model = construction.problem(disks, 4, center[0], floor)
    result = construction.solve(model)
    assert result["success"] is True
    x = np.asarray(result["x"])
    assert max(model["A"]@x-model["b"]) <= 1e-10
    coeff = construction.export_coefficients(x[:9], center, phi, 5)
    positions = fourier_curves(coeff[None], 1024)["positions"][0]
    radius = np.linalg.norm(positions[:, :2], axis=1)
    # Exact Euclidean distance to the surface of this circular torus.
    for minor in (.2, .21):
        distances = abs(np.sqrt((radius-1)**2+positions[:, 2]**2)-minor)
        assert distances.min() >= d


def test_native_nonaxisymmetric_surface_all_mixed_modes_and_signed_n():
    data = torus()
    data.update(mpol=4, ntor=3)
    data["rbc"] += [dict(m=1, n=-2, value=.03), dict(m=3, n=1, value=.006)]
    data["zbs"] += [dict(m=2, n=3, value=.011), dict(m=1, n=-1, value=-.02)]
    nphi, ntheta, offset = 64, 48, .5
    row = construction.surface(data, nphi, ntheta, offset)
    phi = 2*np.pi*(np.arange(nphi)+offset)/nphi
    theta = 2*np.pi*(np.arange(ntheta)+offset)/ntheta
    radius, height = np.zeros((nphi, ntheta)), np.zeros((nphi, ntheta))
    for mode in data["rbc"]:
        radius += mode["value"]*np.cos(mode["m"]*theta[None]-2*mode["n"]*phi[:, None])
    for mode in data["zbs"]:
        height += mode["value"]*np.sin(mode["m"]*theta[None]-2*mode["n"]*phi[:, None])
    expected = np.stack((radius*np.cos(phi[:, None]), radius*np.sin(phi[:, None]), height), axis=-1)
    np.testing.assert_allclose(row["points"], expected, rtol=0, atol=5e-12)


def test_explicit_single_thread_options_reach_native_wrapper(monkeypatch):
    import importlib

    module = importlib.import_module("scipy.optimize._linprog_highs")
    original = module._highs_wrapper
    received = []

    def check(*args, **kwargs):
        options = args[-1]
        received.append(options.copy())
        assert options["threads"] == 1 and options["parallel"] is False
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "_highs_wrapper", check)
    model = construction.problem(dict(centers=[[0, 0]], radii=[.25]), 1, 1, .3)
    result = construction.solve(model)
    assert result["success"] is True and len(received) == 1
    assert result["warnings"] == [dict(category="OptimizeWarning", message=(
        "Unrecognized options detected: {'threads': 1, 'parallel': False}. "
        "These will be passed to HiGHS verbatim."))]
