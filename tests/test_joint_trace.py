"""Frozen-current direct tracing, field controls and retained-path provenance."""
import time

import numpy as np
import pytest
import test_joint_diagnostics as fixtures

from fusion_baselines import joint_coil as joint
from fusion_baselines import realized_field as rf


@pytest.fixture
def admitted(tmp_path, monkeypatch):
    a = fixtures.admitted.__wrapped__(tmp_path, monkeypatch)
    a.record = joint.fit.Recorder(tmp_path/'trace', time.monotonic()+60)
    return a


def wire(monkeypatch, admitted, fault=None):
    from simsopt import field, geo

    a = admitted
    calls = []
    class Field:
        def set_points(self, points):
            assert points.shape == (64, 3)
        def B(self):
            return np.ones((64, 3))*(2 if fault == 'field' else 1)
    monkeypatch.setattr(field, 'BiotSavart', lambda _: Field())
    target = type('Target', (), {'sha256': 'c'*64 if fault == 'wout' else
                                 a.binding['wout_sha256']})()
    monkeypatch.setattr(rf.Target, 'from_wout', lambda *args: target)
    monkeypatch.setattr(rf, 'sample_points', lambda *args: np.zeros((64, 3)))
    physical = joint.check.independent.physical_curves(a.snapshot, 512)
    monkeypatch.setattr(joint.check, '_native_coils', lambda *args:
                        ([], physical, dict(position=0., tangent=0.)))
    monkeypatch.setattr(joint.check.independent, 'filament_field_and_potential', lambda *args:
                        (np.ones((64, 3)), np.zeros((64, 3))))
    monkeypatch.setattr(geo.SurfaceRZFourier, 'from_wout', lambda *args, **kwargs: None)
    def trace(native, target, surface, **kwargs):
        calls.append(kwargs)
        assert kwargs == dict(transits=200, tol=1e-10, s_values=rf.S_VALUES, keep_paths=True)
        if fault == 'receipt':
            (a.folder/'parent.json').write_text('changed', encoding='utf-8')
        count = 9 if fault == 'missing' else 10
        lines = [dict(s=s, R0=1., transits=200., left_target=False,
                      termination='requested_transits', iota_traced=-.6, iota_target=-.6)
                 for s in rf.S_VALUES[:count]]
        if fault == 'short':
            lines[-1].update(transits=199., termination='integration_limit')
        return (lines, [np.zeros((3, 5)) for _ in lines],
                [np.zeros((4, 4)) for _ in lines])
    monkeypatch.setattr(rf, 'trace', trace)
    return calls


@pytest.mark.parametrize('fault', [None, 'short'])
def test_direct_route_keeps_fixed_protocol_and_all_paths(admitted, monkeypatch, fault):
    calls = wire(monkeypatch, admitted, fault)
    a = admitted
    result = joint.direct_trace(a.snapshot, a.folder, a.parent, a.record)
    assert len(calls) == 1 and result['completed']
    assert result['frozen_current'] and result['current_A'] == 1e5*a.snapshot['scale']
    assert not result['physical_admission']
    assert result['summary']['all_confined_and_iota_matching'] == (fault is None)
    assert len(result['arrays_sha256']) == 10
    for name, sha in result['arrays_sha256'].items():
        assert joint.check.digest(a.record.output/name) == sha
        with np.load(a.record.output/name) as arrays:
            assert arrays['path'].shape == (4, 4) and arrays['hits'].shape == (3, 5)


@pytest.mark.parametrize('fault', ['wout', 'field', 'receipt', 'missing'])
def test_wrong_field_target_receipt_or_missing_line_cannot_pass(admitted, monkeypatch, fault):
    calls = wire(monkeypatch, admitted, fault)
    a = admitted
    with pytest.raises(ValueError):
        joint.direct_trace(a.snapshot, a.folder, a.parent, a.record)
    assert len(calls) == (0 if fault in ('wout', 'field') else 1)


def test_bad_snapshot_cannot_reach_direct_field(admitted, monkeypatch):
    wire(monkeypatch, admitted)
    a = admitted
    a.snapshot['B2_scale'] *= 1.01
    with pytest.raises(ValueError, match='reference B2'):
        joint.direct_trace(a.snapshot, a.folder, a.parent, a.record)
    assert not (a.record.output/'trace-kernel.npz').exists()
