"""Bounded saved-point diagnosis of the continuation coverage failure; no tracing."""
import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines import flux_labels as labels  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402

MANIFESTS = {
    'continuation': '09bfe306edc73524f0c1d1270424b70ec605969f9d61e0293e6732b392395316',
    'reference401': '4b39d87d53aaa47a4e1ccf599e3b45ffdd586693363689a914943d4bd54f0bb3',
}
RUNS = {'continuation': 'raw/run', 'reference401': 'reference401/run'}
CASES = (('continuation', 8), ('continuation', 9), ('continuation', 10),
         ('continuation', 11), ('reference401', 10))


def angles(rz, center):
    offset = np.asarray(rz)-center
    check.need(offset.ndim == 2 and offset.shape[1] == 2 and len(offset) >= 16
               and np.isfinite(offset).all() and np.min(np.linalg.norm(offset, axis=1)) > 1e-10,
               'finite noncentral R,Z points required')
    return np.arctan2(offset[:, 1], offset[:, 0])


def gap(rz, center):
    theta = np.sort(np.mod(angles(rz, center), 2*np.pi))
    return float(np.max(np.diff(np.r_[theta, theta[0]+2*np.pi])))


def recurrence(rz, center):
    theta = angles(rz, center)
    returns = {str(lag): float(np.sqrt(np.mean(np.sum((rz[lag:]-rz[:-lag])**2, axis=1))))
               for lag in (10, 11, 12)}
    groups = []
    for offset in range(11):
        series = np.unwrap(theta[offset::11])
        differences = np.diff(series)
        resolved = differences[abs(differences) > 1e-8]
        groups.append(dict(offset=offset, count=len(series),
            angular_span_rad=float(np.ptp(series)), net_advance_rad=float(series[-1]-series[0]),
            total_variation_rad=float(np.sum(abs(differences))),
            resolved_direction_changes=int(np.count_nonzero(resolved[1:]*resolved[:-1] < 0))))
    return dict(points=len(rz), return_rms_m=returns,
                prefix_gap_rad={str(n): gap(rz[:n], center) for n in (80, 160, 320)},
                last_160_gap_rad=gap(rz[-160:], center), residue_classes=groups)


def interpolation_check(rz, center):
    row = dict(crossings=len(rz), max_gap_rad=gap(rz, center), orders=[])
    try:
        spline, _ = labels.polar_contour(rz, center)
        for order in (4, 8):
            try:
                labels.interval_contour_points(spline, center, order)
                row['orders'].append(dict(order=order, valid_sampled_radius=True))
            except ValueError as exc:
                row['orders'].append(dict(order=order, error=str(exc)))
    except ValueError as exc:
        row['error'] = str(exc)
    return row


def controls():
    rows = []
    for name, rotation in (('rational_circle', -6/11),
                            ('near_rational_circle', -6/11+1e-5),
                            ('well_sampled_circle', (np.sqrt(5)-1)/2)):
        theta = 2*np.pi*rotation*np.arange(320)
        points = np.column_stack((1.+.2*np.cos(theta), .2*np.sin(theta)))
        row = recurrence(points, np.array([1., 0.]))
        row.update(name=name, rotation=rotation, known_geometry='exact circle')
        rows.append(row)
    check.need(abs(rows[0]['prefix_gap_rad']['320']-2*np.pi/11) < 1e-12
               and rows[0]['return_rms_m']['11'] < 1e-12
               and rows[1]['prefix_gap_rad']['320'] > .4
               and rows[2]['prefix_gap_rad']['320'] < .04, 'analytic controls failed')
    return rows


def run(archive, reference_archive, output, revision):
    started = time.monotonic()
    archives = {'continuation': archive, 'reference401': reference_archive}
    fit.MAX_BYTES = 255*1024**2
    check.need(all(os.environ.get(k) == '1' for k in (
        'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS',
        'MKL_NUM_THREADS')), 'one-thread execution required')
    check.need(fit.shutil.disk_usage(output.parent).free >= fit.START_RESERVE,
               '3 GiB initial reserve required')
    record = fit.Recorder(output, started+60)
    report = dict(completed=False, provenance=build_run_record(ROOT), cases=[],
                  physical_admission=False, dynamical_classification='not established')
    try:
        repo = report['provenance']['repository']
        check.need(repo['commit'] == revision and not repo['dirty'],
                   'clean reviewed source required')
        sources = {}
        manifests = {}
        for target, path in archives.items():
            check.bind(path/'manifest.json', MANIFESTS[target], sources)
            manifests[target] = check.read_json(path/'manifest.json')
        for target, index in CASES:
            for name in (f'{RUNS[target]}/result.json', f'{RUNS[target]}/line-{index}.npz'):
                check.bind(archives[target]/name, manifests[target][name], sources)
        for source in [Path(__file__), ROOT/'docs/optimization/ISSUE48_CONTINUATION_RECURRENCE.md',
                       *sorted((ROOT/'src/fusion_baselines').glob('*.py'))]:
            check.bind(source, check.digest(source), sources)
        report['sources_before'] = dict(sources)
        report['controls'] = controls()
        for target, index in CASES:
            record.guard()
            original = check.read_json(archives[target]/RUNS[target]/'result.json')
            check.need(original['completed'] and original['deadline_met'],
                       'complete trace required')
            line = original['lines'][index]
            check.need(line['index'] == index and line['s'] == .5,
                       'frozen mid-radius case required')
            center = np.asarray(original['center_RZ'])
            saved_line = archives[target]/RUNS[target]/f'line-{index}.npz'
            with np.load(saved_line, allow_pickle=False) as data:
                hits = data['hits'].copy()
            hits = hits[(hits[:, 1] >= 0) & (hits[:, 0] > 1e-8)]
            hits = hits[np.argsort(hits[:, 0], kind='stable')][:640]
            check.need(len(hits) == 640, '640 pooled crossings required')
            rz = np.column_stack((np.hypot(hits[:, 2], hits[:, 3]), hits[:, 4]))
            row = dict(target=target, index=index, theta=line['theta'],
                        original_qualified=line['passed'], original_iota=line['iota'],
                        pooled=[interpolation_check(rz[:n], center) for n in (160, 320, 640)],
                        planes=[])
            for plane in (0, 1):
                points = rz[hits[:, 1] == plane]
                check.need(len(points) == 320, '320 crossings on each plane required')
                row['planes'].append(dict(plane=plane, **recurrence(points, center)))
            report['cases'].append(row)
            record.save('progress.json', report)
        report['sources_after'] = {p: check.digest(p) for p in sources}
        check.need(sources == report['sources_after'], 'sources changed')
        record.guard()
        report['completed'] = True
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    record.finish(report, started)
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--reference-archive', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.archive.resolve(), args.reference_archive.resolve(),
                         args.output.resolve(), args.revision))
