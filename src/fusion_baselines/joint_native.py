"""Native operations for the fixed joint schedule; no experiment enabled by import."""
import copy
import io
import sys
import time
from pathlib import Path

import numpy as np

from fusion_baselines import coil_fit as fit
from fusion_baselines import joint_action as action
from fusion_baselines import joint_coil as coil
from fusion_baselines import joint_decision as decision
from fusion_baselines import joint_equilibrium as solver
from fusion_baselines import joint_schedule as schedule
from fusion_baselines.provenance import build_run_record

check, target = coil.check, coil.target
NATIVE_PACKAGES = ('numpy', 'scipy', 'netCDF4', 'simsopt')


class FitCap(TimeoutError):
    """Only the declared fit cap; the hard arm/resource guard has already passed."""


class Recorder(fit.Recorder):
    def __init__(self, output, request, storage=None, components=None):
        self.settings, self.finalizing, self.cap_reached = request, False, False
        super().__init__(output, request['outer']['monotonic'], storage)
        self.points = {key: dict(attempted=0, completed=0) for key in self.counts}
        self.components = {} if components is None else components
        self.components[str(output)] = self.counts

    def guard(self):
        req = self.settings
        reason = solver.stop_reason(req['arm_root'], req['outer']['monotonic'],
                                    req['outer']['wall'], req['clock_origin'])
        if reason:
            raise schedule.ArmInterrupted(reason)
        if not self.finalizing:
            reason = solver.stop_reason(req['arm_root'], req['window']['monotonic'],
                                        req['window']['wall'], req['clock_origin'])
            if reason == 'deadline' and req['operation'] == 'fit':
                self.cap_reached = True
                raise FitCap('declared fit cap reached')
            if reason:
                raise schedule.ArmInterrupted(reason)

    def child(self, name):
        return Recorder(self.output/name, self.settings, self.storage, self.components)

    def request_field(self, name, count, function, *args):
        self.guard()
        self.points[name]['attempted'] += count
        before = self.counts[name]['completed']
        try:
            return self.call(name, function, *args)
        finally:
            if self.counts[name]['completed'] > before:
                self.points[name]['completed'] += count


class InteriorRecorder(Recorder):
    # _screen_level expects the existing check.Recorder request/write interface.
    def request(self, name, count, function, *args):
        return self.request_field(name, count, function, *args)

    def write(self, name, value):
        self.guard()
        self.save(name, value)
        self.guard()


def score(request, record):
    if request['proposal'] == 'control':
        return action.score_reference(Path(request['wout']), 'training', record)
    solved = request['solved']
    return action.score_proposal(solved['folder'], solved['parent'], 'training', record)


def step_score(request, record):
    check.need(request['proposal'] == 'scale035', 'registered step-scale score required')
    solved = request['solved']
    return action.score_step_scale(solved['folder'], solved['parent'], record)


def phase_score(request, record):
    check.need(request['mode'] in ('holdout', 'holdout-refined'), 'validation grid required')
    if request['proposal'] == 'control':
        return action.score_reference(Path(request['wout']), request['mode'], record)
    check.need(request['proposal'] == 'scale035', 'fixed validation candidate required')
    solved = request['solved']
    return action.score_step_validation(solved['folder'], solved['parent'], request['mode'], record)


