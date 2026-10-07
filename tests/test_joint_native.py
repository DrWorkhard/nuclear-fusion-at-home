"""Native operation handoff and resource failures, without running an experiment."""
import copy
import json
from types import SimpleNamespace

import pytest
import test_joint_schedule as timing

from fusion_baselines import joint_native as native


@pytest.fixture
def clock(monkeypatch):
    clock = timing.Clock()
    monkeypatch.setattr(native.time, 'monotonic', lambda: clock.mono)
    monkeypatch.setattr(native.time, 'time', lambda: clock.wall)
    return clock


def request(tmp_path, clock, operation='fit'):
    return dict(operation=operation, proposal='control', revision='pin', arm_root=str(tmp_path),
                sources={}, clock_origin=[clock.mono, clock.wall],
                window=dict(monotonic=clock.mono+300, wall=clock.wall+300),
                outer=dict(monotonic=clock.mono+1800, wall=clock.wall+1800))


def test_recorders_distinguish_fit_cap_from_hard_resource_interruption(tmp_path, clock):
    record = native.Recorder(tmp_path/'fit', request(tmp_path, clock))
    clock.advance(300)
    with pytest.raises(native.FitCap):
        record.guard()
    assert record.cap_reached
    record.finalizing = True
    record.guard()
    clock.advance(1500)
    with pytest.raises(native.schedule.ArmInterrupted, match='deadline'):
        record.guard()


def test_cumulative_clock_jump_is_never_a_fit_cap(tmp_path, clock):
    record = native.Recorder(tmp_path/'fit', request(tmp_path, clock))
    clock.wall += 6
    with pytest.raises(native.schedule.ArmInterrupted, match='arm-wide clock'):
        record.guard()
    assert not record.cap_reached


def test_interior_request_interface_and_shared_storage_are_usable(tmp_path, clock):
    record = native.InteriorRecorder(tmp_path/'interior', request(tmp_path, clock, 'diagnostics'))
    value = record.request('B', 3, lambda: [1, 2, 3])
    assert value == [1, 2, 3] and record.points['B']['completed'] == 3
    assert record.counts['B']['completed'] == 1
    child = record.child('child')
    child.save('data', b'abc')
    assert child.storage is record.storage and record.storage[0] >= 3


def configured(tmp_path, monkeypatch):
    env = tmp_path/'environment.json'
    native.solver.save(env, {'native': True})
    monkeypatch.setattr(native.solver, 'identity', lambda packages=None: {'native': True})
    return native.Operations(seed=tmp_path/'seed', wout=tmp_path/'wout',
        solver_python=tmp_path/'python', solver_environment=env,
        solver_environment_sha256=native.solver.digest(env), native_environment=env,
        native_environment_sha256=native.solver.digest(env), revision='pin')


@pytest.mark.parametrize('fault', ['none', 'request', 'receipt', 'incomplete', 'environment',
                                  'late'])
def test_parent_admits_only_bound_completed_supervised_operation(
        tmp_path, clock, monkeypatch, fault):
    operations = configured(tmp_path, monkeypatch)
    arm = native.schedule.Arm(tmp_path/'C', 'C')
    operations.states['C'] = dict(sources={})
    seen = []

    def supervised(command, folder, arm_root, mono, wall, clock_origin=None):
        seen.append((mono, wall, clock_origin))
        path = folder/'request.json'
        report = dict(completed=fault != 'incomplete', request_sha256=native.solver.digest(path),
            operation='score', proposal='control', sources_unchanged=True,
            environment_unchanged=fault != 'environment', result={'scored': True})
        if fault == 'request':
            path.write_text(path.read_text(encoding='utf-8')+' ', encoding='utf-8')
        elif fault == 'receipt':
            report['request_sha256'] = 'f'*64
        elif fault == 'late':
            clock.advance(1801)
        (folder/'run').mkdir()
        native.solver.save(folder/'run/result.json', report)
        return dict(completed=True, returncode=0, stop_reason=None)

    monkeypatch.setattr(native.solver, 'supervise', supervised)
    if fault == 'none':
        assert operations.score(arm, 'control', None, arm.search) == {'scored': True}
        assert len(operations.states['C']['sources']) == 3
    else:
        with pytest.raises((ValueError, native.schedule.ArmInterrupted)):
            operations.score(arm, 'control', None, arm.search)
    assert seen == [(arm.search.monotonic, arm.search.wall, [arm.started, arm.wall_started])]


