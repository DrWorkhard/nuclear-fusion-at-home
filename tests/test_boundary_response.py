"""Analytic checks of the study's linear box solution and residual weighting."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines.boundary_control_metrics import boundary_metrics

spec = importlib.util.spec_from_file_location('response',
    Path(__file__).resolve().parents[1]/'scripts/explore_boundary_response.py')
response = importlib.util.module_from_spec(spec)
spec.loader.exec_module(response)


@pytest.mark.parametrize('target', [[.1, -.2, .3, -.4], [2, -3, .3, -.4]])
def test_linear_box_exact_separable_solution(target):
    matrix = np.diag([1., 2., 3., 4.])
    residual = -matrix@target
    value, x = response.bounded_step(matrix, residual)
    expected = np.clip(target, -1, 1)
    assert np.allclose(x, expected, atol=1e-14)
    assert value == pytest.approx(np.linalg.norm(matrix@(expected-target)))


def test_rank_deficient_box_can_fit_with_one_saturated_coordinate():
    matrix = np.array([[1., 1., 0., 0.], [0., 0., 1., 1.]])
    value, x = response.bounded_step(matrix, np.array([-1.5, 0.]))
    assert value < 1e-14 and np.all(abs(x) <= 1)


def test_weighted_signed_residual_matches_shared_metric_and_global_current_invariance():
    B = np.array([[[1., 2., 3.], [3., -2., 2.]]])
    normals = np.array([[[1., 0., 0.], [0., 0., 8.]]])
    residual = response.weighted_residual(B, normals)
    assert np.linalg.norm(residual) == pytest.approx(boundary_metrics(B, normals)['normal_rms'])
    assert np.allclose(response.weighted_residual(-3*B, normals), -residual)
    assert not np.isclose(np.linalg.norm(residual), np.sqrt(np.mean(
        (np.sum(B*normals, axis=-1)/np.linalg.norm(normals, axis=-1)
         /np.linalg.norm(B, axis=-1))**2)))
