"""Synthetic producer/auditor integration; no project equilibrium is evaluated."""

import copy
import sys
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines import coupled_coil_audit as audit
from fusion_baselines import coupled_coils as producer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import coupled_coil_inputs as inputs  # noqa: E402


def synthetic_input():
    return dict(
        nfp=2, mpol=3, ntor=1, lasym=False, phiedge=np.pi / 100,
        rbc=[dict(m=0, n=0, value=1.0), dict(m=1, n=0, value=0.1),
             dict(m=2, n=1, value=0.003)],
        zbs=[dict(m=1, n=0, value=0.1), dict(m=1, n=-1, value=0.002)],
    )


def synthetic_target(wout, input_json, ninner):
    data = synthetic_input()
    phi, theta = np.meshgrid(
        np.pi * np.arange(ninner) / ninner,
        2 * np.pi * np.arange(ninner) / ninner, indexing="ij",
    )
    points, fields = [], []
    for s in (0.25, 0.5, 0.75):
        radius = 1 + 0.1 * np.sqrt(s) * np.cos(theta)
        points.append(np.stack((radius * np.cos(phi), radius * np.sin(phi),
                                0.1 * np.sqrt(s) * np.sin(theta)), axis=-1).reshape(-1, 3))
        fields.append(np.stack((-np.sin(phi) / radius, np.cos(phi) / radius,
                                np.zeros_like(phi)), axis=-1).reshape(-1, 3))
    return dict(input=data, inner_points=np.concatenate(points),
                inner_target=np.concatenate(fields), target_flux=-np.pi / 100, sources={})


@pytest.fixture
def make_model(monkeypatch):
    monkeypatch.setattr(producer, "load_target", synthetic_target)

    def make(nbase=6, order=5, method="N", **kwargs):
        return producer.CoupledCoils(
            "synthetic-not-a-project-wout", "synthetic-not-a-project-input", nbase, order,
            method, ncoil=48, nphi=8, ntheta=12, **kwargs,
        )

    return make


@pytest.mark.parametrize("nbase,order", [(6, 5), (8, 7)])
@pytest.mark.parametrize("method", ["N", "V"])
def test_full_named_reconstruction_and_objectives(make_model, nbase, order, method):
    model = make_model(nbase, order, method)
    x = model.seed_x.copy()
    # Exercise every canonical mode without assuming that startup circles suffice.
    x += 0.0002 * np.sin(np.arange(x.size) + 1)
    j, gradient, native_metrics = model.evaluate(x)
    snapshot, arrays = model.snapshot(x), model.arrays(x)
    audit.validate_snapshot(snapshot)
    assert snapshot["names"] == audit.parameter_names(nbase, order)
    assert np.isfinite(gradient).all() and gradient.shape == x.shape
    curves = audit.physical_curves(snapshot, model.ncoil)
    for key in ("positions", "tangents", "currents"):
        np.testing.assert_allclose(curves[key], arrays[f"coil_{key}"], rtol=2e-13, atol=1e-14)
    surface = audit.boundary(synthetic_input(), model.nphi, model.ntheta)
    for key, expected in (("points", "boundary_points"), ("unitnormal", "boundary_normals")):
        np.testing.assert_allclose(surface[key].reshape(-1, 3), arrays[expected],
                                   rtol=2e-13, atol=1e-14)
    np.testing.assert_allclose(surface["weights"].ravel(), arrays["boundary_weights"],
                               rtol=2e-13, atol=1e-14)
    loop_points, loop_tangent = audit.loop(synthetic_input(), 256)
    np.testing.assert_allclose(loop_points, arrays["loop_points"], rtol=0, atol=1e-14)
    np.testing.assert_allclose(loop_tangent, arrays["loop_tangents"], rtol=0, atol=1e-14)
    for grid, field_key, component in (
        ("boundary", "B", 0), ("inner", "B", 0), ("loop", "A", 1),
    ):
        indices = np.linspace(0, len(arrays[f"{grid}_points"]) - 1, 16, dtype=int)
        independent = audit.direct_field(
            snapshot, arrays[f"{grid}_points"][indices], ncoil=model.ncoil,
        )[component]
        np.testing.assert_allclose(independent, arrays[f"{grid}_{field_key}"][indices],
                                   rtol=2e-12, atol=1e-13)
    independent_metrics = audit.metrics(arrays["boundary_B"], arrays["boundary_normals"],
                                        arrays["boundary_weights"], snapshot["B2_scale"])
    independent_metrics.update(audit.inner_metrics(arrays["inner_B"], arrays["inner_target"],
                                                   snapshot["B2_scale"]))
    for key in ("JN", "JV", "normal_rms", "normal_max", "vector_rms"):
        assert independent_metrics[key] == pytest.approx(native_metrics[key], rel=2e-13, abs=1e-15)
    penalties = audit.geometry_penalties(snapshot, synthetic_input(), model.ncoil)
    assert penalties["total"] == pytest.approx(native_metrics["geometry_penalty"],
                                              rel=2e-11, abs=1e-14)
    objective = independent_metrics["JN"] + penalties["total"]
    if method == "V":
        objective += 0.05 * independent_metrics["JV"]
    assert objective == pytest.approx(j, rel=2e-12, abs=1e-14)
    assert np.mean(np.sum(arrays["loop_A"] * loop_tangent, axis=1)) == pytest.approx(
        snapshot["target_flux"], rel=2e-13,
    )


