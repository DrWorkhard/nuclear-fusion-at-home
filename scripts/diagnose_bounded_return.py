"""Trust-region local periodic-point search with unchanged physical verification."""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))

import diagnose_axis_center as axis  # noqa: E402
from diagnose_periodic_return import classify, difference_matrix  # noqa: E402

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402

MANIFEST = 'a6e1708bbb3996752d331cb61485cefc656d40d59948deadabda6f9488ed39f7'


def solve_return(mapping, seed, guard, progress=lambda rows: None):
    seed = np.asarray(seed)
    scale, h = .01, 5e-6
    trials = []

    def physical_residual(point, role):
        guard()
        trial = dict(point=np.asarray(point).tolist(), role=role, status='attempted')
        trials.append(trial)
        progress(trials)
        check.need(np.isfinite(point).all() and np.linalg.norm(point-seed) <= scale,
                   'trial left the 1 cm seed neighborhood')
        delta = mapping(point)-point
        check.need(np.isfinite(delta).all(), 'finite return residual required')
        trial.update(residual=delta.tolist(), status='completed')
        progress(trials)
        return delta

    def residual(u):
        return physical_residual(seed+scale*u, 'search')/scale

    def jacobian(u):
        point = seed+scale*u
        columns = []
        for direction in np.eye(2):
            plus = physical_residual(point+h*direction, 'derivative_plus')
            minus = physical_residual(point-h*direction, 'derivative_minus')
            columns.append((plus-minus)/(2*h))
        return np.column_stack(columns)

    solved = least_squares(residual, np.zeros(2), jac=jacobian, bounds=(-1., 1.),
                           method='trf', tr_solver='exact', x_scale=1., loss='linear',
                           ftol=1e-11, xtol=1e-11, gtol=1e-12)
    point = seed+scale*solved.x
    delta = physical_residual(point, 'final_verification')
    return dict(point=point.tolist(), residual_m=float(np.linalg.norm(delta)),
                solver_success=bool(solved.success), solver_status=int(solved.status),
                message=str(solved.message), nfev=int(solved.nfev), njev=int(solved.njev),
                optimality=float(solved.optimality), cost=float(solved.cost),
                trials=trials)



def run(archive, output, revision):
    from simsopt.field import BiotSavart

    started = time.monotonic()
    record = fit.Recorder(output, started+300)
    report = dict(completed=False, provenance=build_run_record(ROOT), resolutions=[],
                  physical_admission=False, contour_qualification=False,
                  island_boundary_established=False, original_qualification_unchanged=True)
    try:
        repo = report['provenance']['repository']
        check.need(repo['commit'] == revision and not repo['dirty'], 'clean producer required')
        sources = {}
        for path in [Path(__file__), ROOT/'scripts/diagnose_axis_center.py',
                     ROOT/'scripts/diagnose_saved_recurrence.py',
                     ROOT/'scripts/diagnose_periodic_return.py',
                     ROOT/'docs/optimization/ISSUE48_BOUNDED_RETURN.md',
                     *sorted((ROOT/'src/fusion_baselines').glob('*.py'))]:
            check.bind(path, check.digest(path), sources)
        check.bind(archive/'manifest.json', MANIFEST, sources)
        manifest = check.read_json(archive/'manifest.json')
        names = ('inputs/inputs/continuation-snapshot.json', 'raw/run/line-10.npz',
                 'raw/run/result.json')
        for name in names:
            check.bind(archive/name, manifest[name], sources)
        previous = check.read_json(archive/'raw/run/result.json')
        check.need(previous['completed'] and previous['both_comparisons_pass'],
                   'qualified numerical-comparison inputs required')
        with np.load(archive/'raw/run/line-10.npz', allow_pickle=False) as data:
            points = data['rz'][data['planes'] == 0]
        check.need(points.shape == (320, 2), '320 phi=0 crossings required')
        seed = np.mean(points[::11], axis=0)
        report.update(seed_RZ=seed.tolist(), seed_count=len(points[::11]),
                      seed_rule='mean of first residue sequence in refined phi=0 crossings',
                      sources_before=dict(sources))
        record.save('start.json', report)
        snapshot = check.read_json(archive/names[0])
        for nodes, rtol, atol in ((512, 1e-10, 1e-12), (1024, 1e-11, 1e-13)):
            coils, own, mapping_checks = check.native_coils(snapshot, nodes)
            field = BiotSavart(coils)

            def orbit(point, field=field, rtol=rtol, atol=atol):
                path = [np.asarray(point).copy()]
                for _ in range(11):
                    values, _ = axis.period_map(field, path[-1], record.guard, rtol, atol)
                    path.append(values[-1])
                return np.asarray(path)

            def mapping(point, orbit=orbit):
                check.need(np.isfinite(point).all() and np.linalg.norm(point-seed) <= .01,
                           'map start left the 1 cm seed neighborhood')
                return orbit(point)[-1]

            def progress(trials, nodes=nodes):
                record.save(f'root-{nodes}-attempt.json', dict(nodes=nodes, trials=trials))

            result = solve_return(mapping, seed, record.guard, progress)
            record.save(f'solver-{nodes}.json', result)
            check.need(result['solver_success'] and result['residual_m'] <= 1e-9,
                       'eleven-period root not numerically resolved')
            point = np.asarray(result['point'])
            path = orbit(point)
            one_period_distance = float(np.linalg.norm(path[1]-point))
            check.need(one_period_distance > 1e-3, 'one-period fixed point is not the sought orbit')
            matrices = [difference_matrix(mapping, point, h) for h in (1e-5, 5e-6)]
            phi = np.arange(12)*np.pi
            xyz = np.column_stack((path[:, 0]*np.cos(phi), path[:, 0]*np.sin(phi), path[:, 1]))
            field.set_points(xyz)
            native = field.B().copy()
            independent, _ = check.independent.filament_field_and_potential(
                xyz, own['positions'], own['tangents'], own['currents'])
            error = check.error(native, independent)
            check.need(error <= 1e-12, 'sampled independent-field disagreement')
            result.update(nodes=nodes, rtol=rtol, atol=atol,
                          one_period_distance_m=one_period_distance,
                          orbit_RZ=path.tolist(), matrices=matrices, mapping_checks=mapping_checks,
                          sampled_independent_field_error=error)
            report['resolutions'].append(result)
            record.save('progress.json', report)
        rows = report['resolutions']
        difference = float(np.linalg.norm(np.asarray(rows[0]['point'])-rows[1]['point']))
        report['point_refinement_difference_m'] = difference
        report['point_refinement_pass'] = difference <= 1e-7
        report['linear_diagnosis'] = classify([m for row in rows for m in row['matrices']])
        if not report['point_refinement_pass']:
            report['linear_diagnosis']['classification'] = 'unresolved'
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
