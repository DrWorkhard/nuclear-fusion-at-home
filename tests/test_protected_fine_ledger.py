"""Synthetic fixed-work accounting; no fine native execution or physics claim."""

import copy

import numpy as np
import pytest

from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.clear_coil_field import CountedField
from fusion_baselines.protected_fine_ledger import FineLedger
from fusion_baselines.protected_search_journal import EventJournal, read_events

REF = {"path": "/synthetic-fine-raw.json", "sha256": "a" * 64, "bytes": 42}


class Native:
    def __init__(self, calls):
        self.calls = calls

    def set_points(self, points):
        self.points = points

    def A(self):
        self.calls.append(("A", len(self.points)))
        return np.zeros_like(self.points)

    def B(self):
        self.calls.append(("B", len(self.points)))
        return np.zeros_like(self.points)


class Harness:
    def __init__(self, case=None, record=None, guard=None):
        self.case = case or plan.cases()[0]
        self.x = np.zeros(self.case["nbase"] * 3 * (2 * self.case["order"] + 1))
        self.x[0] = -0.0
        self.events, self.calls, self.timeline = [], [], []
        self.ledger = FineLedger(
            self.case, self.x, record=record or self.events.append, guard=guard or (lambda: None)
        )
        self.specs = plan.model_plan(self.case)

    def factory(self, callback):
        events = []
        model = {
            field: CountedField(Native(self.calls), field, events, callback)
            for field in ("boundary", "inner", "loop")
        }
        model["loop"].set_points(np.zeros((256, 3)))
        model["loop"].A()
        return model

    def validate(self, result):
        self.timeline.append("validate")
        return True

    def publish(self, result):
        self.timeline.append("publish")
        return copy.deepcopy(REF)

    def initialize(self, spec=None, **kwargs):
        options = dict(factory=self.factory, validate=self.validate, publish=self.publish)
        options.update(kwargs)
        return self.ledger.initialize(spec or self.specs[0], **options)

    def compute(self, model, spec, op):
        self.timeline.append("compute")
        if op["kind"] == "diagnostic":
            grid = spec["grid"]
            requests = [
                ("boundary", "B", grid["nphi"] * grid["ntheta"]),
                ("inner", "B", 3 * grid["ninner"] ** 2), ("loop", "A", 256),
                ("boundary", "A", grid["nphi"] * grid["ntheta"]),
                ("inner", "A", 3 * grid["ninner"] ** 2), ("loop", "B", 256),
            ]
        else:
            order = ("A", "B") if op["form"] == "line" else ("B", "A")
            requests = [("loop", q, op["ntheta"] * op.get("nrho", 1)) for q in order]
        for field, quantity, points in requests:
            model[field].set_points(np.zeros((points, 3)))
            getattr(model[field], quantity)()
        return {"synthetic": True}

    def execute(self, model, spec=None, op=None, **kwargs):
        spec = spec or self.specs[0]
        op = op or plan.operation_plan(spec, self.x)[0]
        options = dict(compute=lambda m: self.compute(m, spec, op),
                       validate=self.validate, publish=self.publish)
        options.update(kwargs)
        return self.ledger.execute(model, spec, op, **options)

    def all(self):
        for spec in self.specs:
            model = self.initialize(spec)
            for op in plan.operation_plan(spec, self.x):
                self.execute(model, spec, op)
        return self.ledger.finish()


@pytest.mark.parametrize("case", plan.cases(), ids=lambda c: c["label"])
def test_complete_fixed_sequence_all_cases(case, tmp_path):
    journal = EventJournal(tmp_path / "events")
    h = Harness(case, record=journal)
    counts = h.all()
    assert counts == {
        key: {"attempted": count, "completed": count}
        for key, count in (("initialization", 8), ("operation", 24),
                           ("native", 80), ("points", 552960))
    }
    assert len(h.calls) == 80
    assert sum(points for _, points in h.calls) == 552960
    rows = read_events(tmp_path / "events", journal.receipt)
    assert len(rows) == 225
    assert rows[-1]["event"] == "fine-dispatch-completed"
    attempts = [r for r in rows if r["event"] == "native-attempted"]
    assert [r["quantity"] for r in (a["native"] for a in attempts[:7])] == [
        "A", "B", "B", "A", "A", "A", "B"
    ]
    for i, spec in enumerate(h.specs):
        indices = [r["native"]["index"] for r in attempts if r["model_id"] == spec["id"]]
        assert indices == list(range(7 if i < 6 else 19))
    assert all("physical_admission" not in row for row in rows)
    counts["native"]["attempted"] = 0
    assert h.ledger.counts["native"]["attempted"] == 80
    assert not h.ledger.failed
    with pytest.raises(ValueError, match="finished"):
        h.ledger.finish()
    assert h.ledger.failed


def test_validate_and_publish_before_completion():
    h = Harness()
    model = h.initialize()
    h.timeline.clear()
    h.execute(model)
    assert h.timeline == ["compute", "validate", "publish"]
    assert h.events[-1]["raw_reference"] == REF


@pytest.mark.parametrize("scenario", ["skip-model", "duplicate-init", "before-init",
                                     "wrong-model", "early-finish", "skip-flux"])
