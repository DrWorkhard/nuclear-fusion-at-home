"""Instrumented models only: no native fields, model constructors or certificates."""

import copy
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest
from test_protected_cell_contract import bundle_fixture, context_fixture

from fusion_baselines import protected_fine_native as native
from fusion_baselines import protected_fine_plan as plan


@pytest.fixture(autouse=True)
def single_thread(monkeypatch):
    for name in native.THREADS:
        monkeypatch.setenv(name, "1")


def inputs(nbase=6, method="N", target="reference", changed=True):
    original = context_fixture(nbase, method, target)
    x = np.asarray(original["seed"]["base_coefficients"]).ravel().copy()
    if changed:
        x[0] += 0.001
    selected = bundle_fixture(original, x, current=234567.0)

    def ref(name):
        return dict(path="/synthetic/fine/" + name + ".json", sha256="a" * 64, bytes=123)

    coarse = {
        name: ref(name)
        for name in (
            "case_record",
            "parent_acknowledgement",
            "cell_result",
            "independent_reconstruction",
            "selected_bundle",
            "selected_snapshot",
            "selected_certificate",
        )
    }
    context = dict(
        case=original["case"],
        original_context=original,
        coarse=coarse,
        selected=dict(selected, certificate=dict(synthetic=True)),
    )
    source = dict(
        targets=original["seed"]["sources"],
        normalization={
            label: dict(B2_scale=original["B2_scale"]) for label in ("reference", "selected")
        },
    )
    archive = dict(
        archived_source=dict(physics_sources=dict(native_sources=dict(cell_sources=source)))
    )
    return context, archive


class Current:
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value


class Model:
    def __init__(self, context, spec, callback):
        original, seed = context["original_context"], context["original_context"]["seed"]
        self.spec, self.callback = copy.deepcopy(spec), callback
        self.names = seed["names"].copy()
        self.local_names = [
            name.split("/", 1)[1] for name in self.names[: 3 * (2 * seed["order"] + 1)]
        ]
        self._seed_geometry = copy.deepcopy(seed)
        self.seed_x = np.asarray(seed["base_coefficients"]).ravel().copy()
        self._x, self._cache = self.seed_x.copy(), None
        self.assignments, self.native_calls = [], []
        self.nbase, self.order, self.nfp = seed["nbase"], seed["order"], 2
        self.method = spec["method"]
        for key, value in spec["grid"].items():
            setattr(self, key, value)
        self.target = dict(sources=copy.deepcopy(original["target_sources"]))
        self.B2_scale = original["B2_scale"]
        self.target_flux = context["selected"]["snapshot"]["target_flux"]
        # A deliberately resolution-dependent original seed scalar. This must
        # stay separate from the selected snapshot's frozen coarse unit flux.
        self.seed_unit_flux = 0.125 if self.ncoil == 256 else 0.124
        self.initialization_work = dict(seed_A_calls=1, seed_A_points=256)
        self.base_currents = [Current(100000.0) for _ in range(self.nbase)]
        self.coils = [
            SimpleNamespace(current=Current(-100000.0 if r["flip"] else 100000.0))
            for r in seed["physical"]
        ]
        self.request("loop", "A", 256)

    @property
    def x(self):
        return self._x.copy()

    @x.setter
    def x(self, value):
        self.assignments.append(np.asarray(value).copy())
        self._x = np.asarray(value).copy()
        self._cache = None

    def snapshot(self, *args, **kwargs):
        pytest.fail("fine diagnostics must never request/recalibrate a snapshot")

    def evaluate(self, *args, **kwargs):
        pytest.fail("fine work must never dispatch a gradient or unscaled construction bundle")

    def request(self, field, quantity, points):
        event = dict(
            index=len(self.native_calls),
            field=field,
            quantity=quantity,
            points=points,
            status="attempted",
            native_started=False,
            native_completed=False,
        )
        self.native_calls.append(event)
        self.callback(copy.deepcopy(event))
        event.update(status="completed", native_started=True, native_completed=True)
        self.callback(copy.deepcopy(event))


