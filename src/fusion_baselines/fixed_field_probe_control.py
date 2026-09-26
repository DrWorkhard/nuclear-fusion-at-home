"""Fixed-probe resource and work accounting, not numerical acceptance.

Single-writer POSIX research execution. All native attempts consume their slot;
an error poisons the ledger. The parent independently bounds child lifetime and
requires an explicit returned reference, never a discovered output file.
"""

import copy
import hashlib
import json
import math
import os
import selectors
import shutil
import signal
import subprocess
import time
from pathlib import Path

from fusion_baselines.protected_search_journal import _encode, _unique_object

PHASE_SECONDS = 600
GRACE_SECONDS = 5
PAIR_BYTES = 512 * 1024**2
MODEL_RESERVE = 64 * 1024**2
TERMINAL_RESERVE = 2 * 1024**2
LIVE_FREE = 2 * 1024**3
START_FREE = 3 * 1024**3
MAX_FRAME = 4096
MAX_FRAMES = 256
MAX_CONTROL_BYTES = 256 * 1024
MAX_LOG_BYTES = 128 * 1024
THREADS = dict.fromkeys(
    ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"),
    "1",
)
SCOPE = dict.fromkeys(("physical_admission", "step4_pass", "ms1_reached", "sota_advance"), False)
LEVELS = [
    dict(index=i, nphi=p, ntheta=p, ncoil=c, ninner=n, offset=o)
    for i, (p, c, n, o) in enumerate(
        (
            (64, 256, 32, 0),
            (128, 256, 32, 0),
            (128, 512, 32, 0),
            (128, 512, 32, 0.5),
            (64, 256, 64, 0),
            (64, 512, 64, 0),
        )
    )
]


def need(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected, message):
    need(_encode(actual) == _encode(expected), "exact identity: " + message)


def requests(level):
    same(level, LEVELS[level["index"]], "registered model level")
    nb, ni = level["nphi"] * level["ntheta"], 3 * level["ninner"] ** 2
    return [
        ("loop", "A", 256),
        ("boundary", "B", nb),
        ("inner", "B", ni),
        ("loop", "A", 256),
        ("boundary", "A", nb),
        ("inner", "A", ni),
        ("loop", "B", 256),
    ]


class Guard:
    def __init__(self, directory, started, *, clock=time.monotonic, space=shutil.disk_usage):
        need(
            type(started) in (int, float) and math.isfinite(started) and started >= 0,
            "finite nonnegative parent start",
        )
        self.directory, self.started, self.clock, self.space = directory, started, clock, space
        self.last = started
        self.failed = False

    def __call__(self):
        try:
            need(not self.failed, "phase guard poisoned")
            now = self.clock()
            need(math.isfinite(now) and now >= self.last, "monotonic finite phase clock")
            self.last = now
            if now - self.started >= PHASE_SECONDS:
                raise TimeoutError("fixed-probe 600 second phase exhausted")
            need(self.space(self.directory).free >= LIVE_FREE, "2 GiB live disk reserve")
        except BaseException:
            self.failed = True
            raise


class PayloadBudget:
    """Shared producer/audit bytes, including known partial writes, never scans.

    A write is precharged by its exact serialized length. Failed writes retain
    that conservative charge. Explicit journal paths and pipe metadata use this
    same account; no budget is reclaimed by deleting or truncating evidence.
    """

    def __init__(self, used=0):
        need(type(used) is int and 0 <= used <= PAIR_BYTES, "shared payload starting bytes")
        self.used = used
        self.failed = False

    def reserve_model(self):
        need(
            not self.failed and self.used + MODEL_RESERVE + TERMINAL_RESERVE <= PAIR_BYTES,
            "64 MiB model and 2 MiB terminal reserves",
        )

    def charge(self, size, *, terminal=False):
        need(type(size) is int and size > 0, "positive exact write byte count")
        limit = PAIR_BYTES if terminal else PAIR_BYTES - TERMINAL_RESERVE
        if (self.failed and not terminal) or self.used + size > limit:
            self.failed = True
            raise ValueError("shared 512 MiB pair payload cap")
        self.used += size


