"""POSIX supervision of one owned protected cell, not scientific acceptance.

Only an explicitly returned acknowledgement reference acknowledges completion.
Preserved files after failed publication are not acknowledged results. This is a
single-writer local execution boundary, not isolation for untrusted PR code or a
kill-on-parent-death service. Production time/resource limits are not arguments.
"""

import copy
import os
import signal
import subprocess
import time
from pathlib import Path

from fusion_baselines.protected_run_ledger import _reference
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json
from fusion_baselines.protected_search_journal import _encode
from fusion_baselines.protected_worker_control import (
    MAX_FRAME_BYTES,
    THREADS,
    ControlReader,
    _clock,
)
from fusion_baselines.resource_guard import GIB, space_check

START_RESERVE_BYTES = 3 * GIB
LIVE_RESERVE_BYTES = 2 * GIB
POLL_SECONDS = 0.5
TERM_GRACE_SECONDS = 5.0
# Reaping after escalation is bounded too; this is not an additional TERM grace.
_KILL_REAP_SECONDS = 1.0
_RUNNING = False
_POISONED = False
_CONFIG_KEYS = {
    "schema_version",
    "kind",
    "case",
    "source",
    "output",
    "parent_pid",
    "started_monotonic",
    "threads",
}
_RETURN_KEYS = {
    "schema_version",
    "kind",
    "case",
    "config",
    "cell_result",
    "source_before",
    "source_after",
    "threads",
    "parent_pid",
    "worker_pid",
    "started_monotonic",
    "returned_monotonic",
    "physical_admission",
    "step4_pass",
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, label):
    _need(_encode(actual) == _encode(expected), "exact parent binding: " + label)


def _configuration(value, *, started, parent_pid, output):
    _need(type(value) is dict and set(value) == _CONFIG_KEYS, "exact worker config schema")
    _same(value["schema_version"], 1, "config schema version")
    _same(value["kind"], "protected-cell-worker-config", "config kind")
    _same(value["parent_pid"], parent_pid, "parent PID")
    _same(value["started_monotonic"], started, "parent start clock")
    _same(value["threads"], THREADS, "single-thread environment")
    _same(value["output"], str(output / "worker"), "fresh worker directory")
    case = value["case"]
    _need(type(case) is dict, "plain registered case required")
    expected = [
        dict(
            label=f"{target}-n{nbase}-{method}",
            target=target,
            nbase=nbase,
            order=order,
            seed_label=f"n{nbase}-shape-d100mm",
            method=method,
        )
        for target in ("reference", "selected")
        for nbase, order in ((6, 5), (8, 7))
        for method in ("N", "V")
    ]
    _need(any(_encode(case) == _encode(row) for row in expected), "registered eight-cell case")
    _reference(value["source"])
    read_json(value["source"])
    return copy.deepcopy(value)


def _inside(reference, directory):
    _reference(reference)
    path = Path(reference["path"])
    _need(path.resolve().is_relative_to(directory.resolve()), "result outside owned worker output")


def _returned(reference, config, config_ref, *, worker_pid, search_ended, message):
    _inside(reference, Path(config["output"]))
    envelope = read_json(reference)
    _need(type(envelope) is dict and set(envelope) == _RETURN_KEYS, "exact worker return schema")
    _same(envelope["schema_version"], 1, "return schema version")
    _same(envelope["kind"], "protected-cell-worker-return", "return kind")
    for key in ("case", "threads", "parent_pid", "started_monotonic"):
        _same(envelope[key], config[key], key)
    _same(envelope["config"], config_ref, "configuration reference")
    source = read_json(config["source"])
    for key in ("source_before", "source_after"):
        _inside(envelope[key], Path(config["output"]))
        _same(read_json(envelope[key]), source, key)
    _same(envelope["worker_pid"], worker_pid, "launched worker PID")
    for key in ("physical_admission", "step4_pass"):
        _need(envelope[key] is False, "worker plumbing cannot assert " + key)
    returned = _clock(envelope["returned_monotonic"])
    _need(search_ended <= returned <= message["monotonic"], "bounded worker return clock")
    _inside(envelope["cell_result"], Path(config["output"]))
    result = read_json(envelope["cell_result"])
    _need(type(result) is dict, "plain cell result required")
    _same(result.get("schema_version"), 1, "cell schema version")
    _same(result.get("kind"), "protected-cell-execution", "cell result kind")
    _same(result.get("case"), config["case"], "cell result case")
    _need(result.get("producer_complete") is True, "explicit cell producer completion required")
    for key in ("independent_audit_pass", "physical_admission", "step4_pass"):
        _need(result.get(key) is False, "cell plumbing cannot assert " + key)
    return envelope