@pytest.mark.parametrize("full_torus,offset", [(False, 0), (False, 0.5), (True, 0), (True, 0.5)])
def test_nonaxisymmetric_boundary_grid_normalization(make_model, full_torus, offset):
    model = make_model()
    native = model.boundary_surface(12, 16, full_torus=full_torus, offset=offset)
    independent = audit.boundary(synthetic_input(), 12, 16, full_torus=full_torus,
                                 shift=bool(offset))
    for key, actual in (("points", native.gamma()), ("normal", native.normal()),
                        ("dphi", native.gammadash1()), ("dtheta", native.gammadash2())):
        np.testing.assert_allclose(independent[key], actual, rtol=5e-13, atol=2e-14)


def test_frozen_validation_uses_original_snapshot(make_model):
    original = make_model(method="V")
    x = original.seed_x.copy()
    _, _, metrics = original.evaluate(x)
    snapshot = original.snapshot(x)
    fine = make_model(method="V", offset=0.5)
    diagnostic = fine.diagnostics(x, metrics["scale"], metrics["B2_scale"])
    arrays = fine.arrays(x, metrics["scale"], metrics["B2_scale"])
    independently = audit.direct_field(snapshot, arrays["boundary_points"], ncoil=fine.ncoil)[0]
    np.testing.assert_allclose(independently, arrays["boundary_B"], rtol=2e-12, atol=1e-13)
    assert diagnostic["scale"] == snapshot["scale"]
    assert diagnostic["B2_scale"] == snapshot["B2_scale"]
    assert diagnostic["frozen_scale"] is True
    changed = copy.deepcopy(snapshot)
    changed["unit_flux"] *= 1.00001
    with pytest.raises(ValueError, match="normalization"):
        audit.validate_snapshot(changed)


@pytest.mark.parametrize("active", ["length", "curvature", "cc", "cs"])
def test_active_geometric_penalties_and_two_direction_derivatives(make_model, active):
    model = make_model(method="V")
    coefficients = model.seed_x.reshape(model.nbase, 3, 2 * model.order + 1).copy()
    if active == "length":
        coefficients[:, :, 1:] *= 1.7
    elif active == "curvature":
        coefficients[:, 0, 2 * model.order - 1] = 0.06
    elif active == "cc":
        coefficients[1] = coefficients[0]
        coefficients[1, 2, 0] += 0.02
    else:
        coefficients[:, :, 1:] *= 0.12 / 0.35
    x = coefficients.ravel()
    _, derivative, metrics = model.evaluate(x)
    penalties = audit.geometry_penalties(model.snapshot(x), synthetic_input(), model.ncoil)
    assert penalties[active] > 0
    assert penalties["total"] == pytest.approx(metrics["geometry_penalty"], rel=2e-11, abs=1e-13)
    for direction in (np.sin(np.arange(len(x)) + 1), np.cos(np.arange(len(x)) + 1)):
        direction /= np.linalg.norm(direction)
        for h in (1e-5, 5e-6):
            difference = (model.evaluate(x + h * direction)[0]
                          - model.evaluate(x - h * direction)[0]) / (2 * h)
            assert difference == pytest.approx(derivative @ direction, rel=2e-4, abs=1e-8)


