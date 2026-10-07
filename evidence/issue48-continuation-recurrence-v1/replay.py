"""Recompute saved-sample diagnostics; never trace or change qualification."""

import time

START = time.monotonic()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import runpy  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

PAYLOAD = Path(__file__).resolve().parent
ROOT = PAYLOAD.parents[1]


def need(condition, message):
    if not condition:
        raise ValueError(message)
    if time.monotonic()-START >= 60:
        raise TimeoutError('60-second saved-arithmetic replay budget exhausted')


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(manifest_sha):
    need(digest(PAYLOAD/'manifest.json') == manifest_sha, 'Wrong evidence manifest')
    manifest = read(PAYLOAD/'manifest.json')
    for relative, expected in manifest.items():
        path = (PAYLOAD/relative).resolve()
        need(path.is_relative_to(PAYLOAD), 'Manifest path escapes payload')
        need(digest(path) == expected, f'Evidence hash mismatch: {relative}')
    bindings = read(PAYLOAD/'metadata/source-bindings.json')
    for original, row in bindings.items():
        path = (ROOT/row['archive_path']).resolve()
        need(path.is_relative_to(ROOT), 'Source path escapes checkout')
        need(digest(path) == row['sha256'], f'Source mismatch: {original}')
    report = read(PAYLOAD/'raw/run/result.json')
    receipt = read(PAYLOAD/'raw/receipt.json')
    for record in (report, receipt):
        need(record['completed'], 'Original attempt incomplete')
        need(record['sources_before'] == record['sources_after'], 'Original source change')
        for original, sha in record['sources_before'].items():
            need(bindings[original]['sha256'] == sha, 'Missing original source identity')
    need(report['deadline_met'] and receipt['cleanup_confirmed'], 'Incomplete original run')
    sys.modules.update({name: None for name in
                        ('simsopt', 'simsoptpp', 'mpi4py', 'netCDF4', 'vmecpp', 'matplotlib')})
    study = runpy.run_path(str(ROOT/'scripts/diagnose_saved_recurrence.py'))
    need(study['controls']() == report['controls'], 'Analytic controls changed')
    cases = []
    for target, index in study['CASES']:
        base = PAYLOAD/'inputs'/target/study['RUNS'][target]
        original = read(base/'result.json')
        need(original['completed'] and original['deadline_met'], 'Original trace incomplete')
        line = original['lines'][index]
        need(line['index'] == index and line['s'] == .5, 'Wrong frozen launch')
        center = np.asarray(original['center_RZ'])
        with np.load(base/f'line-{index}.npz', allow_pickle=False) as data:
            hits = data['hits'].copy()
        hits = hits[(hits[:, 1] >= 0) & (hits[:, 0] > 1e-8)]
        hits = hits[np.argsort(hits[:, 0], kind='stable')][:640]
        need(len(hits) == 640, 'Missing pooled crossings')
        rz = np.column_stack((np.hypot(hits[:, 2], hits[:, 3]), hits[:, 4]))
        row = dict(target=target, index=index, theta=line['theta'],
                   original_qualified=line['passed'], original_iota=line['iota'],
                   pooled=[study['interpolation_check'](rz[:n], center)
                           for n in (160, 320, 640)], planes=[])
        for plane in (0, 1):
            points = rz[hits[:, 1] == plane]
            need(len(points) == 320, 'Missing plane crossings')
            row['planes'].append(dict(plane=plane, **study['recurrence'](points, center)))
        cases.append(row)
    need(cases == report['cases'], 'Saved-sample diagnostics changed')
    need(not report['physical_admission']
         and report['dynamical_classification'] == 'not established', 'Claim changed')
    result = dict(completed=True, manifest_files=len(manifest), source_bindings=len(bindings),
                  cases=len(cases), planes=10, residue_sequences=110, exact_agreement=True,
                  elapsed_s=time.monotonic()-START, physical_admission=False,
                  scope='Same NumPy/SciPy kernels, saved crossings only; no retracing, '
                        'native field calculation, environment or timing reproduction')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha', required=True)
    replay(parser.parse_args().manifest_sha)
