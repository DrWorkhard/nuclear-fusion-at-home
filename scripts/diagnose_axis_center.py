"""One bounded periodic-axis estimate; existing saved-label verdicts stay fixed."""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import root

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))

import diagnose_saved_recurrence as saved  # noqa: E402

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402

SNAPSHOTS = {'continuation': 'inputs/continuation-snapshot.json',
             'reference401': 'reference401-snapshot.json'}


def period_map(field, start, guard, rtol=1e-10, atol=1e-12):
    """Direct R,Z field-line map from phi=0 to pi (one nfp=2 period)."""
    def rhs(phi, rz):
        guard()
        check.need(np.isfinite(rz).all() and rz[0] > 0, 'finite positive R required')
        c, s = np.cos(phi), np.sin(phi)
        field.set_points(np.array([[rz[0]*c, rz[0]*s, rz[1]]]))
        b = field.B()[0].copy()
        guard()
        radial, toroidal = b[0]*c+b[1]*s, -b[0]*s+b[1]*c
        check.need(np.isfinite(b).all() and abs(toroidal) > 1e-6*np.linalg.norm(b),
                   'nondegenerate toroidal field required')
        return np.array([rz[0]*radial/toroidal, rz[0]*b[2]/toroidal])

    solution = solve_ivp(rhs, (0., np.pi), start, method='DOP853', rtol=rtol,
                         atol=atol, max_step=np.pi/100, t_eval=np.linspace(0., np.pi, 9))
    guard()
    check.need(solution.success and solution.y.shape == (2, 9), 'complete period required')
    return solution.y.T, int(solution.nfev)


def axis_estimate(field, center, guard, rtol, atol, progress=lambda row: None):
    center = np.asarray(center, dtype=float)
    evaluations = []

    def residual(point):
        guard()
        trial = dict(point=np.asarray(point).tolist(), status='attempted')
        evaluations.append(trial)
        progress(evaluations)
        check.need(np.linalg.norm(point-center) <= .02, 'root left 2 cm local neighborhood')
        orbit, nfev = period_map(field, point, guard, rtol, atol)
        delta = orbit[-1]-point
        trial.update(residual=delta.tolist(), field_evaluations=nfev, status='completed')
        progress(evaluations)
        return delta

    solved = root(residual, center, method='hybr', options={'xtol': 1e-9})
    last = residual(solved.x)
    check.need(solved.success and np.linalg.norm(last) <= 1e-9,
               'periodic root not numerically resolved')
    orbit, nfev = period_map(field, solved.x, guard, rtol, atol)
    return dict(center_RZ=solved.x.tolist(), displacement_m=float(np.linalg.norm(solved.x-center)),
                residual_m=float(np.linalg.norm(last)), solver_message=str(solved.message),
                iterations=evaluations, orbit_RZ=orbit.tolist(), final_field_evaluations=nfev)


