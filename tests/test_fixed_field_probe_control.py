"""No native physics: exact dispatch, resource bounds and explicit process returns."""

import copy
import os
import sys
import time
from types import SimpleNamespace

import pytest

from fusion_baselines import fixed_field_probe_control as control
from fusion_baselines.protected_search_journal import _encode


def events(level):
    result = []
    for i, (field, quantity, points) in enumerate(control.requests(level)):
        event = dict(
            index=i,
            field=field,
            quantity=quantity,
            points=points,
            status="attempted",
            started_monotonic=float(i),
            native_started=False,
            native_completed=False,
        )
        result.append(event)
        result.append(
            dict(
                event,
                status="completed",
                native_started=True,
                native_completed=True,
                completed_monotonic=float(i) + 0.5,
            )
        )
    return result


def test_schedule():
    assert len(control.LEVELS) == 6
    counts = [sum(r[2] for r in control.requests(level)) for level in control.LEVELS]
    assert counts == [15104, 39680, 39680, 39680, 33536, 33536]
    assert sum(counts) * 4 == 804864
    assert 4 * 6 * 7 == 168


@pytest.mark.parametrize("level", control.LEVELS)
def test_exact_work(level):
    saved = []
    work = control.Work(level, saved.append, lambda: None)
    sequence = events(level)
    for event in sequence:
        work(event)
    assert saved == sequence
    assert work.finish(sequence[1::2]) == dict(
        requests=7, points=sum(p for _, _, p in control.requests(level))
    )


@pytest.mark.parametrize("at", range(14))
@pytest.mark.parametrize("fault", ("index", "quantity", "points", "status", "native_started"))
def test_bad_events_poison(at, fault):
    sequence = events(control.LEVELS[0])
    event = sequence[at]
    event[fault] = dict(
        index=True,
        quantity="B_vjp",
        points=True,
        status="lost",
        native_started=not event["native_started"],
    )[fault]
    work = control.Work(control.LEVELS[0], lambda e: None, lambda: None)
    with pytest.raises(ValueError):
        for event in sequence:
            work(event)
    assert work.failed
    with pytest.raises(ValueError, match="poisoned"):
        work(events(control.LEVELS[0])[0])


@pytest.mark.parametrize("at", range(14))
def test_persistence_failures_poison(at):
    saved = []

    def persist(event):
        if len(saved) == at:
            raise OSError("synthetic fsync")
        saved.append(event)

    work = control.Work(control.LEVELS[0], persist, lambda: None)
    with pytest.raises(OSError):
        for event in events(control.LEVELS[0]):
            work(event)
    assert work.failed and len(saved) == at


@pytest.mark.parametrize("count", range(14))
def test_missing_calls_cannot_finish(count):
    work = control.Work(control.LEVELS[0], lambda e: None, lambda: None)
    sequence = events(control.LEVELS[0])
    for event in sequence[:count]:
        work(event)
    with pytest.raises(ValueError):
        work.finish(sequence[1::2])


def test_extra_and_mutated_return():
    work = control.Work(control.LEVELS[0], lambda e: None, lambda: None)
    sequence = events(control.LEVELS[0])
    for event in sequence:
        work(event)
    returned = copy.deepcopy(sequence[1::2])
    returned[0]["points"] += 1
    with pytest.raises(ValueError):
        work.finish(returned)
    with pytest.raises(ValueError):
        work(sequence[-2])


@pytest.mark.parametrize("now", (99, 700, 701, float("nan"), float("inf")))
def test_guard_time(now):
    guard = control.Guard(
        "unused", 100, clock=lambda: now, space=lambda _: SimpleNamespace(free=control.LIVE_FREE)
    )
    with pytest.raises((ValueError, TimeoutError)):
        guard()
    assert guard.failed


def test_guard_disk_and_monotonic_poison():
    guard = control.Guard(
        "unused", 0, clock=lambda: 1, space=lambda _: SimpleNamespace(free=control.LIVE_FREE - 1)
    )
    with pytest.raises(ValueError, match="reserve"):
        guard()
    guard.space = lambda _: SimpleNamespace(free=10 * control.LIVE_FREE)
    with pytest.raises(ValueError, match="poisoned"):
        guard()


