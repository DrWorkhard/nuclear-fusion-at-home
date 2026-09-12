import copy
import gzip
import json

import numpy as np
import pytest

import fusion_baselines.mesh_nonlocal_scan as producer
from fusion_baselines.mesh_nonlocal_audit import audit_scan
from fusion_baselines.mesh_nonlocal_scan import scan

TET = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])


def test_complete_separated_excludes_all_pairs_by_boxes(tmp_path):
    points = np.vstack((TET, TET+3))
    r = scan(points, np.arange(8).reshape(2, 4), np.array([1, 2]), tmp_path / "scan")
    assert r["complete"] and r["nonlocal_screen_pass"]
    assert r["sat_calls"] == r["processed_candidates"] == 0
    assert r["broad_phase"]["box_separated_pairs"] == 1
    assert audit_scan(points, np.arange(8).reshape(2, 4), np.array([1, 2]), r)["all_pass"]


def test_overlap_contact_and_shared_vertex_are_not_conflated(tmp_path):
    cells = np.arange(8).reshape(2, 4)
    for name, delta in (("overlap", [.1, .1, .1]), ("contact", [1, 0, 0])):
        r = scan(np.vstack((TET, TET+delta)), cells, np.array([1, 2]), tmp_path / name)
        assert r["complete"] and not r["nonlocal_screen_pass"] and r["lp_calls"] == 1
        assert r["positive_interior_pairs"] == (name == "overlap")
        assert r["unresolved_pairs"] == (name == "contact")
        with gzip.open(r["witnesses"]["path"], "rt") as stream:
            assert json.loads(stream.readline())["pair"] == [0, 1]
        a = audit_scan(np.vstack((TET, TET+delta)), cells, np.array([1, 2]), r)
        assert a["all_pass"] and not a["nonlocal_screen_pass"]
    r = scan(TET, np.array([[0, 1, 2, 3], [3, 2, 1, 0]]), np.array([1, 1]),
             tmp_path / "neighbor")
    assert r["complete"] and r["shared_vertex_pairs"] == 1 and r["sat_calls"] == 0
    assert r["nonlocal_screen_pass"]  # Neighbor pairs are explicitly outside this narrow scope.
    assert audit_scan(TET, np.array([[0, 1, 2, 3], [3, 2, 1, 0]]), np.array([1, 1]), r)[
        "nonlocal_screen_pass"]


def test_pair_cap_preserves_partial_witnesses_and_never_passes(tmp_path):
    points = np.vstack((TET, TET+.1, TET+.2))
    r = scan(points, np.arange(12).reshape(3, 4), np.array([1, 2, 3]), tmp_path / "cap",
             max_sat_pairs=1)
    assert r["status"] == "pair_cap" and not r["complete"] and not r["nonlocal_screen_pass"]
    assert r["sat_calls"] == r["processed_candidates"] == 1
    assert r["broad_phase"]["candidates_delivered"] == 3
    with gzip.open(r["witnesses"]["path"], "rt") as stream:
        assert len(stream.readlines()) == 1
    audit = audit_scan(points, np.arange(12).reshape(3, 4), np.array([1, 2, 3]), r)
    assert audit["all_pass"] and not audit["complete"] and not audit["nonlocal_screen_pass"]


def test_clock_cap_and_explicit_narrow_failure_are_retained(tmp_path, monkeypatch):
    points, cells, tags = np.vstack((TET, TET+.1)), np.arange(8).reshape(2, 4), np.array([1, 2])
    with monkeypatch.context() as local:
        ticks = iter(range(100))
        local.setattr(producer.time, "monotonic", lambda: next(ticks))
        r = scan(points, cells, tags, tmp_path / "clock", max_seconds=.1)
    assert r["status"] == "time_cap" and not r["complete"]
    assert audit_scan(points, cells, tags, r)["all_pass"]
    def failure(*args):
        raise ValueError("injected narrow-phase failure")
    monkeypatch.setattr(producer, "separation_witness", failure)
    r = scan(points, cells, tags, tmp_path / "failure")
    assert r["status"] == "error" and r["narrow_errors"] == r["sat_calls"] == 1
    a = audit_scan(points, cells, tags, r)
    assert a["all_pass"] and not a["nonlocal_screen_pass"]


def test_changed_accounting_and_false_admission_are_rejected(tmp_path):
    points, cells, tags = np.vstack((TET, TET+.1)), np.arange(8).reshape(2, 4), np.array([1, 2])
    r = scan(points, cells, tags, tmp_path / "scan")
    for key, value in (("nonlocal_screen_pass", True), ("positive_interior_pairs", 0),
                       ("processed_candidates", 0)):
        changed = copy.deepcopy(r)
        changed[key] = value
        with pytest.raises(ValueError):
            audit_scan(points, cells, tags, changed)
