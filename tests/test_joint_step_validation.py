"""Paired validation requires frozen identities, complete domains and original clocks."""
from types import SimpleNamespace

import pytest
import test_joint_decision as fixtures
import test_joint_schedule as timing

from fusion_baselines import joint_step_validation as validation


def reports():
    rows = {p: {m: fixtures.score(p, m, amplitude=.1 if p == 'control' else .08)
                for m in validation.MODES} for p in ('control', 'scale035')}
    for row in rows['scale035'].values():
        row['identity']['target_id'] = validation.target.proposal_id('scale035')
    return rows


def parent():
    return dict(wout_sha256='a'*64, record_sha256='b'*64)


def test_frozen_protocol_domain_and_limits():
    protocol = validation.solver.read(validation.check.ROOT/validation.PROTOCOL)
    assert validation.solver.digest(validation.check.ROOT/validation.PROTOCOL) == (
        validation.PROTOCOL_SHA)
    assert protocol['order'] == [list(row) for row in validation.ORDER]
    assert protocol['budget']['total_seconds'] == validation.SECONDS
    assert protocol['candidate']['input_sha256'] == validation.target.INPUT_HASHES['scale035']
    assert protocol['reference']['wout_sha256'] == validation.check.FIXED[validation.check.WOUT]
    assert protocol['grids'] == {m: list(validation.action.GRIDS[m]) for m in validation.MODES}
    assert protocol['domain'] == dict(surfaces=list(validation.decision.bounce.SURFACES),
        pitches=list(validation.decision.bounce.HOLD_PITCHES), periods=2)


def test_both_grid_gains_and_both_refinements_are_required():
    rows = reports()
    assert validation.classify(rows, parent())['verdict'] == 'positive'
    for mode in validation.MODES:
        rows['scale035'][mode] = fixtures.score('scale035', mode, amplitude=.11)
        rows['scale035'][mode]['identity']['target_id'] = validation.target.proposal_id('scale035')
    result = validation.classify(rows, parent())
    assert result['verdict'] == 'negative' and not result['gain_hurdle_passed']
    assert result['refinement_hurdle_passed']
    rows = reports()
    row = fixtures.score('scale035', 'holdout-refined', amplitude=.081)
    row['identity']['target_id'] = validation.target.proposal_id('scale035')
    rows['scale035']['holdout-refined'] = row
    result = validation.classify(rows, parent())
    assert result['gain_hurdle_passed'] and not result['refinement_hurdle_passed']
    assert result['verdict'] == 'negative'


@pytest.mark.parametrize('fault', ['pair', 'surface', 'pitch', 'scalar', 'domain', 'target',
                                  'input', 'wout', 'parent'])
def test_missing_or_unbound_evidence_cannot_pass(fault):
    rows = reports()
    row = rows['scale035']['holdout-refined']
    if fault == 'pair':
        del rows['control']['holdout']
    elif fault == 'surface':
        row['surfaces'].pop()
    elif fault == 'pitch':
        row['surfaces'][0]['cells'].pop()
    elif fault == 'scalar':
        row['score'] = 0.
    elif fault == 'domain':
        row.update(eligible=False, score=None)
    else:
        key = {'target': 'target_id', 'input': 'input_sha256', 'wout': 'wout_sha256',
               'parent': 'parent_sha256'}[fault]
        row['identity'][key] = 'different'
    with pytest.raises(ValueError):
        validation.classify(rows, parent())


def test_training_screen_and_old_proposal_contracts_stay_separate(monkeypatch):
    calls = []
    monkeypatch.setattr(validation.action, '_score_receipt',
                        lambda *args: calls.append(args))
    validation.action.score_step_scale('folder', parent(), None)
    assert calls[-1][2:] == ('training', None, ('scale035',))
    validation.action.score_step_validation('folder', parent(), 'holdout', None)
    assert calls[-1][2:] == ('holdout', None, ('scale035',))
    validation.action.score_proposal('folder', parent(), 'holdout', None)
    assert calls[-1][4] == ('plus', 'minus')
    with pytest.raises(ValueError):
        validation.action.score_step_validation('folder', parent(), 'training', None)


def assembled(tmp_path, monkeypatch, fault=None):
    clock = timing.Clock()
    origin = clock.mono, clock.wall
    monkeypatch.setattr(validation.time, 'monotonic', lambda: clock.mono)
    monkeypatch.setattr(validation.time, 'time', lambda: clock.wall)
    monkeypatch.setattr(validation.solver.shutil, 'disk_usage',
                        lambda path: SimpleNamespace(free=10*1024**3))
    config = dict(native_environment='native-lock', reference_wout='reference-wout',
                  candidate_folder='candidate')
    calls = []

    def prepare(*args):
        clock.advance(180 if fault == 'prepare' else 5)
        return config, parent(), {}

    monkeypatch.setattr(validation, 'prepare', prepare)
    monkeypatch.setattr(validation.screen, 'verify', lambda config, sources, guard: guard())

    def supervise(command, folder, output, mono, wall, clock_origin=None):
        assert (mono, wall) == (origin[0]+180, origin[1]+180) and clock_origin == origin
        path = folder/'request.json'
        request = validation.solver.read(path)
        p, m = request['proposal'], request['mode']
        calls.append((p, m))
        assert request['operation'] == 'phase-score'
        assert request['window'] == request['outer'] == dict(monotonic=mono, wall=wall)
        assert request['clock_origin'] == list(origin)
        row = reports()[p][m]
        if fault == 'domain':
            row.update(eligible=False, score=None)
        (folder/'run').mkdir()
        receipt = dict(completed=True, operation='phase-score', proposal=p,
            request_sha256=validation.solver.digest(path), result=row,
            sources_unchanged=True, environment_unchanged=True)
        if fault == 'receipt':
            receipt['request_sha256'] = 'changed'
        validation.solver.save(folder/'run/result.json', receipt)
        clock.advance(180 if fault == 'deadline' else 10)
        if fault == 'clock-jump':
            clock.wall += 6
        return dict(completed=fault != 'process', returncode=0, stop_reason=None)

    monkeypatch.setattr(validation.solver, 'supervise', supervise)
    if fault == 'final-save':
        save = validation.solver.save

        def late_save(path, value):
            save(path, value)
            if path.name == 'validation.json' and value['completed']:
                clock.advance(180)

        monkeypatch.setattr(validation.solver, 'save', late_save)
    result = validation.run(tmp_path/'config.json', tmp_path/'output', 'a'*40, origin)
    return result, calls, validation.solver.read(tmp_path/'output/validation.json')


def test_four_fixed_scores_share_one_budget_without_solve_or_fit(tmp_path, monkeypatch):
    result, calls, saved = assembled(tmp_path, monkeypatch)
    assert result == saved and result['completed'] and result['verdict'] == 'positive'
    assert calls == validation.ORDER and result['elapsed_s'] == 45
    assert result['cold_solve_reused'] and not result['coil_feasibility_established']
    assert not result['physical_admission'] and result['actual_coil_endpoint'] is None


@pytest.mark.parametrize('fault', ['prepare', 'deadline', 'clock-jump', 'receipt', 'process',
                                  'domain', 'final-save'])
def test_interrupted_unbound_or_missing_work_is_inconclusive(tmp_path, monkeypatch, fault):
    result, calls, saved = assembled(tmp_path, monkeypatch, fault)
    assert result == saved and not result['completed'] and result['verdict'] == 'inconclusive'
    assert calls == validation.ORDER[:len(calls)] and len(calls) <= 4
    if fault == 'prepare':
        assert not calls
