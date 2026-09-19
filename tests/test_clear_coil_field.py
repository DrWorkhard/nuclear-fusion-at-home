"""Synthetic clear-seed adapter controls; no project boundary or field is read."""

import json

import numpy as np
import pytest

from fusion_baselines import clear_coil_field as clear
from fusion_baselines import coupled_coil_audit as independent
from fusion_baselines.clear_coil_geometry_audit import cases, physical_rows


def sources():
    return {
        label: {
            key: dict(path=f"/synthetic/{label}-{key}", sha256=str(i) * 64)
            for i, key in enumerate(("input", "wout"), 1)
        }
        for label in ("reference", "selected")
    }


def seed(nbase=6, order=5):
    coefficient = np.zeros((nbase, 3, 2 * order + 1))
    for i in range(nbase):
        phi = np.pi * (i + 0.5) / (2 * nbase)
        radius = 0.24 + 0.002 * i
        coefficient[i, 0, 0], coefficient[i, 1, 0] = 1.01 * np.cos(phi), 1.01 * np.sin(phi)
        coefficient[i, 0, 2], coefficient[i, 1, 2] = radius * np.cos(phi), radius * np.sin(phi)
        coefficient[i, 2, 1] = -radius
        coefficient[i, 0, 4], coefficient[i, 1, 4] = 0.003 * np.cos(phi), 0.003 * np.sin(phi)
        coefficient[i, 2, 5] = 0.001
    return dict(
        schema_version=1,
        kind="geometry-only",
        nfp=2,
        nbase=nbase,
        order=order,
        names=independent.parameter_names(nbase, order),
        base_coefficients=coefficient.tolist(),
        physical=physical_rows(nbase),
        case=next(c for c in cases() if c["label"] == f"n{nbase}-shape-d100mm"),
        sources=sources(),
        parameter_orientation="alpha=-2*pi*t",
    )


def target(wout, input_json, ninner):
    data = dict(
        nfp=2,
        mpol=3,
        ntor=1,
        lasym=False,
        phiedge=np.pi / 100,
        rbc=[dict(m=0, n=0, value=1.0), dict(m=1, n=0, value=0.10), dict(m=2, n=1, value=0.003)],
        zbs=[dict(m=1, n=0, value=0.10), dict(m=1, n=-1, value=0.002)],
    )
    phi, theta = np.meshgrid(
        np.pi * np.arange(ninner) / ninner, 2 * np.pi * np.arange(ninner) / ninner, indexing="ij"
    )
    points, fields = [], []
    for s in (0.25, 0.5, 0.75):
        radius = 1 + 0.10 * np.sqrt(s) * np.cos(theta)
        points.append(
            np.stack(
                (radius * np.cos(phi), radius * np.sin(phi), 0.10 * np.sqrt(s) * np.sin(theta)),
                axis=-1,
            ).reshape(-1, 3)
        )
        fields.append(
            np.stack(
                (-np.sin(phi) / radius, np.cos(phi) / radius, np.zeros_like(phi)), axis=-1
            ).reshape(-1, 3)
        )
    return dict(
        input=data,
        inner_points=np.concatenate(points),
        inner_target=np.concatenate(fields),
        target_flux=-np.pi / 100,
        sources=sources()["reference"],
    )


@pytest.fixture
def factory(monkeypatch):
    monkeypatch.setattr(clear, "load_target", target)

    def make(document=None, method="N", **kwargs):
        return clear.ClearCoilField(
            "/synthetic/reference-wout",
            "/synthetic/reference-input",
            seed() if document is None else document,
            method,
            3.25,
            **dict(ncoil=48, nphi=8, ntheta=12, **kwargs),
        )

    return make


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.update(kind="magnetic"),
        lambda s: s.update(scale=1.0),
        lambda s: s.update(nbase=True),
        lambda s: s.update(order=7),
        lambda s: s.update(schema_version=True),
        lambda s: s.update(parameter_orientation="alpha=2*pi*t"),
        lambda s: s["names"].reverse(),
        lambda s: s["base_coefficients"].pop(),
        lambda s: s["base_coefficients"][0][0].__setitem__(0, float("nan")),
        lambda s: s["base_coefficients"][0][0].__setitem__(0, "1.0"),
        lambda s: s["physical"].pop(),
        lambda s: s["physical"][0].update(current=1e5),
        lambda s: s["physical"][0].update(flip=0),
        lambda s: s["physical"][0]["matrix"][0].__setitem__(0, -1.0),
        lambda s: s["case"].update(d=0.14),
        lambda s: s["sources"].pop("selected"),
        lambda s: s["sources"]["reference"]["input"].update(path="relative"),
        lambda s: s["sources"]["reference"]["input"].update(sha256="wrong"),
    ],
)
def test_geometry_schema_mutations_fail_without_any_fields(mutation):
    document = seed()
    mutation(document)
    with pytest.raises((ValueError, TypeError)):
        clear.geometry_seed(document)


