"""One bounded fixed-coil surface response diagnostic; never equilibrium acceptance."""
import argparse
import copy
import io
import itertools
import json
import os
import shutil
import sys
import time
from pathlib import Path

STARTED = (time.monotonic(), time.time())

import numpy as np  # noqa: E402 - charge the native import against the study clock.

MODES = (('rbc', 1, 1), ('rbc', 2, 0), ('zbs', 1, 1), ('zbs', 2, 0))
BOUND, STEPS = 5e-4, (1e-5, 5e-6)
ROOT = Path(__file__).resolve().parents[1]


def bounded_step(matrix, residual):
    """Exact active-face enumeration of the four-variable linear box problem."""
    best = None
    for face in itertools.product((-1, 0, 1), repeat=4):
        fixed = np.asarray(face) != 0
        x = np.asarray(face, dtype=float)
        rhs = -residual-matrix[:, fixed]@x[fixed]
        x[~fixed] = np.linalg.lstsq(matrix[:, ~fixed], rhs, rcond=None)[0]
        if np.any(abs(x) > 1+1e-12):
            continue
        x = np.clip(x, -1, 1)
        value = float(np.linalg.norm(residual+matrix@x))
        if best is None or value < best[0]:
            best = value, x.copy()
    return best


def weighted_residual(B, normals):
    area = np.linalg.norm(normals, axis=-1)
    magnitude = np.linalg.norm(B, axis=-1)
    if not np.isfinite([B, normals]).all() or np.any(area <= 0) or np.any(magnitude <= 0):
        raise ValueError('finite nondegenerate geometry and fields required')
    signed = np.sum(B*normals, axis=-1)/(area*magnitude)
    return (np.sqrt(area/area.sum())*signed).ravel()


def changed(data, delta):
    result = copy.deepcopy(data)
    for (key, m, n), value in zip(MODES, delta, strict=True):
        rows = [r for r in result[key] if (r['m'], r['n']) == (m, n)]
        if len(rows) != 1:
            raise ValueError('one explicit entry per released mode required')
        rows[0]['value'] += float(value)
    return result


def failure_receipt(output, report, exc, started):
    """Demote a success whose publication/check failed, preserving its original bytes."""
    result = output/'result.json'
    if result.exists():
        result.rename(output/'attempted-result.json')
    report.update(completed=False, error=f'{type(exc).__name__}: {exc}',
                  elapsed_s=time.monotonic()-started[0], wall_elapsed_s=time.time()-started[1])
    with result.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)


