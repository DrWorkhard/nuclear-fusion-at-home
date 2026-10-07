"""Bound the periodic-return diagnosis using the reviewed process and receipt helpers."""

import time

START, WALL = time.monotonic(), time.time()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import signal  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HELPER_SHA = 'dfc4e8cb750e28aa8d399f6c64691659674a874a1c2f1126133424d82b3cd15b'
ENVIRONMENT_SHA = 'ad07af4aec0b0fb54c84499c2981efe52788c63795ace8199c71fbbeee4dbe70'
DISABLED = ('mpi4py',)
SERIAL = (f"import runpy,sys; sys.modules.update({{k:None for k in {DISABLED!r}}}); "
          "sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def run(config_path, config_sha, output, revision):
    need(digest(config_path) == config_sha, 'Frozen configuration required')
    config = json.loads(config_path.read_bytes())
    helper_path, environment_path = Path(config['supervisor']), Path(config['environment'])
    need(digest(helper_path) == HELPER_SHA, 'Exact reviewed supervision helpers required')
    need(digest(environment_path) == ENVIRONMENT_SHA, 'Frozen environment identity required')
    spec = importlib.util.spec_from_file_location('reviewed_supervisor', helper_path)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    supervisor.ROOT, supervisor.START, supervisor.WALL = ROOT, START, WALL
    supervisor.clean_head(revision)
    need(shutil.disk_usage(output.parent).free >= 3*1024**3, 'Initial reserve exhausted')
    output.mkdir(exist_ok=False)
    paths = [config_path, helper_path, environment_path,
             *sorted((ROOT/'scripts').glob('*.py')), *sorted((ROOT/'src').rglob('*.py')),
             ROOT/'docs/optimization/ISSUE48_PERIODIC_RETURN.md']
    sources = {str(p): digest(p) for p in paths}
    receipt = dict(completed=False, revision=revision, sources_before=sources,
                   serial_runner=SERIAL, disabled_native_packages=DISABLED,
                   driver_budget_s=300, supervisor_budget_s=330, output_limit_bytes=256*1024**2,
                   physical_admission=False)
    termination = [False]

    def request_stop(signum, frame):
        termination[0] = True

    def check_resources():
        need(not termination[0], 'Supervisor termination requested')
        need(max(time.monotonic()-START, time.time()-WALL) < 330, '330 s total budget exhausted')
        supervisor.guard(output)  # Unchanged disk/storage/dual-clock checks.

    previous_handler = signal.signal(signal.SIGTERM, request_stop)
    try:
        receipt['environment_files'] = supervisor.verify_environment(environment_path,
                                                                     check_resources)
        command = [sys.executable, '-c', SERIAL, str(ROOT/'scripts/diagnose_periodic_return.py'),
                   '--archive', config['archive'],
                   '--revision', revision, '--output', str(output/'run')]
        environment = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', TMPDIR='/private/tmp',
                           PYTHONDONTWRITEBYTECODE='1', MPLCONFIGDIR='/private/tmp/fusion-mpl',
                           MPLBACKEND='Agg', OMP_NUM_THREADS='1',
                           OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1',
                           MKL_NUM_THREADS='1')
        receipt['command'] = command
        (output/'start.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
        supervisor.supervise(command, environment, output, receipt, check_resources)
        report = json.loads((output/'run/result.json').read_bytes())
        need(report['completed'] and report['deadline_met'],
             'Incomplete periodic-return assessment')
        need(report['sources_before'] == report['sources_after'], 'Diagnostic inputs changed')
        receipt['sources_after'] = {p: digest(p) for p in sources}
        need(receipt['sources_after'] == sources, 'Source/input changed during supervision')
        count = supervisor.verify_environment(environment_path, check_resources)
        need(count == receipt['environment_files'], 'Environment identity changed')
        supervisor.clean_head(revision)
        check_resources()
        receipt['completed'] = True
    except Exception as error:
        receipt['error'] = f'{type(error).__name__}: {error}'[:1024]
    finally:
        try:
            receipt['termination_requested'] = termination[0]
            receipt = supervisor.finish_receipt(output, receipt, check_resources)
        finally:
            signal.signal(signal.SIGTERM, previous_handler)
    print(json.dumps({k: v for k, v in receipt.items() if k not in (
        'sources_before', 'sources_after', 'serial_runner', 'command')}, indent=2))
    return 0 if receipt['completed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--config-sha', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.config.resolve(), args.config_sha, args.output.resolve(),
                         args.revision))
