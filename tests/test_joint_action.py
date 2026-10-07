"""Fixed action domain, trusted intake, and failure controls for joint scoring."""
import copy
import json
import time
from types import SimpleNamespace

import numpy as np
import pytest

from fusion_baselines import joint_action as action
from fusion_baselines.coil_fit import Recorder


def analytic_trace(nphi, nalpha, offset=0., epsilon=.2):
    phi = np.linspace(0, 2*np.pi, nphi)
    alpha = np.linspace(0, 2*np.pi, nalpha, endpoint=False)+offset
    return dict(phi=phi, alpha=alpha,
                B=np.tile((1.3+.28*np.cos(2*phi))[:, None], (1, nalpha)),
                length=phi[:, None]*(1+epsilon*np.cos(alpha)))


def test_kernel_matches_analytic_phase_variance():
    trace = analytic_trace(101, 16)
    row = action.bounce.period_actions(trace, .5)
    assert row['variance'] == pytest.approx([.02, .02], abs=1e-14)
    assert row['score'] == pytest.approx(.02, abs=1e-14)
    # The two periods are separate families, with no spurious phase variance.
    assert np.asarray(row['actions'])[:, 0] == pytest.approx(
        np.asarray(row['actions'])[:, 1], abs=1e-13)


@pytest.fixture
def score_cell(tmp_path, monkeypatch):
    wout = tmp_path/'wout.nc'
    wout.write_bytes(b'unit-test Wout placeholder; intake tested separately')
    identity = dict(target_id='reference401', wout_sha256=action.check.digest(wout))
    record = Recorder(tmp_path/'output', time.monotonic()+60)
    calls = []

    def trace(path, surface, nphi, nalpha, periods, *, alpha_offset):
        assert path == wout and periods == 2
        calls.append((surface, nphi, nalpha, alpha_offset))
        return analytic_trace(nphi, nalpha, alpha_offset)

    monkeypatch.setattr(action, 'trace_geometry', trace)
    # Full-grid routing uses a cheap distinct score for each pitch; kernel math
    # has a separate analytic control above, so this is not a duplicate kernel.
    monkeypatch.setattr(action.bounce, 'period_actions', lambda trace, q: dict(score=q))
    return wout, identity, record, calls


@pytest.mark.parametrize('mode,nphi,nalpha,offset', [
    ('training', 801, 16, 0.), ('holdout', 1601, 32, np.pi/32),
    ('holdout-refined', 3201, 32, np.pi/32)])
def test_complete_domain_and_frozen_grids(score_cell, mode, nphi, nalpha, offset):
    wout, identity, record, calls = score_cell
    result = action._score(wout, mode, record, {}, identity)
    assert calls == [(s, nphi, nalpha, offset) for s in (.1, .25, .5, .75, .9)]
    assert result['completed'] and result['eligible']
    assert result['score'] == pytest.approx(.5)
    assert sum(len(r['cells']) for r in result['surfaces']) == 35
    assert result['sources_before'] == result['sources_after']
    assert result['actual_coil_endpoint'] is None and not result['physical_admission']
    assert not result['full_joint_execution_enabled']
    for row in result['surfaces']:
        path = record.output/f"ideal-s{row['s']}.npz"
        assert action.check.digest(path) == row['arrays_sha256']
        with np.load(path) as arrays:
            assert arrays['B'].shape == (nphi, nalpha)
    with pytest.raises(ValueError, match='fresh action-score cell'):
        action._score(wout, mode, record, {}, identity)


def test_domain_failure_retains_every_alpha_without_partial_score(score_cell, monkeypatch):
    wout, identity, record, _ = score_cell

    def score(trace, q):
        if q == .5:
            raise action.bounce.IncompleteActionDomain('incomplete test well family')
        return dict(score=q)

    monkeypatch.setattr(action.bounce, 'period_actions', score)
    monkeypatch.setattr(action.bounce, 'bounce_wells', lambda *a: [
        SimpleNamespace(record=lambda: dict(complete=False, action=None))])
    result = action._score(wout, 'training', record, {}, identity)
    assert result['completed'] and not result['eligible'] and result['score'] is None
    for row in result['surfaces']:
        assert len(row['cells']) == 6 and len(row['errors']) == 1
        failure = row['errors'][0]
        assert failure['q'] == .5 and len(failure['wells_by_alpha']) == 16
        assert all(r['wells'] == [dict(complete=False, action=None)]
                   for r in failure['wells_by_alpha'])


@pytest.mark.parametrize('error', [ValueError, FloatingPointError, TimeoutError, OSError])
def test_software_or_resource_failure_is_not_scientific_rejection(score_cell, monkeypatch, error):
    wout, identity, record, _ = score_cell

    def fail(*args):
        raise error('test failure')

    monkeypatch.setattr(action.bounce, 'period_actions', fail)
    with pytest.raises(error, match='test failure'):
        action._score(wout, 'training', record, {}, identity)
    assert not (record.output/'action-score.json').exists()
    assert not json.loads((record.output/'action-attempt.json').read_text())['completed']
    assert (record.output/'ideal-s0.1.npz').exists()


