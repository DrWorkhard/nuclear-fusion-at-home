"""One registered paired fitting-burden screen; no complete coil acceptance claim."""
import sys
import time
from pathlib import Path

import numpy as np

from fusion_baselines import joint_step_scale as screen

native, solver, check, decision = screen.native, screen.solver, screen.check, screen.decision
coil, target = native.coil, screen.target
ORDER, FIT_SECONDS, ARM_SECONDS, TOTAL_SECONDS = ('control', 'scale035'), 300, 600, 1200
CONFIG_KEYS = {'revision', 'seed', 'candidate_folder', 'reference_wout',
               'control_training', 'candidate_training', 'validation_report',
               'native_environment', 'native_environment_sha256'}


def boundary_checks(request, record):
    """Reuse numerical fine fields and continuous geometry; no interior or tracing."""
    frozen, proposal = request['frozen'], request['proposal']
    check.need(proposal in ORDER, 'registered fitting-screen target required')
    check.need(frozen['selection_sha256'] == decision.canonical_sha(
        {k: v for k, v in frozen.items() if k != 'selection_sha256'}), 'changed selection')
    snapshot = frozen['snapshot']
    decision.snapshot_identity(proposal, frozen['identity'], snapshot)
    control = proposal == 'control'
    if control:
        data, _, context = native.reference_context(frozen, request, record)
    else:
        solved = request['solved']
    report = dict(completed=False, selection_sha256=frozen['selection_sha256'], fine=[],
                  interior_tested=False, tracing_tested=False, physical_admission=False)
    fine = record.child('fine')
    chosen = dict(index=frozen['selected_index'],
                  x=np.asarray(snapshot['base_coefficients']).ravel(),
                  metrics=dict(scale=snapshot['scale'], unit_flux=snapshot['unit_flux']))
    for shift in (0., .5):
        row = (native.fit.fine(snapshot, data, chosen, fine, shift) if control else
               coil.boundary(snapshot, solved['folder'], solved['parent'], shift,
                             frozen['selected_index'], fine))
        report['fine'].append(row)
        record.save('progress.json', report)
    report['geometry'] = (check.geometry(snapshot, data, record.guard) if control else
                         coil.geometry(snapshot, solved['folder'], solved['parent'], record))
    if control:
        solver.check_sources(context['sources'])
    record.guard()
    report['completed'] = True
    return report


def summary(frozen, report):
    """Caller independently binds the worker receipt and verifies its original deadlines."""
    check.need(frozen['selection_sha256'] == decision.canonical_sha(
        {k: v for k, v in frozen.items() if k != 'selection_sha256'}), 'changed frozen selection')
    decision.snapshot_identity(frozen['proposal'], frozen['identity'], frozen['snapshot'])
    check.need(decision.canonical_sha(frozen['snapshot']) == frozen['canonical_snapshot_sha256']
               and report['completed'] and report['selection_sha256'] == frozen['selection_sha256'],
               'completed diagnostics for the exact frozen snapshot required')
    rows = report['fine']
    check.need([r['shift'] for r in rows] == [0., .5]
               and all(r['n'] == 128 and r['nodes'] == 512 for r in rows),
               'both registered fine grids required')
    scale = frozen['snapshot']['scale']
    if frozen['proposal'] != 'control':
        binding = {k: frozen['identity'][k] for k in coil.BINDING_KEYS}
        for row in [*rows, report['geometry']]:
            context = row['joint_target']
            check.need(context['binding'] == binding and context['canonical_snapshot_sha256']
                       == frozen['canonical_snapshot_sha256'], 'diagnostic target/snapshot differs')
    for row in rows:
        errors, metrics = row['independent_errors'], row['metrics']
        check.need(row['checks_pass'] and set(errors) == {'B', 'A'}
                   and np.isfinite(list(errors.values())).all()
                   and min(errors.values()) >= 0 and max(errors.values()) <= 1e-12,
                   'independent numerical fine checks failed')
        check.need(metrics['frozen_scale'] == scale and metrics['current'] == 1e5*scale,
                   'fine current differs from frozen selection')
        values = [metrics[k] for k in ('normal_rms', 'normal_max', 'flux_relative_error')]
        check.need(np.isfinite(values).all() and min(values) >= 0,
                   'finite nonnegative fine metrics required')
        check.need(metrics['flux_limit_met'] == (metrics['flux_relative_error'] <= 1e-6),
                   'flux verdict differs from recorded metric')
    geometry = report['geometry']['status']
    check.need(geometry in ('pass', 'fail'), 'unresolved geometry is inconclusive')
    rms = max(r['metrics']['normal_rms'] for r in rows)
    maximum = max(r['metrics']['normal_max'] for r in rows)
    return dict(boundary_rms=rms, normal_max=maximum, geometry_pass=geometry == 'pass',
                current_pass=abs(1e5*scale) <= 500000,
                flux_pass=all(r['metrics']['flux_limit_met'] for r in rows),
                normal_rms_limit_met=rms <= 1e-4, normal_max_limit_met=maximum <= 1e-3,
                interior_tested=False, tracing_tested=False, physical_admission=False)


