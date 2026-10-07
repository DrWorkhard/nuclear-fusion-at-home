"""Independently repeat the desk arithmetic using 50-digit Decimal calculations."""
import argparse
from collections import Counter
from decimal import Decimal, getcontext
import hashlib
import itertools
import json
import math
from pathlib import Path
import time

started = time.monotonic()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
a = parser.parse_args()
root = a.root.resolve()
payload = root/'evidence/issue27-envelope-v1'
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest = read(payload/'manifest.json')
for name, expected in manifest.items():
    assert sha(payload/name) == expected, name
report = read(payload/'raw/result.json')
assert report['completed'] and report['inputs_unchanged'] and not report['dirty']
assert report['producer'] == '532f3b72302ecb75a857072beae1816cbdbee4de'
assert not any(report[k] for k in ('physical_admission', 'new_geometry_evaluation',
                                  'magnet_qualified', 'operating_point_established'))
assert max(report['elapsed_s'], report['wall_elapsed_s']) < 30
assert abs(report['elapsed_s']-report['wall_elapsed_s']) <= 5
old = Path('/private/tmp/fusion-issue27-envelope-20261007')
source_map = read(payload/'source-map.json')
for name, expected in report['source_hashes'].items():
    mapped = payload/source_map[name] if name in source_map else root/Path(name).relative_to(old)
    assert sha(mapped) == expected, name
assert report['config'] == read(payload/'metadata/config.json')
arm, frozen, data = [read(payload/'inputs'/f'{name}.json') for name in ('arm', 'frozen', 'input')]
assert arm['completed'] and arm['frozen'] == frozen
assert arm['diagnostics']['geometry']['status'] == 'pass'
g = arm['diagnostics']['geometry']['levels'][-1]['geometry']
current = abs(frozen['snapshot']['physical'][0]['current'])
assert all(abs(c['current']) == current for c in frozen['snapshot']['physical'])
base = dict(current_A=current, plasma_distance_m=[g['plasma_lower'],
    min(r['sampled'] for r in g['plasma_distances'])+g['floating_pad']],
    coil_distance_m=[g['coil_lower'], min(r['sampled'] for r in g['coil_pairs'])+g['floating_pad']],
    R00_m=next(r['value'] for r in data['rbc'] if (r['m'], r['n']) == (0, 0)),
    normalized_boundary_rms=arm['summary']['boundary_rms'])
assert report['base'] == base
getcontext().prec = 50
D = lambda x: Decimal(str(x))
pi = D('3.1415926535897932384626433832795028841971693993751')
settings = report['config']['assumptions']
combinations = list(itertools.product(settings['length_scales'], settings['field_scales'],
                                     settings['winding_density_A_mm2'], settings['casing_m']))
assert len(report['rows']) == len(combinations) == 108
worst = 0.


def equal(actual, expected):
    global worst
    expected = float(expected)
    assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), (actual, expected)
    worst = max(worst, abs(actual-expected)/max(1., abs(expected)))


for row, values in zip(report['rows'], combinations, strict=True):
    assert [row[k] for k in ('length_scale', 'field_scale', 'winding_density_A_mm2',
                            'casing_m')] == list(values)
    length, field, density, casing = map(D, values)
    gap = D(settings['casing_plasma_gap_m'])
    ampere_turns = D(current)*length*field
    area = ampere_turns/(density*D(1000000))
    radius = (area/pi).sqrt()
    outer = radius+casing
    plasma = [length*D(v)-outer-gap for v in base['plasma_distance_m']]
    coil = [length*D(v)-2*outer for v in base['coil_distance_m']]
    for k, v in dict(ampere_turns_A=ampere_turns, winding_area_m2=area,
                     winding_radius_m=radius, outer_radius_m=outer,
                     R00_m=length*D(base['R00_m']), casing_plasma_gap_m=gap).items():
        equal(row[k], v)
    for key, expected in [('plasma_margin_m', plasma), ('coil_margin_m', coil)]:
        for x, y in zip(row[key], expected, strict=True):
            equal(x, y)
    coefficient = (D(current)*field/(pi*density*D(1000000))).sqrt()
    thresholds = []
    for dp, dc in zip(base['plasma_distance_m'], base['coil_distance_m'], strict=True):
        dp, dc = D(dp), D(dc)
        plasma_threshold = ((coefficient+(coefficient**2+4*dp*(gap+casing)).sqrt())/(2*dp))**2
        coil_threshold = ((2*coefficient+(4*coefficient**2+8*dc*casing).sqrt())/(2*dc))**2
        thresholds.append(max(plasma_threshold, coil_threshold))
    equal(row['clearance_scale_at_least'], thresholds[0])
    equal(row['exclusion_scale_below'], thresholds[1])
    verdict = ('excluded' if plasma[1] < 0 or coil[1] < 0 else
               'clears-two-separation-checks' if plasma[0] >= 0 and coil[0] >= 0 else 'unresolved')
    assert verdict == row['verdict']
    assert row['existing_pilot_current_limit_met'] == (ampere_turns <= 500000)
    assert row['normalized_boundary_rms'] == base['normalized_boundary_rms']
    assert row['physical_admission'] is False
    assert time.monotonic()-started < 30
result = dict(completed=True, manifest_files=len(manifest), source_bindings=len(report['source_hashes']),
              cases=108, independent_precision_digits=50, normalized_arithmetic_error=worst,
              verdict_counts=dict(Counter(r['verdict'] for r in report['rows'])),
              geometry_recomputed=False, source_physics_revalidated=False,
              timing_reattested=False, physical_admission=False,
              elapsed_s=time.monotonic()-started)
with a.output.open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result))
