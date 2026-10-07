"""Receipt-bound diagnostic routes reuse checks without admitting candidate targets."""
import copy
from types import SimpleNamespace

import numpy as np
import pytest
import test_coil_check as fixtures
import test_joint_coil as joint_fixtures

from fusion_baselines import joint_coil as joint


@pytest.fixture
def admitted(tmp_path, monkeypatch):
    binding = joint_fixtures.binding.__wrapped__()
    snapshot = joint_fixtures.adapted(fixtures.snapshot.__wrapped__(), binding)
    parent = dict(sources_before={})
    for name, key in (('parent.json', 'record_sha256'), ('solver.json', 'solver_report_sha256'),
                      ('request.json', 'request_sha256')):
        path = tmp_path/name
        path.write_text(name, encoding='utf-8')
        parent[key] = joint.check.digest(path)
    data, targets = {'trusted': True}, {32: {'trusted': 'arrays'}}
    numerical = dict(binding, solver_provenance_verified=True, numerical_consistency_pass=True)
    calls = []
    def intake(folder, receipt, guard):
        assert folder == tmp_path and receipt is parent
        calls.append('intake')
        return data, targets, {}, numerical
    monkeypatch.setattr(joint.solver, 'intake_result', intake)
    record = SimpleNamespace(guard=lambda: None)
    return SimpleNamespace(snapshot=snapshot, binding=binding, parent=parent,
        folder=tmp_path, data=data, targets=targets, record=record, calls=calls)


def invoke(kind, a):
    args = (a.snapshot, a.folder, a.parent)
    if kind == 'interior':
        return joint.interior(*args, 32, 256, a.record)[0]
    if kind == 'boundary':
        return joint.boundary(*args, .5, 7, a.record)
    return joint.geometry(*args, a.record)


@pytest.mark.parametrize('kind', ['interior', 'boundary', 'geometry'])
def test_diagnostics_reconstruct_target_and_keep_frozen_snapshot(admitted, monkeypatch, kind):
    a = admitted
    original = copy.deepcopy(a.snapshot)
    def capture(snapshot, data, *args):
        assert snapshot == original and snapshot is not a.snapshot
        assert data is a.data
        a.calls.append(kind)
        # Mutation of the caller's candidate cannot change the frozen local copy.
        a.snapshot['scale'] *= 2
        assert snapshot == original
        if kind == 'interior':
            target, n, nodes, record, spec = args
            assert target is a.targets[32] and (n, nodes) == (32, 256)
            assert spec == dict(B2=joint.check.B2, flux=joint.check.TARGET_FLUX)
            return dict(checks_pass=True, physical_admission=False), {}
        if kind == 'boundary':
            chosen, record, shift = args
            assert shift == .5 and chosen['index'] == 7
            np.testing.assert_array_equal(chosen['x'],
                                          np.asarray(original['base_coefficients']).ravel())
            assert chosen['metrics'] == dict(scale=original['scale'],
                                            unit_flux=original['unit_flux'])
        return dict(physical_admission=False)
    monkeypatch.setattr(joint.check, '_screen_level', capture)
    monkeypatch.setattr(joint.fit, 'fine', capture)
    monkeypatch.setattr(joint.check, 'geometry', capture)
    result = invoke(kind, a)
    assert a.calls == ['intake', kind]
    assert result['joint_target']['binding'] == a.binding
    assert not result['physical_admission']
    assert not result['joint_target']['full_joint_execution_enabled']
    assert len(result['joint_target']['canonical_snapshot_sha256']) == 64


@pytest.mark.parametrize('kind', ['interior', 'boundary', 'geometry'])
@pytest.mark.parametrize('fault', ['target', 'wout', 'receipt', 'B2', 'current'])
def test_invalid_target_binding_or_physics_never_reaches_field(admitted, monkeypatch, kind, fault):
    a = admitted
    if fault in ('target', 'wout', 'receipt'):
        key = dict(target='target_id', wout='wout_sha256', receipt='parent_sha256')[fault]
        a.snapshot['joint_target_binding'][key] = 'c'*64
    elif fault == 'B2':
        a.snapshot['B2_scale'] *= 1.01
    else:
        a.snapshot['physical'][0]['current'] *= -1
    def forbidden(*args):
        pytest.fail('invalid snapshot reached native diagnostic')
    monkeypatch.setattr(joint.check, '_screen_level', forbidden)
    monkeypatch.setattr(joint.fit, 'fine', forbidden)
    monkeypatch.setattr(joint.check, 'geometry', forbidden)
    with pytest.raises(ValueError):
        invoke(kind, a)


@pytest.mark.parametrize('kind', ['interior', 'boundary', 'geometry'])
def test_changed_receipt_during_diagnostic_invalidates_result(admitted, monkeypatch, kind):
    a = admitted
    def corrupt(*args):
        (a.folder/'parent.json').write_text('changed', encoding='utf-8')
        return ({'checks_pass': True}, {}) if kind == 'interior' else {'status': 'pass'}
    monkeypatch.setattr(joint.check, '_screen_level', corrupt)
    monkeypatch.setattr(joint.fit, 'fine', corrupt)
    monkeypatch.setattr(joint.check, 'geometry', corrupt)
    with pytest.raises(ValueError, match='source/input changed'):
        invoke(kind, a)


def test_shared_metrics_equal_archived_route_with_identical_physics():
    original = fixtures.snapshot.__wrapped__()
    binding = joint_fixtures.binding.__wrapped__()
    snapshot = joint_fixtures.adapted(original, binding)
    B, target, A, tangent = fixtures.metric_arrays()
    expected = joint.check.field_metrics(B, target, A, tangent, original, 32)
    actual = joint.check._field_metrics(B, target, A, tangent, snapshot, 32,
                                      dict(B2=joint.check.B2, flux=joint.check.TARGET_FLUX))
    assert actual == expected
    assert not actual['fine_renormalization_applied']
    with pytest.raises(ValueError, match='normalization differ'):
        joint.check._field_metrics(B, target, A, tangent, snapshot, 32,
                                   dict(B2=joint.check.B2*1.01, flux=joint.check.TARGET_FLUX))


@pytest.mark.parametrize('kind', ['interior', 'boundary', 'geometry'])
def test_unverified_solver_never_reaches_diagnostics(admitted, monkeypatch, kind):
    a = admitted
    def reject(*args):
        raise ValueError('unverified solver receipt')
    monkeypatch.setattr(joint.solver, 'intake_result', reject)
    with pytest.raises(ValueError, match='unverified solver receipt'):
        invoke(kind, a)
