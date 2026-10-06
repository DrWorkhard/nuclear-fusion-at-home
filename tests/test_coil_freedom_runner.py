"""No native work: enforce the comparison's shared clock and failure rules."""

import importlib.util
import json
import os
import signal
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "coil_freedom_runner", Path(__file__).resolve().parents[1]/"scripts/run_coil_freedom.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.fixture(autouse=True)
def enough_disk(monkeypatch):
    monkeypatch.setattr(runner.shutil, "disk_usage", lambda _: SimpleNamespace(free=8*1024**3))


def test_diagnostic_deadline_never_restarts_or_exceeds_outer_limit(tmp_path):
    marker = tmp_path/"clock.json"
    assert runner.diagnostic_deadline(marker, 2700) == 2700
    runner.save(marker, dict(deadline_monotonic=905))  # Early solver return at 5 s.
    assert runner.diagnostic_deadline(marker, 2700) == 905
    assert runner.diagnostic_deadline(marker, 900) == 900
    for value in (True, "905", float("inf"), float("nan")):
        marker.write_text(json.dumps(dict(deadline_monotonic=value)), encoding="utf-8")
        with pytest.raises(ValueError, match="deadline"):
            runner.diagnostic_deadline(marker, 2700)


@pytest.mark.skipif(os.name != "posix", reason="study supervisor uses POSIX process groups")
def test_actual_child_stops_at_shared_check_deadline_and_retains_partial_file(tmp_path):
    marker, partial = tmp_path/"clock.json", tmp_path/"partial.json"
    code = ("import json,pathlib,time; "
            f"pathlib.Path({str(marker)!r}).write_text(json.dumps("
            "{'deadline_monotonic':time.monotonic()+.2})); "
            f"pathlib.Path({str(partial)!r}).write_text('partial'); time.sleep(30)")
    result = runner.supervise([sys.executable, "-c", code], tmp_path, "test",
                              time.monotonic()+10, marker)
    assert result["stop_reason"] == "deadline" and not result["completed"]
    assert result["elapsed_s"] < 5
    assert partial.read_text(encoding="utf-8") == "partial"


@pytest.mark.skipif(os.name != "posix", reason="study supervisor uses POSIX process groups")
def test_zero_status_cannot_hide_aggregate_storage_overrun(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "MAX_BYTES", 100)
    monkeypatch.setattr(runner, "REPORT_RESERVE", 0)
    (tmp_path/"fit").mkdir()
    (tmp_path/"fit"/"prior").write_bytes(b"a"*60)
    code = f"from pathlib import Path; Path({str(tmp_path/'trace-data')!r}).write_bytes(b'b'*60)"
    result = runner.supervise([sys.executable, "-c", code], tmp_path, "trace",
                              time.monotonic()+10)
    assert not result["completed"] and result["stop_reason"] == "aggregate storage ceiling"
    assert (tmp_path/"fit"/"prior").read_bytes() == b"a"*60
    assert (tmp_path/"trace-data").read_bytes() == b"b"*60


@pytest.mark.skipif(os.name != "posix", reason="study supervisor uses POSIX process groups")
def test_descendant_cannot_write_after_its_leader_exits(tmp_path):
    ready, late = tmp_path/"ready", tmp_path/"late"
    child = ("import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); "
             f"pathlib.Path({str(ready)!r}).touch(); time.sleep(.6); "
             f"pathlib.Path({str(late)!r}).touch()")
    leader = ("import subprocess,sys,time,pathlib; "
              f"subprocess.Popen([sys.executable,'-c',{child!r}]);"
              f"\nwhile not pathlib.Path({str(ready)!r}).exists(): time.sleep(.01)")
    result = runner.supervise([sys.executable, "-c", leader], tmp_path, "leader",
                              time.monotonic()+5)
    assert result["completed"]
    time.sleep(.7)
    assert ready.exists() and not late.exists()


def test_cleanup_failure_is_not_assumed_safe_when_leader_has_exited(monkeypatch):
    process = SimpleNamespace(pid=123, returncode=0, poll=lambda: 0)

    def denied(*args):
        raise PermissionError("process group may still exist")

    monkeypatch.setattr(runner.os, "killpg", denied)
    with pytest.raises(runner.CleanupError):
        runner.stop(process)


