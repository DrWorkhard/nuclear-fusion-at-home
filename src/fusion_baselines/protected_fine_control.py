"""One returned-reference fine-worker stream; no search phases or scientific work.

The parent enforces the wall deadline while a child is blocked. Worker parent
checks are cooperative, not an OS-level kill-on-parent-death guarantee.
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
RETURN_KIND = "fine_returned_result"


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
    _need(
        type(value) is dict
        and set(value) == {"schema_version", "kind", "monotonic", "reference"}
        and type(value["schema_version"]) is int
        and value["schema_version"] == 1
        and value["kind"] == RETURN_KIND,
        "exact fine returned-reference schema required",
    )
    _clock(value["monotonic"])
    _reference(value["reference"])
    return copy.deepcopy(value)


def send_fine_control(fd, message):
    """One bounded atomic pipe write; never retry an ambiguous publication."""
    _need(type(fd) is int and fd >= 0, "control pipe descriptor required")
    _need(stat.S_ISFIFO(os.fstat(fd).st_mode), "dedicated control pipe required")
    raw = _encode(_message(message))
    _need(len(raw) <= MAX_FRAME_BYTES, "fine control frame limit exceeded")
    _need(len(raw) <= os.fpathconf(fd, "PC_PIPE_BUF"), "one atomic pipe frame required")
    _need(os.write(fd, raw) == len(raw), "short fine control write; do not retry")


class FineControlReader:
    """Bounded canonical one-frame parser with permanent failure and wall clock."""

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
    def returned(self):
        return copy.deepcopy(self._messages[0]["reference"]) if self._messages else None

    def _healthy(self):
        if self._failed:
            raise RuntimeError("fine worker control failed; do not resume")

    def _now(self, now):
        _clock(now)
        _need(now >= self._last_now, "fine observation clock moved backwards")
        self._last_now = now
        if now - self.started >= CELL_SECONDS:
            raise TimeoutError("protected fine cell exceeded 1800-second deadline")

    def check(self, now):
        try:
            self._healthy()
            self._now(now)
        except BaseException:
            self._failed = True
            raise

    def feed(self, data, now):
        try:
            self._healthy()
            _need(not self._finished, "fine control stream already finished")
            self._now(now)
            _need(
                type(data) is bytes and len(self._buffer) + len(data) <= MAX_FRAME_BYTES,
                "bounded binary fine control chunk required",
            )
            buffer = self._buffer + data
            new = []
            if b"\n" in buffer:
                end = buffer.index(b"\n") + 1
                _need(end <= MAX_FRAME_BYTES, "fine control frame limit exceeded before parsing")
                _need(not self._messages, "extra fine control message")
                raw, buffer = buffer[:end], buffer[end:]
                value = _message(json.loads(raw, object_pairs_hook=_unique_object))
                _need(_encode(value) == raw, "canonical finite fine control JSON required")
                _need(
                    self.started <= value["monotonic"] <= now,
                    "bounded forward fine return clock required",
                )
                self._messages.append(value)
                new.append(copy.deepcopy(value))
            _need(len(buffer) < MAX_FRAME_BYTES, "unterminated fine control frame limit exceeded")
            _need(not self._messages or not buffer, "extra bytes after fine return frame")
            self._buffer = buffer
            return new
        except BaseException:
            self._failed = True
            raise

    def finish(self):
        try:
            self._healthy()
            _need(
                not self._finished and not self._buffer and len(self._messages) == 1,
                "complete fine stream and explicit returned reference required",
            )
            self._finished = True
            return self.messages
        except BaseException:
            self._failed = True
            raise


class FineWorkerControl:
    """Fail-stop cooperative worker guard and exactly one explicit return."""

    def __init__(
        self, started, parent_pid, send, resource_check, *, clock=time.monotonic, parent=os.getppid
    ):
        _need(type(parent_pid) is int and parent_pid > 1, "original parent PID required")
        _need(
            all(callable(f) for f in (send, resource_check, clock, parent)),
            "explicit synchronous fine control callbacks required",
        )
        self.reader = FineControlReader(started)
        self._parent_pid, self._send, self._resource = parent_pid, send, resource_check
        self._clock, self._parent = clock, parent
        self._failed = self._active = self._done = False

    def _healthy(self):
        if self._failed or self.reader.failed:
            self._failed = True
            raise RuntimeError("fine worker guard failed; no further dispatch")

    def _operation(self, action):
        entered = False
        try:
            self._healthy()
            _need(not self._done, "fine worker already returned; no further dispatch")
            _need(not self._active, "reentrant fine worker guard/control callback")
            self._active = entered = True
            return action()
        except BaseException:
            self._failed = True
            raise
        finally:
            if entered:
                self._active = False

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
        return self._operation(self._check)

    def returned(self, reference):
        def action():
            self._check()
            now = self._clock()
            self._healthy()
            message = _message(
                dict(schema_version=1, kind=RETURN_KIND, monotonic=now, reference=reference)
            )
            self.reader.feed(_encode(message), now)
            self._send(copy.deepcopy(message))
            self._healthy()
            self._check()
            self.reader.finish()
            self._done = True
            return message

        return self._operation(action)
