"""Numerical intake for fixed issue37 comparisons and a separate one-point screen.

This does not authorize joint execution or certify solver provenance/physics.
Existing reference401/selected401 intake and normalization gates stay separate.
"""
import copy

import numpy as np

from fusion_baselines import coil_check as check
from fusion_baselines import coupled_coil_audit as geometry
from fusion_baselines import wout_target
from fusion_baselines.clear_coil_field_audit import archived_target
from fusion_baselines.reference_wout import validate_reference

INPUT_HASHES = {
    'control': '57394ef682f3c6399faa03012abc02da2eb1ce40703a4f99640ece3d07e5691f',
    'plus': '3ad26eada826bbb0e33cadfbcf9c393acd9bcc6a72b32a4059e052d8675208b9',
    'minus': 'e7f764ab6a348225c31487696e8190dfb36aea9940b551e2e120abf6fb951599',
    'scale035': '68dac87c81a3356805736fa874175e20041b3c5a79966e6247adb68b31460dcf',
}
DELTAS = {'control': 0., 'plus': .001, 'minus': -.001, 'scale035': .00035}
PROTOCOL = 'docs/optimization/ISSUE37_JOINT_FEASIBILITY.json'
PROTOCOL_SHA = '25a8887544c4861c1e7c40ff0c884730f2ac5784ea3460430a69fd7ece6690b7'
SCALE_PROTOCOL = 'docs/optimization/ISSUE37_STEP_SCALE.json'
SCALE_PROTOCOL_SHA = '583a3eeb45af28a54de0f4be100ef366d99f501efd2392b403a18024757c7d44'
SURFACES = (.25, .5, .75)
GRIDS = (64, 128)


def proposal_id(proposal):
    namespace = 'issue37-step-scale-v1' if proposal == 'scale035' else 'issue37-joint-v1'
    return f'{namespace}/{proposal}'


def registered_input(path, proposal, sources):
    check.need(proposal in INPUT_HASHES, 'registered issue37 proposal required')
    protocol, sha = ((SCALE_PROTOCOL, SCALE_PROTOCOL_SHA) if proposal == 'scale035'
                     else (PROTOCOL, PROTOCOL_SHA))
    check.bind(check.ROOT/protocol, sha, sources)
    original_path = check.bind(check.ROOT/check.TARGET, INPUT_HASHES['control'], sources)
    original = check.read_json(original_path)
    data = check.read_json(check.bind(path, INPUT_HASHES[proposal], sources))
    expected = copy.deepcopy(original)
    row = [r for r in expected['rbc'] if (r['m'], r['n']) == (2, 1)]
    check.need(len(row) == 1 and row[0]['value'] == -.00788128880747288,
               'original named coefficient required')
    row[0]['value'] += DELTAS[proposal]
    check.need(data == expected, 'only the registered coefficient change is permitted')
    return data, original


def volume(document, count):
    """Same full-turn signed integral and cylindrical cross-check as the preflight."""
    surface = geometry.boundary(document, count, count, full_torus=True, shift=True)
    signed = float(np.mean(np.sum(surface['points'] * np.cross(
        surface['dtheta'], surface['dphi']), axis=-1)) / 3)
    phi, theta = np.meshgrid(2*np.pi*(np.arange(count)+.5)/count,
                            2*np.pi*(np.arange(count)+.5)/count, indexing='ij')
    radius, ztheta = np.zeros_like(theta), np.zeros_like(theta)
    for row in document['rbc']:
        radius += row['value']*np.cos(row['m']*theta-row['n']*document['nfp']*phi)
    for row in document['zbs']:
        ztheta += row['m']*row['value']*np.cos(
            row['m']*theta-row['n']*document['nfp']*phi)
    cylindrical = float(-.5*(2*np.pi)**2*np.mean(radius**2*ztheta))
    check.need(np.isfinite([signed, cylindrical]).all() and abs(signed) > 1e-12
               and abs(signed-cylindrical) <= 1e-10*max(abs(signed), abs(cylindrical)),
               'independent volume check failed')
    return abs(signed)


