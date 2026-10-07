"""Selection and decision rules for the trusted joint driver, never a candidate verifier.

The driver must establish source/receipt identity, completion and resource state
before calling these helpers. A report's own completion flag is insufficient.
"""
import copy
import hashlib
import json

import numpy as np

from fusion_baselines import coil_bounce as bounce
from fusion_baselines import coil_check as check
from fusion_baselines import joint_action as action
from fusion_baselines import joint_coil as coil
from fusion_baselines import joint_target as target
from fusion_baselines import realized_field as tracing


class IncompleteComparison(ValueError):
    """Required work or a usable paired measurement is missing."""


def require(condition, message):
    if not condition:
        raise IncompleteComparison(message)


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                    separators=(',', ':')).encode()).hexdigest()


def complete_score(row, mode):
    """Verify the complete registered domain, not a candidate-selected aggregate."""
    require(row['mode'] == mode and row['completed'] and row['eligible'],
            'complete eligible action domain required')
    nphi, nalpha, offset = action.GRIDS[mode]
    require(row['settings'] == dict(nphi=nphi, nalpha=nalpha, alpha_offset=offset, periods=2,
                                   surfaces=list(bounce.SURFACES),
                                   pitches=list(bounce.HOLD_PITCHES)), 'action settings changed')
    require([r['s'] for r in row['surfaces']] == list(bounce.SURFACES),
            'all registered action surfaces required')
    values = []
    for surface in row['surfaces']:
        require(not surface['errors'] and [c['q'] for c in surface['cells']]
                == list(bounce.HOLD_PITCHES), 'all registered action pitches required')
        for cell in surface['cells']:
            require(np.shape(cell['actions']) == (nalpha, 2), 'every phase and family required')
            require(cell['score'] == bounce.action_statistics(cell['actions'])['score'],
                    'cell score differs from actions')
        values.extend(c['score'] for c in surface['cells'])
    require(np.isfinite(values).all() and min(values) >= 0
            and row['score'] == float(np.mean(values)), 'action aggregate differs from cells')
    return row['score']


def fit_eligible(search, ordinary_cap):
    """A cap is normal only when independently established by the trusted driver."""
    if not search['startup_pass'] or search['selected'] is None:
        return False
    reason = search['status']['reason']
    if reason != 'solver-return' and not (reason == 'budget' and ordinary_cap is True):
        return False
    row = search['selected']
    metrics = row['metrics']
    return (row['status'] == 'completed' and row['role'] in ('startup-seed', 'search')
            and metrics['sampled_geometry_limits_met'] and metrics['current_limit_met']
            and len(metrics['lengths']) == 6 and np.isfinite(metrics['lengths']).all()
            and min(metrics['lengths']) > 0 and max(metrics['lengths']) <= 3.45
            and np.isfinite([row['value'], metrics['normal_rms']]).all()
            and row['value'] >= 0 and metrics['normal_rms'] >= 0)


