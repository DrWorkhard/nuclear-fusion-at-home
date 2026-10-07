"""The new input stays separate; one cold solve and score share one hard budget."""
import copy
from types import SimpleNamespace

import pytest
import test_joint_decision as fixtures
import test_joint_schedule as timing

from fusion_baselines import joint_step_scale as screen


def score(amplitude=.08):
    row = fixtures.score('scale035', amplitude=amplitude)
    row['identity']['target_id'] = screen.target.proposal_id('scale035')
    return row


def parent():
    return dict(wout_sha256='a'*64, record_sha256='b'*64)


def test_step_input_is_exact_and_not_a_coil_or_public_target(tmp_path):
    target = screen.target
    original = screen.solver.read(screen.check.ROOT/screen.check.TARGET)
    document = copy.deepcopy(original)
    next(r for r in document['rbc'] if (r['m'], r['n']) == (2, 1))['value'] += .00035
    path = tmp_path/'input.json'
    screen.solver.save(path, document)
    sources = {}
    assert target.registered_input(path, 'scale035', sources) == (document, original)
    assert target.check.digest(path) == target.INPUT_HASHES['scale035']
    assert sources[str((screen.check.ROOT/target.SCALE_PROTOCOL).resolve())]
    assert set(screen.check.TARGETS) == {'reference401', 'selected401'}
    with pytest.raises(ValueError, match='registered proposal binding'):
        screen.native.coil.snapshot_identity({}, dict(target_id=target.proposal_id('scale035'),
            input_sha256=target.INPUT_HASHES['scale035'], wout_sha256='a'*64, parent_sha256='b'*64))
    with pytest.raises(ValueError):
        target.registered_input(path, 'plus', {})
    next(r for r in document['rbc'] if (r['m'], r['n']) == (2, 1))['value'] += .000001
    screen.solver.save(path, document)
    with pytest.raises(ValueError):
        target.registered_input(path, 'scale035', {})


def test_protocol_uses_original_full_training_domain():
    protocol = screen.solver.read(screen.check.ROOT/screen.target.SCALE_PROTOCOL)
    assert screen.solver.digest(screen.check.ROOT/screen.target.SCALE_PROTOCOL) == (
        screen.target.SCALE_PROTOCOL_SHA)
    settings = protocol['science']['training']
    assert settings['surfaces'] == list(screen.decision.bounce.SURFACES)
    assert settings['pitches'] == list(screen.decision.bounce.HOLD_PITCHES)
    assert (settings['nphi'], settings['nalpha'], settings['alpha_offset']) == (
        screen.decision.action.GRIDS['training'])
    assert protocol['budget']['total_seconds'] == screen.SECONDS
    assert protocol['decision']['threshold_ratio'] == screen.RATIO


def test_training_threshold_and_domain_must_be_met():
    reference = fixtures.score()['score']
    assert screen.classify(score(.08), parent(), reference)['verdict'] == 'positive'
    assert screen.classify(score(.1), parent(), reference)['verdict'] == 'negative'
    broken = score(.08)
    broken['surfaces'].pop()
    with pytest.raises(screen.decision.IncompleteComparison):
        screen.classify(broken, parent(), reference)
    broken = score(.08)
    broken['score'] = 0.
    with pytest.raises(screen.decision.IncompleteComparison):
        screen.classify(broken, parent(), reference)


@pytest.mark.parametrize('key', ['target_id', 'input_sha256', 'wout_sha256', 'parent_sha256'])
def test_score_must_belong_to_this_cold_solve(key):
    row = score()
    row['identity'][key] = 'different'
    with pytest.raises(ValueError, match='cold-solve receipt'):
        screen.classify(row, parent(), fixtures.score()['score'])


def test_only_a_complete_documented_domain_failure_is_negative():
    row = dict(proposal='scale035')
    fixtures.reject(row)
    row['training']['identity']['target_id'] = screen.target.proposal_id('scale035')
    assert screen.classify(row['training'], parent(), .1)['verdict'] == 'negative'
    row['training']['surfaces'][0]['errors'][0]['wells_by_alpha'].pop()
    with pytest.raises(screen.decision.IncompleteComparison):
        screen.classify(row['training'], parent(), .1)


