"""Single-cell, single-writer dispatch accounting, not physical verification.

The caller owns real validation, immutable raw publication and source admission.
Callbacks are synchronous; any failure permanently poisons this ledger. Model
factories must construct the original seed, and invalidators must actually clear
the model cache. Those scientific assertions require the separate runner/audit.
"""

import copy
import math
from pathlib import Path

CERT_LIMITS = {"startup": 10, "search-seed": 1, "trial": 116, "replay": 1}
BUNDLE_LIMITS = {"startup": 10, "search-seed": 1, "trial": 20, "replay": 1}
BUNDLE_CALLS = (
    ("boundary", "B", 4096),
    ("inner", "B", 3072),
    ("loop", "A", 256),
    ("boundary", "B_vjp", 4096),
    ("inner", "B_vjp", 3072),
    ("loop", "A_vjp", 256),
    ("boundary", "A", 4096),
    ("inner", "A", 3072),
    ("loop", "B", 256),
)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _name(value):
    _require(type(value) is str and 0 < len(value) <= 256, "bounded nonempty identifier")


def _sha(value):
    _require(
        type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value),
        "lowercase SHA256 required",
    )


def _clock(value):
    _require(type(value) in (int, float), "finite nonnegative native clock required")
    try:
        valid = math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    _require(valid, "finite nonnegative native clock required")


def _reference(value):
    _require(
        type(value) is dict and set(value) == {"path", "sha256", "bytes"},
        "published manifest reference requires path, sha256 and bytes",
    )
    _require(
        type(value["path"]) is str and 0 < len(value["path"]) <= 4096,
        "published manifest path required",
    )
    _require(Path(value["path"]).is_absolute(), "absolute published manifest path required")
    _sha(value["sha256"])
    _require(
        type(value["bytes"]) is int and value["bytes"] > 0,
        "positive integer published bytes required",
    )
    return copy.deepcopy(value)


def _counts(phases):
    return {phase: {"attempted": 0, "completed": 0} for phase in phases}