@pytest.mark.parametrize('fault', ['none', 'source', 'request', 'environment', 'software', 'clock'])
def test_worker_checks_sources_environment_and_budget_after_operation(
        tmp_path, clock, monkeypatch, fault):
    config = request(tmp_path, clock, 'score')
    env = tmp_path/'environment.json'
    native.solver.save(env, {'native': True})
    source = tmp_path/'source.py'
    source.write_text('original', encoding='utf-8')
    config.update(native_environment=str(env), sources={str(source): native.solver.digest(source)})
    path = tmp_path/'request.json'
    native.solver.save(path, config)
    monkeypatch.setattr(native, 'build_run_record', lambda _: dict(repository=dict(
        commit='pin', dirty=False)))
    identities = [{'native': True}, {'native': fault != 'environment'}]
    monkeypatch.setattr(native.solver, 'identity', lambda packages=None: identities.pop(0))

    def score(request, record):
        if fault == 'source':
            source.write_text('changed', encoding='utf-8')
        elif fault == 'request':
            path.write_text(path.read_text(encoding='utf-8')+' ', encoding='utf-8')
        elif fault == 'software':
            raise ValueError('unclassified software failure')
        elif fault == 'clock':
            clock.wall += 6
        return {'score': 1.}

    monkeypatch.setattr(native, 'score', score)
    code = native.worker(path)
    report = json.loads((tmp_path/'run/result.json').read_text(encoding='utf-8'))
    assert report['completed'] == (fault == 'none')
    assert code == (0 if fault == 'none' else 1)
    assert not report['physical_admission']
    if fault != 'none':
        assert 'result' not in report and 'error' in report


def test_fit_source_failure_does_not_hide_behind_an_ordinary_cap(tmp_path, clock, monkeypatch):
    req = request(tmp_path, clock)
    req.update(seed=str(tmp_path/'seed.json'), wout=str(tmp_path/'wout.nc'))
    record = native.Recorder(tmp_path/'fit', req)
    source = tmp_path/'source'
    source.write_text('before', encoding='utf-8')
    sources = {str(source): native.solver.digest(source)}
    seed = {'order': 5}
    native.solver.save(tmp_path/'seed.json', seed)
    monkeypatch.setattr(native.coil, 'SEED_SHA', native.solver.digest(tmp_path/'seed.json'))
    monkeypatch.setattr(native.target, 'intake', lambda *args: ({}, {}, sources, {}))
    monkeypatch.setattr(native.check, 'snapshot_identity', lambda *args: None)
    monkeypatch.setattr(native.fit, 'Model', lambda *args: SimpleNamespace())

    def search(*args):
        clock.advance(300)
        try:
            record.guard()
        except native.FitCap:
            pass
        source.write_text('after', encoding='utf-8')
        return dict(startup_pass=False, selected=None, status={'reason': 'budget'})

    monkeypatch.setattr(native.fit, 'search', search)
    with pytest.raises(ValueError, match='source/input changed'):
        native.search(req, record)


def test_registered_proposal_serialization_matches_frozen_hashes(tmp_path):
    original = native.check.read_json(native.check.ROOT/native.check.TARGET)
    for proposal in ('plus', 'minus'):
        data = copy.deepcopy(original)
        row = next(r for r in data['rbc'] if (r['m'], r['n']) == (2, 1))
        row['value'] += native.target.DELTAS[proposal]
        path = tmp_path/f'{proposal}.json'
        native.solver.save(path, data)
        assert native.solver.digest(path) == native.target.INPUT_HASHES[proposal]


