import numpy as np
import pytest

from fusion_baselines.affine_current_audit import qr_fit
from fusion_baselines.affine_current_fit import fit_affine, physical_currents


def test_known_three_current_minimum_with_nonzero_residual():
    a = np.vstack((np.diag([1., 2., 3.]), np.zeros((2, 3))))
    z0 = np.array([1., -2., 6., 4., -3.])
    result, audit = fit_affine(z0, a), qr_fit(z0, a)
    assert result["qualified"] and result["rank"] == 3
    assert result["condition"] == 3
    np.testing.assert_allclose(result["delta"], [-1., 1., -2.], atol=1e-15)
    np.testing.assert_allclose(result["residual"], [0., 0., 0., 4., -3.], atol=1e-15)
    assert result["objective_after"] == audit["objective_after"] == 12.5
    assert result["normal_error"] == audit["normal_error"] == 0


def test_overdetermined_nonorthogonal_problem_and_exact_zero_case():
    rng = np.random.default_rng(1729)
    a, z0 = rng.normal(size=(30, 3)), rng.normal(size=30)
    result, independent = fit_affine(z0, a), qr_fit(z0, a)
    assert result["qualified"] and result["normal_error"] < 1e-14
    assert independent["normal_error"] < 1e-14
    np.testing.assert_allclose(result["delta"], independent["delta"], atol=1e-14)
    assert result["objective_after"] <= result["objective_before"]
    zero = fit_affine([1., 2., 3.], np.eye(3))
    assert zero["qualified"] and zero["objective_after"] == 0


@pytest.mark.parametrize("a", [np.zeros((4, 3)), np.ones((4, 3)),
                              np.diag([1., 1., 1e-11]), np.diag([1., 1., 1e-13])])
def test_rank_or_condition_failure_preserved_without_minimizer(a):
    result = fit_affine(np.ones(len(a)), a)
    assert not result["qualified"] and result["status"] == "unqualified_rank_or_condition"
    assert "delta" not in result


def test_invalid_arrays_and_independent_rank_failure():
    with pytest.raises(ValueError):
        fit_affine([1., np.nan, 3.], np.eye(3))
    with pytest.raises(ValueError):
        qr_fit([1., np.nan, 3.], np.eye(3))
    with pytest.raises(ValueError):
        fit_affine(np.ones(3), np.ones((3, 4)))
    with pytest.raises(ValueError, match="rank"):
        qr_fit(np.ones(4), np.ones((4, 3)))


def test_fixed_sum_and_scale_preserved_without_sign_constraint():
    actual = physical_currents([.03, .04, -.01], 1250075.624635464, 1e7)
    np.testing.assert_allclose(actual[:3], [300000., 400000., -100000.], atol=1e-10)
    assert abs(actual.sum()-1250075.624635464) < 1e-9
    for total, scale in ((0, 1), (1, 0), (np.inf, 1), (1, np.nan)):
        with pytest.raises(ValueError):
            physical_currents([1., 2., 3.], total, scale)
