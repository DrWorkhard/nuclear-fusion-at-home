"""Replay paired saved-crossing arithmetic, not either field-line integrator."""
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
    bindings = json.loads((PAYLOAD/'metadata/source-bindings.json').read_bytes())
    for name, row in bindings.items():
        path = (ROOT/row['archive_path']).resolve()
        need(path.is_relative_to(ROOT) and digest(path) == row['sha256'], name)
    for relative in ('raw/receipt.json', 'raw/run/result.json'):
        record = json.loads((PAYLOAD/relative).read_bytes())
        need(record['completed'] and record['sources_before'] == record['sources_after'],
             'incomplete original attempt')
        for name, sha in record['sources_before'].items():
            need(bindings[name]['sha256'] == sha, 'source binding missing')
    sys.modules.update({name: None for name in
                        ('simsopt', 'simsoptpp', 'mpi4py', 'netCDF4', 'vmecpp', 'matplotlib')})
    study = runpy.run_path(str(ROOT/'scripts/diagnose_trace_refinement.py'))
    saved = study['saved']
    report = json.loads((PAYLOAD/'raw/run/result.json').read_bytes())
    original = json.loads((PAYLOAD/'inputs/raw/run/result.json').read_bytes())
    center = np.asarray(original['center_RZ'])
    outcomes = []
    for case in report['cases']:
        index = case['index']
        with np.load(PAYLOAD/f'inputs/raw/run/line-{index}.npz', allow_pickle=False) as data:
            old, planes = study['saved_crossings'](data['hits'])
        with np.load(PAYLOAD/f'raw/run/line-{index}.npz', allow_pickle=False) as data:
            new = data['rz'].copy()
            need(np.array_equal(data['planes'], planes), 'plane pairing changed')
        need(new.shape == old.shape == (640, 2), 'complete paired crossings required')
        delta = np.linalg.norm(new-old, axis=1)
        need(float(np.max(delta)) == case['maximum_crossing_difference_m'], 'maximum changed')
        need(float(np.sqrt(np.mean(delta**2))) == case['rms_crossing_difference_m'], 'RMS changed')
        counts = []
        for label, rz in (('original', old), ('refined', new)):
            actual = dict(pooled_gap_rad=saved.gap(rz, center), planes=[
                dict(plane=plane, **saved.recurrence(rz[planes == plane], center))
                for plane in (0, 1)])
            need(actual == case['geometry'][label], 'saved geometry changed')
            counts.append([[g['resolved_direction_changes'] for g in p['residue_classes']]
                           for p in actual['planes']])
        decision = bool(np.max(delta) <= 1e-5 and counts[0] == counts[1]
                        and abs(case['geometry']['original']['pooled_gap_rad']
                                -case['geometry']['refined']['pooled_gap_rad']) <= .01)
        need(decision == case['comparison_pass'], 'comparison verdict changed')
        outcomes.append(decision)
    need(tuple(c['index'] for c in report['cases']) == study['CASES'], 'case set changed')
    need(all(outcomes) == report['both_comparisons_pass'], 'aggregate verdict changed')
    need(report['original_qualification_unchanged'] and not report['physical_admission'],
         'claim changed')
    print(json.dumps(dict(completed=True, manifest_files=len(manifest),
                          source_bindings=len(bindings), cases=2, paired_crossings=1280,
                          residue_sequences=88, exact_saved_arithmetic_agreement=True,
                          elapsed_s=time.monotonic()-START,
                          scope='Same NumPy kernels on saved arrays; no native fields, '
                                'integrator execution, environment or timing reproduction'),
                     indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha', required=True)
    replay(parser.parse_args().manifest_sha)
