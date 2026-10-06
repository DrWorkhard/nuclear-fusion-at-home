"""One reviewed, fixed full-grid pair; reuse the immutable archive supervisor."""
import datetime
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path('/private/tmp/fusion-issue48-grid-20261007')
SUPERVISOR = Path('/private/tmp/fusion-issue53-evidence-20261006/scripts/run_coil_freedom.py')
NATIVE = Path('/Users/sebastianwirkert/workspace/fusion')
OUTPUT = NATIVE/'artifacts/issue48-full-grid-v1'
EXPECTED = '130347fe29e03852e257a63d0ce6ab9f828d2c85'
SUPERVISOR_COMMIT = '293d0a65601c8293c936617f720fcfe099b3a27f'
SUPERVISOR_SHA = 'bf415756945ae4d5b7a5c44fc9e41d2018af2822ff90deecf6827d126f98f5e3'


def clean_producer():
    return (subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                   text=True).strip() == EXPECTED
            and not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT,
                                            text=True).strip())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.datetime.now(datetime.UTC)


if not clean_producer():
    raise ValueError('clean reviewed producer required')
if (subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SUPERVISOR.parents[1],
                            text=True).strip() != SUPERVISOR_COMMIT
        or sha(SUPERVISOR) != SUPERVISOR_SHA):
    raise ValueError('reviewed immutable supervisor required')
spec = importlib.util.spec_from_file_location('bounded_supervisor', SUPERVISOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if module.shutil.disk_usage(OUTPUT.parent).free < module.START_RESERVE:
    raise OSError('3 GiB initial reserve required')
OUTPUT.mkdir(exist_ok=False)
pair = dict(producer=EXPECTED, source_clean=True, started_utc=utc().isoformat(),
            launcher_sha256=sha(Path(__file__)), supervisor_sha256=sha(SUPERVISOR),
            supervisor_source=SUPERVISOR_COMMIT, external_host_load_verified=False,
            agent_controlled_heavy_jobs='serial', driver_limit_s=1800,
            supervisor_limit_s=1860, clock_discrepancy_limit_s=5,
            arms=[], completed=False)
module.save(OUTPUT/'supervisor-start.json', pair)
for target, wout, target_input in (
    ('reference401', 'artifacts/plasma-design-v2/reference-fine/wout.nc',
     'evidence/plasma-design-v2/reference-input-401.json'),
    ('selected401', 'artifacts/plasma-balanced-v1/endpoints/selected-fine/native/wout.nc',
     'evidence/plasma-balanced-v1/selected-input-401.json'),
):
    arm = OUTPUT/target
    arm.mkdir(exist_ok=False)
    start_utc, started = utc(), time.monotonic()
    row = dict(target=target, started_utc=start_utc.isoformat(), completed=False,
               initial_free_bytes=module.shutil.disk_usage(arm).free)
    command = [sys.executable, '-c', module.SERIAL_RUNNER,
               str(ROOT/'scripts/measure_flux_labels.py'),
               '--snapshot', str(NATIVE/f'artifacts/issue25-matched-v1/{target}/fit/selected-snapshot.json'),
               '--wout', str(NATIVE/wout), '--target-input', str(NATIVE/target_input),
               '--target', target, '--output', str(arm/'run'),
               '--full-grid', '--half-period', '--crossings', '320', '--seconds', '1800']
    row['command'] = command
    module.save(arm/'supervisor-start.json', row)
    try:
        if row['initial_free_bytes'] < module.START_RESERVE or not clean_producer():
            raise ValueError('initial reserve or exact clean producer unavailable')
        row.update(module.supervise(command, arm, 'run', started+1860))
        if row['completed']:
            result = module.read(arm/'run/result.json')
            row['driver_completed'] = bool(result['completed'] and result['deadline_met']
                                          and result['sources_before'] == result['sources_after'])
            row['all_points_numerically_qualified'] = result['all_points_numerically_qualified']
            row['completed'] = row['driver_completed']
    except Exception as exc:
        row.update(completed=False, error=f'{type(exc).__name__}: {exc}',
                   cleanup_failed=isinstance(exc, module.CleanupError))
    finished = utc()
    row.update(finished_utc=finished.isoformat(), monotonic_elapsed_s=time.monotonic()-started,
               utc_elapsed_s=(finished-start_utc).total_seconds(),
               retained_bytes_before_final_report=module.retained_bytes(arm))
    row['clock_discrepancy_s'] = abs(row['utc_elapsed_s']-row['monotonic_elapsed_s'])
    row['clock_consistent'] = row['clock_discrepancy_s'] <= 5
    row['producer_unchanged'] = clean_producer()
    row['completed'] &= row['producer_unchanged'] and row['clock_consistent']
    module.save(arm/'supervisor-result.json', row)
    pair['arms'].append(row)
    module.save(OUTPUT/'supervisor-progress.json', pair)
    print(json.dumps(row, indent=2), flush=True)
    if row.get('cleanup_failed'):
        break
pair.update(finished_utc=utc().isoformat(), completed=len(pair['arms']) == 2
            and all(row['completed'] for row in pair['arms']))
module.save(OUTPUT/'supervisor-result.json', pair)
raise SystemExit(0 if pair['completed'] else 1)
