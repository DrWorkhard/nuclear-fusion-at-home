import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mesh_nonlocal_inputs as inputs
import run_mesh_nonlocal as runner
from mesh_nonlocal_inputs import LEVELS, frozen_inputs, load_mesh

from fusion_baselines.mesh_nonlocal_scan import reference


def fixture(root):
    (root / "evidence").mkdir()
    rows, items = [], []
    for i, h in enumerate(LEVELS):
        mesh = root / f"mesh-{i}"
        mesh.write_text(f"test bytes {i}")
        ref = reference(mesh)
        rows.append(dict(mesh=ref, target_h_m=h, pass_=True, checks={"test": True}))
        rows[-1]["pass"] = rows[-1].pop("pass_")
        items.append(dict(**ref, target_h_m=h))
    manifests = []
    for i, group in enumerate((items[:4], items[4:])):
        path = root / f"manifest-{i}.json"
        path.write_text(json.dumps(dict(meshes=group)))
        manifests.append(reference(path))
    code = root / "old_code.py"
    code.write_text("# original test source\n")
    result = dict(status="completed", all_pass=True, meshes=rows, manifests=manifests,
                  code=[reference(code)], repository=dict(path=str(root), commit="9ee1796"))
    path = root / "evidence/mesh-integrity-2026-09-09.json"
    path.write_text(json.dumps(result))
    return path, result


def test_all_six_sources_and_identity_mismatch_rejected(tmp_path):
    path, source = fixture(tmp_path)
    assert frozen_inputs(tmp_path)[1] == source
    changed = copy.deepcopy(source)
    changed["meshes"][0]["target_h_m"] = .1
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError):
        frozen_inputs(tmp_path)
    path.write_text(json.dumps(source))
    Path(source["meshes"][1]["mesh"]["path"]).write_text("corrupted source")
    with pytest.raises(ValueError, match="binding"):
        frozen_inputs(tmp_path)


def test_missing_level_cannot_be_hidden(tmp_path):
    path, source = fixture(tmp_path)
    source["meshes"].pop()
    path.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="all six"):
        frozen_inputs(tmp_path)


def test_historical_code_resolution_is_exact_and_explicit(tmp_path, monkeypatch):
    path, source = fixture(tmp_path)
    original = Path(source["code"][0]["path"])
    original.write_text("# changed current source\n")
    with pytest.raises(ValueError, match="unresolved historical"):
        frozen_inputs(tmp_path)
    calls = []

    def historical(ref, root, recorded, revision):
        calls.append((ref, root, recorded, revision))
        return dict(**ref, status="historical_git", source_revision=revision,
                    git_path="old_code.py")

    monkeypatch.setattr(inputs, "resolve_reference", historical)
    assert frozen_inputs(tmp_path)[1] == source
    binding = inputs.source_code_bindings(tmp_path, source)
    assert binding[0]["sha256"] == source["code"][0]["sha256"]
    assert all(c[2:] == (str(tmp_path), "9ee1796") for c in calls)
    Path(source["meshes"][0]["mesh"]["path"]).write_text("changed physical file")
    before = len(calls)
    with pytest.raises(ValueError, match="binding"):
        frozen_inputs(tmp_path)
    assert len(calls) == before  # no historical fallback for a corrupt physical mesh


def test_empty_or_unresolved_source_codes_never_pass(tmp_path, monkeypatch):
    path, source = fixture(tmp_path)
    source["code"] = []
    path.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="unresolved historical"):
        frozen_inputs(tmp_path)


def test_actual_small_mesh_reader_requires_four_tags(tmp_path):
    import meshio

    points = np.array([[0., 0., 0.], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
    cells = np.tile(np.arange(4), (4, 1))
    path = tmp_path / "test.msh"
    meshio.write(path, meshio.Mesh(points, [("tetra", cells)], cell_data={
        "gmsh:physical": [np.array([1, 2, 3, 4])], "gmsh:geometrical": [np.ones(4, dtype=int)]}),
        file_format="gmsh22")
    xyz, actual, tags = load_mesh(reference(path))
    assert np.array_equal(xyz, points) and np.array_equal(actual, cells)
    assert tags.tolist() == [1, 2, 3, 4]
    meshio.write(path, meshio.Mesh(points, [("tetra", cells)], cell_data={
        "gmsh:physical": [np.ones(4, dtype=int)], "gmsh:geometrical": [np.ones(4, dtype=int)]}),
        file_format="gmsh22")
    with pytest.raises(ValueError, match="four original"):
        load_mesh(reference(path))


def test_physical_study_predecessor_requires_closed_all_four_holdouts(tmp_path, monkeypatch):
    paths = [tmp_path / p for p in (
        "evidence/slsqp-composite-v1/summary.json", "evidence/slsqp-composite-v1-audit.json",
        "evidence/slsqp-composite-v1-validation/summary.json")]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    paths[0].write_text(json.dumps(dict(status="completed", qualification_pass=True,
                                       arms=[{}, {}])))
    paths[1].write_text(json.dumps(dict(all_pass=True, study=reference(paths[0]))))
    holdout = dict(status="completed", all_four_phases_completed=True, study=reference(paths[0]),
                   audit=reference(paths[1]), steps=[])
    for name in ("holdout", "curvature", "clearance", "native"):
        path = tmp_path / f"{name}.json"
        path.write_text("{}")
        holdout["steps"].append(dict(name=name, result=reference(path)))
    paths[2].write_text(json.dumps(holdout))
    checked = []
    monkeypatch.setattr(runner, "require_committed", lambda root, path: checked.append(path))
    assert len(runner.closed_predecessor(tmp_path)) == len(checked) == 3
    holdout["steps"].pop()
    paths[2].write_text(json.dumps(holdout))
    with pytest.raises(ValueError, match="four original"):
        runner.closed_predecessor(tmp_path)
    holdout["all_four_phases_completed"] = False
    paths[2].write_text(json.dumps(holdout))
    with pytest.raises(ValueError, match="closed independently"):
        runner.closed_predecessor(tmp_path)
