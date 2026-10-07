"""A fake clock tests full schedule ordering and failures without scientific compute."""
import copy

import pytest
import test_joint_decision as fixtures

from fusion_baselines import joint_schedule as schedule


class Clock:
    def __init__(self):
        self.mono, self.wall = 100., 1000.

    def advance(self, seconds):
        self.mono += seconds
        self.wall += seconds


@pytest.fixture
def clock(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(schedule.time, 'monotonic', lambda: clock.mono)
    monkeypatch.setattr(schedule.time, 'time', lambda: clock.wall)
    return clock


class Operations:
    """Synthetic native receipts only; the real decision helpers remain active."""
    def __init__(self, clock):
        self.clock, self.calls, self.states, self.windows = clock, [], {}, []
        self.delays = dict(setup=5., solve=150., score=10., fit=50., freeze=1., diagnose=100.)
        self.fault = None

    def step(self, name, proposal):
        self.calls.append((name, proposal))
        self.clock.advance(self.delays.get(name, 0.))
        if self.fault == (name, proposal):
            raise RuntimeError('unclassified operation failure')

    def setup(self, arm, window):
        self.windows.append((arm.name, 'setup', window))
        self.step('setup', arm.name)

    def score(self, arm, proposal, solved, window):
        self.windows.append((proposal, 'score', window))
        self.step('score', proposal)
        return fixtures.score(proposal)

    def solve(self, arm, proposal, window):
        self.windows.append((proposal, 'solve', window))
        self.step('solve', proposal)
        return dict(completed=True, rejection=None)

    def fit(self, arm, proposal, solved, training, window, outer):
        self.windows.append((proposal, 'fit', window, outer))
        self.step('fit', proposal)
        result = dict(search=fixtures.search(), snapshot=fixtures.fixtures.snapshot.__wrapped__(),
                      stop='solver-return', window=window)
        if self.clock.mono >= window.monotonic or self.clock.wall >= window.wall:
            result.update(stop='fit-cap')
            result['search']['status']['reason'] = 'budget'
        return result

    def freeze(self, arm, proposal, solved, training, fit, window):
        self.step('freeze', proposal)
        snapshot = copy.deepcopy(fit['snapshot'])
        identity = training['identity']
        if proposal != 'control':
            snapshot.update(target_id=identity['target_id'],
                            joint_target_binding=copy.deepcopy(identity))
        selected = fit['search']['selected']
        frozen = dict(proposal=proposal, identity=copy.deepcopy(identity), snapshot=snapshot,
            selected_index=selected['index'], inner_objective=selected['value'],
            training_score=training['score'], sources={}, physical_admission=False,
            canonical_snapshot_sha256=schedule.decision.canonical_sha(snapshot))
        frozen['selection_sha256'] = schedule.decision.canonical_sha(frozen)
        self.states[proposal] = frozen
        return frozen

    def diagnose(self, arm, frozen, window):
        proposal = frozen['proposal']
        self.windows.append((proposal, 'diagnose', window))
        assert proposal in self.states  # Freeze must precede every validation request.
        self.step('diagnose', proposal)
        report = fixtures.diagnostics(frozen)
        for mode in ('holdout', 'holdout-refined'):
            report[mode] = fixtures.score(proposal, mode,
                                          amplitude=.1 if proposal == 'control' else .095)
        if proposal != 'control':
            for row in [*report['fine'], *report['interior'], report['geometry'], report['trace']]:
                row['joint_target'] = dict(binding=copy.deepcopy(frozen['identity']),
                    canonical_snapshot_sha256=frozen['canonical_snapshot_sha256'])
        # Only the scheduler, after final budget checks, can certify this flag.
        report['budget_complete'] = False
        return report

    def verify(self, arm):
        self.step('verify', arm.name)

    def save_proposal(self, arm, row):
        self.step('save', row['proposal'])


def test_full_schedule_is_fixed_serial_and_freezes_before_holdout(clock, tmp_path):
    operations = Operations(clock)
    result = schedule.run(operations, tmp_path/'run')
    assert result['completed'] and result['verdict'] == 'continue'
    assert result['arms'] == ['C', 'J']
    assert [p for name, p in operations.calls if name == 'solve'] == ['plus', 'minus']
    assert [p for name, p in operations.calls if name == 'fit'] == ['control', 'plus', 'minus']
    assert [p for name, p in operations.calls if name == 'diagnose'] == ['control', 'plus']
    assert operations.calls.index(('freeze', 'plus')) > operations.calls.index(('save', 'minus'))
    assert operations.calls.index(('freeze', 'plus')) < operations.calls.index(('diagnose', 'plus'))
    assert result['actual_coil_endpoint'] is None and not result['physical_admission']


def test_setup_scoring_and_solves_consume_one_arm_deadline(clock, tmp_path):
    operations = Operations(clock)
    schedule.run(operations, tmp_path/'run')
    c = [row[2] for row in operations.windows if row[0] in ('C', 'control')
         and row[1] in ('setup', 'score', 'fit')]
    assert all(w == schedule.Window(1900., 2800.) for w in c)
    j = [row[2] for row in operations.windows if row[0] in ('J', 'plus', 'minus')
         and row[1] in ('setup', 'score', 'solve')]
    assert len(set(j)) == 1
    assert all(row[2].monotonic <= row[3].monotonic for row in operations.windows
               if row[1] == 'fit')


def test_control_cap_overrun_consumes_diagnostic_budget_without_reset(clock, tmp_path):
    operations = Operations(clock)
    original = operations.fit

    def fitted(arm, proposal, solved, training, window, outer):
        if proposal == 'control':
            operations.delays['fit'] = window.monotonic-clock.mono+20.
        else:
            operations.delays['fit'] = 50.
        return original(arm, proposal, solved, training, window, outer)

    operations.fit = fitted
    result = schedule.run(operations, tmp_path/'run')
    assert result['completed']
    window = next(r[2] for r in operations.windows if r[:2] == ('control', 'diagnose'))
    assert window.monotonic == 100.+1800+900


def test_joint_fit_gets_300_seconds_and_requires_300_remaining(clock, tmp_path):
    operations = Operations(clock)
    operations.delays['solve'] = 700.
    operations.delays['fit'] = 150.
    result = schedule.run(operations, tmp_path/'run')
    assert not result['completed'] and result['verdict'] == 'inconclusive'
    assert result['reason'] == 'less than 300 search seconds remain for joint fit'
    assert ('fit', 'minus') not in operations.calls
    assert not any(p == 'plus' for name, p in operations.calls if name == 'diagnose')


@pytest.mark.parametrize('operation', ['setup', 'solve', 'score', 'fit', 'freeze', 'diagnose'])
def test_late_operation_cannot_complete_or_restart_budget(clock, tmp_path, operation):
    operations = Operations(clock)
    operations.delays[operation] = 3000.
    result = schedule.run(operations, tmp_path/'run')
    assert not result['completed'] and result['verdict'] == 'inconclusive'
    assert len([x for x in operations.calls if x == ('solve', 'plus')]) <= 1
    assert len([x for x in operations.calls if x == ('solve', 'minus')]) <= 1


def test_clock_jump_is_not_an_ordinary_fit_cap(clock, tmp_path):
    operations = Operations(clock)
    original = operations.fit

    def jump(*args):
        row = original(*args)
        clock.wall += 6.
        return row

    operations.fit = jump
    result = schedule.run(operations, tmp_path/'run')
    assert not result['completed'] and result['reason'] == 'clock disagreement'
    assert not any(name == 'diagnose' for name, _ in operations.calls)


def test_generic_failure_is_not_a_numerical_rejection_or_retry(clock, tmp_path):
    operations = Operations(clock)
    operations.fault = ('solve', 'plus')
    result = schedule.run(operations, tmp_path/'run')
    assert result['verdict'] == 'inconclusive' and 'RuntimeError' in result['error']
    assert [p for name, p in operations.calls if name == 'solve'] == ['plus']


def test_two_completed_numerical_rejections_change_without_joint_diagnostics(clock, tmp_path):
    operations = Operations(clock)

    def rejected(arm, proposal, window):
        operations.step('solve', proposal)
        row = next(r for r in fixtures.proposals() if r['proposal'] == proposal)
        fixtures.reject(row, 'equilibrium')
        return dict(completed=True, rejection=row['rejection'])

    operations.solve = rejected
    result = schedule.run(operations, tmp_path/'run')
    assert result['completed'] and result['verdict'] == 'change'
    assert [p for name, p in operations.calls if name == 'diagnose'] == ['control']


def test_unfinished_solve_cannot_be_promoted_by_attached_rejection(clock, tmp_path):
    operations = Operations(clock)

    def rejected(arm, proposal, window):
        row = next(r for r in fixtures.proposals() if r['proposal'] == proposal)
        fixtures.reject(row, 'equilibrium')
        return dict(completed=False, rejection=row['rejection'])

    operations.solve = rejected
    result = schedule.run(operations, tmp_path/'run')
    assert not result['completed'] and result['reason'] == 'unfinished equilibrium operation'


def test_freeze_crossing_joint_search_deadline_cannot_start_diagnostics(clock, tmp_path):
    operations = Operations(clock)
    original = operations.freeze

    def late(arm, proposal, solved, training, fit, window):
        if proposal != 'control':
            clock.advance(window.monotonic-clock.mono+1.)
        return original(arm, proposal, solved, training, fit, window)

    operations.freeze = late
    result = schedule.run(operations, tmp_path/'run')
    assert not result['completed']
    assert [p for name, p in operations.calls if name == 'diagnose'] == ['control']


def test_final_source_failure_prevents_completed_comparison(clock, tmp_path):
    operations = Operations(clock)
    original = operations.verify

    def changed(arm):
        original(arm)
        if arm.name == 'C' and 'plus' in operations.states:
            raise ValueError('changed original control source')

    operations.verify = changed
    result = schedule.run(operations, tmp_path/'run')
    assert not result['completed'] and 'changed original control source' in result['error']


def test_late_normal_joint_fit_return_is_not_an_ordinary_cap(clock, tmp_path):
    operations = Operations(clock)
    original = operations.fit

    def late(arm, proposal, solved, training, window, outer):
        result = original(arm, proposal, solved, training, window, outer)
        if proposal == 'plus':
            clock.advance(window.monotonic-clock.mono+1.)
            result['stop'] = 'solver-return'
            result['search']['status']['reason'] = 'solver-return'
        return result

    operations.fit = late
    result = schedule.run(operations, tmp_path/'run')
    assert not result['completed'] and result['reason'] == 'deadline'
    assert ('solve', 'minus') not in operations.calls