def main(started):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    if any(os.environ.get(k) != '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
           'VECLIB_MAXIMUM_THREADS', 'MKL_NUM_THREADS')):
        raise ValueError('all four native thread limits must be one')
    sys.modules['mpi4py'] = None
    sys.path.insert(0, str(ROOT/'src'))
    from simsopt.field import BiotSavart

    from fusion_baselines import coil_check as check
    from fusion_baselines import joint_coil, joint_target
    from fusion_baselines.boundary_control_metrics import boundary_metrics
    from fusion_baselines.coil_fit import loop_geometry
    from fusion_baselines.provenance import build_run_record

    config = check.read_json(args.config)
    args.output.mkdir(parents=True, exist_ok=False)
    if shutil.disk_usage(args.output).free < 3*1024**3:
        raise OSError('initial 3 GiB reserve required')
    sources = {}
    for row in config['inputs'].values():
        check.bind(row['path'], row['sha256'], sources)
    check.bind(args.config, check.digest(args.config), sources)
    for base in ('src', 'scripts'):
        for path in sorted((ROOT/base).rglob('*.py')):
            check.bind(path, check.digest(path), sources)
    provenance = build_run_record(ROOT)
    check.need(provenance['repository']['commit'] == args.revision
               and not provenance['repository']['dirty'], 'clean exact producer required')
    environment = check.read_json(config['inputs']['environment']['path'])
    environment_before = joint_coil.solver.identity(('numpy', 'scipy', 'netCDF4', 'simsopt'))
    check.need(environment_before == environment, 'frozen native environment required')
    total_bytes = 0

    def guard():
        elapsed = (time.monotonic()-started[0], time.time()-started[1])
        if max(elapsed) >= 180 or abs(elapsed[0]-elapsed[1]) > 5:
            raise TimeoutError('180 s dual-clock / 5 s disagreement limit')
        if shutil.disk_usage(args.output).free < 2*1024**3:
            raise OSError('live 2 GiB reserve required')

    def save(name, value):
        nonlocal total_bytes
        guard()
        payload = value if isinstance(value, bytes) else (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
        total_bytes += len(payload)
        if total_bytes > 32*1024**2-256*1024:
            raise OSError('32 MiB output limit')
        with (args.output/name).open('xb') as stream:
            stream.write(payload)
        guard()

    report = dict(completed=False, physical_admission=False, equilibrium_tested=False,
                  coils_changed=False, current_changed=False, ideal_score_tested=False,
                  provenance=provenance, source_hashes=sources, config=config,
                  modes=MODES, bound_m=BOUND, derivative_steps_m=STEPS)
    try:
        guard()
        data = check.read_json(config['inputs']['input']['path'])
        frozen = check.read_json(config['inputs']['frozen']['path'])
        snapshot = frozen['snapshot']
        joint_coil.snapshot_identity(snapshot, snapshot['joint_target_binding'])
        check.need(check.digest(config['inputs']['input']['path']) ==
                   snapshot['joint_target_binding']['input_sha256'], 'same frozen target input')
        coils, own, mapping = check._native_coils(snapshot, 512)
        field = BiotSavart(coils)
        save('setup.json', report)

        def evaluate(delta, n, shift, name):
            guard()
            document = changed(data, delta)
            surface = check.independent.boundary(document, n, n, shift=shift)
            points = surface['points'].reshape(-1, 3)
            blocks = []
            for first in range(0, len(points), 128):
                guard()
                field.set_points(np.ascontiguousarray(points[first:first+128]))
                blocks.append(field.B().copy())
                guard()
            B = np.concatenate(blocks).reshape(surface['points'].shape)
            residual = weighted_residual(B, surface['normal'])
            metrics = boundary_metrics(B, surface['normal'])
            check.need(abs(np.linalg.norm(residual)-metrics['normal_rms']) < 1e-15,
                       'residual norm matches shared area-weighted RMS')
            buffer = io.BytesIO()
            np.savez_compressed(buffer, B=B, points=surface['points'],
                                normals=surface['normal'], residual=residual)
            save(name+'.npz', buffer.getvalue())
            return residual, metrics, surface, B

        zero = np.zeros(4)
        r0, baseline, surface0, B0 = evaluate(zero, 64, False, 'baseline-64')
        with np.load(config['inputs']['fine0']['path'], allow_pickle=False) as old:
            for key, actual in [('B', B0), ('points', surface0['points']),
                                ('normals', surface0['normal'])]:
                expected = old[key].reshape(128, 128, 3)[::2, ::2]
                check.need(check.error(actual.reshape(-1, 3), expected.reshape(-1, 3)) < 1e-12,
                           'baseline reproduces original fine-grid subsample')
        matrices = []
        for h in STEPS:
            columns = []
            for j in range(4):
                delta = zero.copy()
                delta[j] = h
                plus = evaluate(delta, 64, False, f'probe-{h}-{j}-plus')[0]
                minus = evaluate(-delta, 64, False, f'probe-{h}-{j}-minus')[0]
                columns.append((plus-minus)/(2*h))
            matrices.append(np.column_stack(columns))
        errors = [float(np.linalg.norm(matrices[0][:, j]-matrices[1][:, j]) /
                        max(np.linalg.norm(matrices[1][:, j]), 1e-12)) for j in range(4)]
        report.update(derivative_relative_errors=errors, mapping=mapping, baseline=baseline)
        check.need(max(errors) <= 1e-3, 'derivative steps disagree')
        jacobian = matrices[1]
        predicted, scaled = bounded_step(BOUND*jacobian, r0)
        delta = BOUND*scaled
        frozen_step = dict(delta_m=delta.tolist(), predicted_rms=predicted,
                           predicted_ratio=predicted/baseline['normal_rms'])
        save('frozen-step.json', frozen_step)
        save('proposed-input.json', changed(data, delta))
        buffer = io.BytesIO()
        np.savez_compressed(buffer, r0=r0, jacobian=jacobian, jacobian_large=matrices[0],
                            delta=delta, predicted_residual=r0+jacobian@delta)
        save('linear-model.npz', buffer.getvalue())
        actual, coarse, _, _ = evaluate(delta, 64, False, 'candidate-64')
        model_error = float(np.linalg.norm(actual-(r0+jacobian@delta))/np.linalg.norm(r0))
        report.update(frozen_step=frozen_step, model_relative_error=model_error,
                      coarse_candidate=coarse)
        fine = []
        for shift, key in [(False, 'fine0'), (True, 'fine_half')]:
            _, metrics, surface, B = evaluate(delta, 128, shift, f'candidate-128-{shift}')
            bi = np.linspace(0, 128*128-1, 64, dtype=int)
            independent_B, _ = check.independent.filament_field_and_potential(
                surface['points'].reshape(-1, 3)[bi], own['positions'],
                own['tangents'], own['currents'])
            independent_error = check.error(independent_B, B.reshape(-1, 3)[bi])
            check.need(independent_error <= 1e-12, 'independent fine B sample mismatch')
            with np.load(config['inputs'][key]['path'], allow_pickle=False) as old:
                base_metrics = boundary_metrics(old['B'].reshape(128, 128, 3), old['normals'])
            fine.append(dict(shift=float(shift)*.5, metrics=metrics,
                             ratio=metrics['normal_rms']/base_metrics['normal_rms'],
                             independent_error=independent_error))
        volumes = [dict(n=n, base=joint_target.volume(data, n),
                        candidate=joint_target.volume(changed(data, delta), n)) for n in (128, 256)]
        loops = []
        for label, document in [('base', data), ('candidate', changed(data, delta))]:
            points, tangent = loop_geometry(document, 512)
            field.set_points(points)
            guard()
            flux = float(np.mean(np.sum(field.A()*tangent, axis=1)))
            guard()
            loops.append(dict(label=label, flux=flux,
                              relative_to_target=flux/snapshot['target_flux']-1))
        refinement = max(abs(f['metrics']['normal_rms']/coarse['normal_rms']-1) for f in fine)
        valid = model_error <= .01 and refinement <= .001
        verdict = ('promising-fixed-coil-step' if all(f['ratio'] <= .5 for f in fine)
                   else 'no-substantial-fixed-coil-shortcut') if valid else 'inconclusive-model'
        report.update(fine=fine, volumes=volumes, fixed_current_flux=loops,
                      refinement_relative_error=refinement, verdict=verdict,
                      sources_unchanged=all(check.digest(p) == s for p, s in sources.items()),
                      environment_unchanged=joint_coil.solver.identity(
                          ('numpy', 'scipy', 'netCDF4', 'simsopt')) == environment_before)
        check.need(report['sources_unchanged'] and report['environment_unchanged'],
                   'source/environment identity changed')
        guard()
        report.update(completed=True, elapsed_s=time.monotonic()-started[0],
                      wall_elapsed_s=time.time()-started[1])
        save('result.json', report)
        print(json.dumps({k: report[k] for k in ('completed', 'verdict', 'frozen_step',
                         'model_relative_error', 'refinement_relative_error', 'elapsed_s')}))
    except Exception as exc:
        # Reserved metadata space records failure even after the scientific deadline.
        failure_receipt(args.output, report, exc, started)
        raise


if __name__ == '__main__':
    main(STARTED)
