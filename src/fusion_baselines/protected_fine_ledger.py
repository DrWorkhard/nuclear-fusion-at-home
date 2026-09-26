"""Fixed fine-phase dispatch accounting, not a field or geometry verifier.

The trusted caller validates scientific outputs and publishes immutable raw
manifests. This ledger binds the full selected coordinate bytes, all eight model
identities, and the registered request order before any native dispatch. Any
failure permanently poisons it; callbacks cannot retry or hide failed work.
"""

import copy
import hashlib

from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_run_ledger import _clock, _reference, _require


class FineLedger:
    """Eight initializations, 24 operations, 80 calls and 552,960 point requests.

    ``record`` must durably append before returning. ``guard`` must raise on a
    failed resource/time check. Validators return exact True; publishers return
    a raw manifest reference. Its shape is checked here, not its file contents.
    This is a synchronous trusted-runner boundary, not an untrusted-code sandbox.
    """

    def __init__(self, case, selected_x, *, record, guard):
        plan.validate_case(case)
        _require(callable(record) and callable(guard), "record and guard must be callable")
        self._case = copy.deepcopy(case)
        self._x = plan._coordinates(case, selected_x)
        self._state_sha = hashlib.sha256(self._x.tobytes()).hexdigest()
        self._record, self._guard = record, guard
        self._queue = []
        for spec in plan.model_plan(case):
            self._queue.append((spec, None))
            self._queue.extend((spec, op) for op in plan.operation_plan(spec, self._x))
        self._position = 0
        self._failed = self._finished = self._busy = self._hook_active = False
        self._dispatching = False
        self._active = None
        self._models, self._indices = {}, {}
        self._last_clock = 0
        self._counts = {
            kind: {"attempted": 0, "completed": 0}
            for kind in ("initialization", "operation", "native", "points")
        }

    @property
    def counts(self):
        return copy.deepcopy(self._counts)

    @property
    def failed(self):
        return self._failed

    def _healthy(self):
        if self._failed:
            raise RuntimeError("fine ledger failed; preserve evidence and do not retry")

    def _hook(self, callback, *args):
        self._healthy()
        _require(not self._hook_active, "reentrant fine callback forbidden")
        self._hook_active = True
        try:
            value = callback(*args)
        finally:
            self._hook_active = False
        self._healthy()
        return value

    def _check(self):
        self._hook(self._guard)

    def _emit(self, event):
        self._hook(self._record, copy.deepcopy(event))

    def _transaction(self, action):
        entered = False
        try:
            self._healthy()
            _require(not self._finished, "fine ledger already finished")
            _require(not self._busy, "reentrant fine operation forbidden")
            self._busy = entered = True
            return action()
        except BaseException:
            self._failed = True
            raise
        finally:
            if entered:
                self._busy = False

    def _start(self, spec, operation):
        plan.validate_spec(spec)
        _require(self._position < len(self._queue), "registered fine sequence exhausted")
        expected_spec, expected_op = self._queue[self._position]
        _require(plan._same(spec, expected_spec), "exact next fine model required")
        if expected_op is None:
            _require(operation is None, "original-seed initialization required next")
        else:
            _require(operation is not None, "registered fine operation required next")
            plan.validate_operation(spec, operation, self._x)
            _require(
                operation["operation_id"] == expected_op["operation_id"],
                "exact next fine operation required",
            )
        identity = dict(
            kind="initialization" if operation is None else "operation",
            model_id=spec["id"],
            operation_id=f"initialize/{spec['id']}" if operation is None
            else operation["operation_id"],
            case=self._case["label"],
            selected_coordinate_sha256=self._state_sha,
            sequence=self._position,
        )
        self._active = dict(
            identity=identity, calls=plan.expected_calls(spec, operation), cursor=0, pending=None
        )
        self._check()
        self._emit(dict(event="operation-attempted", **identity))
        self._counts[identity["kind"]]["attempted"] += 1
        self._check()

    def _work(self, callback, *args):
        self._dispatching = True
        try:
            result = callback(*args)
        finally:
            self._dispatching = False
        self._healthy()
        _require(
            self._active["pending"] is None
            and self._active["cursor"] == len(self._active["calls"]),
            "fine operation missing native outcomes",
        )
        self._check()
        return result

    def _complete(self, result, validate, publish):
        _require(self._hook(validate, result) is True, "fine validation must return exact True")
        self._check()
        reference = _reference(self._hook(publish, result))
        self._check()
        identity = self._active["identity"]
        self._emit(dict(event="operation-completed", **identity, raw_reference=reference))
        self._check()
        self._counts[identity["kind"]]["completed"] += 1
        self._position += 1
        self._active = None

    def initialize(self, spec, *, factory, validate, publish):
        """Construct a fresh original-seed model via factory(native_callback)."""
        def action():
            self._start(spec, None)
            model_id = self._active["identity"]["model_id"]
            self._indices[model_id] = 0
            model = self._work(factory, lambda event: self.native_event(model_id, event))
            _require(model is not None, "fresh fine model required")
            _require(
                all(model is not prior for prior in self._models.values()),
                "distinct fresh fine model identity required",
            )
            self._complete(model, validate, publish)
            self._models[model_id] = model
            return model
        return self._transaction(action)

    def execute(self, model, spec, operation, *, compute, validate, publish):
        """compute(model) assigns fixed selected x and performs exactly this operation."""
        def action():
            self._start(spec, operation)
            model_id = self._active["identity"]["model_id"]
            _require(
                model_id in self._models and model is self._models[model_id],
                "owned initialized fine model required",
            )
            result = self._work(compute, model)
            self._complete(result, validate, publish)
            return result
        return self._transaction(action)

    def native_event(self, model_id, event):
        """Count paired actual requests. Only factory/compute may dispatch."""
        try:
            self._healthy()
            _require(
                self._busy and self._dispatching and not self._hook_active
                and self._active is not None,
                "native event outside fine factory/compute",
            )
            active = self._active
            _require(
                type(model_id) is str and model_id == active["identity"]["model_id"],
                "native callback fine model mismatch",
            )
            _require(type(event) is dict, "native event object required")
            event = copy.deepcopy(event)
            status = event.get("status")
            _require(
                type(status) is str and status in ("attempted", "completed", "error"),
                "native callback status",
            )
            extra = {"completed_monotonic"} if status == "completed" else (
                {"failed_monotonic", "error"} if status == "error" else set()
            )
            _require(
                all(type(key) is str for key in event) and set(event) == {
                    "index", "field", "quantity", "points", "status", "started_monotonic",
                    "native_started", "native_completed",
                } | extra,
                "exact native callback schema required",
            )
            _require(
                type(event["index"]) is int and event["index"] == self._indices[model_id],
                "exact per-model fine native index required",
            )
            _require(type(event["points"]) is int, "integer native point count required")
            _require(
                type(event["field"]) is str and type(event["quantity"]) is str,
                "exact native field and quantity required",
            )
            _require(active["cursor"] < len(active["calls"]), "too many fine native requests")
            _require(
                (event["field"], event["quantity"], event["points"])
                == active["calls"][active["cursor"]], "native fine field/order/points mismatch",
            )
            _clock(event["started_monotonic"])
            _require(event["started_monotonic"] >= self._last_clock, "native clock moved backwards")
            if status == "attempted":
                _require(active["pending"] is None, "unpaired native attempt")
                _require(
                    event["native_started"] is False and event["native_completed"] is False,
                    "native attempt flags must precede dispatch",
                )
                _require(
                    self._counts["native"]["attempted"] < 80
                    and self._counts["points"]["attempted"] + event["points"] <= 552960,
                    "registered fine native budget exhausted",
                )
                self._check()
                self._emit(dict(event="native-attempted", **active["identity"], native=event))
                self._counts["native"]["attempted"] += 1
                self._counts["points"]["attempted"] += event["points"]
                active["pending"] = copy.deepcopy(event)
                self._check()
            else:
                pending = active["pending"]
                _require(pending is not None, "native outcome without reservation")
                _require(
                    all(type(event[k]) is type(pending[k]) and event[k] == pending[k]
                        for k in ("index", "field", "quantity", "points", "started_monotonic")),
                    "native outcome changed request identity",
                )
                _require(
                    event["native_started"] is True
                    and event["native_completed"] is (status == "completed"),
                    "native outcome flags mismatch",
                )
                end = event["completed_monotonic" if status == "completed" else "failed_monotonic"]
                _clock(end)
                _require(end >= event["started_monotonic"], "native outcome clock precedes start")
                if status == "error":
                    _require(
                        type(event["error"]) is str and bool(event["error"]),
                        "native error required",
                    )
                self._check()
                self._emit(dict(event=f"native-{status}", **active["identity"], native=event))
                self._check()
                if status == "error":
                    raise RuntimeError("native fine request failed; do not retry")
                self._counts["native"]["completed"] += 1
                self._counts["points"]["completed"] += event["points"]
                self._indices[model_id] += 1
                self._last_clock = end
                active["pending"] = None
                active["cursor"] += 1
        except BaseException:
            self._failed = True
            raise

    def finish(self):
        """Return accounting only, after all fixed work and raw publications succeed."""
        def action():
            _require(self._position == 32 and self._active is None, "all fine work required")
            expected = {
                key: {"attempted": number, "completed": number}
                for key, number in (("initialization", 8), ("operation", 24),
                                    ("native", 80), ("points", 552960))
            }
            _require(self._counts == expected, "exact complete fine counts required")
            self._check()
            self._emit(dict(event="fine-dispatch-completed", case=self._case["label"],
                            selected_coordinate_sha256=self._state_sha, counts=self.counts))
            self._check()
            self._finished = True
            return self.counts
        return self._transaction(action)
