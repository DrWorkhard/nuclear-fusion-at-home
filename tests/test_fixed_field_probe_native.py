"""Instrumented value-only bridge controls: no native models or fields."""

import copy
import subprocess
import sys

import numpy as np
import pytest
from test_protected_cell_contract import bundle_fixture, context_fixture
from test_protected_fine_native import Model as FineModel
from test_protected_fine_native import raw_arrays

from fusion_baselines import fixed_field_probe_native as native
from fusion_baselines import protected_fine_plan as plan


@pytest.fixture(autouse=True)
def environment(monkeypatch):
    for name in native.THREADS:
        monkeypatch.setenv(name, "1")


class Model(FineModel):
    def __init__(self, context, spec, callback):
        self.context = context
        self.snapshot_calls = 0
        self.requests_started = 0
        super().__init__(context, spec, callback)
        self.seed_unit_flux = 0.25 if self.ncoil == 256 else 0.249

    def request(self, field, quantity, points):
        event = dict(
            index=len(self.native_calls),
            field=field,
            quantity=quantity,
            points=points,
            status="attempted",
            started_monotonic=float(len(self.native_calls)),
            native_started=False,
            native_completed=False,
        )
        self.native_calls.append(event)
        self.callback(copy.deepcopy(event))
        self.requests_started += 1
        event.update(
            status="completed",
            native_started=True,
            native_completed=True,
            completed_monotonic=event["started_monotonic"] + 0.5,
        )
        self.callback(copy.deepcopy(event))

    def _state(self, x, scale=None, B2_scale=None):
        key = (np.asarray(x).tobytes(), scale, self.B2_scale if B2_scale is None else B2_scale)
        if self._cache is None or self._cache["key"] != key:
            self.x = np.asarray(x).copy()
            self.request("boundary", "B", self.nphi * self.ntheta)
            self.request("inner", "B", 3 * self.ninner**2)
            self.request("loop", "A", 256)
            bundle = bundle_fixture(
                self.context["original_context"],
                x,
                current=234567.0 if scale is None else 1e5 * scale,
            )
            bundle["snapshot"]["seed_unit_flux"] = self.seed_unit_flux
            arrays = raw_arrays(self.spec, {}, bundle["snapshot"])
            for key_to_remove in ("boundary_A", "inner_A", "loop_B"):
                arrays.pop(key_to_remove)
            self._cache = dict(
                key=key,
                metrics=dict(bundle["state"]["metrics"], frozen_scale=scale is not None),
                snapshot=bundle["snapshot"],
                arrays=arrays,
            )
        return self._cache

    def snapshot(self, x):
        self.snapshot_calls += 1
        return copy.deepcopy(self._state(x)["snapshot"])

    def diagnostics(self, x, scale, B2_scale):
        return copy.deepcopy(self._state(x, scale, B2_scale)["metrics"])

    def arrays(self, x, scale=None, B2_scale=None):
        return {
            key: value.copy() for key, value in self._state(x, scale, B2_scale)["arrays"].items()
        }


def setup(monkeypatch, nbase=6):
    original = context_fixture(nbase=nbase)
    x = np.asarray(original["seed"]["base_coefficients"]).ravel().copy()
    x[0] += 0.001
    context = dict(original_context=original, selected=bundle_fixture(original, x))
    source = dict(
        targets=copy.deepcopy(original["seed"]["sources"]),
        normalization={"reference": dict(B2_scale=original["B2_scale"])},
    )
    models, events = [], []

    def make(source_arg, case, spec, seed, callback):
        assert source_arg == source
        assert seed == original["seed"]
        model = Model(context, spec, callback)
        models.append(model)
        return model

    def supplement(model, raw, scale):
        for key, field, quantity, points in (
            ("boundary_A", "boundary", "A", model.nphi * model.ntheta),
            ("inner_A", "inner", "A", 3 * model.ninner**2),
            ("loop_B", "loop", "B", 256),
        ):
            model.request(field, quantity, points)
            raw[key] = np.zeros((points, 3))
        return raw

    monkeypatch.setattr(native, "_make_model", make)
    monkeypatch.setattr(native, "_supplement", supplement)
    args = dict(
        source=source,
        case=copy.deepcopy(original["case"]),
        seed=original["seed"],
        x=x,
        level=plan.diagnostic_levels()[0],
        callback=events.append,
    )
    return args, models, events


