"""Replay saved trace/action arithmetic and identities; do not retrace fields."""

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(root, output):
    start = time.monotonic()
    base = root/'evidence/issue26-shallow-wells-v1'
    manifest = read(base/'manifest.json')
    for name, sha in manifest.items():
        need(digest(base/name) == sha, f'Archive changed: {name}')
    report, launch = read(base/'raw/run/result.json'), read(base/'raw/receipt.json')
    mapping = read(base/'source-map.json')
    need(report['sources_before'] == report['sources_after'], 'Source/input changed in run')
    verified, external = 0, []
    for original, sha in report['sources_before'].items():
        entry = mapping[original]
        need(entry['sha256'] == sha, 'Source binding mismatch')
        if entry['relative_path']:
            need(digest(root/entry['relative_path']) == sha, f'Source changed: {original}')
            verified += 1
        else:
            external.append(dict(original=original, sha256=sha, verified_now=False))
    need(launch['completed'] and report['completed'] and launch['returncode'] == 0,
         'Original run did not complete')
    need(report['producer_evaluator'] == launch['revision'] ==
         '568a96a428fbb730ff23568ef917ab2b947fa255', 'Unexpected producer/evaluator')
    for name, row in launch['retained_files'].items():
        path = base/'raw'/name
        need(path.stat().st_size == row['bytes'] and digest(path) == row['sha256'],
             f'Raw file changed: {name}')
    for name, key in [('runner.py', 'runner_sha256'), ('serial-python.py', 'wrapper_sha256'),
                      ('config.json', 'config_sha256')]:
        need(digest(base/'metadata'/name) == launch[key], 'Launch source changed')
    sys.path.insert(0, str(root/'src'))
    spec = importlib.util.spec_from_file_location('comparison',
                                                 root/'scripts/compare_interior_wells.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    surfaces = {'ideal': report['ideal'], **{k: v['surfaces'] for k, v in report['arms'].items()}}
    checked_cells = 0
    maximum_field_error = 0.
    for label, rows in surfaces.items():
        for row in rows:
            with np.load(base/'raw/run'/f'{label}-s{row["s"]}.npz', allow_pickle=False) as data:
                trace = {key: data[key] for key in data.files}
            for stride, n in [(1, 1601), (2, 801)]:
                level = {key: trace[key][::stride] for key in ('B', 'phi', 'length')}
                level['alpha'] = trace['alpha']
                need(module.cells(level) == row[str(n)], f'Saved actions/mask differ: {label}')
                checked_cells += 7
            if label != 'ideal':
                actual, expected = trace['native_B_control'], trace['independent_B']
                error = float(np.max(np.linalg.norm(actual-expected, axis=-1)
                                     / np.maximum(1., np.linalg.norm(expected, axis=-1))))
                need(error == row['independent_field_error'] and error <= 1e-12,
                     'Saved independent field check differs')
                need(np.max(np.abs(np.linalg.norm(expected, axis=1)
                                   - trace['B'].ravel()[trace['B_indices']])) <= 1e-12,
                     'Saved magnitude differs from independent field')
                maximum_field_error = max(maximum_field_error, error)
    dense = read(base/'raw/run/continuation-dense.json')
    packet_path = root/'examples/clear-coil-interior-v1/reference401.json'
    packet = read(packet_path)
    with np.load(base/'raw/run/continuation-inner-B.npz', allow_pickle=False) as data:
        residual = data['B']-np.asarray(packet['samples_xyz_B'])[:, 3:]
    rms = float(np.sqrt(np.sum(residual**2)/len(residual)/packet['B2_scale_T2']))
    need(abs(rms-dense['dense_inner_vector_rms']) <= 1e-14, 'Dense RMS not reproduced')
    decision = module.compare({name: arm['surfaces'] for name, arm in report['arms'].items()},
                              report['ideal'], dense['dense_inner_vector_rms'])
    decision = json.loads(json.dumps(decision))  # JSON represents coordinate tuples as lists.
    need(decision == report['decision'] == launch['decision'], 'Verdict not reproduced')
    need(not any(report[key] for key in ('physical_admission', 'benefit_transfer_confirmed',
                                        'realized_flux_labels_qualified')), 'Unsupported admission')
    result = dict(completed=True, manifest_files=len(manifest), source_bindings_verified=verified,
                  external_inputs=external, replayed_cells=checked_cells, decision=decision,
                  dense_inner_vector_rms=rms, max_saved_field_error=maximum_field_error,
                  elapsed_s=time.monotonic()-start, fields_recomputed=False,
                  trajectories_recomputed=False, timing_reattested=False, physical_admission=False)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    replay(args.root.resolve(), args.output)