def size_check(data, original, guard):
    rows = []
    for document in (original, data):
        values = []
        for count in (128, 256):
            guard()
            values.append(volume(document, count))
            guard()
        check.need(abs(values[0]-values[1])/max(values) <= 1e-6,
                   'volume grid disagreement')
        rows.append(values)
    changes = [v/b-1 for v, b in zip(rows[1], rows[0], strict=True)]
    check.need(max(abs(v) for v in changes) <= .001, 'registered volume limit failed')
    return dict(grids=[128, 256], original_m3=rows[0], proposal_m3=rows[1],
                relative_changes=changes)


def validate_equilibrium(data, target_input):
    """Strict recorded numerical state; no claim of a unique or stable equilibrium."""
    required_scalars = ('nfp', 'ns', 'lasym__logical__', 'lfreeb__logical__',
                        'lrfp__logical__', 'mpol', 'ntor', 'ier_flag', 'signgs',
                        'fsqr', 'fsqz', 'fsql', 'ftolv', 'ctor', 'volume_p',
                        'mnmax', 'mnmax_nyq')
    required_vectors = ('phi', 'pres', 'presf', 'phipf', 'phips', 'iotas')
    keys = (*required_scalars, *required_vectors, 'xm', 'xn', 'xm_nyq', 'xn_nyq',
            'rmnc', 'zmns', 'lmns', 'gmnc', 'bmnc', 'bsupumnc', 'bsupvmnc')
    arrays = {}
    for key in keys:
        a = np.ma.asarray(data[key][...], dtype=float).filled(np.nan)
        check.need(a.size > 0 and np.isfinite(a).all(), f'finite Wout array required: {key}')
        arrays[key] = a
    for key in required_scalars:
        check.need(arrays[key].shape == (), f'scalar Wout value required: {key}')
    for key in required_vectors:
        check.need(arrays[key].shape == (401,), f'401-point Wout profile required: {key}')
    # Frozen input uses ntheta=32,nzeta=48; VMEC output tables have maxima
    # (mpol-1,ntor)=(4,10) and (ntheta/2,nzeta/2)=(16,24). Exact complete
    # sets reject out-of-band interior modes that alias on both check grids.
    check.need((target_input['mpol'], target_input['ntor'], target_input['ntheta'],
                target_input['nzeta']) == (5, 10, 32, 48), 'frozen mode tables required')
    for mkey, nkey, count_key, mmax, nmax in (
            ('xm', 'xn', 'mnmax', 4, 10), ('xm_nyq', 'xn_nyq', 'mnmax_nyq', 16, 24)):
        m, n = arrays[mkey], arrays[nkey]
        check.need(m.ndim == 1 and m.size and m.shape == n.shape,
                   'matched Fourier mode vectors required')
        pairs = np.column_stack((m, n/2))
        check.need(np.array_equal(pairs, np.rint(pairs)) and np.all(m >= 0)
                   and len(np.unique(pairs, axis=0)) == len(pairs),
                   'unique nonnegative integer Fourier mode pairs required')
        expected = {(0, k) for k in range(nmax+1)} | {
            (j, k) for j in range(1, mmax+1) for k in range(-nmax, nmax+1)}
        check.need(set(map(tuple, pairs)) == expected
                   and arrays[count_key] == len(expected),
                   f'complete frozen Fourier mode table required: {mkey}')
    for key in ('rmnc', 'zmns', 'lmns'):
        check.need(arrays[key].shape == (401, len(arrays['xm'])),
                   f'full geometric coefficient matrix required: {key}')
    for key in ('gmnc', 'bmnc', 'bsupumnc', 'bsupvmnc'):
        check.need(arrays[key].shape == (401, len(arrays['xm_nyq'])),
                   f'full Nyquist coefficient matrix required: {key}')
    validate_reference(arrays, target_input)
    check.need(arrays['mpol'] == target_input['mpol']
               and arrays['ntor'] == target_input['ntor'] and arrays['signgs'] == -1,
               'frozen Fourier resolution and Jacobian orientation required')
    check.need(all(arrays[k] == 0 for k in ('ier_flag', 'lfreeb__logical__', 'lrfp__logical__')),
               'converged fixed-boundary non-RFP equilibrium required')
    tolerance = target_input['ftol_array'][-1]
    residuals = {k: float(arrays[k]) for k in ('fsqr', 'fsqz', 'fsql')}
    check.need(arrays['ftolv'] == tolerance and all(0 <= v <= tolerance
                                                  for v in residuals.values()),
               'recorded force residuals exceed the frozen convergence tolerance')
    check.need(all(np.all(arrays[k] == 0) for k in ('pres', 'presf'))
               and abs(arrays['ctor']) <= 1e-6, 'vacuum pressure and net-current checks failed')
    flux = target_input['phiedge']
    check.need(np.max(abs(arrays['phi']-np.linspace(0, flux, 401))) <= 1e-14
               and np.max(abs(arrays['phipf']-flux)) <= 1e-14
               and np.max(abs(arrays['phips'][1:]+flux/(2*np.pi))) <= 1e-14,
               'frozen linear toroidal flux and sign conventions required')
    check.need(arrays['volume_p'] > 0, 'positive recorded volume required')
    return arrays, dict(force_residuals=residuals, ftol=tolerance,
                        net_current_A=float(arrays['ctor']))


