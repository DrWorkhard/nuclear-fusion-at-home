"""Tiny synthetic POSIX workers only; no native adapter or scientific search."""

import copy
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from fusion_baselines import protected_process as supervisor
from fusion_baselines import protected_worker_control as control
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json

CASE = dict(
    label="reference-n6-N",
    target="reference",
    nbase=6,
    order=5,
    seed_label="n6-shape-d100mm",
    method="N",
)
THREAD_NAMES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)

# This worker intentionally uses only stdlib and does not import the producer,
# reference checker, native field code, supervisor or control implementation.
WORKER = r"""
import hashlib, json, os, signal, subprocess, sys, time
from pathlib import Path
config_ref = json.loads(sys.argv[1])
config = json.loads(Path(config_ref['path']).read_text(encoding='utf-8'))
fd, mode = int(sys.argv[2]), sys.argv[3]
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
            'VECLIB_MAXIMUM_THREADS'):
    assert os.environ[key] == '1'
output = Path(config['output'])
output.mkdir()
def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
def persist(name, value):
    path = output / name
    raw = encode(value)
    with path.open('xb') as f:
        f.write(raw)
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
def message(kind, stamp=None, reference=None):
    value = dict(schema_version=1, kind=kind,
                 monotonic=time.monotonic() if stamp is None else stamp)
    if reference is not None:
        value['reference'] = reference
    return encode(value)
if mode == 'malformed':
    os.write(fd, b'{bad}\n'); sys.exit(0)
if mode == 'oversized':
    os.write(fd, b'x'*4096); sys.exit(0)
if mode == 'out-of-order':
    os.write(fd, message('search_ended')); sys.exit(0)
if mode == 'future':
    os.write(fd, message('search_started', time.monotonic()+100)); sys.exit(0)
if mode == 'before-launch':
    os.write(fd, message('search_started', config['started_monotonic'])); sys.exit(0)
if mode == 'before-search-hang':
    while True: time.sleep(10)
search_start = time.monotonic()
os.write(fd, message('search_started', search_start))
if mode == 'duplicate':
    os.write(fd, message('search_started')); sys.exit(0)
if mode == 'hung-search':
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    while True: time.sleep(10)
os.write(fd, message('search_ended'))
core = dict(schema_version=1, kind='protected-cell-execution', case=config['case'],
            producer_complete=True, independent_audit_pass=False,
            physical_admission=False, step4_pass=False)
if mode.startswith('core:'):
    _, key, raw = mode.split(':', 2); core[key] = json.loads(raw)
core_ref = persist('core.json', core)
source = json.loads(Path(config['source']['path']).read_text(encoding='utf-8'))
before = persist('source-before.json', source)
if mode == 'source-drift': source['revision'] = 'changed'
after = persist('source-after.json', source)
envelope = dict(schema_version=1, kind='protected-cell-worker-return', case=config['case'],
    config=config_ref, cell_result=core_ref, source_before=before, source_after=after,
    threads=config['threads'], parent_pid=config['parent_pid'], worker_pid=os.getpid(),
    started_monotonic=config['started_monotonic'], returned_monotonic=time.monotonic(),
    physical_admission=False, step4_pass=False)
if mode.startswith('envelope:'):
    _, key, raw = mode.split(':', 2); envelope[key] = json.loads(raw)
if mode == 'extra-envelope-key': envelope['extra'] = False
if mode == 'future-envelope': envelope['returned_monotonic'] += 100
if mode == 'pre-replay-envelope': envelope['returned_monotonic'] = search_start
if mode == 'core-outside': envelope['cell_result'] = config['source']
returned = persist('returned.json', envelope)
if mode == 'missing-return': sys.exit(0)
raw = message('returned_result', reference=returned)
if mode == 'truncated': raw = raw[:-1]
os.write(fd, raw)
if mode == 'bad-return-bytes':
    with Path(returned['path']).open('ab') as f: f.write(b' ')
if mode == 'extra-message': os.write(fd, message('search_started'))
if mode == 'descendant':
    ready_read, ready_write = os.pipe()
    child = subprocess.Popen([sys.executable, '-c',
        'import os,signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); '
        'os.write(int(__import__("sys").argv[1]),b"ready"); time.sleep(10)', str(ready_write)],
        pass_fds=(fd, ready_write))
    os.close(ready_write)
    assert os.read(ready_read, 5) == b'ready'
    os.close(ready_read)
    (output / 'descendant.pid').write_text(str(child.pid), encoding='utf-8')
if mode == 'nonzero': sys.exit(7)
"""


