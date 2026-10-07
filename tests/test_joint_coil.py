"""Joint seed preparation never changes the archived target registry or gates."""
import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest
import test_coil_check as fixtures

from fusion_baselines import joint_coil as joint


@pytest.fixture
def snapshot():
    return fixtures.snapshot.__wrapped__()


@pytest.fixture
def binding():
    return dict(target_id='issue37-joint-v1/plus',
                input_sha256=joint.target.INPUT_HASHES['plus'],
                wout_sha256='a'*64, parent_sha256='b'*64)


def adapted(snapshot, binding):
    result = copy.deepcopy(snapshot)
    result.update(target_id=binding['target_id'], joint_target_binding=copy.deepcopy(binding))
    return result


def test_joint_snapshot_keeps_archived_registry_closed(snapshot, binding):
    seed = adapted(snapshot, binding)
    joint.snapshot_identity(seed, binding)
    for archived in ('reference401', 'selected401', binding['target_id']):
        with pytest.raises(ValueError):
            joint.check.snapshot_identity(seed, archived)
    with pytest.raises(ValueError):
        joint.snapshot_identity(snapshot, binding)
    assert set(joint.check.TARGETS) == {'reference401', 'selected401'}


@pytest.mark.parametrize('fault', ['target', 'input', 'wout', 'receipt', 'missing',
                                  'B2', 'flux', 'physical', 'orientation'])
def test_joint_snapshot_rejects_mixed_binding_or_changed_conventions(snapshot, binding, fault):
    seed = adapted(snapshot, binding)
    if fault in ('target', 'input', 'wout', 'receipt'):
        key = dict(target='target_id', input='input_sha256', wout='wout_sha256',
                   receipt='parent_sha256')[fault]
        seed['joint_target_binding'][key] = 'c'*64
    elif fault == 'missing':
        del seed['joint_target_binding']['parent_sha256']
    elif fault == 'B2':
        seed['B2_scale'] *= 1.01
    elif fault == 'flux':
        seed['target_flux'] *= -1
    elif fault == 'physical':
        seed['physical'][0]['current'] *= -1
    else:
        seed['seed_unit_flux'] *= -1
    with pytest.raises(ValueError):
        joint.snapshot_identity(seed, binding)


def test_freezing_selection_keeps_target_seed_and_frozen_currents(snapshot, binding):
    seed = adapted(snapshot, binding)
    prepared = dict(seed=seed, binding=binding, sources={})
    original = copy.deepcopy(prepared)
    coefficients = np.asarray(seed['base_coefficients']).ravel()
    coefficients[0] += .001
    phi = seed['unit_flux']*1.01
    row = dict(status='completed', role='search', x=coefficients,
               metrics=dict(unit_flux=phi, scale=joint.check.TARGET_FLUX/phi))
    chosen = joint.selected_snapshot(prepared, row)
    assert prepared == original
    assert np.asarray(chosen['base_coefficients']).ravel()[0] == coefficients[0]
    assert chosen['scale'] == row['metrics']['scale']
    assert chosen['seed_unit_flux'] == seed['seed_unit_flux']
    assert chosen['joint_target_binding'] == binding
    for item in chosen['physical']:
        assert item['current'] == 1e5*chosen['scale']*(-1 if item['flip'] else 1)
    row['role'] = 'probe'
    with pytest.raises(ValueError, match='completed fit row'):
        joint.selected_snapshot(prepared, row)
    row['role'] = 'search'
    row['metrics']['scale'] *= 1.01
    with pytest.raises(ValueError, match='current scale'):
        joint.selected_snapshot(prepared, row)


def test_changed_sources_prevent_freezing(snapshot, binding, tmp_path):
    source = tmp_path/'source'
    source.write_text('before')
    prepared = dict(seed=adapted(snapshot, binding), binding=binding,
                    sources={str(source): joint.check.digest(source)})
    source.write_text('after')
    with pytest.raises(ValueError, match='source/input changed'):
        joint.selected_snapshot(prepared, {})


def test_rejected_solver_receipt_cannot_construct_model(monkeypatch, tmp_path):
    calls = []
    def reject(*args):
        raise ValueError('receipt rejected')
    monkeypatch.setattr(joint.solver, 'intake_result', reject)
    monkeypatch.setattr(joint.fit, 'Model', lambda *a: calls.append(a))
    with pytest.raises(ValueError, match='receipt rejected'):
        joint.prepare(tmp_path/'seed', tmp_path, {}, SimpleNamespace(guard=lambda: None))
    assert calls == []


@pytest.mark.parametrize('phi', [0., 1e-13, np.nan, np.inf, .01])
def test_seed_renormalization_rejects_invalid_or_reversed_flux(snapshot, phi):
    original = copy.deepcopy(snapshot)
    with pytest.raises(ValueError, match='orientation'):
        joint.normalize(snapshot, phi)
    assert snapshot == original


@pytest.mark.parametrize('proposal', ['plus', 'minus'])
def test_preparation_rebuilds_named_seed_for_each_target(snapshot, binding, monkeypatch,
                                                       tmp_path, proposal):
    binding.update(target_id=f'issue37-joint-v1/{proposal}',
                   input_sha256=joint.target.INPUT_HASHES[proposal])
    seed_path = tmp_path/'seed.json'
    seed_path.write_text(json.dumps(snapshot))
    monkeypatch.setattr(joint, 'SEED_SHA', joint.check.digest(seed_path))
    parent = dict(sources_before={})
    for name, key in (('parent.json', 'record_sha256'), ('solver.json', 'solver_report_sha256'),
                      ('request.json', 'request_sha256')):
        path = tmp_path/name
        path.write_text(name)
        parent[key] = joint.check.digest(path)
    data = {'proposal': proposal}
    numerical = dict(binding, solver_provenance_verified=True, numerical_consistency_pass=True)
    monkeypatch.setattr(joint.solver, 'intake_result', lambda *a: (data, {}, {}, numerical))
    models = []
    def model(seed, boundary, record):
        assert boundary is data
        assert seed['base_coefficients'] == snapshot['base_coefficients']
        assert seed['names'] == snapshot['names']
        result = SimpleNamespace(seed=seed, unit_flux=lambda: snapshot['unit_flux']*1.03)
        models.append(result)
        return result
    monkeypatch.setattr(joint.fit, 'Model', model)
    prepared = joint.prepare(seed_path, tmp_path, parent, SimpleNamespace(guard=lambda: None))
    assert len(models) == 1 and models[0].seed is prepared['seed']
    assert prepared['seed']['seed_unit_flux'] == snapshot['unit_flux']*1.03
    assert prepared['seed']['scale'] == joint.check.TARGET_FLUX/(snapshot['unit_flux']*1.03)
    joint.snapshot_identity(prepared['seed'], binding)
    assert prepared['seed']['base_coefficients'] == snapshot['base_coefficients']
    assert json.loads(seed_path.read_text()) == snapshot
    assert not prepared['physical_admission'] and not prepared['full_joint_execution_enabled']
    seed_path.write_text(seed_path.read_text()+' ')
    with pytest.raises(ValueError, match='source identity changed'):
        joint.prepare(seed_path, tmp_path, parent, SimpleNamespace(guard=lambda: None))
    assert len(models) == 1
