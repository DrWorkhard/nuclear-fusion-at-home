"""Prepare the frozen original coil seed for a receipt-bound issue37 target.

This supplies the unchanged fitting model and receipt-bound diagnostics, not a
joint driver. Archived-target entry points do not accept these snapshots.
"""
import copy
import hashlib
import io
import json
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


def _diagnostic_inputs(snapshot, folder, parent, record):
    """Reconstruct trusted targets afresh; accept no candidate-provided target arrays."""
    record.guard()
    snapshot = copy.deepcopy(snapshot)
    data, targets, sources, numerical = solver.intake_result(folder, parent, record.guard)
    binding = {k: numerical[k] for k in BINDING_KEYS}
    check.need(numerical['solver_provenance_verified']
               and numerical['numerical_consistency_pass'], 'verified solver intake required')
    snapshot_identity(snapshot, binding)
    for path, sha in parent['sources_before'].items():
        check.bind(path, sha, sources)
    for name, key in (('parent.json', 'record_sha256'), ('solver.json', 'solver_report_sha256'),
                      ('request.json', 'request_sha256')):
        check.bind(Path(folder)/name, parent[key], sources)
    for path in sorted((check.ROOT/'src/fusion_baselines').glob('*.py')):
        check.bind(path, check.digest(path), sources)
    identity = hashlib.sha256(json.dumps(snapshot, sort_keys=True, allow_nan=False,
                                       separators=(',', ':')).encode()).hexdigest()
    context = dict(binding=binding, canonical_snapshot_sha256=identity, intake=numerical,
                   sources=sources, full_joint_execution_enabled=False, physical_admission=False)
    record.guard()
    return snapshot, data, targets, context


def _finish_diagnostic(row, context, record):
    record.guard()
    solver.check_sources(context['sources'])
    record.guard()
    return dict(row, joint_target=context)


def interior(snapshot, folder, parent, ninner, nodes, record):
    """Existing three-surface B/A checks with fixed currents and reference B2."""
    check.need((ninner, nodes) in check.LEVELS, 'registered interior/coil grid required')
    snapshot, data, targets, context = _diagnostic_inputs(snapshot, folder, parent, record)
    row, arrays = check._screen_level(snapshot, data, targets[ninner], ninner, nodes, record,
                                     dict(B2=check.B2, flux=check.TARGET_FLUX))
    return _finish_diagnostic(row, context, record), arrays


def boundary(snapshot, folder, parent, shift, selected_index, record):
    """Existing 128-square/512-node fine field check without current renormalization."""
    check.need(shift in (0., .5) and type(selected_index) is int and selected_index >= 0,
               'registered fine shift and nonnegative selection index required')
    snapshot, data, _, context = _diagnostic_inputs(snapshot, folder, parent, record)
    chosen = dict(index=selected_index, x=np.asarray(snapshot['base_coefficients']).ravel(),
                  metrics=dict(scale=snapshot['scale'], unit_flux=snapshot['unit_flux']))
    row = fit.fine(snapshot, data, chosen, record, shift)
    return _finish_diagnostic(row, context, record)


def geometry(snapshot, folder, parent, record):
    """Existing continuous geometry enclosures against the admitted proposal boundary."""
    snapshot, data, _, context = _diagnostic_inputs(snapshot, folder, parent, record)
    row = check.geometry(snapshot, data, record.guard)
    return _finish_diagnostic(row, context, record)


def direct_trace(snapshot, folder, parent, record):
    """Ten target launches, 200 direct transits and unchanged signed-iota checks."""
    from simsopt.field import BiotSavart
    from simsopt.geo import SurfaceRZFourier

    from fusion_baselines import realized_field as rf

    snapshot, data, _, context = _diagnostic_inputs(snapshot, folder, parent, record)
    wout = Path(folder)/'wout.nc'
    traced_target = rf.Target.from_wout(wout, data)
    check.need(traced_target.sha256 == context['binding']['wout_sha256'],
               'tracing Wout differs from admitted target')
    record.guard()
    coils, own, control = check._native_coils(snapshot, 512)
    field = BiotSavart(coils)
    points = rf.sample_points(traced_target, np.random.default_rng(20261005), 64)
    field.set_points(points)
    expected, _ = record.call('independent_BA', check.independent.filament_field_and_potential,
                              points, own['positions'], own['tangents'], own['currents'])
    actual = record.call('B', field.B).copy()
    control['independent_volume'] = check.error(actual, expected)
    check.need(max(control.values()) <= 1e-12, 'direct tracing field identity failed')
    buffer = io.BytesIO()
    np.savez_compressed(buffer, points=points, native_B=actual, independent_B=expected,
                        **own)
    record.save('trace-kernel.npz', buffer.getvalue())
    surface = SurfaceRZFourier.from_wout(str(wout), range='full torus', nphi=128, ntheta=64)
    record.guard()
    row = dict(completed=False, field='direct BiotSavart', transits=200,
               target_launches=list(rf.S_VALUES), tol=1e-10, kernel_control=control,
               kernel_arrays_sha256=check.digest(record.output/'trace-kernel.npz'),
               frozen_current=True, current_A=1e5*snapshot['scale'], physical_admission=False)
    record.save('direct-trace-attempt.json', dict(row, joint_target=context))
    record.guard()
    lines, hits, paths = rf.trace(field, traced_target, surface, transits=200, tol=1e-10,
                                  s_values=rf.S_VALUES, keep_paths=True)
    record.guard()
    check.need(len(lines) == len(hits) == len(paths) == 10, 'all ten trace records required')
    hashes = {}
    for index, (path, hit) in enumerate(zip(paths, hits, strict=True)):
        record.guard()
        buffer = io.BytesIO()
        np.savez_compressed(buffer, path=path, hits=hit)
        name = f'trace-line-{index}.npz'
        record.save(name, buffer.getvalue())
        hashes[name] = check.digest(record.output/name)
    row.update(completed=True, lines=lines, summary=rf.summarize(lines, 200), arrays_sha256=hashes,
               internal_native_field_call_counts_measured=False)
    return _finish_diagnostic(row, context, record)