def run(archive, reference_archive, output, revision):
    from simsopt.field import BiotSavart

    started = time.monotonic()
    record = fit.Recorder(output, started+240)
    archives = {'continuation': archive, 'reference401': reference_archive}
    report = dict(completed=False, provenance=build_run_record(ROOT), axes={}, cases=[],
                  physical_admission=False, original_qualification_unchanged=True,
                  axis_scope='local periodic fixed-point estimate; uniqueness/stability unproved')
    try:
        repo = report['provenance']['repository']
        check.need(repo['commit'] == revision and not repo['dirty'], 'clean producer required')
        sources, originals, centers = {}, {}, {}
        for source in [Path(__file__), ROOT/'scripts/diagnose_saved_recurrence.py',
                       ROOT/'docs/optimization/ISSUE48_AXIS_CENTER.md',
                       *sorted((ROOT/'src/fusion_baselines').glob('*.py'))]:
            check.bind(source, check.digest(source), sources)
        for target, path in archives.items():
            check.bind(path/'manifest.json', saved.MANIFESTS[target], sources)
            manifest = check.read_json(path/'manifest.json')
            names = [SNAPSHOTS[target], f'{saved.RUNS[target]}/result.json',
                     *[f'{saved.RUNS[target]}/line-{i}.npz'
                       for t, i in saved.CASES if t == target]]
            for name in names:
                check.bind(path/name, manifest[name], sources)
            original = check.read_json(path/saved.RUNS[target]/'result.json')
            check.need(original['completed'] and original['deadline_met'],
                       'complete source required')
            originals[target] = original
        report['sources_before'] = dict(sources)
        record.save('start.json', report)
        for target, path in archives.items():
            center = np.asarray(originals[target]['center_RZ'])
            snapshot = check.read_json(path/SNAPSHOTS[target])
            rows = []
            for nodes, rtol, atol in ((512, 1e-10, 1e-12), (1024, 1e-11, 1e-13)):
                record.guard()
                coils, own, mapping = check.native_coils(snapshot, nodes)
                field = BiotSavart(coils)
                def progress(evaluations, target=target, nodes=nodes):
                    record.save(f'axis-{target}-{nodes}-attempt.json',
                                dict(target=target, nodes=nodes, iterations=evaluations))

                row = axis_estimate(field, center, record.guard, rtol, atol, progress)
                phi = np.linspace(0., np.pi, 9)
                rz = np.asarray(row['orbit_RZ'])
                xyz = np.column_stack((rz[:, 0]*np.cos(phi), rz[:, 0]*np.sin(phi), rz[:, 1]))
                field.set_points(xyz)
                native = field.B().copy()
                independent, _ = check.independent.filament_field_and_potential(
                    xyz, own['positions'], own['tangents'], own['currents'])
                error = check.error(native, independent)
                check.need(error <= 1e-12, 'independent sampled field disagreement')
                row.update(nodes=nodes, rtol=rtol, atol=atol, mapping=mapping,
                           sampled_independent_field_error=error)
                rows.append(row)
                report['axes'][target] = rows
                record.save('progress.json', report)
            difference = float(np.linalg.norm(
                np.asarray(rows[0]['center_RZ'])-rows[1]['center_RZ']))
            check.need(difference <= 1e-7, 'axis estimates do not agree to 0.1 micrometre')
            centers[target] = np.asarray(rows[-1]['center_RZ'])
        for target, index in saved.CASES:
            record.guard()
            original = originals[target]
            with np.load(archives[target]/saved.RUNS[target]/f'line-{index}.npz',
                         allow_pickle=False) as data:
                hits = data['hits'].copy()
            hits = hits[(hits[:, 1] >= 0) & (hits[:, 0] > 1e-8)]
            hits = hits[np.argsort(hits[:, 0], kind='stable')][:640]
            check.need(len(hits) == 640, 'complete frozen crossings required')
            rz = np.column_stack((np.hypot(hits[:, 2], hits[:, 3]), hits[:, 4]))
            row = dict(target=target, index=index,
                       original_qualified=original['lines'][index]['passed'], centers={})
            for name, center in (('target', original['center_RZ']), ('periodic', centers[target])):
                planes = []
                for plane in (0, 1):
                    points = rz[hits[:, 1] == plane]
                    check.need(len(points) == 320, 'complete plane crossings required')
                    planes.append(dict(plane=plane, **saved.recurrence(points, center)))
                row['centers'][name] = dict(center_RZ=np.asarray(center).tolist(), planes=planes,
                                            pooled_gap_rad=saved.gap(rz, center))
            report['cases'].append(row)
            record.save('progress.json', report)
        report['sources_after'] = {p: check.digest(p) for p in sources}
        check.need(sources == report['sources_after'], 'source/input changed')
        record.guard()
        report['completed'] = True
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    record.finish(report, started)
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'reference-archive', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.archive.resolve(), args.reference_archive.resolve(),
                         args.output.resolve(), args.revision))
