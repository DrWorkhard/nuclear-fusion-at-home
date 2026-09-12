import copy

import numpy as np
import pytest

from fusion_baselines.tetra_broad_phase import TetraBroadPhase
from fusion_baselines.tetra_partition_audit import audit_partition


def fixture():
    rng = np.random.default_rng(328)
    points = rng.normal(size=(80, 4, 3)) * .2 + rng.normal(size=(80, 1, 3))
    points, cells = points.reshape(-1, 3), np.arange(320).reshape(-1, 4)
    tree = TetraBroadPhase(points, cells)
    candidates = list(tree.candidates())
    return points, cells, tree, candidates


def test_independent_frontier_partition_and_original_vertex_leaf_reconstruction():
    points, cells, tree, expected = fixture()
    replay = []
    r = audit_partition(points, cells, tree.indices, tree.nodes, tree.events, tree.padding,
                         visit=lambda pairs: replay.append(pairs))
    assert r["complete"] and r["covered_pairs"] == 80*79//2
    assert r["candidate_count"] == tree.candidate_count
    assert np.array_equal(np.concatenate(replay), np.concatenate(expected))


def test_truncated_events_remain_valid_but_incomplete():
    points, cells, tree, _ = fixture()
    r = audit_partition(points, cells, tree.indices, tree.nodes, tree.events[:10], tree.padding)
    assert not r["complete"] and r["remaining_pairs"] > 0
    assert r["covered_pairs"]+r["remaining_pairs"] == r["total_pairs"]


@pytest.mark.parametrize("mutation", ["box", "span", "index", "padding", "duplicate", "count"])
def test_invalid_certificate_mutations_rejected(mutation):
    points, cells, tree, _ = fixture()
    nodes, events, indices, padding = copy.deepcopy(tree.nodes), copy.deepcopy(tree.events), (
        tree.indices.copy()), tree.padding
    if mutation == "box":
        nodes[0]["lower"][0] += .01
    elif mutation == "span":
        nodes[1]["lo"] += 1
    elif mutation == "index":
        indices[0] = indices[1]
    elif mutation == "padding":
        padding *= 2
    elif mutation == "duplicate":
        events.insert(1, events[0])
    else:
        events[-1]["pairs"] += 1
    with pytest.raises(ValueError):
        audit_partition(points, cells, indices, nodes, events, padding)
