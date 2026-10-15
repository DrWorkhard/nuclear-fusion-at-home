"""Frozen non-registered target specifications (#115) never alias registered targets."""

import copy
import json
from pathlib import Path

import pytest

from fusion_baselines import coil_check as check

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def spec(tmp_path):
    source = tmp_path/'input.json'
    source.write_bytes((ROOT/check.TARGET).read_bytes())
    data = json.loads(source.read_text())
    value = dict(schema=check.SPEC_SCHEMA, target_id='new-plasma.v1',
                 input=dict(path=str(source), sha256=check.digest(source)),
                 wout=dict(sha256='a'*64, vmecpp='0.8.0'), B2=1.5, flux=-data['phiedge'],
                 seed=dict(snapshot_sha256='b'*64, current_A=1.0))
    before = dict(check.TARGETS)
    yield tmp_path, value
    check.TARGETS.clear()
    check.TARGETS.update(before)


def write(tmp_path, value, name='spec.json'):
    path = tmp_path/name
    path.write_text(json.dumps(value))
    return path


def test_spec_registers_distinct_label_and_keeps_registered_meaning(spec):
    tmp_path, value = spec
    registered = copy.deepcopy(check.TARGETS)
    label = check.load_target_spec(write(tmp_path, value))
    assert label == 'new-plasma.v1' and check.REGISTERED == ('reference401', 'selected401')
    entry = check.target_spec(label)
    assert entry['B2'] == 1.5 and entry['wout_sha256'] == 'a'*64 and 'spec_sha256' in entry
    assert {k: check.TARGETS[k] for k in registered} == registered
    assert check.load_target_spec(write(tmp_path, value, 'same.json')) == label


@pytest.mark.parametrize('fault', ['registered', 'label', 'schema', 'flux', 'B2', 'hash',
                                   'version', 'input'])
def test_spec_rejects_aliasing_or_unbound_identity(spec, fault):
    tmp_path, value = spec
    if fault == 'registered':
        value['target_id'] = 'selected401'
    elif fault == 'label':
        value['target_id'] = 'New Plasma'
    elif fault == 'schema':
        value['schema'] = 'coil-target-spec/v0'
    elif fault == 'flux':
        value['flux'] = -value['flux']
    elif fault == 'B2':
        value['B2'] = 0.
    elif fault == 'hash':
        value['wout']['sha256'] = 'A'*64
    elif fault == 'version':
        del value['wout']['vmecpp']
    else:
        value['input']['sha256'] = 'c'*64
    with pytest.raises((ValueError, KeyError)):
        check.load_target_spec(write(tmp_path, value))
    assert value['target_id'] not in check.TARGETS or fault == 'registered'


def test_conflicting_spec_for_same_label_rejected(spec):
    tmp_path, value = spec
    check.load_target_spec(write(tmp_path, value))
    value['B2'] = 1.25
    with pytest.raises(ValueError, match='conflicting'):
        check.load_target_spec(write(tmp_path, value, 'other.json'))


def test_spec_target_requires_its_frozen_wout(spec):
    tmp_path, value = spec
    label = check.load_target_spec(write(tmp_path, value))
    wrong = tmp_path/'wout.nc'
    wrong.write_bytes(b'not the frozen Wout')
    with pytest.raises(ValueError, match='source identity changed'):
        check.portable_intake(wrong, target_id=label)
