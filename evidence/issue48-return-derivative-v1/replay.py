"""Replay saved derivative arithmetic; do not evaluate fields or seek roots."""
import argparse
import hashlib
import json
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


def close(actual, expected):
    need(np.allclose(actual, expected, rtol=1e-10, atol=1e-12), 'arithmetic mismatch')


def check_proposal(matrix, residual, saved):
    step = np.linalg.solve(matrix, -np.asarray(residual))
    close(matrix, saved['residual_jacobian'])
    close(step, saved['step_m'])
    close(np.linalg.norm(step), saved['step_norm_m'])
    close(np.linalg.cond(matrix), saved['condition_number'])
    close(np.linalg.svd(matrix, compute_uv=False), saved['singular_values'])
    return step


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
        need(record['completed'] and record['sources_before'] == record['sources_after'],
             'incomplete or changed sources')
        for name, sha in record['sources_before'].items():
            need(bindings[name]['sha256'] == sha, 'missing original source binding')
    need(receipt['cleanup_confirmed'] and report['deadline_met'], 'incomplete cleanup/budget')
    need(not report['physical_admission'] and not report['root_search_performed']
         and report['original_qualification_unchanged'], 'scope changed')
    failure = read(PAYLOAD/'failure_archive/raw/run/result.json')
    trials = read(PAYLOAD/'failure_archive/raw/run/root-512-attempt.json')['trials']
    need(not failure['completed'] and len(trials) == 6, 'failed input changed')
    need(all(t['status'] == 'completed' for t in trials[:5])
         and trials[5]['status'] == 'attempted' and 'residual' not in trials[5],
         'failed trial statuses changed')
    seed = np.asarray(failure['seed_RZ'])
    need(seed.tolist() == report['seed_RZ'], 'seed changed')
    f = np.asarray(trials[0]['residual'])
    original = np.column_stack([(np.asarray(trials[k]['residual'])-f)
                                /(trials[k]['point'][j]-seed[j])
                                for j, k in enumerate((3, 4))])
    baseline = check_proposal(original, f, report['baseline'])
    baseline_error = float(np.linalg.norm(seed+baseline-trials[5]['point']))
    need(baseline_error < 1e-9, 'reconstructed rejected proposal differs')
    rows = report['rows']
    need([(r['nodes'], r['derivative']['h_m']) for r in rows]
         == [(512, 1e-5), (512, 5e-6), (1024, 1e-5), (1024, 5e-6)], 'settings changed')
    steps = []
    for row in rows:
        center = read(PAYLOAD/f"raw/run/center-{row['nodes']}.json")
        need(center['seed'] == seed.tolist(), 'center changed')
        residual = np.asarray(center['final'])-seed
        close(residual, center['residual'])
        close(residual, row['residual'])
        derivative = row['derivative']
        matrix = np.column_stack([(np.asarray(s['plus'])-s['minus'])
                                  /(2*derivative['h_m']) for s in derivative['samples']])
        close(matrix, derivative['matrix'])
        close(np.trace(matrix), derivative['trace'])
        close(np.linalg.det(matrix), derivative['determinant'])
        close((2-np.trace(matrix))/4, derivative['residue'])
        steps.append(check_proposal(matrix-np.eye(2), residual, row['proposal']))
    spread = max(float(np.linalg.norm(a-b)) for a in steps for b in steps)
    norms = [float(np.linalg.norm(s)) for s in steps]
    decision = 'unresolved'
    if spread <= .001:
        if min(norms) > .011:
            decision = 'refined proposals still leave the frozen neighborhood'
        elif max(norms) < .009:
            decision = 'refined proposals stay inside the frozen neighborhood'
    need(decision == report['decision']['result'], 'decision changed')
    close(spread, report['decision']['maximum_proposal_spread_m'])
    print(json.dumps(dict(completed=True, manifest_files=len(manifest),
                          source_bindings=len(bindings), proposal_norms_m=norms,
                          maximum_proposal_spread_m=spread, decision=decision,
                          baseline_reconstruction_difference_m=baseline_error,
                          elapsed_s=time.monotonic()-START,
                          scope='Identity and saved derivative arithmetic with NumPy; no field '
                                'evaluation, integration, root search or timing reproduction'),
                     indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha', required=True)
    replay(parser.parse_args().manifest_sha)
