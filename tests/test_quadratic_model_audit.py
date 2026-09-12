import importlib.util
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    'quadratic_audit', Path(__file__).parents[1] / 'scripts/audit_quadratic_field_model.py')
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def fixture(monkeypatch):
    arrays, states, probes = {}, [], []
    z, dz = np.array([1., 2.]), np.eye(2)
    directions = np.eye(2)
    plus = np.stack([z + h*directions for h in (1e-4, 1e-5, 1e-6)], axis=1)
    minus = np.stack([z - h*directions for h in (1e-4, 1e-5, 1e-6)], axis=1)
    for name in ('original', 'selected119'):
        arrays[name] = dict(z=z, dz=dz, local_dz=dz, x=np.zeros(2),
                            jacobian=(z/1e-6)[None, :], directions=directions,
                            plus_z=plus, minus_z=minus)
        states.append(dict(name=name, arrays=name))
    for name, radius in [('original', 1e-2), ('selected119', 1e-4),
                         ('selected119', 1e-3), ('selected119', 1e-2)]:
        step = np.array([radius, -radius])
        actual = z + step
        f0, f1 = z @ z / 2e-6, actual @ actual / 2e-6
        linear = z @ step / 1e-6
        key = f'{name}/{radius}'
        arrays[key] = dict(x=step, step=step, actual_z=actual, values=np.array([f1]))
        prediction = dict(baseline=f0, actual=f1, actual_change=f1-f0,
                          quadratic_change=f1-f0, linear_change=linear,
                          linear_absolute_error=abs(f1-f0-linear),
                          quadratic_absolute_error=0., usefulness_pass=True)
        probes.append(dict(state=name, radius=radius, arrays=key, prediction=prediction))
    monkeypatch.setattr(AUDIT, 'load_arrays', lambda key: deepcopy(arrays[key]))
    return dict(states=states, probes=probes), arrays


def test_independent_audit_pass(monkeypatch):
    report, _ = fixture(monkeypatch)
    checks, records = AUDIT.check_raw(report)
    assert all(checks.values())
    assert len(records) == 4


@pytest.mark.parametrize('corruption', ['number', 'matrix', 'step', 'flag', 'missing'])
def test_audit_rejects_untrusted_summary_and_raw_corruption(monkeypatch, corruption):
    report, arrays = fixture(monkeypatch)
    if corruption == 'number':
        report['probes'][0]['prediction']['actual'] += 1
    elif corruption == 'matrix':
        arrays['original']['local_dz'] = np.eye(2)*2
    elif corruption == 'step':
        arrays['original/0.01']['x'] += 1
    elif corruption == 'flag':
        report['probes'][0]['prediction']['usefulness_pass'] = False
    else:
        report['probes'].pop()
    checks, _ = AUDIT.check_raw(report)
    assert not all(checks.values())
