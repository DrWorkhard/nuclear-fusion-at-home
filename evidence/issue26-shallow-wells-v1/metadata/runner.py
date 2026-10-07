"""One bounded issue26 comparison; outer failure receipts retain partial outputs."""
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

root = Path('/private/tmp/fusion-issue26-shallow-wells-20261007')
output = Path('/private/tmp/issue26-shallow-wells-v1')
revision = '568a96a428fbb730ff23568ef917ab2b947fa255'
config = Path('/private/tmp/issue26-shallow-config-v1.json')
config_sha = '25a50f00b010f78cac7f8329a53861a9e6452e0d9f256a2aed03c5d78fe4b2d0'
wrapper = Path('/private/tmp/fusion-serial-python.py')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip()
    if head != revision or dirty or digest(config) != config_sha:
        raise ValueError('Frozen clean code/configuration required')

check()
if shutil.disk_usage(root).free < 3*1024**3:
    raise ValueError('Initial disk reserve violated')
output.mkdir(exist_ok=False)
command = [sys.executable, str(wrapper), 'script', 'scripts/compare_interior_wells.py',
           '--config', str(config), '--config-sha', config_sha, '--revision', revision,
           '--output', str(output/'run')]
receipt = dict(completed=False, revision=revision, command=command,
               runner_sha256=digest(Path(__file__)), wrapper_sha256=digest(wrapper),
               config_sha256=config_sha, budget_s=900, output_limit_bytes=64*1024**2,
               live_reserve_bytes=2*1024**3, maximum_clock_difference_s=5)
start, wall = time.monotonic(), time.time()
process = None
try:
    with (output/'stdout.log').open('xb') as stdout, (output/'stderr.log').open('xb') as stderr:
        process = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr)
        while process.poll() is None:
            elapsed, wall_elapsed = time.monotonic()-start, time.time()-wall
            if max(elapsed, wall_elapsed) >= 900:
                raise TimeoutError('900 s total budget exhausted')
            if abs(elapsed-wall_elapsed) > 5:
                raise RuntimeError('Wall/monotonic clock discrepancy exceeds 5 s')
            if shutil.disk_usage(root).free < 2*1024**3:
                raise OSError('Live disk reserve violated')
            size = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
            if size > 64*1024**2-64*1024:
                raise OSError('Aggregate output reserve exhausted')
            time.sleep(0.1)
    receipt['returncode'] = process.returncode
    if process.returncode != 0:
        raise RuntimeError('Comparison process failed; inspect retained output')
    check()
    report = json.loads((output/'run/result.json').read_bytes())
    if not report['completed'] or (output/'run/failure.json').exists():
        raise RuntimeError('Incomplete comparison')
    receipt.update(completed=True, decision=report['decision'])
except Exception as error:
    receipt['error'] = f'{type(error).__name__}: {error}'[:1024]
finally:
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
    receipt.update(elapsed_s=time.monotonic()-start, wall_elapsed_s=time.time()-wall)
    if (max(receipt['elapsed_s'], receipt['wall_elapsed_s']) >= 900
            or abs(receipt['elapsed_s']-receipt['wall_elapsed_s']) > 5):
        receipt['completed'] = False
    receipt['retained_files'] = {str(p.relative_to(output)): dict(sha256=digest(p),
                                 bytes=p.stat().st_size)
                                 for p in sorted(output.rglob('*')) if p.is_file()}
    payload = (json.dumps(receipt, indent=2)+'\n').encode('utf-8')
    retained = sum(row['bytes'] for row in receipt['retained_files'].values())
    if retained+len(payload) > 64*1024**2:
        raise OSError('Receipt cannot fit aggregate output limit')
    (output/'receipt.json').write_bytes(payload)
print(json.dumps({k: v for k, v in receipt.items() if k not in ('retained_files', 'command')},
                 indent=2))
raise SystemExit(0 if receipt['completed'] else 1)
