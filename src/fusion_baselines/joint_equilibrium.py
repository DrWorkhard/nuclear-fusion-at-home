"""One registered cold equilibrium solve with caller-owned budgets and provenance."""
import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES, START_RESERVE, LIVE_RESERVE = 256*1024**2, 3*1024**3, 2*1024**3
REPORT_RESERVE = 1024**2
PACKAGES = ('vmecpp', 'numpy', 'scipy', 'pydantic', 'pydantic_core', 'netCDF4',
            'cftime', 'jaxtyping', 'typing_extensions', 'typing_inspection', 'annotated_types')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    with temporary.open('x') as stream:
        stream.write(json.dumps(value, allow_nan=False, sort_keys=True, indent=2)+'\n')
    temporary.replace(path)


def identity():
    """Executable and installed Python/native package files, excluding bytecode caches."""
    record = dict(python=sys.version, executable=str(Path(sys.executable).resolve()),
                  executable_sha256=digest(Path(sys.executable).resolve()), packages={})
    for name in PACKAGES:
        distribution = importlib.metadata.distribution(name)
        files = {}
        for entry in distribution.files or []:
            if Path(entry).suffix in ('.py', '.so', '.dylib', '.dll', '.pyd') or Path(
                    entry).name in ('METADATA', 'WHEEL'):
                files[str(entry)] = digest(distribution.locate_file(entry))
        if not files:
            raise ValueError(f'installed package file inventory unavailable: {name}')
        record['packages'][name] = dict(version=distribution.version, files=files)
    return record


def check_sources(sources):
    if any(digest(path) != expected for path, expected in sources.items()):
        raise ValueError('bound solver source/input changed')


def retained_bytes(root):
    total = 0
    for path in Path(root).rglob('*'):
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            pass  # Atomic publication may rename while the parent scans.
    return total


def stop_reason(root, deadline_monotonic, deadline_wall):
    mono, wall = time.monotonic(), time.time()
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
               for v in (deadline_monotonic, deadline_wall)):
        raise ValueError('finite absolute caller deadlines required')
    if abs((deadline_monotonic-mono)-(deadline_wall-wall)) > 5:
        return 'clock disagreement'
    if mono >= deadline_monotonic or wall >= deadline_wall:
        return 'deadline'
    if retained_bytes(root) > MAX_BYTES-REPORT_RESERVE:
        return 'aggregate storage ceiling'
    if shutil.disk_usage(root).free < LIVE_RESERVE:
        return 'live disk reserve'
    return None


class CleanupError(RuntimeError):
    """Unknown process-group state forbids subsequent work."""


def stop(process):
    # Reuse issue53's reviewed cleanup, including descendants of exited leaders.
    process.poll()
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        raise CleanupError('cannot terminate child process group') from exc
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError as exc:
            raise CleanupError('cannot confirm child process-group cleanup') from exc
    process.wait()


def supervise(command, folder, arm_root, deadline_monotonic, deadline_wall):
    """No deadline reset; all sibling outputs count against the caller's arm cap."""
    if os.name != 'posix':
        raise ValueError('POSIX process-group supervision required')
    started = time.monotonic()
    environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', TMPDIR=str(folder),
                       PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
                       OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', MKL_NUM_THREADS='1')
    reason, process = stop_reason(arm_root, deadline_monotonic, deadline_wall), None
    state = dict(terminate=False)

    def terminated(signum, frame):
        # A flag cannot interrupt Popen before its handle is assigned or interrupt
        # the cleanup itself. The watchdog observes it within its 0.1 s interval.
        state['terminate'] = True

    previous = signal.signal(signal.SIGTERM, terminated)
    try:
        try:
            if reason is None:
                with (folder/'solver.log').open('xb') as log:
                    process = subprocess.Popen(command, cwd=folder, env=environment,
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                        start_new_session=True)
                    while True:
                        reason = ('supervisor SIGTERM' if state['terminate'] else
                                  stop_reason(arm_root, deadline_monotonic, deadline_wall))
                        if reason is not None or process.poll() is not None:
                            break
                        time.sleep(.1)
        finally:
            if process is not None:
                stop(process)
    finally:
        signal.signal(signal.SIGTERM, previous)
    reason = reason or ('supervisor SIGTERM' if state['terminate'] else None) or stop_reason(
        arm_root, deadline_monotonic, deadline_wall)
    return dict(command=command, returncode=None if process is None else process.returncode,
                stop_reason=reason, elapsed_s=time.monotonic()-started,
                completed=reason is None and process is not None and process.returncode == 0)


