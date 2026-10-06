"""Replay final-prefix A flux and reconstruction, without Wouts or native packages.

Earlier-prefix and separate-plane arithmetic is checked against saved flux values;
native B-fan fields, trajectories and target geometry are not recalculated.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PAYLOAD = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))

from measure_flux_labels import SURFACES, grid_summary, launch_grid  # noqa: E402
from qualify_saved_flux_labels import qualified  # noqa: E402

from fusion_baselines import flux_labels as labels  # noqa: E402
from fusion_baselines.coupled_coil_audit import (  # noqa: E402
    filament_field_and_potential,
    physical_curves,
)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def close(actual, expected, name, tolerance=5e-11):
    if not np.isfinite([actual, expected]).all() or abs(actual-expected) > tolerance:
        raise ValueError(f'{name}: {actual} differs from {expected}')
    return abs(actual-expected)


def line_label(curves, rz, center, edge, order, deadline):
    spline, gap = labels.polar_contour(rz, center)
    points, tangent, weights = labels.interval_contour_points(spline, center, order)
    total = 0.
    for first in range(0, len(points), 128):
        if time.monotonic() >= deadline:
            raise TimeoutError('900 s saved-array replay budget reached')
        _, potential = filament_field_and_potential(points[first:first+128], curves['positions'],
                                                    curves['tangents'], curves['currents'])
        total += float(np.sum(weights[first:first+128]*np.sum(
            potential*tangent[first:first+128], axis=1)))
    if time.monotonic() >= deadline:
        raise TimeoutError('900 s saved-array replay budget reached')
    return total/edge, gap, spline


def derived(row, edge):
    if 'error' in row:
        return
    for grid in row['grids']:
        close(abs(grid['line_flux']-grid['area_flux']), grid['stokes_abs_error'],
              'Stokes arithmetic')
    close(row['grids'][-1]['line_flux']/edge, row['label'], 'derived label')
    close(abs(row['grids'][0]['line_flux']-row['grids'][1]['line_flux'])/abs(edge),
          row['quadrature_label_change'], 'derived order change')
    if 'independent_label' in row:
        close(abs(row['label']-row['independent_label']), row['independent_label_error'],
              'derived independent error')


def main(manifest_sha):
    started = time.monotonic()
    deadline = started+900
    if digest(PAYLOAD/'manifest.json') != manifest_sha:
        raise ValueError('manifest identity mismatch')
    entries = read(PAYLOAD/'manifest.json')
    for name, expected in entries.items():
        path = PAYLOAD/name
        if not path.resolve().is_relative_to(PAYLOAD) or digest(path) != expected:
            raise ValueError('payload mismatch: '+name)
    supervisor = read(PAYLOAD/'supervisor-result.json')
    if (not supervisor['completed']
            or [a['target'] for a in supervisor['arms']] != ['reference401', 'selected401']):
        raise ValueError('both software-complete arms required for this replay')
    maximum, checked, skipped, summaries = 0., 0, [], []
    for target in ('reference401', 'selected401'):
        arm = read(PAYLOAD/target/'run/result.json')
        status = read(PAYLOAD/target/'supervisor-result.json')
        if not (arm['completed'] and arm['deadline_met'] and status['completed']
                and status['clock_consistent'] and status['producer_unchanged']
                and arm['sources_before'] == arm['sources_after']):
            raise ValueError('incomplete arm')
        for path, expected in arm['sources_before'].items():
            local = None
            for component in ('src/fusion_baselines/', 'scripts/', 'docs/optimization/'):
                if '/'+component in path:
                    local = ROOT/component/path.split('/'+component)[1]
                    break
            if local is not None and digest(local) != expected:
                raise ValueError('producer source mismatch: '+str(local))
        snapshot_path = PAYLOAD/f'{target}-snapshot.json'
        if digest(snapshot_path) not in arm['sources_before'].values():
            raise ValueError('snapshot not bound by native producer')
        curves = physical_curves(read(snapshot_path), 512)
        center, edge = arm['center_RZ'], arm['edge']['line_flux']
        controls_path = PAYLOAD/target/'run/control-contours.npz'
        if digest(controls_path) != arm['control_arrays_sha256']:
            raise ValueError('control array mismatch')
        with np.load(controls_path, allow_pickle=False) as data:
            dense_edge = data['edge'].copy()
            indices = data['sample_indices'].copy()
            dense = {s: data[f's{s}'].copy() for s in SURFACES}
            np.testing.assert_array_equal(data['center'], center)
        value, _, _ = line_label(curves, dense_edge, center, edge, 8, deadline)
        maximum = max(maximum, close(value, 1., 'edge label'))
        checked += 1
        if [c['s'] for c in arm['controls']] != list(SURFACES):
            raise ValueError('all five controls required')
        for control in arm['controls']:
            exact, _, _ = line_label(curves, dense[control['s']], center, edge, 8, deadline)
            sample, _, _ = line_label(curves, dense[control['s']][indices], center, edge, 8,
                                      deadline)
            maximum = max(maximum, close(exact, control['exact_flux']/edge, 'dense control'),
                          close(sample, control['label'], 'sampled control'))
            close(abs(sample-exact), control['label_error'], 'control error')
            derived(control, edge)
            checked += 2
        if ([(line['s'], line['theta']) for line in arm['lines']] != launch_grid(True)
                or [line['index'] for line in arm['lines']] != list(range(20))
                or arm['launch_scales'] != [1.]*20):
            raise ValueError('complete unchanged nominal grid required')
        for line in arm['lines']:
            if [p['requested'] for p in line['prefixes']] != [160, 320, 640]:
                raise ValueError('all three prefixes required')
            for row in line['prefixes']+line['planes']:
                derived(row, edge)
            final = line['prefixes'][-1]
            if 'error' in final:
                skipped.append(dict(target=target, index=line['index'], error=final['error']))
            else:
                with np.load(PAYLOAD/target/f'run/line-{line["index"]}.npz',
                             allow_pickle=False) as data:
                    hits = data['hits'].copy()
                hits = hits[(hits[:, 1] >= 0) & (hits[:, 0] > 1e-8)]
                hits = hits[np.argsort(hits[:, 0], kind='stable')][:640]
                rz = np.column_stack((np.hypot(hits[:, 2], hits[:, 3]), hits[:, 4]))
                if len(rz) != 640:
                    raise ValueError('640 crossings required')
                values = []
                for i, order in enumerate((4, 8)):
                    value, gap, _ = line_label(curves, rz, center, edge, order, deadline)
                    values.append(value)
                    maximum = max(maximum, close(value, final['grids'][i]['line_flux']/edge,
                                                 'final prefix'))
                    checked += 1
                close(gap, final['max_gap_rad'], 'gap', 1e-14)
                close(abs(values[0]-values[1]), final['quadrature_label_change'], 'order change')
                maximum = max(maximum, close(values[-1], final['independent_label'],
                                             'saved independent final label'))
                for offset, subset in enumerate(final['subsets']):
                    if 'error' in subset:
                        skipped.append(dict(target=target, index=line['index'], subset=offset,
                                             error=subset['error']))
                        continue
                    values = []
                    for order in (4, 8):
                        value, gap, spline = line_label(curves, rz[offset::2], center, edge,
                                                        order, deadline)
                        values.append(value)
                        checked += 1
                    maximum = max(maximum, close(values[-1], subset['label'], 'subset'))
                    close(abs(values[0]-values[1]), subset['quadrature_label_change'],
                          'subset order')
                    close(gap, subset['max_gap_rad'], 'subset gap', 1e-14)
                    held = rz[1-offset::2]-center
                    angle = np.arctan2(held[:, 1], held[:, 0])
                    residual = float(np.max(abs(np.linalg.norm(held, axis=1)-spline(angle))))
                    close(residual, subset['heldout_radius_max_m'], 'held-out radius', 1e-14)
            verdict = qualified(line, edge, expected_label=None)
            if verdict != {k: line[k] for k in ('passed', 'failures')}:
                raise ValueError('line qualification arithmetic mismatch')
        close(abs(arm['target_oriented_flux']/-.03141592653589793-1),
              arm['target_flux_relative_error'], 'target flux error')
        close(abs(abs(edge/arm['target_oriented_flux'])-1), arm['polar_edge_magnitude_error'],
              'polar edge magnitude error')
        close(abs(edge-arm['edge']['area_flux']), arm['edge']['stokes_abs_error'], 'edge Stokes')
        if not (all(c['passed'] for c in arm['analytic_controls'])
                and arm['target_flux_relative_error'] < 1e-6
                and arm['polar_edge_magnitude_error'] < 1e-5):
            raise ValueError('required initial control failed')
        controls_pass = (all(c['label_error'] < 5e-4 for c in arm['controls'])
                         and arm['edge']['stokes_abs_error']/abs(edge) < 1e-5)
        summary = grid_summary(arm['lines'], controls_pass)
        if (controls_pass != arm['controls_pass'] or summary != arm['surface_summary']
                or all(row['numerically_qualified'] for row in summary)
                != arm['all_points_numerically_qualified']):
            raise ValueError('grid qualification arithmetic mismatch')
        summaries.append(dict(target=target, qualified=sum(line['passed'] for line in arm['lines']),
                               surface_summary=summary))
        print(target+' replayed', flush=True)
    if time.monotonic() >= deadline:
        raise TimeoutError('900 s replay budget reached')
    print(json.dumps(dict(manifest_files=len(entries), line_integrals_recomputed=checked,
                          maximum_recorded_label_disagreement=maximum,
                          final_prefix_errors_not_numerically_replayed=skipped, arms=summaries,
                          elapsed_s=time.monotonic()-started,
                          scope='final-prefix and control A flux; other saved arithmetic only')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha', required=True)
    main(parser.parse_args().manifest_sha)
