"""Analytic canonical-sized GN workflow, strict failure accounting and independent audit."""

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from test_geometric_curvature_workflow import setup_case

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_current_start_gn as audit
import evaluate_geometric_curvature as toy_driver
import run_current_gn_arm as arm
import run_current_start_gn as driver
from current_diagnostic_inputs import reference


def setup_gn(tmp_path, monkeypatch, fault=None):
    source, frozen, doc, names = setup_case(tmp_path, monkeypatch)
    source["label"] = "slsqp"
    x0 = frozen["points"][0]
    matrix = np.zeros((1024, 207))
    matrix[np.arange(207), np.arange(207)] = 0.05

    def state(point):
        delta = point - x0
        z = matrix @ delta
        z[500] += 1e-4 + 0.01 * float(delta @ delta)
        d = matrix.copy()
        d[500] += 0.02 * delta
        values, jac = np.ones(138), np.zeros((138, 207))
        values[0], jac[0] = float(z @ z / 2e-6), d.T @ z / 1e-6
        if fault == "budget":
            values[1] = point[3] - x0[3] - 0.05
            jac[1, 3] = 1
        return values, jac

    qualified = dict(
        points=frozen["points"],
        values=np.array([state(p)[0] for p in frozen["points"]]),
        jacobian=state(x0)[1],
        native_matrix=matrix,
        hessian=matrix.T @ matrix / 1e-6,
    )
    if fault == "gate":
        qualified["values"][0, 0] += 0.01

    def native_setup(root, raw):
        ctx, prep, full = toy_driver.native_setup(root, raw)

        def save(filename):
            saved = copy.deepcopy(doc)
            for name, value in zip(names, ctx.Jf.x, strict=True):
                owner, label = name.split(":", 1)
                dofs = saved["simsopt_objs"][saved["simsopt_objs"][owner]["dofs"]["value"]]
                dofs["x"]["data"][dofs["names"].index(label)] = float(value)
            Path(filename).write_text(json.dumps(saved))

        ctx.Jf.field.save = save
        return ctx, prep, full

    class Direct:
        def __init__(self, ctx, full):
            old = toy_driver.DirectConstraintBackend(ctx, full)
            self.__dict__.update(old.__dict__)
            self.ctx, self.global_objective, self.work = ctx, ctx.Jf, audit.expected_work(0)[0]
            self.labels = [str(i) for i in range(138)]

        def evaluate(self, point):
            self.work = audit.expected_work(self.work["evaluations"] + 1)[0]
            self.ctx.Jf.x = point.copy()
            return *state(point), {}

    calls = 0

    def batch(*args):
        nonlocal calls
        calls += 1
        if fault == "backend" and calls == 3:
            raise RuntimeError("deliberate batched assembly interruption")
        return toy_driver.batched_field_jacobian(*args)

    monkeypatch.setattr(arm, "batched_field_jacobian", batch)
    monkeypatch.setattr(driver, "native_setup", native_setup)
    monkeypatch.setattr(driver, "DirectConstraintBackend", Direct)
    monkeypatch.setattr(driver, "versions", lambda: dict(scipy="1.18.1", toy="not native physics"))
    binding = dict(toy=True)
    for module in (driver, audit):
        monkeypatch.setattr(module, "qualified_source", lambda _: (source, qualified, binding))
        monkeypatch.setattr(module, "require_committed", lambda *_args: None)
    return qualified, names


def test_analytic_control_and_full_two_repeat_workflow(tmp_path, monkeypatch):
    setup_gn(tmp_path, monkeypatch)
    assert arm.control()["all_pass"]
    study, raw = tmp_path / "study", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["study", str(study), str(raw)])
    assert driver.main() == 0
    summary = json.loads((study / "summary.json").read_text())
    for ref in summary["arms"]:
        record = json.loads(Path(ref["path"]).read_text())
        assert record["stop_reason"] == "construction_target"
        assert len(record["startup"]) == 16
        assert record["counters"]["attempts"] >= 17
    output = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(study), str(output)])
    assert audit.main() == 0
    assert json.loads(output.read_text())["all_pass"]
    summary["solver_options"]["initial_tr_radius"] = 0.2
    (study / "summary.json").write_text(json.dumps(summary))
    monkeypatch.setattr(sys, "argv", ["audit", str(study), str(tmp_path / "bad-audit.json")])
    assert audit.main() == 2


def test_budget_boundary_and_corrupted_work_point_or_start_rejected(tmp_path, monkeypatch):
    qualified, names = setup_gn(tmp_path, monkeypatch, "budget")
    prep = tmp_path / "prep"
    prep.mkdir()
    ctx, _, full = driver.native_setup(None, prep)
    direct = driver.DirectConstraintBackend(ctx, full)
    record = arm.run_arm(
        direct, ctx, qualified, tmp_path / "raw", tmp_path / "arm.json", 1, budget=20
    )
    assert record["status"] == "budget_exhausted"
    assert record["counters"]["attempts"] == 20 and record["counters"]["denied"] == 1
    assert all(audit.audit_arm(record, names, qualified, budget=20).values())
    for kind in ("work", "point", "startup", "identity"):
        bad = copy.deepcopy(record)
        if kind == "work":
            bad["gn_work"]["native_covector_B_requests"] -= 1
        elif kind == "point":
            bad["physical_points"][-1][0] += 0.01
        elif kind == "startup":
            bad["startup"][0]["values_error"] = 0.01
        else:
            bad["gn_identity_checks"][0]["gradient_normalized_error"] = 0.1
        assert not all(audit.audit_arm(bad, names, qualified, budget=20).values())


@pytest.mark.parametrize("fault", ["gate", "backend"])
def test_early_failures_keep_complete_points_and_available_bundle(tmp_path, monkeypatch, fault):
    qualified, _ = setup_gn(tmp_path, monkeypatch, fault)
    prep = tmp_path / "prep"
    prep.mkdir()
    ctx, _, full = driver.native_setup(None, prep)
    direct = driver.DirectConstraintBackend(ctx, full)
    output = tmp_path / "arm.json"
    with pytest.raises((ValueError, RuntimeError), match="startup gate|deliberate"):
        arm.run_arm(direct, ctx, qualified, tmp_path / "raw", output, 1, budget=20)
    record = json.loads(output.read_text())
    assert record["status"] == "error" and not record["gradient_screen_pass"]
    expected = 1 if fault == "gate" else 3
    assert record["counters"]["attempts"] == expected
    assert len(record["physical_points"]) == expected
    data = audit.arrays(record["failed_arrays"])
    assert data["jacobian"].shape == (138, 207)
    assert np.array_equal(data["x"], record["physical_points"][-1])
    assert reference(Path(record["failed_field"]["path"])) == record["failed_field"]
    assert record["gn_work"]["assembly_requests"] == expected
    assert record["gn_work"]["assembly_completed"] == (1 if fault == "gate" else 2)