# Reused unchanged mathematical checks from clebsch_field at research freeze
# 56181dc4250cb24ce3d2bedf5cec3d894d1ac250; archived studies are not rerun.
def compare_fields(psi, g, bt, bp, lt, lp, iota, et, ep, mod_b):
    g, bt, bp, lt, lp, mod_b = [np.asarray(v, dtype=float) for v in (g, bt, bp, lt, lp, mod_b)]
    et, ep = np.asarray(et, dtype=float), np.asarray(ep, dtype=float)
    if (
        not np.isfinite(psi) or psi == 0 or not np.isfinite(iota)
        or g.size == 0 or any(v.shape != g.shape for v in (bt, bp, lt, lp, mod_b))
        or et.shape != ep.shape or et.shape != (*g.shape, 3)
        or any(not np.isfinite(v).all() for v in (g, bt, bp, lt, lp, mod_b, et, ep))
        or np.any(g == 0) or np.any(mod_b <= 0)
    ):
        raise ValueError("finite nonsingular field-coordinate arrays required")
    expected_p, expected_t = psi * (1 + lt), psi * (iota - lp)
    norm_p = float(np.max(abs(expected_p)))
    if norm_p == 0:
        raise ValueError("nonzero toroidal reference required")
    native = bt[..., None] * et + bp[..., None] * ep
    clebsch = (expected_t[..., None] * et + expected_p[..., None] * ep) / g[..., None]
    norm_b = float(np.max(np.linalg.norm(native, axis=-1)))
    if norm_b == 0 or not np.isfinite(clebsch).all():
        raise ValueError("nonzero finite reconstructed field required")
    errors = dict(
        toroidal=float(np.max(abs(g * bp - expected_p)) / norm_p),
        poloidal=float(np.max(abs(g * bt - expected_t)) /
                       max(abs(psi), float(np.max(abs(expected_t))))),
        cartesian=float(np.max(np.linalg.norm(native - clebsch, axis=-1)) / norm_b),
        magnitude=float(np.max(abs(np.linalg.norm(native, axis=-1) - mod_b)) / mod_b.max()),
        wrong_sign=float(np.max(abs(g * bp + expected_p)) / norm_p),
        missing_2pi=float(np.max(abs(g * bp - 2 * np.pi * expected_p)) / norm_p),
    )
    checks = {k: bool(np.isfinite(v) and (v > 0.1 if k in ("wrong_sign", "missing_2pi")
                                         else v <= 1e-3)) for k, v in errors.items()}
    return native, clebsch, errors, checks



