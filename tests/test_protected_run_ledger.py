"""Synthetic dispatch controls; no native physics or physical acceptance claim."""

import copy

import numpy as np
import pytest

from fusion_baselines.clear_coil_field import CountedField
from fusion_baselines.protected_run_ledger import ProtectedRunLedger
from fusion_baselines.protected_search_journal import EventJournal, read_events

STATE = "a" * 64
REFERENCE = {"path": "/synthetic-raw-manifest.json", "sha256": "b" * 64, "bytes": 42}
# Deliberately independent of implementation constants.
EXPECTED = [
    ("boundary", "B", 4096),
    ("inner", "B", 3072),
    ("loop", "A", 256),
    ("boundary", "B_vjp", 4096),
    ("inner", "B_vjp", 3072),
    ("loop", "A_vjp", 256),
    ("boundary", "A", 4096),
    ("inner", "A", 3072),
    ("loop", "B", 256),
]


class Native:
    def __init__(self, calls, fail=False):
        self.calls, self.fail = calls, fail

    def set_points(self, points):
        self.points = points

    def _request(self, kind):
        self.calls.append((kind, len(self.points)))
        if self.fail:
            raise ArithmeticError("synthetic native failure")
        return np.zeros((len(self.points), 3))

    def B(self):
        return self._request("B")

    def A(self):
        return self._request("A")

    def B_vjp(self, weights):
        return self._request("B_vjp")

    def A_vjp(self, weights):
        return self._request("A_vjp")


class Harness:
    def __init__(self, record=None, guard=None):
        self.events, self.native_calls, self.timeline = [], [], []
        self.ledger = ProtectedRunLedger(
            record=record or self.events.append, guard=guard or (lambda: None)
        )

    def factory(self, callback, fail=False):
        events = []
        model = {
            field: CountedField(Native(self.native_calls, fail), field, events, callback)
            for field in ("boundary", "inner", "loop")
        }
        model["loop"].set_points(np.zeros((256, 3)))
        model["loop"].A()
        return model

    def publish(self, result):
        self.timeline.append("publish")
        return copy.deepcopy(REFERENCE)

    def validate(self, result):
        self.timeline.append("validate")
        return True

    def initialize(self, model_id="main", **kwargs):
        options = dict(factory=self.factory, validate=self.validate, publish=self.publish)
        options.update(kwargs)
        return self.ledger.initialize(model_id, **options)

    def certificate(self, phase, index=0, certified=True, **kwargs):
        options = dict(
            compute=lambda: {"certified": certified},
            validate=lambda result: result["certified"],
            publish=self.publish,
        )
        options.update(kwargs)
        return self.ledger.certificate(phase, f"{phase}/certificate/{index}", STATE, **options)

    def compute(self, model):
        self.timeline.append("compute")
        for field, quantity, points in EXPECTED:
            model[field].set_points(np.zeros((points, 3)))
            getattr(model[field], quantity)(np.zeros((points, 3))) if quantity.endswith(
                "vjp"
            ) else getattr(model[field], quantity)()
        return {"value": 1.0}

    def bundle(self, phase, index=0, **kwargs):
        options = dict(
            certificate_id=f"{phase}/certificate/{index}",
            invalidate=lambda model: self.timeline.append("invalidate"),
            compute=self.compute,
            validate=self.validate,
            publish=self.publish,
        )
        options.update(kwargs)
        return self.ledger.bundle(phase, f"{phase}/bundle/{index}", STATE, **options)

    def search_ready(self):
        self.initialize()
        for i in range(10):
            self.certificate("startup", i)
            self.bundle("startup", i)
        self.certificate("search-seed")
        self.bundle("search-seed")