@pytest.fixture
def setup(tmp_path, monkeypatch):
    source = SnapshotStore(tmp_path / "sources").json(
        "manifest", dict(kind="synthetic-source", revision="unchanged")
    )
    output = tmp_path / "cell"
    checks = []

    def config_builder(started, parent_pid, threads):
        return dict(
            schema_version=1,
            kind="protected-cell-worker-config",
            case=copy.deepcopy(CASE),
            source=copy.deepcopy(source),
            output=str(output / "worker"),
            parent_pid=parent_pid,
            started_monotonic=started,
            threads=threads,
        )

    def command_builder(reference, fd, mode="normal"):
        return [sys.executable, "-c", WORKER, json.dumps(reference), str(fd), mode]

    def disk(path, reserve):
        checks.append((Path(path), reserve))
        return dict(path=str(path), free_bytes=5 * 1024**3, required_bytes=reserve, sufficient=True)

    monkeypatch.setattr(supervisor, "space_check", disk)
    monkeypatch.setattr(supervisor, "POLL_SECONDS", 0.005)
    monkeypatch.setattr(supervisor, "TERM_GRACE_SECONDS", 0.05)
    config = SimpleNamespace(
        source=source,
        output=output,
        config_builder=config_builder,
        command_builder=command_builder,
        disk_checks=checks,
    )

    def run(
        mode="normal", *, config_fn=None, command_fn=None, source_check=None, validate_return=None
    ):
        return supervisor.supervise_cell(
            config_fn or config_builder,
            command_fn or (lambda ref, fd: command_builder(ref, fd, mode)),
            output,
            source_check=source_check or (lambda _: True),
            validate_return=validate_return or (lambda ref, config: True),
        )

    config.run = run
    return config


def no_ack(setup):
    assert not (setup.output / "parent" / "acknowledgement.json").exists()
    assert supervisor._RUNNING is False


def test_registered_limits_are_fixed_and_not_public_parameters():
    import inspect

    assert supervisor.START_RESERVE_BYTES == 3 * 1024**3
    assert supervisor.LIVE_RESERVE_BYTES == 2 * 1024**3
    assert supervisor.POLL_SECONDS == 0.5
    assert supervisor.TERM_GRACE_SECONDS == 5.0
    assert control.CELL_SECONDS == 1800
    assert control.SEARCH_SECONDS == 600
    assert control.MAX_FRAME_BYTES == 4096
    assert control.THREADS == dict.fromkeys(THREAD_NAMES, "1")
    assert list(inspect.signature(supervisor.supervise_cell).parameters) == [
        "config_builder",
        "command_builder",
        "output",
        "validate_return",
        "source_check",
    ]


def test_success_is_parent_bound_with_three_immutable_observations(setup, monkeypatch):
    for key in THREAD_NAMES:
        monkeypatch.setenv(key, "7")
    callback_configs = []

    def source_check(config):
        callback_configs.append(copy.deepcopy(config))
        config["case"]["label"] = "caller mutation cannot affect parent"
        return True

    result = read_json(setup.run(source_check=source_check))
    assert result["parent_acknowledged"] is True
    assert result["returncode"] == 0
    assert result["threads"] == dict.fromkeys(THREAD_NAMES, "1")
    assert result["worker_pid"] != os.getpid()
    assert result["owned_process_group"] == result["worker_pid"]
    assert result["physical_admission"] is result["step4_pass"] is False
    assert result["independent_physical_audit_pass"] is False
    assert result["case"] == CASE
    assert result["source"] == setup.source
    assert len(callback_configs) == 2
    assert callback_configs[0] == callback_configs[1] == read_json(result["config"])
    rows = [read_json(r) for r in result["control_observations"]]
    assert [r["message"]["kind"] for r in rows] == [
        "search_started",
        "search_ended",
        "returned_result",
    ]
    assert rows[-1]["message"]["reference"] == result["returned_result"]
    assert (
        result["started_monotonic"]
        <= result["spawned_monotonic"]
        <= rows[0]["message"]["monotonic"]
        <= result["exited_monotonic"]
        <= result["acknowledged_monotonic"]
    )
    assert all(r["message"]["monotonic"] <= r["observed_monotonic"] for r in rows)
    assert setup.disk_checks[0][1] == 3 * 1024**3
    assert all(r[1] == 2 * 1024**3 for r in setup.disk_checks[1:])
    assert result["minimum_observed_free_bytes"] == 5 * 1024**3
    assert supervisor._RUNNING is False


