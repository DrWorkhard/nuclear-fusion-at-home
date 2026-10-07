"""One frozen ideal-target screen; no coil fitting or adaptive follow-up."""
import sys
import time
from pathlib import Path

from fusion_baselines import joint_native as native

solver, target, decision, check = native.solver, native.target, native.decision, native.check
SECONDS, RATIO, PROPOSAL = 600, .99, 'scale035'
CONFIG_KEYS = {'revision', 'input_path', 'reference_report', 'solver_python',
               'solver_environment', 'solver_environment_sha256',
               'native_environment', 'native_environment_sha256'}


def prepare(config_path, revision, sources, guard):
    guard()
    check.bind(config_path, solver.digest(config_path), sources)
    config = solver.read(config_path)
    check.need(set(config) == CONFIG_KEYS and config['revision'] == revision
               and len(revision) == 40, 'exact reviewed screen configuration required')
    provenance = native.build_run_record(check.ROOT)
    check.need(provenance['repository']['commit'] == revision
               and not provenance['repository']['dirty'], 'clean reviewed screen required')
    target.registered_input(config['input_path'], PROPOSAL, sources)
    protocol = solver.read(check.ROOT/target.SCALE_PROTOCOL)
    check.need(protocol['budget']['total_seconds'] == SECONDS
               and protocol['decision']['threshold_ratio'] == RATIO,
               'registered screen limits required')
    for key in ('native_environment', 'solver_environment'):
        check.bind(config[key], config[key+'_sha256'], sources)
        guard()
    reference = protocol['reference']
    path = check.bind(config['reference_report'], reference['report_sha256'], sources)
    receipt = solver.read(path)
    check.need(receipt['completed'] and receipt['operation'] == 'score'
               and receipt['proposal'] == 'control' and receipt['sources_unchanged']
               and receipt['environment_unchanged'], 'frozen completed reference score required')
    score = receipt['result']
    check.need(score['identity']['target_id'] == 'reference401'
               and score['identity']['input_sha256'] == target.INPUT_HASHES['control']
               and score['identity']['wout_sha256'] == check.FIXED[check.WOUT]
               and decision.complete_score(score, 'training') == reference['score'],
               'reference score/domain identity changed')
    for path in [*sorted((check.ROOT/'src').rglob('*.py')),
                 *[check.ROOT/'scripts'/name for name in ('run_joint_step_scale.py',
                    'run_joint_stage.py', 'solve_joint_target.py')]]:
        check.bind(path, solver.digest(path), sources)
        guard()
    verify(config, sources, guard)
    return config, reference['score'], provenance


def verify(config, sources, guard):
    guard()
    solver.check_sources(sources)
    check.need(solver.identity(native.NATIVE_PACKAGES)
               == solver.read(config['native_environment']), 'native environment changed')
    guard()


def classify(score, parent, reference):
    identity = score['identity']
    check.need(identity['target_id'] == target.proposal_id(PROPOSAL)
               and identity['input_sha256'] == target.INPUT_HASHES[PROPOSAL]
               and identity['wout_sha256'] == parent['wout_sha256']
               and identity['parent_sha256'] == parent['record_sha256'],
               'score differs from the completed cold-solve receipt')
    if not score['eligible']:
        decision.numerical_rejection(dict(proposal=PROPOSAL, search=None, training=score,
            rejection=dict(kind='plasma-domain', evidence=dict(proposal=PROPOSAL,
                input_sha256=target.INPUT_HASHES[PROPOSAL], completed=True,
                resource_interrupted=False, result=score))))
        return dict(verdict='negative', reason='complete ineligible training domain',
                    score=None, reference_score=reference)
    value = decision.complete_score(score, 'training')
    return dict(verdict='positive' if value <= RATIO*reference else 'negative',
                score=value, reference_score=reference, threshold=RATIO*reference,
                relative_change=value/reference-1)


def run(config_path, output, revision, origin):
    """All scientific work shares the original 600 s clocks, including final checks."""
    output = Path(output).resolve()
    deadline = dict(monotonic=origin[0]+SECONDS, wall=origin[1]+SECONDS)
    output.mkdir(exist_ok=False)
    result = dict(completed=False, verdict='inconclusive', physical_admission=False,
                  actual_coil_endpoint=None, heldout_gain_established=False,
                  coil_feasibility_established=False, clock_origin=list(origin), deadline=deadline)
    sources = {}

    def guard():
        reason = solver.stop_reason(output, deadline['monotonic'], deadline['wall'], origin)
        if reason:
            raise native.schedule.ArmInterrupted(reason)

    try:
        guard()
        check.need(solver.shutil.disk_usage(output).free >= solver.START_RESERVE,
                   'initial disk reserve')
        config, reference, provenance = prepare(config_path, revision, sources, guard)
        solver.save(output/'setup.json', dict(config=config, provenance=provenance,
            sources=dict(sources), clock_origin=list(origin), deadline=deadline))
        check.bind(output/'setup.json', solver.digest(output/'setup.json'), sources)
        guard()
        folder = output/'solve'
        parent = solver.run_solver(config['solver_python'], config['input_path'], PROPOSAL,
            config['solver_environment'], config['solver_environment_sha256'], folder, output,
            revision, deadline['monotonic'], deadline['wall'], clock_origin=origin)
        guard()
        check.need(parent['completed'] and not parent.get('cleanup_failed'),
                   'cold solve incomplete; no numerical rejection inferred')
        for name in ('parent.json', 'request.json', 'solver.json', 'input.json', 'wout.nc'):
            check.bind(folder/name, solver.digest(folder/name), sources)
            guard()
        verify(config, sources, guard)
        cell = output/'score'
        cell.mkdir(exist_ok=False)
        request = dict(operation='step-score', proposal=PROPOSAL, revision=revision,
            native_environment=config['native_environment'], sources=dict(sources),
            arm_root=str(output), clock_origin=list(origin), window=deadline, outer=deadline,
            solved=dict(folder=str(folder), parent=parent))
        path = cell/'request.json'
        solver.save(path, request)
        request_sha = solver.digest(path)
        guard()
        process = solver.supervise([sys.executable, '-I',
            str(check.ROOT/'scripts/run_joint_stage.py'), '--request', str(path)],
            cell, output, deadline['monotonic'], deadline['wall'], clock_origin=origin)
        solver.save(cell/'supervisor.json', process)
        guard()
        check.need(process['completed'], 'training score subprocess incomplete')
        receipt = solver.read(cell/'run/result.json')
        check.need(receipt['completed'] and receipt['request_sha256'] == request_sha
                   and solver.digest(path) == request_sha and receipt['sources_unchanged']
                   and receipt['environment_unchanged'] and receipt['operation'] == 'step-score'
                   and receipt['proposal'] == PROPOSAL, 'training receipt binding failed')
        for item in (path, cell/'supervisor.json', cell/'run/result.json'):
            check.bind(item, solver.digest(item), sources)
        outcome = classify(receipt['result'], parent, reference)
        guard()
        verify(config, sources, guard)
        result.update(outcome, completed=True, sources_after=dict(sources),
                      sources_unchanged=True, environment_unchanged=True)
        result.update(elapsed_s=time.monotonic()-origin[0], wall_elapsed_s=time.time()-origin[1])
        solver.save(output/'screen.json', result)
        guard()
        return result
    except Exception as exc:
        result.update(completed=False, verdict='inconclusive', error=f'{type(exc).__name__}: {exc}')
    result.update(elapsed_s=time.monotonic()-origin[0], wall_elapsed_s=time.time()-origin[1])
    solver.save(output/'screen.json', result)
    return result