def test_solver_launch_preserves_virtual_environment_symlink(tmp_path, monkeypatch):
    operations = configured(tmp_path, monkeypatch)
    launcher = tmp_path/'python'
    launcher.symlink_to(native.sys.executable)
    assert operations.config['solver_python'] == str(launcher)
    assert launcher.resolve() != launcher


def test_original_arm_clock_is_checked_before_any_child_launch(tmp_path, clock, monkeypatch):
    origin = [clock.mono, clock.wall]
    clock.wall += 6
    monkeypatch.setattr(native.solver.subprocess, 'Popen', lambda *a, **k: pytest.fail('launched'))
    result = native.solver.supervise([], tmp_path, tmp_path,
        clock.mono+300, clock.wall+300, clock_origin=origin)
    assert not result['completed'] and result['stop_reason'] == 'arm-wide clock disagreement'


def cold_result(operations, input_path, proposal, folder, fault='none'):
    """Synthetic native output: only costly VMEC is replaced, not the receipt handoff."""
    folder.mkdir()
    (folder/'input.json').write_bytes(input_path.read_bytes())
    (folder/'wout.nc').write_bytes(proposal.encode())
    native.solver.save(folder/'request.json', {
        'environment_sha256': operations.config['solver_environment_sha256']})
    failed = fault != 'none'
    report = dict(completed=fault != 'software', converged=not failed, proposal=proposal,
        request_sha256=native.solver.digest(folder/'request.json'),
        input_sha256=native.target.INPUT_HASHES[proposal],
        environment_sha256=operations.config['solver_environment_sha256'],
        environment_unchanged=fault != 'environment', sources_unchanged=True,
        input_roundtrip_exact=True, output_input_exact=True,
        wout_sha256=native.solver.digest(folder/'wout.nc'), ns=401, ier_flag=0,
        residuals=dict(fsqr=1e-9 if failed else 1e-14, fsqz=1e-14, fsql=1e-14))
    if fault == 'contradictory':
        report['converged'] = True
    native.solver.save(folder/'solver.json', report)
    parent = dict(completed=not failed, request_sha256=report['request_sha256'],
        sources_before={str(folder/'input.json'): report['input_sha256']},
        process=dict(returncode=1 if failed else 0, stop_reason='deadline'
                     if fault == 'resource' else None))
    native.solver.save(folder/'parent.json', parent)
    parent['record_sha256'] = native.solver.digest(folder/'parent.json')
    if fault == 'source':
        (folder/'input.json').write_bytes(b'changed')
    return parent


@pytest.mark.parametrize('fault', ['none', 'nonconvergence', 'software', 'environment',
                                  'contradictory', 'resource', 'source'])
def test_cold_solver_handoff_requires_completed_bound_failure(
        tmp_path, clock, monkeypatch, fault):
    operations = configured(tmp_path, monkeypatch)
    arm = native.schedule.Arm(tmp_path/'J', 'J')
    operations.states['J'] = dict(sources={}, solved={})
    calls = []

    def solve(python, input_path, proposal, env, sha, folder, root, revision, mono, wall,
              clock_origin=None):
        calls.append((proposal, clock_origin, mono, wall))
        return cold_result(operations, input_path, proposal, folder, fault)

    monkeypatch.setattr(native.solver, 'run_solver', solve)
    monkeypatch.setattr(native.target, 'volume', lambda data, n: 1.)
    if fault in ('none', 'nonconvergence'):
        result = operations.solve(arm, 'plus', arm.search)
        assert result['completed']
        assert (result['rejection'] is None) == (fault == 'none')
        assert operations.states['J']['solved']['plus'] == result
    else:
        with pytest.raises(ValueError):
            operations.solve(arm, 'plus', arm.search)
        assert not operations.states['J']['solved']
    assert calls == [('plus', [arm.started, arm.wall_started],
                       arm.search.monotonic, arm.search.wall)]


