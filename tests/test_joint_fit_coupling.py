"""Fixed target admission, trusted fine metrics and bounded paired fitting decisions."""
import copy
from types import SimpleNamespace

import pytest
import test_coil_check as coils
import test_joint_decision as fixtures
import test_joint_schedule as timing

from fusion_baselines import joint_fit_coupling as coupling


def frozen(proposal='control'):
    snapshot = coils.snapshot.__wrapped__()
    training = fixtures.score(proposal)
    if proposal != 'control':
        fixed = coupling.coil.coupling_registration()['candidate']
        training['identity'].update({k: fixed[k] for k in coupling.coil.BINDING_KEYS})
        snapshot.update(target_id=fixed['target_id'],
                        joint_target_binding={k: fixed[k] for k in coupling.coil.BINDING_KEYS})
    result = dict(proposal=proposal, snapshot=snapshot, identity=training['identity'],
                  selected_index=12, sources={}, training_score=training['score'],
                  canonical_snapshot_sha256=coupling.decision.canonical_sha(snapshot))
    result['selection_sha256'] = coupling.decision.canonical_sha(result)
    return result


def diagnostics(selected):
    report = fixtures.diagnostics(selected)
    for row in report['fine']:
        row['metrics']['flux_relative_error'] = 0.
    for key in ('interior', 'trace', 'holdout', 'holdout-refined'):
        del report[key]
    report.update(interior_tested=False, tracing_tested=False)
    if selected['proposal'] != 'control':
        context = dict(binding={k: selected['identity'][k] for k in coupling.coil.BINDING_KEYS},
                       canonical_snapshot_sha256=selected['canonical_snapshot_sha256'])
        for row in [*report['fine'], report['geometry']]:
            row['joint_target'] = copy.deepcopy(context)
    return report


def test_exact_registered_candidate_only_and_public_registry_stays_closed():
    selected = frozen('scale035')
    binding = selected['snapshot']['joint_target_binding']
    coupling.coil.snapshot_identity(selected['snapshot'], binding)
    assert set(coupling.check.TARGETS) == {'reference401', 'selected401'}
    with pytest.raises(ValueError):
        coupling.check.snapshot_identity(selected['snapshot'])
    for key in coupling.coil.BINDING_KEYS:
        changed = copy.deepcopy(selected['snapshot'])
        changed['joint_target_binding'][key] = 'c'*64
        with pytest.raises(ValueError):
            coupling.coil.snapshot_identity(changed, changed['joint_target_binding'])


def test_protocol_budgets_and_seed_remain_frozen():
    p = coupling.coil.coupling_registration()
    assert coupling.check.digest(coupling.check.ROOT/coupling.coil.COUPLING_PROTOCOL) == (
        coupling.coil.COUPLING_SHA)
    assert p['order'] == list(coupling.ORDER)
    assert p['seed']['sha256'] == coupling.coil.SEED_SHA
    assert p['fit']['seconds_per_arm'] == coupling.FIT_SECONDS == 300
    assert p['diagnostics']['total_arm_seconds'] == coupling.ARM_SECONDS == 600
    assert p['budget']['total_seconds_max'] == coupling.TOTAL_SECONDS == 1200


@pytest.mark.parametrize('proposal', ['control', 'scale035'])
def test_fine_summary_is_not_physical_acceptance(proposal):
    selected = frozen(proposal)
    result = coupling.summary(selected, diagnostics(selected))
    assert result['boundary_rms'] == .003 and result['geometry_pass']
    assert not result['normal_rms_limit_met'] and not result['normal_max_limit_met']
    assert not result['interior_tested'] and not result['tracing_tested']
    assert not result['physical_admission']


@pytest.mark.parametrize('fault', ['selection', 'snapshot', 'fine', 'numerical', 'nan',
                                  'current', 'flux-claim', 'unresolved', 'target-context'])