@pytest.mark.parametrize("nbase", [6, 8])
def test_exact_six_grid_schedule_currents_and_private_results(monkeypatch, nbase):
    args, models, events = setup(monkeypatch, nbase)
    coarse = native.evaluate_model(**args)
    assert set(coarse) == {"snapshot", "metrics", "arrays", "initialization", "native_calls"}
    frozen = copy.deepcopy(coarse["snapshot"])
    outputs = [coarse]
    for level in plan.diagnostic_levels()[1:]:
        outputs.append(native.evaluate_model(**dict(args, level=level, frozen_snapshot=frozen)))
    assert sum(len(row["native_calls"]) for row in outputs) == 42
    assert sum(call["points"] for row in outputs for call in row["native_calls"]) == 201216
    assert len(events) == 84
    assert [model.snapshot_calls for model in models] == [1, 0, 0, 0, 0, 0]
    for index, (result, model) in enumerate(zip(outputs, models, strict=True)):
        assert model.requests_started == 7
        assert result["snapshot"] == frozen
        assert result["metrics"]["frozen_scale"] is (index != 0)
        assert result["metrics"]["scale"] == frozen["scale"]
        assert result["metrics"]["current"] == 234567.0
        assert result["initialization"] == dict(
            seed_unit_flux=0.25 if model.ncoil == 256 else 0.249,
            names=args["seed"]["names"],
            seed_x=np.asarray(args["seed"]["base_coefficients"]).ravel().tolist(),
            ncoil=model.ncoil,
            initialization_work=dict(seed_A_calls=1, seed_A_points=256),
        )
        assert not np.array_equal(model.seed_x, args["x"])
        np.testing.assert_array_equal(model.x, args["x"])
        result["arrays"]["boundary_B"][0, 0] = 999
        assert model._cache["arrays"]["boundary_B"][0, 0] == 0
    coarse["snapshot"]["names"][0] = "caller-owned"
    assert args["seed"]["names"][0] != "caller-owned"
    assert outputs[1]["snapshot"] == frozen
    outputs[1]["snapshot"]["scale"] = -1
    assert frozen["scale"] > 0


@pytest.mark.parametrize(
    "mutation",
    [
        lambda a: a["case"].update(method="V"),
        lambda a: a["case"].update(target="selected"),
        lambda a: a["level"].update(index=True),
        lambda a: a["level"].update(ncoil=512),
        lambda a: a["level"].update(offset=0.0),
        lambda a: a["seed"]["names"].reverse(),
        lambda a: a["seed"]["physical"][0]["matrix"][0].__setitem__(0, -1.0),
        lambda a: a["source"]["targets"]["reference"]["input"].update(sha256="b" * 64),
        lambda a: a["source"]["normalization"]["reference"].update(B2_scale=True),
        lambda a: a.update(x=a["x"].astype(np.float32)),
        lambda a: a.update(x=a["x"].reshape(-1, 1)),
        lambda a: a.update(x=[True] * len(a["x"])),
        lambda a: a.update(frozen_snapshot={}),
        lambda a: a.update(level=plan.diagnostic_levels()[1]),
    ],
)
def test_bad_inputs_dispatch_nothing(monkeypatch, mutation):
    args, models, events = setup(monkeypatch)
    mutation(args)
    with pytest.raises((ValueError, KeyError)):
        native.evaluate_model(**args)
    assert not models and not events


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.update(scale=s["scale"] + 1),
        lambda s: s.update(unit_flux=s["unit_flux"] * 0.9),
        lambda s: s.update(method="V"),
        lambda s: s.update(B2_scale=3.0),
        lambda s: s.update(schema_version=True),
        lambda s: s["names"].reverse(),
        lambda s: s["construction"].update(ncoil=512),
        lambda s: s["physical"][0].update(current=-123.0),
        lambda s: s["physical"][0]["matrix"][0].__setitem__(0, -1.0),
        lambda s: s["base_coefficients"][0][0].__setitem__(1, -0.0),
        lambda s: s["sources"]["wout"].update(sha256="b" * 64),
    ],
)
def test_changed_frozen_identity_is_rejected_before_fine_initializer(monkeypatch, mutation):
    args, models, events = setup(monkeypatch)
    frozen = native.evaluate_model(**args)["snapshot"]
    mutation(frozen)
    events.clear()
    with pytest.raises(ValueError):
        native.evaluate_model(
            **dict(args, level=plan.diagnostic_levels()[1], frozen_snapshot=frozen)
        )
    assert len(models) == 1 and not events


