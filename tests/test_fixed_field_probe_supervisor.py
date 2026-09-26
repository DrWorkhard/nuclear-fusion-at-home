"""Tiny synthetic POSIX processes only; no scientific or native model work."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from fusion_baselines import fixed_field_probe_control as control

pytestmark = pytest.mark.skipif(os.name != "posix", reason="registered POSIX supervisor")


def command(code, payload=None):
    if payload is None:
        payload = dict(sequence=0, kind="returned", payload=dict(reference="synthetic"))
    raw = control._encode(payload)

    def build(fd):
        return [sys.executable, "-c", f"import os,time,signal,sys\nfd={fd}\nraw={raw!r}\n" + code]

    return build


def run(tmp_path, code="os.write(fd,raw);os.close(fd)", *, payload=None, clock=time.monotonic):
    return control.supervise(
        command(code, payload), tmp_path / "owned", time.monotonic(), clock=clock
    )


def test_complete_explicit_return_and_single_thread_environment(tmp_path):
    code = "\n".join(f"assert os.environ[{key!r}]=='1'" for key in control.THREADS)
    result = run(tmp_path, code + "\nos.write(fd,raw);os.close(fd);print('ok')")
    assert result["complete"] and result["exit_code"] == 0
    assert result["frames"][0]["kind"] == "returned"
    assert result["group_cleanup"]["reaped"] and result["group_cleanup"]["retired"]
    assert (tmp_path / "owned/stdout.log").read_text() == "ok\n"
    assert result["log_bytes"] == dict(stdout=3, stderr=0)


def test_no_poll_or_reap_until_final_group_signal(tmp_path, monkeypatch):
    original = control.subprocess.Popen
    events = []

    class Process(original):
        def poll(self):
            raise AssertionError("poll would reap before group cleanup")

        def wait(self, *args, **kwargs):
            events.append(("wait", self.returncode, kwargs["timeout"]))
            return super().wait(*args, **kwargs)

    kill = control.os.killpg

    def signal_group(pid, sig):
        events.append(("signal", pid, sig))
        return kill(pid, sig)

    monkeypatch.setattr(control.subprocess, "Popen", Process)
    monkeypatch.setattr(control.os, "killpg", signal_group)
    result = run(tmp_path)
    assert result["complete"]
    waited = next(i for i, e in enumerate(events) if e[0] == "wait")
    assert any(e[0] == "signal" and e[2] == signal.SIGKILL for e in events[:waited])
    assert all(e[2] == 0 for e in events[waited + 1 :] if e[0] == "signal")
    assert events[waited][1] is None and 0 <= events[waited][2] <= 1


@pytest.mark.parametrize(
    "code,payload,reason",
    [
        ("os.close(fd)", None, "explicit control"),
        ("os.write(fd,raw[:-1]);os.close(fd)", None, "explicit control"),
        ("os.write(fd,raw);os.close(fd);sys.exit(7)", None, "nonzero child"),
        (
            "os.write(fd,raw);os.close(fd)",
            dict(sequence=0, kind="failed", payload={}),
            "successful return",
        ),
        ("os.write(fd,raw+raw);os.close(fd)", None, "sole return"),
        ("os.write(fd,b'[]\\n');os.close(fd)", None, "ordered control"),
    ],
)
def test_terminal_negative_controls(tmp_path, code, payload, reason):
    result = run(tmp_path, code, payload=payload)
    assert not result["complete"] and reason in result["error"]
    assert result["group_cleanup"]["retired"]


def test_hard_timeout_kills_owned_group_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(control, "PHASE_SECONDS", 0.15)
    monkeypatch.setattr(control, "GRACE_SECONDS", 0.10)
    before = time.monotonic()
    result = run(tmp_path, "time.sleep(10)")
    assert not result["complete"] and "hard termination" in result["error"]
    assert result["exit_code"] == -signal.SIGKILL
    assert result["group_cleanup"]["retired"]
    assert time.monotonic() - before < 1.5


def test_return_inside_grace_is_negative(tmp_path, monkeypatch):
    monkeypatch.setattr(control, "PHASE_SECONDS", 0.10)
    monkeypatch.setattr(control, "GRACE_SECONDS", 0.30)
    result = run(tmp_path, "time.sleep(.15);os.write(fd,raw);os.close(fd)")
    assert not result["complete"] and "on-time" in result["error"]
    assert result["exit_code"] == 0


def test_descendant_holds_pipes_after_leader_exit_is_killed(tmp_path, monkeypatch):
    monkeypatch.setattr(control, "PHASE_SECONDS", 0.2)
    monkeypatch.setattr(control, "GRACE_SECONDS", 0.1)
    code = """child=os.fork()
if child==0:
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 time.sleep(30)
 os._exit(0)