def worker(request_path):
    """Worker success is insufficient until the independent parent accepts the run."""
    from fusion_baselines import joint_target as target

    request_path = Path(request_path)
    folder = request_path.parent
    if (folder/'solver.json').exists() or (folder/'wout.nc').exists():
        raise FileExistsError('fresh unsolved cell required')
    request_sha = digest(request_path)
    request = read(request_path)
    report = dict(completed=False, converged=False, input_sha256=request['input_sha256'],
                  request_sha256=request_sha, proposal=request['proposal'],
                  environment_sha256=request['environment_sha256'])
    started = time.monotonic()
    try:
        check_sources(request['sources'])
        lock = read(request['environment'])
        if identity() != lock:
            raise ValueError('solver environment differs from frozen inventory')
        if not all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                    'VECLIB_MAXIMUM_THREADS', 'MKL_NUM_THREADS')):
            raise ValueError('one-thread solver execution required')
        document, _ = target.registered_input(folder/'input.json', request['proposal'], {})
        import vmecpp

        module_files = {str(Path(sys.modules[k].__file__).resolve()):
                        digest(sys.modules[k].__file__)
                        for k in ('vmecpp', 'vmecpp.cpp._vmecpp')}
        expected_root = Path(importlib.metadata.distribution('vmecpp').locate_file('')).resolve()
        if any(not Path(p).is_relative_to(expected_root) for p in module_files):
            raise ValueError('imported solver is outside the frozen distribution')
        report['solver_module_files'] = module_files
        parsed = vmecpp.VmecInput.model_validate(document)
        if parsed.model_dump(mode='json') != document:
            raise ValueError('solver input conversion changed registered values')
        if parsed.return_outputs_even_if_not_converged is not False:
            raise ValueError('nonconvergence override forbidden')
        report['input_roundtrip_exact'] = True
        save(folder/'solver-start.json', report)
        reason = stop_reason(request['arm_root'], request['deadline_monotonic'],
                             request['deadline_wall'])
        if reason:
            raise TimeoutError(reason)
        result = vmecpp.run(parsed, max_threads=1, verbose=True,
                            restart_from=None, magnetic_field=None)
        result.wout.save(folder/'wout.nc')
        if parsed.model_dump(mode='json') != document or result.input.model_dump(
                mode='json') != document:
            raise ValueError('solver changed the registered input')
        report['output_input_exact'] = True
        check_sources(module_files)
        residuals = {k: float(getattr(result.wout, k)) for k in ('fsqr', 'fsqz', 'fsql')}
        if not all(math.isfinite(v) for v in residuals.values()):
            raise ValueError(f'nonfinite force residuals: {residuals}')
        converged = (int(result.wout.ier_flag) == 0 and int(result.wout.ns) == 401
                     and all(math.isfinite(v) and 0 <= v <= document['ftol_array'][-1]
                             for v in residuals.values()))
        check_sources(request['sources'])
        if identity() != lock or digest(request_path) != request_sha:
            raise ValueError('solver environment/request changed during execution')
        report.update(completed=True, converged=converged, residuals=residuals,
                      niter=int(result.wout.niter), wout_sha256=digest(folder/'wout.nc'),
                      sources_unchanged=True, environment_unchanged=True)
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    report['elapsed_s'] = time.monotonic()-started
    save(folder/'solver.json', report)
    return 0 if report['completed'] and report['converged'] else 1


