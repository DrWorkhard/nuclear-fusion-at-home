"""Schedule, summary and comparison controls for the documented Wout path (#115)."""

import json
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines import wout_build as build

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ('evidence/plasma-design-v2/reference-input-401.json',
          'evidence/plasma-balanced-v1/selected-input-401.json')


@pytest.mark.parametrize('path', INPUTS)
def test_registered_inputs_carry_explicit_401_schedule(path):
    result = build.schedule(json.loads((ROOT/path).read_text()))
    assert result['ns_array'] == [12, 25, 51, 101, 201, 401]


@pytest.mark.parametrize('fault', ['missing', 'length', 'end', 'order', 'ftol', 'niter'])
def test_schedule_rejects_implicit_or_wrong_resolution(fault):
    data = dict(ns_array=[12, 101, 401], ftol_array=[1e-8, 1e-11, 1e-12],
                niter_array=[100, 100, 100])
    if fault == 'missing':
        del data['niter_array']
    elif fault == 'length':
        data['ftol_array'] = [1e-8]
    elif fault == 'end':
        data['ns_array'] = [12, 101, 201]
    elif fault == 'order':
        data['ns_array'] = [101, 12, 401]
    elif fault == 'ftol':
        data['ftol_array'][1] = 0.
    else:
        data['niter_array'][0] = 1.5
    with pytest.raises(ValueError):
        build.schedule(data)


def wout(**changes):
    data = dict(ier_flag=np.array(0), ns=np.array(401), aspect=np.array(9.995),
                iotaf=np.linspace(-0.4, -0.5, 5), rmnc=np.arange(12.).reshape(3, 4),
                version_=np.array(b'x'))
    data.update(changes)
    return data


def test_summary_reports_scalars_and_profile_ends():
    result = build.summary(wout())
    assert result['ns'] == 401 and result['ier_flag'] == 0
    assert result['iotaf_axis'] == -0.4 and result['iotaf_edge'] == -0.5


def test_compare_identical_and_measured_differences():
    assert build.compare(wout(), wout())['identical']
    changed = wout(rmnc=np.arange(12.).reshape(3, 4) + np.eye(3, 4)*1e-9)
    result = build.compare(wout(), changed)
    assert not result['identical'] and result['worst_variable'] == 'rmnc'
    assert result['variables']['rmnc']['max_abs'] == pytest.approx(1e-9)
    assert result['worst_max_rel'] == pytest.approx(1e-9/11)


def test_compare_lists_missing_and_reshaped_variables():
    first, second = wout(), wout(rmnc=np.zeros((4, 3)))
    del second['aspect']
    result = build.compare(first, second)
    assert result['only_first'] == ['aspect'] and not result['identical']
    assert result['variables']['rmnc']['comparable'] is False