@pytest.mark.parametrize(
    "attribute,value",
    [
        ("names", ["wrong"]),
        ("method", "V"),
        ("ncoil", 512),
        ("offset", 0.5),
        ("B2_scale", 3.0),
        ("seed_unit_flux", 0.0),
        ("initialization_work", {}),
        ("_cache", {"stale": True}),
    ],
)
def test_factory_substitution_stops_after_initializer(monkeypatch, attribute, value):
    args, models, events = setup(monkeypatch)
    factory = native._make_model

    def wrong(*values):
        model = factory(*values)
        setattr(model, attribute, value)
        return model

    monkeypatch.setattr(native, "_make_model", wrong)
    with pytest.raises(ValueError):
        native.evaluate_model(**args)
    assert len(events) == 2 and models[0].requests_started == 1


def test_changed_original_or_assigned_coordinate_bits(monkeypatch):
    args, models, _ = setup(monkeypatch)
    factory = native._make_model

    def wrong(*values):
        model = factory(*values)
        model.seed_x = args["x"].copy()
        return model

    monkeypatch.setattr(native, "_make_model", wrong)
    with pytest.raises(ValueError, match="original model seed"):
        native.evaluate_model(**args)
    assert models[0].requests_started == 1


@pytest.mark.parametrize("change", ["base", "physical", "initial_coordinates"])
def test_initializer_currents_and_seed_must_be_original(monkeypatch, change):
    args, models, _ = setup(monkeypatch)
    factory = native._make_model

    def wrong(*values):
        model = factory(*values)
        if change == "base":
            model.base_currents[0].value *= 2
        elif change == "physical":
            model.coils[0].current.value *= -1
        else:
            model.x = args["x"]
        return model

    monkeypatch.setattr(native, "_make_model", wrong)
    with pytest.raises(ValueError):
        native.evaluate_model(**args)
    assert models[0].requests_started == 1


@pytest.mark.parametrize("event_number", range(1, 15))
def test_callback_failure_poison_is_never_swallowed(monkeypatch, event_number):
    args, models, events = setup(monkeypatch)

    def fail(event):
        events.append(event)
        if len(events) == event_number:
            raise OSError("ledger failed")

    with pytest.raises(OSError, match="ledger failed"):
        native.evaluate_model(**dict(args, callback=fail))
    assert len(events) == event_number
    assert native._ACTIVE is None


@pytest.mark.parametrize("cutoff", range(1, 38))
def test_guard_expiration_at_every_phase_cannot_return_success(monkeypatch, cutoff):
    args, _, _ = setup(monkeypatch)
    checks = 0

    def guard():
        nonlocal checks
        checks += 1
        if checks >= cutoff:
            raise TimeoutError("expired")

    with pytest.raises(TimeoutError):
        native.evaluate_model(**dict(args, guard=guard))
    assert checks == cutoff and native._ACTIVE is None


def test_swallowed_reentry_still_poisoned(monkeypatch):
    args, _, events = setup(monkeypatch)

    def callback(event):
        events.append(event)
        with pytest.raises(RuntimeError, match="reentrant"):
            native.evaluate_model(**args)

    with pytest.raises(ValueError, match="swallowed|poisoned"):
        native.evaluate_model(**dict(args, callback=callback))
    assert len(events) == 1