def _owned_group(process):
    """Only use the session ID of our own start_new_session child."""
    pid = process.pid
    _need(
        type(pid) is int and pid > 1 and pid not in (os.getpid(), os.getpgrp()),
        "refuse to signal parent or unowned process group",
    )
    try:
        _need(os.getpgid(pid) == pid, "worker did not retain its owned process group")
    except ProcessLookupError:
        # The leader may have exited while its original group still exists.
        pass
    return pid


def _group_exists(pgid):
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    return True


def _signal_group(pgid, sig):
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        pass


def _stop_group(process):
    """Bound TERM/KILL cleanup even after leader exit or failed wait operations.

    The older resource_guard helper returns at leader exit and can wait forever
    after KILL. Keep its frozen behavior untouched; supervise the whole owned
    group here. Orphan zombies can prevent confirming group disappearance, in
    which case cleanup fails rather than certifying success.
    """
    pgid = _owned_group(process)
    process.poll()
    errors = []
    alive = True
    try:
        alive = _group_exists(pgid)
    except OSError as error:
        errors.append(error)
    if alive:
        try:
            _signal_group(pgid, signal.SIGTERM)
        except OSError as error:
            errors.append(error)
    deadline = time.monotonic() + TERM_GRACE_SECONDS
    while alive:
        try:
            process.poll()
            alive = _group_exists(pgid)
            if not alive:
                break
        except OSError as error:
            errors.append(error)
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(POLL_SECONDS, remaining))
    if alive:
        try:
            _signal_group(pgid, signal.SIGKILL)
        except OSError as error:
            errors.append(error)
    try:
        process.wait(timeout=_KILL_REAP_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as error:
        errors.append(error)
    if alive:
        try:
            if _group_exists(pgid):
                errors.append(RuntimeError("owned process group remains after bounded cleanup"))
        except OSError as error:
            errors.append(error)
    if errors:
        raise RuntimeError(
            "owned process cleanup failed: " + "; ".join(map(str, errors))
        ) from errors[0]


def supervise_cell(config_builder, command_builder, output, *, validate_return, source_check):
    """Run one fresh cell and return a checked immutable parent acknowledgement.

    Builders receive ``(started_monotonic, parent_pid, thread_env)`` and
    ``(config_reference, inherited_control_write_fd)`` respectively. Source and
    return validators receive private configuration copies and must return the
    exact singleton True. The latter receives ``(worker_return_ref, config)``;
    it may add a graph audit, but this module makes no physical-audit claim.

    Trusted synchronous parent callbacks must return to permit clock checks;
    the independently monitored child may block indefinitely and is terminated.
    A failed attempt is never resumed, retried or inferred successful from files.
    """
    global _RUNNING, _POISONED
    if _RUNNING:
        _POISONED = True
        raise ValueError("protected cells must run serially in one parent")
    _RUNNING = True
    _POISONED = False
    process = stream = None
    cleanup_needed = False
    read_fd = write_fd = None
    try:
        started = _clock(time.monotonic())
        reader = ControlReader(started)
        parent_pid = os.getpid()
        _need(os.name == "posix", "owned POSIX process groups required")
        _need(
            all(
                callable(f)
                for f in (config_builder, command_builder, validate_return, source_check)
            ),
            "explicit synchronous parent callbacks required",
        )
        output = Path(output)
        _need(output.is_absolute(), "absolute fresh supervision directory required")
        output = output.resolve()
        before = space_check(output.parent, START_RESERVE_BYTES)
        _need(not _POISONED, "reentrant parent execution poisoned")
        reader.check(time.monotonic())
        minimum = before["free_bytes"]
        output.mkdir(exist_ok=False)
        store = SnapshotStore(output / "parent")

        def guard():
            nonlocal minimum
            _need(not _POISONED, "reentrant parent execution poisoned")
            reader.check(time.monotonic())
            current = space_check(output, LIVE_RESERVE_BYTES)
            _need(not _POISONED, "reentrant parent execution poisoned")
            minimum = min(minimum, current["free_bytes"])
            reader.check(time.monotonic())
            _need(store._failed is False, "parent publication store poisoned")

        config = _configuration(
            config_builder(started, parent_pid, copy.deepcopy(THREADS)),
            started=started,
            parent_pid=parent_pid,
            output=output,
        )
        guard()
        _need(source_check(copy.deepcopy(config)) is True, "parent source admission failed")
        guard()
        config_ref = store.json("config", config)
        guard()
        read_fd, write_fd = os.pipe()
        os.set_blocking(read_fd, False)
        command = command_builder(copy.deepcopy(config_ref), write_fd)
        _need(
            type(command) is list
            and bool(command)
            and all(type(arg) is str and arg and "\0" not in arg for arg in command),
            "explicit nonempty argument-vector command required",
        )
        guard()
        stream = (output / "worker-stdout.log").open("xb")
        spawned = _clock(time.monotonic())
        reader.check(spawned)
        process = subprocess.Popen(
            command,
            env=dict(os.environ, **THREADS),
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            pass_fds=(write_fd,),
        )
        cleanup_needed = True
        _owned_group(process)
        os.close(write_fd)
        write_fd = None
        observations, eof = [], False

        def receive():
            nonlocal eof
            # One bounded read per poll prevents a producer flood monopolizing
            # the parent. At most three complete frames can be legitimate.
            if eof:
                return
            try:
                chunk = os.read(read_fd, 3 * MAX_FRAME_BYTES)
            except BlockingIOError:
                return
            if not chunk:
                eof = True
                return
            observed = _clock(time.monotonic())
            for message in reader.feed(chunk, observed):
                _need(message["monotonic"] >= spawned, "phase precedes worker launch")
                observations.append(
                    store.json(
                        f"control-{len(observations)}",
                        dict(
                            schema_version=1,
                            kind="protected-parent-control-observation",
                            observed_monotonic=observed,
                            worker_pid=process.pid,
                            message=message,
                        ),
                    )
                )
                _need(not _POISONED and store._failed is False, "parent observation poisoned")

        while True:
            receive()
            guard()
            if process.poll() is not None:
                # Retire signaling authority as soon as original disappearance
                # is observed. A later callback failure must never re-signal a
                # PID/PGID that could have been reused meanwhile.
                if not _group_exists(_owned_group(process)):
                    cleanup_needed = False
                # No unbounded wait for a descendant which inherited the pipe.
                receive()
                if not eof:
                    receive()
                _need(eof, "control pipe remains open after worker exit")
                break
            time.sleep(POLL_SECONDS)
        exited = _clock(time.monotonic())
        reader.check(exited)
        _need(process.returncode == 0, "worker exited unsuccessfully")
        if cleanup_needed and not _group_exists(_owned_group(process)):
            cleanup_needed = False
        _need(not cleanup_needed, "worker left descendants in owned group")
        messages = reader.finish()
        guard()
        _returned(
            reader.returned,
            config,
            config_ref,
            worker_pid=process.pid,
            search_ended=reader.search_ended,
            message=messages[-1],
        )
        _need(
            validate_return(copy.deepcopy(reader.returned), copy.deepcopy(config)) is True,
            "parent returned-result validation failed",
        )
        guard()
        _need(source_check(copy.deepcopy(config)) is True, "parent final source admission failed")
        # Recheck bytes after caller callbacks, which are not permitted to change
        # the bound files. Validation copies cannot change the parent identities.
        _same(read_json(config_ref), config, "persisted configuration")
        read_json(config["source"])
        _returned(
            reader.returned,
            config,
            config_ref,
            worker_pid=process.pid,
            search_ended=reader.search_ended,
            message=messages[-1],
        )
        guard()
        stream.flush()
        os.fsync(stream.fileno())
        stream.close()
        stream = None
        os.close(read_fd)
        read_fd = None
        guard()
        acknowledged = _clock(time.monotonic())
        reader.check(acknowledged)
        result = dict(
            schema_version=1,
            kind="protected-parent-acknowledgement",
            parent_acknowledged=True,
            case=config["case"],
            config=config_ref,
            source=config["source"],
            threads=copy.deepcopy(THREADS),
            parent_pid=parent_pid,
            worker_pid=process.pid,
            owned_process_group=process.pid,
            returncode=0,
            started_monotonic=started,
            spawned_monotonic=spawned,
            exited_monotonic=exited,
            acknowledged_monotonic=acknowledged,
            minimum_observed_free_bytes=minimum,
            control_observations=observations,
            returned_result=reader.returned,
            physical_admission=False,
            step4_pass=False,
            independent_physical_audit_pass=False,
        )
        # All fallible guards/handles are complete before terminal publication.
        # A publication fsync failure can leave a file; only this returned ref is
        # acknowledged. No filename discovery can substitute for that return.
        reference = store.json("acknowledgement", result)
        # Pure in-memory poison checks, not a postpublication resource/clock
        # callback. As in the cell's terminal writer, swallowed storage or
        # reentrancy failures must prevent acknowledgement of a returned ref.
        _need(not _POISONED and store._failed is False, "parent publication poisoned")
        return reference
    except BaseException as error:
        if process is not None and cleanup_needed:
            try:
                _stop_group(process)
            except BaseException as cleanup:
                error.add_note("Process cleanup failure: " + repr(cleanup))
        raise
    finally:
        # On the successful path these handles are already closed. Failed tails
        # are preserved. Close failures do not replace the primary failure.
        for fd in (read_fd, write_fd):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if stream is not None:
            try:
                stream.close()
            except OSError:
                pass
        _RUNNING = False