@pytest.mark.parametrize(
    "mode",
    [
        "malformed",
        "oversized",
        "out-of-order",
        "future",
        "before-launch",
        "duplicate",
        "truncated",
        "missing-return",
        "bad-return-bytes",
        "extra-message",
        "nonzero",
        "source-drift",
        "future-envelope",
        "extra-envelope-key",
        "core-outside",
    ],
)
def test_bad_subprocess_cannot_publish_acknowledgement(setup, mode):
    with pytest.raises((ValueError, TimeoutError, json.JSONDecodeError)):
        setup.run(mode)
    no_ack(setup)
    assert (setup.output / "parent" / "config.json").exists()


@pytest.mark.parametrize(
    ("scope", "key", "value"),
    [
        ("envelope", "schema_version", True),
        ("envelope", "kind", "other"),
        ("envelope", "parent_pid", True),
        ("envelope", "worker_pid", 1),
        ("envelope", "started_monotonic", 0),
        ("envelope", "threads", {}),
        ("envelope", "config", {}),
        ("envelope", "case", {}),
        ("envelope", "physical_admission", True),
        ("envelope", "step4_pass", 0),
        ("core", "schema_version", True),
        ("core", "kind", "other"),
        ("core", "case", {}),
        ("core", "producer_complete", 1),
        ("core", "independent_audit_pass", True),
        ("core", "physical_admission", True),
        ("core", "step4_pass", 0),
    ],
)
def test_typed_return_bindings(setup, scope, key, value):
    with pytest.raises(ValueError):
        setup.run(f"{scope}:{key}:{json.dumps(value)}")
    no_ack(setup)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("schema_version", True),
        ("kind", "other"),
        ("parent_pid", True),
        ("started_monotonic", 0),
        ("threads", {}),
        ("output", "/tmp/not-our-worker"),
        ("case", {}),
        ("source", {}),
        ("extra", 1),
    ],
)
def test_config_rejected_before_launch(setup, key, value):
    def config(*args):
        result = setup.config_builder(*args)
        result[key] = value
        return result

    with pytest.raises(ValueError):
        setup.run(config_fn=config)
    no_ack(setup)
    assert not (setup.output / "worker-stdout.log").exists()


@pytest.mark.parametrize("callback", ["source-before", "source-after", "return"])
@pytest.mark.parametrize("bad", [False, None, 1])
def test_exact_true_from_parent_callbacks_required(setup, callback, bad):
    calls = 0

    def source(config):
        nonlocal calls
        calls += 1
        return bad if callback == ("source-before" if calls == 1 else "source-after") else True

    with pytest.raises(ValueError):
        setup.run(
            source_check=source,
            validate_return=lambda ref, config: bad if callback == "return" else True,
        )
    no_ack(setup)


@pytest.mark.parametrize("callback", ["config", "command", "source", "return"])
def test_parent_callback_exceptions_preserved(setup, callback):
    def failure(*args):
        raise OSError("injected " + callback)

    kwargs = {
        dict(
            config="config_fn",
            command="command_fn",
            source="source_check",
            **{"return": "validate_return"},
        )[callback]: failure
    }
    with pytest.raises(OSError, match="injected " + callback):
        setup.run(**kwargs)
    no_ack(setup)


@pytest.mark.parametrize("stage", ["initial", "live", "after-launch"])
def test_disk_failure_preserves_prefix_and_never_acknowledges(setup, monkeypatch, stage):
    def disk(path, reserve):
        if (
            stage == "initial"
            or stage == "live"
            and reserve == 2 * 1024**3
            or stage == "after-launch"
            and (setup.output / "worker").exists()
        ):
            raise OSError("injected disk denial")
        return dict(free_bytes=5 * 1024**3, sufficient=True)

    monkeypatch.setattr(supervisor, "space_check", disk)
    with pytest.raises(OSError, match="disk denial"):
        setup.run()
    no_ack(setup)
    if stage == "initial":
        assert not setup.output.exists()


@pytest.mark.parametrize(
    "name", ["config", "control-0", "control-1", "control-2", "acknowledgement"]
)
def test_publication_failure_never_returns_ack(setup, monkeypatch, name):
    original = SnapshotStore.json

    def fail(self, stem, payload):
        if stem == name:
            self._failed = True
            raise OSError("injected publication " + name)
        return original(self, stem, payload)

    monkeypatch.setattr(SnapshotStore, "json", fail)
    with pytest.raises(OSError, match="publication " + name):
        setup.run()
    no_ack(setup)


