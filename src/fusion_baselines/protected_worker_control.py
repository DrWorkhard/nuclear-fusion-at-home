"""Bounded POSIX worker control and cooperative phase guards; no scientific work.

A living parent enforces deadlines even during a blocked native request. Worker
parent-identity checks are cooperative, not OS-level kill-on-parent-death support.
"""

import copy
import json
import math
import os
import stat
import time

from fusion_baselines.protected_run_ledger import _reference
from fusion_baselines.protected_search_journal import _encode, _unique_object

CELL_SECONDS = 1800.0
SEARCH_SECONDS = 600.0
MAX_FRAME_BYTES = 4096
THREADS = {
    key: "1"
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    )
}
KINDS = ("search_started", "search_ended", "returned_result")


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _clock(value):
    _need(type(value) in (int, float), "plain finite nonnegative clock required")
    try:
        valid = math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    _need(valid, "plain finite nonnegative clock required")
    return value


def _message(value):
    _need(type(value) is dict and value.get("kind") in KINDS, "registered control message")
    keys = {"schema_version", "kind", "monotonic"}
    if value["kind"] == "returned_result":
        keys.add("reference")
        _reference(value.get("reference"))
    _need(
        set(value) == keys
        and type(value["schema_version"]) is int
        and value["schema_version"] == 1,
        "exact control message schema",
    )
    _clock(value["monotonic"])
    return copy.deepcopy(value)


def send_control(fd, message):
    """One atomic bounded write; no retry after an ambiguous/partial publication."""
    _need(type(fd) is int and fd >= 0, "control pipe descriptor required")
    _need(stat.S_ISFIFO(os.fstat(fd).st_mode), "dedicated control pipe required")
    raw = _encode(_message(message))
    _need(len(raw) <= MAX_FRAME_BYTES, "control frame limit exceeded")
    _need(len(raw) <= os.fpathconf(fd, "PC_PIPE_BUF"), "one atomic pipe frame required")
    _need(os.write(fd, raw) == len(raw), "short control write; do not retry")


class ControlReader:
    """Strict ordered control stream with bounded pre-parse buffering and clocks."""

    def __init__(self, started):
        self.started = _clock(started)
        self._last_now = started
        self._messages = []
        self._buffer = b""
        self._failed = False
        self._finished = False

    @property
    def failed(self):
        return self._failed

    @property
    def messages(self):
        return copy.deepcopy(self._messages)

    @property
    def search_started(self):
        return self._messages[0]["monotonic"] if self._messages else None

    @property
    def search_ended(self):
        return self._messages[1]["monotonic"] if len(self._messages) >= 2 else None

    @property
    def returned(self):
        return copy.deepcopy(self._messages[2]["reference"]) if len(self._messages) == 3 else None

    def _healthy(self):
        if self._failed:
            raise RuntimeError("worker control failed; do not resume")

    def _now(self, now):
        _clock(now)
        _need(now >= self._last_now, "parent/worker observation clock moved backwards")
        self._last_now = now
        if now - self.started >= CELL_SECONDS:
            raise TimeoutError("protected cell exceeded 1800-second deadline")

    def check(self, now):
        try:
            self._healthy()
            self._now(now)
            if self.search_started is not None and self.search_ended is None:
                if now - self.search_started >= SEARCH_SECONDS:
                    raise TimeoutError("protected search exceeded 600-second deadline")
        except BaseException:
            self._failed = True
            raise

    def feed(self, data, now):
        try:
            self._healthy()
            _need(not self._finished, "control stream already finished")
            self._now(now)
            _need(
                type(data) is bytes and len(self._buffer) + len(data) <= 3 * MAX_FRAME_BYTES,
                "bounded binary control chunk required",
            )
            buffer = self._buffer + data
            new = []
            while b"\n" in buffer:
                end = buffer.index(b"\n") + 1
                _need(end <= MAX_FRAME_BYTES, "control frame limit exceeded before parsing")
                raw, buffer = buffer[:end], buffer[end:]
                _need(len(self._messages) < 3, "extra control message")
                value = _message(json.loads(raw, object_pairs_hook=_unique_object))
                _need(_encode(value) == raw, "canonical finite control JSON required")
                _need(
                    value["kind"] == KINDS[len(self._messages)], "ordered control phases required"
                )
                previous = self.started if not self._messages else self._messages[-1]["monotonic"]
                _need(previous <= value["monotonic"] <= now, "bounded forward phase clock required")
                if value["kind"] == "search_ended":
                    if value["monotonic"] - self.search_started >= SEARCH_SECONDS:
                        raise TimeoutError("recorded search exceeded 600-second deadline")
                self._messages.append(value)
                new.append(copy.deepcopy(value))
            _need(len(buffer) < MAX_FRAME_BYTES, "unterminated control frame limit exceeded")
            self._buffer = buffer
            self.check(now)
            return new
        except BaseException:
            self._failed = True
            raise

    def finish(self):
        try:
            self._healthy()
            _need(
                not self._finished and not self._buffer and len(self._messages) == 3,
                "complete control stream and explicit returned result required",
            )
            self._finished = True
            return self.messages
        except BaseException:
            self._failed = True
            raise