def test_exact_full_budget_and_journal_composition(tmp_path):
    journal = EventJournal(tmp_path / "events")
    h = Harness(record=journal)
    h.search_ready()
    for i in range(116):
        h.certificate("trial", i, certified=i < 20)
        if i < 20:
            h.bundle("trial", i)
    h.initialize("replay")
    h.certificate("replay")
    h.bundle("replay")
    counts = h.ledger.counts
    assert counts["initialization"] == {
        x: {"attempted": 1, "completed": 1} for x in ("main", "replay")
    }
    assert counts["certificate"] == {
        k: {"attempted": v, "completed": v}
        for k, v in {"startup": 10, "search-seed": 1, "trial": 116, "replay": 1}.items()
    }
    assert counts["bundle"] == {
        k: {"attempted": v, "completed": v}
        for k, v in {"startup": 10, "search-seed": 1, "trial": 20, "replay": 1}.items()
    }
    assert counts["native"] == {"attempted": 290, "completed": 290}
    assert len(h.native_calls) == 290
    events = read_events(tmp_path / "events", journal.receipt)
    assert len(events) == 904
    attempts = [e for e in events if e["event"] == "native-attempted"]
    assert [e["native"]["index"] for e in attempts if e["model_id"] == "main"] == list(range(280))
    assert [e["native"]["index"] for e in attempts if e["model_id"] == "replay"] == list(range(10))
    assert not any("physical_admission" in e for e in events)
    counts["native"]["attempted"] = 0
    assert h.ledger.counts["native"]["attempted"] == 290
    assert not h.ledger.failed


def test_zero_trial_replay_is_valid_and_order_is_explicit():
    h = Harness()
    h.search_ready()
    h.initialize("replay")
    h.certificate("replay")
    h.timeline.clear()
    h.bundle("replay")
    assert h.timeline == ["invalidate", "compute", "validate", "publish"]
    assert h.ledger.counts["native"] == {"attempted": 110, "completed": 110}


@pytest.mark.parametrize(
    "phase,limit", [("startup", 10), ("search-seed", 1), ("trial", 116), ("replay", 1)]
)
def test_each_certificate_cap(phase, limit):
    h = Harness()
    h.initialize()
    if phase != "startup":
        for i in range(10):
            h.certificate("startup", i)
            h.bundle("startup", i)
    if phase in ("trial", "replay"):
        h.certificate("search-seed")
        h.bundle("search-seed")
    if phase == "replay":
        h.initialize("replay")
    for i in range(limit):
        h.certificate(phase, i, certified=phase != "trial")
        if phase != "trial":
            h.bundle(phase, i)
    before = len(h.native_calls)
    with pytest.raises(ValueError):
        h.certificate(phase, limit)
    assert h.ledger.failed and len(h.native_calls) == before


def test_trial_field_cap_is_twenty_not_certificate_cap():
    h = Harness()
    h.search_ready()
    for i in range(21):
        h.certificate("trial", i)
        if i < 20:
            h.bundle("trial", i)
    before = len(h.native_calls)
    with pytest.raises(ValueError, match="budget"):
        h.bundle("trial", 20)
    assert h.ledger.counts["bundle"]["trial"] == {"attempted": 20, "completed": 20}
    assert len(h.native_calls) == before


@pytest.mark.parametrize("model_id", ["main", "replay"])
def test_each_initialization_cap(model_id):
    h = Harness()
    h.search_ready()
    if model_id == "replay":
        h.initialize("replay")
    with pytest.raises(ValueError):
        h.initialize(model_id)
    assert h.ledger.failed


@pytest.mark.parametrize(
    "scenario",
    [
        "before-main",
        "before-ten-startup",
        "before-seed",
        "trial-after-replay",
        "replay-before-model",
    ],
)
def test_phase_order(scenario):
    h = Harness()
    if scenario == "before-main":

        def action():
            return h.certificate("startup")
    elif scenario == "before-ten-startup":
        h.initialize()

        def action():
            return h.certificate("search-seed")
    elif scenario == "before-seed":
        h.initialize()

        def action():
            return h.initialize("replay")
    else:
        h.search_ready()
        if scenario == "trial-after-replay":
            h.initialize("replay")

            def action():
                return h.certificate("trial")
        else:

            def action():
                return h.certificate("replay")

    with pytest.raises(ValueError):
        action()
    assert h.ledger.failed


