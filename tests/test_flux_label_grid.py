"""Full-grid summaries cannot hide incomplete phases or unqualified observations."""

import runpy
from pathlib import Path

import numpy as np
import pytest

driver = runpy.run_path(str(Path(__file__).resolve().parents[1]
                           /'scripts/measure_flux_labels.py'))


def test_full_grid_is_nominal_and_legacy_launches_stay_unchanged():
    phases = [0., np.pi/2, np.pi, 3*np.pi/2]
    assert driver['launch_grid']() == [(.25, 0.)]+[(.75, theta) for theta in phases]
    assert driver['launch_grid'](True) == [
        (s, theta) for s in (.1, .25, .5, .75, .9) for theta in phases]


@pytest.mark.parametrize('failure', [None, 'missing', 'duplicate', 'line', 'controls'])
def test_surface_aggregate_requires_all_four_qualified_phases(failure):
    rows = [dict(s=s, theta=theta, prefixes=[dict(label=s+.002*i)], passed=True)
            for s in (.1, .25, .5, .75, .9)
            for i, theta in enumerate((0., np.pi/2, np.pi, 3*np.pi/2))]
    if failure == 'missing':
        rows.pop(0)
    elif failure == 'duplicate':
        rows[0]['theta'] = rows[1]['theta']
    elif failure == 'line':
        rows[0].update(passed=False, prefixes=[dict(error='underresolved')])
    result = driver['grid_summary'](rows, failure != 'controls')
    assert len(result) == 5
    first = result[0]
    assert first['numerically_qualified'] == (failure is None)
    if failure is None:
        assert first['max_absolute_offset'] == pytest.approx(.006)
        assert first['phase_spread'] == pytest.approx(.006)
        assert first['phase_spread_exceeds_0_005']
    else:
        assert 'max_absolute_offset' not in first
        assert 'phase_spread' not in first
        assert len(first['labels']) == (3 if failure == 'missing' else 4)
    assert all(row['numerically_qualified'] == (failure != 'controls') for row in result[1:])