def field_check(data, surface, resolution):
    """Check independent geometry and flux/lambda field against the current sampler."""
    from fusion_baselines.vmec_trace import _fourier, _interpolate

    raw = wout_target.sample(data, surface, resolution)
    full = np.linspace(0, 1, 401)
    half = (full[:-1]+full[1:])/2
    m, n, mn, nn = (data[k] for k in ('xm', 'xn', 'xm_nyq', 'xn_nyq'))
    theta, phi = raw['theta'], raw['phi']

    def radial(key, half_mesh=True):
        return _interpolate(half if half_mesh else full,
                            data[key][1:] if half_mesh else data[key], surface)

    def project(coefficients, sine=False, nyquist=False):
        return _fourier(theta, phi, mn if nyquist else m, nn if nyquist else n,
                        coefficients, sine=sine)

    r, z, lam = radial('rmnc', False), radial('zmns', False), radial('lmns')
    radius, height = project(r), project(z, True)
    rt, rp = project(-m*r, True), project(n*r, True)
    zt, zp = project(m*z), project(-n*z)
    et = np.stack((rt*np.cos(phi), rt*np.sin(phi), zt), axis=-1)
    ep = np.stack((rp*np.cos(phi)-radius*np.sin(phi),
                   rp*np.sin(phi)+radius*np.cos(phi), zp), axis=-1)
    geometry_errors = {}
    for key, expected in (('radius', radius), ('height', height), ('et', et), ('ep', ep)):
        error = float(np.max(abs(raw[key]-expected))/max(1., float(np.max(abs(expected)))))
        check.need(error <= 1e-12, f'independent geometry disagrees: {key}')
        geometry_errors[key] = error
    g, mod_b = (project(radial(key), nyquist=True) for key in ('gmnc', 'bmnc'))
    check.need(np.all(radius > 0) and np.all(g < 0), 'positive R and negative Jacobian required')
    native, clebsch, errors, checks = compare_fields(
        -float(data['phi'][-1])/(2*np.pi), g, raw['bt'], raw['bp'],
        project(m*lam), project(-n*lam), float(radial('iotas')), et, ep, mod_b)
    check.need(all(checks.values()), f'independent field checks failed: {errors}')
    check.need(np.max(abs(raw['native']-native)) <= 1e-12,
               'Cartesian sampler differs from independent geometry')
    return raw, dict(s=surface, n=resolution, errors=errors, checks=checks,
                     geometry_errors=geometry_errors,
                     min_jacobian=float(g.min()), max_jacobian=float(g.max()))


def intake(input_path, wout, proposal, expected_wout_sha256, guard=lambda: None):
    """Caller must separately bind a trusted solver run to this explicit Wout hash.

    Never registers the proposal as reference401 or changes a fitter/checker gate.
    Failed intake raises and supplies no target arrays to a prospective fitter.
    """
    import netCDF4

    sources = {}
    guard()
    document, original = registered_input(input_path, proposal, sources)
    sizes = size_check(document, original, guard)
    path = check.bind(wout, expected_wout_sha256, sources)
    guard()
    with netCDF4.Dataset(path) as dataset:
        data, state = validate_equilibrium(dataset, document)
    guard()
    check.need(abs(float(data['volume_p'])/sizes['proposal_m3'][-1]-1) <= 1e-6,
               'Wout volume differs from independent boundary volume')
    rows, reports = [], []
    for surface in SURFACES:
        for resolution in GRIDS:
            guard()
            raw, report = field_check(data, surface, resolution)
            reports.append(report)
            if resolution == 64:
                rows.append(dict(s=surface, n=64, arrays=raw))
            guard()
    targets = {n: archived_target(rows, n) for n in (32, 64)}
    measured = targets[64]['B2_scale']
    target_id = proposal_id(proposal)
    for target in targets.values():
        target.update(B2_scale=check.B2, target_id=target_id)
    guard()
    check.need(all(check.digest(p) == sha for p, sha in sources.items()),
               'intake input changed during validation')
    guard()  # Final identity hashing also consumes the caller's budget.
    report = dict(target_id=target_id, input_sha256=INPUT_HASHES[proposal],
                  wout_sha256=expected_wout_sha256, size=sizes, equilibrium=state,
                  fields=reports, B2_scale=check.B2, measured_B2=measured,
                  target_flux=check.TARGET_FLUX, numerical_consistency_pass=True,
                  solver_provenance_verified=False, full_joint_execution_enabled=False,
                  physical_admission=False, dense_identity_verified=False)
    return document, targets, sources, report