def test_ack_file_after_failed_persistence_is_not_returned(setup, monkeypatch):
    original = SnapshotStore.json

    def fail_after(self, stem, payload):
        reference = original(self, stem, payload)
        if stem == "acknowledgement":
            self._failed = True
            raise OSError("injected post-write fsync failure")
        return reference

    monkeypatch.setattr(SnapshotStore, "json", fail_after)
    with pytest.raises(OSError, match="fsync"):
        setup.run()
    assert (setup.output / "parent" / "acknowledgement.json").exists()
    assert supervisor._RUNNING is False


def test_callback_cannot_change_previously_checked_result_bytes(setup):
    def change(ref, config):
        with Path(ref["path"]).open("ab") as stream:
            stream.write(b" ")
        return True

    with pytest.raises(ValueError, match="identity mismatch"):
        setup.run(validate_return=change)
    no_ack(setup)


def test_deadline_clock_starts_before_config_builder(setup, monkeypatch):
    now = [100.0]
    monkeypatch.setattr(supervisor.time, "monotonic", lambda: now[0])

    def config(started, parent_pid, threads):
        assert started == 100
        now[0] += 1800
        return setup.config_builder(started, parent_pid, threads)

    with pytest.raises(TimeoutError, match="1800"):
        setup.run(config_fn=config)
    no_ack(setup)
    assert not (setup.output / "worker-stdout.log").exists()


@pytest.mark.parametrize("mode", ["before-search-hang", "hung-search"])
def test_parent_terminates_wedged_worker_with_test_only_deadlines(setup, monkeypatch, mode):
    # Test injection only: there is no public argument changing these limits.
    monkeypatch.setattr(control, "CELL_SECONDS", 0.20)
    monkeypatch.setattr(control, "SEARCH_SECONDS", 0.05)
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        setup.run(mode)
    assert time.monotonic() - started < 2
    no_ack(setup)


def test_pipe_inheriting_descendant_rejected_and_killed(setup):
    with pytest.raises(ValueError):
        setup.run("descendant")
    no_ack(setup)
    pid = int((setup.output / "worker" / "descendant.pid").read_text(encoding="utf-8"))
    for _ in range(100):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.005)
    else:
        pytest.fail("owned descendant survived cleanup")


def test_fresh_output_and_serial_parent_are_required(setup):
    setup.output.mkdir()
    with pytest.raises(FileExistsError):
        setup.run()
    assert supervisor._RUNNING is False


def test_reentrant_parent_attempt_is_rejected(setup):
    def source(config):
        setup.run()
        return True

    with pytest.raises(ValueError, match="serially"):
        setup.run(source_check=source)
    no_ack(setup)


@pytest.mark.parametrize("hook", ["config", "source", "command", "return"])
def test_swallowed_reentrant_attempt_poisons_outer_parent(setup, hook):
    def swallow():
        with pytest.raises(ValueError, match="serially"):
            setup.run()

    def config(*args):
        if hook == "config":
            swallow()
        return setup.config_builder(*args)

    def source(config):
        if hook == "source":
            swallow()
        return True

    def command(ref, fd):
        if hook == "command":
            swallow()
        return setup.command_builder(ref, fd)

    def returned(ref, config):
        if hook == "return":
            swallow()
        return True

    with pytest.raises((ValueError, RuntimeError), match="poison|reentrant"):
        setup.run(
            config_fn=config, command_fn=command, source_check=source, validate_return=returned
        )
    no_ack(setup)


def test_return_clock_cannot_precede_search_completion(setup):
    with pytest.raises(ValueError, match="return clock"):
        setup.run("pre-replay-envelope")
    no_ack(setup)


def test_retired_process_group_is_never_signalled_on_late_failure(setup, monkeypatch):
    calls = []
    monkeypatch.setattr(supervisor, "_stop_group", lambda process: calls.append(process.pid))

    def reject(ref, config):
        raise ValueError("injected late result rejection")

    with pytest.raises(ValueError, match="late result"):
        setup.run(validate_return=reject)
    assert calls == [], "original group was already gone: PID reuse must not be signalled"
    no_ack(setup)


