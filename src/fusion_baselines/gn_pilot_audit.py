"""Additional independent work, identity and accepted-iteration checks for GN pilots."""

import numpy as np


def audit_gn_ledger(arm):
    n = arm['counters']['attempts']
    expected = dict(assemblies=n, assembly_attempts=n, failed_assemblies=0,
                    native_covector_B_requests=n, coil_contractions=16*n,
                    geometry_derivative_requests=32*n, current_VJP_requests=16*n)
    native = dict(evaluations=n, jacobian_evaluations=n, B_grid_requests=n, B_vjp_requests=n,
                  position_requests=16*n, position_derivative_requests=16*n,
                  curvature_requests=4*n, curvature_derivative_requests=4*n,
                  native_metric_requests=12*n, native_gradient_requests=12*n,
                  coil_pair_samples=4800000*n, plasma_pair_samples=3276800*n)
    required_errors = ('field_relative_error', 'gradient_normalized_error',
                       'batch_field_relative_error', 'projection_normalized_error')
    identities = arm['gn_identity_checks']
    checks = dict(
        additional_gn_work=arm['gn_work'] == expected, native_work=arm['work'] == native,
        all_gn_identities=len(identities) == n and all(
            np.isfinite(record[k]) and 0 <= record[k] <= 1e-10
            for record in identities for k in required_errors),
        hessian_requests_counted=0 < arm['hessian_requests'] <= arm['counters']['requests'])
    gradients = arm['gradient_checks']
    finest = gradients[-1]
    actual = np.asarray(finest['finite_difference'])
    exact = np.asarray(finest['analytic'])
    errors = np.abs(actual-exact) / np.maximum(1, np.abs(exact))
    checks['independent_gradient_screen'] = bool(
        [r['eps'] for r in gradients] == [1e-5, 1e-6, 1e-7, 1e-8]
        and actual.shape == exact.shape == (138,) and np.all(np.isfinite(errors))
        and errors.max() <= 1e-6
        and np.array_equal(errors, finest['normalized_errors']))
    by_hash = {row['x_sha256']: row for row in arm['evaluations'] if row['status'] == 'completed'}
    iterations, aligned = arm['iterations'], True
    for record in iterations:
        row = by_hash.get(record['physical_x_sha256'])
        if row is None:
            aligned = False
            continue
        values = np.asarray(row['values'])
        margin = float(np.min(values[1:]))
        aligned &= (values[0] == record['objective'] and margin == record['minimum_margin']
                    and record['construction_target'] == (values[0] <= 0.008 and margin >= 0))
    checks['accepted_iterations_bound_to_evaluated_values'] = bool(iterations) and bool(aligned)
    if arm['stop_reason'] == 'construction_target':
        checks['construction_stop_not_convergence'] = bool(
            iterations and iterations[-1]['construction_target']
            and not any(i['construction_target'] for i in iterations[:-1])
            and arm['solver']['status'] == 3 and not arm['solver']['success'])
    else:
        checks['no_unreported_target_stop'] = not any(i['construction_target'] for i in iterations)
    return {k: bool(v) for k, v in checks.items()}