def numerical_rejection(row):
    """Validate the parent's classified failure, including contradictory success evidence."""
    rejected = row['rejection']
    kind, evidence = rejected['kind'], rejected['evidence']
    require(kind in ('size', 'equilibrium', 'plasma-domain'),
            'classified numerical failure required')
    require(isinstance(evidence, dict) and evidence.get('proposal') == row['proposal']
            and evidence.get('input_sha256') == target.INPUT_HASHES[row['proposal']]
            and evidence.get('completed') is True
            and evidence.get('resource_interrupted') is False
            and row.get('search') is None, 'completed bound rejection before fitting required')
    result = evidence.get('result')
    require(isinstance(result, dict), 'structured failed check required')
    if kind == 'size':
        original = np.asarray(result.get('original_m3', []), dtype=float)
        proposed = np.asarray(result.get('proposal_m3', []), dtype=float)
        require(row.get('training') is None and result.get('grids') == [128, 256]
                and original.shape == proposed.shape == (2,)
                and np.isfinite([original, proposed]).all()
                and min(original) > 0 and min(proposed) > 0, 'complete size check required')
        require(all(abs(a[0]-a[1])/max(a) <= 1e-6 for a in (original, proposed)),
                'unresolved volume quadrature is not an explicit size rejection')
        require(np.max(np.abs(proposed/original-1)) > .001,
                'size evidence does not fail registered limit')
    elif kind == 'equilibrium':
        residuals = result.get('residuals', {})
        require(row.get('training') is None and result.get('completed') is True
                and result.get('converged') is False
                and set(residuals) == {'fsqr', 'fsqz', 'fsql'}
                and np.isfinite(list(residuals.values())).all()
                and min(residuals.values()) >= 0
                and type(result.get('ier_flag')) is int and type(result.get('ns')) is int,
                'documented completed nonconvergence required')
        require(result['ier_flag'] != 0 or result['ns'] != 401
                or max(residuals.values()) > 1e-12,
                'equilibrium evidence does not fail registered convergence')
    else:
        require(result == row.get('training') and result.get('completed') is True
                and result.get('eligible') is False and result.get('score') is None
                and result.get('mode') == 'training', 'completed ineligible plasma domain required')
        require(result['identity']['input_sha256'] == evidence['input_sha256']
                and result['identity']['target_id'] == f"issue37-joint-v1/{row['proposal']}",
                'plasma rejection belongs to another target')
        require(result['settings'] == dict(nphi=801, nalpha=16, alpha_offset=0., periods=2,
                    surfaces=list(bounce.SURFACES), pitches=list(bounce.HOLD_PITCHES))
                and [r['s'] for r in result['surfaces']] == list(bounce.SURFACES),
                'complete registered plasma rejection domain required')
        failures = []
        for surface in result['surfaces']:
            pitches = [r['q'] for r in surface['cells']+surface['errors']]
            require(sorted(pitches) == list(bounce.HOLD_PITCHES),
                    'all pitch successes and failures required')
            failures.extend(surface['errors'])
        require(bool(failures), 'plasma rejection has no failed cells')
        for failed in failures:
            require(failed['error'] in ('exactly two uncensored wells required on every line',
                    'well family crosses its registered field period')
                    and [r['alpha'] for r in failed['wells_by_alpha']]
                    == np.linspace(0, 2*np.pi, 16, endpoint=False).tolist(),
                    'typed domain failure with every phase required')
            missing = any(len(r['wells']) != 2 or any(not w['complete'] for w in r['wells'])
                          for r in failed['wells_by_alpha'])
            if failed['error'] == 'exactly two uncensored wells required on every line':
                require(missing, 'reported well-domain rejection has no missing/censored wells')
            else:
                crossings = []
                for line in failed['wells_by_alpha']:
                    angles = np.asarray(line.get('phi_bounds', []), dtype=float)
                    require(angles.shape == (len(line['wells']), 2)
                            and np.isfinite(angles).all(), 'saved angular well bounds required')
                    crossings.append(len(line['wells']) == 2 and any(
                        lo < p*np.pi-1e-12 or hi > (p+1)*np.pi+1e-12
                        for p, (lo, hi) in enumerate(angles)))
                require(any(crossings), 'reported period rejection has no crossing well')


def select_joint(proposals):
    """Both fixed proposals must terminate before training-only selection."""
    require([r['proposal'] for r in proposals] == ['plus', 'minus'],
            'both registered proposals in fixed order required')
    require(all(r['completed'] for r in proposals), 'unfinished joint proposal')
    candidates = []
    for index, row in enumerate(proposals):
        if row.get('rejection') is not None:
            numerical_rejection(row)
            continue
        score = complete_score(row['training'], 'training')
        identity = row['training']['identity']
        require(identity['target_id'] == f"issue37-joint-v1/{row['proposal']}"
                and identity['input_sha256'] == target.INPUT_HASHES[row['proposal']],
                'training score belongs to another proposal')
        if fit_eligible(row['search'], row['ordinary_fit_cap']):
            candidates.append((score, row['search']['selected']['value'], index))
    return None if not candidates else min(candidates)[2]


def snapshot_identity(proposal, identity, snapshot):
    """Keep the original control and admitted nonzero targets in their proper roles."""
    require(proposal in target.INPUT_HASHES
            and identity['input_sha256'] == target.INPUT_HASHES[proposal], 'wrong selected input')
    if proposal == 'control':
        require(identity['target_id'] == 'reference401'
                and identity['wout_sha256'] == check.FIXED[check.WOUT], 'original control required')
        check.snapshot_identity(snapshot)
        require(snapshot['order'] == 5, 'fixed order5 control required')
    else:
        coil.snapshot_identity(snapshot, {k: identity[k] for k in coil.BINDING_KEYS})