def raw_arrays(spec, op, snapshot):
    if spec["kind"] == "diagnostic":
        b, i, n = (
            spec["grid"]["nphi"] * spec["grid"]["ntheta"],
            3 * spec["grid"]["ninner"] ** 2,
            256,
        )
        shapes = dict(
            boundary_points=(b, 3),
            boundary_normals=(b, 3),
            boundary_weights=(b,),
            boundary_B=(b, 3),
            boundary_A=(b, 3),
            inner_points=(i, 3),
            inner_target=(i, 3),
            inner_B=(i, 3),
            inner_A=(i, 3),
            loop_points=(n, 3),
            loop_tangents=(n, 3),
            loop_A=(n, 3),
            loop_B=(n, 3),
            coil_positions=(4 * spec["case"]["nbase"], spec["grid"]["ncoil"], 3),
            coil_tangents=(4 * spec["case"]["nbase"], spec["grid"]["ncoil"], 3),
        )
        raw = {key: np.zeros(shape) for key, shape in shapes.items()}
        raw["coil_currents"] = np.array([row["current"] for row in snapshot["physical"]])
        return raw
    shape = (op["ntheta"] * op.get("nrho", 1), 3)
    return {
        key: np.zeros(shape)
        for key in ("points", "A", "B", "tangents" if op["form"] == "line" else "weighted_normals")
    }


def setup(monkeypatch, nbase=6, method="N", target="reference", changed=True):
    context, archive = inputs(nbase, method, target, changed)
    bound = copy.deepcopy(context)
    calls = dict(build=[], initialize=[], execute=[], models=[], raw=[])

    def build(source, case):
        calls["build"].append((source, case))
        return copy.deepcopy(bound)

    def make(source, case, spec, seed, callback):
        calls["initialize"].append(
            (copy.deepcopy(source), copy.deepcopy(case), copy.deepcopy(spec), copy.deepcopy(seed))
        )
        model = Model(bound, spec, callback)
        calls["models"].append(model)
        return model

    def execute(model, operation, frozen):
        snapshot, reference = frozen
        # Legacy flux does not assign x: assert the adapter did so BEFORE entry.
        np.testing.assert_array_equal(model.x, np.asarray(bound["selected"]["state"]["x"]))
        assert model.assignments and model._cache is None
        assert snapshot == bound["selected"]["snapshot"]
        assert reference == bound["coarse"]["selected_snapshot"]
        calls["execute"].append((model, copy.deepcopy(operation), copy.deepcopy(frozen)))
        for field, quantity, points in plan.expected_calls(model.spec, operation):
            model.request(field, quantity, points)
        record = dict(
            snapshot=copy.deepcopy(reference),
            **{key: snapshot[key] for key in ("scale", "B2_scale", "target_flux")},
        )
        if operation["kind"] == "diagnostic":
            record["metrics"] = dict(
                copy.deepcopy(bound["selected"]["state"]["metrics"]), frozen_scale=True
            )
        else:
            record["flux"] = 0.0
        raw = raw_arrays(model.spec, operation, snapshot)
        calls["raw"].append(raw)
        model._cache = {"fine": True}
        return record, raw

    monkeypatch.setattr(native, "_build_context", build)
    monkeypatch.setattr(native, "_make_model", make)
    monkeypatch.setattr(native, "_execute", execute)
    return context, archive, calls


@pytest.mark.parametrize("case", plan.cases(), ids=lambda case: case["label"])
@pytest.mark.parametrize("changed", [False, True])
def test_all_cases_eight_models_full_operation_schedule(monkeypatch, case, changed):
    context, archive, calls = setup(
        monkeypatch, case["nbase"], case["method"], case["target"], changed
    )
    adapter = native.FineNativeAdapter(context, archive)
    events, models = [], []
    for spec in plan.model_plan(case):
        model = adapter.initialize(spec, events.append)
        models.append(model)
        metadata = adapter.metadata(model)
        assert model.assignments == []
        assert metadata["original_seed_unit_flux"] == (
            0.125 if spec["grid"]["ncoil"] == 256 else 0.124
        )
        assert metadata["original_seed_unit_flux"] != context["selected"]["snapshot"]["unit_flux"]
        assert metadata["initializer_physical_currents"] == [
            -100000.0 if row["flip"] else 100000.0
            for row in context["original_context"]["seed"]["physical"]
        ]
        for operation in plan.operation_plan(spec, context["selected"]["state"]["x"]):
            model._x = model.seed_x.copy()  # Stale flux x must never survive into execute.
            model._cache = {"old": True}
            result = adapter.execute(model, operation)
            assert set(result) == {"record", "arrays", "metadata"}
            assert result["record"]["snapshot"] == context["coarse"]["selected_snapshot"]
            assert result["metadata"]["complete_execution"] is False
            assert result["metadata"]["fine_numerical_qualification"] is False
            assert result["record"]["scale"] == context["selected"]["snapshot"]["scale"]
    assert len({id(model) for model in models}) == 8
    assert (
        len(calls["build"]) == 1 and len(calls["initialize"]) == 8 and len(calls["execute"]) == 24
    )
    assert len(events) == 160 and sum(len(model.native_calls) for model in models) == 80
    assert sum(event["points"] for event in events if event["status"] == "attempted") == 552960
    assert all(row[3] == context["original_context"]["seed"] for row in calls["initialize"])
    assert all(row[2]["method"] == case["method"] for row in calls["initialize"])