def test_sequence_violations_poison_before_dispatch(scenario):
    h = Harness()
    if scenario == "skip-model":
        def action():
            return h.initialize(h.specs[1])
    elif scenario == "before-init":
        def action():
            return h.execute(object())
    elif scenario == "early-finish":
        action = h.ledger.finish
    elif scenario == "skip-flux":
        for spec in h.specs[:6]:
            model = h.initialize(spec)
            h.execute(model, spec)
        spec = h.specs[6]
        model = h.initialize(spec)
        def action():
            return h.execute(model, spec, plan.operation_plan(spec, h.x)[1])
    else:
        h.initialize()
        action = h.initialize if scenario == "duplicate-init" else lambda: h.execute(object())
    before = len(h.calls)
    with pytest.raises(ValueError):
        action()
    assert h.ledger.failed and len(h.calls) == before
    with pytest.raises(RuntimeError, match="failed"):
        h.initialize()


@pytest.mark.parametrize("change", ["value", "signed-zero", "dtype", "length", "method"])
def test_selected_state_and_spec_are_bound(change):
    h = Harness()
    model = h.initialize()
    spec = copy.deepcopy(h.specs[0])
    op = plan.operation_plan(spec, h.x)[0]
    if change == "value":
        op["x"][1] = 0.125
    elif change == "signed-zero":
        op["x"][0] = 0.0
    elif change == "dtype":
        op["x"] = op["x"].astype(np.float32)
    elif change == "length":
        op["x"] = op["x"][:-1]
    else:
        spec["method"] = "V"
    with pytest.raises(ValueError):
        h.execute(model, spec, op)
    assert len(h.calls) == 1 and h.ledger.failed


@pytest.mark.parametrize("stage", ["factory", "compute", "validate", "publish", "record", "guard"])
@pytest.mark.parametrize("swallow", [False, True])
def test_reentrant_failure_cannot_be_swallowed(stage, swallow):
    h = Harness()

    def reenter(*args):
        if swallow:
            try:
                h.ledger.finish()
            except ValueError:
                pass
        else:
            h.ledger.finish()
        return True

    options = {}
    if stage in ("record", "guard"):
        setattr(h.ledger, "_" + stage, reenter)
    elif stage == "compute":
        model = h.initialize()
        options["compute"] = reenter
    else:
        options[stage] = reenter
    with pytest.raises((ValueError, RuntimeError)):
        h.execute(model, **options) if stage == "compute" else h.initialize(**options)
    assert h.ledger.failed
    assert h.ledger.counts["operation"]["completed"] == 0


@pytest.mark.parametrize("result", [False, 1, None, np.bool_(True)])
def test_exact_true_validation_required(result):
    h = Harness()
    with pytest.raises(ValueError, match="exact True"):
        h.initialize(validate=lambda m: result)
    assert h.ledger.failed
    assert "publish" not in h.timeline


@pytest.mark.parametrize("reference", [None, {}, dict(REF, extra=1), dict(REF, bytes=True),
                                       dict(REF, path="relative.json"), dict(REF, sha256="B" * 64)])
def test_failed_raw_publication_never_completes(reference):
    h = Harness()
    with pytest.raises(ValueError):
        h.initialize(publish=lambda m: reference)
    assert h.ledger.failed
    assert h.ledger.counts["initialization"] == {"attempted": 1, "completed": 0}


def event(index=0, **changes):
    return dict(index=index, field="loop", quantity="A", points=256, status="attempted",
                started_monotonic=10.0, native_started=False, native_completed=False, **changes)


@pytest.mark.parametrize("key,value", [
    ("index", True), ("index", 1), ("points", 256.0), ("points", 255),
    ("field", "boundary"), ("quantity", "B"), ("status", "unknown"),
    ("started_monotonic", -1.0), ("started_monotonic", float("nan")),
    ("started_monotonic", True), ("native_started", 0), ("native_completed", 0),
    ("extra", 1),
])
def test_malformed_native_attempt_rejected_before_work(key, value):
    h = Harness()
    bad = event()
    bad[key] = value
    with pytest.raises(ValueError):
        h.initialize(factory=lambda callback: callback(bad))
    assert h.ledger.failed
    assert h.ledger.counts["native"] == {"attempted": 0, "completed": 0}


@pytest.mark.parametrize("fault", ["missing", "unpaired", "duplicate-attempt", "changed-start",
                                  "backward-end", "native-error", "extra", "callback-model"])
def test_native_pairing_failures(fault):
    h = Harness()

    def factory(callback):
        start = event()
        end = dict(start, status="completed", native_started=True, native_completed=True,
                   completed_monotonic=11.0)
        if fault == "missing":
            return object()
        if fault == "unpaired":
            callback(end)
        elif fault == "callback-model":
            h.ledger.native_event("diagnostic-1", start)
        else:
            callback(start)
            if fault == "duplicate-attempt":
                callback(start)
            elif fault == "changed-start":
                callback(dict(end, started_monotonic=10))
            elif fault == "backward-end":
                callback(dict(end, completed_monotonic=9.0))
            elif fault == "native-error":
                callback(dict(start, status="error", native_started=True,
                              failed_monotonic=11.0, error="synthetic failure"))
            else:
                callback(end)
                callback(dict(start, index=1, started_monotonic=12.0))
        return object()

    with pytest.raises((ValueError, RuntimeError)):
        h.initialize(factory=factory)
    assert h.ledger.failed
    assert h.ledger.counts["initialization"]["completed"] == 0


