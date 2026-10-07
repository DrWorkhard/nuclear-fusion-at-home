"""Conditional scale/envelope arithmetic from an already checked filament geometry."""
import argparse
import hashlib
import itertools
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify(plasma_margins, coil_margins):
    if plasma_margins[1] < 0 or coil_margins[1] < 0:
        return 'excluded'
    if plasma_margins[0] >= 0 and coil_margins[0] >= 0:
        return 'clears-two-separation-checks'
    return 'unresolved'


def critical_scale(distance, linear_radius, fixed_allowance):
    """Solve d*lambda = a*sqrt(lambda)+b, for positive d,a and nonnegative b."""
    return ((linear_radius+math.sqrt(linear_radius**2+4*distance*fixed_allowance))
            /(2*distance))**2


def scenario(base, length_scale, field_scale, density, casing, gap):
    current = abs(base['current_A'])*length_scale*field_scale
    area = current/(density*1e6)
    radius = math.sqrt(area/math.pi)
    outer_radius = radius+casing
    plasma = [length_scale*d-outer_radius-gap for d in base['plasma_distance_m']]
    coil = [length_scale*d-2*outer_radius for d in base['coil_distance_m']]
    coefficient = math.sqrt(abs(base['current_A'])*field_scale/(math.pi*density*1e6))
    critical = [max(critical_scale(dp, coefficient, gap+casing),
                    critical_scale(dc, 2*coefficient, 2*casing))
                for dp, dc in zip(base['plasma_distance_m'], base['coil_distance_m'], strict=True)]
    return dict(length_scale=length_scale, field_scale=field_scale,
                winding_density_A_mm2=density, casing_m=casing, casing_plasma_gap_m=gap,
                winding_area_m2=area, winding_radius_m=radius,
                ampere_turns_A=current, outer_radius_m=outer_radius,
                R00_m=base['R00_m']*length_scale,
                plasma_margin_m=plasma, coil_margin_m=coil,
                exclusion_scale_below=critical[1], clearance_scale_at_least=critical[0],
                verdict=classify(plasma, coil),
                existing_pilot_current_limit_met=current <= 500000,
                normalized_boundary_rms=base['normalized_boundary_rms'],
                physical_admission=False)


def main():
    started = time.monotonic(), time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=False)
    report = dict(completed=False, physical_admission=False, new_geometry_evaluation=False,
                  magnet_qualified=False, operating_point_established=False)

    def guard():
        mono, wall = time.monotonic()-started[0], time.time()-started[1]
        if max(mono, wall) >= 30 or abs(mono-wall) > 5:
            raise TimeoutError('30 s total / 5 s clock-disagreement limit')
        if shutil.disk_usage(args.output).free < 2*1024**3:
            raise OSError('2 GiB live reserve required')
        if sum(p.stat().st_size for p in args.output.iterdir() if p.is_file()) > 2*1024**2:
            raise OSError('2 MiB output ceiling')

    def git(*arguments):
        return subprocess.check_output(['git', '-C', str(root), *arguments], text=True).strip()

    try:
        if shutil.disk_usage(args.output).free < 3*1024**3:
            raise OSError('3 GiB initial reserve required')
        guard()
        config = json.loads(args.config.read_text(encoding='utf-8'))
        before = {str(args.config.resolve()): digest(args.config),
                  str(Path(__file__).resolve()): digest(__file__)}
        inputs = {}
        for key, row in config['inputs'].items():
            if digest(row['path']) != row['sha256']:
                raise ValueError(f'input hash changed: {key}')
            before[str(Path(row['path']).resolve())] = row['sha256']
            inputs[key] = json.loads(Path(row['path']).read_text(encoding='utf-8'))
        if git('rev-parse', 'HEAD') != args.revision or git('status', '--porcelain'):
            raise ValueError('clean exact producer required')
        arm, frozen, data = inputs['arm'], inputs['frozen'], inputs['input']
        if (not arm['completed'] or arm['frozen'] != frozen
                or arm['diagnostics']['geometry']['status'] != 'pass'):
            raise ValueError('completed original geometry and exact frozen selection required')
        if (frozen['snapshot']['joint_target_binding']['input_sha256']
                != config['inputs']['input']['sha256']):
            raise ValueError('geometry belongs to another boundary input')
        currents = {abs(c['current']) for c in frozen['snapshot']['physical']}
        if len(currents) != 1:
            raise ValueError('one equal-magnitude current across the frozen 24 filaments required')
        g = arm['diagnostics']['geometry']['levels'][-1]['geometry']
        base = dict(current_A=currents.pop(),
                    plasma_distance_m=[g['plasma_lower'], min(r['sampled'] for r in
                        g['plasma_distances'])+g['floating_pad']],
                    coil_distance_m=[g['coil_lower'], min(r['sampled'] for r in
                        g['coil_pairs'])+g['floating_pad']],
                    R00_m=next(r['value'] for r in data['rbc'] if (r['m'], r['n']) == (0, 0)),
                    normalized_boundary_rms=arm['summary']['boundary_rms'])
        for bounds in (base['plasma_distance_m'], base['coil_distance_m']):
            if not 0 < bounds[0] <= bounds[1]:
                raise ValueError('positive ordered distance bounds required')
        a = config['assumptions']
        values = [*a['length_scales'], *a['field_scales'], *a['winding_density_A_mm2'],
                  *a['casing_m'], a['casing_plasma_gap_m']]
        if not all(isinstance(v, (int, float)) and math.isfinite(v) and v >= 0 for v in values):
            raise ValueError('finite nonnegative assumptions required')
        if min(*a['length_scales'], *a['field_scales'], *a['winding_density_A_mm2'],
               a['casing_plasma_gap_m']) <= 0:
            raise ValueError('positive scale, density and clearance required')
        rows = []
        for scale, field, density, casing in itertools.product(a['length_scales'],
                a['field_scales'], a['winding_density_A_mm2'], a['casing_m']):
            guard()
            rows.append(scenario(base, scale, field, density, casing, a['casing_plasma_gap_m']))
        guard()
        if any(digest(p) != s for p, s in before.items()):
            raise ValueError('source/input changed during arithmetic')
        report.update(completed=True, producer=args.revision, dirty=False,
                      source_hashes=before, inputs_unchanged=True, config=config,
                      runtime=dict(python=sys.version, executable=sys.executable),
                      base=base, rows=rows,
                      elapsed_s=time.monotonic()-started[0], wall_elapsed_s=time.time()-started[1])
        payload = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
        if len(payload) > 1024**2:
            raise OSError('reserve half the output ceiling for failure metadata')
        (args.output/'result.json').write_bytes(payload)
        guard()
        print(json.dumps(dict(completed=True, cases=len(rows), elapsed_s=report['elapsed_s'])))
    except Exception as exc:
        result = args.output/'result.json'
        if result.exists():
            result.rename(args.output/'attempted-result.json')
        report.update(completed=False, error=f'{type(exc).__name__}: {exc}',
                      elapsed_s=time.monotonic()-started[0], wall_elapsed_s=time.time()-started[1])
        result.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