@pytest.mark.parametrize(
    "scenario",
    ["missing", "rejected", "wrong-id", "wrong-state", "wrong-phase", "duplicate", "skip-positive"],
)
def test_certificate_binding(scenario):
    h = Harness()
    h.initialize()
    if scenario != "missing":
        h.certificate("startup", certified=scenario != "rejected")
    if scenario == "duplicate":
        h.bundle("startup")

        def action():
            return h.bundle("startup")
    elif scenario == "skip-positive":

        def action():
            return h.certificate("startup", 1)
    elif scenario == "wrong-state":

        def action():
            return h.ledger.bundle(
                "startup",
                "other",
                "c" * 64,
                certificate_id="startup/certificate/0",
                invalidate=lambda model: None,
                compute=h.compute,
                validate=h.validate,
                publish=h.publish,
            )
    else:

        def action():
            return h.bundle(
                "trial" if scenario == "wrong-phase" else "startup",
                **({"certificate_id": "other"} if scenario == "wrong-id" else {}),
            )

    before = len(h.native_calls)
    with pytest.raises(ValueError):
        action()
    assert h.ledger.failed and len(h.native_calls) == before


@pytest.mark.parametrize(
    "mutation",
    [
        {"index": True},
        {"index": 1},
        {"points": True},
        {"points": 255},
        {"field": "boundary"},
        {"quantity": "B"},
        {"native_started": 0},
        {"native_started": True},
        {"native_completed": 0},
        {"native_completed": True},
        {"started_monotonic": float("nan")},
        {"started_monotonic": float("inf")},
        {"started_monotonic": True},
        {"started_monotonic": -1},
        {"started_monotonic": 10**400},
        {"extra": 0},
        {"status": "unknown"},
    ],
)
def test_malformed_attempt_never_dispatches(mutation):
    h = Harness()

    def factory(callback):
        return h.factory(lambda event: callback({**event, **mutation}))

    with pytest.raises((ValueError, RuntimeError)):
        h.initialize(factory=factory)
    assert h.ledger.failed and not h.native_calls
    assert h.ledger.counts["native"] == {"attempted": 0, "completed": 0}


@pytest.mark.parametrize(
    "mutation",
    [
        {"index": 1},
        {"native_started": False},
        {"native_completed": False},
        {"native_completed": 1},
        {"completed_monotonic": -1},
        {"completed_monotonic": float("nan")},
        {"started_monotonic": 0},
        {"points": 255},
        {"extra": 0},
        {"field": "inner"},
    ],
)
def test_malformed_completion_retains_attempt(mutation):
    h = Harness()

    def factory(callback):
        return h.factory(
            lambda event: (
                callback({**event, **mutation})
                if event["status"] == "completed"
                else callback(event)
            )
        )

    with pytest.raises(ValueError):
        h.initialize(factory=factory)
    assert h.ledger.failed and len(h.native_calls) == 1
    assert h.ledger.counts["native"] == {"attempted": 1, "completed": 0}
    assert h.ledger.counts["initialization"]["main"]["completed"] == 0


@pytest.mark.parametrize(
    "fault",
    ["operation-reservation", "native-reservation", "native-completion", "operation-completion"],
)
def test_record_failure_stops_at_known_boundary(fault):
    events = []
    target = {
        "operation-reservation": "operation-attempted",
        "native-reservation": "native-attempted",
        "native-completion": "native-completed",
        "operation-completion": "operation-completed",
    }[fault]

    def record(event):
        if event["event"] == target:
            raise OSError("synthetic persistence failure")
        events.append(copy.deepcopy(event))

    h = Harness(record=record)
    with pytest.raises(OSError):
        h.initialize()
    assert h.ledger.failed
    assert len(h.native_calls) == int(fault in ("native-completion", "operation-completion"))
    assert h.ledger.counts["initialization"]["main"]["completed"] == 0
    with pytest.raises(RuntimeError):
        h.initialize()


