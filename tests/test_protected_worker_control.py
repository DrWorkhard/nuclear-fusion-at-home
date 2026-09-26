"""Pure clock/framing tests and real tiny POSIX pipe I/O, never native physics."""

import copy
import json
import os
import tempfile

import pytest

from fusion_baselines import protected_worker_control as control
from fusion_baselines.protected_search_journal import EventJournal, _encode, read_events


def message(kind, monotonic, **extra):
    return dict(schema_version=1, kind=kind, monotonic=monotonic, **extra)


def reference():
    return dict(path="/synthetic/returned.json", sha256="a" * 64, bytes=123)


def messages():
    return [
        message("search_started", 100.0),
        message("search_ended", 200.0),
        message("returned_result", 210.0, reference=reference()),
    ]


def test_complete_control_frames_at_arbitrary_byte_boundaries():
    wire = b"".join(_encode(v) for v in messages())
    for size in (1, 2, 7, 64, len(wire)):
        reader = control.ControlReader(90.0)
        emitted = []
        for at in range(0, len(wire), size):
            emitted += reader.feed(wire[at : at + size], 220.0)
        assert emitted == reader.finish() == messages()
        assert reader.search_started == 100.0 and reader.search_ended == 200.0
        assert reader.returned == reference()
        changed = reader.messages
        changed[0]["monotonic"] = 0.0
        assert reader.search_started == 100.0


@pytest.mark.parametrize("value", [True, None, "0", -1.0, float("inf"), float("nan"), 10**1000])
def test_bad_initial_clocks(value):
    with pytest.raises(ValueError):
        control.ControlReader(value)


def test_exclusive_cell_and_search_boundaries_and_sticky_failure():
    reader = control.ControlReader(90.0)
    reader.check(1889.9999)
    with pytest.raises(TimeoutError, match="1800"):
        reader.check(1890.0)
    assert reader.failed
    with pytest.raises(RuntimeError):
        reader.check(100.0)
    reader = control.ControlReader(90.0)
    reader.feed(_encode(messages()[0]), 100.0)
    reader.check(699.9999)
    with pytest.raises(TimeoutError, match="600"):
        reader.check(700.0)


def test_completed_search_cannot_hide_an_overlong_recorded_interval():
    reader = control.ControlReader(90.0)
    with pytest.raises(TimeoutError, match="recorded search"):
        reader.feed(_encode(messages()[0]) + _encode(message("search_ended", 700.0)), 710.0)


def test_clock_does_not_restart_at_parent_receipt_and_valid_ended_interval_is_preserved():
    reader = control.ControlReader(90.0)
    with pytest.raises(TimeoutError, match="600"):
        reader.feed(_encode(messages()[0]), 701.0)
    reader = control.ControlReader(90.0)
    reader.feed(_encode(messages()[0]) + _encode(message("search_ended", 699.9999)), 710.0)
    reader.check(1800.0)


@pytest.mark.parametrize(
    "case",
    [
        "out-of-order",
        "duplicate",
        "missing",
        "tail",
        "extra",
        "unknown",
        "future",
        "backward",
        "before-start",
        "bool-clock",
        "bool-schema",
        "unknown-key",
        "reference",
    ],
)
def test_malformed_stream_fails_permanently(case):
    values = messages()
    if case == "out-of-order":
        values.reverse()
    elif case == "duplicate":
        values.insert(1, values[0])
    elif case == "missing":
        values.pop()
    elif case == "extra":
        values.append(values[-1])
    elif case == "unknown":
        values[0]["kind"] = "ready"
    elif case == "future":
        values[0]["monotonic"] = 1000.0
    elif case == "backward":
        values[1]["monotonic"] = 99.0
    elif case == "before-start":
        values[0]["monotonic"] = 89.0
    elif case == "bool-clock":
        values[0]["monotonic"] = True
    elif case == "bool-schema":
        values[0]["schema_version"] = True
    elif case == "unknown-key":
        values[0]["extra"] = None
    elif case == "reference":
        values[-1]["reference"]["bytes"] = True
    wire = b"".join(_encode(v) for v in values) + (b"{" if case == "tail" else b"")
    reader = control.ControlReader(90.0)
    with pytest.raises(ValueError):
        reader.feed(wire, 220.0)
        reader.finish()
    assert reader.failed
    with pytest.raises(RuntimeError):
        reader.feed(b"", 220.0)


@pytest.mark.parametrize(
    "wire",
    [
        b"not-json\n",
        b"\xff\n",
        b"\n",
        b"[]\n",
        b'{"kind":"search_started","kind":"search_ended"}\n',
        json.dumps(messages()[0]).encode() + b"\n",
    ],
)
def test_noncanonical_or_invalid_wire(wire):
    reader = control.ControlReader(90.0)
    with pytest.raises(ValueError):
        reader.feed(wire, 220.0)


@pytest.mark.parametrize("terminated", [False, True])
def test_oversized_frame_rejected_before_json_parser(monkeypatch, terminated):
    def forbidden(*args, **kwargs):
        pytest.fail("oversized bytes reached JSON parser")

    monkeypatch.setattr(control.json, "loads", forbidden)
    reader = control.ControlReader(0.0)
    with pytest.raises(ValueError, match="limit"):
        reader.feed(b"x" * control.MAX_FRAME_BYTES + (b"\n" if terminated else b""), 1.0)


