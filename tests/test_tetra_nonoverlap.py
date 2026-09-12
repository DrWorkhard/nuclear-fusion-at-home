import numpy as np
import pytest

from fusion_baselines.tetra_nonoverlap import interior_witness, separation_witness

TET = np.vstack((np.zeros(3), np.eye(3)))


def test_disjoint_tetrahedra_have_recheckable_separator():
    b = TET + [2, 0, 0]
    result = separation_witness(TET, b)
    assert result["status"] == "separated"
    axis, origin = np.array(result["axis"]), np.array(result["origin"])
    gap = min(np.dot(p - origin, axis) for p in b) - max(
        np.dot(p - origin, axis) for p in TET)
    assert gap == pytest.approx(result["raw_projection_gap"])
    assert result["separation_lower"] > 0.9
    assert interior_witness(TET, b)["status"] == "unresolved"


def test_aabb_overlap_does_not_imply_tetrahedron_overlap():
    b = TET + [0.4, 0.4, 0.4]
    assert np.all(b.min(axis=0) < TET.max(axis=0))
    assert separation_witness(TET, b)["status"] == "separated"


@pytest.mark.parametrize("b", [TET + 0.1, 0.1 * TET + 0.2])
def test_overlap_and_containment_have_independent_interior_witnesses(b):
    assert separation_witness(TET, b)["status"] == "unresolved"
    result = interior_witness(TET, b)
    assert result["status"] == "positive_interior_witness"
    assert np.min(result["independently_solved_weights"]) > 1e-3


def test_face_contact_is_not_promoted_to_positive_overlap_or_separation():
    b = TET.copy()
    b[3, 2] *= -1
    assert separation_witness(TET, b)["status"] == "unresolved"
    assert interior_witness(TET, b)["status"] == "unresolved"


def test_rigid_motion_and_vertex_order_do_not_change_classification():
    q, _ = np.linalg.qr(np.random.default_rng(71).normal(size=(3, 3)))
    a = TET @ q + [301, -200, 50]
    b = (TET + [0.4, 0.4, 0.4]) @ q + [301, -200, 50]
    assert separation_witness(a[[2, 0, 3, 1]], b[[3, 2, 1, 0]])["status"] == "separated"


@pytest.mark.parametrize("bad", [np.zeros((4, 3)), np.full((4, 3), np.nan), np.zeros((3, 3))])
def test_invalid_and_degenerate_data_rejected(bad):
    for check in (interior_witness, separation_witness):
        with pytest.raises(ValueError):
            check(TET, bad)


def test_axis_and_lp_methods_agree_on_fixed_random_controls():
    rng = np.random.default_rng(624)
    separated = overlapping = 0
    for _ in range(32):
        a = rng.normal(size=(4, 3))
        b = rng.normal(size=(4, 3)) + rng.normal(size=3)
        sat, lp = separation_witness(a, b), interior_witness(a, b)
        assert lp["solver_success"]
        if lp["lp_margin"] < -1e-7:
            assert sat["status"] == "separated"
            separated += 1
        elif lp["lp_margin"] > 1e-7:
            assert sat["status"] == "unresolved"
            assert lp["status"] == "positive_interior_witness"
            overlapping += 1
        else:
            pytest.fail("fixed control unexpectedly ambiguous; keep it unresolved")
    assert separated > 0 and overlapping > 0
