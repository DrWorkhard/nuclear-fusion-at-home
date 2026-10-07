"""Failure and boundary cases for the registered joint comparison rules."""
import copy
import time

import numpy as np
import pytest
import test_coil_check as fixtures

from fusion_baselines import joint_decision as decision
from fusion_baselines.coil_fit import Recorder


def score(proposal='control', mode='training', amplitude=.1):
    nphi, nalpha, offset = decision.action.GRIDS[mode]
    values = np.tile(np.repeat([1-amplitude, 1+amplitude], nalpha//2)[:, None], (1, 2))
    stats = decision.bounce.action_statistics(values)
    surfaces = [dict(s=s, errors=[], cells=[dict(q=q, actions=values.tolist(), **stats)
                for q in decision.bounce.HOLD_PITCHES]) for s in decision.bounce.SURFACES]
    identity = dict(target_id='reference401' if proposal == 'control'
                    else f'issue37-joint-v1/{proposal}',
                    input_sha256=decision.target.INPUT_HASHES[proposal],
                    wout_sha256=decision.check.FIXED[decision.check.WOUT]
                    if proposal == 'control' else 'a'*64)
    if proposal != 'control':
        identity['parent_sha256'] = 'b'*64
    return dict(completed=True, eligible=True, mode=mode, identity=identity, surfaces=surfaces,
                settings=dict(nphi=nphi, nalpha=nalpha, alpha_offset=offset, periods=2,
                              surfaces=list(decision.bounce.SURFACES),
                              pitches=list(decision.bounce.HOLD_PITCHES)),
                score=float(np.mean([stats['score']]*35)), sources_after={})


def search(snapshot=None, objective=.02):
    snapshot = fixtures.snapshot.__wrapped__() if snapshot is None else snapshot
    return dict(startup_pass=True, status=dict(reason='solver-return'), selected=dict(
        index=12, status='completed', role='search', value=objective,
        x=np.asarray(snapshot['base_coefficients']).ravel().tolist(), metrics=dict(
            sampled_geometry_limits_met=True, current_limit_met=True, lengths=[3.4]*6,
            normal_rms=.002, scale=snapshot['scale'], unit_flux=snapshot['unit_flux'])))


def proposals():
    return [dict(proposal=p, completed=True, training=score(p), search=search(),
                 ordinary_fit_cap=False, rejection=None) for p in ('plus', 'minus')]


def test_training_score_then_inner_objective_then_order_choose_joint():
    rows = proposals()
    assert decision.select_joint(rows) == 0
    rows[1]['search']['selected']['value'] *= .5
    assert decision.select_joint(rows) == 1
    rows[0]['training'] = score('plus', amplitude=.08)
    assert decision.select_joint(rows) == 0
    # Validation values are deliberately absent from the selection interface.
    assert 'holdout' not in rows[0]


@pytest.mark.parametrize('fault', ['missing', 'order', 'unfinished', 'wrong-target',
                                  'untyped-reject'])
def test_missing_or_unqualified_proposals_cannot_be_selected(fault):
    rows = proposals()
    if fault == 'missing':
        rows.pop()
    elif fault == 'order':
        rows.reverse()
    elif fault == 'unfinished':
        rows[1]['completed'] = False
    elif fault == 'wrong-target':
        rows[0]['training']['identity']['target_id'] = 'reference401'
    else:
        rows[1]['rejection'] = dict(kind='timeout', evidence='timed out')
    with pytest.raises(decision.IncompleteComparison):
        decision.select_joint(rows)


def test_completed_explicit_rejection_does_not_hide_unfinished_other_proposal():
    rows = proposals()
    rows[0]['rejection'] = dict(kind='plasma-domain', evidence={'failed_cells': [(.5, .97)]})
    assert decision.select_joint(rows) == 1
    rows[1]['rejection'] = dict(kind='equilibrium', evidence={'converged': False})
    assert decision.select_joint(rows) is None
    rows[1]['completed'] = False
    with pytest.raises(decision.IncompleteComparison, match='unfinished'):
        decision.select_joint(rows)


def test_ordinary_fit_cap_only_keeps_earlier_eligible_candidate_after_startup():
    result = search()
    result['status']['reason'] = 'budget'
    assert decision.fit_eligible(result, True)
    assert not decision.fit_eligible(result, False)
    result['startup_pass'] = False
    assert not decision.fit_eligible(result, True)
    result['startup_pass'] = True
    result['selected']['role'] = 'probe'
    assert not decision.fit_eligible(result, True)


@pytest.mark.parametrize('fault', ['domain', 'phases', 'aggregate', 'cell', 'settings',
                                  'ineligible'])
def test_reduced_or_changed_action_domain_is_incomplete(fault):
    row = score()
    if fault == 'domain':
        row['surfaces'][0]['cells'].pop()
    elif fault == 'phases':
        row['surfaces'][0]['cells'][0]['actions'].pop()
    elif fault == 'aggregate':
        row['score'] *= .99
    elif fault == 'cell':
        row['surfaces'][0]['cells'][0]['score'] *= .99
    elif fault == 'settings':
        row['settings']['nalpha'] = 32
    else:
        row['eligible'] = False
    with pytest.raises(decision.IncompleteComparison):
        decision.complete_score(row, 'training')


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    wout = tmp_path/'wout.nc'
    wout.write_bytes(b'unit-test Wout placeholder')
    monkeypatch.setitem(decision.check.FIXED, decision.check.WOUT, decision.check.digest(wout))
    snapshot = fixtures.snapshot.__wrapped__()
    record = Recorder(tmp_path/'selection', time.monotonic()+60)
    result = decision.freeze_selection('control', score(), search(snapshot), False, snapshot,
                                      decision.check.ROOT/decision.check.TARGET, wout, record)
    return result, record, wout


def test_freeze_copies_selection_and_rejects_reselection(frozen):
    result, record, wout = frozen
    assert (record.output/'frozen-selection.json').exists()
    original = copy.deepcopy(result)
    with pytest.raises(decision.IncompleteComparison, match='already frozen'):
        decision.freeze_selection('control', score(), search(), False, result['snapshot'],
                                  decision.check.ROOT/decision.check.TARGET, wout, record)
    assert result == original


def diagnostics(frozen):
    scale = frozen['snapshot']['scale']
    fine = [dict(shift=s, n=128, nodes=512, checks_pass=True,
                 independent_errors=dict(B=1e-16, A=1e-16), metrics=dict(frozen_scale=scale,
                 current=1e5*scale, normal_rms=v, normal_max=.005, flux_limit_met=True))
            for s, v in ((0., .002), (.5, .003))]
    interior = [dict(ninner=n, ncoil=c, checks_pass=True, checks=dict(B=1e-16, A=1e-16),
                     metrics=dict(frozen_scale=scale, base_current=1e5*scale,
                                  vector_rms=v, flux_limit_met=True))
                for (n, c), v in zip(decision.check.LEVELS, (.02, .03, .01), strict=True)]
    lines = [dict(s=s, transits=200., iota_target=-.3, iota_traced=-.3,
                  left_target=False, termination='transits') for s in decision.tracing.S_VALUES]
    trace = dict(completed=True, current_A=1e5*scale, transits=200,
                 field='direct BiotSavart', tol=1e-10, frozen_current=True,
                 kernel_control=dict(independent_volume=1e-16),
                 target_launches=list(decision.tracing.S_VALUES), lines=lines,
                 summary=decision.tracing.summarize(lines, 200))
    return dict(completed=True, budget_complete=True, selection_sha256=frozen['selection_sha256'],
                fine=fine, interior=interior, geometry=dict(status='pass'), trace=trace,
                holdout=score(mode='holdout'), **{'holdout-refined': score(mode='holdout-refined')})


def test_summary_uses_worst_fine_and_finest_interior_with_frozen_currents(frozen):
    selected, _, _ = frozen
    result = decision.diagnostic_summary(selected, diagnostics(selected))
    assert result['boundary_rms'] == .003 and result['interior_rms'] == .01
    assert result['normal_max'] == .005 and not result['normal_max_limit_met']
    assert not result['normal_rms_limit_met'] and result['interior_limit_met']


@pytest.mark.parametrize('fault', ['selection', 'budget', 'fine', 'interior', 'native-check',
                                  'current', 'holdout-target', 'holdout-domain',
                                  'trace-count', 'trace-summary', 'trace-cap', 'classifier'])
def test_incomplete_or_mixed_diagnostics_cannot_receive_verdict(frozen, fault):
    selected, _, _ = frozen
    report = diagnostics(selected)
    if fault == 'selection':
        selected['snapshot']['scale'] *= 1.1
    elif fault == 'budget':
        report['budget_complete'] = False
    elif fault in ('fine', 'interior'):
        report[fault].pop()
    elif fault == 'native-check':
        report['fine'][0]['independent_errors']['B'] = 1e-5
    elif fault == 'current':
        report['interior'][0]['metrics']['base_current'] *= 1.001
    elif fault == 'holdout-target':
        report['holdout']['identity']['wout_sha256'] = 'c'*64
    elif fault == 'holdout-domain':
        report['holdout']['eligible'] = False
    elif fault == 'trace-count':
        report['trace']['lines'].pop()
    elif fault == 'trace-summary':
        report['trace']['summary']['max_abs_iota_mismatch'] = 1.
    elif fault in ('trace-cap', 'classifier'):
        report['trace']['lines'][0]['transits'] = 50.
        if fault == 'classifier':
            report['trace']['lines'][0]['termination'] = 'classifier_stop_inside_target'
        report['trace']['summary'] = decision.tracing.summarize(report['trace']['lines'], 200)
    with pytest.raises(decision.IncompleteComparison):
        decision.diagnostic_summary(selected, report)


def test_confirmed_exit_is_observed_failure_not_an_unfinished_trajectory(frozen):
    selected, _, _ = frozen
    report = diagnostics(selected)
    report['trace']['lines'][0].update(left_target=True, transits=50.)
    report['trace']['summary'] = decision.tracing.summarize(report['trace']['lines'], 200)
    result = decision.diagnostic_summary(selected, report)
    assert not result['tracing_pass']


def summaries():
    control = dict(boundary_rms=.002, interior_rms=.01, holdout_scores=[.02, .02],
                   refinement_pass=True, geometry_pass=True, current_pass=True,
                   flux_pass=True, tracing_pass=True)
    joint = dict(control, holdout_scores=[.019, .019])
    return control, joint


def test_continue_never_asserts_physical_acceptance_or_common_coil_benefit():
    result = decision.decide(*summaries())
    assert result['verdict'] == 'continue'
    assert not result['physical_admission'] and not result['physical_benefit_claim_allowed']
    assert result['actual_coil_endpoint'] is None


@pytest.mark.parametrize('key', ['boundary_rms', 'interior_rms', 'holdout_scores',
                               'geometry_pass', 'current_pass', 'flux_pass',
                               'tracing_pass', 'refinement_pass'])
def test_each_registered_feasibility_screen_can_change_recipe(key):
    control, joint = summaries()
    if key.endswith('_rms'):
        joint[key] = 1.100001*control[key]
    elif key == 'holdout_scores':
        joint[key] = [.019, .02]
    else:
        joint[key] = False
    assert decision.decide(control, joint)['verdict'] == 'change'


@pytest.mark.parametrize('values', [[], [.01], [.01, float('nan')], [-.1, -.1]])
def test_missing_or_nonfinite_heldout_metrics_are_not_a_positive_result(values):
    control, joint = summaries()
    joint['holdout_scores'] = values
    with pytest.raises(decision.IncompleteComparison):
        decision.decide(control, joint)


def test_assess_reports_inconclusive_for_missing_control_or_proposal(frozen):
    assert decision.assess(proposals(), None, None)['verdict'] == 'inconclusive'
    selected, _, _ = frozen
    control = dict(frozen=selected, diagnostics=diagnostics(selected))
    rows = proposals()
    rows[1]['completed'] = False
    result = decision.assess(rows, control, None)
    assert result['verdict'] == 'inconclusive' and not result['completed']
    assert result['reason'] == 'unfinished joint proposal'


def test_assess_changes_only_after_both_explicit_rejections_with_complete_control(frozen):
    selected, _, _ = frozen
    control = dict(frozen=selected, diagnostics=diagnostics(selected))
    rows = proposals()
    for row in rows:
        row['rejection'] = dict(kind='plasma-domain', evidence={'failed_cells': [(.5, .97)]})
    result = decision.assess(rows, control, None)
    assert result['verdict'] == 'change' and result['completed']
    control['diagnostics']['budget_complete'] = False
    assert decision.assess(rows, control, None)['verdict'] == 'inconclusive'


def selected_pair(frozen):
    selected, _, _ = frozen
    control = dict(frozen=selected, diagnostics=diagnostics(selected))
    rows = proposals()
    chosen = copy.deepcopy(selected)
    chosen.update(proposal='plus', identity=rows[0]['training']['identity'],
                  training_score=rows[0]['training']['score'],
                  inner_objective=rows[0]['search']['selected']['value'],
                  selected_index=rows[0]['search']['selected']['index'])
    chosen['snapshot'].update(target_id=chosen['identity']['target_id'],
                              joint_target_binding=copy.deepcopy(chosen['identity']))
    chosen['canonical_snapshot_sha256'] = decision.canonical_sha(chosen['snapshot'])
    chosen['selection_sha256'] = decision.canonical_sha(
        {k: v for k, v in chosen.items() if k != 'selection_sha256'})
    joint = dict(frozen=chosen, diagnostics=diagnostics(chosen))
    report = joint['diagnostics']
    for row in [*report['fine'], *report['interior'], report['geometry'], report['trace']]:
        row['joint_target'] = dict(binding=copy.deepcopy(chosen['identity']),
            canonical_snapshot_sha256=chosen['canonical_snapshot_sha256'])
    for mode in ('holdout', 'holdout-refined'):
        joint['diagnostics'][mode] = score('plus', mode, amplitude=.095)
    return rows, control, joint


def test_full_assessment_keeps_selection_separate_from_validation(frozen):
    rows, control, joint = selected_pair(frozen)
    result = decision.assess(rows, control, joint)
    assert result['completed'] and result['verdict'] == 'continue'
    assert result['selected_proposal'] == 'plus' and result['actual_coil_endpoint'] is None
    # A lower training score at minus invalidates the frozen plus diagnostic;
    # good validation at plus cannot choose a different winner retrospectively.
    rows[1]['training'] = score('minus', amplitude=.08)
    result = decision.assess(rows, control, joint)
    assert not result['completed'] and result['verdict'] == 'inconclusive'


def test_complete_pair_that_misses_ideal_hurdle_changes_recipe(frozen):
    rows, control, joint = selected_pair(frozen)
    for mode in ('holdout', 'holdout-refined'):
        joint['diagnostics'][mode] = score('plus', mode, amplitude=.1)
    result = decision.assess(rows, control, joint)
    assert result['completed'] and result['verdict'] == 'change'
    assert not result['checks']['ideal_gain']


def test_no_joint_fit_candidate_does_not_turn_resource_limit_into_rejection(frozen):
    rows, control, _ = selected_pair(frozen)
    for row in rows:
        row['search']['selected'] = None
        row['search']['status']['reason'] = 'budget'
        row['ordinary_fit_cap'] = True
    result = decision.assess(rows, control, None)
    assert not result['completed'] and result['verdict'] == 'inconclusive'


@pytest.mark.parametrize('group,key', [('fine', 'normal_rms'), ('fine', 'normal_max'),
                                     ('interior', 'vector_rms')])
def test_bad_nonselected_grid_cannot_be_hidden_by_metric_aggregation(frozen, group, key):
    selected, _, _ = frozen
    report = diagnostics(selected)
    report[group][0]['metrics'][key] = float('nan')
    with pytest.raises(decision.IncompleteComparison, match='every field grid'):
        decision.diagnostic_summary(selected, report)


@pytest.mark.parametrize('group', ['fine', 'interior', 'geometry', 'trace'])
@pytest.mark.parametrize('fault', ['wout', 'parent', 'snapshot', 'missing'])
def test_each_joint_diagnostic_must_belong_to_frozen_target_and_coils(frozen, group, fault):
    rows, control, joint = selected_pair(frozen)
    row = joint['diagnostics'][group]
    if isinstance(row, list):
        row = row[0]
    if fault == 'missing':
        del row['joint_target']
    elif fault == 'snapshot':
        row['joint_target']['canonical_snapshot_sha256'] = 'c'*64
    else:
        row['joint_target']['binding'][fault+'_sha256'] = 'c'*64
    result = decision.assess(rows, control, joint)
    assert result['verdict'] == 'inconclusive' and not result['completed']
    assert 'diagnostic target or snapshot' in result['reason']


def test_zero_score_tie_is_not_a_relative_improvement():
    control, joint = summaries()
    control['holdout_scores'] = joint['holdout_scores'] = [0., 0.]
    assert decision.decide(control, joint)['verdict'] == 'change'