@pytest.mark.parametrize("boundary", [1, 2, 3, 4])
def test_guard_failure_stops_dispatch(boundary):
    calls = []

    def guard():
        calls.append(None)
        if len(calls) == boundary:
            raise TimeoutError("synthetic guard")

    h = Harness(guard=guard)
    with pytest.raises(TimeoutError):
        h.initialize()
    assert h.ledger.failed
    assert len(h.native_calls) == int(boundary >= 3)
    assert h.ledger.counts["initialization"]["main"]["completed"] == 0


def test_native_error_keeps_requested_but_uncompleted_and_poisons():
    h = Harness()
    with pytest.raises(ArithmeticError):
        h.initialize(factory=lambda callback: h.factory(callback, fail=True))
    assert h.ledger.failed
    assert h.ledger.counts["native"] == {"attempted": 1, "completed": 0}
    assert h.events[-1]["event"] == "native-error"


@pytest.mark.parametrize("kind", ["initialize", "certificate", "bundle"])
@pytest.mark.parametrize("failure", ["compute", "validate", "publish"])
def test_operation_work_failures_never_complete(kind, failure):
    h = Harness()

    def fail(*args):
        raise ArithmeticError("synthetic operation failure")

    if kind == "initialize":

        def action():
            return h.initialize(**{"factory" if failure == "compute" else failure: fail})

        section, phase = "initialization", "main"
    else:
        h.initialize()
        if kind == "bundle":
            h.certificate("startup")

        def action():
            return getattr(h, kind)("startup", **{failure: fail})

        section, phase = kind, "startup"
    with pytest.raises(ArithmeticError):
        action()
    assert h.ledger.failed
    assert h.ledger.counts[section][phase] == {"attempted": 1, "completed": 0}


@pytest.mark.parametrize(
    "reference",
    [
        None,
        {},
        {**REFERENCE, "bytes": True},
        {**REFERENCE, "sha256": "wrong"},
        {**REFERENCE, "path": ""},
        {**REFERENCE, "path": "relative.json"},
    ],
)
def test_bad_published_reference_fails_closed(reference):
    h = Harness()
    with pytest.raises(ValueError):
        h.initialize(publish=lambda model: reference)
    assert h.ledger.failed and h.ledger.counts["initialization"]["main"]["completed"] == 0


@pytest.mark.parametrize("bad", [1, None, "true", np.bool_(True)])
def test_certificate_bool_is_not_coerced(bad):
    h = Harness()
    h.initialize()
    with pytest.raises(ValueError):
        h.certificate("startup", certified=bad)
    assert h.ledger.failed


def test_missing_native_call_and_cache_hit_still_require_requests():
    h = Harness()
    h.initialize()
    h.certificate("startup")
    with pytest.raises(ValueError, match="missing native"):
        h.bundle("startup", compute=lambda model: {"cached": True})
    assert h.ledger.failed
    assert h.ledger.counts["bundle"]["startup"] == {"attempted": 1, "completed": 0}


@pytest.mark.parametrize(
    "bad",
    [
        "wrong-model",
        "duplicate-attempt",
        "unpaired-outcome",
        "extra-request",
        "callback-outside-operation",
    ],
)
def test_unpaired_or_misattributed_callbacks_fail(bad):
    h = Harness()

    def factory(callback):
        def modify(event):
            if bad == "wrong-model":
                h.ledger.native_event("replay", event)
            elif bad == "duplicate-attempt":
                callback(event)
                callback(event)
            elif bad == "unpaired-outcome":
                if event["status"] == "completed":
                    callback(event)
            else:
                callback(event)

        model = h.factory(modify)
        if bad == "extra-request":
            model["loop"].A()
        return model

    if bad == "callback-outside-operation":
        model = h.initialize()

        def action():
            return model["loop"].A()
    else:

        def action():
            return h.initialize(factory=factory)

    with pytest.raises(ValueError):
        action()
    assert h.ledger.failed


