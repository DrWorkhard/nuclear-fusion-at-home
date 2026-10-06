"""Bounded saved-contour method check; does not reclassify the stopped matching pilot."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines import flux_labels as labels  # noqa: E402
from fusion_baselines.coupled_coil_audit import (  # noqa: E402
    filament_field_and_potential,
    physical_curves,
)
from fusion_baselines.provenance import build_run_record  # noqa: E402

MANIFEST_SHA256 = '6b35f5634e7fea8f5a353bbaaad7fd367eed63d5378917caa883ef4a6c9494ab'


class UniformY:
    def set_points(self, points):
        self.points = points

    def A(self):
        return np.column_stack((np.zeros((len(self.points), 2)), -self.points[:, 0]))

    def B(self):
        return np.tile([0., 1., 0.], (len(self.points), 1))


def controls(guard):
    theta = np.sort(np.random.default_rng(4810).uniform(0, 2*np.pi, 160))
    rows = []
    for modulation in (0., .2):
        radius = .2*(1+modulation*np.cos(2*theta))
        rz = np.column_stack((1.+radius*np.cos(theta), radius*np.sin(theta)))
        spline, _ = labels.polar_contour(rz, [1., 0.])
        area = 0.
        for coefficients, width in zip(spline.c.T, np.diff(spline.x), strict=True):
            polynomial = np.polynomial.Polynomial(coefficients[::-1])
            area += .5*(polynomial*polynomial).integ()(width)
        area = float(area)
        result = labels.interval_flux_integrals(UniformY(), spline, [1., 0.], guard=guard)
        errors = dict(line=abs(result['line_flux']+area), area=abs(result['area_flux']+area))
        if not modulation:
            errors['circle'] = abs(area-np.pi*.2**2)
        rows.append(dict(modulation=modulation, exact_spline_area=area, errors=errors,
                         passed=bool(max(errors.values()) < 1e-10)))
    return rows


def run(archive, output):
    from simsopt.field import BiotSavart

    check.need(all(os.environ.get(k) == '1' for k in (
        'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS',
        'MKL_NUM_THREADS')), 'one-thread execution required')
    check.need(fit.shutil.disk_usage(output.parent).free >= fit.START_RESERVE,
               '3 GiB initial reserve required')
    started = time.monotonic()
    record = fit.Recorder(output, started+600)
    report = dict(kind='saved-contour-interval-quadrature-check', completed=False,
                  provenance=build_run_record(ROOT), cases=[], controls=[],
                  original_matching_verdict='inconclusive', physical_admission=False)
    try:
        sources = {}
        check.bind(archive/'manifest.json', MANIFEST_SHA256, sources)
        manifest = check.read_json(archive/'manifest.json')
        for source in [Path(__file__), *sorted((ROOT/'src/fusion_baselines').glob('*.py'))]:
            check.bind(source, check.digest(source), sources)
        for target in ('reference401', 'selected401'):
            for name in (f'{target}-snapshot.json', f'round2/{target}/line-1.npz',
                         f'round2-quadrature/{target}/result.json'):
                check.bind(archive/name, manifest[name], sources)
        report['sources_before'] = dict(sources)
        report['controls'] = controls(record.guard)
        record.save('progress.json', report)
        for target in ('reference401', 'selected401'):
            original = check.read_json(archive/f'round2-quadrature/{target}/result.json')
            snapshot = check.read_json(archive/f'{target}-snapshot.json')
            field = BiotSavart(check.native_coils(snapshot, 512, target)[0])
            center, edge = original['center_RZ'], original['edge']['line_flux']
            with np.load(archive/f'round2/{target}/line-1.npz', allow_pickle=False) as data:
                hits = data['hits'].copy()
            hits = hits[(hits[:, 1] >= 0) & (hits[:, 0] > 1e-8)]
            hits = hits[np.argsort(hits[:, 0], kind='stable')][:640]
            check.need(len(hits) == 640, 'complete frozen contour required')
            rz = np.column_stack((np.hypot(hits[:, 2], hits[:, 3]), hits[:, 4]))
            spline, _ = labels.polar_contour(rz, center)
            values = [labels.interval_flux_integrals(field, spline, center, order=n,
                       guard=record.guard) for n in (4, 8)]
            points, tangent, weights = labels.interval_contour_points(spline, center, 8)
            own = physical_curves(snapshot, 512)
            _, A = record.call('independent_BA', filament_field_and_potential, points,
                               own['positions'], own['tangents'], own['currents'])
            independent = float(np.sum(weights*np.sum(A*tangent, axis=1)))
            differences = dict(order=abs(values[0]['line_flux']-values[1]['line_flux'])/abs(edge),
                               Stokes=values[-1]['stokes_abs_error']/abs(edge),
                               independent=abs(independent-values[-1]['line_flux'])/abs(edge))
            passed = (differences['order'] < 1e-5 and differences['Stokes'] < 1e-5
                      and differences['independent'] < 1e-10)
            row = dict(target=target, uniform_label=original['lines'][1]['prefixes'][-1]['label'],
                       interval_label=values[-1]['line_flux']/edge, edge_flux=edge,
                       minimum_knot_gap=float(np.min(np.diff(spline.x))),
                       intervals=640, orders=[4, 8], radial_count=24, integrals=values,
                       independent_line_flux=independent, differences=differences, passed=passed)
            report['cases'].append(row)
            record.save('progress-method.json', report)
            print(json.dumps(row), flush=True)
        report['sources_after'] = {p: check.digest(p) for p in sources}
        check.need(report['sources_before'] == report['sources_after'], 'sources changed')
        report['method_check_passed'] = (all(r['passed'] for r in report['controls'])
                                         and all(r['passed'] for r in report['cases']))
        record.guard()
        report['completed'] = True
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
    record.finish(report, started)
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.archive.resolve(), args.output.resolve()))
