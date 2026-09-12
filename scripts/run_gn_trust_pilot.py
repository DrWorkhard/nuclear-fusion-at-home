"""Preregistered complete-bundle GN trust-constr construction, two repeats."""

import argparse
import hashlib
import importlib
import inspect
import json
import os
import time
import warnings
from pathlib import Path

import numpy as np
from qualify_optimization_oracle import prepare
from scipy.optimize import BFGS, NonlinearConstraint, minimize
from simsopt import load
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.affine_coordinates import AffineCoordinates
from fusion_baselines.batched_field_jacobian import batched_field_jacobian
from fusion_baselines.budgeted_oracle import BudgetExhausted
from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.gauss_newton_backend import GaussNewtonBackend
from fusion_baselines.inequality_oracle import InequalityOracle
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import base_coil_owners, dof_permutation

OPTIONS = dict(gtol=1e-12, xtol=1e-12, barrier_tol=1e-10, initial_tr_radius=0.1,
               initial_constr_penalty=1., initial_barrier_parameter=1e-3,
               initial_barrier_tolerance=1e-3, factorization_method='QRFactorization',
               sparse_jacobian=False, maxiter=10000, verbose=0)


def reference(path):
    return {'path': str(path.resolve()), 'sha256': sha256_file(path)}


def checked(ref):
    path = Path(ref['path'])
    if sha256_file(path) != ref['sha256']:
        raise ValueError(f'input/code hash mismatch: {path}')
    return path


def error(a, b):
    return float(np.max(np.abs(a-b) / np.maximum(1, np.abs(b))))


def control():
    result = minimize(
        lambda x: (0.5*((x[0]-2)**2+(x[1]+1)**2), x-np.array([2., -1.])),
        [0., 0.], jac=True, hess=lambda x: np.eye(2), method='trust-constr',
        constraints=NonlinearConstraint(
            lambda x: np.array([1-x[0], x[1]]), 0., np.inf,
            jac=lambda x: np.diag([-1., 1.]), hess=lambda x, v: np.zeros((2, 2))),
        options=OPTIONS)
    return {'x': result.x.tolist(), 'status': int(result.status),
            'optimality': float(result.optimality),
            'constraint_violation': float(result.constr_violation),
            'pass': bool(np.max(np.abs(result.x-[1, 0])) <= 1e-5
                         and result.optimality <= 1e-8 and result.constr_violation <= 1e-8)}


def make_gn(direct):
    return GaussNewtonBackend(direct.evaluate, lambda: batched_field_jacobian(
        direct.field, direct.global_objective, direct.points, direct.weights))


