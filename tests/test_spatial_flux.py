import numpy as np
import pytest

from fusion_baselines.flux_metrics import quadratic_flux
from fusion_baselines.spatial_flux import lift_flux, normal_weights, spatial_flux


def test_raw_quadrature_and_field_direction():
    rng = np.random.default_rng(101)
    normal, field, delta = rng.normal(size=(3, 5, 7, 3))
    z = spatial_flux(field, normal)
    assert z @ z / 2 == pytest.approx(quadratic_flux(field, normal), rel=1e-14)
    exact = np.sum(delta.reshape(-1, 3) * normal_weights(normal), axis=1)
    np.testing.assert_allclose((spatial_flux(field+1e-5*delta, normal)
        - spatial_flux(field-1e-5*delta, normal))/2e-5, exact, rtol=1e-9, atol=1e-10)


def test_lift_value_gradient_and_full_jacobian():
    rng = np.random.default_rng(102)
    z, jac = rng.normal(size=11), rng.normal(size=(11, 5))
    k = 3.7
    r, derivative = lift_flux(z, jac, scale=k)
    phi, dphi = z @ z / 2, z @ jac
    assert r @ r == pytest.approx((k*phi)**2, rel=1e-14)
    np.testing.assert_allclose(derivative.T @ r, k*k*phi*dphi, rtol=1e-14, atol=1e-12)
    for direction in np.eye(5):
        plus = lift_flux(z+1e-5*jac@direction, scale=k)[0]
        minus = lift_flux(z-1e-5*jac@direction, scale=k)[0]
        np.testing.assert_allclose((plus-minus)/2e-5, derivative@direction,
                                   rtol=1e-8, atol=1e-8)


def test_same_objective_different_gauss_newton_rank():
    z = np.array([1.0, 2.0])
    r, jac = lift_flux(z, np.eye(2))
    scalar_jac = z[None, :]
    assert np.linalg.matrix_rank(scalar_jac.T @ scalar_jac) == 1
    assert np.linalg.matrix_rank(jac.T @ jac) == 2
    np.testing.assert_allclose(jac.T @ r, (z @ z / 2) * z)


def test_zero_clipped_and_boundary_branch():
    for z, threshold in [(np.zeros(3), 0), (np.ones(3), 2.0)]:
        r, jac = lift_flux(z, np.ones((3, 2)), threshold=threshold)
        assert not r.any() and not jac.any()
    # Check branch value only: no two-sided derivative exists at positive cut-in.
    r, _ = lift_flux(np.array([2.0]), threshold=2.0)
    np.testing.assert_array_equal(r, [2.0])


@pytest.mark.parametrize("z,jac,kwargs", [
    ([], None, {}), ([[1]], None, {}), ([np.nan], None, {}),
    ([1], [[np.inf]], {}), ([1], [[1], [2]], {}), ([1], np.empty((1, 0)), {}),
    ([1], None, {"scale": 0}), ([1], None, {"scale": np.inf}),
    ([1], None, {"threshold": -1}), ([1], None, {"threshold": np.nan}),
])
def test_invalid_lifts(z, jac, kwargs):
    with pytest.raises(ValueError):
        lift_flux(z, jac, **kwargs)


@pytest.mark.parametrize("normal", [[], [1, 2, 3], [[0, 0, 0]], [[np.nan, 0, 1]]])
def test_invalid_normals(normal):
    with pytest.raises(ValueError):
        normal_weights(normal)
