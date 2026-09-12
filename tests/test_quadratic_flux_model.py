import numpy as np
import pytest

from fusion_baselines.quadratic_flux_model import quadratic_flux_model


def test_affine_residual_quadratic_prediction_is_exact():
    z = np.array([1., 2.])
    jac = np.array([[2., 1.], [-1., 3.]])
    step = np.array([0.5, -0.25])
    result = quadratic_flux_model(z, jac, step, z + jac @ step, flux_scale=2)
    assert result['quadratic_absolute_error'] == 0
    assert result['linear_absolute_error'] > 0
    assert result['matrix_identity_error'] == 0
    assert result['remainder_identity_error'] == 0
    assert result['usefulness_pass']


def test_nonlinear_residual_retains_missing_hessian_and_remainder():
    # z(x)=1+x² at x=1: f''=6, but H_GN=4. q is not the full Taylor model.
    h = 0.1
    actual = np.array([1 + (1 + h)**2])
    result = quadratic_flux_model([2], [[2]], [h], actual, flux_scale=1)
    expected_q = 0.5 * (2 + 2*h)**2
    assert result['baseline'] == 2
    assert result['gn_curvature_term'] == pytest.approx(0.02)
    assert result['quadratic_change'] == pytest.approx(expected_q - 2)
    assert result['quadratic_absolute_error'] > 0
    assert result['remainder_identity_error'] < 1e-15
    assert result['field_linearization_remainder_norm'] == pytest.approx(h*h)


def test_permutation_and_scale_preserve_predictions():
    rng = np.random.default_rng(54)
    z, jac, step = rng.normal(size=7), rng.normal(size=(7, 4)), rng.normal(size=4)
    actual = z + jac @ step + 0.03
    first = quadratic_flux_model(z, jac, step, actual)
    p = [2, 0, 3, 1]
    second = quadratic_flux_model(z, jac[:, p], step[p], actual)
    third = quadratic_flux_model(3*z, 3*jac, step, 3*actual, flux_scale=9e-6)
    for key in ('actual_change', 'quadratic_change', 'linear_change', 'gn_curvature_term'):
        assert first[key] == pytest.approx(second[key], rel=1e-14)
        assert first[key] == pytest.approx(third[key], rel=1e-14)


@pytest.mark.parametrize('z,jac,step,actual,scale', [
    ([], [], [], [], 1),
    ([1], [[1, 2]], [1], [1], 1),
    ([1], [[1]], [1], [1, 2], 1),
    ([np.nan], [[1]], [1], [1], 1),
    ([1], [[np.inf]], [1], [1], 1),
    ([1], [[1]], [1], [1], 0),
    ([1], [[1]], [1], [1], np.inf),
    ([1e300], [[1e300]], [1e300], [1], 1),
])
def test_reject_invalid_or_overflow(z, jac, step, actual, scale):
    with pytest.raises(ValueError):
        quadratic_flux_model(z, jac, step, actual, flux_scale=scale)
