"""Transfer the interval estimator to all fixed round-2 contours; no retracing."""

import argparse
import io
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))

from diagnose_flux_quadrature import MANIFEST_SHA256, controls  # noqa: E402

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines import flux_labels as labels  # noqa: E402
from fusion_baselines.coupled_coil_audit import (  # noqa: E402
    filament_field_and_potential,
    physical_curves,
)
from fusion_baselines.provenance import build_run_record  # noqa: E402
from fusion_baselines.realized_field import Target  # noqa: E402


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


def run(archive, native_inputs, output):
    from simsopt.field import BiotSavart

    check.need(all(os.environ.get(k) == '1' for k in (
        'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS',
        'MKL_NUM_THREADS')), 'one-thread execution required')
    check.need(fit.shutil.disk_usage(output.parent).free >= fit.START_RESERVE,
               '3 GiB initial reserve required')
    started = time.monotonic()
    record = fit.Recorder(output, started+600)
    report = dict(kind='interval-estimator-transfer', completed=False, arms=[],
                  provenance=build_run_record(ROOT), original_matching_verdict='inconclusive',
                  physical_admission=False, equal_alpha_verified=False, nestedness_proven=False)
    try:
        sources = {}
        check.bind(archive/'manifest.json', MANIFEST_SHA256, sources)
        manifest = check.read_json(archive/'manifest.json')
        for source in [Path(__file__), ROOT/'scripts/diagnose_flux_quadrature.py',
                       ROOT/'docs/optimization/ISSUE48_ESTIMATOR_TRANSFER.md',
                       *sorted((ROOT/'src/fusion_baselines').glob('*.py'))]:
            check.bind(source, check.digest(source), sources)
        for target in ('reference401', 'selected401'):
            names = [f'{target}-snapshot.json', f'round2/{target}/result.json',
                     f'round2-quadrature/{target}/result.json']
            names += [f'round2/{target}/line-{i}.npz' for i in range(5)]
            for name in names:
                check.bind(archive/name, manifest[name], sources)
            spec = check.target_spec(target)
            check.bind(native_inputs/spec['input'], spec['input_sha256'], sources)
            wout = (check.WOUT if target == 'reference401' else
                    'artifacts/plasma-balanced-v1/endpoints/selected-fine/native/wout.nc')
            check.bind(native_inputs/wout, spec['wout_sha256'], sources)
        report['sources_before'] = dict(sources)
        report['controls'] = controls(record.guard)
        check.need(all(r['passed'] for r in report['controls']), 'analytic controls failed')
        record.save('inputs.json', report)
        for target_id in ('reference401', 'selected401'):
            original = check.read_json(archive/f'round2-quadrature/{target_id}/result.json')
            trace = check.read_json(archive/f'round2/{target_id}/result.json')
            check.need(trace['completed'] and trace['deadline_met'] and len(trace['lines']) == 5
                       and trace['half_period_sections'],
                       'complete frozen five-line trace required')
            check.need(max(trace['half_period_symmetry'].values()) <= 1e-12,
                       'recorded half-period covariance required')
            snapshot = check.read_json(archive/f'{target_id}-snapshot.json')
            field = BiotSavart(check.native_coils(snapshot, 512, target_id)[0])
            center, edge = original['center_RZ'], original['edge']['line_flux']
            spec = check.target_spec(target_id)
            wout = (check.WOUT if target_id == 'reference401' else
                    'artifacts/plasma-balanced-v1/endpoints/selected-fine/native/wout.nc')
            target = Target.from_wout(native_inputs/wout,
                                      check.read_json(native_inputs/spec['input']))
            check.need(np.max(abs(np.asarray(target.axis(0.))-center)) <= 1e-12,
                       'frozen polar center changed')
            arm = dict(target=target_id, edge_flux=edge, center_RZ=center, controls=[], lines=[])
            theta = np.linspace(0, 2*np.pi, 2048, endpoint=False)
            dense_edge = np.column_stack(target.rz(1., theta, np.zeros_like(theta)))
            control_arrays = dict(edge=dense_edge, center=np.asarray(center))
            spline, _ = labels.polar_contour(dense_edge, center)
            new_edge = labels.interval_flux_integrals(field, spline, center, guard=record.guard)
            arm['edge_recheck'] = dict(**new_edge,
                                       frozen_label_error=abs(new_edge['line_flux']/edge-1))
            for s in (.25, .75):
                dense = np.column_stack(target.rz(s, theta, np.zeros_like(theta)))
                spline, _ = labels.polar_contour(dense, center)
                exact = labels.interval_flux_integrals(field, spline, center, guard=record.guard)
                indices = np.sort(np.random.default_rng(4806).choice(2048, 160, replace=False))
                sampled = dense[indices]
                control_arrays[f's{s}'] = dense
                control_arrays['sample_indices'] = indices
                row = estimate(field, sampled, center, edge, record)
                row.update(s=s, dense_label=exact['line_flux']/edge,
                           label_error=abs(row['label']-exact['line_flux']/edge))
                arm['controls'].append(row)
            buffer = io.BytesIO()
            np.savez_compressed(buffer, **control_arrays)
            control_name = f'{target_id}-control-contours.npz'
            record.save(control_name, buffer.getvalue())
            arm['control_arrays_sha256'] = check.digest(output/control_name)
            for index in range(5):
                path = archive/f'round2/{target_id}/line-{index}.npz'
                with np.load(path, allow_pickle=False) as data:
                    hits = data['hits'].copy()
                hits = hits[(hits[:, 1] >= 0) & (hits[:, 0] > 1e-8)]
                hits = hits[np.argsort(hits[:, 0], kind='stable')]
                check.need(len(hits) >= 640, '640 crossings required')
                rz = np.column_stack((np.hypot(hits[:, 2], hits[:, 3]), hits[:, 4]))
                line = dict(index=index, s=trace['lines'][index]['s'],
                            theta=trace['lines'][index]['theta'],
                            transits=trace['lines'][index]['transits'], prefixes=[])
                for count in (160, 320, 640):
                    try:
                        row = estimate(field, rz[:count], center, edge, record)
                        independent = independent_label(snapshot, rz[:count], center, edge, record)
                        row.update(independent_label=independent,
                                   independent_label_error=abs(row['label']-independent))
                        line['prefixes'].append(row)
                    except ValueError as exc:
                        line['prefixes'].append(dict(crossings=count, error=str(exc)))
                line.update(qualified(line, edge))
                arm['lines'].append(line)
                record.save(f'{target_id}-progress.json', arm)
                print(f'{target_id} line {index}: {line["failures"]}', flush=True)
            arm['controls_pass'] = bool(all(c['label_error'] < 5e-4 for c in arm['controls'])
                and arm['edge_recheck']['frozen_label_error'] < 1e-5
                and arm['edge_recheck']['stokes_abs_error']/abs(edge) < 1e-5)
            arm['numerically_qualified'] = (arm['controls_pass']
                                            and all(row['passed'] for row in arm['lines']))
            report['arms'].append(arm)
            record.save('progress-transfer.json', report)
        report['sources_after'] = {p: check.digest(p) for p in sources}
        check.need(sources == report['sources_after'], 'sources changed')
        report['pair_numerically_qualified'] = all(
            arm['numerically_qualified'] for arm in report['arms'])
        record.guard()
        report['completed'] = True
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    record.finish(report, started)
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--native-inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.archive.resolve(), args.native_inputs.resolve(),
                         args.output.resolve()))
