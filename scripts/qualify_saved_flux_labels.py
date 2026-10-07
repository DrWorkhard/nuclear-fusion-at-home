"""Unchanged qualification and independent A-line check from the #48 study."""

import numpy as np

from fusion_baselines import flux_labels as labels
from fusion_baselines.coupled_coil_audit import (
    filament_field_and_potential,
    physical_curves,
)


def qualified(line, edge, expected_label=.75):
    """Frozen reconstruction checks; a failed subset cannot disappear from a verdict."""
    prefixes = line['prefixes']
    if len(prefixes) != 3 or any('error' in p for p in prefixes):
        return dict(passed=False, failures=['incomplete prefixes'])
    a, b = prefixes[-2:]
    subsets = b['subsets']
    if len(subsets) != 2 or any('error' in s for s in subsets):
        return dict(passed=False, failures=['incomplete subsets'])
    tests = {
        'trace completion': line['transits'] >= 320 and b['crossings'] == 640,
        'label convergence': abs(a['label']-b['label']) < 5e-4,
        'angular coverage': b['max_gap_rad'] < .4,
        'subset labels': abs(subsets[0]['label']-subsets[1]['label']) < 5e-4,
        'heldout radius': max(s['heldout_radius_max_m'] for s in subsets) < 1e-4,
        'quadrature': b['quadrature_label_change'] < 1e-5,
        'subset quadrature': max(s['quadrature_label_change'] for s in subsets) < 1e-5,
        'Stokes': b['grids'][-1]['stokes_abs_error']/abs(edge) < 1e-5,
        'independent': b['independent_label_error'] < 1e-10,
    }
    if line['index'] and expected_label is not None:
        tests['matched label'] = abs(b['label']-expected_label) < 5e-4
    return dict(passed=bool(all(tests.values())),
                failures=[name for name, passed in tests.items() if not passed])


def estimate(field, rz, center, edge, record):
    return labels.contour_diagnostics(field, rz, center, edge, record.guard,
                                     radial_count=24, interval_orders=(4, 8))


def independent_label(snapshot, rz, center, edge, record):
    spline, _ = labels.polar_contour(rz, center)
    points, tangent, weights = labels.interval_contour_points(spline, center, 8)
    own = physical_curves(snapshot, 512)
    _, potential = record.call('independent_BA', filament_field_and_potential, points,
                               own['positions'], own['tangents'], own['currents'])
    return float(np.sum(weights*np.sum(potential*tangent, axis=1))/edge)