def test_untrustworthy_or_incomplete_diagnostics_cannot_classify_fitting(fault):
    selected = frozen('scale035')
    report = diagnostics(selected)
    if fault == 'selection':
        report['selection_sha256'] = 'changed'
    elif fault == 'snapshot':
        selected['snapshot']['scale'] *= 1.01
    elif fault == 'fine':
        report['fine'].pop()
    elif fault == 'numerical':
        report['fine'][0]['independent_errors']['B'] = 1e-5
    elif fault == 'nan':
        report['fine'][0]['metrics']['normal_rms'] = float('nan')
    elif fault == 'current':
        report['fine'][0]['metrics']['current'] *= 1.01
    elif fault == 'flux-claim':
        report['fine'][0]['metrics']['flux_limit_met'] = False
    elif fault == 'unresolved':
        report['geometry']['status'] = 'unresolved'
    else:
        report['geometry']['joint_target']['binding']['wout_sha256'] = 'changed'
    with pytest.raises(ValueError):
        coupling.summary(selected, report)


def test_registered_screen_and_absolute_limits_remain_distinct():
    arms = {}
    for p in coupling.ORDER:
        selected = frozen(p)
        arms[p] = dict(completed=True, no_eligible_candidate=False,
                       summary=coupling.summary(selected, diagnostics(selected)))
    result = coupling.classify(arms)
    assert result['verdict'] == 'boundary-fitting-nonregression'
    assert not result['candidate']['normal_rms_limit_met']
    arms['scale035']['summary']['boundary_rms'] *= 1.11
    assert coupling.classify(arms)['verdict'] == 'negative'
    arms['scale035']['no_eligible_candidate'] = True
    assert coupling.classify(arms)['rejected_arms'] == ['scale035']


def test_early_completion_cap_and_outer_bounds_control_diagnostic_window():
    fit = dict(monotonic=400., wall=1300.)
    outer = dict(monotonic=700., wall=1600.)
    assert coupling.diagnostic_deadline((200., 1100.), fit, outer) == dict(
        monotonic=500., wall=1400.)
    assert coupling.diagnostic_deadline((401., 1301.), fit, outer) == outer
    assert coupling.diagnostic_deadline((401., 1301.), fit,
        dict(monotonic=690., wall=1590.)) == dict(monotonic=690., wall=1590.)


