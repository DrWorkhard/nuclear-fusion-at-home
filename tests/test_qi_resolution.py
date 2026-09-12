import copy

import f90nml
import pytest

from fusion_baselines.qi_resolution import (
    MATRIX,
    author_input_checks,
    check_effective,
    effective_input,
    mode_map,
)


@pytest.mark.parametrize("ns,angular", MATRIX)
def test_frozen_controls_preserve_physics(ns, angular):
    original = dict(mpol=5, ntor=10, rbc=[dict(m=0, n=0, value=1)], phiedge=0.03)
    before = copy.deepcopy(original)
    result = effective_input(original, ns, angular)
    assert original == before
    assert result["ns_array"][-1] == ns
    assert result["ntheta"] == 16 * angular
    assert result["nzeta"] == 24 * angular
    assert check_effective(original, result, ns, angular)
    result["phiedge"] *= 2
    assert not check_effective(original, result, ns, angular)


def test_unregistered_controls_rejected():
    with pytest.raises(ValueError):
        effective_input({}, 801, 1)


def test_independent_author_mapping_handles_negative_n_and_scalar_array():
    nml = f90nml.reads('&indata nfp=2 ac=0 rbc(-1,0)=0.2 rbc(0,0)=1 zbs(0,1)=0.3 /')[
        "indata"]
    converted = dict(nfp=2, ac=[0], rbc=[dict(m=0, n=-1, value=0.2),
                                       dict(m=0, n=0, value=1)],
                     zbs=[dict(m=1, n=0, value=0.3)])
    assert all(author_input_checks(nml, converted).values())
    converted["rbc"][0]["n"] = 1
    assert not author_input_checks(nml, converted)["rbc"]


def test_duplicate_mode_rejected():
    with pytest.raises(ValueError):
        mode_map([dict(m=1, n=2, value=1), dict(m=1, n=2, value=2)])


def test_missing_author_field_rejected():
    with pytest.raises(ValueError, match="silently dropped"):
        author_input_checks(f90nml.reads('&indata phiedge=0.03 /')["indata"], {})


def test_nonfinite_mode_rejected():
    with pytest.raises(ValueError):
        mode_map([dict(m=0, n=0, value=float("nan"))])