def test_geometry_document_has_no_caller_alias():
    document = seed()
    copied = clear.geometry_seed(document)
    document["base_coefficients"][0][0][0] += 1
    document["sources"]["reference"]["input"]["sha256"] = "f" * 64
    assert copied == seed()


class FakeNative:
    def __init__(self):
        self.requests = []

    def set_points(self, points):
        self.points = points

    def A(self):
        self.requests.append("A")
        return np.ones_like(self.points)

    def B(self):
        self.requests.append("B")
        raise ArithmeticError("synthetic native field error")

    def A_vjp(self, weights):
        self.requests.append("A_vjp")
        return weights.copy()

    def B_vjp(self, weights):
        self.requests.append("B_vjp")
        return weights.copy()


def test_counted_proxy_retains_requests_points_status_and_independent_callback_copies():
    native, events, emitted = FakeNative(), [], []
    proxy = clear.CountedField(native, "loop", events, emitted.append)
    points = np.zeros((5, 3))
    proxy.set_points(points)
    points[0] = 1
    assert not native.points.any()
    np.testing.assert_array_equal(proxy.A(), np.ones((5, 3)))
    weights = np.zeros((5, 3))
    proxy.A_vjp(weights)
    proxy.B_vjp(weights)
    with pytest.raises(ArithmeticError, match="synthetic"):
        proxy.B()
    assert native.requests == ["A", "A_vjp", "B_vjp", "B"]
    assert [e["status"] for e in events] == ["completed"] * 3 + ["error"]
    assert [e["status"] for e in emitted] == ["attempted", "completed"] * 3 + ["attempted", "error"]
    assert all(e["points"] == 5 and e["field"] == "loop" for e in events)
    assert events[-1]["native_started"] is True and events[-1]["native_completed"] is False
    assert events[-1]["error"] == "ArithmeticError: synthetic native field error"
    emitted[-1]["status"] = "tampered"
    assert events[-1]["status"] == "error"


def test_unpersisted_attempt_does_not_start_native_call():
    native, events = FakeNative(), []

    def fail(_):
        raise OSError("synthetic disk failure")

    proxy = clear.CountedField(native, "loop", events, fail)
    proxy.set_points(np.zeros((4, 3)))
    with pytest.raises(OSError, match="disk failure"):
        proxy.A()
    assert native.requests == []
    assert events[0]["status"] == "error" and events[0]["native_started"] is False


def test_completion_persistence_error_does_not_hide_performed_native_call():
    native, events = FakeNative(), []

    def fail(event):
        if event["status"] != "attempted":
            raise OSError("synthetic completion disk failure")

    proxy = clear.CountedField(native, "loop", events, fail)
    proxy.set_points(np.zeros((4, 3)))
    with pytest.raises(OSError, match="completion disk failure"):
        proxy.A()
    assert native.requests == ["A"]
    assert events[0]["status"] == "error" and events[0]["native_completed"] is True