@pytest.mark.parametrize("name", ["config", "control-0", "acknowledgement"])
@pytest.mark.parametrize("fault", ["reentry", "poisoned-store"])
def test_swallowed_publication_failure_cannot_return_ack(setup, monkeypatch, name, fault):
    original = SnapshotStore.json

    def fail(self, stem, payload):
        result = original(self, stem, payload)
        if stem == name:
            if fault == "reentry":
                with pytest.raises(ValueError, match="serially"):
                    setup.run()
            else:
                self._failed = True
        return result

    monkeypatch.setattr(SnapshotStore, "json", fail)
    with pytest.raises((ValueError, RuntimeError), match="poison"):
        setup.run()
    if name == "acknowledgement":
        assert (setup.output / "parent" / "acknowledgement.json").exists()
        assert supervisor._RUNNING is False
    else:
        no_ack(setup)


@pytest.mark.parametrize("command", [[], "echo hi", [""], [True], ["a\0b"]])
def test_only_explicit_argument_vectors_allowed(setup, command):
    with pytest.raises(ValueError, match="argument-vector"):
        setup.run(command_fn=lambda ref, fd: command)
    no_ack(setup)


def fake_process(pid=1234567, *, wait_error=None):
    calls = []

    def wait(*, timeout):
        calls.append(timeout)
        if wait_error:
            raise wait_error
        return 0

    return SimpleNamespace(pid=pid, poll=lambda: 0, wait=wait, waits=calls)


def test_cleanup_kills_group_even_when_leader_has_already_exited(monkeypatch):
    process = fake_process()
    signals, present = [], [True]
    monkeypatch.setattr(supervisor.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(supervisor, "TERM_GRACE_SECONDS", 0)

    def killpg(pid, sig):
        assert pid == process.pid
        if not present[0]:
            raise ProcessLookupError
        if sig:
            signals.append(sig)
        if sig == signal.SIGKILL:
            present[0] = False

    monkeypatch.setattr(supervisor.os, "killpg", killpg)
    supervisor._stop_group(process)
    assert signals == [signal.SIGTERM, signal.SIGKILL]
    assert process.waits == [1.0]


def test_cleanup_retires_group_identity_after_observed_disappearance(monkeypatch):
    process = fake_process()
    monkeypatch.setattr(supervisor.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(supervisor, "TERM_GRACE_SECONDS", 0)
    observed_disappearance = [False]

    def killpg(pid, sig):
        assert not observed_disappearance[0], "do not inspect or signal a retired group ID"
        if sig == 0:
            observed_disappearance[0] = True
            raise ProcessLookupError

    monkeypatch.setattr(supervisor.os, "killpg", killpg)
    supervisor._stop_group(process)
    assert observed_disappearance[0]
    assert process.waits == [1.0]


@pytest.mark.parametrize("operation", ["TERM", "KILL", "wait", "remaining-group"])
def test_cleanup_failure_is_bounded_and_reported(monkeypatch, operation):
    process = fake_process(
        wait_error=subprocess.TimeoutExpired("worker", 1) if operation == "wait" else None
    )
    monkeypatch.setattr(supervisor.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(supervisor, "TERM_GRACE_SECONDS", 0)
    present, signals = [True], []

    def killpg(pid, sig):
        if not present[0]:
            raise ProcessLookupError
        if sig:
            signals.append(sig)
        if (sig == signal.SIGTERM and operation == "TERM") or (
            sig == signal.SIGKILL and operation == "KILL"
        ):
            raise PermissionError("injected signal failure")
        if sig == signal.SIGKILL and operation != "remaining-group":
            present[0] = False

    monkeypatch.setattr(supervisor.os, "killpg", killpg)
    with pytest.raises(RuntimeError, match="cleanup failed"):
        supervisor._stop_group(process)
    assert signal.SIGKILL in signals
    assert process.waits == [1.0]


@pytest.mark.parametrize("pid", [1, True, -1, os.getpid(), os.getpgrp()])
def test_cleanup_never_signals_parent_or_unowned_group(monkeypatch, pid):
    monkeypatch.setattr(
        supervisor.os, "killpg", lambda *args: pytest.fail("unowned group was signalled")
    )
    with pytest.raises(ValueError, match="unowned"):
        supervisor._stop_group(fake_process(pid))


def test_cleanup_error_does_not_hide_original_worker_failure(setup, monkeypatch):
    def failure(process):
        raise RuntimeError("synthetic cleanup error")

    monkeypatch.setattr(supervisor, "_stop_group", failure)
    monkeypatch.setattr(supervisor, "_group_exists", lambda pgid: True)
    with pytest.raises(ValueError, match="unsuccessfully") as captured:
        setup.run("nonzero")
    assert any("synthetic cleanup error" in note for note in captured.value.__notes__)
    no_ack(setup)