def test_callback_closed_after_return_and_no_live_model_escape(monkeypatch):
    args, models, _ = setup(monkeypatch)
    result = native.evaluate_model(**args)
    with pytest.raises(ValueError, match="closed"):
        models[0].request("loop", "A", 256)
    assert models[0].requests_started == 7
    assert len(result["native_calls"]) == 7


def test_coarse_frozen_cache_bug_is_detected_before_extra_dispatch(monkeypatch):
    args, models, _ = setup(monkeypatch)
    original = Model.arrays

    def wrong(model, x, scale=None, B2_scale=None):
        return original(model, x, scale=2.34567, B2_scale=B2_scale)

    monkeypatch.setattr(Model, "arrays", wrong)
    with pytest.raises(ValueError, match="native dispatch"):
        native.evaluate_model(**args)
    assert models[0].requests_started == 4


@pytest.mark.parametrize("fault", ["missing", "extra", "reordered", "vjp", "bad_points", "forged"])
def test_exact_native_schedule_is_closed(monkeypatch, fault):
    args, models, _ = setup(monkeypatch)
    supplement = native._supplement

    def wrong(model, arrays, scale):
        if fault == "missing":
            arrays.update(
                boundary_A=np.zeros((model.nphi * model.ntheta, 3)),
                inner_A=np.zeros((3 * model.ninner**2, 3)),
                loop_B=np.zeros((256, 3)),
            )
            return arrays
        if fault == "reordered":
            model.request("inner", "A", 3 * model.ninner**2)
        if fault == "vjp":
            model.request("boundary", "A_vjp", model.nphi * model.ntheta)
        if fault == "bad_points":
            model.request("boundary", "A", 1)
        result = supplement(model, arrays, scale)
        if fault == "extra":
            model.request("loop", "A", 256)
        if fault == "forged":
            model.native_calls[0]["points"] = 1
        return result

    monkeypatch.setattr(native, "_supplement", wrong)
    with pytest.raises(ValueError):
        native.evaluate_model(**args)
    assert models[0].requests_started <= 7


@pytest.mark.parametrize("fault", ["metrics", "arrays", "currents", "coordinate", "owner", "flux"])
def test_mutated_outputs_or_model_fail_closed(monkeypatch, fault):
    args, _, _ = setup(monkeypatch)
    supplement = native._supplement

    def wrong(model, arrays, scale):
        result = supplement(model, arrays, scale)
        if fault == "metrics":
            model._cache["metrics"]["scale"] += 1
        elif fault == "arrays":
            result["inner_A"] = np.full((1, 3), np.nan)
        elif fault == "currents":
            result["coil_currents"][0] *= -1
        elif fault == "coordinate":
            model._x[0] += 1
        elif fault == "owner":
            model._fixed_probe_owner = object()
        else:
            model.seed_unit_flux += 1
        return result

    # Metrics are already privately copied before supplement, so mutating the
    # model's old metrics cannot corrupt the returned result.
    monkeypatch.setattr(native, "_supplement", wrong)
    if fault == "metrics":
        assert native.evaluate_model(**args)["metrics"]["scale"] == 2.34567
    else:
        with pytest.raises(ValueError):
            native.evaluate_model(**args)


@pytest.mark.parametrize("name", list(native.THREADS))
def test_thread_environment_checked_before_work(monkeypatch, name):
    args, models, events = setup(monkeypatch)
    monkeypatch.setenv(name, "2")
    with pytest.raises(ValueError, match="single-thread"):
        native.evaluate_model(**args)
    assert not models and not events


def test_environment_change_during_callback_denies_next_native_work(monkeypatch):
    args, _, events = setup(monkeypatch)

    def callback(event):
        events.append(event)
        monkeypatch.setenv("OMP_NUM_THREADS", "2")

    with pytest.raises(ValueError, match="single-thread"):
        native.evaluate_model(**dict(args, callback=callback))
    assert len(events) == 1