@pytest.mark.parametrize('fault', ['none', 'request', 'late', 'source'])
def test_assembled_schedule_parent_worker_freeze_and_verdict(
        tmp_path, clock, monkeypatch, fault):
    import test_joint_decision as fixtures

    operations = configured(tmp_path, monkeypatch)
    seed = fixtures.fixtures.snapshot.__wrapped__()
    native.solver.save(tmp_path/'seed', seed)
    (tmp_path/'wout').write_bytes(b'control')
    monkeypatch.setattr(native.coil, 'SEED_SHA', native.solver.digest(tmp_path/'seed'))
    monkeypatch.setitem(native.check.FIXED, native.check.WOUT,
                        native.solver.digest(tmp_path/'wout'))
    monkeypatch.setattr(native, 'build_run_record', lambda _: dict(repository=dict(
        commit='pin', dirty=False)))
    monkeypatch.setattr(native.target, 'volume', lambda data, n: 1.)
    calls = []

    def solve(python, input_path, proposal, env, sha, folder, root, revision, mono, wall,
              clock_origin=None):
        calls.append(('solve', proposal))
        clock.advance(10)
        return cold_result(operations, input_path, proposal, folder)

    def score(req, record):
        row = fixtures.score(req['proposal'])
        if req['proposal'] != 'control':
            row['identity'].update(wout_sha256=native.solver.digest(req['solved']['wout']),
                                  parent_sha256=req['solved']['parent']['record_sha256'])
        return row

    def search(req, record):
        snapshot = copy.deepcopy(seed)
        if req['proposal'] != 'control':
            snapshot.update(target_id=req['training']['identity']['target_id'],
                            joint_target_binding=copy.deepcopy(req['training']['identity']))
        return dict(snapshot=snapshot, search=fixtures.search(snapshot),
                    stop='solver-return', window=req['window'])

    def diagnostics(req, record):
        frozen = req['frozen']
        # The real freeze must already exist before the first diagnostic request.
        assert (native.check.Path(req['arm_root'])/'selection/frozen-selection.json').exists()
        report = fixtures.diagnostics(frozen)
        if req['proposal'] != 'control':
            context = dict(binding=frozen['identity'],
                           canonical_snapshot_sha256=frozen['canonical_snapshot_sha256'])
            for row in [*report['fine'], *report['interior'], report['geometry'], report['trace']]:
                row['joint_target'] = copy.deepcopy(context)
        for mode in ('holdout', 'holdout-refined'):
            row = fixtures.score(req['proposal'], mode,
                                 amplitude=.1 if req['proposal'] == 'control' else .095)
            row['identity'] = copy.deepcopy(frozen['identity'])
            report[mode] = row
        report['budget_complete'] = False
        return report

    def supervised(command, folder, root, mono, wall, clock_origin=None):
        path = folder/'request.json'
        req = native.solver.read(path)
        calls.append((req['operation'], req['proposal']))
        clock.advance(5)
        code = native.worker(path)
        if req['proposal'] == 'plus' and req['operation'] == 'diagnostics':
            if fault == 'request':
                path.write_bytes(path.read_bytes()+b' ')
            elif fault == 'late':
                clock.advance(mono-clock.mono+1)
            elif fault == 'source':
                (tmp_path/'wout').write_bytes(b'changed original control')
        return dict(completed=code == 0, returncode=code, stop_reason=None)

    monkeypatch.setattr(native.solver, 'run_solver', solve)
    monkeypatch.setattr(native.solver, 'supervise', supervised)
    monkeypatch.setattr(native, 'score', score)
    monkeypatch.setattr(native, 'search', search)
    monkeypatch.setattr(native, 'diagnostics', diagnostics)
    result = native.schedule.run(operations, tmp_path/'run')
    assert result['completed'] == (fault == 'none'), result
    assert result['verdict'] == ('continue' if fault == 'none' else 'inconclusive'), result
    assert result['actual_coil_endpoint'] is None and not result['physical_admission']
    assert calls == [('score', 'control'), ('fit', 'control'), ('diagnostics', 'control'),
                     ('solve', 'plus'), ('score', 'plus'), ('fit', 'plus'),
                     ('solve', 'minus'), ('score', 'minus'), ('fit', 'minus'),
                     ('diagnostics', 'plus')]
    saved = native.solver.read(tmp_path/'run/comparison.json')
    assert saved == result