def classify(arms):
    check.need(list(arms) == list(ORDER) and all(r['completed'] for r in arms.values()),
               'both completed fitting arms required')
    rejected = [p for p, row in arms.items() if row['no_eligible_candidate']]
    if rejected:
        return dict(verdict='negative', reason='normal fit returned no eligible candidate',
                    rejected_arms=rejected)
    c, s = [arms[p]['summary'] for p in ORDER]
    checks = dict(boundary_nonregression=s['boundary_rms'] <= 1.1*c['boundary_rms'])
    for key in ('geometry_pass', 'current_pass', 'flux_pass'):
        checks[key] = bool(c[key] and s[key])
    return dict(verdict='boundary-fitting-nonregression' if all(checks.values()) else 'negative',
                checks=checks, boundary_ratio=s['boundary_rms']/c['boundary_rms']
                if c['boundary_rms'] > 0 else None, control=c, candidate=s)


def prepare(config_path, revision, sources, guard):
    guard()
    check.bind(config_path, solver.digest(config_path), sources)
    config = solver.read(config_path)
    check.need(set(config) == CONFIG_KEYS and config['revision'] == revision
               and len(revision) == 40, 'exact reviewed fitting configuration required')
    provenance = native.build_run_record(check.ROOT)
    check.need(provenance['repository']['commit'] == revision
               and not provenance['repository']['dirty'], 'clean reviewed fitting screen required')
    protocol = coil.coupling_registration(sources)
    check.need(protocol['fit']['seconds_per_arm'] == FIT_SECONDS
               and protocol['diagnostics']['total_arm_seconds'] == ARM_SECONDS
               and protocol['budget']['total_seconds_max'] == TOTAL_SECONDS,
               'registered fitting allowances required')
    candidate = protocol['candidate']
    folder = Path(config['candidate_folder'])
    target.registered_input(folder/'input.json', 'scale035', sources)
    check.bind(folder/'wout.nc', candidate['wout_sha256'], sources)
    check.bind(folder/'parent.json', candidate['parent_sha256'], sources)
    parent = solver.read(folder/'parent.json')
    check.need(parent['completed'] and not parent.get('cleanup_failed')
               and parent['proposal'] == 'scale035'
               and parent['wout_sha256'] == candidate['wout_sha256'], 'frozen cold parent required')
    parent['record_sha256'] = candidate['parent_sha256']
    for name, key in (('solver.json', 'solver_report_sha256'), ('request.json', 'request_sha256')):
        check.bind(folder/name, parent[key], sources)
    solver.check_sources(parent['sources_before'])
    check.need(parent['sources_before'] == parent['sources_after'], 'cold sources changed')
    sources.update(parent['sources_before'])
    validated = solver.read(check.bind(config['validation_report'],
                                       candidate['validation_report_sha256'], sources))
    check.need(validated['completed'] and validated['verdict'] == 'positive',
               'successful frozen ideal validation required')
    check.bind(config['seed'], coil.SEED_SHA, sources)
    check.bind(config['reference_wout'], protocol['reference']['wout_sha256'], sources)
    check.bind(config['native_environment'], config['native_environment_sha256'], sources)
    training = {}
    for proposal, kind, key in (('control', 'reference', 'control_training'),
                                ('scale035', 'candidate', 'candidate_training')):
        path = check.bind(config[key], protocol[kind]['training_receipt_sha256'], sources)
        receipt = solver.read(path)
        check.need(receipt['completed'] and receipt['sources_unchanged']
                   and receipt['environment_unchanged'] and receipt['proposal'] == proposal,
                   'completed frozen training receipt required')
        row = receipt['result']
        decision.complete_score(row, 'training')
        expected = dict(input_sha256=protocol[kind]['input_sha256'],
                        wout_sha256=protocol[kind]['wout_sha256'],
                        target_id='reference401' if proposal == 'control'
                        else candidate['target_id'])
        if proposal != 'control':
            expected['parent_sha256'] = candidate['parent_sha256']
        check.need(all(row['identity'].get(k) == v for k, v in expected.items()),
                   'training target binding differs')
        solver.check_sources(row['sources_after'])
        sources.update(row['sources_after'])
        training[proposal] = row
        guard()
    for path in [*sorted((check.ROOT/'src').rglob('*.py')),
                 *[check.ROOT/'scripts'/name for name in ('run_fit_coupling.py',
                                                         'run_joint_stage.py')]]:
        check.bind(path, solver.digest(path), sources)
        guard()
    screen.verify(config, sources, guard)
    return config, parent, training, provenance


