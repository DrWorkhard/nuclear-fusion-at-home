"""Stub all native/certificate bridges; no new project fields or certificates."""

import copy
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest
from test_protected_cell_contract import bundle_fixture, context_fixture, model_fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import protected_native_adapter as native  # noqa: E402


def test_lazy_bridges_forward_exact_frozen_apis_without_importing_native_code(monkeypatch):
    calls = []
    legacy = ModuleType("run_clear_coil_field_start")
    perturbation = ModuleType("fusion_baselines.coil_perturbation")

    def record(name):
        def call(*args):
            calls.append((name, args))
            return name

        return call

    legacy.make_model = record("initialize")
    legacy.execute = record("bundle")
    perturbation.candidate_certificate = record("certificate")
    monkeypatch.setitem(sys.modules, legacy.__name__, legacy)
    monkeypatch.setitem(sys.modules, perturbation.__name__, perturbation)
    arguments = tuple(object() for _ in range(5))
    assert native._make_model(*arguments) == "initialize"
    assert native._execute(*arguments[:2]) == "bundle"
    assert native._certify(*arguments[:3]) == "certificate"
    assert calls == [
        ("initialize", arguments),
        ("bundle", (*arguments[:2], None)),
        ("certificate", arguments[:3]),
    ]


def fixture(monkeypatch, nbase=6, method="N", target="reference"):
    context = context_fixture(nbase, method, target)
    source = dict(
        cell_sources=dict(marker="original archived sources"),
        plumbing={},
        repository=dict(commit="test"),
    )
    calls = dict(models=[], certificates=[], bundles=[])
    monkeypatch.setattr(native, "build_context", lambda source, case: copy.deepcopy(context))

    def make_model(source, case, spec, seed, callback):
        calls["models"].append(
            (copy.deepcopy(source), copy.deepcopy(case), copy.deepcopy(spec), copy.deepcopy(seed))
        )
        callback(dict(status="synthetic-initialization-request"))
        return model_fixture(context)

    def execute(model, operation):
        calls["bundles"].append(copy.deepcopy(operation))
        model.x = operation["x"].copy()
        bundle = bundle_fixture(context, operation["x"])
        model._cache = dict(computed=True)
        return dict(
            J=np.float64(bundle["state"]["value"]),
            gradient=np.asarray(bundle["state"]["gradient"]),
            metrics=bundle["state"]["metrics"],
            snapshot_data=bundle["snapshot"],
        ), bundle["arrays"]

    def certify(seed, report, candidate):
        calls["certificates"].append((copy.deepcopy(seed), copy.deepcopy(report), candidate.copy()))
        return dict(certified=True, calculation_complete=True, status="certified")

    monkeypatch.setattr(native, "_make_model", make_model)
    monkeypatch.setattr(native, "_execute", execute)
    monkeypatch.setattr(native, "_certify", certify)
    return context, source, calls


@pytest.mark.parametrize("nbase", [6, 8])
@pytest.mark.parametrize("method", ["N", "V"])
@pytest.mark.parametrize("target", ["reference", "selected"])
def test_all_eight_native_specs_and_complete_json_conversion(monkeypatch, nbase, method, target):
    context, source, calls = fixture(monkeypatch, nbase, method, target)
    adapter = native.NativeAdapter(context, source)
    events = []
    main, replay = adapter.initialize(events.append), adapter.initialize(events.append)
    assert main is not replay
    assert len(events) == 2
    for forwarded, case, spec, seed in calls["models"]:
        assert forwarded == source["cell_sources"] and case == context["case"]
        assert spec == dict(
            method=method, grid=dict(ncoil=256, nphi=64, ntheta=64, ninner=32, offset=0)
        )
        assert seed == context["seed"]
    x = np.asarray(context["seed"]["base_coefficients"]).ravel()
    candidate = x.copy()
    candidate[0] += 1e-4
    adapter.certificate(x, candidate)
    original, report, coefficients = calls["certificates"][0]
    assert original == context["seed"] and report == context["geometry_report"]
    np.testing.assert_array_equal(coefficients.ravel(), candidate)
    main._cache = {"old": True}
    adapter.invalidate(main)
    assert main._cache is None
    result = adapter.bundle(main, candidate)
    assert type(result["state"]["x"]) is list
    assert type(result["state"]["gradient"]) is list
    assert type(result["state"]["value"]) is float
    assert len(result["arrays"]) == 16
    assert calls["bundles"][0]["kind"] == "qualification"
    assert len(calls["bundles"]) == 1