def search(request, record):
    from scipy.optimize import minimize

    if request['proposal'] == 'control':
        data, _, sources, _ = target.intake(check.ROOT/check.TARGET, request['wout'], 'control',
                                            check.FIXED[check.WOUT], record.guard)
        path = check.bind(request['seed'], coil.SEED_SHA, sources)
        seed = check.read_json(path)
        check.snapshot_identity(seed)
        check.need(seed['order'] == 5, 'original order5 seed required')
        model = fit.Model(seed, data, record)
        prepared = None
    else:
        solved = request['solved']
        prepared = coil.prepare(request['seed'], solved['folder'], solved['parent'], record)
        model, seed, sources = (prepared[k] for k in ('model', 'seed', 'sources'))
    record.save('seed.json', seed)
    result = fit.search(model, record, minimize)
    record.finalizing = True
    record.guard()
    ordinary = result['status']['reason'] == 'budget' and record.cap_reached
    stop = ('fit-cap' if ordinary else 'solver-return'
            if result['status']['reason'] == 'solver-return' else 'failure')
    snapshot = None
    if decision.fit_eligible(result, ordinary):
        selected = result['selected']
        if prepared is None:
            snapshot = copy.deepcopy(seed)
            snapshot['base_coefficients'] = np.asarray(selected['x']).reshape(6, 3, 11).tolist()
            coil.normalize(snapshot, selected['metrics']['unit_flux'])
            check.need(snapshot['scale'] == selected['metrics']['scale'], 'selected scale changed')
            check.snapshot_identity(snapshot)
        else:
            snapshot = coil.selected_snapshot(prepared, selected)
        record.save('selected-snapshot.json', snapshot)
    record.save('search.json', result)
    solver.check_sources(sources)
    record.guard()
    return dict(search=result, snapshot=snapshot, stop=stop, sources=sources,
                cap_reached=record.cap_reached, window=request['window'])


def reference_context(frozen, request, record):
    decision.snapshot_identity('control', frozen['identity'], frozen['snapshot'])
    data, targets, sources, numerical = target.intake(check.ROOT/check.TARGET, request['wout'],
        'control', check.FIXED[check.WOUT], record.guard)
    for path, sha in frozen['sources'].items():
        check.bind(path, sha, sources)
    context = dict(binding=copy.deepcopy(frozen['identity']), intake=numerical, sources=sources,
        canonical_snapshot_sha256=frozen['canonical_snapshot_sha256'],
        full_joint_execution_enabled=False, physical_admission=False)
    return data, targets, context


def diagnostics(request, record):
    frozen = request['frozen']
    check.need(frozen['selection_sha256'] == decision.canonical_sha(
        {k: v for k, v in frozen.items() if k != 'selection_sha256'}), 'changed selection')
    snapshot = frozen['snapshot']
    control = request['proposal'] == 'control'
    solved = request.get('solved')
    if control:
        data, targets, context = reference_context(frozen, request, record)
    else:
        decision.snapshot_identity(request['proposal'], frozen['identity'], snapshot)
        data = targets = context = None
    report = dict(completed=False, budget_complete=False, fine=[], interior=[],
                  selection_sha256=frozen['selection_sha256'], physical_admission=False)
    fine = record.child('fine')
    chosen = dict(index=frozen['selected_index'],
                  x=np.asarray(snapshot['base_coefficients']).ravel(),
                  metrics=dict(scale=snapshot['scale'], unit_flux=snapshot['unit_flux']))
    for shift in (0., .5):
        row = (fit.fine(snapshot, data, chosen, fine, shift) if control else
               coil.boundary(snapshot, solved['folder'], solved['parent'], shift,
                             frozen['selected_index'], fine))
        report['fine'].append(row)
        record.save('progress.json', report)
    report['geometry'] = (check.geometry(snapshot, data, record.guard) if control else
                         coil.geometry(snapshot, solved['folder'], solved['parent'], record))
    interior = InteriorRecorder(record.output/'interior', request, record.storage,
                                record.components)
    for index, (n, nodes) in enumerate(check.LEVELS):
        row, arrays = (check._screen_level(snapshot, data, targets[n], n, nodes, interior,
                                          dict(B2=check.B2, flux=check.TARGET_FLUX)) if control else
                       coil.interior(snapshot, solved['folder'], solved['parent'], n, nodes,
                                     interior))
        buffer = io.BytesIO()
        np.savez_compressed(buffer, **arrays)
        interior.write(f'level-{index}.npz', buffer.getvalue())
        row['arrays_sha256'] = check.digest(interior.output/f'level-{index}.npz')
        interior.write(f'level-{index}.json', row)
        report['interior'].append(row)
        record.save('progress.json', report)
    report['interior_refinements'] = check.refinements(report['interior'])
    trace = record.child('trace')
    report['trace'] = (coil._direct_trace(snapshot, data, Path(request['wout']), context, trace)
                       if control else coil.direct_trace(snapshot, solved['folder'],
                                                          solved['parent'], trace))
    record.save('progress.json', report)
    for mode in ('holdout', 'holdout-refined'):
        cell = record.child(mode)
        report[mode] = (action.score_reference(Path(request['wout']), mode, cell) if control else
                        action.score_proposal(solved['folder'], solved['parent'], mode, cell))
        record.save('progress.json', report)
    if control:
        solver.check_sources(context['sources'])
    record.guard()
    report['completed'] = True
    return report