def run_solver(python, input_path, proposal, environment, environment_sha256, folder,
               arm_root, revision, deadline_monotonic, deadline_wall):
    """Run exactly one solve; retain a failure and never retry or certify its field here."""
    from fusion_baselines import joint_target as target
    from fusion_baselines.provenance import build_run_record

    folder, arm_root = Path(folder).resolve(), Path(arm_root).resolve()
    if not folder.is_relative_to(arm_root) or folder == arm_root:
        raise ValueError('fresh solver cell must be inside the caller arm root')
    if shutil.disk_usage(arm_root).free < START_RESERVE:
        raise OSError('3 GiB initial disk reserve required')
    reason = stop_reason(arm_root, deadline_monotonic, deadline_wall)
    if reason:
        raise TimeoutError(reason)
    folder.mkdir(exist_ok=False)
    record = dict(completed=False, provenance=build_run_record(ROOT),
                  physical_admission=False, proposal=proposal,
                  deadline_monotonic=deadline_monotonic, deadline_wall=deadline_wall)
    sources = {}
    started, wall_started = time.monotonic(), time.time()
    try:
        repo = record['provenance']['repository']
        if repo['commit'] != revision or repo['dirty']:
            raise ValueError('clean reviewed runner source required')
        document, original = target.registered_input(input_path, proposal, sources)
        env_path = target.check.bind(environment, environment_sha256, sources)
        lock = read(env_path)
        executable = Path(python).resolve()
        if str(executable) != lock['executable'] or digest(executable) != lock['executable_sha256']:
            raise ValueError('solver interpreter differs from frozen inventory')
        for path in [*sorted((ROOT/'src/fusion_baselines').glob('*.py')),
                     ROOT/'scripts/solve_joint_target.py']:
            sources[str(path.resolve())] = digest(path)

        def guard():
            reason = stop_reason(arm_root, deadline_monotonic, deadline_wall)
            if reason:
                raise TimeoutError(reason)

        record['size'] = target.size_check(document, original, guard)
        (folder/'input.json').write_bytes(Path(input_path).read_bytes())
        sources[str(folder/'input.json')] = target.INPUT_HASHES[proposal]
        request = dict(proposal=proposal, input_sha256=target.INPUT_HASHES[proposal],
                       environment=str(env_path), environment_sha256=environment_sha256,
                       sources=sources, producer=revision, arm_root=str(arm_root),
                       deadline_monotonic=deadline_monotonic, deadline_wall=deadline_wall)
        save(folder/'request.json', request)
        record.update(request_sha256=digest(folder/'request.json'), sources_before=dict(sources),
                      environment_sha256=environment_sha256)
        save(folder/'parent-start.json', record)
        guard()
        command = [str(python), '-I', str(ROOT/'scripts/solve_joint_target.py'),
                   '--request', str(folder/'request.json')]
        record['process'] = supervise(command, folder, arm_root, deadline_monotonic, deadline_wall)
        if not record['process']['completed']:
            raise RuntimeError('solver subprocess incomplete')
        result = read(folder/'solver.json')
        if (not result['completed'] or not result['converged']
                or result['request_sha256'] != record['request_sha256']
                or result['input_sha256'] != target.INPUT_HASHES[proposal]
                or result['proposal'] != proposal
                or result['environment_sha256'] != environment_sha256
                or not result['environment_unchanged'] or not result['sources_unchanged']
                or not result['input_roundtrip_exact'] or not result['output_input_exact']):
            raise ValueError('solver provenance or convergence binding failed')
        check_sources(sources)
        if digest(folder/'request.json') != record['request_sha256']:
            raise ValueError('solver request changed')
        target.check.bind(folder/'wout.nc', result['wout_sha256'], {})
        guard()
        record.update(completed=True, wout_sha256=result['wout_sha256'], solver=result,
                      sources_after={p: digest(p) for p in sources},
                      solver_report_sha256=digest(folder/'solver.json'))
        if record['sources_after'] != record['sources_before']:
            raise ValueError('source changed during final identity verification')
        guard()
    except Exception as exc:
        record.update(completed=False, error=f'{type(exc).__name__}: {exc}',
                      cleanup_failed=isinstance(exc, CleanupError))
    record.update(elapsed_s=time.monotonic()-started, wall_elapsed_s=time.time()-wall_started)
    reason = stop_reason(arm_root, deadline_monotonic, deadline_wall)
    if reason:
        record.update(completed=False, stop_reason=reason)
    save(folder/'parent.json', record)
    reason = stop_reason(arm_root, deadline_monotonic, deadline_wall)
    if reason:
        record.update(completed=False, stop_reason=reason)
        save(folder/'parent.json', record)
    record['record_sha256'] = digest(folder/'parent.json')
    reason = stop_reason(arm_root, deadline_monotonic, deadline_wall)
    if reason:
        record.pop('record_sha256')
        record.update(completed=False, stop_reason=reason)
        save(folder/'parent.json', record)
        record['record_sha256'] = digest(folder/'parent.json')
    return record


def intake_result(folder, record, guard):
    """Consume the trusted parent's in-memory receipt, then independently verify fields."""
    from fusion_baselines import joint_target as target

    folder = Path(folder)
    guard()
    if not record['completed'] or digest(folder/'parent.json') != record['record_sha256']:
        raise ValueError('completed unchanged parent receipt required')
    if read(folder/'parent.json') != {k: v for k, v in record.items() if k != 'record_sha256'}:
        raise ValueError('parent receipt differs from trusted run result')
    if digest(folder/'solver.json') != record['solver_report_sha256']:
        raise ValueError('worker receipt changed')
    if digest(folder/'request.json') != record['request_sha256']:
        raise ValueError('solver request changed')
    check_sources(record['sources_before'])
    if record['sources_before'] != record['sources_after']:
        raise ValueError('solver source changed')
    data, targets, sources, numerical = target.intake(folder/'input.json', folder/'wout.nc',
        record['proposal'], record['wout_sha256'], guard)
    check_sources(record['sources_before'])
    check_sources({str(folder/'parent.json'): record['record_sha256'],
                   str(folder/'solver.json'): record['solver_report_sha256'],
                   str(folder/'request.json'): record['request_sha256']})
    guard()
    numerical.update(solver_provenance_verified=True, parent_sha256=record['record_sha256'],
                     solver_report_sha256=record['solver_report_sha256'],
                     environment_sha256=record['environment_sha256'])
    return data, targets, sources, numerical
