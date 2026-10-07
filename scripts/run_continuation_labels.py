"""Supervise the single frozen continuation-label grid, including startup and receipts."""

import time

START, WALL = time.monotonic(), time.time()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.metadata  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import signal  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = '73972fc86375fcffa67a44833d1c87016e7ff9d070857aac97acc1dcf335bb97'
WOUT = '83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e'
ENVIRONMENT = 'ad07af4aec0b0fb54c84499c2981efe52788c63795ace8199c71fbbeee4dbe70'
SERIAL = ("import runpy,sys; sys.modules['mpi4py']=None; "
          "sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')")
MAX_BYTES = 256*1024**2


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean_head(revision):
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()
    need(head == revision and not dirty, 'Exact clean reviewed revision required')


def retained_bytes(output):
    size = 0
    for path in output.rglob('*'):
        try:
            if path.is_file():
                size += path.stat().st_size
        except FileNotFoundError:  # Atomic publication can race the watchdog.
            pass
    return size


def guard(output):
    elapsed, wall = time.monotonic()-START, time.time()-WALL
    need(max(elapsed, wall) < 1800, '1800 s total budget exhausted')
    need(abs(elapsed-wall) <= 5, 'Wall/monotonic clock discrepancy exceeds 5 s')
    need(shutil.disk_usage(output.parent).free >= 2*1024**3, 'Live disk reserve exhausted')
    need(retained_bytes(output) <= MAX_BYTES-64*1024, 'Aggregate output reserve exhausted')


def verify_environment(path, output):
    environment = json.loads(path.read_bytes())
    need(sys.version == environment['python'], 'Frozen Python version required')
    need(digest(sys.executable) == environment['executable_sha256'], 'Python executable changed')
    count = 0
    for name, row in environment['packages'].items():
        distribution = importlib.metadata.distribution(name)
        need(distribution.version == row['version'], 'Native package version changed')
        for relative, expected in row['files'].items():
            guard(output)
            need(digest(distribution.locate_file(relative)) == expected,
                 f'Native package file changed: {relative}')
            count += 1
    return count


def stop(process):
    process.poll()
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait()


def finish_receipt(output, receipt):
    def save(value):
        payload = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode('utf-8')
        need(retained_bytes(output)+len(payload) <= MAX_BYTES, 'Failure receipt exceeds cap')
        (output/'receipt.json').write_bytes(payload)

    receipt.update(elapsed_s=time.monotonic()-START, wall_elapsed_s=time.time()-WALL,
                   retained_bytes_before_receipt=retained_bytes(output))
    save(receipt)
    try:
        guard(output)  # Publication itself cannot complete after the declared budget.
    except Exception as error:
        (output/'receipt.json').rename(output/'attempted-receipt.json')
        receipt = dict(completed=False, revision=receipt['revision'],
                       error=f'{type(error).__name__}: {error}'[:1024],
                       elapsed_s=time.monotonic()-START, wall_elapsed_s=time.time()-WALL,
                       retained_attempt='attempted-receipt.json', physical_admission=False)
        save(receipt)
    return receipt


def run(config_path, config_sha, output, revision):
    clean_head(revision)
    need(digest(config_path) == config_sha, 'Frozen configuration required')
    need(shutil.disk_usage(output.parent).free >= 3*1024**3, 'Initial disk reserve exhausted')
    config = json.loads(config_path.read_bytes())
    paths = {'snapshot': Path(config['snapshot']), 'wout': Path(config['wout']),
             'environment': Path(config['environment'])}
    for name, expected in [('snapshot', SNAPSHOT), ('wout', WOUT), ('environment', ENVIRONMENT)]:
        need(digest(paths[name]) == expected, f'Frozen {name} identity required')
    sources = {str(p): digest(p) for p in [config_path, *paths.values(),
               *sorted((ROOT/'scripts').glob('*.py')), *sorted((ROOT/'src').rglob('*.py')),
               ROOT/'docs/optimization/ISSUE48_CONTINUATION_LABELS.md']}
    output.mkdir(exist_ok=False)
    receipt = dict(completed=False, revision=revision, sources_before=sources,
                   serial_runner=SERIAL, budget_s=1800, output_limit_bytes=MAX_BYTES,
                   wall_start_unix=WALL, physical_admission=False)
    process = None
    try:
        receipt['environment_files'] = verify_environment(paths['environment'], output)
        command = [sys.executable, '-c', SERIAL, str(ROOT/'scripts/measure_flux_labels.py'),
                   '--snapshot', str(paths['snapshot']), '--wout', str(paths['wout']),
                   '--target', 'reference401', '--output', str(output/'run'),
                   '--full-grid', '--half-period', '--crossings', '320', '--seconds', '1800']
        environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', TMPDIR='/private/tmp',
                           PYTHONDONTWRITEBYTECODE='1', MPLCONFIGDIR=str(output/'mpl-cache'),
                           OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                           VECLIB_MAXIMUM_THREADS='1', MKL_NUM_THREADS='1')
        receipt['command'] = command
        with (output/'start.json').open('x', encoding='utf-8') as stream:
            json.dump(receipt, stream, indent=2)
        guard(output)
        with (output/'run.log').open('xb') as log:
            process = subprocess.Popen(command, cwd=ROOT, env=environment,
                                       stdin=subprocess.DEVNULL, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            while True:
                guard(output)
                if process.poll() is not None:
                    break
                time.sleep(.1)
        stop(process)
        receipt['returncode'] = process.returncode
        need(process.returncode == 0, 'Scientific driver failed; retain partial output')
        report = json.loads((output/'run/result.json').read_bytes())
        need(report['completed'] and report['deadline_met'], 'Incomplete scientific driver')
        receipt['sources_after'] = {p: digest(p) for p in sources}
        need(receipt['sources_after'] == sources, 'Source/input changed during run')
        need(verify_environment(paths['environment'], output) == receipt['environment_files'],
             'Native environment changed')
        clean_head(revision)
        guard(output)
        receipt.update(completed=True,
                       all_points_numerically_qualified=report['all_points_numerically_qualified'])
    except Exception as error:
        receipt['error'] = f'{type(error).__name__}: {error}'[:1024]
    finally:
        if process is not None and process.poll() is None:
            stop(process)
        receipt = finish_receipt(output, receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in (
        'sources_before', 'sources_after', 'serial_runner', 'command')}, indent=2))
    return 0 if receipt['completed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.config.resolve(), args.config_sha, args.output.resolve(),
                         args.revision))
