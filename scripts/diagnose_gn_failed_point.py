"""Independent fresh-field routes at the captured single GN guard failure."""

import argparse
import hashlib
import inspect
import json
import time
from pathlib import Path

import numpy as np
from simsopt import load
from simsopt.field import BiotSavart
from simsopt.geo import SurfaceRZFourier
from simsopt.objectives import SquaredFlux

from fusion_baselines.batched_field_jacobian import batched_field_jacobian
from fusion_baselines.local_field_jacobian import local_field_jacobian
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import (
    base_coil_owners,
    dof_permutation,
    named_serialized_values,
)
from fusion_baselines.spatial_flux import normal_weights, spatial_flux


def reference(path):
    return {'path': str(path.resolve()), 'sha256': sha256_file(path)}


def checked(ref):
    path = Path(ref['path'])
    if sha256_file(path) != ref['sha256']:
        raise ValueError(f'hash mismatch: {path}')
    return path


def error(a, b):
    return np.abs(a-b) / np.maximum(1, np.abs(b))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('raw', type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError('new immutable diagnostic paths required')
    root = Path(__file__).resolve().parents[1]
    summary_path = root / 'evidence/gn-failure-replay-v1/summary.json'
    replay = json.loads(summary_path.read_text())
    if not replay['failure_reproduced'] or replay['status'] != 'diagnostic_complete':
        raise ValueError('exact captured prefix replay required')
    arm_path = checked(replay['arms'][0])
    arm = json.loads(arm_path.read_text())
    failure = arm['failed_bundle']
    field_path = checked(failure['field'])
    document = json.loads(field_path.read_text())
    field = load(str(field_path))
    source_names = replay['preparation']['degrees_of_freedom']
    surface_path = checked(replay['preparation']['surface'])
    surface = SurfaceRZFourier.from_vmec_input(
        str(surface_path), range='half period', nphi=32, ntheta=32)
    objective = SquaredFlux(surface, field, definition='quadratic flux')
    owners = {}
    for (curve, leaves), coil in zip(base_coil_owners(document), field.coils[:4], strict=True):
        pairs = [(curve, coil.curve.name)]
        for attributes, owner in leaves:
            current = coil.current
            for attribute in attributes:
                current = getattr(current, attribute)
            pairs.append((owner, current.name))
        for source, target in pairs:
            if source in owners and owners[source] != target:
                raise ValueError('conflicting shared owner')
            owners[source] = target
    permutation = dof_permutation(source_names, objective.dof_names, owners)
    with np.load(checked(failure['arrays']), allow_pickle=False) as saved:
        if (not np.array_equal(saved['x'], named_serialized_values(document, source_names))
                or hashlib.sha256(saved['x'].tobytes()).hexdigest()
                != arm['evaluations'][-1]['x_sha256']):
            raise ValueError('failed field/array/ledger parameter identity mismatch')
        x = saved['x'][permutation].copy()
        old_gradient = saved['jacobian'][0, permutation].copy()
        old_z, old_dz = saved['z'].copy(), saved['dz'][:, permutation].copy()
        old_phi = float(saved['values'][0])
    if not np.array_equal(objective.x, x):
        raise ValueError('fresh native parameter identity mismatch')
    normal, points = surface.normal().copy(), surface.gamma().reshape(-1, 3).copy()
    weights = normal_weights(normal)
    if (len(x) != 207 or len(field.coils) != 16 or normal.shape != (32, 32, 3)
            or any(len(c.curve.quadpoints) != 200 for c in field.coils)):
        raise ValueError('unexpected physical discretization')
    report = dict(
        schema_version=1, repository=git_state(root), host=host_state(), status='running',
        protocol=reference(root/'docs/optimization/GN_FAILED_POINT_PROTOCOL.md'),
        replay=reference(summary_path), arm=reference(arm_path), failure=failure,
        surface=reference(surface_path), source_indices_in_target_order=permutation.tolist(),
        target_names=list(objective.dof_names), optimization_performed=False,
        code=[reference(root/p) for p in (
            'scripts/diagnose_gn_failed_point.py', 'src/fusion_baselines/batched_field_jacobian.py',
            'src/fusion_baselines/local_field_jacobian.py', 'src/fusion_baselines/spatial_flux.py',
            'src/fusion_baselines/serialized_dofs.py')],
        native_source=reference(Path(inspect.getfile(BiotSavart))),
        work=dict(full_B_requests=0, full_VJP_requests=0, local_B_requests=1024,
                  local_VJP_requests=1024, batched_coil_contractions=16))
    args.raw.mkdir(parents=True)
    start = time.monotonic()

    def native_z(value):
        objective.x = value.copy()
        field.set_points(points)
        report['work']['full_B_requests'] += 1
        return spatial_flux(field.B().reshape(normal.shape), normal)

    def native_gradient(z):
        report['work']['full_VJP_requests'] += 1
        return np.asarray(field.B_vjp(z[:, None]*weights)(objective))/1e-6

    try:
        z = native_z(x)
        direct = native_gradient(z)
        batch_z, dz = batched_field_jacobian(field, objective, points, weights)
        local = local_field_jacobian(field, objective, points, weights)
        points_unchanged = np.array_equal(points, field.get_points_cart_ref())
        restored_z = native_z(x)
        restored_gradient = native_gradient(restored_z)
        routes = dict(archived_direct=old_gradient, fresh_direct=direct,
                      native_covector_batched_matrix=dz.T @ z/1e-6,
                      batched_covector_batched_matrix=dz.T @ batch_z/1e-6,
                      native_covector_local_matrix=local.T @ z/1e-6,
                      fresh_after_local=restored_gradient)
        gradient_errors = {name: error(value, direct).tolist() for name, value in routes.items()}
        currents = [i for i, name in enumerate(objective.dof_names) if name.startswith('Current')]
        if len(currents) != 3:
            raise ValueError('expected three affine free-current parameters')
        current_values, current_records = [], []
        for index in currents:
            direction = np.eye(len(x))[index]
            for h in (1., 0.5):
                plus, minus = native_z(x+h*direction), native_z(x-h*direction)
                derivative = (plus-minus)/(2*h)
                current_values.append([plus, minus])
                current_records.append(dict(
                    index=index, name=objective.dof_names[index], h=h,
                    spatial_error=float(error(derivative, dz[:, index]).max()),
                    gradient=float(z @ derivative / 1e-6),
                    gradient_error=float(error(np.array(z @ derivative/1e-6), direct[index]))))
        direction = np.random.default_rng(51).normal(size=len(x))
        direction = direction[permutation]
        direction[currents] = 0
        direction /= np.linalg.norm(direction)
        exact, geometry_values, geometry_records = dz @ direction, [], []
        for h in (1e-4, 1e-5, 1e-6):
            plus, minus = native_z(x+h*direction), native_z(x-h*direction)
            geometry_values.append([plus, minus])
            geometry_records.append(dict(h=h, maximum_error=float(
                error((plus-minus)/(2*h), exact).max())))
        final_z = native_z(x)
        final_gradient = native_gradient(final_z)
        checks = dict(
            points_restored=bool(points_unchanged), original_parameters_restored=bool(
                np.array_equal(objective.x, x)),
            raw_flux_replay=abs(z @ z / 2e-6-old_phi)/abs(old_phi) <= 1e-10,
            batch_projection_replay=error(batch_z, old_z).max() <= 1e-10,
            batch_matrix_replay=error(dz, old_dz).max() <= 1e-10,
            native_matrix_agreement=error(dz, local).max() <= 1e-10,
            fresh_covector_gradient=error(routes['native_covector_batched_matrix'], direct).max()
            <= 1e-10,
            batch_covector_gradient=error(routes['batched_covector_batched_matrix'], direct).max()
            <= 1e-10,
            full_route_state_stability=error(final_gradient, direct).max() <= 1e-10
            and error(restored_gradient, direct).max() <= 1e-10,
            affine_current_checks=all(r['spatial_error'] <= 1e-10 and r['gradient_error'] <= 1e-10
                                      for r in current_records),
            finest_geometry_direction=geometry_records[-1]['maximum_error'] <= 1e-6)
        raw = args.raw/'state.npz'
        with raw.open('xb') as stream:
            np.savez_compressed(stream, x=x, native_z=z, batch_z=batch_z, dz=dz,
                                local_dz=local, old_dz=old_dz, old_z=old_z,
                                direct_gradient=direct, old_gradient=old_gradient,
                                restored_gradient=restored_gradient, final_gradient=final_gradient,
                                current_values=current_values, geometry_direction=direction,
                                geometry_values=geometry_values)
        report.update(
            status='completed', arrays=reference(raw), gradient_routes={k: v.tolist()
                                                                     for k, v in routes.items()},
            gradient_errors_vs_fresh_direct=gradient_errors,
            projection_difference_contribution=(dz.T @ (batch_z-z)/1e-6).tolist(),
            maximum_projection_discrepancy=float(error(batch_z, z).max()),
            currents=current_records, geometry=geometry_records,
            checks={k: bool(v) for k, v in checks.items()},
            historical_pilot_qualification_pass=False)
        print(json.dumps({'checks': report['checks'], 'gradient_errors': {
            k: max(v) for k, v in gradient_errors.items()}}))
    except Exception as exc:
        report.update(status='error', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-start
        write_json_atomic(args.output, report)
    return 0  # Diagnostic completion is not a pass of every compared route.


if __name__ == '__main__':
    raise SystemExit(main())