def assembled(tmp_path, monkeypatch, fault=None):
    clock = timing.Clock()
    origin = clock.mono, clock.wall
    monkeypatch.setattr(coupling.time, 'monotonic', lambda: clock.mono)
    monkeypatch.setattr(coupling.time, 'time', lambda: clock.wall)
    monkeypatch.setattr(coupling.solver.shutil, 'disk_usage',
                        lambda path: SimpleNamespace(free=10*1024**3))
    config = dict(seed='original-seed', native_environment='native-lock',
                  reference_wout='reference-wout', candidate_folder='candidate')
    fixed = coupling.coil.coupling_registration()['candidate']
    parent = dict(wout_sha256=fixed['wout_sha256'], record_sha256=fixed['parent_sha256'])
    calls, prepares, windows = [], [], []

    def prepare(*args):
        prepares.append('prepare')
        clock.advance(300 if fault == 'setup' else 5)
        return config, parent, {}, {}

    monkeypatch.setattr(coupling, 'prepare', prepare)
    monkeypatch.setattr(coupling.screen, 'verify', lambda config, sources, guard: guard())

    def freeze(proposal, training, search, ordinary, snapshot, input_path, wout, record):
        row = frozen(proposal)
        assert row['snapshot'] == snapshot
        record.save('frozen-selection.json', row)
        return row

    monkeypatch.setattr(coupling.decision, 'freeze_selection', freeze)
    # The synthetic prepare still supplies both complete training rows to the parent.
    raw_prepare = prepare

    def prepared(*args):
        c, p, _, provenance = raw_prepare(*args)
        return c, p, {p: fixtures.score(p) for p in coupling.ORDER}, provenance

    monkeypatch.setattr(coupling, 'prepare', prepared)

    def supervise(command, folder, output, mono, wall, clock_origin=None):
        request_path = folder/'request.json'
        request = coupling.solver.read(request_path)
        p, op = request['proposal'], request['operation']
        calls.append((p, op))
        windows.append((p, op, request['window'], request['outer']))
        assert (mono, wall) == (request['outer']['monotonic'], request['outer']['wall'])
        assert clock_origin == origin and request['clock_origin'] == list(origin)
        assert request['arm_root'] == str(output)
        if op == 'fit':
            selected = frozen(p)
            search = fixtures.search(selected['snapshot'])
            cap = fault == 'fit-cap'
            if cap:
                search['status']['reason'] = 'budget'
                clock.advance(request['window']['monotonic']-clock.mono+1)
            else:
                clock.advance(40)
            snapshot = selected['snapshot']
            if fault == 'no-candidate':
                search['selected'], snapshot = None, None
            if fault == 'startup':
                search['startup_pass'] = False
            row = dict(search=search, snapshot=snapshot, cap_reached=cap,
                       stop='fit-cap' if cap else 'solver-return', window=request['window'])
            if fault == 'fit-window':
                row['window'] = dict(monotonic=mono+1, wall=wall+1)
        else:
            assert op == 'boundary-screen'
            row = diagnostics(request['frozen'])
            clock.advance(301 if fault == 'late-diagnostics' else 60)
            if fault == 'numerical':
                row['fine'][0]['checks_pass'] = False
        if fault == 'clock-jump':
            clock.wall += 6
        (folder/'run').mkdir()
        receipt = dict(completed=True, operation=op, proposal=p, result=row,
                       request_sha256=coupling.solver.digest(request_path),
                       sources_unchanged=True, environment_unchanged=True)
        if fault == 'receipt':
            receipt['request_sha256'] = 'changed'
        coupling.solver.save(folder/'run/result.json', receipt)
        return dict(completed=fault != 'process', returncode=0, stop_reason=None)

    monkeypatch.setattr(coupling.solver, 'supervise', supervise)
    if fault == 'final-save':
        save = coupling.solver.save

        def late_save(path, value):
            save(path, value)
            if path.name == 'screen.json' and value['completed']:
                clock.advance(600)

        monkeypatch.setattr(coupling.solver, 'save', late_save)
    result = coupling.run(tmp_path/'config.json', tmp_path/'output', 'a'*40, origin)
    return result, calls, prepares, windows, coupling.solver.read(tmp_path/'output/screen.json')


@pytest.mark.parametrize('fault', [None, 'fit-cap', 'no-candidate'])
def test_two_fresh_fits_are_charged_and_only_declared_diagnostics_run(tmp_path, monkeypatch, fault):
    result, calls, prepares, windows, saved = assembled(tmp_path, monkeypatch, fault)
    assert result == saved and result['completed'] and len(prepares) == 2
    ops = ['fit'] if fault == 'no-candidate' else ['fit', 'boundary-screen']
    assert calls == [(p, op) for p in coupling.ORDER for op in ops]
    assert result['verdict'] == ('negative' if fault == 'no-candidate'
                                 else 'boundary-fitting-nonregression')
    assert not result['coil_feasibility_established'] and not result['physical_admission']
    for p, arm in result['arms'].items():
        window = next(w for proposal, op, w, outer in windows if proposal == p and op == 'fit')
        assert arm['diagnostic_deadline']['monotonic'] == min(
            arm['fit_finished'][0], window['monotonic'])+300


@pytest.mark.parametrize('fault', ['setup', 'startup', 'receipt', 'process', 'clock-jump',
                                  'late-diagnostics', 'numerical', 'final-save', 'fit-window'])
def test_untrustworthy_missing_or_late_work_never_passes_or_retries(tmp_path, monkeypatch, fault):
    result, calls, prepares, windows, saved = assembled(tmp_path, monkeypatch, fault)
    assert result == saved and not result['completed'] and result['verdict'] == 'inconclusive'
    assert len(calls) == len(set(calls)) and len(prepares) <= 2
    if fault == 'setup':
        assert not calls
