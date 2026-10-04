"""Counterexamples at the shared reference401 Wout boundary."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines.reference_wout import validate_reference

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def reference():
    source = json.loads((ROOT/'evidence/plasma-design-v2/reference-input-401.json').read_text())
    modes = sorted({(r['m'], r['n']) for k in ('rbc', 'zbs') for r in source[k]})
    data = dict(nfp=np.array(2), ns=np.array(401), lasym__logical__=np.array(0),
                phi=np.array([0., source['phiedge']]),
                xm=np.array([m for m, n in modes], dtype=float),
                xn=np.array([2*n for m, n in modes], dtype=float))
    for key, wkey in (('rbc', 'rmnc'), ('zbs', 'zmns')):
        values = {(row['m'], row['n']): row['value'] for row in source[key]}
        data[wkey] = np.array([[values.get(mode, 0.) for mode in modes]])
    return data, source


def test_reference_consistency_accepts_expected_boundary(reference):
    validate_reference(*reference)


@pytest.mark.parametrize('fault', ['period', 'asymmetry', 'resolution', 'flux', 'boundary',
                                  'fractional_mode', 'duplicate_mode', 'nonfinite'])
def test_reference_rejects_mixed_target_semantics(reference, fault):
    data, source = copy.deepcopy(reference)
    if fault == 'period':
        data['nfp'][...] = 3
    elif fault == 'asymmetry':
        data['lasym__logical__'][...] = 1
    elif fault == 'resolution':
        data['ns'][...] = 101
    elif fault == 'flux':
        data['phi'][-1] *= -1
    elif fault == 'boundary':
        data['rmnc'][0, 0] += 1e-5
    elif fault == 'fractional_mode':
        data['xn'][0] += 0.5
    elif fault == 'duplicate_mode':
        data['xm'][1], data['xn'][1] = data['xm'][0], data['xn'][0]
    elif fault == 'nonfinite':
        data['rmnc'][0, 0] = float('nan')
    with pytest.raises(ValueError):
        validate_reference(data, source)