class Work:
    """Exact one-model native sequence; callback receipts persist before dispatch."""

    def __init__(self, level, persist, guard):
        self.expected, self.persist, self.guard = requests(level), persist, guard
        self.events, self.completed, self.pending = [], [], None
        self.failed = False

    def __call__(self, event):
        try:
            need(not self.failed, "native ledger poisoned")
            self.guard()
            need(type(event) is dict, "plain native event")
            i, status = event.get("index"), event.get("status")
            need(type(i) is int and 0 <= i < 7, "bounded native event index")
            field, quantity, points = self.expected[i]
            same(
                {k: event.get(k) for k in ("field", "quantity", "points")},
                dict(field=field, quantity=quantity, points=points),
                "native work dispatch",
            )
            need(
                type(event.get("started_monotonic")) in (int, float)
                and math.isfinite(event["started_monotonic"])
                and event["started_monotonic"] >= 0,
                "native start timestamp",
            )
            base_keys = {
                "index",
                "field",
                "quantity",
                "points",
                "status",
                "started_monotonic",
                "native_started",
                "native_completed",
            }
            if status in ("attempted", "completed"):
                expected_keys = base_keys | (
                    {"completed_monotonic"} if status == "completed" else set()
                )
                need(set(event) == expected_keys, "exact native event keys")
            if status == "attempted":
                need(
                    self.pending is None
                    and i == len(self.completed)
                    and event.get("native_started") is False
                    and event.get("native_completed") is False,
                    "next fresh native attempt",
                )
                need(
                    not self.completed
                    or event["started_monotonic"] >= self.completed[-1]["completed_monotonic"],
                    "nondecreasing cross-call native time",
                )
                self.pending = copy.deepcopy(event)
            elif status == "completed":
                need(
                    self.pending is not None
                    and i == self.pending["index"]
                    and event.get("native_started") is True
                    and event.get("native_completed") is True,
                    "matching native completion",
                )
                same(
                    event["started_monotonic"],
                    self.pending["started_monotonic"],
                    "attempt start retained",
                )
                ended = event.get("completed_monotonic")
                need(
                    type(ended) in (int, float)
                    and math.isfinite(ended)
                    and ended >= event["started_monotonic"],
                    "finite completion timestamp",
                )
                self.completed.append(copy.deepcopy(event))
                self.pending = None
            elif status == "error":
                self.failed = True
            else:
                raise ValueError("native event status")
            self.events.append(copy.deepcopy(event))
            self.persist(copy.deepcopy(event))
            self.guard()
            need(not self.failed, "native error is terminal")
        except BaseException:
            self.failed = True
            raise

    def finish(self, returned):
        try:
            need(
                not self.failed and self.pending is None and len(self.completed) == 7,
                "seven completed native requests without errors",
            )
            same(returned, self.completed, "explicit returned native calls")
            self.guard()
            return dict(requests=7, points=sum(p for _, _, p in self.expected))
        except BaseException:
            self.failed = True
            raise


def send(fd, sequence, kind, payload):
    raw = _encode(dict(sequence=sequence, kind=kind, payload=payload))
    need(
        len(raw) <= MAX_FRAME and type(sequence) is int and 0 <= sequence < MAX_FRAMES,
        "bounded atomic control frame",
    )
    need(os.write(fd, raw) == len(raw), "complete atomic control write")
    return len(raw)


class Frames:
    def __init__(self):
        self.pending = b""
        self.rows = []
        self.returned = None
        self.bytes = 0

    def feed(self, data):
        need(type(data) is bytes and len(data) <= MAX_FRAME, "bounded pipe read")
        self.bytes += len(data)
        need(self.bytes <= MAX_CONTROL_BYTES, "bounded total control stream")
        self.pending += data
        while b"\n" in self.pending:
            raw, self.pending = self.pending.split(b"\n", 1)
            need(
                len(raw) + 1 <= MAX_FRAME and len(self.rows) < MAX_FRAMES, "bounded control stream"
            )
            item = json.loads(raw, object_pairs_hook=_unique_object)
            same(raw.decode() + "\n", _encode(item).decode(), "canonical control frame")
            need(
                type(item) is dict
                and set(item) == {"sequence", "kind", "payload"}
                and type(item["sequence"]) is int
                and item["sequence"] == len(self.rows)
                and self.returned is None,
                "ordered control before sole return",
            )
            need(item["kind"] in ("progress", "returned", "failed"), "control kind")
            need(type(item["payload"]) is dict, "plain control payload")
            self.rows.append(item)
            if item["kind"] in ("returned", "failed"):
                self.returned = item
        need(len(self.pending) < MAX_FRAME, "bounded partial control frame")

    def finish(self):
        need(not self.pending and self.returned is not None, "complete explicit control return")
        return self.returned


