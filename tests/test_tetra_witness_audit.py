import copy

import numpy as np
import pytest

from fusion_baselines.tetra_nonoverlap import interior_witness, separation_witness
from fusion_baselines.tetra_witness_audit import audit_interior, audit_separation

TET = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])


def test_separated_positive_interior_and_contact_remain_distinct():
    for delta in (np.array([2, 0, 0]), np.array([.1, .1, .1]), np.array([1, 0, 0])):
        b = TET+delta
        witness = separation_witness(TET, b)
        result = audit_separation(TET, b, witness)
        assert result["valid"]
        assert result["separation_verified"] == bool(delta[0] == 2)
        interior = audit_interior(TET, b, interior_witness(TET, b))
        assert interior["valid"]
        assert interior["positive_interior_verified"] == bool(delta[0] == .1)


@pytest.mark.parametrize("mutation", ["origin", "axis", "gap", "pad", "lower"])
def test_false_separation_certificate_rejected(mutation):
    b = TET+2
    w = separation_witness(TET, b)
    if mutation == "origin":
        w["origin"][0] += 1
    elif mutation == "axis":
        w["axis"] = [1, 1, 1]
    elif mutation == "gap":
        w["raw_projection_gap"] += .1
    elif mutation == "pad":
        w["safety_pad"] = 0
    else:
        w["separation_lower"] += .1
    try:
        result = audit_separation(TET, b, w)
    except ValueError:
        return
    assert not result["valid"]


def test_false_interior_point_and_unverified_solver_failure_do_not_admit():
    b = TET+.1
    w = interior_witness(TET, b)
    wrong = copy.deepcopy(w)
    wrong["point_relative_to_origin"][0] += 1
    r = audit_interior(TET, b, wrong)
    assert not r["valid"] and not r["positive_interior_verified"]
    failure = dict(status="unresolved", origin=TET[0].tolist(), barycentric_margin=1e-10,
                   solver_success=False)
    assert audit_interior(TET, b, failure) == dict(valid=True, positive_interior_verified=False)
