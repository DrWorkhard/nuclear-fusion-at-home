from copy import deepcopy

import numpy as np
import pytest

from fusion_baselines.gn_pilot_audit import audit_gn_ledger


def fixture():
    n = 1
    errors = dict(field_relative_error=0., gradient_normalized_error=1e-13,
                  batch_field_relative_error=1e-14, projection_normalized_error=1e-17,
                  uncoupled_gradient_normalized_error=1e-8)
    values = [0.008, *np.ones(137).tolist()]
    return dict(
        counters=dict(attempts=n, requests=5), hessian_requests=1,
        gn_work=dict(assemblies=n, assembly_attempts=n, failed_assemblies=0,
                     native_covector_B_requests=n, coil_contractions=16*n,
                     geometry_derivative_requests=32*n, current_VJP_requests=16*n),
        work=dict(evaluations=n, jacobian_evaluations=n, B_grid_requests=n, B_vjp_requests=n,
                  position_requests=16*n, position_derivative_requests=16*n,
                  curvature_requests=4*n, curvature_derivative_requests=4*n,
                  native_metric_requests=12*n, native_gradient_requests=12*n,
                  coil_pair_samples=4800000*n, plasma_pair_samples=3276800*n),
        gn_identity_checks=[errors], gradient_checks=[
            dict(eps=h, finite_difference=np.zeros(138).tolist(), analytic=np.zeros(138).tolist(),
                 normalized_errors=np.zeros(138).tolist()) for h in (1e-5, 1e-6, 1e-7, 1e-8)],
        evaluations=[dict(x_sha256='saved', status='completed', values=values)],
        iterations=[dict(physical_x_sha256='saved', objective=0.008, minimum_margin=1.,
                         construction_target=True)],
        stop_reason='construction_target', solver=dict(status=3, success=False))


def test_work_audit_preserves_uncoupled_failure_without_false_convergence():
    assert all(audit_gn_ledger(fixture()).values())


@pytest.mark.parametrize('field', ['gn_work', 'identity', 'iteration', 'convergence', 'gradient'])
def test_gn_audit_detects_mutated_evidence(field):
    arm = deepcopy(fixture())
    if field == 'gn_work':
        arm['gn_work']['native_covector_B_requests'] = 0
    elif field == 'identity':
        arm['gn_identity_checks'][0]['gradient_normalized_error'] = 2e-10
    elif field == 'iteration':
        arm['iterations'][0]['minimum_margin'] = 2
    elif field == 'convergence':
        arm['solver']['success'] = True
    else:
        arm['gradient_checks'][-1]['finite_difference'][0] = 1
    assert not all(audit_gn_ledger(arm).values())