def predecessor_fixture():
    plasma = dict(legacy=dict(identity="synthetic legacy"))
    validation_ref = dict(path="synthetic-validation.json", sha256="synthetic")
    targets = {label: dict(wout=dict(path=f"{label}.nc", sha256=sha))
               for label, sha in inputs.TARGET_WOUT_HASHES.items()}
    states = []
    for ns in (201, 401):
        for label in ("reference", "selected"):
            states.append(dict(
                label=f"{label}-{ns}", errors=[], wout=targets[label]["wout"],
                fields=[dict(s=s, n=n, checks=dict.fromkeys(inputs.FIELD_CHECKS, True),
                             arrays=dict(path=f"{label}-{s}-{n}.npz", sha256="synthetic"))
                        for s in (0.25, 0.5, 0.75) for n in (64, 128)],
            ))
    validation = dict(status="completed", all_phases_completed=True, used_for_selection=False,
                      source=plasma["legacy"], states=states)
    final = dict(status="completed", phase="final", step3_pass=True,
                 arithmetic_and_source_pass=True, gates=dict.fromkeys(inputs.STEP3_GATES, True),
                 source=plasma, validation=validation_ref)
    end = dict(status="completed", source=plasma,
               rows=[dict(label="selected-repeat"), dict(label="selected-fine")])
    return final, end, validation, plasma, validation_ref, targets


def test_predecessor_requires_final_scientific_acceptance_and_exact_archives(monkeypatch):
    final, end, validation, plasma, ref, targets = predecessor_fixture()
    inputs.accepted_predecessor(final, end, validation, plasma, ref)
    checked = []
    monkeypatch.setattr(inputs, "checked", checked.append)
    archives = inputs.target_archives(validation, targets)
    assert list(archives) == ["reference", "selected"] and len(checked) == 12
    assert archives["selected"]["fields"][0]["s"] == 0.25
    assert set(archives["selected"]["fields"][0]) == {"s", "n", "arrays"}


@pytest.mark.parametrize("gate", inputs.STEP3_GATES)
def test_each_step3_gate_is_required(gate):
    final, end, validation, plasma, ref, _ = predecessor_fixture()
    final["gates"][gate] = False
    with pytest.raises(ValueError, match="predecessor"):
        inputs.accepted_predecessor(final, end, validation, plasma, ref)


@pytest.mark.parametrize("mutation", ["phase", "partial", "wrong_source", "missing_gate",
                                     "truthy_gate", "wrong_validation", "state_label",
                                     "errors", "selection_feedback", "endpoint_label"])
def test_predecessor_metadata_mutations_fail_closed(mutation):
    final, end, validation, plasma, ref, _ = predecessor_fixture()
    if mutation == "phase":
        final["phase"] = "propose"
    elif mutation == "partial":
        validation["all_phases_completed"] = False
    elif mutation == "wrong_source":
        validation["source"] = {"different": True}
    elif mutation == "missing_gate":
        final["gates"].pop("geometry")
    elif mutation == "truthy_gate":
        final["gates"]["geometry"] = 1
    elif mutation == "wrong_validation":
        final["validation"] = dict(path="other", sha256="other")
    elif mutation == "state_label":
        validation["states"][2]["label"] = "selected-401"
    elif mutation == "errors":
        validation["states"][3]["errors"] = ["failed"]
    elif mutation == "selection_feedback":
        validation["used_for_selection"] = True
    else:
        end["rows"][1]["label"] = "selected-repeat"
    with pytest.raises(ValueError, match="predecessor"):
        inputs.accepted_predecessor(final, end, validation, plasma, ref)


@pytest.mark.parametrize("mutation", ["label", "wout", "duplicate", "missing", "check",
                                     "truthy", "wrong_s", "wrong_n"])
def test_target_archive_mapping_mutations_fail_closed(monkeypatch, mutation):
    _, _, validation, _, _, targets = predecessor_fixture()
    monkeypatch.setattr(inputs, "checked", lambda ref: None)
    state = validation["states"][3]
    if mutation == "label":
        state["label"] = "selected-201"
    elif mutation == "wout":
        state["wout"] = targets["reference"]["wout"]
    elif mutation == "duplicate":
        state["fields"][1] = state["fields"][0]
    elif mutation == "missing":
        state["fields"].pop()
    elif mutation in ("check", "truthy"):
        state["fields"][0]["checks"]["cartesian"] = False if mutation == "check" else 1
    elif mutation == "wrong_s":
        state["fields"][0]["s"] = 0.3
    else:
        state["fields"][0]["n"] = 16
    with pytest.raises(ValueError, match="archive identities"):
        inputs.target_archives(validation, targets)
