"""POSIX supervision of one owned no-search fine cell, not scientific acceptance.

Only an explicitly returned acknowledgement reference acknowledges completion.
Preserved files after failed publication are not acknowledged results. This is a
single-writer local execution boundary, not isolation for untrusted PR code or a
kill-on-parent-death service. Production time/resource limits are not arguments.
"""

import copy
import os
import subprocess
import time
from pathlib import Path

from fusion_baselines.protected_fine_control import (
    MAX_FRAME_BYTES,
    THREADS,
    FineControlReader,
    _clock,
)
from fusion_baselines.protected_run_ledger import _reference
from fusion_baselines.protected_search_journal import _encode
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
    "fine_result",
    "source_before",
    "source_after",
    "threads",
    "parent_pid",
    "worker_pid",
    "started_monotonic",
    "returned_monotonic",
    "complete_execution",
    "arithmetic_consistency",
    "fine_numerical_qualification",
    "absolute_field_geometry_pass",
    "physical_admission",
    "resolved_fine_grid_improvement",
    "pareto_dominance",
    "realized_field_transfer",
    "step4_pass",
    "sota_advance",
    "ms1_reached",
}

SCOPE = dict.fromkeys(
    (
        "arithmetic_consistency",
        "fine_numerical_qualification",
        "absolute_field_geometry_pass",
        "physical_admission",
        "resolved_fine_grid_improvement",
        "pareto_dominance",
        "realized_field_transfer",
        "step4_pass",
        "sota_advance",
        "ms1_reached",
    ),
    False,
)


def read_json(reference):
    # Timed caller admission precedes scientific/storage imports.
    from fusion_baselines.protected_run_snapshots import read_json as checked_read

    return checked_read(reference)


def _store(directory):
    from fusion_baselines.protected_run_snapshots import SnapshotStore

    return SnapshotStore(directory)


def _threads():
    _need(
        all(os.environ.get(k) == v for k, v in THREADS.items()),
        "fine parent requires unchanged single-thread environment",
    )


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, label):
    _need(_encode(actual) == _encode(expected), "exact parent binding: " + label)


def _configuration(value, *, started, parent_pid, output):
    _need(type(value) is dict and set(value) == _CONFIG_KEYS, "exact worker config schema")
    _same(value["schema_version"], 1, "config schema version")
    _same(value["kind"], "protected-fine-worker-config", "config kind")
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


def _returned(reference, config, config_ref, *, worker_pid, spawned, message):
    _inside(reference, Path(config["output"]))
    envelope = read_json(reference)
    _need(type(envelope) is dict and set(envelope) == _RETURN_KEYS, "exact worker return schema")
    _same(envelope["schema_version"], 1, "return schema version")
    _same(envelope["kind"], "protected-fine-worker-return", "return kind")
    for key in ("case", "threads", "parent_pid", "started_monotonic"):
        _same(envelope[key], config[key], key)
    _same(envelope["config"], config_ref, "configuration reference")
    source = read_json(config["source"])
    for key in ("source_before", "source_after"):
        _inside(envelope[key], Path(config["output"]))
        _same(read_json(envelope[key]), source, key)
    _same(envelope["worker_pid"], worker_pid, "launched worker PID")
    for key in ("complete_execution", *SCOPE):
        _need(envelope[key] is False, "fine worker plumbing cannot assert " + key)
    returned = _clock(envelope["returned_monotonic"])
    _need(spawned <= returned <= message["monotonic"], "bounded fine worker return clock")
    _inside(envelope["fine_result"], Path(config["output"]))
    result = read_json(envelope["fine_result"])
    _need(type(result) is dict, "plain cell result required")
    _same(result.get("schema_version"), 1, "cell schema version")
    _same(result.get("kind"), "protected-fine-cell-execution", "cell result kind")
    _same(result.get("case"), config["case"], "cell result case")
    _need(result.get("producer_complete") is True, "explicit cell producer completion required")
    for key in ("complete_execution", *SCOPE):
        _need(result.get(key) is False, "fine cell plumbing cannot assert " + key)
    return envelope


def _owned_group(process):
    from fusion_baselines.protected_process import _owned_group as owned

    return owned(process)


def _group_exists(pgid):
    from fusion_baselines.protected_process import _group_exists as exists

    return exists(pgid)


def _stop_group(process):
    # Frozen qualified TERM/KILL/reap and group-retirement implementation only;
    # never construction's supervisor, config schema or three-phase reader.
    from fusion_baselines.protected_process import _stop_group as stop

    return stop(process)


def supervise_fine_cell(config_builder, command_builder, output, *, validate_return, source_check):
    """Run one fresh no-search fine cell and return a checked immutable parent acknowledgement.

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
        reader = FineControlReader(started)
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
        _threads()
        before = space_check(output.parent, START_RESERVE_BYTES)
        _need(not _POISONED, "reentrant parent execution poisoned")
        reader.check(time.monotonic())
        minimum = before["free_bytes"]
        output.mkdir(exist_ok=False)
        _threads()
        store = _store(output / "parent")

        def guard():
            nonlocal minimum
            _threads()
            _need(not _POISONED, "reentrant parent execution poisoned")
            reader.check(time.monotonic())
            current = space_check(output, LIVE_RESERVE_BYTES)
            _threads()
            _need(not _POISONED, "reentrant parent execution poisoned")
            minimum = min(minimum, current["free_bytes"])
            reader.check(time.monotonic())
            _need(store._failed is False, "parent publication store poisoned")

        guard()
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
            # One bounded read per poll; exactly one complete frame is legitimate.
            if eof:
                return
            try:
                chunk = os.read(read_fd, MAX_FRAME_BYTES)
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
                            kind="protected-fine-parent-control-observation",
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
            spawned=spawned,
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
            spawned=spawned,
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
            kind="protected-fine-parent-acknowledgement",
            parent_acknowledged=True,
            complete_execution=True,
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
            acknowledgement_clock_scope="before-terminal-publication",
            minimum_observed_free_bytes=minimum,
            control_observations=observations,
            returned_result=reader.returned,
            independent_physical_audit_pass=False,
            **SCOPE,
        )
        # All fallible guards/handles are complete before terminal publication.
        # A publication fsync failure can leave a file; only this returned ref is
        # acknowledged. No filename discovery can substitute for that return.
        reference = store.json("acknowledgement", result)
        # Final storage is part of the cell deadline. A late persisted file is
        # only a failed prefix, never an acknowledged return. No disk/source
        # callback follows publication; clock, thread and poison checks remain.
        reader.check(time.monotonic())
        _threads()
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
