import numpy as np
import pytest

from fusion_baselines.budgeted_oracle import BudgetExhausted
from fusion_baselines.gauss_newton_backend import GaussNewtonBackend
from fusion_baselines.inequality_oracle import InequalityOracle


def make_backend():
    state = {}
    matrix = np.array([[1., 2.], [3., -1.]])

    def direct(x):
        state['x'] = x.copy()
        z = matrix @ x
        return np.array([z @ z / 2, 1-x.sum()]), np.vstack((z @ matrix, [-1, -1])), {}

    backend = GaussNewtonBackend(direct, lambda: (matrix @ state['x'], matrix), flux_scale=1)
    return backend, matrix


def test_gn_is_correct_scaled_psd_and_defensive_copy():
    backend, matrix = make_backend()
    x = np.array([0.2, -0.1])
    _, jac, _ = backend.evaluate(x)
    h = backend.hessian_for(x)
    np.testing.assert_array_equal(h, matrix.T @ matrix)
    np.testing.assert_allclose(h @ x, jac[0], atol=1e-15)
    assert np.linalg.eigvalsh(h).min() > 0
    h[:] = 0
    assert np.any(backend.hessian_for(x))
    np.testing.assert_allclose(0.01**2 * backend.hessian_for(x),
                               (0.01*matrix).T @ (0.01*matrix))


def test_shared_oracle_cache_and_budget_covers_hessian_points():
    backend, _ = make_backend()
    oracle = InequalityOracle(backend.evaluate, 1, 2, 1)
    x = np.array([0.2, -0.1])
    oracle.evaluate(x)
    oracle.evaluate(x)
    backend.hessian_for(x)
    assert len(backend.records) == 1 and oracle.cache_hits == 1
    with pytest.raises(BudgetExhausted):
        oracle.evaluate(x+1)
    with pytest.raises(ValueError, match='complete bundle'):
        backend.hessian_for(x+1)


def test_reference_covector_prevents_projection_rounding_amplification_without_changing_hessian():
    native_z = np.array([1e-3, 1e-3])
    batch_z = native_z + np.array([1e-16, 0])
    dz = np.array([[1e7], [-1e7]])

    def direct(x):
        return np.array([native_z @ native_z/2, 1.]), np.vstack((native_z @ dz, [0.])), {}

    old = GaussNewtonBackend(direct, lambda: (batch_z, dz), flux_scale=1)
    with pytest.raises(ValueError, match='identity failed'):
        old.evaluate([0.])
    corrected = GaussNewtonBackend(direct, lambda: (batch_z, dz), flux_scale=1,
                                  native_residual=lambda: native_z)
    values, jac, _ = corrected.evaluate([0.])
    np.testing.assert_array_equal(values, direct([0.])[0])
    np.testing.assert_array_equal(jac, direct([0.])[1])
    np.testing.assert_array_equal(corrected.hessian_for([0.]), dz.T @ dz)
    assert corrected.records[-1]['gradient_normalized_error'] <= 1e-10
    assert corrected.records[-1]['uncoupled_gradient_normalized_error'] > 1e-10


def test_invalid_reference_covector_is_rejected():
    backend, _ = make_backend()
    backend.native_residual = lambda: [np.nan, 0.]
    with pytest.raises(ValueError, match='invalid'):
        backend.evaluate([0.2, -0.1])


@pytest.mark.parametrize('mode', ['value', 'gradient', 'shape', 'nonfinite'])
def test_reject_inconsistent_bundle_and_invalidate_old_hessian(mode):
    backend, _ = make_backend()
    x = np.array([0.2, -0.1])
    backend.evaluate(x)
    if mode in ('value', 'gradient'):
        old = backend.direct

        def corrupt(x):
            values, jac, metrics = old(x)
            if mode == 'value':
                values[0] += 1
            else:
                jac[0, 0] += 1
            return values, jac, metrics

        backend.direct = corrupt
    elif mode == 'shape':
        backend.spatial = lambda: (np.ones(3), np.ones((3, 1)))
    else:
        backend.spatial = lambda: (np.ones(3), np.full((3, 2), np.nan))
    with pytest.raises(ValueError):
        backend.evaluate(x)
    if mode in ('value', 'gradient'):
        np.testing.assert_array_equal(backend.failed_bundle['x'], x)
        assert max(backend.failed_metrics.values()) > 1e-10
    with pytest.raises(ValueError, match='complete bundle'):
        backend.hessian_for(x)
