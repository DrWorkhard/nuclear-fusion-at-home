"""Reproduce the saved direct/interpolated crossing and signed-iota comparison."""
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parent
a, b = [json.loads((root/name/'result.json').read_text()) for name in ('direct', 'interpolated')]
for key in ('candidate_sha256', 'wout_sha256'):
    assert a[key] == b[key]
assert a['provenance']['repository']['commit'] == b['provenance']['repository']['commit']
rows = []
with np.load(root/'direct/poincare.npz') as da, np.load(root/'interpolated/poincare.npz') as db:
    for i, (x, y) in enumerate(zip(a['lines'], b['lines'], strict=True)):
        ca, cb = da[f'line_{i}'], db[f'line_{i}']
        ca, cb = ca[ca[:, 1] >= 0], cb[cb[:, 1] >= 0]
        assert ca.shape == cb.shape and np.array_equal(ca[:, 1], cb[:, 1])
        rows.append(dict(s=x['s'], crossings=len(ca),
                         signed_iota_difference=abs(x['iota_traced']-y['iota_traced']),
                         max_crossing_distance_m=float(np.linalg.norm(
                             ca[:, 2:]-cb[:, 2:], axis=1).max())))
report = dict(producer_commit=a['provenance']['repository']['commit'],
              candidate_sha256=a['candidate_sha256'], wout_sha256=a['wout_sha256'],
              direct=a['summary'], interpolated=b['summary'],
              interpolation_errors=b['interpolation_errors'], comparisons=rows,
              max_signed_iota_difference=max(r['signed_iota_difference'] for r in rows),
              max_crossing_distance_m=max(r['max_crossing_distance_m'] for r in rows),
              physical_admission=False, nestedness_tested=False)
assert report == json.loads((root/'comparison.json').read_text())
print(json.dumps(report, indent=2))