@pytest.mark.parametrize("nbase,order", [(6, 5), (8, 7)])
@pytest.mark.parametrize("method", ["N", "V"])
def test_direct_clear_initialization_native_mapping_and_frozen_objective(
    factory, monkeypatch, nbase, order, method
):
    def no_circle(*args, **kwargs):
        pytest.fail("old circular constructor must never be called")

    monkeypatch.setattr(clear.CoupledCoils, "__init__", no_circle)
    emitted, document = [], seed(nbase, order)
    model = factory(document, method, event_callback=emitted.append)
    assert np.array_equal(model.seed_x, np.ravel(document["base_coefficients"]))
    assert len(model.native_calls) == 1 and model.native_calls[0]["quantity"] == "A"
    assert model.native_calls[0]["points"] == 256 and model.native_calls[0]["status"] == "completed"
    assert [e["status"] for e in emitted] == ["attempted", "completed"]
    assert model.initialization_work == dict(seed_A_calls=1, seed_A_points=256)
    assert model.geometry_surface.gamma().shape == (128, 128, 3)
    assert model.B2_scale == 3.25
    assert model.B2_scale != np.mean(np.sum(model.inner_target**2, axis=1))
    value, gradient, metrics = model.evaluate(model.seed_x)
    snapshot, arrays = model.snapshot(model.seed_x), model.arrays(model.seed_x)
    independent.validate_snapshot(snapshot)
    assert snapshot["seed_geometry"] == document
    assert snapshot["construction"]["geometry_full_torus"] is True
    assert snapshot["construction"]["geometry_nphi"] == 128
    assert snapshot["construction"]["geometry_ntheta"] == 128
    assert snapshot["seed_unit_flux"] == model.seed_unit_flux == metrics["unit_flux"]
    assert len(model.native_calls) == 7  # One initialization plus3 values and3 VJPs.
    assert [e["quantity"] for e in model.native_calls] == [
        "A",
        "B",
        "B",
        "A",
        "B_vjp",
        "B_vjp",
        "A_vjp",
    ]
    assert np.isfinite(gradient).all() and gradient.shape == model.seed_x.shape
    expected_value = metrics["JN"] + metrics["geometry_penalty"]
    if method == "V":
        expected_value += 0.05 * metrics["JV"]
    assert value == expected_value
    curves = independent.physical_curves(snapshot, model.ncoil)
    for key in ("positions", "tangents", "currents"):
        np.testing.assert_allclose(curves[key], arrays[f"coil_{key}"], rtol=2e-13, atol=2e-14)
    assert all(
        current.get_value() == 1e5 and current.local_dof_size == 0
        for current in model.base_currents
    )
    for grid, quantity, component in (("boundary", "B", 0), ("inner", "B", 0), ("loop", "A", 1)):
        selected = np.linspace(0, len(arrays[f"{grid}_points"]) - 1, 8, dtype=int)
        own = independent.direct_field(
            snapshot, arrays[f"{grid}_points"][selected], ncoil=model.ncoil
        )[component]
        np.testing.assert_allclose(
            own, arrays[f"{grid}_{quantity}"][selected], rtol=2e-12, atol=1e-13
        )
    json.dumps(snapshot, allow_nan=False)
    # No native work is hidden by same-state serialization or caller mutation.
    document["base_coefficients"][0][0][0] += 0.1
    snapshot["seed_geometry"]["base_coefficients"][0][0][0] += 0.1
    assert model.snapshot(model.seed_x)["seed_geometry"] == seed(nbase, order)
    model.arrays(model.seed_x)
    assert len(model.native_calls) == 7


def test_seed_is_loaded_before_first_potential_call(factory, monkeypatch):
    from simsopt import field

    original, observed = field.BiotSavart, []

    def tracking(coils):
        native = original(coils)
        old_a = native.A

        def a():
            observed.append(np.concatenate([c.curve.local_full_x for c in coils[:6]]))
            return old_a()

        native.A = a
        return native

    monkeypatch.setattr(field, "BiotSavart", tracking)
    model = factory()
    assert len(observed) == 1
    np.testing.assert_array_equal(observed[0], model.seed_x)


def test_snapshot_sources_have_no_model_or_seed_alias(factory):
    model = factory()
    snapshot = model.snapshot(model.seed_x)
    work_before = len(model.native_calls)
    snapshot["sources"]["input"]["sha256"] = "f" * 64
    snapshot["sources"]["wout"]["path"] = "/synthetic/tampered-wout"
    assert model.target["sources"] == sources()["reference"]
    repeated = model.snapshot(model.seed_x)
    assert repeated["sources"] == sources()["reference"]
    assert repeated["seed_geometry"]["sources"] == sources()
    assert len(model.native_calls) == work_before