def assembled(tmp_path, monkeypatch, fault=None):
    clock = timing.Clock()
    origin = clock.mono, clock.wall
    monkeypatch.setattr(screen.time, 'monotonic', lambda: clock.mono)
    monkeypatch.setattr(screen.time, 'time', lambda: clock.wall)
    monkeypatch.setattr(screen.solver.shutil, 'disk_usage',
                        lambda path: SimpleNamespace(free=10*1024**3))
    reference = fixtures.score()['score']
    config = dict(input_path=str(tmp_path/'input.json'), solver_python='venv-python',
                  solver_environment='solver-lock', solver_environment_sha256='lock',
                  native_environment='native-lock')
    calls = []

    def prepare(*args):
        calls.append('prepare')
        clock.advance(600 if fault == 'prepare' else 5)
        return config, reference, {}

    monkeypatch.setattr(screen, 'prepare', prepare)
    monkeypatch.setattr(screen, 'verify', lambda config, sources, guard: guard())

    def solve(python, input_path, proposal, environment, sha, folder, output, revision,
              mono, wall, clock_origin=None):
        calls.append('solve')
        assert proposal == 'scale035' and python == 'venv-python'
        assert (mono, wall) == (origin[0]+600, origin[1]+600) and clock_origin == origin
        folder.mkdir()
        for name in ('parent.json', 'request.json', 'solver.json', 'input.json', 'wout.nc'):
            screen.solver.save(folder/name, {'synthetic': True})
        clock.advance(600 if fault == 'solve' else 185)
        return dict(completed=fault != 'unfinished-solve',
                    wout_sha256=screen.solver.digest(folder/'wout.nc'),
                    record_sha256=screen.solver.digest(folder/'parent.json'))

    monkeypatch.setattr(screen.solver, 'run_solver', solve)

    def supervise(command, folder, output, mono, wall, clock_origin=None):
        calls.append('score')
        assert (mono, wall) == (origin[0]+600, origin[1]+600) and clock_origin == origin
        path = folder/'request.json'
        request = screen.solver.read(path)
        assert request['operation'] == 'step-score' and request['proposal'] == 'scale035'
        assert request['clock_origin'] == list(origin)
        assert request['outer'] == request['window'] == dict(monotonic=mono, wall=wall)
        row = score()
        row['identity']['wout_sha256'] = request['solved']['parent']['wout_sha256']
        row['identity']['parent_sha256'] = request['solved']['parent']['record_sha256']
        (folder/'run').mkdir()
        receipt = dict(completed=True, operation='step-score', proposal='scale035',
                       request_sha256=screen.solver.digest(path), result=row,
                       sources_unchanged=True, environment_unchanged=True)
        if fault == 'receipt':
            receipt['request_sha256'] = 'changed'
        screen.solver.save(folder/'run/result.json', receipt)
        clock.advance(600 if fault == 'score' else 10)
        if fault == 'clock-jump':
            clock.wall += 6
        return dict(completed=True)

    monkeypatch.setattr(screen.solver, 'supervise', supervise)
    if fault == 'final-save':
        save = screen.solver.save

        def late_save(path, value):
            save(path, value)
            if path.name == 'screen.json' and value['completed']:
                clock.advance(600)

        monkeypatch.setattr(screen.solver, 'save', late_save)
    result = screen.run(tmp_path/'config.json', tmp_path/'output', 'a'*40, origin)
    return result, calls, screen.solver.read(tmp_path/'output/screen.json')


def test_one_cold_solve_and_score_with_no_fit_share_original_clocks(tmp_path, monkeypatch):
    result, calls, saved = assembled(tmp_path, monkeypatch)
    assert result == saved and result['completed'] and result['verdict'] == 'positive'
    assert result['elapsed_s'] == 200 and calls == ['prepare', 'solve', 'score']
    assert not result['physical_admission'] and not result['coil_feasibility_established']
    assert not result['heldout_gain_established'] and result['actual_coil_endpoint'] is None


@pytest.mark.parametrize('fault', ['prepare', 'solve', 'score', 'final-save', 'clock-jump',
                                  'unfinished-solve', 'receipt'])
def test_late_incomplete_or_unbound_work_never_wins_or_retries(tmp_path, monkeypatch, fault):
    result, calls, saved = assembled(tmp_path, monkeypatch, fault)
    assert result == saved and not result['completed'] and result['verdict'] == 'inconclusive'
    assert calls.count('solve') <= 1 and calls.count('score') <= 1
    if fault in ('prepare', 'solve', 'unfinished-solve'):
        assert 'score' not in calls
