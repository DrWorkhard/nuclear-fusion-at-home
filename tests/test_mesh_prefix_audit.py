import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import run_mesh_fine_completion as runner

from fusion_baselines.mesh_nonlocal_scan import reference, scan
from fusion_baselines.mesh_prefix_audit import audit_prefix


def pair(tmp_path):
    tetra = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
    points = np.vstack([tetra+.1*i for i in range(4)])
    cells = np.arange(16).reshape(4, 4)
    tags = np.arange(1, 5)
    old = scan(points, cells, tags, tmp_path/"old", max_sat_pairs=2)
    new = scan(points, cells, tags, tmp_path/"new", max_sat_pairs=20)
    return old, new


def test_exact_spatial_prefix_is_not_physical_admission(tmp_path):
    old, new = pair(tmp_path)
    assert old["status"] == "pair_cap" and new["complete"]
    result = audit_prefix(old, new)
    assert result["all_pass"] and result["old_witnesses_checked"] == 2
    assert not new["nonlocal_screen_pass"]  # overlapping toy tetrahedra, correctly negative


def test_changed_witness_or_incomplete_new_prefix_rejected(tmp_path):
    old, new = pair(tmp_path)
    path = Path(new["witnesses"]["path"])
    with gzip.open(path, "rt") as stream:
        lines = list(stream)
    with gzip.open(path, "wt") as stream:
        stream.writelines(lines[1:])
    with pytest.raises(ValueError, match="hash"):
        audit_prefix(old, new)
    new["witnesses"] = reference(path)
    assert not audit_prefix(old, new)["all_pass"]


def test_changed_partition_or_insufficient_work_rejected(tmp_path):
    old, new = pair(tmp_path)
    path = Path(new["partition"]["path"])
    with gzip.open(path, "rt") as stream:
        data = json.load(stream)
    data["padding"] *= 2
    with gzip.open(path, "wt") as stream:
        json.dump(data, stream)
    new["partition"] = reference(path)
    result = audit_prefix(old, new)
    assert not result["all_pass"] and not result["checks"]["padding"]
    new["sat_calls"] = 1
    assert not audit_prefix(old, new)["checks"]["new_work_covers_prefix"]


def test_closed_predecessors_reject_changed_case_or_open_qi(tmp_path, monkeypatch):
    paths = [tmp_path/p for p in ("evidence/mesh-nonlocal-v2/summary.json",
                                  "evidence/mesh-nonlocal-v2-audit.json",
                                  "evidence/qi-pest-fidelity-v1.json",
                                  "evidence/qi-pest-fidelity-v1-audit.json")]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    old_scan, worker = tmp_path/"old-scan.json", tmp_path/"worker.json"
    old_scan.write_text(json.dumps(dict(status="pair_cap", sat_calls=2000000)))
    worker.write_text(json.dumps(dict(scan=reference(old_scan))))
    mesh = dict(status="completed", all_six_terminal=True,
                meshes=[dict(nonlocal_screen_pass=(i < 5), complete_scan=(i < 5),
                             worker=reference(worker)) for i in range(6)])
    paths[0].write_text(json.dumps(mesh))
    paths[1].write_text(json.dumps(dict(status="completed", all_pass=True,
                                       study=reference(paths[0]))))
    paths[2].write_text(json.dumps(dict(status="completed")))
    paths[3].write_text(json.dumps(dict(status="completed", all_pass=True,
                                       source=reference(paths[2]))))
    commits = []
    monkeypatch.setattr(runner, "require_committed", lambda root, p: commits.append(p))
    assert len(runner.predecessors(tmp_path)[0]) == len(commits) == 4
    mesh["meshes"][0]["complete_scan"] = False
    paths[0].write_text(json.dumps(mesh))
    paths[1].write_text(json.dumps(dict(status="completed", all_pass=True,
                                       study=reference(paths[0]))))
    with pytest.raises(ValueError, match="original finest"):
        runner.predecessors(tmp_path)
    paths[2].write_text(json.dumps(dict(status="running")))
    with pytest.raises(ValueError, match="closed"):
        runner.predecessors(tmp_path)