def test_frozen_diagnostics_do_not_renormalize_or_generate_fine_snapshot(factory):
    coarse = factory()
    coarse.evaluate(coarse.seed_x)
    snapshot = coarse.snapshot(coarse.seed_x)
    fine = factory(ninner=64)
    assert fine.B2_scale == snapshot["B2_scale"] == 3.25
    frozen = fine.diagnostics(fine.seed_x, snapshot["scale"] * 1.1, snapshot["B2_scale"])
    assert frozen["scale"] == snapshot["scale"] * 1.1
    assert frozen["B2_scale"] == 3.25
    assert frozen["frozen_scale"] is True
    fine.arrays(fine.seed_x, snapshot["scale"] * 1.1, snapshot["B2_scale"])
    assert len(fine.native_calls) == 4
    with pytest.raises(ValueError, match="original construction"):
        fine.snapshot(fine.seed_x, snapshot["scale"], snapshot["B2_scale"])
    for method in (fine.diagnostics, fine.arrays, fine.snapshot):
        with pytest.raises(ValueError, match="exactly frozen"):
            method(fine.seed_x, snapshot["scale"], 6.5)
    with pytest.raises(AttributeError):
        fine.B2_scale = 6.5


@pytest.mark.parametrize("nbase,order", [(6, 5), (8, 7)])
def test_fresh_method_models_have_same_physics_and_exact_repeat(factory, nbase, order):
    models = [factory(seed(nbase, order), method) for method in ("N", "V")]
    rows = [model.evaluate(model.seed_x) for model in models]
    for name in rows[0][2].keys() - {"J"}:
        assert rows[0][2][name] == rows[1][2][name]
    a, b = [model.arrays(model.seed_x) for model in models]
    assert all(np.array_equal(a[key], b[key]) for key in a)
    for model, original in zip(models, rows, strict=True):
        x = model.seed_x.copy()
        direction = np.sin(np.arange(x.size) + 1)
        direction /= np.linalg.norm(direction)
        for step in (1e-5, 5e-6):
            plus = model.evaluate(x + step * direction)[0]
            minus = model.evaluate(x - step * direction)[0]
            assert (plus - minus) / (2 * step) == pytest.approx(
                original[1] @ direction, rel=2e-4, abs=1e-8
            )
        repeated = model.evaluate(x)
        assert repeated[0] == original[0] and np.array_equal(repeated[1], original[1])
        assert repeated[2] == original[2]


def test_bound_source_mutation_rejected_before_potential(factory, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("source failure must precede any coil field work")

    monkeypatch.setattr(clear.CountedField, "A", forbidden)
    document = seed()
    document["sources"]["reference"]["input"]["sha256"] = "f" * 64
    with pytest.raises(ValueError, match="bound geometry target"):
        factory(document)


@pytest.mark.parametrize("b2", [0, -1, float("nan"), float("inf"), True, [3.25], "3.25"])
def test_invalid_B2_rejected_before_target_loading(monkeypatch, b2):
    monkeypatch.setattr(clear, "load_target", lambda *args: pytest.fail("target load forbidden"))
    with pytest.raises(ValueError, match="B2"):
        clear.ClearCoilField("unused", "unused", seed(), "N", b2)


def test_changed_native_free_masks_rejected_before_A(factory, monkeypatch):
    from simsopt import geo

    original = geo.CurveXYZFourier

    def fixed(*args, **kwargs):
        curve = original(*args, **kwargs)
        curve.fix("xc(0)")
        return curve

    monkeypatch.setattr(geo, "CurveXYZFourier", fixed)
    with pytest.raises(ValueError, match="names/free masks"):
        factory()


def test_degenerate_initial_flux_still_has_one_counted_attempt(factory, monkeypatch):
    from simsopt import field

    original, emitted = field.BiotSavart, []

    def zero(coils):
        native = original(coils)
        native.A = lambda: np.zeros((256, 3))
        return native

    monkeypatch.setattr(field, "BiotSavart", zero)
    with pytest.raises(ValueError, match="flux degenerate"):
        factory(event_callback=emitted.append)
    assert len(emitted) == 2 and emitted[0]["status"] == "attempted"
    assert emitted[1]["status"] == "completed" and emitted[1]["quantity"] == "A"