@pytest.mark.parametrize(
    "mutation", ["case", "seed", "selected-x", "snapshot-current", "source", "arrays", "reference"]
)
def test_supplied_context_substitution_fails_before_any_native_model(monkeypatch, mutation):
    context, archive, calls = setup(monkeypatch)
    if mutation == "case":
        context["case"] = plan.cases()[1]
    elif mutation == "seed":
        context["original_context"]["seed"]["base_coefficients"][0][0][0] += 1.0
    elif mutation == "selected-x":
        context["selected"]["state"]["x"][0] += 1e-3
    elif mutation == "snapshot-current":
        context["selected"]["snapshot"]["physical"][0]["current"] += 1
    elif mutation == "source":
        context["original_context"]["target_sources"]["input"]["sha256"] = "b" * 64
    elif mutation == "arrays":
        context["selected"]["arrays"]["boundary_B"][0, 0] += 1
    else:
        context["coarse"]["selected_snapshot"]["sha256"] = "b" * 64
    with pytest.raises(ValueError):
        native.FineNativeAdapter(context, archive)
    assert not calls["initialize"]


@pytest.mark.parametrize(
    "mutation",
    [
        "actual-x",
        "seed-x",
        "method",
        "target",
        "grid",
        "B2",
        "flux-array",
        "base-current",
        "physical-current",
        "cache",
        "calls",
        "local-names",
    ],
)
def test_initialized_model_identity_checked_before_use(monkeypatch, mutation):
    context, archive, calls = setup(monkeypatch)
    original = native._make_model

    def bad(*args):
        model = original(*args)
        if mutation == "actual-x":
            model._x[0] += 1
        elif mutation == "seed-x":
            model.seed_x[0] += 1
        elif mutation == "method":
            model.method = "V"
        elif mutation == "target":
            model.target["sources"] = {}
        elif mutation == "grid":
            model.ncoil = 512
        elif mutation == "B2":
            model.B2_scale = True
        elif mutation == "flux-array":
            model.seed_unit_flux = np.asarray(model.seed_unit_flux)
        elif mutation == "base-current":
            model.base_currents[0].value = 1.0
        elif mutation == "physical-current":
            model.coils[-1].current.value *= -1
        elif mutation == "cache":
            model._cache = {"hidden-work": True}
        elif mutation == "calls":
            model.native_calls[0]["points"] = 1
        else:
            model.local_names.reverse()
        return model

    monkeypatch.setattr(native, "_make_model", bad)
    adapter = native.FineNativeAdapter(context, archive)
    with pytest.raises(ValueError):
        adapter.initialize(plan.model_plan(context["case"])[0], lambda event: None)
    assert adapter._failed and not calls["execute"]


def initialized(monkeypatch, index=0):
    context, archive, calls = setup(monkeypatch)
    adapter = native.FineNativeAdapter(context, archive)
    spec = plan.model_plan(context["case"])[index]
    model = adapter.initialize(spec, lambda event: None)
    operation = plan.operation_plan(spec, context["selected"]["state"]["x"])[0]
    return adapter, model, operation, context, calls


@pytest.mark.parametrize("index", [0, 6])
def test_ignored_selected_assignment_stops_before_execute(monkeypatch, index):
    adapter, model, operation, _, calls = initialized(monkeypatch, index)
    monkeypatch.setattr(Model, "x", property(lambda self: self._x.copy(), lambda self, x: None))
    with pytest.raises(ValueError, match="installed before"):
        adapter.execute(model, operation)
    assert calls["execute"] == []


@pytest.mark.parametrize(
    "mutation",
    ["foreign-model", "operation-kind", "coordinates", "current", "seed-flux", "source", "method"],
)
def test_live_changes_block_native_dispatch(monkeypatch, mutation):
    adapter, model, op, _, calls = initialized(monkeypatch, 6)
    if mutation == "foreign-model":
        model = copy.copy(model)
    elif mutation == "operation-kind":
        op["kind"] = "qualification"
    elif mutation == "coordinates":
        op["x"][0] += 1
    elif mutation == "current":
        model.base_currents[0].value *= 2
    elif mutation == "seed-flux":
        model.seed_unit_flux += 1
    elif mutation == "source":
        model.target["sources"] = {}
    else:
        model.method = "V"
    with pytest.raises(ValueError):
        adapter.execute(model, op)
    assert calls["execute"] == []


