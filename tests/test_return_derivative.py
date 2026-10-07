"""Residual Jacobians differ from return-map Jacobians by the identity."""
import runpy
from pathlib import Path

import numpy as np
import pytest

study = runpy.run_path(str(Path(__file__).resolve().parents[1]
                          /'scripts/diagnose_return_derivative.py'))


def test_newton_proposal_uses_residual_jacobian():
    matrix = np.array([[.5, 0.], [0., 1.2]])
    row = study['proposal'](matrix, np.array([.001, .002]))
    assert row['step_m'] == pytest.approx([.002, -.01])
    assert np.asarray(row['residual_jacobian']) == pytest.approx(matrix-np.eye(2))


def test_guard_diagnosis_requires_agreement_and_margin():
    def rows(values):
        return [dict(proposal=dict(step_m=[0., v])) for v in values]

    assert 'still leave' in study['decision'](rows([.02, .0201, .0202, .02]))['result']
    assert 'stay inside' in study['decision'](rows([.005, .0051, .0052, .005]))['result']
    assert study['decision'](rows([.01]*4))['result'] == 'unresolved'
    assert study['decision'](rows([.02, .023, .02, .02]))['result'] == 'unresolved'
