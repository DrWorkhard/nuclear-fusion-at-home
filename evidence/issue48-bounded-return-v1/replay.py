"""Verify the failed local search and its guard arithmetic; never rerun the solver."""
import argparse
import hashlib
import json
import math
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


def read(path):
    return json.loads(path.read_bytes())


def replay(manifest_sha):
    need(digest(PAYLOAD/'manifest.json') == manifest_sha, 'wrong manifest')
    manifest = read(PAYLOAD/'manifest.json')
    for name, sha in manifest.items():
        path = (PAYLOAD/name).resolve()
        need(path.is_relative_to(PAYLOAD) and digest(path) == sha, 'payload mismatch: '+name)
    bindings = read(PAYLOAD/'metadata/source-bindings.json')
    for name, row in bindings.items():
        path = (ROOT/row['archive_path']).resolve()
        need(path.is_relative_to(ROOT) and digest(path) == row['sha256'], name)
    receipt, report = read(PAYLOAD/'raw/receipt.json'), read(PAYLOAD/'raw/run/result.json')
    for record in (receipt, report):
        need(not record['completed'], 'failed attempt was changed to complete')
        for name, sha in record['sources_before'].items():
            need(bindings[name]['sha256'] == sha, 'missing original source binding')
    need(receipt['cleanup_confirmed'], 'process cleanup unconfirmed')
    need(report['error'] == 'ValueError: trial left the 1 cm seed neighborhood',
         'failure reason changed')
    need(report['resolutions'] == [] and 'linear_diagnosis' not in report,
         'a failed search must not have a classification')
    with np.load(PAYLOAD/'inputs/raw/run/line-10.npz', allow_pickle=False) as data:
        points = data['rz'][data['planes'] == 0]
    seed = np.mean(points[::11], axis=0)
    need(seed.tolist() == report['seed_RZ'] and len(points[::11]) == report['seed_count'],
         'data-informed seed changed')
    trials = read(PAYLOAD/'raw/run/root-512-attempt.json')['trials']
    need(len(trials) == 16 and all(t['status'] == 'completed' for t in trials[:-1]),
         'retained trial set changed')
    need(trials[-1]['status'] == 'attempted' and 'residual' not in trials[-1],
         'aborted trial must not have a field evaluation')
    distances = [math.dist(t['point'], report['seed_RZ']) for t in trials]
    need(all(d <= .01 for d in distances[:-1]) and distances[-1] > .01,
         'guard decision differs')
    post = read(PAYLOAD/'metadata/issue48-bounded-return-post-failure-identities-v1.json')
    need(post['completed'] and post['failed_run_still_incomplete']
         and post['source_bindings'] == len(bindings), 'post-failure check scope changed')
    print(json.dumps(dict(completed=True, scientific_attempt_completed=False,
                          manifest_files=len(manifest), source_bindings=len(bindings),
                          seed_count=len(points[::11]), retained_trials=len(trials),
                          aborted_trial_distance_m=distances[-1],
                          minimum_evaluated_residual_m=min(math.hypot(*t['residual'])
                              for t in trials[:-1]),
                          elapsed_s=time.monotonic()-START,
                          scope='Identity, saved-seed and guard arithmetic only; no root solve, '
                                'field calculation, linear classification or timing reproduction'),
                     indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha', required=True)
    replay(parser.parse_args().manifest_sha)