def test_constructor_rejects_context_not_owned_by_source_manifest(monkeypatch):
    context, source, _ = fixture(monkeypatch)
    supplied = copy.deepcopy(context)
    supplied["seed_reference"]["sha256"] = "b" * 64
    with pytest.raises(ValueError, match="source-bound context"):
        native.NativeAdapter(supplied, source)


def test_constructor_rejects_historical_array_substitution(monkeypatch):
    context, source, _ = fixture(monkeypatch)
    supplied = copy.deepcopy(context)
    supplied["historical_seed"]["arrays"]["boundary_B"][0, 0] = 1.0
    with pytest.raises(ValueError, match="exact replay array"):
        native.NativeAdapter(supplied, source)


def test_caller_mutations_cannot_change_bound_sources_or_seed(monkeypatch):
    context, source, calls = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)
    source["cell_sources"]["marker"] = "changed"
    context["seed"]["base_coefficients"][0][0][0] = 7.0
    # The stub model uses context too; replace only its source with a private copy.
    bound = copy.deepcopy(adapter._context)
    monkeypatch.setattr(native, "_make_model", lambda *args: model_fixture(bound))
    model = adapter.initialize(lambda event: None)
    assert model.seed_x[0] == 1.0
    assert adapter._source["cell_sources"]["marker"] == "original archived sources"
    assert calls["models"] == []


def test_third_model_or_reused_model_is_forbidden(monkeypatch):
    context, source, _ = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)
    adapter.initialize(lambda event: None)
    adapter.initialize(lambda event: None)
    with pytest.raises(ValueError, match="only original"):
        adapter.initialize(lambda event: None)
    assert adapter._failed
    other = native.NativeAdapter(context, source)
    first = other.initialize(lambda event: None)
    monkeypatch.setattr(native, "_make_model", lambda *args: first)
    with pytest.raises(ValueError, match="distinct"):
        other.initialize(lambda event: None)


@pytest.mark.parametrize("mutation", ["claimed-seed", "actual-x", "cache", "source", "method"])
def test_wrong_initialized_native_model_is_rejected(monkeypatch, mutation):
    context, source, _ = fixture(monkeypatch)
    model = model_fixture(context)
    if mutation == "claimed-seed":
        model.seed_x[0] += 1e-3
    elif mutation == "actual-x":
        model.x[0] += 1e-3
    elif mutation == "cache":
        model._cache = {}
    elif mutation == "source":
        model.target = dict(sources={})
    else:
        model.method = "V"
    monkeypatch.setattr(native, "_make_model", lambda *args: model)
    with pytest.raises(ValueError):
        native.NativeAdapter(context, source).initialize(lambda event: None)


@pytest.mark.parametrize("mutation", ["prior-seed", "shape", "inactive", "boolean"])
def test_certificate_never_resets_original_seed_or_parameter_mapping(monkeypatch, mutation):
    context, source, calls = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)
    seed = np.asarray(context["seed"]["base_coefficients"]).ravel()
    candidate = seed.copy()
    if mutation == "prior-seed":
        seed[0] += 1e-4
    elif mutation == "shape":
        candidate = candidate[:-1]
    elif mutation == "inactive":
        candidate[5] += 1e-4
    else:
        candidate = [False] * len(candidate)
    with pytest.raises(ValueError):
        adapter.certificate(seed, candidate)
    assert calls["certificates"] == [] and adapter._failed


def test_negative_certificate_is_returned_without_field_work(monkeypatch):
    context, source, calls = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)
    monkeypatch.setattr(
        native,
        "_certify",
        lambda *args: dict(certified=False, calculation_complete=True, status="uncertified"),
    )
    seed = np.asarray(context["seed"]["base_coefficients"]).ravel()
    result = adapter.certificate(seed, seed)
    assert result["certified"] is False and not adapter._failed and calls["bundles"] == []