def run_arm(direct, ctx, x0, raw, output, repeat, permutation):
    raw.mkdir()
    ctx.Jf.x = x0.copy()
    direct.work = dict.fromkeys(direct.work, 0)
    backend = make_gn(direct)
    coordinates = AffineCoordinates(x0, 0.01)
    oracle = InequalityOracle(backend.evaluate, 1024, len(x0), 137, tolerance=1e-8)
    record = dict(method='gn-trust', representation='direct', repeat=repeat,
                  status='running', coordinate_scale=0.01, selection_tolerance=1e-8,
                  gradient_screen_pass=False, iterations=[], hessian_requests=0)
    started, checkpoint_count, target_stop = time.monotonic(), 0, False

    def checkpoint():
        record.update(counters=oracle.counters(), evaluations=oracle.records,
                      work=dict(direct.work), gn_identity_checks=backend.records,
                      gn_work=dict(assemblies=len(backend.records),
                                   assembly_attempts=backend.spatial_attempts,
                                   failed_assemblies=backend.spatial_attempts-len(backend.records),
                                   coil_contractions=16*len(backend.records),
                                   geometry_derivative_requests=32*len(backend.records),
                                   current_VJP_requests=16*len(backend.records)),
                      elapsed_seconds=time.monotonic()-started)
        write_json_atomic(output, record)

    def request(x):
        nonlocal checkpoint_count
        result = oracle.evaluate(x)
        if len(oracle.records)//25 > checkpoint_count:
            checkpoint_count = len(oracle.records)//25
            print(f'GN trust repeat={repeat} bundles={len(oracle.records)} '
                  f'best={oracle.best["selection_key"]}', flush=True)
            checkpoint()
        return result

    def objective(y):
        values, jacobian = request(coordinates.physical(y))
        return values[0], 0.01*jacobian[0]

    def hessian(y):
        record['hessian_requests'] += 1
        x = coordinates.physical(y)
        request(x)
        return 0.01**2 * backend.hessian_for(x)

    def callback(y, state):
        nonlocal target_stop
        margins = np.asarray(state.constr[0])
        target_stop = bool(state.fun <= 0.008 and np.min(margins) >= 0)
        record['iterations'].append({
            'iteration': int(state.nit), 'objective': float(state.fun),
            'physical_x_sha256': hashlib.sha256(coordinates.physical(y).tobytes()).hexdigest(),
            'minimum_margin': float(np.min(margins)), 'optimality': float(state.optimality),
            'constraint_violation': float(state.constr_violation),
            'trust_radius': float(state.tr_radius),
            'barrier_parameter': float(state.barrier_parameter),
            'construction_target': target_stop})
        return target_stop

    try:
        _, jacobian = request(x0)
        direction = np.random.default_rng(46).normal(size=len(x0))
        direction /= np.linalg.norm(direction)
        # Direction source order is passed explicitly by the shared qualification.
        direction = direction[np.asarray(permutation)]
        exact, screens = jacobian @ direction, []
        for eps in (1e-5, 1e-6, 1e-7, 1e-8):
            plus, minus = request(x0+eps*direction)[0], request(x0-eps*direction)[0]
            fd = (plus-minus)/(2*eps)
            errors = np.abs(fd-exact)/np.maximum(1, np.abs(exact))
            screens.append(dict(eps=eps, finite_difference=fd.tolist(), analytic=exact.tolist(),
                                normalized_errors=errors.tolist()))
        record['gradient_checks'] = screens
        record['gradient_screen_pass'] = bool(max(screens[-1]['normalized_errors']) <= 1e-6)
        if not record['gradient_screen_pass']:
            raise ValueError('unchanged original-state gradient screen failed')
        constraints = NonlinearConstraint(
            lambda y: request(coordinates.physical(y))[0][1:], 0., np.inf,
            jac=lambda y: 0.01*request(coordinates.physical(y))[1][1:],
            hess=BFGS(), keep_feasible=False)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            solution = minimize(objective, np.zeros_like(x0), jac=True, hess=hessian,
                                method='trust-constr', constraints=constraints,
                                callback=callback, options=OPTIONS)
            record['warnings'] = [str(w.message) for w in caught]
        record.update(
            status='solver_returned',
            stop_reason='construction_target' if target_stop else 'solver_returned',
            solver=dict(success=bool(solution.success), status=int(solution.status),
                        message=str(solution.message), nit=int(solution.nit),
                        nfev=int(solution.nfev), njev=int(solution.njev), nhev=int(solution.nhev),
                        optimality=float(solution.optimality),
                        constr_violation=float(solution.constr_violation),
                        physical_terminal_x=coordinates.physical(solution.x).tolist()))
    except BudgetExhausted:
        record.update(status='budget_exhausted', stop_reason='proposal_cap')
    except Exception as exc:
        record.update(status='error', stop_reason='error', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        if oracle.best is not None:
            best = oracle.best
            ctx.Jf.x = best['x'].copy()
            path = raw / 'best.npz'
            with path.open('xb') as stream:
                np.savez_compressed(stream, x=best['x'], values=best['values'])
            field_path = raw / 'best_field.json'
            ctx.Jf.field.save(str(field_path))
            record['best'] = {k: best[k] for k in (
                'attempt', 'x_sha256', 'objective', 'maximum_violation',
                'construction_screen_pass', 'selection_key', 'metrics')}
            record['best'].update(arrays=reference(path), field=reference(field_path))
        checkpoint()
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('study', type=Path)
    parser.add_argument('raw', type=Path)
    args = parser.parse_args()
    if args.study.exists() or args.raw.exists():
        raise FileExistsError('new immutable study paths required')
    root = Path(__file__).resolve().parents[1]
    qualification_path = root / 'evidence/quadratic-field-model-v1.json'
    audit_path = root / 'evidence/quadratic-field-model-v1-core-audit.json'
    qualification = json.loads(qualification_path.read_text())
    audit = json.loads(audit_path.read_text())
    if not all((qualification['qualification_pass'], qualification['model_usefulness_pass'],
                audit['all_pass'], audit['input']['sha256'] == sha256_file(qualification_path))):
        raise ValueError('passing quadratic qualification and independent audit required')
    for ref in qualification['code'] + qualification['qualified_backend_code']:
        checked(ref)
    prior = json.loads(checked(qualification['source_diagnostic']).read_text())
    old_study = json.loads(checked(prior['study']).read_text())
    arm = json.loads(checked(prior['arm']).read_text())
    field_path = checked(arm['best']['field'])
    document = json.loads(field_path.read_text())
    stored_field = load(str(field_path))
    report = dict(
        schema_version=1, repository=git_state(root), host=host_state(),
        protocol=reference(root / 'docs/optimization/GN_TRUST_PILOT_PROTOCOL.md'),
        qualification=reference(qualification_path), core_audit=reference(audit_path),
        status='running', qualification_pass=False, methods=['gn-trust'], arms=[],
        solver_options=OPTIONS, flux_scale=1e-6, construction_tolerance=1e-8,
        qualified_backend_code=qualification['qualified_backend_code'],
        code=[reference(root / p) for p in (
            'scripts/run_gn_trust_pilot.py', 'src/fusion_baselines/gauss_newton_backend.py',
            'src/fusion_baselines/inequality_oracle.py',
            'src/fusion_baselines/affine_coordinates.py',
            'src/fusion_baselines/batched_field_jacobian.py')],
        solver_sources=[reference(Path(inspect.getfile(importlib.import_module(n)))) for n in (
            'scipy.optimize._trustregion_constr.minimize_trustregion_constr',
            'scipy.optimize._trustregion_constr.tr_interior_point',
            'scipy.optimize._trustregion_constr.equality_constrained_sqp',
            'scipy.optimize._hessian_update_strategy')],
        thread_environment={n: os.environ.get(n) for n in (
            'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')})
    args.study.mkdir(parents=True)
    args.raw.mkdir(parents=True)
    try:
        report['analytic_control'] = control()
        if not report['analytic_control']['pass']:
            raise ValueError('analytic constrained solver control failed')
        ctx, _, prep = prepare(root, args.raw, guarded_curvature=True)
        if prep['thresholds'] != qualification['preparation']['thresholds']:
            raise ValueError('physical problem changed')
        full = SurfaceRZFourier.from_vmec_input(
            str(checked(prep['surface'])), range='full torus', nphi=64, ntheta=64)
        direct = DirectConstraintBackend(ctx, full)
        x0 = ctx.Jf.x.copy()
        owners = {}
        for (curve, leaves), coil in zip(base_coil_owners(document), direct.field.coils[:4],
                                         strict=True):
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
        record_permutation = dof_permutation(
            old_study['preparation']['degrees_of_freedom'], direct.names, owners)
        from_old = np.argsort(qualification['source_indices_in_target_order'])[record_permutation]
        gn, qualification_checks = make_gn(direct), []
        for state in qualification['states']:
            with np.load(checked(state['arrays']), allow_pickle=False) as saved:
                x = saved['x'][from_old]
                values, jacobian, _ = gn.evaluate(x)
                dz = saved['dz'][:, from_old]
                checks = dict(values=error(values, saved['values']) <= 1e-10,
                              jacobian=error(jacobian, saved['jacobian'][:, from_old]) <= 1e-10,
                              hessian=error(gn.hessian_for(x), dz.T @ dz / 1e-6) <= 1e-10,
                              identity=bool(np.array_equal(x, x0)) if state['name'] == 'original'
                              else all(np.array_equal(a.curve.gamma(), b.curve.gamma())
                                       and a.current.get_value() == b.current.get_value()
                                       and a.regularization == b.regularization
                                       for a, b in zip(direct.field.coils, stored_field.coils,
                                                       strict=True)))
            qualification_checks.append(dict(name=state['name'], checks=checks))
        report.update(preparation=prep, source_indices_in_target_order=record_permutation.tolist(),
                      labels=direct.labels, shared_qualification=qualification_checks,
                      shared_native_work=dict(direct.work), shared_gn_assemblies=len(gn.records))
        if not all(all(s['checks'].values()) for s in qualification_checks):
            raise ValueError('shared physical GN qualification failed')
        write_json_atomic(args.study/'summary.json', report)
        runs = []
        for repeat in (1, 2):
            output = args.study / f'gn-trust-{repeat}.json'
            runs.append(run_arm(direct, ctx, x0, args.raw / f'gn-trust-{repeat}', output, repeat,
                                record_permutation))
            report['arms'].append(reference(output))
            write_json_atomic(args.study/'summary.json', report)
        a, b = runs
        checks = dict(
            gradient_screens=all(r['gradient_screen_pass'] for r in runs),
            same_counters=a['counters'] == b['counters'],
            same_stop=a['status'] == b['status'] and a['stop_reason'] == b['stop_reason'],
            identical_complete_histories=len(a['evaluations']) == len(b['evaluations']) and all(
                r['x_sha256'] == s['x_sha256'] and r['values'] == s['values']
                for r, s in zip(a['evaluations'], b['evaluations'], strict=True)),
            same_best=a['best']['x_sha256'] == b['best']['x_sha256'],
            same_logical_work=a['work'] == b['work'] and a['gn_work'] == b['gn_work'])
        report.update(status='completed', checks=checks, qualification_pass=all(checks.values()))
    except Exception as exc:
        report.update(status='error', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        write_json_atomic(args.study/'summary.json', report)
    print(json.dumps({'qualification_pass': report['qualification_pass']}))
    return 0 if report['qualification_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
