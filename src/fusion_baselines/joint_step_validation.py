"""Four registered scores for two frozen equilibria; no new search or solve."""
import sys
import time
from pathlib import Path

from fusion_baselines import joint_step_scale as screen

native, solver, check, target = screen.native, screen.solver, screen.check, screen.target
decision, action = screen.decision, screen.native.action
PROTOCOL = 'docs/optimization/ISSUE37_STEP_VALIDATION.json'
PROTOCOL_SHA = 'c3f5c65379dd80f070a603e357db21c060862e682f4751149b828912fa4a7398'
SECONDS = 180
MODES = ('holdout', 'holdout-refined')
ORDER = [(p, mode) for p in ('control', 'scale035') for mode in MODES]
CONFIG_KEYS = {'revision', 'candidate_folder', 'screen_report', 'reference_wout',
               'native_environment', 'native_environment_sha256'}


def prepare(config_path, revision, sources, guard):
    guard()
    check.bind(config_path, solver.digest(config_path), sources)
    config = solver.read(config_path)
    check.need(set(config) == CONFIG_KEYS and config['revision'] == revision
               and len(revision) == 40, 'exact reviewed validation configuration required')
    provenance = native.build_run_record(check.ROOT)
    check.need(provenance['repository']['commit'] == revision
               and not provenance['repository']['dirty'], 'clean reviewed validation required')
    protocol = solver.read(check.bind(check.ROOT/PROTOCOL, PROTOCOL_SHA, sources))
    check.need(protocol['budget']['total_seconds'] == SECONDS
               and protocol['order'] == [list(row) for row in ORDER]
               and protocol['decision']['threshold_ratio'] == .99
               and protocol['decision']['refinement_tolerance'] == .001,
               'fixed validation limits required')
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
    prior = solver.read(check.bind(config['screen_report'], candidate['screen_sha256'], sources))
    check.need(prior['completed'] and prior['verdict'] == 'positive',
               'successful frozen screen required')
    check.bind(config['reference_wout'], protocol['reference']['wout_sha256'], sources)
    check.bind(config['native_environment'], config['native_environment_sha256'], sources)
    for path in [*sorted((check.ROOT/'src').rglob('*.py')),
                 *[check.ROOT/'scripts'/name for name in ('validate_joint_step.py',
                                                         'run_joint_stage.py')]]:
        check.bind(path, solver.digest(path), sources)
        guard()
    screen.verify(config, sources, guard)
    return config, parent, provenance


def classify(reports, parent):
    check.need(set(reports) == {'control', 'scale035'}
               and all(set(r) == set(MODES) for r in reports.values()), 'all four scores required')
    scores, refinements = {}, {}
    for proposal, modes in reports.items():
        expected = dict(target_id='reference401' if proposal == 'control'
                        else target.proposal_id(proposal),
                        input_sha256=target.INPUT_HASHES[proposal],
                        wout_sha256=check.FIXED[check.WOUT] if proposal == 'control'
                        else parent['wout_sha256'])
        if proposal != 'control':
            expected['parent_sha256'] = parent['record_sha256']
        scores[proposal] = {}
        for mode in MODES:
            row = modes[mode]
            check.need(all(row['identity'].get(k) == v for k, v in expected.items()),
                       'validation score target identity differs')
            scores[proposal][mode] = decision.complete_score(row, mode)
        refinements[proposal] = action.holdout_agreement(modes[MODES[0]], modes[MODES[1]])
    check.need(min(scores['control'].values()) > 0, 'positive paired reference required')
    ratios = {mode: scores['scale035'][mode]/scores['control'][mode] for mode in MODES}
    gain_pass = all(ratio <= .99 for ratio in ratios.values())
    refinement_pass = all(row['passed'] for row in refinements.values())
    return dict(verdict='positive' if gain_pass and refinement_pass else 'negative',
                scores=scores, ratios=ratios, refinements=refinements,
                gain_hurdle_passed=gain_pass, refinement_hurdle_passed=refinement_pass)


def run(config_path, output, revision, origin):
    output = Path(output).resolve()
    output.mkdir(exist_ok=False)
    deadline = dict(monotonic=origin[0]+SECONDS, wall=origin[1]+SECONDS)
    result = dict(completed=False, verdict='inconclusive', physical_admission=False,
                  actual_coil_endpoint=None, coil_feasibility_established=False,
                  clock_origin=list(origin), deadline=deadline, cold_solve_reused=True)
    sources, reports = {}, {'control': {}, 'scale035': {}}

    def guard():
        reason = solver.stop_reason(output, deadline['monotonic'], deadline['wall'], origin)
        if reason:
            raise native.schedule.ArmInterrupted(reason)

    try:
        guard()
        check.need(solver.shutil.disk_usage(output).free >= solver.START_RESERVE,
                   'initial disk reserve')
        config, parent, provenance = prepare(config_path, revision, sources, guard)
        solver.save(output/'setup.json', dict(config=config, parent=parent, provenance=provenance,
            sources=dict(sources), clock_origin=list(origin), deadline=deadline))
        check.bind(output/'setup.json', solver.digest(output/'setup.json'), sources)
        for proposal, mode in ORDER:
            guard()
            cell = output/f'{proposal}-{mode}'
            cell.mkdir(exist_ok=False)
            request = dict(operation='phase-score', proposal=proposal, mode=mode, revision=revision,
                native_environment=config['native_environment'], sources=dict(sources),
                arm_root=str(output), clock_origin=list(origin), window=deadline, outer=deadline)
            if proposal == 'control':
                request['wout'] = config['reference_wout']
            else:
                request['solved'] = dict(folder=config['candidate_folder'], parent=parent)
            path = cell/'request.json'
            solver.save(path, request)
            request_sha = solver.digest(path)
            guard()
            process = solver.supervise([sys.executable, '-I',
                str(check.ROOT/'scripts/run_joint_stage.py'), '--request', str(path)],
                cell, output, deadline['monotonic'], deadline['wall'], clock_origin=origin)
            solver.save(cell/'supervisor.json', process)
            guard()
            check.need(process['completed'] and process['returncode'] == 0
                       and process['stop_reason'] is None, 'validation score process incomplete')
            receipt = solver.read(cell/'run/result.json')
            check.need(receipt['completed'] and receipt['sources_unchanged']
                       and receipt['environment_unchanged']
                       and receipt['request_sha256'] == request_sha
                       and solver.digest(path) == request_sha
                       and receipt['operation'] == 'phase-score'
                       and receipt['proposal'] == proposal and receipt['result']['mode'] == mode,
                       'validation receipt binding failed')
            for item in (path, cell/'supervisor.json', cell/'run/result.json'):
                check.bind(item, solver.digest(item), sources)
            reports[proposal][mode] = receipt['result']
        outcome = classify(reports, parent)
        guard()
        screen.verify(config, sources, guard)
        result.update(outcome, completed=True, sources_after=dict(sources),
                      sources_unchanged=True, environment_unchanged=True)
        result.update(elapsed_s=time.monotonic()-origin[0], wall_elapsed_s=time.time()-origin[1])
        solver.save(output/'validation.json', result)
        guard()
        return result
    except Exception as exc:
        result.update(completed=False, verdict='inconclusive', error=f'{type(exc).__name__}: {exc}')
    result.update(elapsed_s=time.monotonic()-origin[0], wall_elapsed_s=time.time()-origin[1])
    solver.save(output/'validation.json', result)
    return result