def test_reference_diagnostics_use_original_intake_and_shared_checks(
        tmp_path, clock, monkeypatch):
    import test_joint_decision as fixtures

    snapshot = fixtures.fixtures.snapshot.__wrapped__()
    frozen = dict(proposal='control', identity=fixtures.score()['identity'], snapshot=snapshot,
        selected_index=12, sources={}, canonical_snapshot_sha256=
        native.decision.canonical_sha(snapshot))
    frozen['selection_sha256'] = native.decision.canonical_sha(frozen)
    req = request(tmp_path, clock, 'diagnostics')
    req.update(frozen=frozen, wout=str(tmp_path/'original-wout'))
    record = native.Recorder(tmp_path/'diagnostics', req)
    data, targets, numerical = object(), {32: object(), 64: object()}, object()
    seen = []

    def intake(input_path, wout, proposal, expected, guard):
        assert input_path == native.check.ROOT/native.check.TARGET
        assert wout == req['wout'] and proposal == 'control'
        assert expected == native.check.FIXED[native.check.WOUT]
        guard()
        seen.append('original-intake')
        return data, targets, {}, numerical

    def fine(seed, passed, chosen, recorder, shift):
        assert seed == snapshot and passed is data
        assert chosen['metrics']['scale'] == snapshot['scale']
        recorder.call('B', lambda: None)
        seen.append(('fine', shift))
        return dict(shift=shift)

    def interior(seed, passed, arrays, n, nodes, recorder, constants):
        assert seed == snapshot and passed is data and arrays is targets[n]
        assert constants == dict(B2=native.check.B2, flux=native.check.TARGET_FLUX)
        recorder.request('B', 3, lambda: None)
        seen.append(('interior', n, nodes))
        return dict(ninner=n, ncoil=nodes), {'B': [1., 2., 3.]}

    def trace(seed, passed, wout, context, recorder):
        assert seed == snapshot and passed is data and str(wout) == req['wout']
        assert context['binding'] == frozen['identity'] and context['intake'] is numerical
        recorder.call('B', lambda: None)
        seen.append('trace')
        return {'traced': True}

    def holdout(wout, mode, recorder):
        assert str(wout) == req['wout']
        seen.append(mode)
        return {'mode': mode}

    monkeypatch.setattr(native.target, 'intake', intake)
    monkeypatch.setattr(native.fit, 'fine', fine)
    monkeypatch.setattr(native.check, 'geometry', lambda *a: {'geometry': True})
    monkeypatch.setattr(native.check, '_screen_level', interior)
    monkeypatch.setattr(native.check, 'refinements', lambda rows: {'refined': True})
    monkeypatch.setattr(native.coil, '_direct_trace', trace)
    monkeypatch.setattr(native.action, 'score_reference', holdout)
    monkeypatch.setattr(native.solver, 'intake_result', lambda *a: pytest.fail('joint admission'))
    report = native.diagnostics(req, record)
    assert report['completed'] and not report['budget_complete']
    assert seen == ['original-intake', ('fine', 0.), ('fine', .5),
                    ('interior', 32, 256), ('interior', 64, 256), ('interior', 64, 512),
                    'trace', 'holdout', 'holdout-refined']
    assert sum(c['B']['completed'] for c in record.components.values()) == 6
    assert set(native.check.TARGETS) == {'reference401', 'selected401'}
