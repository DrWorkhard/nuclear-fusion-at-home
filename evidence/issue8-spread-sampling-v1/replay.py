"""Verify preserved files and recompute sampling metrics from saved full-grid B."""

import time

START = time.monotonic()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import runpy  # noqa: E402
from pathlib import Path  # noqa: E402

PAYLOAD = Path(__file__).resolve().parent
ROOT = PAYLOAD.parents[1]


def need(condition, message):
    if not condition:
        raise ValueError(message)
    if time.monotonic()-START >= 60:
        raise TimeoutError('60-second saved-arithmetic replay limit')


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(manifest_sha):
    need(digest(PAYLOAD/'manifest.json') == manifest_sha, 'Wrong evidence manifest')
    manifest = read(PAYLOAD/'manifest.json')
    for relative, sha in manifest.items():
        path = (PAYLOAD/relative).resolve()
        need(path.is_relative_to(PAYLOAD), 'Manifest path escapes evidence')
        need(digest(path) == sha, f'Changed evidence: {relative}')
    bindings = read(PAYLOAD/'metadata/source-bindings.json')
    distributed = 0
    for original, row in bindings.items():
        if row['archive_path'] is None:
            need(original == '/Users/sebastianwirkert/workspace/fusion/.venv/bin/python',
                 'Unexpected unavailable input')
            continue
        path = (ROOT/row['archive_path']).resolve()
        need(path.is_relative_to(ROOT), 'Source path escapes checkout')
        need(digest(path) == row['sha256'], f'Changed source/input: {original}')
        distributed += 1
    report, receipt = [read(PAYLOAD/'raw'/name)
                       for name in ('run/result.json', 'receipt.json')]
    for record in (report, receipt):
        need(record['completed'], 'Original attempt did not complete')
        need(record['sources_before'] == record['sources_after'], 'Original source changed')
        for path, sha in record['sources_before'].items():
            need(bindings[path]['sha256'] == sha, 'Missing recorded source binding')
    need(receipt['cleanup_confirmed'] and receipt['returncode'] == 0, 'Cleanup/run incomplete')
    for record, limit in ((report, 300), (receipt, 360)):
        need(max(record['elapsed_s'], record['wall_elapsed_s']) < limit
             and abs(record['elapsed_s']-record['wall_elapsed_s']) <= 5, 'Original timing failed')
    study = runpy.run_path(str(ROOT/'scripts/check_spread_sampling.py'))
    case, _ = study['load_case']()
    points, normals, weights = study['boundary_grid'](study['load_input'](case))
    need(read(PAYLOAD/'raw/run/geometry.json')
         == dict(points_m=points, unit_normals=normals, weights=weights), 'Geometry changed')
    sparse, spread = case['groups']['boundary']['indices'], study['indices']()
    need(report['sparse_indices'] == sparse and report['spread_indices'] == spread,
         'Sample layout changed')
    rows = []
    for name, relative in study['CANDIDATES']:
        row = dict(name=name, path=relative, candidate_sha256=digest(ROOT/relative), levels=[])
        for count in (256, 512):
            saved = read(PAYLOAD/f'raw/run/{name}-{count}.json')
            need(len(saved['B_T']) == len(normals) == 4096, 'Incomplete saved field')
            errors = []
            for b, n in zip(saved['B_T'], normals, strict=True):
                norm = math.sqrt(sum(x*x for x in b))
                need(norm > 0, 'Zero boundary field')
                errors.append(sum(x*y for x, y in zip(b, n, strict=True))/norm)
            need(errors == saved['normal_errors'], 'Recorded normal errors changed')
            level = dict(ncoil=count,
                         dense_rms=study['metric'](errors, weights, range(4096)),
                         sparse_rms=study['metric'](errors, weights, sparse),
                         spread_rms=study['metric'](errors, weights, spread))
            for kind in ('sparse', 'spread'):
                level[kind+'_relative_error'] = abs(level[kind+'_rms']/level['dense_rms']-1)
            need(level == {key: saved[key] for key in level}, 'Recorded metrics changed')
            row['levels'].append(level)
        row['max_quadrature_relative_change'] = max(
            abs(row['levels'][0][key]/row['levels'][1][key]-1)
            for key in ('dense_rms', 'sparse_rms', 'spread_rms'))
        need(row == read(PAYLOAD/f'raw/run/{name}-complete.json'), 'Candidate summary changed')
        rows.append(row)
    need(rows == report['candidates'], 'Final candidate records changed')
    headroom, counter = [row['levels'][-1] for row in rows[1:]]
    checks = dict(
        quadrature=all(row['max_quadrature_relative_change'] <= .001 for row in rows),
        spread_accuracy=all(row['levels'][-1]['spread_relative_error'] <= .05 for row in rows),
        improves_error=all(row['levels'][-1]['spread_relative_error']
                          < row['levels'][-1]['sparse_relative_error'] for row in rows),
        dense_counterexample=counter['dense_rms'] > headroom['dense_rms'],
        legacy_counterexample=counter['sparse_rms'] < headroom['sparse_rms'],
        spread_counterexample=counter['spread_rms'] > headroom['spread_rms'],
    )
    need(checks == report['checks'], 'Decision checks changed')
    need(all(checks.values()) == report['promote_to_case_work']
         == receipt['promote_to_case_work'], 'Promotion verdict changed')
    need(not report['physical_admission'] and not receipt['physical_admission'], 'Claim changed')
    print(json.dumps(dict(completed=True, manifest_files=len(manifest),
                         distributed_source_bindings=distributed, external_python_identity=True,
                         field_points_reduced=6*4096, exact_arithmetic_agreement=True,
                         promote_to_case_work=all(checks.values()),
                         elapsed_s=time.monotonic()-START,
                         scope='Saved B reduction and geometry, same stdlib kernels; '
                               'no field evaluation, original Python or timing reproduction'),
                     indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha', required=True)
    replay(parser.parse_args().manifest_sha)