def worker(request_path):
    """Execute a single native operation in the supervisor's process group."""
    request_path = Path(request_path)
    request_sha = solver.digest(request_path)
    request = solver.read(request_path)
    started = time.monotonic()
    record = Recorder(request_path.parent/'run', request,
                      [solver.retained_bytes(request['arm_root'])])
    report = dict(completed=False, request_sha256=request_sha, physical_admission=False,
                  operation=request['operation'], proposal=request['proposal'])
    try:
        record.guard()
        provenance = build_run_record(check.ROOT)
        check.need(provenance['repository']['commit'] == request['revision']
                   and not provenance['repository']['dirty'], 'clean reviewed operation required')
        report['provenance'] = provenance
        solver.check_sources(request['sources'])
        check.need(solver.identity(NATIVE_PACKAGES) == solver.read(request['native_environment']),
                   'native environment differs from frozen inventory')
        record.guard()
        record.save('attempt.json', report)
        operation = {'score': score, 'step-score': step_score, 'phase-score': phase_score,
                     'fit': search, 'diagnostics': diagnostics}[request['operation']]
        result = operation(request, record)
        record.guard()
        solver.check_sources(request['sources'])
        check.need(solver.digest(request_path) == request_sha, 'operation request changed')
        check.need(solver.identity(NATIVE_PACKAGES) == solver.read(request['native_environment']),
                   'native environment changed during operation')
        record.guard()
        report.update(completed=True, result=result, sources_unchanged=True,
                      environment_unchanged=True)
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    totals = {name: {state: sum(row[name][state] for row in record.components.values())
                     for state in ('attempted', 'completed')} for name in record.counts}
    report.update(native_counts=totals, component_native_counts=record.components,
                  native_counts_scope='Recorder calls; excludes internal tracer native calls',
                  elapsed_s=time.monotonic()-started)
    record.save('result.json', report)
    try:
        record.guard()
    except Exception as exc:
        report.update(completed=False, error=f'{type(exc).__name__}: {exc}')
        record.save('result.json', report)
    return 0 if report['completed'] else 1