class WorkerControl:
    """Phase timer plus permanent failure state at every cooperative boundary."""

    def __init__(
        self, started, parent_pid, send, resource_check, *, clock=time.monotonic, parent=os.getppid
    ):
        _need(type(parent_pid) is int and parent_pid > 1, "original parent PID required")
        _need(
            all(callable(f) for f in (send, resource_check, clock, parent)),
            "explicit synchronous control callbacks required",
        )
        self.reader = ControlReader(started)
        self._parent_pid, self._send, self._resource = parent_pid, send, resource_check
        self._clock, self._parent = clock, parent
        self._failed, self._active = False, False

    def _healthy(self):
        if self._failed or self.reader.failed:
            self._failed = True
            raise RuntimeError("worker phase guard failed; no further dispatch")

    def _enter(self):
        self._healthy()
        _need(not self._active, "reentrant worker guard/control callback")
        self._active = True

    def _check(self):
        parent = self._parent()
        self._healthy()
        _need(type(parent) is int and parent == self._parent_pid, "worker parent identity changed")
        self.reader.check(self._clock())
        self._healthy()
        self._resource()
        self._healthy()
        self.reader.check(self._clock())
        self._healthy()

    def check(self):
        try:
            self._enter()
            self._check()
        except BaseException:
            self._failed = True
            raise
        finally:
            self._active = False

    def signal(self, kind, reference=None):
        try:
            self._enter()
            self._check()
            now = self._clock()
            self._healthy()
            message = dict(schema_version=1, kind=kind, monotonic=now)
            if reference is not None:
                message["reference"] = copy.deepcopy(reference)
            # Validate before sending, without opening any result path.
            self.reader.feed(_encode(_message(message)), now)
            self._send(copy.deepcopy(message))
            self._healthy()
            self._check()
            return message
        except BaseException:
            self._failed = True
            raise
        finally:
            self._active = False


class PhaseJournal:
    """Transparent payload forwarding with the registered search-clock boundaries."""

    def __init__(self, journal, control, kind):
        _need(kind in ("native", "controller"), "registered journal role")
        self.journal, self.control, self.kind = journal, control, kind
        self._failed = False
        self._active = False
        self._directory = journal._directory

    @property
    def receipt(self):
        return self.journal.receipt

    def __call__(self, event):
        try:
            _need(not self._failed and not self._active, "failed/reentrant phase journal")
            self._active = True
            self.control.check()
            if self.kind == "controller" and event.get("event") == "search_started":
                self.control.signal("search_started")
            if self.kind == "native" and all(
                event.get(k) == v
                for k, v in dict(
                    event="operation-attempted",
                    kind="initialization",
                    phase="replay",
                    model_id="replay",
                ).items()
            ):
                self.control.signal("search_ended")
            result = self.journal(copy.deepcopy(event))
            _need(
                not self._failed and getattr(self.journal, "_failed", False) is not True,
                "phase journal poisoned during callback",
            )
            self.control.check()
            return result
        except BaseException:
            self._failed = True
            raise
        finally:
            self._active = False