def supervise(command, directory, started, *, clock=time.monotonic):
    """Bound a child group without reaping/reusing its leader before cleanup.

    POSIX waitid(WNOWAIT), or macOS kqueue NOTE_EXIT, observes exit while keeping
    our child PID reserved. Every group signal precedes the sole bounded reap.
    Pipes held by descendants cannot keep the parent waiting indefinitely.
    """
    import errno
    import select

    need(os.name == "posix", "POSIX process supervision required")
    need(
        type(started) in (int, float) and math.isfinite(started) and started >= 0,
        "finite nonnegative parent start",
    )
    need(
        signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL,
        "default SIGCHLD disposition preserves owned child identity",
    )
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)
    reader, process, error, last = Frames(), None, None, started
    exit_queue, leader_exited, exit_seen = None, False, None
    signalled, retired, reaped = False, False, False
    deferred_signal_error = None
    log_sizes = dict(stdout=0, stderr=0)
    selector = selectors.DefaultSelector()

    def failure(exc):
        nonlocal error
        detail = f"{type(exc).__name__}: {exc}"
        error = detail if error is None else error + "; " + detail

    def checked_time():
        nonlocal last
        now = clock()
        need(
            type(now) in (int, float) and math.isfinite(now) and now >= last,
            "monotonic finite parent clock",
        )
        last = now
        return now

    def observe_exit():
        nonlocal leader_exited, exit_seen
        if not leader_exited:
            if exit_queue is not None:
                for event in exit_queue.control(None, 1, 0):
                    need(not event.flags & select.KQ_EV_ERROR, "child exit watcher failed")
                    need(
                        event.ident == process.pid and event.fflags & select.KQ_NOTE_EXIT,
                        "owned child exit event",
                    )
                    leader_exited = True
            elif hasattr(os, "waitid"):
                info = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                leader_exited = info is not None
            else:
                # A kqueue registration returning ESRCH means this unreaped
                # child has already exited. No other reaper is authorized.
                leader_exited = True
        if leader_exited and exit_seen is None:
            exit_seen = time.monotonic()
        return leader_exited

    try:
        need(checked_time() - started < PHASE_SECONDS, "on-time phase launch")
        need(shutil.disk_usage(directory).free >= LIVE_FREE, "2 GiB parent live disk reserve")
        need(
            hasattr(os, "waitid") or hasattr(select, "kqueue"),
            "non-reaping POSIX exit observation required",
        )
        selector.register(read_fd, selectors.EVENT_READ, "control")
        with (
            (directory / "stdout.log").open("xb") as stdout,
            (directory / "stderr.log").open("xb") as stderr,
        ):
            process = subprocess.Popen(
                command(write_fd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                pass_fds=(write_fd,),
                start_new_session=True,
                env={**os.environ, **THREADS},
            )
            need(
                type(process.pid) is int and process.pid > 1 and process.pid != os.getpgrp(),
                "separate owned child process group",
            )
            if not hasattr(os, "waitid"):
                exit_queue = select.kqueue()
                try:
                    exit_queue.control(
                        [
                            select.kevent(
                                process.pid,
                                filter=select.KQ_FILTER_PROC,
                                flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                fflags=select.KQ_NOTE_EXIT,
                            )
                        ],
                        0,
                        0,
                    )
                except OSError as exc:
                    if exc.errno != errno.ESRCH:
                        raise
                    exit_queue.close()
                    exit_queue = None
                    leader_exited = True
            logs = dict(stdout=(stdout, process.stdout), stderr=(stderr, process.stderr))
            for key, (_, stream) in logs.items():
                os.set_blocking(stream.fileno(), False)
                selector.register(stream.fileno(), selectors.EVENT_READ, key)
            os.close(write_fd)
            write_fd = None
            while True:
                now = checked_time()
                if now - started >= PHASE_SECONDS + GRACE_SECONDS:
                    raise TimeoutError("fixed-probe 605 second hard termination")
                need(
                    shutil.disk_usage(directory).free >= LIVE_FREE, "2 GiB parent live disk reserve"
                )
                for selected, _mask in selector.select(timeout=0.05):
                    chunk = os.read(selected.fd, MAX_FRAME)
                    if chunk:
                        if selected.data == "control":
                            reader.feed(chunk)
                        else:
                            key = selected.data
                            log_sizes[key] += len(chunk)
                            need(log_sizes[key] <= MAX_LOG_BYTES, "bounded worker log")
                            need(logs[key][0].write(chunk) == len(chunk), "complete log write")
                    else:
                        selector.unregister(selected.fd)
                if observe_exit():
                    if not selector.get_map():
                        break
                    need(
                        time.monotonic() - exit_seen < 1, "exited leader left descendant-held pipes"
                    )
            for output in (stdout, stderr):
                output.flush()
                os.fsync(output.fileno())
            result = reader.finish()
            need(result["kind"] == "returned", "explicit successful return")
            need(checked_time() - started < PHASE_SECONDS, "on-time child exit/return")
    except BaseException as exc:
        failure(exc)
    finally:
        if process is not None:
            # We have NEVER polled/waited/reaped this child. Even after its exit,
            # its reserved PID cannot be recycled while this group is signalled.
            try:
                need(process.pid > 1 and process.pid != os.getpgrp(), "owned group cleanup")
                os.killpg(process.pid, signal.SIGKILL)
                signalled = True
            except ProcessLookupError:
                retired = True
            except PermissionError as exc:
                # Darwin can report EPERM when only the already-exited zombie
                # leader remains. This is not proof of cleanup: defer only with
                # observed exit, then require group absence after the sole reap.
                if leader_exited:
                    deferred_signal_error = str(exc)
                else:
                    failure(exc)
            except BaseException as exc:
                failure(exc)
            cleanup_until = time.monotonic() + 1
            try:
                process.wait(timeout=max(0, cleanup_until - time.monotonic()))
                reaped = True
                if process.returncode != 0:
                    failure(ValueError("nonzero child exit"))
            except BaseException as exc:
                failure(RuntimeError("bounded child reap failed: " + str(exc)))
            # Read-only existence checks are safe after reap; never signal the
            # retired/reusable identifier again. Descendants already got KILL.
            while not retired and time.monotonic() < cleanup_until:
                try:
                    os.killpg(process.pid, 0)
                except ProcessLookupError:
                    retired = True
                except BaseException as exc:
                    failure(exc)
                    break
                else:
                    time.sleep(min(0.01, max(0, cleanup_until - time.monotonic())))
            if not retired:
                failure(RuntimeError("owned group disappearance not confirmed in cleanup bound"))
        if process is not None:
            for stream in (process.stdout, process.stderr):
                try:
                    stream.close()
                except BaseException as exc:
                    failure(exc)
        if exit_queue is not None:
            try:
                exit_queue.close()
            except BaseException as exc:
                failure(exc)
        for close in (selector.close, lambda: os.close(read_fd)):
            try:
                close()
            except BaseException as exc:
                failure(exc)
        if write_fd is not None:
            try:
                os.close(write_fd)
            except BaseException as exc:
                failure(exc)
    try:
        finished = checked_time()
        need(
            finished - started < PHASE_SECONDS or error is not None,
            "final parent cleanup missed phase deadline",
        )
    except BaseException as exc:
        failure(exc)
        finished = None
    return dict(
        schema_version=1,
        complete=error is None,
        error=error,
        started_monotonic=started,
        finished_monotonic=finished,
        exit_code=None if process is None else process.returncode,
        frames=reader.rows,
        partial_frame_hex=reader.pending.hex(),
        group_cleanup=dict(
            signalled_before_reap=signalled,
            reaped=reaped,
            retired=retired,
            deferred_signal_error=deferred_signal_error,
        ),
        log_bytes=log_sizes,
        **SCOPE,
    )


def reference(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