@pytest.mark.parametrize("hook", ["validate", "publish"])
def test_native_calls_not_allowed_in_validation_or_publication(hook):
    h = Harness()
    callbacks = []

    def factory(cb):
        callbacks.append(cb)
        return h.factory(cb)

    def attack(model):
        try:
            callbacks[0](event(index=1))
        except ValueError:
            pass
        return True if hook == "validate" else REF

    with pytest.raises(RuntimeError, match="failed"):
        h.initialize(factory=factory, **{hook: attack})
    assert h.ledger.failed
    assert h.ledger.counts["native"] == {"attempted": 1, "completed": 1}


def test_input_and_callback_containers_are_private():
    h = Harness()
    expected_case = copy.deepcopy(h.case)
    expected_x = h.x.copy()
    h.case["method"] = "V"
    h.x[1] = 99.0
    model = h.initialize()
    op = plan.operation_plan(h.specs[0], expected_x)[0]
    h.execute(model, h.specs[0], op)
    h.events[-1]["raw_reference"]["bytes"] = 1
    assert h.ledger._case == expected_case
    assert h.ledger._x.tobytes() == expected_x.tobytes()


def test_final_journal_failure_does_not_return_counts():
    h = Harness()
    original = h.ledger._record

    def fail_final(row):
        if row["event"] == "fine-dispatch-completed":
            raise OSError("synthetic final publication failure")
        original(row)

    h.ledger._record = fail_final
    with pytest.raises(OSError):
        h.all()
    assert h.ledger.failed
    assert h.ledger.counts["native"]["completed"] == 80


@pytest.mark.parametrize("trigger", ["operation-attempted", "native-attempted", "native-completed",
                                    "operation-completed", "fine-dispatch-completed"])
@pytest.mark.parametrize("fault", ["record", "guard-after-record"])
def test_each_publication_boundary_is_fail_stop(trigger, fault):
    failed_resource = False
    h = Harness()

    def record(row):
        nonlocal failed_resource
        h.events.append(row)
        if row["event"] == trigger:
            if fault == "record":
                raise OSError("synthetic durable record failure")
            failed_resource = True

    def guard():
        if failed_resource:
            raise TimeoutError("synthetic deadline during publication")

    h.ledger._record, h.ledger._guard = record, guard
    with pytest.raises((OSError, TimeoutError)):
        h.all()
    assert h.ledger.failed
    if trigger in ("operation-attempted", "native-attempted"):
        assert h.calls == []
    before = len(h.calls)
    with pytest.raises(RuntimeError):
        h.initialize()
    assert len(h.calls) == before


@pytest.mark.parametrize("stage", ["factory", "compute", "validate", "publish"])
def test_hook_exception_poisoning(stage):
    h = Harness()

    def fail(*args):
        raise OSError("synthetic callback failure")

    if stage == "compute":
        model = h.initialize()
    with pytest.raises(OSError):
        h.execute(model, compute=fail) if stage == "compute" else h.initialize(**{stage: fail})
    assert h.ledger.failed


def test_event_alias_mutation_by_recorder_cannot_change_pending_identity():
    h = Harness()
    original = event()

    def record(row):
        if row["event"] == "native-attempted":
            original["points"] = 1
            row["native"]["points"] = 2

    h.ledger._record = record

    def factory(callback):
        callback(original)
        callback(dict(event(), status="completed", native_started=True,
                      native_completed=True, completed_monotonic=11.0))
        return object()

    h.initialize(factory=factory)
    assert h.ledger.counts["points"] == {"attempted": 256, "completed": 256}


def test_backward_clock_across_models_rejected():
    h = Harness()
    model = h.initialize()
    h.execute(model)
    with pytest.raises(ValueError, match="backwards"):
        h.initialize(h.specs[1], factory=lambda cb: cb(event()))
    assert h.ledger.failed


def test_native_callback_outside_dispatch_poisoning():
    h = Harness()
    with pytest.raises(ValueError, match="outside"):
        h.ledger.native_event("diagnostic-0", event())
    assert h.ledger.failed


def test_reusing_model_identity_rejected_even_after_valid_initialization_callback():
    h = Harness()
    model = h.initialize()
    h.execute(model)

    def reuse(callback):
        h.factory(callback)
        return model

    with pytest.raises(ValueError, match="distinct"):
        h.initialize(h.specs[1], factory=reuse)
    assert h.ledger.failed


def test_missing_native_outcome_not_just_missing_attempt_fails():
    h = Harness()

    def factory(callback):
        callback(event())
        return object()

    with pytest.raises(ValueError, match="missing native outcomes"):
        h.initialize(factory=factory)
    assert h.ledger.failed
    assert h.ledger.counts["native"] == {"attempted": 1, "completed": 0}
