import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from test_qi_pest_fields import toy_file

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_qi_pest as auditor
import evaluate_qi_pest as evaluator
from qi_pest_inputs import SURFACES, matrix_rows, reference

from fusion_baselines.qi_field_grid import sample as old_sample
from fusion_baselines.qi_resolution import MATRIX


def matrix():
    ref = dict(path="/immutable/file", sha256="a"*64)
    inventory = dict(cases=[dict(case=f"c{i}", wout=ref) for i in range(4)])
    study, evaluation = dict(status="completed", cells=[]), dict(
        status="completed", cells=[], old_fields=[])
    zeros = dict(mod_b=0., et=0., ep=0., rz=0., iota=0.)
    for case in inventory["cases"]:
        for s in SURFACES:
            evaluation["old_fields"].append(dict(case=case["case"], surface=s,
                                                 wout=ref, arrays=ref))
        for ns, a in MATRIX:
            base = dict(case=case["case"], ns=ns, angular=a)
            study["cells"].append(dict(**base, numerically_converged=True, wout=ref,
                                       historical_wout=ref))
            evaluation["cells"].append(dict(**base, status="completed", volume_error=0.,
                grids=[dict(surface=s, resolution=n, arrays=ref, fidelity=zeros.copy())
                       for s in SURFACES for n in (64, 128)]))
    return study, evaluation, inventory


def test_fixed_matrix_rejects_omissions_reordering_and_redirection():
    study, evaluation, inventory = matrix()
    rows = matrix_rows(study, evaluation, inventory)
    assert len(rows) == 60 and len([r for r in rows if r["kind"] == "fresh"]) == 48
    for bad in ("omit", "order", "source"):
        changed = copy.deepcopy(evaluation)
        if bad == "omit":
            changed["cells"][0]["grids"].pop()
        elif bad == "order":
            changed["old_fields"].reverse()
        else:
            changed["old_fields"][0]["wout"]["sha256"] = "b"*64
        with pytest.raises(ValueError):
            matrix_rows(study, changed, inventory)


def test_metrics_mismatch_and_nonfinite_rejected():
    old = {k: np.ones((2, 2)) for k in ("mod_b", "radius", "height")}
    old.update(et=np.ones((2, 2, 3)), ep=np.ones((2, 2, 3)), iota=np.array(.7))
    new = {k: v.copy() for k, v in old.items()}
    new["height"][0, 0] += .01
    assert auditor.metrics(new, old, False)["rz"] == pytest.approx(.01)
    assert evaluator.array_errors(new, old)["height"] == pytest.approx(.01)
    new["height"][0, 0] = np.nan
    with pytest.raises(ValueError):
        auditor.metrics(new, old, False)
    with pytest.raises(ValueError):
        evaluator.array_errors(new, old)


def test_complete_toy_matrix_and_independent_audit_then_mutation(tmp_path, monkeypatch):
    path = tmp_path / "toy.nc"
    toy_file(path)
    study, evaluation, inventory = matrix()
    rows = matrix_rows(study, evaluation, inventory)
    for s in SURFACES:
        arrays = tmp_path / f"old-{s}.npz"
        np.savez_compressed(arrays, **old_sample(path, s, 128))
        for r in rows:
            if r["surface"] == s:
                r.update(wout=reference(path), old_arrays=reference(arrays))
    output, raw = tmp_path/"output.json", tmp_path/"raw"
    monkeypatch.setattr(evaluator, "frozen_sources", lambda root: (rows, []))
    monkeypatch.setattr(evaluator, "closed_predecessors", lambda root: [])
    monkeypatch.setattr(evaluator, "require_committed", lambda *a: None)
    monkeypatch.setattr(evaluator, "space_check", lambda *a: {})
    monkeypatch.setattr(sys, "argv", ["evaluate", str(output), str(raw)])
    assert evaluator.main() == 0
    result = json.loads(output.read_text())
    assert len(result["rows"]) == 60 and len(result["cells"]) == 16
    assert result["all_coordinate_checks_pass"] and result["all_fidelity_screens_pass"]
    assert result["all_refinement_screens_pass"]
    monkeypatch.setattr(auditor, "frozen_sources", lambda root: (rows, []))
    monkeypatch.setattr(auditor, "space_check", lambda *a: {})
    audit = tmp_path/"audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(output), str(audit)])
    assert auditor.main() == 0
    checked = json.loads(audit.read_text())
    assert checked["all_pass"] and checked["independent_scalar_point_roots"] == 60*1024
    result["rows"][12]["levels"][0]["pest_fidelity"]["et"] = .2
    altered = tmp_path/"altered.json"
    altered.write_text(json.dumps(result))
    monkeypatch.setattr(sys, "argv", ["audit", str(altered), str(tmp_path/"rejected.json")])
    assert auditor.main() == 2