def test_native_cap_reservation_guard_independent_of_aggregate_phase_caps():
    h = Harness()
    # Direct fault injection isolates the global guard from earlier phase guards.
    h.ledger._counts["native"]["attempted"] = 290
    with pytest.raises(ValueError, match="native budget"):
        h.initialize()
    assert not h.native_calls and h.ledger.failed


def test_interrupt_poisons_without_retry():
    h = Harness()

    def interrupt(*args):
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        h.initialize(publish=interrupt)
    assert h.ledger.failed
    with pytest.raises(RuntimeError):
        h.initialize()


def test_duplicate_operation_id_across_kinds_fails_before_work():
    h = Harness()
    h.initialize()
    with pytest.raises(ValueError, match="already used"):
        h.ledger.certificate(
            "startup",
            "initialize/main",
            STATE,
            compute=lambda: True,
            validate=lambda result: result,
            publish=h.publish,
        )
    assert h.ledger.failed and len(h.native_calls) == 1


@pytest.mark.parametrize("hook", ["factory", "validate", "publish", "guard"])
def test_swallowed_callback_failure_cannot_acknowledge_operation(hook):
    h = Harness()

    def poison():
        with pytest.raises(ValueError):
            h.ledger.native_event("main", {})

    options = {}
    if hook == "factory":

        def factory(callback):
            model = h.factory(callback)
            poison()
            return model

        options["factory"] = factory
    elif hook == "validate":

        def validate(model):
            poison()
            return True

        options["validate"] = validate
    elif hook == "publish":

        def publish(model):
            poison()
            return copy.deepcopy(REFERENCE)

        options["publish"] = publish
    else:
        guards = []

        def guard():
            guards.append(None)
            if len(guards) == 4:
                poison()

        h.ledger._guard = guard
    with pytest.raises(RuntimeError, match="ledger failed"):
        h.initialize(**options)
    assert h.ledger.failed
    assert h.ledger.counts["initialization"]["main"]["completed"] == 0


def test_final_native_slot_is_available_but_no_extra_slot():
    h = Harness()
    h.ledger._counts["native"] = {"attempted": 289, "completed": 289}
    h.initialize()
    assert h.ledger.counts["native"] == {"attempted": 290, "completed": 290}
    h.certificate("startup")
    with pytest.raises(ValueError, match="native budget"):
        h.bundle("startup")
    assert len(h.native_calls) == 1 and h.ledger.failed


@pytest.mark.parametrize(
    "phase,limit", [("startup", 10), ("search-seed", 1), ("trial", 20), ("replay", 1)]
)
def test_each_bundle_reservation_cap_independently(phase, limit):
    h = Harness()
    if phase == "startup":
        h.initialize()
    elif phase == "search-seed":
        h.initialize()
        for i in range(10):
            h.certificate("startup", i)
            h.bundle("startup", i)
    else:
        h.search_ready()
        if phase == "replay":
            h.initialize("replay")
    h.certificate(phase)
    # Fault injection isolates the bundle guard from the certificate/phase guards.
    h.ledger._counts["bundle"][phase]["attempted"] = limit
    before = len(h.native_calls)
    with pytest.raises(ValueError, match="phase budget"):
        h.bundle(phase)
    assert len(h.native_calls) == before and h.ledger.failed


def test_fresh_replay_model_identity_required():
    h = Harness()
    h.search_ready()
    main = h.ledger._models["main"]

    def factory(callback):
        h.factory(callback)
        return main

    with pytest.raises(ValueError, match="fresh model"):
        h.initialize("replay", factory=factory)
    assert h.ledger.counts["initialization"]["replay"] == {"attempted": 1, "completed": 0}


def test_invalidation_failure_prevents_native_bundle_dispatch():
    h = Harness()
    h.initialize()
    h.certificate("startup")

    def invalidate(model):
        raise RuntimeError("synthetic cache invalidation failure")

    with pytest.raises(RuntimeError, match="invalidation failure"):
        h.bundle("startup", invalidate=invalidate)
    assert len(h.native_calls) == 1
    assert h.ledger.failed
    assert h.ledger.counts["bundle"]["startup"] == {"attempted": 1, "completed": 0}


