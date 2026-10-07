"""Check physical scaling, unresolved minima and guarded native-call exclusion."""
import runpy
from pathlib import Path

import numpy as np
import pytest

study = runpy.run_path(str(Path(__file__).resolve().parents[1]
                          /'scripts/diagnose_bounded_return.py'))


def test_known_affine_root_with_scaled_coordinates():
    center = np.array([.96, -.03])
    matrix = np.array([[.8, .2], [-.2, .8]])
    row = study['solve_return'](lambda x: center+matrix@(x-center),
                                center+[.002, .001], lambda: None)
    assert row['solver_success']
    assert row['residual_m'] <= 1e-9
    assert row['point'] == pytest.approx(center, abs=1e-10)
    assert row['trials'][-1]['role'] == 'final_verification'


def test_optimizer_success_does_not_establish_a_root():
    row = study['solve_return'](lambda x: x+np.array([.001, 0.]),
                                np.zeros(2), lambda: None)
    assert row['solver_success']
    assert row['residual_m'] > 1e-9


def test_outside_neighborhood_trial_retained_without_mapping():
    evaluated, retained = [], []

    def mapping(x):
        evaluated.append(x.copy())
        return .5*x+np.array([.1, 0.])

    with pytest.raises(ValueError, match='1 cm'):
        study['solve_return'](mapping, np.zeros(2), lambda: None,
                              lambda rows: retained.append(list(rows)))
    assert all(np.linalg.norm(p) <= .01 for p in evaluated)
    assert retained[-1][-1]['status'] == 'attempted'
    assert 'residual' not in retained[-1][-1]
