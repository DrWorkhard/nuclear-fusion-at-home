"""Independent integrator check of two frozen continuation launches; no new labels."""
import argparse
import io
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))

import diagnose_axis_center as axis  # noqa: E402
import diagnose_saved_recurrence as saved  # noqa: E402

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402

CASES = (10, 8)  # Known failure first, qualifying same-field control second.


def saved_crossings(hits):
    hits = np.asarray(hits)
    hits = hits[(hits[:, 1] >= 0) & (hits[:, 0] > 1e-8)]
    hits = hits[np.argsort(hits[:, 0], kind='stable')][:640]
    check.need(len(hits) == 640, '640 saved crossings required')
    planes = np.arange(1, 641) % 2
    check.need(np.array_equal(hits[:, 1], planes), 'expected chronological pi/0 planes')
    return np.column_stack((np.hypot(hits[:, 2], hits[:, 3]), hits[:, 4])), planes


def run(archive, output, revision):
    from simsopt.field import BiotSavart

    started = time.monotonic()
    record = fit.Recorder(output, started+600)
    report = dict(completed=False, provenance=build_run_record(ROOT), cases=[],
                  physical_admission=False, original_qualification_unchanged=True,
                  method='1024-node native B; SciPy DOP853 one-period maps, rtol1e-11/atol1e-13')
    try:
        repo = report['provenance']['repository']
        check.need(repo['commit'] == revision and not repo['dirty'], 'clean producer required')
        sources = {}
        for path in [Path(__file__), ROOT/'scripts/diagnose_axis_center.py',
                     ROOT/'scripts/diagnose_saved_recurrence.py',
                     ROOT/'docs/optimization/ISSUE48_TRACE_REFINEMENT.md',
                     *sorted((ROOT/'src/fusion_baselines').glob('*.py'))]:
            check.bind(path, check.digest(path), sources)
        check.bind(archive/'manifest.json', saved.MANIFESTS['continuation'], sources)
        manifest = check.read_json(archive/'manifest.json')
        for name in ['inputs/continuation-snapshot.json', 'raw/run/result.json',
                     *[f'raw/run/line-{index}.npz' for index in CASES]]:
            check.bind(archive/name, manifest[name], sources)
        original = check.read_json(archive/'raw/run/result.json')
        check.need(original['completed'] and original['deadline_met'], 'complete source required')
        report['sources_before'] = dict(sources)
        record.save('start.json', report)
        snapshot = check.read_json(archive/'inputs/continuation-snapshot.json')
        coils, own, mapping = check.native_coils(snapshot, 1024)
        field = BiotSavart(coils)
        report['mapping'] = mapping
        center = np.asarray(original['center_RZ'])
        for index in CASES:
            line = original['lines'][index]
            check.need(line['index'] == index and line['s'] == .5, 'frozen mid-radius case')
            with np.load(archive/f'raw/run/line-{index}.npz', allow_pickle=False) as data:
                old, planes = saved_crossings(data['hits'])
                path = data['path']
                check.need(path[0, 2] == 0 and path[1, 2] > 0, 'positive initial phi required')
            start = np.asarray(line['actual_start_RZ'])
            check.need(np.max(abs(start-path[0, [1, 3]])) < 1e-15, 'exact saved launch required')
            points, counts = [], []
            record.save(f'line-{index}-attempt.json', dict(index=index, start_RZ=start.tolist()))
            for period in range(640):
                orbit, count = axis.period_map(field, start, record.guard, 1e-11, 1e-13)
                start = orbit[-1].copy()
                points.append(start)
                counts.append(count)
                if (period+1) % 40 == 0:
                    buffer = io.BytesIO()
                    np.savez_compressed(buffer, rz=np.asarray(points), planes=planes[:period+1],
                                        field_evaluations=np.asarray(counts))
                    record.save(f'line-{index}.npz', buffer.getvalue())
            new = np.asarray(points)
            selected = np.array([0, 79, 159, 319, 639])
            phi = np.pi*planes[selected]
            rz = new[selected]
            xyz = np.column_stack((rz[:, 0]*np.cos(phi), rz[:, 0]*np.sin(phi), rz[:, 1]))
            field.set_points(xyz)
            native = field.B().copy()
            independent, _ = check.independent.filament_field_and_potential(
                xyz, own['positions'], own['tangents'], own['currents'])
            error = check.error(native, independent)
            check.need(error <= 1e-12, 'independent sampled field mismatch')
            delta = np.linalg.norm(new-old, axis=1)
            row = dict(index=index, original_qualified=line['passed'], crossings=len(new),
                       maximum_crossing_difference_m=float(np.max(delta)),
                       rms_crossing_difference_m=float(np.sqrt(np.mean(delta**2))),
                       sampled_independent_field_error=error, geometry={})
            for label, rz in (('original', old), ('refined', new)):
                row['geometry'][label] = dict(pooled_gap_rad=saved.gap(rz, center), planes=[
                    dict(plane=plane, **saved.recurrence(rz[planes == plane], center))
                    for plane in (0, 1)])
            old_reversals = [[g['resolved_direction_changes'] for g in p['residue_classes']]
                             for p in row['geometry']['original']['planes']]
            new_reversals = [[g['resolved_direction_changes'] for g in p['residue_classes']]
                             for p in row['geometry']['refined']['planes']]
            row['comparison_pass'] = bool(np.max(delta) <= 1e-5
                and old_reversals == new_reversals and abs(row['geometry']['original'][
                    'pooled_gap_rad']-row['geometry']['refined']['pooled_gap_rad']) <= .01)
            report['cases'].append(row)
            record.save('progress.json', report)
        report['both_comparisons_pass'] = all(row['comparison_pass'] for row in report['cases'])
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
    for name in ('archive', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.archive.resolve(), args.output.resolve(), args.revision))
