"""Frozen ideal-target action domain for joint feasibility; no actual-coil endpoint."""
import io
from pathlib import Path

import numpy as np

from fusion_baselines import coil_bounce as bounce
from fusion_baselines import coil_check as check
from fusion_baselines import joint_equilibrium as solver
from fusion_baselines import joint_target as target
from fusion_baselines.vmec_trace import trace_geometry

GRIDS = {'training': (801, 16, 0.), 'holdout': (1601, 32, np.pi/32),
         'holdout-refined': (3201, 32, np.pi/32)}


def score_reference(wout, mode, record):
    """Fixed original archive, with independent numerical intake charged to the caller."""
    record.guard()
    source = check.ROOT/check.TARGET
    _, _, sources, numerical = target.intake(source, wout, 'control', check.FIXED[check.WOUT],
                                            record.guard)
    identity = dict(target_id='reference401', input_sha256=numerical['input_sha256'],
                    wout_sha256=numerical['wout_sha256'], source_kind='frozen reference archive')
    return _score(wout, mode, record, sources, identity)


def score_proposal(folder, parent, mode, record):
    """New proposal accepted only through the trusted solver parent's receipt."""
    record.guard()
    _, _, sources, numerical = solver.intake_result(folder, parent, record.guard)
    check.need(numerical['solver_provenance_verified'] and numerical['numerical_consistency_pass'],
               'verified solver intake required')
    check.need(parent['proposal'] in ('plus', 'minus'), 'registered nonzero proposal required')
    for path, sha in parent['sources_before'].items():
        check.bind(path, sha, sources)
    for name, key in (('parent.json', 'record_sha256'), ('solver.json', 'solver_report_sha256'),
                      ('request.json', 'request_sha256')):
        check.bind(Path(folder)/name, parent[key], sources)
    identity = dict(target_id=numerical['target_id'], input_sha256=numerical['input_sha256'],
                    wout_sha256=numerical['wout_sha256'], parent_sha256=numerical['parent_sha256'],
                    source_kind='trusted solver receipt')
    return _score(Path(folder)/'wout.nc', mode, record, sources, identity)


def _score(wout, mode, record, sources, identity):
    check.need(mode in GRIDS, 'registered training or holdout grid required')
    check.need(not (record.output/'action-attempt.json').exists(),
               'fresh action-score cell required')
    check.bind(check.ROOT/target.PROTOCOL, target.PROTOCOL_SHA, sources)
    check.bind(wout, identity['wout_sha256'], sources)
    for path in sorted((check.ROOT/'src/fusion_baselines').glob('*.py')):
        check.bind(path, check.digest(path), sources)
    nphi, nalpha, offset = GRIDS[mode]
    report = dict(completed=False, mode=mode, identity=identity, score=None, eligible=False,
        settings=dict(nphi=nphi, nalpha=nalpha, alpha_offset=offset, periods=2,
                      surfaces=list(bounce.SURFACES), pitches=list(bounce.HOLD_PITCHES)),
        surfaces=[], sources_before=dict(sources), physical_admission=False,
        actual_coil_endpoint=None, full_joint_execution_enabled=False)
    record.save('action-attempt.json', report)
    for surface in bounce.SURFACES:
        record.guard()
        trace = trace_geometry(wout, surface, nphi, nalpha, 2, alpha_offset=offset)
        record.guard()
        check.need(np.shape(trace['B']) == np.shape(trace['length']) == (nphi, nalpha)
                   and np.array_equal(trace['alpha'],
                       np.linspace(0, 2*np.pi, nalpha, endpoint=False)+offset)
                   and np.array_equal(trace['phi'], np.linspace(0, 2*np.pi, nphi)),
                   'complete registered ideal phase grid required')
        buffer = io.BytesIO()
        np.savez_compressed(buffer, **trace)
        name = f'ideal-s{surface}.npz'
        record.save(name, buffer.getvalue())
        row = dict(s=surface, arrays_sha256=check.digest(record.output/name), cells=[], errors=[])
        report['surfaces'].append(row)
        for q in bounce.HOLD_PITCHES:
            record.guard()
            try:
                row['cells'].append(dict(q=q, **bounce.period_actions(trace, q)))
            except bounce.IncompleteActionDomain as exc:
                # Retain every line's wells, not merely the first failing alpha.
                wells = []
                for index, alpha in enumerate(trace['alpha']):
                    record.guard()
                    wells.append(dict(alpha=float(alpha), wells=[w.record() for w in
                        bounce.bounce_wells(trace['length'][:, index], trace['B'][:, index],
                                           bounce.bounce_field(q))]))
                row['errors'].append(dict(q=q, error=str(exc), wells_by_alpha=wells))
            record.guard()
        record.save('action-progress.json', report)
    record.guard()
    report['eligible'] = all(not r['errors'] and len(r['cells']) == 7 for r in report['surfaces'])
    if report['eligible']:
        values = [c['score'] for row in report['surfaces'] for c in row['cells']]
        check.need(len(values) == 35 and np.isfinite(values).all() and min(values) >= 0,
                   'complete finite nonnegative full-domain score required')
        report['score'] = float(np.mean(values))
    solver.check_sources(sources)
    record.guard()
    report.update(completed=True, sources_after={path: check.digest(path) for path in sources})
    check.need(report['sources_before'] == report['sources_after'], 'action source changed')
    record.guard()
    record.save('action-score.json', report)
    record.guard()
    return report


def holdout_agreement(coarse, refined):
    """Only the fixed same-target validation pair; no claim of physical benefit."""
    check.need(coarse['mode'] == 'holdout' and refined['mode'] == 'holdout-refined'
               and coarse['identity'] == refined['identity'], 'same-target holdout pair required')
    for row in (coarse, refined):
        check.need(row['completed'] and row['eligible'] and row['score'] is not None
                   and np.isfinite(row['score']) and row['score'] >= 0,
                   'complete eligible holdout scores required')
    first, second = coarse['score'], refined['score']
    difference = abs(first-second)
    scale = max(abs(first), abs(second), 1e-12)
    return dict(absolute_change=difference, relative_change=difference/scale,
                tolerance=.001, passed=difference <= .001*scale, physical_admission=False)