def fit_state(row):
    ordinary = row['stop'] == 'fit-cap'
    check.need(row['stop'] in ('fit-cap', 'solver-return') and row['cap_reached'] == ordinary
               and row['search']['startup_pass'],
               'normal completed fit after successful startup required')
    check.need(row['search']['status']['reason'] == ('budget' if ordinary else 'solver-return'),
               'fit termination classification differs')
    if row['search']['selected'] is None:
        check.need(row['snapshot'] is None, 'no-candidate fit returned a snapshot')
        return False
    check.need(decision.fit_eligible(row['search'], ordinary) and row['snapshot'] is not None,
               'selected fit candidate is ineligible')
    return True


def diagnostic_deadline(finished, fit_deadline, arm_deadline):
    return {key: min(min(finished[i], fit_deadline[key])+300, arm_deadline[key])
            for i, key in enumerate(('monotonic', 'wall'))}


def run(config_path, output, revision, origin):
    output = Path(output).resolve()
    output.mkdir(exist_ok=False)
    global_deadline = dict(monotonic=origin[0]+TOTAL_SECONDS, wall=origin[1]+TOTAL_SECONDS)
    active_deadline = global_deadline
    result = dict(completed=False, verdict='inconclusive', physical_admission=False,
                  actual_coil_endpoint=None, coil_feasibility_established=False,
                  interior_tested=False, tracing_tested=False, clock_origin=list(origin),
                  deadline=global_deadline, cold_equilibria_reused=True, arms={})
    sources = {}

    def guard():
        reason = solver.stop_reason(output, active_deadline['monotonic'],
                                    active_deadline['wall'], origin)
        if reason:
            raise native.schedule.ArmInterrupted(reason)

    try:
        guard()
        check.need(solver.shutil.disk_usage(output).free >= solver.START_RESERVE,
                   'initial disk reserve')
        for proposal in ORDER:
            arm_origin = origin if proposal == 'control' else (time.monotonic(), time.time())
            arm_deadline = {k: min(arm_origin[i]+ARM_SECONDS, global_deadline[k])
                            for i, k in enumerate(('monotonic', 'wall'))}
            fit_deadline = {k: min(arm_origin[i]+FIT_SECONDS, arm_deadline[k])
                            for i, k in enumerate(('monotonic', 'wall'))}
            active_deadline = fit_deadline
            config, parent, training, provenance = prepare(config_path, revision, sources, guard)
            folder = output/proposal
            folder.mkdir(exist_ok=False)
            setup = dict(config=config, parent=parent, provenance=provenance,
                         sources=dict(sources), clock_origin=list(origin),
                         arm_origin=list(arm_origin),
                         fit_deadline=fit_deadline, arm_deadline=arm_deadline)
            solver.save(folder/'setup.json', setup)
            check.bind(folder/'setup.json', solver.digest(folder/'setup.json'), sources)
            guard()
            base = dict(proposal=proposal, revision=revision,
                        native_environment=config['native_environment'],
                        arm_root=str(output), clock_origin=list(origin), seed=config['seed'])
            if proposal == 'control':
                base['wout'] = config['reference_wout']
            else:
                base['solved'] = dict(folder=config['candidate_folder'], parent=parent)

            def operation(name, window, outer, folder=folder, base=base,
                          proposal=proposal, **extra):
                cell = folder/name
                cell.mkdir(exist_ok=False)
                request = dict(base, operation=name, window=window, outer=outer,
                               sources=dict(sources), **extra)
                path = cell/'request.json'
                solver.save(path, request)
                request_sha = solver.digest(path)
                guard()
                process = solver.supervise([sys.executable, '-I',
                    str(check.ROOT/'scripts/run_joint_stage.py'), '--request', str(path)],
                    cell, output, outer['monotonic'], outer['wall'], clock_origin=origin)
                finished = time.monotonic(), time.time()
                solver.save(cell/'supervisor.json', process)
                guard()
                check.need(process['completed'] and process['returncode'] == 0
                           and process['stop_reason'] is None, 'native operation incomplete')
                receipt = solver.read(cell/'run/result.json')
                check.need(receipt['completed'] and receipt['sources_unchanged']
                           and receipt['environment_unchanged']
                           and receipt['request_sha256'] == request_sha
                           and solver.digest(path) == request_sha and receipt['operation'] == name
                           and receipt['proposal'] == proposal, 'native receipt binding failed')
                for item in (path, cell/'supervisor.json', cell/'run/result.json'):
                    check.bind(item, solver.digest(item), sources)
                return receipt['result'], finished

            active_deadline = arm_deadline
            fitted, finished = operation('fit', fit_deadline, arm_deadline)
            active_deadline = diagnostic_deadline(finished, fit_deadline, arm_deadline)
            guard()
            check.need(fitted['window'] == fit_deadline, 'fit receipt window differs')
            eligible = fit_state(fitted)
            arm = dict(completed=False, no_eligible_candidate=not eligible,
                       fit=fitted, fit_finished=list(finished),
                       diagnostic_deadline=dict(active_deadline), summary=None)
            if eligible:
                settings = dict(base, operation='selection', window=active_deadline,
                                outer=active_deadline)
                recorder = native.Recorder(folder/'selection', settings)
                input_path = check.ROOT/check.TARGET if proposal == 'control' else (
                    Path(config['candidate_folder'])/'input.json')
                wout = config['reference_wout'] if proposal == 'control' else (
                    Path(config['candidate_folder'])/'wout.nc')
                frozen = decision.freeze_selection(proposal, training[proposal], fitted['search'],
                    fitted['stop'] == 'fit-cap', fitted['snapshot'], input_path, wout, recorder)
                check.bind(folder/'selection/frozen-selection.json',
                           solver.digest(folder/'selection/frozen-selection.json'), sources)
                checked, _ = operation('boundary-screen', active_deadline, active_deadline,
                                       frozen=frozen)
                arm.update(frozen=frozen, diagnostics=checked, summary=summary(frozen, checked))
            guard()
            screen.verify(config, sources, guard)
            arm.update(completed=True, elapsed_s=time.monotonic()-arm_origin[0],
                       wall_elapsed_s=time.time()-arm_origin[1])
            solver.save(folder/'arm.json', arm)
            guard()
            result['arms'][proposal] = arm
        result.update(classify(result['arms']))
        screen.verify(config, sources, guard)
        result.update(completed=True, sources_after=dict(sources),
                      sources_unchanged=True, environment_unchanged=True,
                      elapsed_s=time.monotonic()-origin[0], wall_elapsed_s=time.time()-origin[1])
        solver.save(output/'screen.json', result)
        guard()
        return result
    except Exception as exc:
        result.update(completed=False, verdict='inconclusive', error=f'{type(exc).__name__}: {exc}')
    result.update(elapsed_s=time.monotonic()-origin[0], wall_elapsed_s=time.time()-origin[1])
    solver.save(output/'screen.json', result)
    return result
