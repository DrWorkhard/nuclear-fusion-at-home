"""Synthetic/native-circle controls; never read or evaluate the real study targets."""

import json

import numpy as np
import pytest

from fusion_baselines import coupled_coils as cc
from fusion_baselines.filament_field import filament_field


def torus_input(zsign=1):
    return dict(nfp=2, mpol=2, ntor=0, phiedge=np.pi/100,
                rbc=[dict(m=0, n=0, value=1.0), dict(m=1, n=0, value=0.1)],
                zbs=[dict(m=1, n=0, value=0.1*zsign)])


def synthetic_target(wout, input_json, ninner):
    data = torus_input()
    phi, theta = np.meshgrid(np.pi*np.arange(ninner)/ninner,
                             2*np.pi*np.arange(ninner)/ninner, indexing="ij")
    points, fields = [], []
    for s in (0.25, 0.5, 0.75):
        r = 1+0.1*np.sqrt(s)*np.cos(theta)
        points.append(np.stack((r*np.cos(phi), r*np.sin(phi),
                                0.1*np.sqrt(s)*np.sin(theta)), axis=-1).reshape(-1, 3))
        fields.append(np.stack((-np.sin(phi)/r, np.cos(phi)/r,
                                np.zeros_like(r)), axis=-1).reshape(-1, 3))
    return dict(input=data, inner_points=np.concatenate(points),
                inner_target=np.concatenate(fields),
                target_flux=cc.target_flux_sign(data, np.ones((3, ninner))), sources={})


@pytest.fixture
def factory(monkeypatch):
    monkeypatch.setattr(cc, "load_target", synthetic_target)

    def make(method="N", **kwargs):
        return cc.CoupledCoils("synthetic-not-a-wout", "synthetic-not-a-json", 2, 2, method,
                               ncoil=48, nphi=8, ntheta=8, **kwargs)
    return make


def test_exact_canonical_names_and_invalid_dimensions():
    names = cc.canonical_names(2, 2)
    assert names[:5] == ["coil[0]/xc(0)", "coil[0]/xs(1)", "coil[0]/xc(1)",
                         "coil[0]/xs(2)", "coil[0]/xc(2)"]
    assert names[15] == "coil[1]/xc(0)" and len(set(names)) == 30
    for nbase, order in ((0, 2), (2, 0), (True, 2), (2, 1.5)):
        with pytest.raises(ValueError):
            cc.canonical_names(nbase, order)


@pytest.mark.parametrize("zsign", [1, -1])
def test_analytic_toroidal_circle_stokes_sign_and_normalized_tangent(zsign):
    data = torus_input(zsign)
    points, tangent = cc.loop_geometry(data, 256)
    potential = np.column_stack((np.zeros(256), np.zeros(256), -np.log(points[:, 0])))
    flux = np.mean(np.sum(potential*tangent, axis=1))
    exact = -zsign*2*np.pi*(1-np.sqrt(1-0.1**2))
    assert flux == pytest.approx(exact, rel=1e-13)
    assert cc.target_flux_sign(data, [1.0, 2.0]) == pytest.approx(-zsign*np.pi/100)
    assert cc.target_flux_sign(data, [-1.0, -2.0]) == pytest.approx(zsign*np.pi/100)
    assert np.linalg.norm(tangent[0]) == pytest.approx(2*np.pi*0.1)


@pytest.mark.parametrize("values", [[0.0], [1.0, -1.0], [float("nan")], []])
def test_target_field_orientation_rejects_zero_mixed_nonfinite(values):
    with pytest.raises(ValueError):
        cc.target_flux_sign(torus_input(), values)


def test_degenerate_fan_and_duplicate_boundary_modes_fail():
    data = torus_input()
    data["zbs"][0]["value"] = 0
    with pytest.raises(ValueError):
        cc.target_flux_sign(data, [1.0])
    data = torus_input()
    data["rbc"].append(data["rbc"][0].copy())
    with pytest.raises(ValueError):
        cc.loop_geometry(data, 256)


@pytest.mark.parametrize("method", ["N", "V"])
def test_native_circle_flux_gradient_chain_rule_and_exact_replay(factory, method):
    model = factory(method)
    x = model.seed_x.copy()
    direction = np.sin(np.arange(len(x))+1)
    direction /= np.linalg.norm(direction)
    j, gradient, metrics = model.evaluate(x)
    assert metrics["flux"] == pytest.approx(model.target_flux, rel=1e-14)
    assert metrics["JN"] >= 0 and metrics["JV"] >= 0
    for h in (1e-5, 5e-6):
        fp = model.evaluate(x+h*direction)[0]
        fm = model.evaluate(x-h*direction)[0]
        assert (fp-fm)/(2*h) == pytest.approx(float(gradient@direction), rel=2e-4, abs=1e-8)
    jr, gr, mr = model.evaluate(x)
    assert j == jr and np.array_equal(gradient, gr) and metrics == mr
    other = factory(method)
    j2, g2, m2 = other.evaluate(x)
    assert j == j2 and np.array_equal(gradient, g2) and metrics == m2
    assert model.initialization_work == dict(seed_A_calls=1, seed_A_points=256)


