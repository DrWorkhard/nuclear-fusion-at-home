"""Pure fine clock/framing checks and tiny pipe I/O; no native calculations."""

import copy
import json
import os
import tempfile

import pytest

from fusion_baselines import protected_fine_control as control
from fusion_baselines.protected_search_journal import _encode


def reference():
    return dict(path="/synthetic/fine-returned.json", sha256="a" * 64, bytes=123)


def message(**changes):
    return dict(
        dict(schema_version=1, kind="fine_returned_result", monotonic=100.0, reference=reference()),
        **changes,
    )


@pytest.mark.parametrize("size", [1, 2, 7, 64, 4096])
def test_one_frame_at_arbitrary_boundaries_and_private_copies(size):
    wire = _encode(message())
    reader = control.FineControlReader(90.0)
    rows = []
    for at in range(0, len(wire), size):
        rows += reader.feed(wire[at : at + size], 110.0)
    assert rows == reader.finish() == [message()]
    assert reader.returned == reference()
    reader.messages[0]["monotonic"] = 0
    reader.returned["bytes"] = 1
    assert reader.messages == [message()] and reader.returned == reference()
    assert not hasattr(reader, "search_started")


@pytest.mark.parametrize("bad", [True, None, "0", -1, float("inf"), float("nan"), 10**1000])
def test_invalid_initial_clocks(bad):
    with pytest.raises(ValueError):
        control.FineControlReader(bad)


def test_exclusive_deadline_includes_entire_cell_and_sticky_failure():
    reader = control.FineControlReader(90.0)
    reader.feed(_encode(message()), 100.0)
    reader.finish()
    reader.check(1889.9999)
    with pytest.raises(TimeoutError, match="1800"):
        reader.check(1890)
    assert reader.failed
    with pytest.raises(RuntimeError):
        reader.check(100)


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": True},
        {"kind": "search_started"},
        {"kind": "search_ended"},
        {"kind": "returned_result"},
        {"kind": "unknown"},
        {"extra": False},
        {"monotonic": True},
        {"monotonic": 89},
        {"monotonic": 111},
        {"reference": {}},
        {"reference": dict(reference(), bytes=True)},
    ],
)
def test_exact_schema_and_clock_scope(changes):
    reader = control.FineControlReader(90.0)
    with pytest.raises(ValueError):
        reader.feed(_encode(message(**changes)), 110.0)
    assert reader.failed
    with pytest.raises(RuntimeError):
        reader.feed(b"", 110.0)


@pytest.mark.parametrize(
    "wire",
    [
        b"not-json\n",
        b"\xff\n",
        b"\n",
        b"[]\n",
        b'{"kind":"fine_returned_result","kind":"fine_returned_result"}\n',
        json.dumps(message()).encode() + b"\n",
        _encode(message()) + b"x",
        _encode(message()) + _encode(message()),
    ],
)
def test_invalid_noncanonical_duplicate_or_extra_wire(wire):
    reader = control.FineControlReader(90.0)
    with pytest.raises(ValueError):
        reader.feed(wire, 110.0)
        reader.finish()
    assert reader.failed


@pytest.mark.parametrize("wire", [b"", _encode(message())[:-1]])
def test_missing_or_truncated_return_is_not_completion(wire):
    reader = control.FineControlReader(90.0)
    reader.feed(wire, 110.0)
    with pytest.raises(ValueError, match="complete"):
        reader.finish()


@pytest.mark.parametrize("wire", [b"x" * 4096, b"x" * 4097, b"x" * 4096 + b"\n"])
def test_preparse_bounds(monkeypatch, wire):
    monkeypatch.setattr(control.json, "loads", lambda *a, **k: pytest.fail("unbounded parse"))
    reader = control.FineControlReader(0.0)
    with pytest.raises(ValueError, match="limit|bounded"):
        reader.feed(wire, 1.0)


def test_incremental_extra_frame_and_backwards_parent_clock_fail():
    reader = control.FineControlReader(90.0)
    reader.feed(_encode(message()), 110.0)
    with pytest.raises(ValueError, match="extra"):
        reader.feed(b"x", 110.0)
    reader = control.FineControlReader(90.0)
    reader.check(110.0)
    with pytest.raises(ValueError, match="backwards"):
        reader.feed(_encode(message()), 109.0)


@pytest.mark.parametrize("action", ["feed", "finish"])
def test_reader_cannot_resume_after_finish(action):
    reader = control.FineControlReader(90.0)
    reader.feed(_encode(message()), 110.0)
    reader.finish()
    with pytest.raises(ValueError):
        reader.feed(b"", 110.0) if action == "feed" else reader.finish()


def test_real_atomic_pipe_and_no_reference_file_access():
    read_fd, write_fd = os.pipe()
    try:
        control.send_fine_control(write_fd, message())
        assert os.read(read_fd, 4096) == _encode(message())
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_regular_file_is_not_a_pipe():
    with tempfile.TemporaryFile() as f:
        with pytest.raises(ValueError, match="pipe"):
            control.send_fine_control(f.fileno(), message())
        assert f.tell() == 0


@pytest.mark.parametrize("fault", ["atomic-limit", "partial", "raised"])
def test_ambiguous_control_write_never_retries(monkeypatch, fault):
    monkeypatch.setattr(control.os, "fstat", lambda fd: type("Stat", (), {"st_mode": 0o010000})())
    monkeypatch.setattr(
        control.os, "fpathconf", lambda *args: 2 if fault == "atomic-limit" else 4096
    )
    calls = []

    def write(*args):
        calls.append(args)
        if fault == "raised":
            raise OSError("injected write")
        return 1

    monkeypatch.setattr(control.os, "write", write)
    with pytest.raises((ValueError, OSError)):
        control.send_fine_control(3, message())
    assert len(calls) == (0 if fault == "atomic-limit" else 1)


class Harness:
    def __init__(self):
        self.now = 100.0
        self.parent = 1234
        self.sent = []
        self.resources = 0
        self.control = control.FineWorkerControl(
            90.0,
            self.parent,
            self.sent.append,
            self.resource,
            clock=lambda: self.now,
            parent=lambda: self.parent,
        )

    def resource(self):
        self.resources += 1


def test_worker_single_return_and_no_postreturn_dispatch():
    h = Harness()
    h.control.check()
    assert h.control.returned(reference()) == message()
    assert h.sent == [message()]
    with pytest.raises(ValueError, match="already returned"):
        h.control.check()
    with pytest.raises(RuntimeError):
        h.control.returned(reference())


def test_parent_death_and_resource_clock_cost_poison_worker():
    h = Harness()
    h.parent = 1
    with pytest.raises(ValueError, match="parent identity"):
        h.control.check()
    with pytest.raises(RuntimeError):
        h.control.returned(reference())
    h = Harness()
    h.control._resource = lambda: setattr(h, "now", 1890.0)
    with pytest.raises(TimeoutError):
        h.control.check()


@pytest.mark.parametrize("callback", ["_resource", "_send", "_clock", "_parent"])
@pytest.mark.parametrize("fault", ["raised", "swallowed-reentry"])
def test_callback_errors_poison_before_later_forwarding(callback, fault):
    h = Harness()
    original = getattr(h.control, callback)

    def bad(*args):
        if fault == "raised":
            raise OSError("injected hook")
        with pytest.raises(ValueError, match="reentrant"):
            h.control.check()
        return original(*args)

    setattr(h.control, callback, bad)
    with pytest.raises((OSError, RuntimeError)):
        h.control.returned(reference())
    old = copy.deepcopy(h.sent)
    with pytest.raises(RuntimeError):
        h.control.returned(reference())
    assert h.sent == old