def test_altered_source_cannot_complete(score_cell, monkeypatch):
    wout, identity, record, _ = score_cell
    first = action.trace_geometry

    def changed(*args, **kwargs):
        wout.write_bytes(b'changed Wout')
        return first(*args, **kwargs)

    monkeypatch.setattr(action, 'trace_geometry', changed)
    with pytest.raises(ValueError, match='source/input changed'):
        action._score(wout, 'training', record, {}, identity)
    assert not (record.output/'action-score.json').exists()


def test_post_save_deadline_prevents_returning_late_score(score_cell, monkeypatch):
    wout, identity, record, _ = score_cell

    def guard():
        if (record.output/'action-score.json').exists():
            raise TimeoutError('late serialization')

    monkeypatch.setattr(record, 'guard', guard)
    with pytest.raises(TimeoutError, match='late serialization'):
        action._score(wout, 'training', record, {}, identity)


@pytest.mark.parametrize('fault', ['shape', 'phi', 'alpha'])
def test_changed_phase_grid_cannot_receive_score(score_cell, monkeypatch, fault):
    wout, identity, record, _ = score_cell
    first = action.trace_geometry

    def invalid(*args, **kwargs):
        trace = first(*args, **kwargs)
        if fault == 'shape':
            trace['B'] = trace['B'][:-1]
        else:
            trace[fault][1] += .001
        return trace

    monkeypatch.setattr(action, 'trace_geometry', invalid)
    with pytest.raises(ValueError, match='complete registered ideal phase grid'):
        action._score(wout, 'training', record, {}, identity)


def test_reference_uses_exact_original_intake(monkeypatch, tmp_path):
    wout = tmp_path/'wout.nc'
    calls = []
    numerical = dict(input_sha256='input', wout_sha256='wout')

    def intake(*args):
        calls.append(args)
        return None, None, {}, numerical

    monkeypatch.setattr(action.target, 'intake', intake)
    monkeypatch.setattr(action, '_score', lambda *args: args)
    record = SimpleNamespace(guard=lambda: None)
    result = action.score_reference(wout, 'training', record)
    assert calls == [(action.check.ROOT/action.check.TARGET, wout, 'control',
                      action.check.FIXED[action.check.WOUT], record.guard)]
    assert result[-1]['target_id'] == 'reference401'


def test_proposal_rejection_never_reaches_score(monkeypatch, tmp_path):
    calls = []

    def rejected(*args):
        raise ValueError('invalid solver provenance')

    monkeypatch.setattr(action.solver, 'intake_result', rejected)
    monkeypatch.setattr(action, '_score', lambda *args: calls.append(args))
    with pytest.raises(ValueError, match='invalid solver provenance'):
        action.score_proposal(tmp_path, {}, 'training', SimpleNamespace(guard=lambda: None))
    assert not calls


@pytest.mark.parametrize('proposal', ['plus', 'minus'])
def test_proposal_score_binds_parent_and_receipts(monkeypatch, tmp_path, proposal):
    parent = dict(proposal=proposal, sources_before={})
    for name, key in (('parent.json', 'record_sha256'), ('solver.json', 'solver_report_sha256'),
                      ('request.json', 'request_sha256')):
        path = tmp_path/name
        path.write_text(name, encoding='utf-8')
        parent[key] = action.check.digest(path)
    numerical = dict(target_id=f'issue37-joint-v1/{proposal}', input_sha256='input',
                     wout_sha256='wout', parent_sha256=parent['record_sha256'],
                     solver_provenance_verified=True, numerical_consistency_pass=True)
    monkeypatch.setattr(action.solver, 'intake_result', lambda *a: (None, None, {}, numerical))
    monkeypatch.setattr(action, '_score', lambda *args: args)
    result = action.score_proposal(tmp_path, parent, 'training',
                                   SimpleNamespace(guard=lambda: None))
    assert result[0] == tmp_path/'wout.nc'
    assert set(result[-2]) == {str(tmp_path/name) for name in
                             ('parent.json', 'solver.json', 'request.json')}
    assert result[-1]['parent_sha256'] == parent['record_sha256']
    (tmp_path/'parent.json').write_text('modified receipt', encoding='utf-8')
    with pytest.raises(ValueError, match='source identity changed'):
        action.score_proposal(tmp_path, parent, 'training', SimpleNamespace(guard=lambda: None))


def holdouts(first, second):
    coarse = dict(mode='holdout', identity={'wout_sha256': 'frozen'},
                  completed=True, eligible=True, score=first)
    refined = dict(copy.deepcopy(coarse), mode='holdout-refined', score=second)
    return coarse, refined


@pytest.mark.parametrize('first,second,passes', [(1., .9991, True), (1., .9989, False),
                                               (0., 0., True), (0., 1e-16, True),
                                               (0., 1.1e-15, False)])
def test_frozen_holdout_convergence_rule(first, second, passes):
    result = action.holdout_agreement(*holdouts(first, second))
    assert result['passed'] == passes and not result['physical_admission']


@pytest.mark.parametrize('key,value', [('mode', 'training'), ('identity', {'other': 'target'}),
                                     ('completed', False), ('eligible', False),
                                     ('score', None), ('score', -1.), ('score', np.nan)])
def test_incomplete_or_mixed_holdouts_cannot_pass(key, value):
    coarse, refined = holdouts(1., 1.)
    refined[key] = value
    with pytest.raises(ValueError):
        action.holdout_agreement(coarse, refined)
