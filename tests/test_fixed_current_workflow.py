"""Synthetic full driver/file-audit controls; no physical coil data are evaluated."""

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from test_serialized_current_affine import fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_fixed_currents as auditor
import qualify_fixed_currents as driver

from fusion_baselines.current_diagnostic_audit import audit_arrays, project
from fusion_baselines.serialized_dofs import named_serialized_values


def setup_toy(tmp_path, monkeypatch, *, fail_field=False):
    doc, names = fixture()
    x = named_serialized_values(doc, names)
    normal = np.zeros((32, 32, 3))
    normal[..., 2] = 1
    base = np.zeros_like(normal)
    base[..., 0] = 1
    base[..., 2] = 0.001
    base.reshape(-1, 3)[:3, 2] = [-0.1, 0.2, -0.3]
    slopes = np.zeros((3, 32, 32, 3))
    for i in range(3):
        slopes[i].reshape(-1, 3)[i, 2] = i + 1

    def magnetic(proposal):
        return base + np.tensordot(proposal[:3], slopes, 1)

    def values(proposal):
        z = project(magnetic(proposal), normal)
        v = np.ones(138)
        v[0] = float(z @ z) / 2e-6
        jac = np.zeros((138, 207))
        jac[0, :3] = np.column_stack([project(s, normal) for s in slopes]).T @ z / 1e-6
        return v, jac

    source = tmp_path / "source.json"
    source.write_text(json.dumps(doc))
    arrays = tmp_path / "source.npz"
    np.savez_compressed(arrays, x=x, values=values(x)[0])
    prep = dict(
        surface=driver.reference(source),
        case=driver.reference(source),
        thresholds={},
        guarded_search_targets={},
        canonical_total=1250075.624635464,
        degrees_of_freedom=names,
    )
    selected = [
        dict(
            label=label,
            preparation=prep.copy(),
            field=driver.reference(source),
            arrays=driver.reference(arrays),
            names=names,
        )
        for label in ("al", "slsqp")
    ]

    class Field:
        def __init__(self, ctx):
            self.ctx, self.calls = ctx, 0

        def set_points(self, _points):
            pass

        def B(self):
            self.calls += 1
            if fail_field and self.calls == 2:
                raise RuntimeError("deliberate probe interruption")
            return magnetic(self.ctx.Jf.x)

        def save(self, filename):
            saved = copy.deepcopy(doc)
            for i in range(3):
                saved["simsopt_objs"][f"q{i}"]["x"]["data"] = [float(self.ctx.Jf.x[i])]
            Path(filename).write_text(json.dumps(saved))

    def prepare(_root, raw):
        ctx = SimpleNamespace(Jf=SimpleNamespace(x=x.copy()))
        ctx.Jf.field = Field(ctx)
        path = raw / "normalized_start.json"
        path.write_text(json.dumps(doc))
        return ctx, dict(**prep, normalized_start=driver.reference(path)), None

    class Backend:
        def __init__(self, ctx, _full):
            self.ctx, self.names, self.normal = ctx, names, normal
            self.points, self.field = np.zeros((1024, 3)), ctx.Jf.field
            self.work = {}

        def evaluate(self, proposal):
            self.ctx.Jf.x = proposal.copy()
            per = dict(
                evaluations=1,
                jacobian_evaluations=1,
                B_grid_requests=1,
                B_vjp_requests=1,
                position_requests=16,
                position_derivative_requests=16,
                curvature_requests=4,
                curvature_derivative_requests=4,
                native_metric_requests=12,
                native_gradient_requests=12,
                coil_pair_samples=4800000,
                plasma_pair_samples=3276800,
            )
            for key, value in per.items():
                self.work[key] = self.work.get(key, 0) + value
            v, j = values(proposal)
            return v, j, {}

    for module in (driver, auditor):
        monkeypatch.setattr(module, "sources", lambda _root: selected)
        monkeypatch.setattr(module, "predecessor", lambda _root: driver.reference(source))
        monkeypatch.setattr(module, "require_committed", lambda *_args: None)
    monkeypatch.setattr(driver, "native_setup", prepare)
    monkeypatch.setattr(driver, "versions", lambda: dict(toy="no native dependencies"))
    monkeypatch.setattr(driver, "DirectConstraintBackend", Backend)
    return selected


def test_two_state_driver_independent_file_audit_and_mutations(tmp_path, monkeypatch):
    selected = setup_toy(tmp_path, monkeypatch)
    output, raw = tmp_path / "study.json", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["qualify", str(output), str(raw)])
    assert driver.main() == 0
    study = json.loads(output.read_text())
    assert study["all_pass"] and len(study["cases"]) == 2
    for row, original in zip(study["cases"], selected, strict=True):
        audit = auditor.audit_case(row, original)
        assert audit["all_pass"], audit
        with np.load(row["arrays"]["path"]) as archive:
            data = {k: archive[k] for k in archive.files}
        changed = copy.deepcopy(data)
        changed["after_x"][20] += 0.01
        assert not audit_arrays(changed, row)["all_pass"]
        changed = copy.deepcopy(data)
        changed["B_probes"][0, 0, 0, 0, 2] += 0.01
        assert not audit_arrays(changed, row)["all_pass"]
        changed = copy.deepcopy(data)
        changed["B_after"][2, 2, 2] = np.nan
        with pytest.raises(ValueError, match="nonfinite"):
            audit_arrays(changed, row)
        altered = copy.deepcopy(row)
        altered["work"]["additional_B_grid_requests"] -= 1
        assert not audit_arrays(data, altered)["all_pass"]
    audit_path = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(output), str(audit_path)])
    assert auditor.main() == 0
    assert json.loads(audit_path.read_text())["all_pass"]


def test_failed_probe_preserves_proposal_and_completed_work(tmp_path, monkeypatch):
    setup_toy(tmp_path, monkeypatch, fail_field=True)
    output, raw = tmp_path / "failed.json", tmp_path / "partial"
    monkeypatch.setattr(sys, "argv", ["qualify", str(output), str(raw)])
    with pytest.raises(RuntimeError, match="deliberate"):
        driver.main()
    study = json.loads(output.read_text())
    assert study["status"] == "error" and not study["all_pass"]
    assert len(study["cases"]) == 1
    row = study["cases"][0]
    assert row["work"]["direct"]["evaluations"] == 1
    assert row["work"]["additional_B_grid_requests"] == 2
    assert row["work"]["svd_fits"] == row["work"]["qr_fits"] == 0
    with np.load(row["arrays"]["path"]) as data:
        assert "field_request_1_B" in data
        assert "field_request_2_x" in data and "field_request_2_B" not in data
    assert not (raw / "al/current_minimizer.json").exists()