class ProtectedRunLedger:
    """Explicit wrappers for the registered 10+1+20+1 bundle sequence.

    ``record(event)`` must durably publish before returning; ``guard()`` must
    raise on resource/time failure. Publishers return a single immutable raw
    manifest reference; the ledger validates its shape, not its content/files.
    Validators for initialize/bundle return exact True, and certificate validators
    return exact bool. A false certificate is a valid, persisted rejection.
    """

    def __init__(self, *, record, guard):
        _require(callable(record) and callable(guard), "record and guard must be callable")
        self._record, self._guard = record, guard
        self._failed = False
        self._hook_active = False
        self._active = None
        self._models = {}
        self._indices = {"main": 0, "replay": 0}
        self._last_clock = {"main": 0, "replay": 0}
        self._pending_certificate = None
        self._ids = set()
        self._counts = dict(
            initialization=_counts(("main", "replay")),
            certificate=_counts(CERT_LIMITS),
            bundle=_counts(BUNDLE_LIMITS),
            native={"attempted": 0, "completed": 0},
        )

    @property
    def counts(self):
        """Independent copy; attempted work can exceed completed work after failure."""
        return copy.deepcopy(self._counts)

    @property
    def failed(self):
        return self._failed

    def _healthy(self):
        if self._failed:
            raise RuntimeError("ledger failed; preserve this cell and do not retry")

    def _ready(self):
        self._healthy()
        _require(not self._hook_active, "reentrant guard/record callback forbidden")
        _require(self._active is None, "another operation is active")

    def _hook(self, callback, *args):
        self._healthy()
        _require(not self._hook_active, "reentrant guard/record callback forbidden")
        self._hook_active = True
        try:
            callback(*args)
        finally:
            self._hook_active = False
        self._healthy()

    def _emit(self, event):
        self._hook(self._record, copy.deepcopy(event))

    def _check_guard(self):
        self._hook(self._guard)

    def _done(self, kind, phase):
        return self._counts[kind][phase]["completed"]

    def _phase(self, phase):
        _require(type(phase) is str and phase in CERT_LIMITS, "registered phase required")
        _require(self._done("initialization", "main") == 1, "main initialization required")
        if phase == "startup":
            _require(
                self._done("initialization", "replay") == 0
                and self._done("certificate", "startup") == self._done("bundle", "startup")
                and self._done("bundle", "search-seed") == 0,
                "startup ordering",
            )
        else:
            _require(self._done("bundle", "startup") == 10, "ten startup bundles required")
            if phase == "search-seed":
                _require(self._done("initialization", "replay") == 0, "search seed before replay")
            else:
                _require(self._done("bundle", "search-seed") == 1, "fresh search seed required")
                _require(
                    self._done("initialization", "replay") == int(phase == "replay"),
                    "trial/replay model ordering",
                )

    def _start(self, kind, phase, operation_id, **details):
        _name(operation_id)
        _require(operation_id not in self._ids, "operation identifier already used")
        _require(
            self._pending_certificate is None or kind == "bundle",
            "positive certificate must be consumed by its bundle",
        )
        limits = {
            "initialization": {"main": 1, "replay": 1},
            "certificate": CERT_LIMITS,
            "bundle": BUNDLE_LIMITS,
        }[kind]
        _require(self._counts[kind][phase]["attempted"] < limits[phase], "phase budget exhausted")
        self._check_guard()
        operation = dict(kind=kind, phase=phase, operation_id=operation_id, **details)
        self._emit(dict(event="operation-attempted", **operation))
        self._counts[kind][phase]["attempted"] += 1
        self._ids.add(operation_id)
        self._active = dict(operation=operation, calls=(), cursor=0, pending=None)

    def _complete(self, raw_reference, **details):
        self._healthy()
        operation = self._active["operation"]
        _require(
            self._active["pending"] is None
            and self._active["cursor"] == len(self._active["calls"]),
            "operation missing native outcomes",
        )
        self._check_guard()
        self._emit(
            dict(
                event="operation-completed",
                **operation,
                raw_reference=_reference(raw_reference),
                **details,
            )
        )
        self._counts[operation["kind"]][operation["phase"]]["completed"] += 1
        self._active = None

    def initialize(self, model_id, *, factory, validate, publish):
        """factory(callback) constructs one fresh original-seed model and one loop A."""
        try:
            self._ready()
            _require(
                type(model_id) is str and model_id in ("main", "replay"),
                "model must be main or replay",
            )
            if model_id == "replay":
                _require(self._done("bundle", "search-seed") == 1, "search before replay model")
            self._start("initialization", model_id, f"initialize/{model_id}", model_id=model_id)
            self._active["calls"] = (("loop", "A", 256),)
            model = factory(lambda event: self.native_event(model_id, event))
            self._healthy()
            _require(
                all(model is not prior for prior in self._models.values()),
                "a fresh model identity is required",
            )
            _require(validate(model) is True, "initialization validation must pass")
            self._healthy()
            self._complete(publish(model))
            self._models[model_id] = model
            return model
        except BaseException:
            self._failed = True
            raise

    def certificate(self, phase, operation_id, state_sha256, *, compute, validate, publish):
        """Return the raw certificate; its validator supplies only the certified bool."""
        try:
            self._ready()
            self._phase(phase)
            _sha(state_sha256)
            self._start("certificate", phase, operation_id, state_sha256=state_sha256)
            result = compute()
            self._healthy()
            certified = validate(result)
            self._healthy()
            _require(type(certified) is bool, "certificate validator must return exact bool")
            self._complete(publish(result), certified=certified)
            if certified:
                self._pending_certificate = (phase, operation_id, state_sha256)
            return result
        except BaseException:
            self._failed = True
            raise

    def bundle(
        self,
        phase,
        operation_id,
        state_sha256,
        *,
        certificate_id,
        invalidate,
        compute,
        validate,
        publish,
    ):
        """Invalidate, compute nine exact native requests, validate and publish raw data."""
        try:
            self._ready()
            _require(type(phase) is str and phase in BUNDLE_LIMITS, "registered bundle phase")
            _sha(state_sha256)
            _name(certificate_id)
            _require(
                self._pending_certificate == (phase, certificate_id, state_sha256),
                "matching unconsumed positive certificate required",
            )
            model_id = "replay" if phase == "replay" else "main"
            self._start(
                "bundle",
                phase,
                operation_id,
                state_sha256=state_sha256,
                certificate_id=certificate_id,
                model_id=model_id,
            )
            self._active["calls"] = BUNDLE_CALLS
            model = self._models[model_id]
            invalidate(model)
            self._healthy()
            result = compute(model)
            self._healthy()
            _require(validate(result) is True, "bundle validation must pass")
            self._healthy()
            self._complete(publish(result))
            self._pending_certificate = None
            return result
        except BaseException:
            self._failed = True
            raise

    def native_event(self, model_id, event):
        """Strict CountedField callback, bound to the initialized model identity."""
        try:
            if self._failed:
                raise RuntimeError("ledger failed; native dispatch forbidden")
            _require(not self._hook_active, "reentrant guard/record callback forbidden")
            _require(self._active is not None, "native callback outside an operation")
            active = self._active
            operation = active["operation"]
            _require(
                operation.get("model_id") == model_id and model_id in self._indices,
                "native callback model mismatch",
            )
            _require(type(event) is dict, "native event object required")
            base = {
                "index",
                "field",
                "quantity",
                "points",
                "status",
                "started_monotonic",
                "native_started",
                "native_completed",
            }
            status = event.get("status")
            _require(
                type(status) is str and status in ("attempted", "completed", "error"),
                "native callback status",
            )
            extra = (
                {"completed_monotonic"}
                if status == "completed"
                else {"error", "failed_monotonic"}
                if status == "error"
                else set()
            )
            _require(set(event) == base | extra, "exact native callback schema required")
            _require(
                type(event["index"]) is int and event["index"] == self._indices[model_id],
                "exact per-model native index required",
            )
            _require(type(event["points"]) is int, "integer native point count required")
            _require(
                type(event["field"]) is str and type(event["quantity"]) is str,
                "exact native field and quantity strings required",
            )
            _require(
                type(event["native_started"]) is bool and type(event["native_completed"]) is bool,
                "boolean native flags required",
            )
            _require(active["cursor"] < len(active["calls"]), "too many native requests")
            _require(
                (event["field"], event["quantity"], event["points"])
                == active["calls"][active["cursor"]],
                "native field/order/points mismatch",
            )
            _clock(event["started_monotonic"])
            _require(
                event["started_monotonic"] >= self._last_clock[model_id],
                "native clock moved backwards",
            )
            if status == "attempted":
                _require(active["pending"] is None, "unpaired native attempt")
                _require(
                    event["native_started"] is False and event["native_completed"] is False,
                    "native attempt flags must precede dispatch",
                )
                _require(self._counts["native"]["attempted"] < 290, "native budget exhausted")
                self._check_guard()
                self._emit(dict(event="native-attempted", **operation, native=event))
                self._counts["native"]["attempted"] += 1
                active["pending"] = copy.deepcopy(event)
            else:
                pending = active["pending"]
                _require(pending is not None, "native outcome without reservation")
                _require(
                    all(
                        type(event[k]) is type(pending[k]) and event[k] == pending[k]
                        for k in ("index", "field", "quantity", "points", "started_monotonic")
                    ),
                    "native outcome changed request identity",
                )
                _require(
                    event["native_started"] is True
                    and event["native_completed"] is (status == "completed"),
                    "native outcome flags mismatch",
                )
                clock = event[
                    "completed_monotonic" if status == "completed" else "failed_monotonic"
                ]
                _clock(clock)
                _require(clock >= event["started_monotonic"], "native outcome clock precedes start")
                if status == "error":
                    _require(
                        type(event["error"]) is str and bool(event["error"]),
                        "native error description required",
                    )
                self._check_guard()
                self._emit(dict(event=f"native-{status}", **operation, native=event))
                if status == "error":
                    raise RuntimeError("native request failed; execution poisoned")
                self._counts["native"]["completed"] += 1
                self._indices[model_id] += 1
                self._last_clock[model_id] = clock
                active["pending"] = None
                active["cursor"] += 1
        except BaseException:
            self._failed = True
            raise
