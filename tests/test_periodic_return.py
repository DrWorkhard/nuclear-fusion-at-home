"""Known linear maps constrain local root/matrix calculations and classification."""
import runpy
from pathlib import Path

import numpy as np
import pytest

study = runpy.run_path(str(Path(__file__).resolve().parents[1]
                          /'scripts/diagnose_periodic_return.py'))


def test_affine_rotation_root_and_matrix():
    angle = .7
    matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    center = np.array([.96, -.03])
    def mapping(x):
        return center+matrix@(x-center)

    root = study['solve_return'](mapping, center+[.002, .001], lambda: None)
    assert root['point'] == pytest.approx(center, abs=1e-12)
    rows = [study['difference_matrix'](mapping, center, h) for h in (1e-5, 5e-6)]
    assert np.max(abs(np.asarray(rows[0]['matrix'])-matrix)) < 1e-10
    assert study['classify'](rows)['classification'] == 'numerically elliptic'


def test_hyperbolic_and_degenerate_boundaries():
    rows = [study['difference_matrix'](lambda x: np.array([2*x[0], .5*x[1]]),
                                      np.zeros(2), h) for h in (1e-5, 5e-6)]
    assert study['classify'](rows)['classification'] == 'numerically hyperbolic'
    assert study['classify']([dict(trace=2., determinant=1.)])['classification'] == 'unresolved'
    rows[0]['determinant'] = 1.01
    assert study['classify'](rows)['classification'] == 'unresolved'


def test_root_neighborhood_guard_retains_failed_trial():
    retained = []
    with pytest.raises(ValueError, match='1 cm'):
        study['solve_return'](lambda x: .5*x+np.array([.1, 0.]), np.zeros(2),
                              lambda: None, lambda rows: retained.append(list(rows)))
    assert retained and retained[-1][-1]['status'] == 'attempted'
