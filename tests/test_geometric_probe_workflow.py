"""Synthetic native adapter with real Fourier/complex/independent chain-rule controls."""

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from test_serialized_current_affine import fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_geometric_probes as auditor
import probe_geometric_descent as driver
from current_diagnostic_inputs import reference

from fusion_baselines.coil_coefficient_view import base_arrays, serialized_physical_coefficients
from fusion_baselines.complex_clearance import clearance_rows, fourier_positions
from fusion_baselines.serialized_dofs import named_serialized_values


def setup_case(tmp_path, monkeypatch, fault=None):
    doc, names = fixture()
    x = named_serialized_values(doc, names)
    coefficients = serialized_physical_coefficients(doc, base_arrays(doc, names, x))
    values, jac = np.ones(138), np.zeros((138, 207))
    values[0] = 0.2
    values[6:126] = clearance_rows(coefficients, 1.0)[0]
    p = np.zeros((3, 207))
    for axis in range(3):
        columns = [3 + 51 * i + 17 * axis for i in range(4)]
        p[axis, columns] = 0.5
        jac[0, columns] = -0.01
    source_file = tmp_path / "source.json"
    source_file.write_text(json.dumps(doc))
    source_npz = tmp_path / "source.npz"
    np.savez_compressed(source_npz, after_x=x, after_values=values, after_jacobian=jac)
    ref = reference(source_file)
    prep = dict(
        surface=ref,
        case=ref,
        thresholds=dict(a0=1.0),
        guarded_search_targets={},
        canonical_total=1250075.624635464,
        degrees_of_freedom=names,
    )
    selected = [
        dict(label=label, field=ref, arrays=reference(source_npz), names=names, preparation=prep)
        for label in ("al", "slsqp")
    ]
    cases = []
    for source in selected:
        models = []
        for i, radius in enumerate((1e-6, 1e-5, 1e-4)):
            path = tmp_path / f"{source['label']}-model-{i}.npz"
            np.savez_compressed(path, step=radius * p[i], direction=p[i])
            models.append(dict(radius=radius, step_norm=radius, arrays=reference(path)))
        cases.append(dict(source=source, models=models))
    model_path = tmp_path / "models.json"
    model_path.write_text(
        json.dumps(
            dict(
                status="completed",
                all_pass=True,
                cases=cases,
                prerequisites=[],
                code=[],
                protocol=ref,
                environment=dict(installed_sources=[]),
            )
        )
    )
    model_audit = tmp_path / "model-audit.json"
    model_audit.write_text(
        json.dumps(dict(status="completed", all_pass=True, source=reference(model_path), code=[]))
    )

    class Field:
        def __init__(self, ctx):
            self.ctx = ctx
            self.coils = [
                SimpleNamespace(curve=SimpleNamespace(gamma=lambda i=i: self.positions()[i]))
                for i in range(16)
            ]

        def positions(self):
            bases = base_arrays(doc, names, self.ctx.Jf.x)
            return fourier_positions(serialized_physical_coefficients(doc, bases), 200)

        def save(self, filename):
            saved = copy.deepcopy(doc)
            for name, value in zip(names, self.ctx.Jf.x, strict=True):
                owner, label = name.split(":", 1)
                dofs = saved["simsopt_objs"][saved["simsopt_objs"][owner]["dofs"]["value"]]
                dofs["x"]["data"][dofs["names"].index(label)] = float(value)
            Path(filename).write_text(json.dumps(saved))

    class Backend:
        def __init__(self, ctx, _surface):
            self.ctx, self.names, self.field, self.work, self.count = (
                ctx,
                names,
                ctx.Jf.field,
                {},
                0,
            )

        def evaluate(self, point):
            self.count += 1
            self.work = auditor.expected_work(self.count)
            if fault == "exception" and self.count == 3:
                raise RuntimeError("deliberate native failure")
            self.ctx.Jf.x = point.copy()
            delta = point - x
            v = values + jac @ delta
            derivative = jac.copy()
            v[0] += 1000 * float(delta @ delta)
            derivative[0] += 2000 * delta
            if fault == "fd" and self.count == 2:
                v[0] += 4e-10
            return v, derivative, {}

    def native_setup(_root, raw):
        ctx = SimpleNamespace(Jf=SimpleNamespace(x=x.copy()))
        ctx.Jf.field = Field(ctx)
        normalized = raw / "normalized_start.json"
        normalized.write_text(json.dumps(doc))
        return ctx, dict(prep, normalized_start=reference(normalized)), None

    for module in (driver, auditor):
        monkeypatch.setattr(module, "closed_sources", lambda _root: (selected, []))
        monkeypatch.setattr(module, "require_committed", lambda *_args: None)
    monkeypatch.setattr(driver, "native_setup", native_setup)
    monkeypatch.setattr(driver, "versions", lambda: dict(toy="no native dependencies"))
    monkeypatch.setattr(driver, "DirectConstraintBackend", Backend)
    monkeypatch.setattr(
        driver,
        "native_coefficients",
        lambda _field, bases: serialized_physical_coefficients(doc, bases),
    )
    return model_path, model_audit


@pytest.mark.parametrize("fault", [None, "fd"])
def test_complete_native_probe_matrix_and_independent_audit(tmp_path, monkeypatch, fault):
    model, model_audit = setup_case(tmp_path, monkeypatch, fault)
    output, raw = tmp_path / "probes.json", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["probe", str(model), str(model_audit), str(output), str(raw)])
    assert driver.main() == (0 if fault is None else 2)
    study = json.loads(output.read_text())
    assert study["status"] == "completed"
    for row in study["cases"]:
        assert len(row["evaluations"]) == (16 if fault is None else 15)
        assert row["directions"][0]["trial_evaluated"] == (fault is None)
        assert not row["directions"][2]["trial"]["flux_improves"]
    output_audit = tmp_path / "probe-audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(output), str(output_audit)])
    assert auditor.main() == 0
    audit = json.loads(output_audit.read_text())
    assert audit["all_pass"] and audit["original_qualification"] == (fault is None)
    changed = copy.deepcopy(study["cases"][0])
    changed["directions"][2]["trial"]["flux_improves"] = True
    source = changed["source"]
    model_case = json.loads(model.read_text())["cases"][0]
    assert not auditor.audit_case(changed, source, model_case)["all_pass"]


def test_native_failure_preserves_pending_point_and_completed_bundles(tmp_path, monkeypatch):
    model, model_audit = setup_case(tmp_path, monkeypatch, "exception")
    output, raw = tmp_path / "probes.json", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["probe", str(model), str(model_audit), str(output), str(raw)])
    with pytest.raises(RuntimeError, match="deliberate"):
        driver.main()
    study = json.loads(output.read_text())
    assert study["status"] == "error" and len(study["cases"]) == 1
    row = study["cases"][0]
    assert row["work"]["evaluations"] == 3
    assert [e["status"] for e in row["evaluations"]] == ["completed", "completed", "error"]
    assert len(row["evaluations"][-1]["x"]) == 207
    assert Path(row["directions"][0]["input_arrays"]["path"]).exists()