def test_chunk_bound_before_concatenation_and_no_resume_after_finish():
    reader = control.ControlReader(90.0)
    with pytest.raises(ValueError, match="bounded"):
        reader.feed(b"x" * (control.MAX_FRAME_BYTES * 3 + 1), 100.0)
    reader = control.ControlReader(90.0)
    reader.feed(b"".join(_encode(v) for v in messages()), 220.0)
    reader.finish()
    with pytest.raises(ValueError, match="finished"):
        reader.feed(b"", 220.0)


def test_atomic_pipe_publication_and_no_file_read():
    read_fd, write_fd = os.pipe()
    try:
        control.send_control(write_fd, messages()[0])
        assert os.read(read_fd, 4096) == _encode(messages()[0])
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_atomic_limit_checked_before_write(monkeypatch):
    monkeypatch.setattr(control.os, "fstat", lambda fd: type("Stat", (), {"st_mode": 0o010000})())
    monkeypatch.setattr(control.os, "fpathconf", lambda *args: 2)
    monkeypatch.setattr(control.os, "write", lambda *args: pytest.fail("non-atomic write"))
    with pytest.raises(ValueError, match="atomic"):
        control.send_control(3, messages()[0])


def test_partial_write_does_not_retry(monkeypatch):
    monkeypatch.setattr(control.os, "fstat", lambda fd: type("Stat", (), {"st_mode": 0o010000})())
    calls = []
    monkeypatch.setattr(control.os, "fpathconf", lambda *args: 4096)
    monkeypatch.setattr(control.os, "write", lambda *args: calls.append(args) or 1)
    with pytest.raises(ValueError, match="short"):
        control.send_control(3, messages()[0])
    assert len(calls) == 1


def test_regular_file_is_not_an_atomic_control_pipe():
    with tempfile.TemporaryFile() as stream:
        with pytest.raises(ValueError, match="pipe"):
            control.send_control(stream.fileno(), messages()[0])
        assert stream.tell() == 0


class GuardHarness:
    def __init__(self):
        self.now = 100.0
        self.parent = 1234
        self.sent = []
        self.resources = 0
        self.control = control.WorkerControl(
            90.0,
            self.parent,
            self.sent.append,
            self.resource,
            clock=lambda: self.now,
            parent=lambda: self.parent,
        )

    def resource(self):
        self.resources += 1


def test_worker_phase_guard_full_sequence_and_parent_death():
    h = GuardHarness()
    h.control.check()
    h.control.signal("search_started")
    h.now = 200.0
    h.control.signal("search_ended")
    h.now = 210.0
    h.control.signal("returned_result", reference())
    assert h.sent == messages()
    h.parent = 1
    with pytest.raises(ValueError, match="parent identity"):
        h.control.check()
    with pytest.raises(RuntimeError):
        h.control.signal("returned_result", reference())


@pytest.mark.parametrize("callback", ["_resource", "_send", "_clock", "_parent"])
def test_callback_failure_and_swallowed_reentry_poison_guard(callback):
    h = GuardHarness()
    original = getattr(h.control, callback)

    def bad(*args):
        try:
            h.control.check()
        except ValueError:
            pass
        return original(*args)

    setattr(h.control, callback, bad)
    with pytest.raises(RuntimeError, match="failed"):
        h.control.signal("search_started")
    with pytest.raises(RuntimeError):
        h.control.check()


def test_resource_clock_cost_is_counted():
    h = GuardHarness()
    h.control._resource = lambda: setattr(h, "now", 1900.0)
    with pytest.raises(TimeoutError, match="1800"):
        h.control.check()


def test_transparent_journal_payloads_and_exact_search_boundaries(tmp_path):
    h = GuardHarness()
    native = EventJournal(tmp_path / "native")
    controller = EventJournal(tmp_path / "controller")
    n = control.PhaseJournal(native, h.control, "native")
    c = control.PhaseJournal(controller, h.control, "controller")
    initial = dict(
        event="operation-attempted", kind="initialization", phase="main", model_id="main"
    )
    replay = dict(initial, phase="replay", model_id="replay")
    started, complete = dict(event="search_started"), dict(event="search_complete")
    n(initial)
    assert not h.sent
    c(started)
    assert [v["kind"] for v in h.sent] == ["search_started"]
    h.now = 150.0
    c(complete)
    assert h.control.reader.search_ended is None
    h.now = 200.0
    n(replay)
    assert h.control.reader.search_ended == 200.0
    assert read_events(native._directory, n.receipt) == [initial, replay]
    assert read_events(controller._directory, c.receipt) == [started, complete]


def test_search_start_sent_before_journal_publication_failure(tmp_path):
    h = GuardHarness()

    class Broken(EventJournal):
        def __call__(self, value):
            assert h.sent[0]["kind"] == "search_started"
            raise OSError("injected publication failure")

    journal = control.PhaseJournal(Broken(tmp_path / "events"), h.control, "controller")
    with pytest.raises(OSError):
        journal(dict(event="search_started"))
    assert journal._failed
    with pytest.raises(ValueError):
        journal(dict(event="search_complete"))


def test_swallowed_underlying_journal_poison_is_not_acknowledged(tmp_path):
    h = GuardHarness()

    class Swallow(EventJournal):
        def __call__(self, value):
            result = super().__call__(copy.deepcopy(value))
            try:
                super().__call__({"nonfinite": float("nan")})
            except ValueError:
                pass
            return result

    journal = control.PhaseJournal(Swallow(tmp_path / "events"), h.control, "controller")
    with pytest.raises(ValueError, match="poisoned"):
        journal(dict(event="search_started"))
    assert journal._failed
