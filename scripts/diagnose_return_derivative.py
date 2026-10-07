"""Check the rejected local Newton proposal with explicit finite-difference scales."""
import argparse
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))

import diagnose_axis_center as axis  # noqa: E402
import diagnose_periodic_return as periodic  # noqa: E402

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402

FAILURE_MANIFEST = '5e9c1568ad730dddb307fc20d977b39568b5054e54edb32b66da2e7a16fdc76e'


def proposal(matrix, residual):
    jacobian = np.asarray(matrix)-np.eye(2)
    step = np.linalg.solve(jacobian, -np.asarray(residual))
    check.need(np.isfinite(step).all(), 'finite proposed Newton step required')
    return dict(residual_jacobian=jacobian.tolist(), singular_values=np.linalg.svd(
        jacobian, compute_uv=False).tolist(), condition_number=float(np.linalg.cond(jacobian)),
        step_m=step.tolist(), step_norm_m=float(np.linalg.norm(step)))


def decision(rows):
    steps = np.array([row['proposal']['step_m'] for row in rows])
    spread = float(np.max(np.linalg.norm(steps[:, None]-steps[None, :], axis=-1)))
    norms = np.linalg.norm(steps, axis=1)
    name = 'unresolved'
    if spread <= 1e-3:
        if np.all(norms > .011):
            name = 'refined proposals still leave the frozen neighborhood'
        elif np.all(norms < .009):
            name = 'refined proposals stay inside the frozen neighborhood'
    return dict(result=name, maximum_proposal_spread_m=spread)


def run(archive, failure_archive, output, revision):
    from simsopt.field import BiotSavart

    started = time.monotonic()
    record = fit.Recorder(output, started+180)
    report = dict(completed=False, provenance=build_run_record(ROOT), rows=[],
                  physical_admission=False, root_search_performed=False,
                  original_qualification_unchanged=True)
    try:
        repo = report['provenance']['repository']
        check.need(repo['commit'] == revision and not repo['dirty'], 'clean producer required')
        sources = {}
        for path in [Path(__file__), ROOT/'scripts/diagnose_axis_center.py',
                     ROOT/'scripts/diagnose_saved_recurrence.py',
                     ROOT/'scripts/diagnose_periodic_return.py',
                     ROOT/'docs/optimization/ISSUE48_RETURN_DERIVATIVE.md',
                     *sorted((ROOT/'src/fusion_baselines').glob('*.py'))]:
            check.bind(path, check.digest(path), sources)
        for base, sha, names in ((archive, periodic.MANIFEST,
                ('inputs/inputs/continuation-snapshot.json',)),
                (failure_archive, FAILURE_MANIFEST,
                 ('raw/run/result.json', 'raw/run/root-512-attempt.json'))):
            check.bind(base/'manifest.json', sha, sources)
            manifest = check.read_json(base/'manifest.json')
            for name in names:
                check.bind(base/name, manifest[name], sources)
        failed = check.read_json(failure_archive/'raw/run/result.json')
        trials = check.read_json(failure_archive/'raw/run/root-512-attempt.json')['trials']
        check.need(not failed['completed'] and len(trials) == 6, 'exact failed attempt required')
        seed = np.asarray(failed['seed_RZ'])
        baseline_residual = np.asarray(trials[0]['residual'])
        baseline_jacobian = np.column_stack([
            (np.asarray(trials[k]['residual'])-baseline_residual)/(trials[k]['point'][j]-seed[j])
            for j, k in enumerate((3, 4))])
        report.update(seed_RZ=seed.tolist(), baseline=proposal(
            baseline_jacobian+np.eye(2), baseline_residual), sources_before=dict(sources))
        record.save('start.json', report)
        snapshot = check.read_json(archive/'inputs/inputs/continuation-snapshot.json')
        for nodes, rtol, atol in ((512, 1e-10, 1e-12), (1024, 1e-11, 1e-13)):
            coils, _, mapping_checks = check.native_coils(snapshot, nodes)
            field = BiotSavart(coils)

            def mapping(point, field=field, rtol=rtol, atol=atol):
                point = np.asarray(point).copy()
                for _ in range(11):
                    values, _ = axis.period_map(field, point, record.guard, rtol, atol)
                    point = values[-1]
                return point

            final = mapping(seed)
            residual = final-seed
            record.save(f'center-{nodes}.json', dict(seed=seed.tolist(), final=final.tolist(),
                                                   residual=residual.tolist()))
            for h in (1e-5, 5e-6):
                matrix = periodic.difference_matrix(mapping, seed, h)
                row = dict(nodes=nodes, rtol=rtol, atol=atol, mapping_checks=mapping_checks,
                           residual=residual.tolist(), derivative=matrix,
                           proposal=proposal(matrix['matrix'], residual))
                report['rows'].append(row)
                record.save('progress.json', report)
        report['decision'] = decision(report['rows'])
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
    for name in ('archive', 'failure-archive', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.archive.resolve(), args.failure_archive.resolve(),
                         args.output.resolve(), args.revision))
