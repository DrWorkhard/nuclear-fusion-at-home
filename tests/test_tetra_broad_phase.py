from itertools import combinations

import numpy as np
import pytest

from fusion_baselines.tetra_broad_phase import TetraBroadPhase


def all_pairs(points, cells, padding):
    result = set()
    for i, j in combinations(range(len(cells)), 2):
        a, b = points[cells[i]], points[cells[j]]
        gap = max(float((a.min(axis=0) - b.max(axis=0)).max()),
                  float((b.min(axis=0) - a.max(axis=0)).max()))
        if gap <= padding:
            result.add((i, j))
    return result


@pytest.mark.parametrize("leaf_size", [1, 4, 16, 128])
def test_complete_hierarchy_matches_independent_exhaustive_pairs(leaf_size):
    rng = np.random.default_rng(325)
    count = 96
    points = (rng.normal(size=(count, 4, 3)) * 0.25
              + rng.normal(size=(count, 1, 3))).reshape(-1, 3)
    cells = np.arange(len(points)).reshape(-1, 4)
    tree = TetraBroadPhase(points, cells, leaf_size=leaf_size)
    batches = list(tree.candidates())
    pairs = np.vstack(batches)
    assert {tuple(row) for row in pairs} == all_pairs(points, cells, tree.padding)
    assert len(pairs) == len(np.unique(pairs, axis=0))
    assert tree.finished and tree.pairs_accounted == count * (count - 1) // 2
    assert tree.candidate_count + tree.box_separated_pairs == tree.pairs_accounted
    assert sorted(tree.indices.tolist()) == list(range(count))
    for node in tree.nodes:
        geometry = points[cells[tree.indices[node["lo"]:node["hi"]]]]
        np.testing.assert_array_equal(node["lower"], geometry.min(axis=(0, 1)))
        np.testing.assert_array_equal(node["upper"], geometry.max(axis=(0, 1)))
    with pytest.raises(ValueError, match="one traversal"):
        list(tree.candidates())


def test_touching_boxes_and_duplicate_geometry_are_not_pruned():
    tet = np.vstack((np.zeros(3), np.eye(3)))
    points = np.vstack((tet, tet, tet + [1, 0, 0]))
    tree = TetraBroadPhase(points, np.arange(12).reshape(3, 4), leaf_size=1)
    assert {tuple(row) for row in np.vstack(list(tree.candidates()))} == {(0, 1), (0, 2), (1, 2)}


def test_partial_iteration_cannot_claim_complete_coverage():
    points = np.zeros((40, 3))
    tree = TetraBroadPhase(points, np.arange(40).reshape(-1, 4), leaf_size=2)
    stream = tree.candidates()
    next(stream)
    assert tree.started and not tree.finished


def test_single_tetrahedron_has_no_pairs():
    tree = TetraBroadPhase(np.vstack((np.zeros(3), np.eye(3))), np.array([[0, 1, 2, 3]]))
    assert list(tree.candidates()) == []
    assert tree.finished and tree.pairs_accounted == 0


@pytest.mark.parametrize("bad", [np.array([[0, 1, 2, 9]]), np.zeros((1, 4), dtype=float)])
def test_invalid_connectivity_rejected(bad):
    with pytest.raises(ValueError):
        TetraBroadPhase(np.zeros((4, 3)), bad)
