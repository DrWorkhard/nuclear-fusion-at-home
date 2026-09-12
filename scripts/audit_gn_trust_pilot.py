"""Audit native-covector pilot ledgers/fields without new physics calls."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.gn_pilot_audit import audit_gn_ledger
from fusion_baselines.inequality_audit import audit_inequality_arm
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import named_serialized_values


def reference(path):
    return {'path': str(path.resolve()), 'sha256': sha256_file(path)}


def checked(ref):
    path = Path(ref['path'])
    if sha256_file(path) != ref['sha256']:
        raise ValueError(f'hash mismatch: {path}')
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('study', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('new audit output required')
    summary = args.study/'summary.json'
    study = json.loads(summary.read_text())
    if study['status'] != 'completed' or 'native_covector_protocol' not in study:
        raise ValueError('completed native-covector study required')
    records, arms = [], []
    for ref in study['arms']:
        arm = json.loads(checked(ref).read_text())
        arms.append(arm)
        with np.load(checked(arm['best']['arrays']), allow_pickle=False) as data:
            checks = audit_inequality_arm(arm, data['x'], data['values'], expected_limit=1024)
            checks.update(audit_gn_ledger(arm))
            document = json.loads(checked(arm['best']['field']).read_text())
            checks['named_field_identity'] = bool(np.array_equal(data['x'], named_serialized_values(
                document, study['preparation']['degrees_of_freedom'])))
        records.append(dict(arm=ref, checks=checks, all_pass=all(checks.values())))
    repeated = len(arms) == 2 and len(arms[0]['evaluations']) == len(arms[1]['evaluations'])
    if repeated:
        repeated = all(a['x_sha256'] == b['x_sha256'] and a['values'] == b['values']
                       for a, b in zip(arms[0]['evaluations'], arms[1]['evaluations'], strict=True))
    point = json.loads(checked(study['point_diagnostic']).read_text())
    replay = json.loads(checked(point['replay']).read_text())
    old = json.loads(checked(replay['arms'][0]).read_text())
    prefix = all(len(arm['evaluations']) >= 29 and all(
        row['x_sha256'] == previous['x_sha256'] and row['values'] == previous['values']
        for row, previous in zip(arm['evaluations'][:28], old['evaluations'][:28], strict=True))
        and arm['evaluations'][28]['x_sha256'] == old['evaluations'][28]['x_sha256']
        for arm in arms)
    root = Path(__file__).resolve().parents[1]
    result = dict(schema_version=1, repository=git_state(root), study=reference(summary),
                  arms=records, repeat_histories_match=repeated, original_prefix_matches=prefix,
                  all_pass=bool(repeated and prefix and all(r['all_pass'] for r in records)),
                  additional_physics_calls=0, physical_feasibility_certified=False,
                  code=[reference(root/p) for p in (
                      'scripts/audit_gn_trust_pilot.py', 'src/fusion_baselines/gn_pilot_audit.py',
                      'src/fusion_baselines/inequality_audit.py')])
    write_json_atomic(args.output, result)
    print(json.dumps({'all_pass': result['all_pass']}))
    return 0 if result['all_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