@pytest.mark.parametrize(
    "mutation",
    [
        "selected-x",
        "scale",
        "snapshot",
        "current",
        "missing-array",
        "array-shape",
        "array-bool",
        "array-nan",
        "missing-metric",
        "recalibration",
    ],
)
def test_incomplete_or_changed_output_poison_adapter(monkeypatch, mutation):
    adapter, model, op, _, _ = initialized(monkeypatch)
    original = native._execute

    def bad(*args):
        record, raw = original(*args)
        if mutation == "selected-x":
            model._x[0] += 1
        elif mutation == "scale":
            record["scale"] *= 2
        elif mutation == "snapshot":
            record["snapshot"]["sha256"] = "b" * 64
        elif mutation == "current":
            raw["coil_currents"][0] += 1
        elif mutation == "missing-array":
            raw.pop("boundary_A")
        elif mutation == "array-shape":
            raw["boundary_A"] = raw["boundary_A"][:-1]
        elif mutation == "array-bool":
            raw["boundary_A"] = raw["boundary_A"].astype(bool)
        elif mutation == "array-nan":
            raw["boundary_A"][0, 0] = np.nan
        elif mutation == "missing-metric":
            record["metrics"].pop("normal_rms")
        else:
            record["metrics"]["frozen_scale"] = False
        return record, raw

    monkeypatch.setattr(native, "_execute", bad)
    with pytest.raises(ValueError):
        adapter.execute(model, op)
    with pytest.raises(RuntimeError):
        adapter.metadata(model)


def test_array_dtypes_bits_and_returned_containers_are_private(monkeypatch):
    adapter, model, op, context, _ = initialized(monkeypatch, 6)
    original = native._execute
    saved = []

    def mixed(*args):
        record, raw = original(*args)
        raw["points"] = raw["points"].astype(np.float32)
        raw["tangents"] = raw["tangents"].astype(np.int16)
        raw["A"][0, 0] = -0.0
        saved.append(raw)
        return record, raw

    monkeypatch.setattr(native, "_execute", mixed)
    result = adapter.execute(model, op)
    for key, raw in saved[0].items():
        assert result["arrays"][key].dtype == raw.dtype
        assert result["arrays"][key].tobytes() == raw.tobytes()
        assert not np.shares_memory(result["arrays"][key], raw)
    result["metadata"]["names"][0] = "caller mutation"
    context["selected"]["snapshot"]["scale"] = 100
    assert adapter.metadata(model)["names"][0] != "caller mutation"
    assert adapter.metadata(model)["scale"] != 100


def test_model_or_operation_reuse_and_out_of_order_flux_are_rejected(monkeypatch):
    adapter, model, op, context, _ = initialized(monkeypatch)
    adapter.execute(model, op)
    with pytest.raises(ValueError, match="exhausted"):
        adapter.execute(model, op)
    adapter, model, op, context, _ = initialized(monkeypatch, 6)
    op = plan.operation_plan(model.spec, context["selected"]["state"]["x"])[1]
    with pytest.raises(ValueError, match="ordered"):
        adapter.execute(model, op)
    adapter, model, _, _, _ = initialized(monkeypatch)
    with pytest.raises(ValueError, match="distinct"):
        adapter.initialize(model.spec, lambda event: None)


@pytest.mark.parametrize("during", ["initialization", "operation"])
@pytest.mark.parametrize("fault", ["raise", "swallowed-reentry"])
def test_callback_error_or_swallowed_reentry_permanently_poison(monkeypatch, during, fault):
    context, archive, _ = setup(monkeypatch)
    adapter = native.FineNativeAdapter(context, archive)
    spec = plan.model_plan(context["case"])[0]
    events, active = [], [during == "initialization"]

    def callback(event):
        events.append(event)
        if active[0]:
            if fault == "raise":
                raise OSError("injected caller native ledger failure")
            with pytest.raises(ValueError, match="reentrant"):
                adapter.initialize(spec, lambda e: None)

    with pytest.raises((OSError, RuntimeError)):
        model = adapter.initialize(spec, callback)
        active[0] = True
        adapter.execute(model, plan.operation_plan(spec, context["selected"]["state"]["x"])[0])
    count = len(events)
    with pytest.raises(RuntimeError):
        adapter.initialize(spec, callback)
    assert len(events) == count


