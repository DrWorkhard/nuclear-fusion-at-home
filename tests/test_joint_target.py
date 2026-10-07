"""Registered-proposal, malformed-state and independent-field counterexamples."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines import joint_target as jt

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def original():
    return json.loads((ROOT/jt.check.TARGET).read_text())


def encode(path, document):
    path.write_text(json.dumps(document, allow_nan=False, indent=2, sort_keys=True)+'\n')
    return path


@pytest.mark.parametrize('proposal', ['control', 'plus', 'minus'])
def test_registered_inputs_preserve_reference_registry(tmp_path, original, proposal):
    data = copy.deepcopy(original)
    for row in data['rbc']:
        if (row['m'], row['n']) == (2, 1):
            row['value'] += jt.DELTAS[proposal]
    source = encode(tmp_path/'input.json', data)
    sources = {}
    actual, baseline = jt.registered_input(source, proposal, sources)
    assert actual == data and baseline == original
    assert jt.check.digest(source) == jt.INPUT_HASHES[proposal]
    assert set(jt.check.TARGETS) == {'reference401', 'selected401'}
    assert jt.check.target_spec('reference401')['B2'] == jt.check.B2
    with pytest.raises(ValueError, match='registered target'):
        jt.check.target_spec(f'issue37-joint-v1/{proposal}')


@pytest.mark.parametrize('fault', ['mode', 'other_mode', 'flux', 'resolution', 'id', 'bytes'])
def test_proposal_cannot_change_other_physics_or_settings(tmp_path, original, fault):
    data = copy.deepcopy(original)
    if fault == 'mode':
        next(r for r in data['rbc'] if (r['m'], r['n']) == (2, 1))['value'] += .002
    elif fault == 'other_mode':
        data['zbs'][0]['value'] += .001
    elif fault == 'flux':
        data['phiedge'] *= .9
    elif fault == 'resolution':
        data['ns_array'][-1] = 201
    source = encode(tmp_path/'input.json', data)
    if fault == 'bytes':
        source.write_text(source.read_text()+' ')
    with pytest.raises(ValueError):
        jt.registered_input(source, 'unknown' if fault == 'id' else 'plus', {})


def equilibrium_fixture(original):
    """Metadata/boundary fixture only; deliberately not an equilibrium certificate."""
    modes = [(0, n) for n in range(11)] + [(m, n) for m in range(1, 5)
                                                  for n in range(-10, 11)]
    nyquist = [(0, n) for n in range(25)] + [(m, n) for m in range(1, 17)
                                                     for n in range(-24, 25)]
    d = {k: np.array(v) for k, v in dict(
        nfp=2, ns=401, lasym__logical__=0, lfreeb__logical__=0, lrfp__logical__=0,
        mpol=5, ntor=10, ier_flag=0, signgs=-1, fsqr=1e-13, fsqz=1e-13,
        fsql=1e-13, ftolv=1e-12, ctor=0., volume_p=.19, mnmax=len(modes),
        mnmax_nyq=len(nyquist)).items()}
    d.update(xm=np.array([m for m, n in modes]), xn=np.array([2*n for m, n in modes]),
             xm_nyq=np.array([m for m, n in nyquist], dtype=float),
             xn_nyq=np.array([2*n for m, n in nyquist], dtype=float))
    for k in ('pres', 'presf', 'iotas'):
        d[k] = np.zeros(401)
    flux = original['phiedge']
    d['phi'] = np.linspace(0, flux, 401)
    d['phipf'] = np.full(401, flux)
    d['phips'] = np.r_[0., np.full(400, -flux/(2*np.pi))]
    for key, wkey in (('rbc', 'rmnc'), ('zbs', 'zmns')):
        coefficients = {(r['m'], r['n']): r['value'] for r in original[key]}
        d[wkey] = np.tile([coefficients.get(k, 0.) for k in modes], (401, 1))
    d['lmns'] = np.zeros((401, len(modes)))
    for key in ('gmnc', 'bmnc', 'bsupumnc', 'bsupvmnc'):
        d[key] = np.zeros((401, len(nyquist)))
    return d


def test_metadata_validation_does_not_claim_field_or_physical_validity(original):
    data, state = jt.validate_equilibrium(equilibrium_fixture(original), original)
    assert state['net_current_A'] == 0
    with pytest.raises(ValueError, match='Jacobian'):
        jt.field_check(data, .5, 64)


@pytest.mark.parametrize('fault', ['resolution', 'boundary', 'period', 'symmetry', 'free',
    'failure', 'residual', 'negative_residual', 'loose_ftol', 'pressure', 'current',
    'interior_flux', 'flux_sign', 'phips', 'jacobian_sign', 'duplicate_mode',
    'fractional_mode', 'missing_surface', 'wrong_width', 'nonfinite', 'scalar_shape'])
def test_wout_rejects_mixed_or_incomplete_state(original, fault):
    d = equilibrium_fixture(original)
    if fault == 'resolution':
        d['ns'][...] = 201
    elif fault == 'boundary':
        d['rmnc'][-1, 0] += 1e-4
    elif fault == 'period':
        d['nfp'][...] = 3
    elif fault == 'symmetry':
        d['lasym__logical__'][...] = 1
    elif fault == 'free':
        d['lfreeb__logical__'][...] = 1
    elif fault == 'failure':
        d['ier_flag'][...] = 1
    elif fault == 'residual':
        d['fsqr'][...] = 1e-8
    elif fault == 'negative_residual':
        d['fsqz'][...] = -1e-13
    elif fault == 'loose_ftol':
        d['ftolv'][...] = 1e-8
    elif fault == 'pressure':
        d['presf'][200] = 1e-3
    elif fault == 'current':
        d['ctor'][...] = 1.
    elif fault == 'interior_flux':
        d['phi'][20] += 1e-5
    elif fault == 'flux_sign':
        d['phi'] *= -1
    elif fault == 'phips':
        d['phips'][1:] *= -1
    elif fault == 'jacobian_sign':
        d['signgs'][...] = 1
    elif fault == 'duplicate_mode':
        d['xm_nyq'][1], d['xn_nyq'][1] = 0., 0.
    elif fault == 'fractional_mode':
        d['xn_nyq'][1] = .5
    elif fault == 'missing_surface':
        d['rmnc'] = d['rmnc'][:-1]
    elif fault == 'wrong_width':
        d['bmnc'] = d['bmnc'][:, :1]
    elif fault == 'nonfinite':
        d['bsupvmnc'][10, 0] = np.nan
    elif fault == 'scalar_shape':
        d['ns'] = np.array([401])
    with pytest.raises(ValueError):
        jt.validate_equilibrium(d, original)


def represented_torus():
    """Exact Fourier field-representation control, not a solved equilibrium."""
    d = dict(ns=np.array(401), nfp=np.array(2), lasym__logical__=np.array(0),
             xm=np.array([0., 1.]), xn=np.array([0., 0.]),
             xm_nyq=np.array([0., 1.]), xn_nyq=np.array([0., 0.]),
             phi=np.linspace(0, 2*np.pi, 401), iotas=np.zeros(401))
    for key, values in dict(rmnc=[3., .4], zmns=[0., .4], lmns=[0., 0.],
        gmnc=[-1., 0.], bmnc=[3., .4], bsupumnc=[0., 0.], bsupvmnc=[1., 0.]).items():
        d[key] = np.tile(values, (401, 1))
    return d


def test_independent_field_representations_and_sign_controls():
    data = represented_torus()
    raw, report = jt.field_check(data, .5, 64)
    assert all(report['checks'].values())
    assert report['errors']['cartesian'] < 1e-14
    assert report['errors']['wrong_sign'] == pytest.approx(2.)
    assert report['errors']['missing_2pi'] == pytest.approx(2*np.pi-1)
    np.testing.assert_allclose(np.linalg.norm(raw['native'], axis=-1), raw['radius'], atol=1e-14)


@pytest.mark.parametrize('fault', ['wrong_sign', 'missing_2pi', 'magnitude', 'lambda',
                                   'poloidal', 'positive_jacobian', 'sampler_geometry'])
def test_independent_field_check_rejects_plausible_corruptions(monkeypatch, fault):
    data = represented_torus()
    if fault == 'wrong_sign':
        data['bsupvmnc'] *= -1
    elif fault == 'missing_2pi':
        data['bsupvmnc'] *= 2*np.pi
    elif fault == 'magnitude':
        data['bmnc'] *= 1.01
    elif fault == 'lambda':
        data['lmns'][:, 1] = .1
    elif fault == 'poloidal':
        data['bsupumnc'][:, 0] = .1
    elif fault == 'positive_jacobian':
        data['gmnc'] *= -1
    elif fault == 'sampler_geometry':
        original_sample = jt.wout_target.sample

        def corrupt(*args):
            arrays = original_sample(*args)
            arrays['ep'] *= 2*np.pi
            return arrays
        monkeypatch.setattr(jt.wout_target, 'sample', corrupt)
    with pytest.raises(ValueError):
        jt.field_check(data, .5, 64)


def test_volume_normalization_and_size_rejection():
    torus = dict(lasym=False, nfp=2, mpol=2, ntor=0,
                 rbc=[dict(m=0, n=0, value=1.3), dict(m=1, n=0, value=.2)],
                 zbs=[dict(m=1, n=0, value=.15)])
    assert jt.volume(torus, 32) == pytest.approx(2*np.pi**2*1.3*.2*.15, rel=1e-14)
    inflated = copy.deepcopy(torus)
    inflated['rbc'][0]['value'] *= 1.01
    with pytest.raises(ValueError, match='volume limit'):
        jt.size_check(inflated, torus, lambda: None)


def test_intake_requires_explicit_wout_identity_and_obeys_caller_guard(tmp_path, monkeypatch):
    wrong = tmp_path/'wout.nc'
    wrong.write_bytes(b'not the registered Wout')
    monkeypatch.setattr(jt, 'size_check', lambda *args: {})
    with pytest.raises(ValueError, match='source identity changed'):
        jt.intake(ROOT/jt.check.TARGET, wrong, 'control', '0'*64)
    with pytest.raises(ValueError, match='SHA256'):
        jt.intake(ROOT/jt.check.TARGET, wrong, 'control', None)

    def expired():
        raise TimeoutError('caller deadline')
    with pytest.raises(TimeoutError, match='caller deadline'):
        jt.intake(ROOT/jt.check.TARGET, wrong, 'control', '0'*64, expired)


@pytest.mark.parametrize('family,axis', [('geometry', 'm'), ('geometry', 'n'),
                                        ('nyquist', 'm'), ('nyquist', 'n')])
def test_hidden_aliased_interior_modes_rejected(original, family, axis):
    data = equilibrium_fixture(original)
    mkey, nkey, countkey, keys = ('xm', 'xn', 'mnmax', ('rmnc', 'zmns', 'lmns')) if (
        family == 'geometry') else ('xm_nyq', 'xn_nyq', 'mnmax_nyq',
                                    ('gmnc', 'bmnc', 'bsupumnc', 'bsupvmnc'))
    data[mkey] = np.r_[data[mkey], 128 if axis == 'm' else 1]
    data[nkey] = np.r_[data[nkey], 256 if axis == 'n' else 0]
    data[countkey][...] += 1
    for key in keys:
        data[key] = np.column_stack((data[key], np.zeros(401)))
    # Boundary unchanged; a large interior harmonic aliases on both 64/128 grids.
    data[keys[1]][1:-1, -1] = .1
    with pytest.raises(ValueError, match='frozen Fourier mode table'):
        jt.validate_equilibrium(data, original)