def test_import_does_not_import_native_model_or_driver():
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import fusion_baselines.fixed_field_probe_native; "
                "assert 'fusion_baselines.clear_coil_field' not in sys.modules; "
                "assert 'run_clear_coil_field_start' not in sys.modules; "
                "assert 'simsopt' not in sys.modules"
            ),
        ],
        check=True,
    )


@pytest.mark.parametrize("fault", ["missing", "duplicate", "outcome_first", "int_flag", "time"])
def test_malformed_callback_protocol_cannot_be_accepted(monkeypatch, fault):
    args, _, events = setup(monkeypatch)
    request = Model.request

    def wrong(model, field, quantity, points):
        callback = model.callback

        def alter(event):
            if fault == "missing":
                return
            if fault == "duplicate":
                callback(event)
            if fault == "outcome_first" and event["status"] == "attempted":
                return
            if fault == "int_flag":
                event["native_started"] = int(event["native_started"])
            if fault == "time" and event["status"] == "completed":
                event["completed_monotonic"] = event["started_monotonic"] - 1
            callback(event)

        model.callback = alter
        try:
            return request(model, field, quantity, points)
        finally:
            model.callback = callback

    monkeypatch.setattr(Model, "request", wrong)
    with pytest.raises(ValueError):
        native.evaluate_model(**args)
    assert len(events) <= 1


def test_swallowed_callback_exception_still_fails_model(monkeypatch):
    args, models, _ = setup(monkeypatch)
    factory = native._make_model

    def swallowing(*values):
        callback = values[-1]

        def swallow(event):
            try:
                callback(event)
            except OSError:
                pass

        return factory(*values[:-1], swallow)

    def fail(event):
        if event["status"] == "completed":
            raise OSError("lost persisted completion")

    monkeypatch.setattr(native, "_make_model", swallowing)
    with pytest.raises(ValueError, match="poisoned"):
        native.evaluate_model(**dict(args, callback=fail))
    assert models[0].requests_started == 1


def test_callback_receives_private_receipts(monkeypatch):
    args, _, _ = setup(monkeypatch)

    def mutate(event):
        event.clear()

    result = native.evaluate_model(**dict(args, callback=mutate))
    assert len(result["native_calls"]) == 7
    assert all(row["status"] == "completed" for row in result["native_calls"])


def test_native_error_event_is_retained_and_cannot_be_swallowed(monkeypatch):
    args, _, events = setup(monkeypatch)

    def error(model, field, quantity, points):
        event = dict(
            index=0,
            field=field,
            quantity=quantity,
            points=points,
            status="attempted",
            started_monotonic=0.0,
            native_started=False,
            native_completed=False,
        )
        model.native_calls.append(event)
        model.callback(copy.deepcopy(event))
        event.update(
            status="error",
            native_started=True,
            error="ValueError: synthetic native failure",
            failed_monotonic=0.5,
        )
        try:
            model.callback(copy.deepcopy(event))
        except ValueError:
            pass

    monkeypatch.setattr(Model, "request", error)
    with pytest.raises(ValueError, match="poisoned"):
        native.evaluate_model(**args)
    assert [event["status"] for event in events] == ["attempted", "error"]


def test_cross_call_time_cannot_move_backward_before_dispatch(monkeypatch):
    args, models, _ = setup(monkeypatch)
    request = Model.request

    def repeated_clock(model, field, quantity, points):
        callback = model.callback

        def rewrite(event):
            event["started_monotonic"] = 0.0
            model.native_calls[-1]["started_monotonic"] = 0.0
            callback(event)

        model.callback = rewrite
        try:
            return request(model, field, quantity, points)
        finally:
            model.callback = callback

    monkeypatch.setattr(Model, "request", repeated_clock)
    with pytest.raises(ValueError, match="monotonic"):
        native.evaluate_model(**args)
    assert models[0].requests_started == 1