def test_native_field_call_outside_owned_adapter_operation_is_denied(monkeypatch):
    adapter, model, _, _, _ = initialized(monkeypatch)
    with pytest.raises(ValueError, match="outside"):
        model.request("loop", "A", 256)
    assert adapter._failed


@pytest.mark.parametrize("name", list(native.THREADS))
def test_thread_environment_fails_before_context_or_native_import(monkeypatch, name):
    context, archive = inputs()
    monkeypatch.setenv(name, "2")
    monkeypatch.setattr(native, "_build_context", lambda *a: pytest.fail("early source import"))
    with pytest.raises(ValueError, match="single-thread"):
        native.FineNativeAdapter(context, archive)


def test_lazy_bridges_only_forward_fixed_apis(monkeypatch):
    legacy, intake = ModuleType("run_clear_coil_field_start"), ModuleType("protected_fine_inputs")
    calls = []

    def call(name):
        def wrapped(*args):
            calls.append((name, args))
            return name

        return wrapped

    legacy.make_model, legacy.execute = call("model"), call("execute")
    intake.build_context = call("context")
    monkeypatch.setitem(sys.modules, legacy.__name__, legacy)
    monkeypatch.setitem(sys.modules, intake.__name__, intake)
    args = tuple(object() for _ in range(5))
    assert native._build_context(*args[:2]) == "context"
    assert native._make_model(*args) == "model"
    assert native._execute(*args[:3]) == "execute"
    assert calls == [("context", args[:2]), ("model", args), ("execute", args[:3])]


def test_import_is_science_free_in_fresh_interpreter():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import fusion_baselines.protected_fine_native; "
                "assert not ({'numpy','scipy','simsopt','jax','run_clear_coil_field_start',"
                "'protected_fine_inputs'} & set(sys.modules))"
            ),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_swallowed_initial_callback_failure_blocks_second_event_and_result(monkeypatch):
    context, archive, _ = setup(monkeypatch)
    adapter = native.FineNativeAdapter(context, archive)
    received = []

    def callback(event):
        received.append(event)
        raise OSError("caller journal failed")

    def swallowing_factory(source, case, spec, seed, receive):
        with pytest.raises(OSError):
            receive(dict(first=True))
        with pytest.raises(RuntimeError):
            receive(dict(second=True))
        return Model(context, spec, lambda event: None)

    monkeypatch.setattr(native, "_make_model", swallowing_factory)
    with pytest.raises(RuntimeError, match="failed"):
        adapter.initialize(plan.model_plan(context["case"])[0], callback)
    assert received == [dict(first=True)]


def test_swallowed_execute_failure_never_returns_a_bundle(monkeypatch):
    context, archive, _ = setup(monkeypatch)
    adapter = native.FineNativeAdapter(context, archive)
    spec = plan.model_plan(context["case"])[0]
    failed, received = [False], []

    def callback(event):
        received.append(event)
        if failed[0]:
            raise OSError("operation journal failed")

    model = adapter.initialize(spec, callback)
    failed[0] = True

    def swallowed(model, operation, frozen):
        with pytest.raises(OSError):
            model.request("boundary", "B", 4096)
        with pytest.raises(RuntimeError):
            model.callback(dict(second=True))
        return {}, {}

    monkeypatch.setattr(native, "_execute", swallowed)
    with pytest.raises(RuntimeError, match="failed"):
        adapter.execute(model, plan.operation_plan(spec, context["selected"]["state"]["x"])[0])
    assert len(received) == 3  # Two initialization events, one failed operation attempt.


@pytest.mark.parametrize("stage", ["initialize", "execute", "metadata"])
def test_thread_drift_blocks_next_native_adapter_boundary(monkeypatch, stage):
    adapter, model, operation, context, calls = initialized(monkeypatch)
    monkeypatch.setenv("OMP_NUM_THREADS", "2")
    with pytest.raises(ValueError, match="single-thread"):
        if stage == "initialize":
            adapter.initialize(plan.model_plan(context["case"])[1], lambda event: None)
        elif stage == "execute":
            adapter.execute(model, operation)
        else:
            adapter.metadata(model)
    assert len(calls["initialize"]) == 1 and not calls["execute"]


def test_duplicate_model_identity_under_different_spec_is_rejected(monkeypatch):
    adapter, model, _, context, _ = initialized(monkeypatch)
    monkeypatch.setattr(native, "_make_model", lambda *args: model)
    with pytest.raises(ValueError, match="distinct fresh"):
        adapter.initialize(plan.model_plan(context["case"])[1], lambda event: None)
