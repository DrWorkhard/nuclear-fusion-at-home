import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

root = Path('/tmp/fusion-pr18-fixes')
mode = sys.argv[1]
output = root / 'results' / ('review-' + mode + '-200')
cmd = ['/Users/sebastianwirkert/workspace/fusion/.venv/bin/python',
       '/tmp/fusion-serial-python.py', 'scripts', 'scripts/trace_surfaces.py',
       '--candidate', 'submissions/length-headroom-six-coil/candidate.json',
       '--wout', '/tmp/fusion-review-inputs/reference401.nc',
       '--output', str(output), '--transits', '200']
if mode.startswith('direct'):
    cmd.append('--direct')
env = dict(PATH='/usr/bin:/bin', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
           VECLIB_MAXIMUM_THREADS='1', MKL_NUM_THREADS='1', MPLCONFIGDIR='/tmp/fusion-mpl')
assert shutil.disk_usage(root).free >= 3*1024**3
started = time.monotonic()
status = dict(command=cmd, output=str(output), mode=mode, wall_seconds_limit=600,
              storage_bytes_limit=256*1024**2)
with open(f'/tmp/fusion-pr18-confirmation/{mode}.log', 'w') as log:
    p = subprocess.Popen(cmd, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                         start_new_session=True)
    while p.poll() is None:
        elapsed = time.monotonic()-started
        size = sum(f.stat().st_size for f in output.rglob('*') if f.is_file()) if output.exists() else 0
        if elapsed > 600 or size > 256*1024**2 or shutil.disk_usage(root).free < 2*1024**3:
            status['stopped'] = 'resource limit'
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
            break
        time.sleep(1)
    status.update(exit_code=p.wait(), seconds=time.monotonic()-started)
Path(f'/tmp/fusion-pr18-confirmation/{mode}-execution.json').write_text(json.dumps(status, indent=2))
print(json.dumps(status), flush=True)