class Operations:
    """Trusted parent: one supervisor owns each child, including cold VMEC solves."""
    def __init__(self, *, seed, wout, solver_python, solver_environment, solver_environment_sha256,
                 native_environment, native_environment_sha256, revision):
        self.config = dict(seed=str(Path(seed).resolve()), wout=str(Path(wout).resolve()),
            solver_python=str(Path(solver_python).absolute()),
            solver_environment=str(Path(solver_environment).resolve()),
            solver_environment_sha256=solver_environment_sha256,
            native_environment=str(Path(native_environment).resolve()),
            native_environment_sha256=native_environment_sha256, revision=revision)
        self.states = {}

    def setup(self, arm, window):
        arm.guard(window)
        provenance = build_run_record(check.ROOT)
        repo = provenance['repository']
        check.need(repo['commit'] == self.config['revision'] and not repo['dirty'],
                   'clean reviewed parent required')
        sources = {}
        for path, sha in ((self.config['seed'], coil.SEED_SHA),
                          (self.config['wout'], check.FIXED[check.WOUT]),
                          (check.ROOT/check.TARGET, target.INPUT_HASHES['control']),
                          (check.ROOT/target.PROTOCOL, target.PROTOCOL_SHA),
                          (self.config['native_environment'],
                           self.config['native_environment_sha256']),
                          (self.config['solver_environment'],
                           self.config['solver_environment_sha256'])):
            check.bind(path, sha, sources)
            arm.guard(window)
        for path in [*sorted((check.ROOT/'src').rglob('*.py')),
                     check.ROOT/'scripts/run_joint_stage.py',
                     check.ROOT/'scripts/run_joint_comparison.py',
                     check.ROOT/'scripts/solve_joint_target.py']:
            check.bind(path, check.digest(path), sources)
        check.need(solver.identity(NATIVE_PACKAGES)
                   == solver.read(self.config['native_environment']), 'native lock mismatch')
        arm.guard(window)
        self.states[arm.name] = dict(sources=sources, solved={}, fitted={}, frozen=None)
        solver.save(arm.output/'setup.json', dict(provenance=provenance, sources=sources,
            config=self.config, clock_origin=[arm.started, arm.wall_started],
            physical_admission=False))
        check.bind(arm.output/'setup.json', check.digest(arm.output/'setup.json'), sources)
        arm.guard(window)

    def verify(self, arm):
        solver.check_sources(self.states[arm.name]['sources'])
        check.need(solver.identity(NATIVE_PACKAGES)
                   == solver.read(self.config['native_environment']), 'native environment changed')

    def call(self, arm, operation, proposal, solved, window, outer=None, **values):
        outer = window if outer is None else outer
        arm.guard(window)
        state = self.states[arm.name]
        self.verify(arm)
        folder = arm.output/f'{proposal}-{operation}'
        folder.mkdir(exist_ok=False)
        request = dict(self.config, operation=operation, proposal=proposal, solved=solved,
            sources=dict(state['sources']), arm_root=str(arm.output),
            clock_origin=[arm.started, arm.wall_started],
            window=dict(monotonic=window.monotonic, wall=window.wall),
            outer=dict(monotonic=outer.monotonic, wall=outer.wall), **values)
        path = folder/'request.json'
        solver.save(path, request)
        request_sha = solver.digest(path)
        arm.guard(window)
        command = [sys.executable, '-I', str(check.ROOT/'scripts/run_joint_stage.py'),
                   '--request', str(path)]
        process = solver.supervise(command, folder, arm.output, outer.monotonic, outer.wall,
                                   clock_origin=[arm.started, arm.wall_started])
        solver.save(folder/'supervisor.json', process)
        arm.guard(outer)
        if not process['completed']:
            raise schedule.ArmInterrupted(f'{proposal} {operation} subprocess incomplete')
        report_path = folder/'run/result.json'
        report = solver.read(report_path)
        check.need(report['completed'] and report['request_sha256'] == request_sha
                   and solver.digest(path) == request_sha
                   and report['operation'] == operation and report['proposal'] == proposal
                   and report['sources_unchanged'] and report['environment_unchanged'],
                   'operation receipt binding failed')
        self.verify(arm)
        for item in (path, report_path, folder/'supervisor.json'):
            check.bind(item, check.digest(item), state['sources'])
        arm.guard(outer)
        return report['result']

    def score(self, arm, proposal, solved, window):
        return self.call(arm, 'score', proposal, solved, window)

    def fit(self, arm, proposal, solved, training, window, outer):
        result = self.call(arm, 'fit', proposal, solved, window, outer, training=training)
        check.need(result['window'] == dict(monotonic=window.monotonic, wall=window.wall),
                   'fit receipt changed declared cap')
        result['window'] = window
        self.states[arm.name]['fitted'][proposal] = result
        return result

    def solve(self, arm, proposal, window):
        arm.guard(window)
        state = self.states[arm.name]
        self.verify(arm)
        original = check.read_json(check.ROOT/check.TARGET)
        document = copy.deepcopy(original)
        coefficient = next(r for r in document['rbc'] if (r['m'], r['n']) == (2, 1))
        coefficient['value'] += target.DELTAS[proposal]
        input_path = arm.output/f'{proposal}-input.json'
        solver.save(input_path, document)
        check.bind(input_path, target.INPUT_HASHES[proposal], state['sources'])
        # This cheap preflight can supply a documented failed size measurement.
        # The trusted solver repeats its own intake; no gate is bypassed.
        sizes = []
        for data in (original, document):
            row = []
            for n in (128, 256):
                arm.guard(window)
                row.append(target.volume(data, n))
                arm.guard(window)
            sizes.append(row)
        size = dict(grids=[128, 256], original_m3=sizes[0], proposal_m3=sizes[1])
        if max(abs(a/b-1) for a, b in zip(sizes[1], sizes[0], strict=True)) > .001:
            rejection = dict(kind='size', evidence=dict(proposal=proposal,
                input_sha256=target.INPUT_HASHES[proposal], completed=True,
                resource_interrupted=False, result=size))
            decision.numerical_rejection(dict(proposal=proposal, search=None, training=None,
                                               rejection=rejection))
            arm.guard(window)
            return dict(completed=True, rejection=rejection)
        folder = arm.output/f'{proposal}-solve'
        parent = solver.run_solver(self.config['solver_python'], input_path, proposal,
            self.config['solver_environment'], self.config['solver_environment_sha256'],
            folder, arm.output, self.config['revision'], window.monotonic, window.wall,
            clock_origin=[arm.started, arm.wall_started])
        arm.guard(window)
        if parent.get('cleanup_failed'):
            raise solver.CleanupError('equilibrium child cleanup uncertain')
        solved = dict(completed=True, rejection=None, folder=str(folder), parent=parent,
                      input_path=str(folder/'input.json'), wout=str(folder/'wout.nc'))
        if not parent['completed']:
            process = parent.get('process', {})
            check.need(process.get('stop_reason') is None and process.get('returncode') == 1,
                       'unclassified or interrupted solver failure')
            request = solver.read(folder/'request.json')
            failure = solver.read(folder/'solver.json')
            solver.check_sources(parent['sources_before'])
            check.need(solver.digest(folder/'request.json') == parent['request_sha256']
                       and failure['request_sha256'] == parent['request_sha256']
                       and failure['input_sha256'] == target.INPUT_HASHES[proposal]
                       and failure['proposal'] == proposal and failure['completed']
                       and failure['environment_sha256'] == request['environment_sha256']
                       == self.config['solver_environment_sha256']
                       and failure['environment_unchanged'] and failure['sources_unchanged']
                       and failure['input_roundtrip_exact'] and failure['output_input_exact'],
                       'documented solver failure provenance required')
            check.bind(folder/'wout.nc', failure['wout_sha256'], state['sources'])
            solved['rejection'] = dict(kind='equilibrium', evidence=dict(proposal=proposal,
                input_sha256=target.INPUT_HASHES[proposal], completed=True,
                resource_interrupted=False, result=failure))
            decision.numerical_rejection(dict(proposal=proposal, search=None, training=None,
                                               rejection=solved['rejection']))
        for name in ('parent.json', 'request.json', 'solver.json', 'input.json', 'wout.nc'):
            check.bind(folder/name, check.digest(folder/name), state['sources'])
        self.verify(arm)
        arm.guard(window)
        state['solved'][proposal] = solved
        return solved

    def freeze(self, arm, proposal, solved, training, fitted, window):
        arm.guard(window)
        self.verify(arm)
        request = dict(operation='freeze', arm_root=str(arm.output),
            clock_origin=[arm.started, arm.wall_started],
            window=dict(monotonic=window.monotonic, wall=window.wall),
            outer=dict(monotonic=window.monotonic, wall=window.wall))
        record = Recorder(arm.output/'selection', request, [solver.retained_bytes(arm.output)])
        input_path = check.ROOT/check.TARGET if proposal == 'control' else solved['input_path']
        wout = self.config['wout'] if proposal == 'control' else solved['wout']
        frozen = decision.freeze_selection(proposal, training, fitted['search'],
            fitted['ordinary_fit_cap'], fitted['snapshot'], input_path, wout, record)
        path = record.output/'frozen-selection.json'
        check.bind(path, check.digest(path), self.states[arm.name]['sources'])
        self.states[arm.name]['frozen'] = frozen
        arm.guard(window)
        return frozen

    def diagnose(self, arm, frozen, window):
        proposal = frozen['proposal']
        solved = self.states[arm.name]['solved'].get(proposal)
        return self.call(arm, 'diagnostics', proposal, solved, window, frozen=frozen)

    def save_proposal(self, arm, row):
        path = arm.output/f"{row['proposal']}-proposal.json"
        solver.save(path, row)
        check.bind(path, check.digest(path), self.states[arm.name]['sources'])