def freeze_selection(proposal, training, search, ordinary_cap, snapshot, input_path, wout, record):
    """Bind the chosen target, Wout, coils/current and index before any diagnostics."""
    record.guard()
    require(not (record.output/'frozen-selection.json').exists(), 'selection already frozen')
    complete_score(training, 'training')
    require(fit_eligible(search, ordinary_cap), 'eligible completed inner-fit candidate required')
    identity = copy.deepcopy(training['identity'])
    snapshot_identity(proposal, identity, snapshot)
    selected = search['selected']
    require(type(selected['index']) is int and selected['index'] >= 0,
            'nonnegative selected trial index required')
    require(np.array_equal(np.asarray(snapshot['base_coefficients']).ravel(), selected['x'])
            and snapshot['scale'] == selected['metrics']['scale']
            and snapshot['unit_flux'] == selected['metrics']['unit_flux'],
            'snapshot differs from selected fit coefficients or currents')
    sources = dict(training['sources_after'])
    check.bind(input_path, identity['input_sha256'], sources)
    check.bind(wout, identity['wout_sha256'], sources)
    coil.solver.check_sources(sources)
    frozen = dict(proposal=proposal, identity=identity, selected_index=selected['index'],
                  snapshot=copy.deepcopy(snapshot), training_score=training['score'],
                  inner_objective=selected['value'], sources=sources,
                  canonical_snapshot_sha256=canonical_sha(snapshot), physical_admission=False)
    frozen['selection_sha256'] = canonical_sha(frozen)
    record.guard()
    record.save('frozen-selection.json', frozen)
    record.guard()
    return frozen


def diagnostic_summary(frozen, report):
    """Use completed, bound diagnostics; recompute comparisons from reported metrics."""
    require(frozen['selection_sha256'] == canonical_sha(
        {k: v for k, v in frozen.items() if k != 'selection_sha256'}), 'changed frozen selection')
    snapshot_identity(frozen['proposal'], frozen['identity'], frozen['snapshot'])
    require(canonical_sha(frozen['snapshot']) == frozen['canonical_snapshot_sha256'],
            'changed frozen snapshot')
    require(report['completed'] and report['budget_complete']
            and report['selection_sha256'] == frozen['selection_sha256'],
            'completed diagnostics for frozen selection required')
    require([r['shift'] for r in report['fine']] == [0., .5]
            and all(r['n'] == 128 and r['nodes'] == 512 for r in report['fine']),
            'both registered fine grids required')
    require([(r['ninner'], r['ncoil']) for r in report['interior']] == list(check.LEVELS),
            'all three registered interior grids required')
    scale = frozen['snapshot']['scale']
    field_rows = report['fine']+report['interior']
    if frozen['proposal'] != 'control':
        expected = {k: frozen['identity'][k] for k in coil.BINDING_KEYS}
        for row in [*field_rows, report['geometry'], report['trace']]:
            context = row.get('joint_target')
            require(context is not None and context['binding'] == expected
                    and context['canonical_snapshot_sha256']
                    == frozen['canonical_snapshot_sha256'],
                    'diagnostic target or snapshot differs from frozen selection')
    require(all(r['checks_pass'] and r['metrics']['frozen_scale'] == scale for r in field_rows),
            'numerically checked fields with frozen currents required')
    for row in field_rows:
        errors = row.get('independent_errors', row.get('checks'))
        require(bool(errors) and np.isfinite(list(errors.values())).all()
                and min(errors.values()) >= 0 and max(errors.values()) <= 1e-12,
                'independent field checks failed')
    values = [r['metrics'][k] for r in report['fine'] for k in ('normal_rms', 'normal_max')]
    values.extend(r['metrics']['vector_rms'] for r in report['interior'])
    require(np.isfinite(values).all() and min(values) >= 0,
            'every field grid needs finite nonnegative errors')
    holds = [report[m] for m in ('holdout', 'holdout-refined')]
    for mode, row in zip(('holdout', 'holdout-refined'), holds, strict=True):
        require(row['identity'] == frozen['identity'], 'held-out score belongs to another target')
        complete_score(row, mode)
    convergence = action.holdout_agreement(*holds)
    trace = report['trace']
    require(trace['completed'] and trace['current_A'] == 1e5*scale
            and trace['transits'] == 200 and trace['target_launches'] == list(tracing.S_VALUES)
            and [r['s'] for r in trace['lines']] == list(tracing.S_VALUES)
            and trace['field'] == 'direct BiotSavart' and trace['tol'] == 1e-10
            and trace['frozen_current'], 'complete frozen-current direct trace required')
    kernel = list(trace['kernel_control'].values())
    require(bool(kernel) and np.isfinite(kernel).all() and min(kernel) >= 0
            and max(kernel) <= 1e-12, 'independent trace field check failed')
    trace_summary = tracing.summarize(trace['lines'], 200)
    require(trace_summary == trace['summary'], 'trace summary differs from line records')
    require(trace_summary['classifier_stops_inside_target'] == 0,
            'unresolved classifier stop prevents a complete comparison')
    # Confirmed exits are observed failures; a finite integration cap without an
    # exit leaves the requested 200-turn diagnostic unfinished.
    require(all(r['transits'] >= 200 or r['left_target'] for r in trace['lines']),
            'unfinished direct trajectory')
    geometry = report['geometry']['status']
    require(geometry in ('pass', 'fail', 'unresolved'), 'unknown geometry result')
    boundary = max(r['metrics']['normal_rms'] for r in report['fine'])
    interior = report['interior'][-1]['metrics']['vector_rms']
    normal_max = max(r['metrics']['normal_max'] for r in report['fine'])
    require(np.isfinite([boundary, interior, normal_max]).all()
            and min(boundary, interior, normal_max) >= 0,
            'finite nonnegative field errors required')
    currents = [r['metrics'][key] for rows, key in
                ((report['fine'], 'current'), (report['interior'], 'base_current')) for r in rows]
    require(all(value == 1e5*scale for value in currents), 'diagnostic current changed')
    return dict(boundary_rms=boundary, interior_rms=interior, normal_max=normal_max,
                holdout_scores=[r['score'] for r in holds], refinement_pass=convergence['passed'],
                geometry_pass=geometry == 'pass', current_pass=abs(1e5*scale) <= 500000,
                flux_pass=all(r['metrics']['flux_limit_met'] for r in field_rows),
                tracing_pass=trace_summary['all_confined_and_iota_matching'],
                normal_rms_limit_met=boundary <= 1e-4, normal_max_limit_met=normal_max <= 1e-3,
                interior_limit_met=interior <= .01, physical_admission=False)


