"""Canonical-sized toy workflow; native source/physics claims are not mocked into admission."""

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from test_serialized_current_affine import fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_geometric_curvature as auditor
import evaluate_geometric_curvature as driver
import geometric_curvature_inputs as inputs
from current_diagnostic_inputs import reference

from fusion_baselines.serialized_dofs import named_serialized_values


def setup_case(tmp_path, monkeypatch, fault=None):
    doc, names = fixture()
    x = named_serialized_values(doc, names)
    d = np.zeros((1024, 207))
    d[np.arange(207), np.arange(207)] = 0.05
    z0 = np.zeros(1024)
    z0[500] = 1e-4
    normal = np.zeros((32, 32, 3))
    normal[:, :, 2] = 1
    observation = np.zeros((1024, 3))
    observation[:, 0] = np.arange(1024)
    nonlinear = 10 if fault == "usefulness" else 0.01

    def residual(point):
        delta = point - x
        z = z0 + d @ delta
        z[500] += nonlinear * float(delta @ delta)
        return z

    def derivative(point):
        jac = d.copy()
        jac[500] += 2 * nonlinear * (point - x)
        return jac

    field_path = tmp_path / "source.json"
    field_path.write_text(json.dumps(doc))
    ref = reference(field_path)
    source_path = tmp_path / "source.npz"
    values, jacobian = np.ones(138), np.zeros((138, 207))
    values[0] = float(z0 @ z0 / 2e-6)
    jacobian[0] = d.T @ z0 / 1e-6
    np.savez_compressed(
        source_path,
        after_x=x,
        after_values=values,
        after_jacobian=jacobian,
        A=d[:, :3],
        points=observation,
        normal=normal,
    )
    prep = dict(
        surface=ref,
        case=ref,
        thresholds={},
        guarded_search_targets={},
        canonical_total=1250075.624635464,
        degrees_of_freedom=names,
    )
    source = dict(field=ref, names=names, arrays=reference(source_path), preparation=prep)
    points, steps, directions, kinds = [x], [], [], ["source"]
    for i, radius in enumerate((1e-6, 1e-5, 1e-4)):
        p = np.zeros(207)
        p[3 + i] = 1
        directions.append(p)
        steps.append(radius * p)
        for eps in (1e-7, 1e-8):
            for sign in (1, -1):
                points.append(x + sign * eps * p)
                kinds.append(f"direction-{i}-eps-{eps}-sign-{sign}")
        points.append(x + radius * p)
        kinds.append(f"direction-{i}-trial")
    fluxes = [float(residual(p) @ residual(p) / 2) for p in points]
    frozen = dict(
        points=np.array(points),
        steps=np.array(steps),
        directions=np.array(directions),
        kinds=kinds,
        fluxes=np.array(fluxes),
        gradient=jacobian[0],
        currents=np.arange(3),
        A=d[:, :3],
        bundles=[ref] * 16,
    )
    selected = [dict(source, label=label) for label in ("al", "slsqp")]

    class Field:
        def __init__(self, ctx):
            self.ctx, self.points, self.vjps = ctx, observation.copy(), 0
            curve = SimpleNamespace(
                **{
                    name: lambda: np.zeros(1)
                    for name in ("gamma", "gammadash", "dgamma_by_dcoeff", "dgammadash_by_dcoeff")
                }
            )
            current = SimpleNamespace(get_value=lambda: 1.0, vjp=lambda _: lambda _: np.zeros(207))
            self.coils = [SimpleNamespace(curve=curve, current=current) for _ in range(16)]

        def set_points(self, value):
            self.points = np.array(value).copy()

        def get_points_cart_ref(self):
            return self.points

        def B(self):
            ids = self.points[:, 0].astype(int)
            b = np.zeros((len(ids), 3))
            b[:, 2] = 32 * residual(self.ctx.Jf.x)[ids]
            return b

        def B_vjp(self, weights):
            self.vjps += 1
            if fault == "exception" and self.vjps == 3:
                raise RuntimeError("deliberate local VJP interruption")
            ids = self.points[:, 0].astype(int)
            return lambda _: derivative(self.ctx.Jf.x)[ids].T @ (weights[:, 2] * 32)

    class Backend:
        def __init__(self, ctx, _):
            self.field, self.names = ctx.Jf.field, names
            self.points, self.normal = observation.copy(), normal.copy()
            self.weights = normal.reshape(-1, 3) / 32

        def evaluate(self, *_args, **_kwargs):
            raise AssertionError("no full native bundles authorized")

    def native_setup(_root, raw):
        ctx = SimpleNamespace(Jf=SimpleNamespace(x=x.copy(), dof_names=names))
        ctx.Jf.field = Field(ctx)
        template = raw / "normalized_start.json"
        template.write_text(json.dumps(doc))
        return ctx, dict(prep, normalized_start=reference(template)), None

    def batch(field, obj, _points, _weights):
        for coil in field.coils:
            coil.curve.gamma()
            coil.curve.gammadash()
            coil.curve.dgamma_by_dcoeff()
            coil.curve.dgammadash_by_dcoeff()
            coil.current.get_value()
            coil.current.vjp(np.ones(1))(obj)
        return residual(obj.x), derivative(obj.x)

    for module in (driver, auditor):
        monkeypatch.setattr(module, "sources", lambda _: (selected, [frozen, frozen], []))
        monkeypatch.setattr(module, "require_committed", lambda *_args: None)
    monkeypatch.setattr(driver, "installed", lambda _: dict(qualification=ref, sources=[]))
    monkeypatch.setattr(driver, "versions", lambda: dict(toy="pure, not native physics"))
    monkeypatch.setattr(driver, "native_setup", native_setup)
    monkeypatch.setattr(driver, "DirectConstraintBackend", Backend)
    monkeypatch.setattr(driver, "batched_field_jacobian", batch)
    return source, frozen, doc, names


