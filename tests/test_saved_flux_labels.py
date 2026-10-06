"""Numerical qualification cannot omit failed reconstruction or matching gates."""

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    'saved_flux_labels', SCRIPTS/'qualify_saved_flux_labels.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.path.remove(str(SCRIPTS))


def passing_line(index=1):
    subset = dict(label=.75, heldout_radius_max_m=1e-5, quadrature_label_change=1e-8)
    prefix = dict(label=.75, crossings=640, max_gap_rad=.1,
                  quadrature_label_change=1e-8, independent_label_error=1e-12,
                  grids=[dict(stokes_abs_error=1e-8)], subsets=[subset.copy(), subset.copy()])
    return dict(index=index, transits=321, prefixes=[copy.deepcopy(prefix) for _ in range(3)])


@pytest.mark.parametrize('failure', ['prefix', 'subset', 'subset quadrature', 'independent',
                                    'matched label', 'trace completion', 'heldout radius'])
def test_failed_required_diagnostic_cannot_qualify(failure):
    line = passing_line()
    assert module.qualified(line, -1.)['passed']
    last = line['prefixes'][-1]
    if failure == 'prefix':
        line['prefixes'][0] = dict(error='missing')
    elif failure == 'subset':
        last['subsets'][0] = dict(error='duplicate polar angles')
    elif failure == 'subset quadrature':
        last['subsets'][0]['quadrature_label_change'] = 1e-4
    elif failure == 'independent':
        last['independent_label_error'] = 1e-9
    elif failure == 'matched label':
        for prefix in line['prefixes']:
            prefix['label'] = .7
    elif failure == 'trace completion':
        line['transits'] = 319
    elif failure == 'heldout radius':
        last['subsets'][0]['heldout_radius_max_m'] = 1e-3
    assert not module.qualified(line, -1.)['passed']


def test_control_is_not_forced_to_the_matched_launch_label():
    line = passing_line(index=0)
    for prefix in line['prefixes']:
        prefix['label'] = .246
        for subset in prefix['subsets']:
            subset['label'] = .246
    assert module.qualified(line, -1.)['passed']