def test_budget():
    account = control.PayloadBudget(
        control.PAIR_BYTES - control.MODEL_RESERVE - control.TERMINAL_RESERVE
    )
    account.reserve_model()
    account.charge(1)
    with pytest.raises(ValueError, match="reserve"):
        account.reserve_model()
    account = control.PayloadBudget(control.PAIR_BYTES - control.TERMINAL_RESERVE)
    account.charge(control.TERMINAL_RESERVE, terminal=True)
    with pytest.raises(ValueError, match="cap"):
        account.charge(1, terminal=True)
    assert account.failed


def test_failed_nonterminal_cap_preserves_terminal_allowance():
    account = control.PayloadBudget(control.PAIR_BYTES - control.TERMINAL_RESERVE)
    with pytest.raises(ValueError):
        account.charge(1)
    account.charge(100, terminal=True)
    with pytest.raises(ValueError):
        account.charge(1)


def test_backward_cross_call_clock():
    work = control.Work(control.LEVELS[0], lambda e: None, lambda: None)
    sequence = events(control.LEVELS[0])
    work(sequence[0])
    work(sequence[1])
    sequence[2]["started_monotonic"] = 0.0
    with pytest.raises(ValueError, match="cross-call"):
        work(sequence[2])


def frame(i=0, kind="returned", payload=None):
    return _encode(dict(sequence=i, kind=kind, payload={} if payload is None else payload))


def test_frame_chunks():
    reader = control.Frames()
    raw = frame(kind="progress") + frame(i=1)
    for byte in raw:
        reader.feed(bytes([byte]))
    assert reader.finish()["sequence"] == 1
    with pytest.raises(ValueError):
        reader.feed(frame(i=2))


@pytest.mark.parametrize(
    "raw",
    (
        frame(i=1),
        frame(i=True),
        frame(kind="surprise"),
        b'{"sequence":0,"sequence":0}\n',
        b"x" * 4096,
    ),
)
def test_bad_frames(raw):
    with pytest.raises(ValueError):
        control.Frames().feed(raw)


def test_missing_return():
    reader = control.Frames()
    reader.feed(frame(kind="progress"))
    with pytest.raises(ValueError):
        reader.finish()


@pytest.mark.skipif(os.name != "posix", reason="registered POSIX process groups")
@pytest.mark.parametrize("mode", ("good", "missing", "failed", "nonzero", "extra", "biglog"))
def test_real_process_ack(tmp_path, mode):
    data = frame(kind="failed" if mode == "failed" else "returned")
    if mode == "missing":
        data = b""
    elif mode == "extra":
        data += frame(i=1)
    code = "import os,sys;os.write(int(sys.argv[1])," + repr(data) + ");"
    if mode == "biglog":
        code += "os.write(1,b'x'*200000);"
    code += "sys.exit(" + ("1" if mode == "nonzero" else "0") + ")"
    result = control.supervise(
        lambda fd: [sys.executable, "-c", code, str(fd)], tmp_path / "phase", time.monotonic()
    )
    assert result["complete"] is (mode == "good")
    assert result["physical_admission"] is False


def test_real_process_late_return(tmp_path):
    code = "import os,sys;os.write(int(sys.argv[1])," + repr(frame()) + ")"
    result = control.supervise(
        lambda fd: [sys.executable, "-c", code, str(fd)], tmp_path / "phase", time.monotonic() - 601
    )
    assert result["complete"] is False


def test_bridge_work_integration(monkeypatch):
    from test_fixed_field_probe_native import setup

    from fusion_baselines import fixed_field_probe_native as native

    for name in control.THREADS:
        monkeypatch.setenv(name, "1")
    args, _, _ = setup(monkeypatch)
    snapshot = None
    total = 0
    for level in control.LEVELS:
        work = control.Work(level, lambda e: None, lambda: None)
        args.update(level=level, frozen_snapshot=snapshot, callback=work)
        result = native.evaluate_model(**args)
        snapshot = result["snapshot"]
        total += work.finish(result["native_calls"])["points"]
    assert total == 201216