def test_completed_journal_prefix_survives_later_guard_failure(tmp_path):
    directory = tmp_path / "native-events"
    journal = EventJournal(directory)
    h = Harness(record=journal)
    h.initialize()
    before = {path.name: path.read_bytes() for path in directory.iterdir()}
    h.certificate("startup")

    def guard():
        raise OSError("synthetic remaining-space guard")

    h.ledger._guard = guard
    with pytest.raises(OSError):
        h.bundle("startup")
    events = read_events(directory, journal.receipt)
    assert len(events) == 6
    assert events[-1]["event"] == "operation-completed"
    assert events[-1]["kind"] == "certificate"
    assert len(h.native_calls) == 1 and h.ledger.failed
    assert all((directory / name).read_bytes() == raw for name, raw in before.items())


def test_shared_counts_and_record_payloads_do_not_alias_caller_mutations():
    events = []

    def record(event):
        events.append(copy.deepcopy(event))
        event.clear()

    h = Harness(record=record)
    h.initialize()
    assert h.ledger.counts["native"] == {"attempted": 1, "completed": 1}
    assert events[-1]["raw_reference"] == REFERENCE


def test_native_clock_must_be_monotonic_between_calls():
    h = Harness()
    h.initialize()
    h.certificate("startup")
    h.ledger._last_clock["main"] = 1e100
    with pytest.raises(ValueError, match="moved backwards"):
        h.bundle("startup")
    assert len(h.native_calls) == 1 and h.ledger.failed


@pytest.mark.parametrize("quantity", ["B", "A", "B_vjp", "A_vjp"])
def test_wrong_order_in_bundle_rejected_before_any_native_work(quantity):
    h = Harness()
    h.initialize()
    h.certificate("startup")

    def compute(model):
        model["inner"].set_points(np.zeros((3072, 3)))
        if quantity.endswith("vjp"):
            return getattr(model["inner"], quantity)(np.zeros((3072, 3)))
        return getattr(model["inner"], quantity)()

    with pytest.raises(ValueError, match="field/order/points"):
        h.bundle("startup", compute=compute)
    assert h.ledger.failed and len(h.native_calls) == 1


@pytest.mark.parametrize("hook", ["guard", "record"])
@pytest.mark.parametrize("swallow", [False, True])
def test_reentrant_hook_cannot_double_spend_last_certificate(hook, swallow):
    h = Harness()
    h.search_ready()
    for index in range(115):
        h.certificate("trial", index, certified=False)
    triggered = []

    def nested(*args):
        if triggered:
            return
        triggered.append(True)
        try:
            h.certificate("trial", 115, certified=False)
        except (ValueError, RuntimeError):
            if not swallow:
                raise

    setattr(h.ledger, "_guard" if hook == "guard" else "_record", nested)
    with pytest.raises((ValueError, RuntimeError)):
        h.certificate("trial", 116, certified=False)
    assert h.ledger.failed
    assert h.ledger.counts["certificate"]["trial"]["attempted"] <= 116
    assert h.ledger.counts["certificate"]["trial"]["completed"] <= 116


@pytest.mark.parametrize("swallow", [False, True])
def test_native_reservation_record_cannot_reenter_native_event(swallow):
    triggered = []
    h = Harness()

    def record(event):
        h.events.append(copy.deepcopy(event))
        if triggered or event["event"] != "native-attempted":
            return
        triggered.append(True)
        try:
            h.ledger.native_event("main", event["native"])
        except (ValueError, RuntimeError):
            if not swallow:
                raise

    h.ledger._record = record
    with pytest.raises((ValueError, RuntimeError)):
        h.initialize()
    assert h.ledger.failed and not h.native_calls
    assert h.ledger.counts["initialization"]["main"]["completed"] == 0