def decide(control, joint):
    """Apply feasibility screens to complete summaries from diagnostic_summary."""
    for row in (control, joint):
        require(len(row['holdout_scores']) == 2, 'both held-out resolutions required')
        values = [*row['holdout_scores'], row['boundary_rms'], row['interior_rms']]
        require(np.isfinite(values).all() and min(values) >= 0,
                'finite nonnegative comparison metrics required')
    # A zero-to-zero tie cannot demonstrate a relative improvement.
    checks = dict(ideal_gain=all(c > 0 and j <= .99*c for c, j in zip(
                      control['holdout_scores'], joint['holdout_scores'], strict=True)),
                  boundary_nonregression=joint['boundary_rms'] <= 1.10*control['boundary_rms'],
                  interior_nonregression=joint['interior_rms'] <= 1.10*control['interior_rms'])
    for name in ('refinement_pass', 'geometry_pass', 'current_pass', 'flux_pass', 'tracing_pass'):
        checks[name] = bool(control[name] and joint[name])
    return dict(verdict='continue' if all(checks.values()) else 'change', checks=checks,
                actual_coil_endpoint=None, physical_admission=False,
                physical_benefit_claim_allowed=False, full_joint_execution_enabled=False)


def assess(proposals, control, joint):
    """Three-way decision from trusted completed records; never repair missing work."""
    base = dict(completed=False, verdict='inconclusive', actual_coil_endpoint=None,
                physical_admission=False, physical_benefit_claim_allowed=False,
                full_joint_execution_enabled=False)
    try:
        require(control is not None, 'missing control candidate')
        require(control['frozen']['proposal'] == 'control', 'original control arm required')
        c = diagnostic_summary(control['frozen'], control['diagnostics'])
        selected = select_joint(proposals)
        if selected is None:
            require(all(r.get('rejection') is not None for r in proposals),
                    'no eligible joint fit and not all proposals explicitly rejected')
            return dict(base, completed=True, verdict='change',
                        reason='both proposals explicitly rejected', selected_proposal=None)
        require(joint is not None, 'missing selected joint diagnostics')
        expected = proposals[selected]
        frozen = joint['frozen']
        require(frozen['proposal'] == expected['proposal']
                and frozen['identity'] == expected['training']['identity']
                and frozen['training_score'] == expected['training']['score']
                and frozen['inner_objective'] == expected['search']['selected']['value']
                and frozen['selected_index'] == expected['search']['selected']['index'],
                'diagnostics do not belong to training-selected proposal')
        j = diagnostic_summary(frozen, joint['diagnostics'])
        return dict(decide(c, j), completed=True, selected_proposal=expected['proposal'],
                    control=c, joint=j)
    except IncompleteComparison as exc:
        return dict(base, reason=str(exc))