@pytest.mark.parametrize("mutation", ["cache", "foreign-model", "method", "source", "grid", "seed"])
def test_changed_live_identity_or_missing_invalidation_blocks_field_dispatch(monkeypatch, mutation):
    context, source, calls = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)
    model = adapter.initialize(lambda event: None)
    if mutation == "cache":
        model._cache = {"stale": True}
    elif mutation == "foreign-model":
        model = model_fixture(context)
    elif mutation == "method":
        model.method = "V"
    elif mutation == "source":
        model.target = dict(sources={})
    elif mutation == "grid":
        model.ncoil = 512
    else:
        model.seed_x[0] += 1e-4
    with pytest.raises(ValueError):
        adapter.bundle(model, np.asarray(context["seed"]["base_coefficients"]).ravel())
    assert calls["bundles"] == [] and adapter._failed


@pytest.mark.parametrize(
    "mutation",
    [
        "record-key",
        "array-missing",
        "array-shape",
        "method",
        "coordinates",
        "model-coordinates",
        "metadata-bool",
    ],
)
def test_incomplete_or_mismatched_legacy_bundle_fails_closed(monkeypatch, mutation):
    context, source, calls = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)
    model = adapter.initialize(lambda event: None)
    execute = native._execute

    def bad(model, operation):
        record, arrays = execute(model, operation)
        if mutation == "record-key":
            record["unregistered"] = True
        elif mutation == "array-missing":
            arrays.pop("boundary_A")
        elif mutation == "array-shape":
            arrays["inner_B"] = arrays["inner_B"][:-1]
        elif mutation == "method":
            record["snapshot_data"]["method"] = "V"
        elif mutation == "coordinates":
            record["snapshot_data"]["base_coefficients"][0][0][0] += 1e-3
        elif mutation == "model-coordinates":
            model.x[0] += 1e-3
        else:
            record["metrics"]["current"] = True
        return record, arrays

    monkeypatch.setattr(native, "_execute", bad)
    with pytest.raises(ValueError):
        adapter.bundle(model, model.seed_x)
    with pytest.raises(RuntimeError, match="failed"):
        adapter.invalidate(model)
    assert len(calls["bundles"]) == 1


def test_callback_failure_remains_poison_even_if_factory_swallows_it(monkeypatch):
    context, source, _ = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)

    def swallowed(source, case, spec, seed, callback):
        try:
            callback({})
        except OSError:
            pass
        return model_fixture(context)

    def callback(event):
        raise OSError("failed native reservation")

    monkeypatch.setattr(native, "_make_model", swallowed)
    with pytest.raises(RuntimeError, match="callback failed"):
        adapter.initialize(callback)
    assert adapter._failed


def test_swallowed_callback_failure_blocks_subsequent_callback(monkeypatch):
    context, source, _ = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)
    events = []

    def swallowed(source, case, spec, seed, callback):
        for event in (1, 2):
            try:
                callback(dict(request=event))
            except (OSError, RuntimeError):
                pass
        return model_fixture(context)

    def callback(event):
        events.append(event)
        raise OSError("failed native reservation")

    monkeypatch.setattr(native, "_make_model", swallowed)
    with pytest.raises(RuntimeError, match="callback failed"):
        adapter.initialize(callback)
    assert events == [dict(request=1)]


@pytest.mark.parametrize("key", ["B2_scale", "target_flux", "seed_unit_flux"])
@pytest.mark.parametrize("convert", [str, np.asarray])
def test_fixed_normalization_scalar_types_cannot_drift(monkeypatch, key, convert):
    context, source, calls = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)
    model = adapter.initialize(lambda event: None)
    setattr(model, key, convert(getattr(model, key)))
    with pytest.raises(ValueError, match="real fixed model"):
        adapter.invalidate(model)
    assert calls["bundles"] == [] and adapter._failed


def test_adapter_reentrancy_poison_cannot_be_swallowed_by_factory(monkeypatch):
    context, source, _ = fixture(monkeypatch)
    adapter = native.NativeAdapter(context, source)

    def reenter(source, case, spec, seed, callback):
        try:
            adapter.initialize(callback)
        except ValueError:
            pass
        return model_fixture(context)

    monkeypatch.setattr(native, "_make_model", reenter)
    with pytest.raises(RuntimeError, match="callback failed"):
        adapter.initialize(lambda event: None)
    assert adapter._failed
