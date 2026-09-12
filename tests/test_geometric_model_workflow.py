import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from test_serialized_current_affine import fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_geometric_models as auditor
import solve_geometric_models as driver
from current_diagnostic_inputs import reference
from geometric_descent_inputs import source_arrays

from fusion_baselines.serialized_dofs import named_serialized_values


def toy_sources(tmp_path):
    doc, names = fixture()
    path = tmp_path / "source.json"
    path.write_text(json.dumps(doc))
    x = named_serialized_values(doc, names)
    values, jac = np.ones(138), np.zeros((138, 207))
    values[1], jac[1, 3], jac[0, 3], jac[0, 4] = 0.0, 1.0, 1.0, 2.0
    array_path = tmp_path / "source.npz"
    np.savez_compressed(array_path, after_x=x, after_values=values, after_jacobian=jac)
    return [
        dict(label=label, field=reference(path), arrays=reference(array_path), names=names)
        for label in ("al", "slsqp")
    ]


def test_six_model_execution_and_independent_audit_then_mutations(tmp_path, monkeypatch):
    pytest.importorskip("scipy.optimize")
    selected = toy_sources(tmp_path)
    for module in (driver, auditor):
        monkeypatch.setattr(module, "closed_sources", lambda _root: (selected, []))
        monkeypatch.setattr(module, "require_committed", lambda *_args: None)
    output, raw = tmp_path / "models.json", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["solve", str(output), str(raw)])
    assert driver.main() == 0
    study = json.loads(output.read_text())
    assert study["LP_calls"] == study["independent_certificate_checks"] == 6
    assert study["native_calls"] == 0
    audit_path = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(output), str(audit_path)])
    assert auditor.main() == 0
    assert json.loads(audit_path.read_text())["all_pass"]
    row = copy.deepcopy(study["cases"][0])
    row["models"][0]["solver"]["lower_marginals"][0] += 0.01
    assert not auditor.audit_case(row, selected[0])["all_pass"]
    row = copy.deepcopy(study["cases"][0])
    row["models"].reverse()
    with pytest.raises(ValueError, match="matrix"):
        auditor.audit_case(row, selected[0])


def test_source_named_vector_and_zero_current_geometry_columns(tmp_path):
    sources = toy_sources(tmp_path)
    data = source_arrays(sources[0])
    assert len(data["geometry"]) == 204 and data["currents"].tolist() == [0, 1, 2]
    x, v, jac = data["x"], data["values"], data["jacobian"]
    changed = tmp_path / "bad.npz"
    jac[1, 0] = 1
    np.savez_compressed(changed, after_x=x, after_values=v, after_jacobian=jac)
    source = dict(sources[0], arrays=reference(changed))
    with pytest.raises(ValueError, match="current-independent"):
        source_arrays(source)
    jac[1, 0] = 0
    x[10] += 0.1
    np.savez_compressed(changed, after_x=x, after_values=v, after_jacobian=jac)
    source["arrays"] = reference(changed)
    with pytest.raises(ValueError, match="named"):
        source_arrays(source)


def test_interrupted_lp_preserves_source_arrays_and_attempt_counter(tmp_path, monkeypatch):
    selected = toy_sources(tmp_path)
    monkeypatch.setattr(driver, "closed_sources", lambda _root: (selected, []))
    monkeypatch.setattr(driver, "require_committed", lambda *_args: None)
    monkeypatch.setattr(driver, "environment", lambda: {})

    def fail(_model):
        raise RuntimeError("deliberate LP interruption")

    monkeypatch.setattr(driver, "solve_model", fail)
    output, raw = tmp_path / "failure.json", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["solve", str(output), str(raw)])
    with pytest.raises(RuntimeError, match="deliberate"):
        driver.main()
    result = json.loads(output.read_text())
    assert result["status"] == "error" and result["LP_calls"] == 1 and result["native_calls"] == 0
    model = result["cases"][0]["models"][0]
    with np.load(model["arrays"]["path"]) as arrays:
        assert arrays["A"].shape == (137, 204) and arrays["x"].shape == (207,)