print(child,flush=True)
os.write(fd,raw)
os._exit(0)
"""
    result = run(tmp_path, code)
    assert not result["complete"]
    assert result["group_cleanup"]["signalled_before_reap"]
    child = int((tmp_path / "owned/stdout.log").read_text())
    # On Linux an init process may retain a killed orphan as a zombie briefly;
    # the supervisor then reports unconfirmed group retirement rather than pass.
    try:
        os.kill(child, 0)
    except ProcessLookupError:
        pass
    else:
        stat = Path(f"/proc/{child}/stat")
        assert stat.exists() and ") Z " in stat.read_text()


def test_closed_pipe_descendant_is_also_killed_before_leader_reap(tmp_path):
    code = """child=os.fork()
if child==0:
 os.close(fd);os.close(1);os.close(2)
 time.sleep(30)
 os._exit(0)
print(child,flush=True)
os.write(fd,raw)
os._exit(0)
"""
    result = run(tmp_path, code)
    assert result["group_cleanup"]["signalled_before_reap"]
    child = int((tmp_path / "owned/stdout.log").read_text())
    try:
        os.kill(child, 0)
    except ProcessLookupError:
        pass
    else:
        stat = Path(f"/proc/{child}/stat")
        assert not result["complete"] and stat.exists() and ") Z " in stat.read_text()


def test_live_disk_reserve_checked_while_native_equivalent_wedges(tmp_path, monkeypatch):
    calls = 0

    def space(path):
        nonlocal calls
        calls += 1
        return SimpleNamespace(free=control.LIVE_FREE if calls < 3 else control.LIVE_FREE - 1)

    monkeypatch.setattr(control.shutil, "disk_usage", space)
    result = run(tmp_path, "time.sleep(30)")
    assert not result["complete"] and "parent live disk reserve" in result["error"]
    assert result["exit_code"] == -signal.SIGKILL
    assert calls == 3


def test_no_launch_without_initial_live_reserve(tmp_path, monkeypatch):
    monkeypatch.setattr(control.shutil, "disk_usage", lambda p: SimpleNamespace(free=0))
    monkeypatch.setattr(
        control.subprocess, "Popen", lambda *a, **k: pytest.fail("unexpected launch")
    )
    result = run(tmp_path)
    assert not result["complete"] and result["exit_code"] is None


@pytest.mark.parametrize("channel", ["stdout", "stderr", "control"])
def test_bounded_streams(tmp_path, monkeypatch, channel):
    monkeypatch.setattr(control, "MAX_LOG_BYTES", 40)
    code = {
        "stdout": "os.write(1,b'x'*100)",
        "stderr": "os.write(2,b'x'*100)",
        "control": "os.write(fd,b'x'*4096)",
    }[channel]
    result = run(tmp_path, code + ";time.sleep(.1)")
    assert not result["complete"] and "bounded" in result["error"]


def test_launch_failure_retained(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("launch failed")

    monkeypatch.setattr(control.subprocess, "Popen", fail)
    result = run(tmp_path)
    assert not result["complete"] and "launch failed" in result["error"]


def test_invalid_parent_clock_after_exit_never_signals_reaped_group(tmp_path, monkeypatch):
    original = control.subprocess.Popen
    reaped = False
    signals = []

    class Process(original):
        def wait(self, *args, **kwargs):
            nonlocal reaped
            result = super().wait(*args, **kwargs)
            reaped = True
            return result

    kill = control.os.killpg

    def signal_group(pid, sig):
        signals.append((sig, reaped))
        return kill(pid, sig)

    monkeypatch.setattr(control.subprocess, "Popen", Process)
    monkeypatch.setattr(control.os, "killpg", signal_group)
    result = run(tmp_path, clock=lambda: float("nan") if reaped else time.monotonic())
    assert not result["complete"] and result["finished_monotonic"] is None
    assert all(sig == 0 or not was_reaped for sig, was_reaped in signals)


def test_bounded_reap_timeout_is_recorded(tmp_path, monkeypatch):
    original = control.subprocess.Popen
    instances = []

    class Process(original):
        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired("synthetic reap", timeout)

    def launch(*a, **k):
        result = Process(*a, **k)
        instances.append(result)
        return result

    monkeypatch.setattr(control.subprocess, "Popen", launch)
    result = run(tmp_path)
    assert not result["complete"] and "bounded child reap failed" in result["error"]
    # Test-only reap through the original implementation, after all owned signals.
    original.wait(instances[0], timeout=1)


def test_disallow_auto_reaping_sigchld(tmp_path, monkeypatch):
    actual = control.signal.getsignal
    monkeypatch.setattr(
        control.signal,
        "getsignal",
        lambda sig: signal.SIG_IGN if sig == signal.SIGCHLD else actual(sig),
    )
    with pytest.raises(ValueError, match="SIGCHLD"):
        run(tmp_path)
