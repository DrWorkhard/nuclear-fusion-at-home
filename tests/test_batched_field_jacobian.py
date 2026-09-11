from types import SimpleNamespace

import numpy as np
import pytest

from fusion_baselines.batched_field_jacobian import batched_field_jacobian, projected_filament


def circle(radius=1.3, n=200):
    t = 2 * np.pi * np.arange(n) / n
    g = np.column_stack((np.cos(t), np.sin(t), np.zeros(n)))
    tangent = 2 * np.pi * np.column_stack((-np.sin(t), np.cos(t), np.zeros(n)))
    return radius * g, radius * tangent, g[:, :, None], tangent[:, :, None]


def test_axis_field_radius_derivative_and_direct_quadrature():
    a = 1.3
    points = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.7], [0.2, -0.1, 1.0]])
    weights = np.tile([0.0, 0.0, 1.0], (3, 1))
    g, t, dg, dt = circle(a)
    z, jac = projected_filament(points, weights, g, t, dg, dt)
    h = points[:2, 2]
    expected = 2 * np.pi * 1e-7 * a * a / (a * a + h * h) ** 1.5
    derivative = 2 * np.pi * 1e-7 * a * (2 * h * h - a * a) / (a * a + h * h) ** 2.5
    np.testing.assert_allclose(z[:2], expected, rtol=1e-13)
    np.testing.assert_allclose(jac[:2, 0], derivative, rtol=1e-13)
    direct = []
    for p, w in zip(points, weights, strict=True):
        r = p - g
        direct.append(1e-7 * np.mean(np.cross(t, r) @ w / np.linalg.norm(r, axis=1) ** 3))
    np.testing.assert_allclose(z, direct, rtol=1e-13)
    plus = projected_filament(points, weights, *circle(a + 1e-5))[0]
    minus = projected_filament(points, weights, *circle(a - 1e-5))[0]
    np.testing.assert_allclose((plus - minus) / 2e-5, jac[:, 0], rtol=1e-8, atol=1e-17)


def test_arbitrary_geometry_perturbations():
    rng = np.random.default_rng(52)
    g, t, _, _ = circle()
    dg, dt = rng.normal(size=(200, 3, 4)), rng.normal(size=(200, 3, 4))
    points, weights = rng.normal(size=(2, 9, 3))
    points[:, 2] += 4
    z, jac = projected_filament(points, weights, g, t, dg, dt)
    for i in range(4):
        plus = projected_filament(
            points, weights, g + 1e-5 * dg[:, :, i], t + 1e-5 * dt[:, :, i], dg, dt
        )[0]
        minus = projected_filament(
            points, weights, g - 1e-5 * dg[:, :, i], t - 1e-5 * dt[:, :, i], dg, dt
        )[0]
        np.testing.assert_allclose((plus - minus) / 2e-5, jac[:, i], rtol=1e-6, atol=1e-16)
    assert np.all(np.isfinite(z))


def test_adapter_permutation_shared_geometry_and_dependent_current():
    g, t, dg, dt = circle()
    curve = SimpleNamespace(
        full_dof_names=["radius"],
        dof_names=["radius"],
        quadpoints=np.arange(200) / 200,
        gamma=lambda: g,
        gammadash=lambda: t,
        dgamma_by_dcoeff=lambda: dg,
        dgammadash_by_dcoeff=lambda: dt,
    )
    objective = SimpleNamespace(dof_names=["current", "radius"], x=np.array([2.0, 1.3]))
    # I1=I and I2=5-I share one geometry DOF: current derivatives cancel exactly.
    coils = [
        SimpleNamespace(
            curve=curve,
            current=SimpleNamespace(
                get_value=lambda v=v: v, vjp=lambda w, sign=sign: lambda obj: np.array([sign, 0.0])
            ),
        )
        for v, sign in ((2.0, 1.0), (3.0, -1.0))
    ]
    points, weights = np.array([[0.0, 0.0, 0.4]]), np.array([[0.0, 0.0, 1.0]])
    z, jac = batched_field_jacobian(SimpleNamespace(coils=coils), objective, points, weights)
    unit, derivative = projected_filament(points, weights, g, t, dg, dt)
    np.testing.assert_allclose(z, 5 * unit)
    np.testing.assert_allclose(jac[:, 0], 0, atol=1e-20)
    np.testing.assert_allclose(jac[:, 1], 5 * derivative[:, 0])


def test_invalid_singular_and_passive_inputs():
    g, t, dg, dt = circle()
    weights = np.ones((1, 3))
    for points in (g[:1], np.full((1, 3), np.nan), np.empty((0, 3))):
        with pytest.raises(ValueError):
            projected_filament(points, weights, g, t, dg, dt)
    with pytest.raises(ValueError, match="passive"):
        batched_field_jacobian(SimpleNamespace(psc_array=object()), None, None, None)