@pytest.mark.parametrize("fault", [None, "usefulness"])
def test_full_workflow_and_negative_model_classification(tmp_path, monkeypatch, fault):
    setup_case(tmp_path, monkeypatch, fault)
    output, raw = tmp_path / "study.json", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["study", str(output), str(raw)])
    assert driver.main() == (0 if fault is None else 2)
    study = json.loads(output.read_text())
    assert study["all_pass"]
    assert study["usefulness_pass"] == (fault is None)
    assert all(row["work"] == auditor.native_work() for row in study["cases"])
    audit_path = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", str(output), str(audit_path)])
    assert auditor.main() == 0
    audit = json.loads(audit_path.read_text())
    assert audit["all_pass"] and not audit["physical_admission"]
    for key in ("steps", "directions", "gradient", "columns", "A", "points"):
        changed = copy.deepcopy(study["cases"][0])
        data = inputs.arrays(changed["inputs"])
        data[key].flat[0] += 1
        path = tmp_path / f"corrupt-{key}.npz"
        np.savez_compressed(path, **data)
        changed["inputs"] = reference(path)
        selected, frozen, _ = auditor.sources(None)
        result = auditor.audit_case(changed, selected[0], frozen[0])
        assert not result["all_pass"]


def test_partial_local_failure_keeps_field_batch_rows_and_counts(tmp_path, monkeypatch):
    setup_case(tmp_path, monkeypatch, "exception")
    output, raw = tmp_path / "study.json", tmp_path / "raw"
    monkeypatch.setattr(sys, "argv", ["study", str(output), str(raw)])
    with pytest.raises(RuntimeError, match="deliberate"):
        driver.main()
    study = json.loads(output.read_text())
    row = study["cases"][0]
    assert study["status"] == "error" and len(study["cases"]) == 1
    assert row["events"][0]["status"] == "completed" and "batch_arrays" in row
    assert row["work"]["local_VJP_requests"] == 3
    assert row["work"]["local_VJP_completed"] == 2
    assert inputs.arrays(row["partial_local_arrays"])["rows"].shape == (2, 207)


def test_frozen_source_mapping_and_point_mutations(tmp_path, monkeypatch):
    source, frozen, doc, names = setup_case(tmp_path, monkeypatch)
    source["label"] = "al"
    # Exercise a nontrivial runtime-name ordering without changing physical owners.
    permutation = np.arange(206, -1, -1)
    row = dict(
        names=list(reversed(names)),
        preparation=dict(normalized_start=source["field"]),
        source_indices_in_target_order=permutation.tolist(),
        owner_map={f"{kind}{i}": f"{kind}{i}" for kind in ("curve", "current") for i in range(4)},
        evaluations=[],
        directions=[],
    )
    # The current graph has the same fourth fixed leaf, as mapped_start verifies.
    original = inputs.source_arrays(source)
    for i, point in enumerate(frozen["points"]):
        path = tmp_path / f"bundle-{i}.npz"
        values = np.ones(138)
        values[0] = frozen["fluxes"][i] / 1e-6
        np.savez_compressed(
            path, x=point[permutation], values=values, jacobian=original["jacobian"][:, permutation]
        )
        row["evaluations"].append(
            dict(
                index=i,
                kind=frozen["kinds"][i],
                status="completed",
                x=point[permutation].tolist(),
                arrays=reference(path),
            )
        )
    for i, radius in enumerate((1e-6, 1e-5, 1e-4)):
        path = tmp_path / f"direction-{i}.npz"
        np.savez_compressed(
            path,
            step=frozen["steps"][i, permutation],
            direction=frozen["directions"][i, permutation],
        )
        row["directions"].append(
            dict(
                radius=radius,
                all_pass=True,
                trial_evaluated=True,
                gate=dict(all_pass=True),
                arrays=reference(path),
            )
        )
    result = inputs.frozen_case(row, source)
    assert np.array_equal(result["points"], frozen["points"])
    changed = copy.deepcopy(row)
    changed["directions"][0]["radius"] = 1e-3
    with pytest.raises(ValueError, match="radius"):
        inputs.frozen_case(changed, source)
    changed = copy.deepcopy(row)
    changed["evaluations"][1]["x"][10] += 1
    with pytest.raises(ValueError, match="point"):
        inputs.frozen_case(changed, source)