def test_cached_snapshot_and_named_symmetries(factory, monkeypatch):
    model = factory("V")
    x = model.seed_x.copy()
    model.evaluate(x)
    arrays = model.arrays(x)
    snap = model.snapshot(x)
    json.dumps(snap, allow_nan=False)
    bases = np.asarray(snap["base_coefficients"])
    t = np.arange(model.ncoil)/model.ncoil
    phase = 2*np.pi*np.arange(1, model.order+1)[:, None]*t
    for i, row in enumerate(snap["physical"]):
        coeff = np.asarray(row["matrix"]).T@bases[row["base_index"]]
        gamma = (coeff[:, 0, None]+coeff[:, 1::2]@np.sin(phase)
                 + coeff[:, 2::2]@np.cos(phase)).T
        np.testing.assert_allclose(gamma, arrays["coil_positions"][i], atol=1e-15, rtol=0)
        assert row["current"] == arrays["coil_currents"][i]
    selected = arrays["boundary_points"][::8]
    independent = filament_field(selected, arrays["coil_positions"],
                                 arrays["coil_tangents"], arrays["coil_currents"])
    np.testing.assert_allclose(independent, arrays["boundary_B"][::8], rtol=1e-12, atol=1e-13)
    point = arrays["loop_points"][::32]
    vector_potential = np.zeros_like(point)
    for position, tangent, current in zip(arrays["coil_positions"], arrays["coil_tangents"],
                                          arrays["coil_currents"], strict=True):
        distance = np.linalg.norm(point[:, None, :]-position[None, :, :], axis=2)
        vector_potential += 1e-7*current*np.mean(tangent[None, :, :]/distance[..., None], axis=1)
    np.testing.assert_allclose(vector_potential, arrays["loop_A"][::32], rtol=1e-12, atol=1e-13)

    def forbidden(*args, **kwargs):
        raise AssertionError("same-state serialization must not evaluate native state")

    monkeypatch.setattr(model.field, "B", forbidden)
    monkeypatch.setattr(model.geometry, "J", forbidden)
    monkeypatch.setattr(model, "evaluate", forbidden)
    assert model.snapshot(x) == snap
    assert np.array_equal(model.arrays(x)["boundary_B"], arrays["boundary_B"])


def test_frozen_scale_and_denominator_not_recomputed(factory):
    model = factory("V")
    x = model.seed_x.copy()
    _, _, metrics = model.evaluate(x)
    frozen = model.diagnostics(x, metrics["scale"]*1.1, metrics["B2_scale"]*2)
    assert frozen["current"] == pytest.approx(metrics["current"]*1.1)
    assert frozen["flux"] == pytest.approx(metrics["flux"]*1.1)
    assert frozen["JN"] == pytest.approx(metrics["JN"]*1.1**2/2)
    assert frozen["B2_scale"] == metrics["B2_scale"]*2
    assert frozen["frozen_scale"] is True
    snap = model.snapshot(x, metrics["scale"]*1.1, metrics["B2_scale"]*2)
    assert snap["scale"] == metrics["scale"]*1.1
    assert snap["B2_scale"] == metrics["B2_scale"]*2
    assert model.evaluate(x)[2] == metrics


def test_no_runtime_object_name_dependence(factory):
    first, second = factory(), factory()
    assert first.base_curves[0].name != second.base_curves[0].name
    assert first.names == second.names
    assert first.snapshot(first.seed_x) == second.snapshot(second.seed_x)


def test_explicit_x_setter_invalidates_cached_native_state(factory):
    model = factory()
    j, g, _ = model.evaluate(model.seed_x)
    moved = model.seed_x.copy()
    moved[0] += 0.001
    model.x = moved
    jr, gr, _ = model.evaluate(model.seed_x)
    assert j == jr and np.array_equal(g, gr)


def test_wrong_flux_orientation_is_not_a_zero_cost(factory):
    model = factory()
    model.seed_unit_flux *= -1
    with pytest.raises(ValueError, match="orientation"):
        model.evaluate(model.seed_x)


def test_malformed_vector_fixed_dofs_and_zero_filament_fail(factory):
    model = factory()
    with pytest.raises(ValueError):
        model.evaluate(model.seed_x[:-1])
    bad = model.seed_x.copy()
    bad[0] = np.nan
    with pytest.raises(ValueError):
        model.evaluate(bad)
    zero = model.seed_x.reshape(2, 3, 5).copy()
    zero[:, :, 1:] = 0
    with pytest.raises(ValueError, match="stationary"):
        model.evaluate(zero.ravel())
    model.base_curves[0].fix(0)
    with pytest.raises(ValueError, match="masks"):
        model.evaluate(model.seed_x)


@pytest.mark.parametrize("scale,b2", [(0, 1), (np.nan, 1), (1, 0), (1, -1)])
def test_invalid_frozen_normalization_fails(factory, scale, b2):
    model = factory()
    with pytest.raises(ValueError):
        model.diagnostics(model.seed_x, scale, b2)


def test_native_penalty_gradient_with_active_length(factory):
    model = factory("V")
    coeff = model.seed_x.reshape(2, 3, 5).copy()
    coeff[:, :, 1:] *= 1.7
    x = coeff.ravel()
    j, grad, metrics = model.evaluate(x)
    assert metrics["geometry_penalty"] > 0 and min(metrics["lengths"]) > 3.5
    direction = np.cos(np.arange(len(x))+1)
    direction /= np.linalg.norm(direction)
    h = 5e-6
    difference = (model.evaluate(x+h*direction)[0]-model.evaluate(x-h*direction)[0])/(2*h)
    assert np.isfinite(j)
    assert difference == pytest.approx(grad@direction, rel=2e-4, abs=1e-8)


def test_figure_eight_crossing_rejected_despite_trigonometric_roundoff(factory):
    model = factory()
    coefficients = model.seed_x.reshape(2, 3, 5).copy()
    coefficients[0] = 0
    coefficients[0, 0, 0] = 1
    coefficients[0, 0, 1] = 0.1
    coefficients[0, 2, 3] = 0.1
    with pytest.raises(ValueError, match="self-intersection"):
        model.evaluate(coefficients.ravel())
