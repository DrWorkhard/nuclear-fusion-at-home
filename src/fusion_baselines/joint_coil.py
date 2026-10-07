"""Prepare the frozen original coil seed for a receipt-bound issue37 target.

This supplies the unchanged fitting model, not a joint driver or an acceptance
route. Archived-target evaluators deliberately do not accept these snapshots.
"""
import copy
import re
from pathlib import Path

import numpy as np

from fusion_baselines import coil_check as check
from fusion_baselines import coil_fit as fit
from fusion_baselines import joint_equilibrium as solver
from fusion_baselines import joint_target as target

SEED_SHA = '84bbdf3eca274981dfff80c967b6fd623a1a40350e583407cbb7262c26820217'
BINDING_KEYS = ('target_id', 'input_sha256', 'wout_sha256', 'parent_sha256')


def snapshot_identity(snapshot, binding):
    """Exact proposal identity plus the existing independent physical mapping."""
    check.need(set(binding) == set(BINDING_KEYS), 'complete joint target binding required')
    proposal = binding['target_id'].removeprefix('issue37-joint-v1/')
    check.need(proposal in ('plus', 'minus')
               and binding['target_id'] == f'issue37-joint-v1/{proposal}'
               and binding['input_sha256'] == target.INPUT_HASHES[proposal]
               and all(isinstance(binding[k], str) and re.fullmatch('[0-9a-f]{64}', binding[k])
                       for k in BINDING_KEYS[1:]), 'registered proposal binding required')
    check.independent.validate_snapshot(snapshot)
    check.need(snapshot.get('target_id') == binding['target_id']
               and snapshot.get('joint_target_binding') == binding,
               'snapshot belongs to a different joint target')
    check.need(snapshot['nbase'] == 6 and snapshot['order'] == 5
               and snapshot['B2_scale'] == check.B2
               and snapshot['target_flux'] == check.TARGET_FLUX,
               'frozen six/order5 coils, reference B2 and signed flux required')
    check.need(np.isfinite(snapshot['seed_unit_flux']) and abs(snapshot['seed_unit_flux']) > 1e-12
               and np.sign(snapshot['unit_flux']) == np.sign(snapshot['seed_unit_flux']),
               'preserved nondegenerate seed flux orientation required')


def normalize(snapshot, unit_flux):
    """Same scalar current rule as Model.evaluate and fine; never move a coil."""
    check.need(np.isfinite(unit_flux) and abs(unit_flux) > 1e-12
               and np.sign(unit_flux) == np.sign(snapshot['seed_unit_flux']),
               'nondegenerate unit flux with original orientation required')
    snapshot.update(unit_flux=float(unit_flux), scale=check.TARGET_FLUX/float(unit_flux))
    for row in snapshot['physical']:
        row['current'] = 1e5*snapshot['scale']*(-1 if row['flip'] else 1)


def prepare(seed_path, folder, parent, record):
    """Intake a trusted parent's solve and rebuild the original seed's model.

The caller owns the arm budget and provenance of the in-memory parent receipt.
A cached qualification receipt does not make its solve free in a future arm.
"""
    record.guard()
    data, targets, sources, numerical = solver.intake_result(folder, parent, record.guard)
    check.need(numerical['solver_provenance_verified']
               and numerical['numerical_consistency_pass'], 'verified solver intake required')
    binding = {k: numerical[k] for k in BINDING_KEYS}
    seed_path = check.bind(seed_path, SEED_SHA, sources)
    seed = check.read_json(seed_path)
    check.snapshot_identity(seed, 'reference401')
    check.need(seed['order'] == 5, 'original order5 seed required')
    seed.update(target_id=binding['target_id'], joint_target_binding=copy.deepcopy(binding))
    snapshot_identity(seed, binding)
    # Receipt/source checks are repeated by the caller after fitting. No global
    # registry modification or relabelling as an archived target is involved.
    for path, sha in parent['sources_before'].items():
        check.bind(path, sha, sources)
    folder = Path(folder)
    for name, key in (('parent.json', 'record_sha256'), ('solver.json', 'solver_report_sha256'),
                      ('request.json', 'request_sha256')):
        check.bind(folder/name, parent[key], sources)
    for path in sorted((check.ROOT/'src/fusion_baselines').glob('*.py')):
        check.bind(path, check.digest(path), sources)
    record.guard()
    model = fit.Model(seed, data, record)
    normalize(seed, model.unit_flux())
    seed['seed_unit_flux'] = seed['unit_flux']
    snapshot_identity(seed, binding)
    record.guard()
    solver.check_sources(sources)
    record.guard()
    return dict(seed=seed, data=data, targets=targets, model=model, sources=sources,
                binding=binding, intake=numerical, physical_admission=False,
                full_joint_execution_enabled=False)


def selected_snapshot(prepared, selected):
    """Freeze the selected fit row's coefficients and currents for later diagnostics."""
    solver.check_sources(prepared['sources'])
    check.need(selected['status'] == 'completed'
               and selected['role'] in ('startup-seed', 'search'), 'completed fit row required')
    result = copy.deepcopy(prepared['seed'])
    snapshot_identity(result, prepared['binding'])
    result['base_coefficients'] = np.asarray(selected['x']).reshape(6, 3, 11).tolist()
    normalize(result, selected['metrics']['unit_flux'])
    check.need(result['scale'] == selected['metrics']['scale'], 'selected current scale changed')
    snapshot_identity(result, prepared['binding'])
    return result