def test_cleanup_signals_the_group_after_leader_exit(monkeypatch):
    signals = []
    process = SimpleNamespace(pid=123, returncode=0, poll=lambda: 0, wait=lambda **kw: 0)
    monkeypatch.setattr(runner.os, "killpg", lambda pid, sig: signals.append((pid, sig)))
    runner.stop(process)
    assert signals == [(123, signal.SIGTERM), (123, signal.SIGKILL)]


@pytest.mark.parametrize("cleanup_failed,expected_orders", [(True, [5]), (False, [5, 8])])
def test_unknown_survivor_aborts_study_but_ordinary_failure_retains_both_arms(
        tmp_path, monkeypatch, cleanup_failed, expected_orders):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "build_run_record", lambda _: dict(
        repository=dict(dirty=False, commit="a"*40)))
    protocol = tmp_path/"docs/optimization/ISSUE53_COIL_FREEDOM.md"
    protocol.parent.mkdir(parents=True)
    protocol.write_text("frozen", encoding="utf-8")
    seed, wout = tmp_path/"seed", tmp_path/"wout"
    seed.write_bytes(b"seed")
    wout.write_bytes(b"wout")
    monkeypatch.setattr(runner, "SNAPSHOT_SHA", runner.digest(seed))
    monkeypatch.setattr(runner, "WOUT_SHA", runner.digest(wout))
    orders = []

    def failed_arm(order, *args):
        orders.append(order)
        return dict(completed=False, cleanup_failed=cleanup_failed)

    monkeypatch.setattr(runner, "run_arm", failed_arm)
    assert runner.run(seed, wout, tmp_path/"output", "a"*40) == 1
    assert orders == expected_orders
    assert not runner.read(tmp_path/"output"/"study.json")["completed"]


def test_no_child_starts_after_deadline_or_below_reserve(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.subprocess, "Popen", lambda *a, **kw: pytest.fail("child started"))
    result = runner.supervise([], tmp_path, "late", time.monotonic()-1)
    assert result["stop_reason"] == "deadline"
    monkeypatch.setattr(runner.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    result = runner.supervise([], tmp_path, "full", time.monotonic()+1)
    assert result["stop_reason"] == "live disk reserve"


@pytest.mark.parametrize("fit_completed,marker_present", [(False, True), (True, False)])
def test_incomplete_fit_or_missing_clock_never_starts_trace(
        tmp_path, monkeypatch, fit_completed, marker_present):
    calls = []

    def fake(command, arm, label, deadline, marker=None):
        calls.append(label)
        assert label == "fit"
        (arm/"fit").mkdir()
        runner.save(arm/"fit"/"result.json", dict(completed=fit_completed))
        if marker_present:
            runner.save(marker, dict(deadline_monotonic=deadline))
        return dict(completed=True)

    monkeypatch.setattr(runner, "supervise", fake)
    result = runner.run_arm(5, tmp_path/"seed", tmp_path/"wout", tmp_path/"C")
    assert calls == ["fit"] and not result["completed"]


def test_trace_uses_existing_clock_and_watchdog_overrides_raw_success(tmp_path, monkeypatch):
    calls = []
    shared_deadline = time.monotonic()+50

    def fake(command, arm, label, deadline, marker=None):
        calls.append(label)
        (arm/label).mkdir()
        runner.save(arm/label/"result.json", dict(completed=True))
        if label == "fit":
            runner.save(marker, dict(deadline_monotonic=shared_deadline))
            return dict(completed=True)
        assert deadline == shared_deadline
        return dict(completed=False, stop_reason="deadline")

    monkeypatch.setattr(runner, "supervise", fake)
    result = runner.run_arm(8, tmp_path/"seed", tmp_path/"wout", tmp_path/"P")
    assert calls == ["fit", "trace"] and not result["completed"]
    assert runner.read(tmp_path/"P"/"trace"/"result.json")["completed"]


def test_refuses_wrong_revision_dirty_checkout_and_substituted_inputs(tmp_path, monkeypatch):
    state = dict(dirty=False, commit="a"*40)
    monkeypatch.setattr(runner, "build_run_record", lambda _: dict(repository=state))
    seed, wout = tmp_path/"seed", tmp_path/"wout"
    seed.write_bytes(b"wrong")
    wout.write_bytes(b"wrong")
    for revision, dirty, message in (("b"*40, False, "reviewed"),
                                     ("a"*40, True, "reviewed"),
                                     ("a"*40, False, "original")):
        state["dirty"] = dirty
        with pytest.raises(ValueError, match=message):
            runner.run(seed, wout, tmp_path/"out", revision)
        assert not (tmp_path/"out").exists()
