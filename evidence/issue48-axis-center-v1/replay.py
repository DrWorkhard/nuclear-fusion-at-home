"""Verify archived identities and replay saved-center geometry, without native fields."""
import argparse
import hashlib
import json
import runpy
import sys
import time
from pathlib import Path

import numpy as np

START = time.monotonic()
PAYLOAD = Path(__file__).resolve().parent
ROOT = PAYLOAD.parents[1]


def need(condition, message):
    if not condition:
        raise ValueError(message)
    if time.monotonic()-START > 60:
        raise TimeoutError('60 second replay ceiling')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(manifest_sha):
    need(digest(PAYLOAD/'manifest.json') == manifest_sha, 'wrong manifest')
    manifest = json.loads((PAYLOAD/'manifest.json').read_bytes())
    for name, sha in manifest.items():
        path = (PAYLOAD/name).resolve()
        need(path.is_relative_to(PAYLOAD) and digest(path) == sha, 'payload mismatch: '+name)
    counts = {}
    for version in ('v1', 'v2'):
        bindings = json.loads((PAYLOAD/'metadata'/f'source-bindings-{version}.json').read_bytes())
        for original, row in bindings.items():
            path = (ROOT/row['archive_path']).resolve()
            need(path.is_relative_to(ROOT) and digest(path) == row['sha256'], original)
        records = [PAYLOAD/'raw'/version/'receipt.json']
        if version == 'v2':
            records.append(PAYLOAD/'raw/v2/run/result.json')
        for path in records:
            record = json.loads(path.read_bytes())
            for name, sha in record['sources_before'].items():
                need(bindings[name]['sha256'] == sha, 'missing source identity')
            if version == 'v2':
                need(record['completed'] and record['sources_before'] == record['sources_after'],
                     'incomplete successful attempt')
            else:
                need(not record['completed'], 'failed startup must remain failed')
        counts[version] = len(bindings)
    sys.modules.update({name: None for name in
                        ('simsopt', 'simsoptpp', 'mpi4py', 'netCDF4', 'vmecpp', 'matplotlib')})
    saved = runpy.run_path(str(ROOT/'scripts/diagnose_saved_recurrence.py'))
    report = json.loads((PAYLOAD/'raw/v2/run/result.json').read_bytes())
    for case in report['cases']:
        target, index = case['target'], case['index']
        path = PAYLOAD/'inputs'/target/saved['RUNS'][target]/f'line-{index}.npz'
        with np.load(path, allow_pickle=False) as data:
            hits = data['hits'].copy()
        hits = hits[(hits[:, 1] >= 0) & (hits[:, 0] > 1e-8)]
        hits = hits[np.argsort(hits[:, 0], kind='stable')][:640]
        need(len(hits) == 640, 'missing saved crossings')
        rz = np.column_stack((np.hypot(hits[:, 2], hits[:, 3]), hits[:, 4]))
        for row in case['centers'].values():
            center = np.asarray(row['center_RZ'])
            need(saved['gap'](rz, center) == row['pooled_gap_rad'], 'gap changed')
            for plane in row['planes']:
                actual = saved['recurrence'](rz[hits[:, 1] == plane['plane']], center)
                need(dict(plane=plane['plane'], **actual) == plane, 'recurrence changed')
    need(report['original_qualification_unchanged'] and not report['physical_admission'],
         'claim changed')
    print(json.dumps(dict(completed=True, manifest_files=len(manifest), source_bindings=counts,
                          cases=len(report['cases']), residue_sequences=220,
                          exact_saved_geometry_agreement=True, elapsed_s=time.monotonic()-START,
                          scope='Same NumPy kernels and stored centers; no periodic-root solve, '
                                'native field calculation, retracing or timing reproduction'),
                     indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha', required=True)
    replay(parser.parse_args().manifest_sha)
