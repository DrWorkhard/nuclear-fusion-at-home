"""Sequential bounded launcher; retain every command, exit and timeout."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

root = Path('/private/tmp/fusion-issue10-code-checks-v2-20261007')
output = Path('/private/tmp/issue10-full-qualification-v1')
controls = Path('/private/tmp/fusion-issue10-interior-20261007/artifacts/issue10-export-controls-v2')
revision = 'f40c53851e99f175f06257c17340e9b79237f3cb'
hashes = {'reference401': 'f59bd03f03c126db1820766be831e02da4e64767a15aedcfa0c8b2beedd456f8',
          'selected401': 'caa78f10048a4c5c920116dbd1c42d34a8ae267084ebdad5cb72844a6018b1f8'}
output.mkdir(exist_ok=False)
receipt = {'completed': False, 'producer_evaluator': revision, 'arms': [],
           'launcher_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'environment': dict(os.environ), 'external_timeout_seconds_per_arm': 600}
try:
    for target, expected in hashes.items():
        command = [sys.executable, '-I', '-S', 'scripts/qualify_dense_interior.py',
                   '--target', target, '--expected', str(controls / (target + '-native.json')),
                   '--expected-sha', expected, '--output', str(output / target),
                   '--revision', revision]
        row = {'target_id': target, 'command': command, 'completed': False}
        receipt['arms'].append(row)
        start, wall = time.monotonic(), time.time()
        with (output / (target + '-process.log')).open('xb') as stream:
            try:
                process = subprocess.run(command, cwd=root, stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=600)
                row['returncode'] = process.returncode
            except subprocess.TimeoutExpired:
                row['timed_out'] = True
                raise
        row.update(elapsed_s=time.monotonic()-start, wall_elapsed_s=time.time()-wall)
        if row['returncode'] != 0 or abs(row['elapsed_s']-row['wall_elapsed_s']) > 5:
            raise RuntimeError('Qualification process failed or clocks disagreed')
        row['completed'] = True
    receipt['completed'] = True
finally:
    (output / 'launch.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
print(json.dumps(receipt, indent=2))
