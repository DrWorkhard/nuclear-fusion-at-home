"""Supervise the single, preregistered issue-53 comparison on a POSIX native host."""

import argparse
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fusion_baselines.provenance import build_run_record  # noqa: E402

SEARCH_SECONDS, CHECK_SECONDS = 1800, 900
MAX_BYTES, START_RESERVE, LIVE_RESERVE = 256*1024**2, 3*1024**3, 2*1024**3
REPORT_RESERVE = 64*1024
SNAPSHOT_SHA = "84bbdf3eca274981dfff80c967b6fd623a1a40350e583407cbb7262c26820217"
WOUT_SHA = "83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e"
SERIAL_RUNNER = ("import runpy,sys; sys.modules['mpi4py']=None; "
                 "sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')")


class CleanupError(RuntimeError):
    """An uncertain process-group state forbids starting the next arm."""


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def retained_bytes(output):
    # Include logs, temporary writes and matplotlib's per-arm cache.
    total = 0
    for path in output.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:  # An atomic recorder rename can race the watchdog.
            pass
    return total


def resource_error(output):
    if retained_bytes(output) > MAX_BYTES-REPORT_RESERVE:
        return "aggregate storage ceiling"
    if shutil.disk_usage(output).free < LIVE_RESERVE:
        return "live disk reserve"
    return None


def diagnostic_deadline(marker, outer_deadline):
    if not marker.exists():
        return outer_deadline
    value = read(marker)["deadline_monotonic"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("invalid diagnostic deadline")
    return min(value, outer_deadline)


def stop(process):
    # Each child owns a process group, so native descendants cannot outlive an overrun.
    # Reap an exited leader first (macOS can return EPERM for a zombie-only group),
    # but still signal the group: surviving descendants are independent of its exit.
    process.poll()
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        raise CleanupError("cannot terminate child process group") from exc
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError as exc:
            raise CleanupError("cannot confirm child process-group cleanup") from exc
    process.wait()


def supervise(command, arm, label, deadline, marker=None):
    started = time.monotonic()
    environment = dict(PATH="/usr/bin:/bin:/usr/sbin:/sbin", TMPDIR=str(arm),
                       PYTHONDONTWRITEBYTECODE="1", MPLCONFIGDIR=str(arm/"mpl-cache"),
                       OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                       VECLIB_MAXIMUM_THREADS="1", MKL_NUM_THREADS="1")
    reason, process = resource_error(arm), None
    if started >= deadline:
        reason = reason or "deadline"
    try:
        if reason is None:
            with (arm/f"{label}.log").open("xb") as log:
                process = subprocess.Popen(command, cwd=ROOT, env=environment,
                                           stdin=subprocess.DEVNULL,
                                           stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True)
                while True:
                    if marker is not None:
                        deadline = diagnostic_deadline(marker, deadline)
                    # Check resources before accepting even a zero-status return.
                    reason = resource_error(arm)
                    if time.monotonic() >= deadline:
                        reason = reason or "deadline"
                    if reason is not None or process.poll() is not None:
                        break
                    time.sleep(.1)
    finally:
        if process is not None:
            stop(process)
    reason = reason or resource_error(arm)
    if time.monotonic() >= deadline:
        reason = reason or "deadline"
    return dict(command=command, returncode=None if process is None else process.returncode,
                stop_reason=reason, elapsed_s=time.monotonic()-started,
                deadline_monotonic=deadline,
                completed=reason is None and process is not None and process.returncode == 0)


def command(script, *args):
    return [sys.executable, "-c", SERIAL_RUNNER, str(ROOT/"scripts"/script),
            *(str(arg) for arg in args)]


def run_arm(order, snapshot, wout, arm):
    arm.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    result = dict(order=order, completed=False, physical_admission=False)
    try:
        if shutil.disk_usage(arm).free < START_RESERVE:
            raise OSError("3 GiB initial disk reserve required")
        marker = arm/"fit"/"checks-start.json"
        outer = started+SEARCH_SECONDS+CHECK_SECONDS
        result["fit"] = supervise(command("fit_coils.py", "--snapshot", snapshot,
            "--wout", wout, "--output", arm/"fit", "--seconds", SEARCH_SECONDS,
            "--check-seconds", CHECK_SECONDS, "--order", order), arm, "fit", outer, marker)
        if not result["fit"]["completed"] or not read(arm/"fit"/"result.json")["completed"]:
            raise ValueError("fitting or shared diagnostics incomplete")
        if not marker.exists():
            raise ValueError("missing diagnostic clock; tracing cannot receive a fresh budget")
        deadline = diagnostic_deadline(marker, outer)
        result["trace"] = supervise(command("trace_surfaces.py", "--snapshot",
            arm/"fit"/"selected-snapshot.json", "--wout", wout, "--output", arm/"trace",
            "--direct", "--transits", 200), arm, "trace", deadline)
        if not result["trace"]["completed"] or not read(arm/"trace"/"result.json")["completed"]:
            raise ValueError("realized-field diagnostic incomplete")
        result["completed"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["cleanup_failed"] = isinstance(exc, CleanupError)
    result.update(elapsed_s=time.monotonic()-started, retained_bytes=retained_bytes(arm))
    save(arm/"supervisor.json", result)
    return result


def run(snapshot, wout, output, revision):
    if os.name != "posix":
        raise ValueError("this study launcher requires POSIX process groups")
    record = build_run_record(ROOT)
    repository = record["repository"]
    if repository["dirty"] or repository["commit"] != revision:
        raise ValueError("clean checkout at the explicitly reviewed full revision required")
    if digest(snapshot) != SNAPSHOT_SHA or digest(wout) != WOUT_SHA:
        raise ValueError("original declared snapshot and Wout required")
    paths = [snapshot, wout, Path(sys.executable).resolve(),
             *sorted((ROOT/"src").rglob("*.py")), *sorted((ROOT/"scripts").glob("*.py")),
             ROOT/"docs/optimization/ISSUE53_COIL_FREEDOM.md"]
    sources = {str(path): digest(path) for path in paths}
    output.mkdir(parents=True, exist_ok=False)
    result = dict(completed=False, physical_admission=False, provenance=record,
                  sources_before=sources, serial_runner=SERIAL_RUNNER, arms=[],
                  search_seconds=SEARCH_SECONDS, diagnostic_seconds=CHECK_SECONDS,
                  storage_bytes=MAX_BYTES, watchdog_interval_s=.1)
    save(output/"study.json", result)
    try:
        for name, order in (("C", 5), ("P", 8)):
            # A failed arm is retained. Still collect the other declared arm once.
            result["arms"].append(run_arm(order, snapshot, wout, output/name))
            save(output/"study.json", result)
            if result["arms"][-1].get("cleanup_failed"):
                break  # Do not overlap an unknown surviving process group.
        result["sources_after"] = {path: digest(Path(path)) for path in sources}
        result["completed"] = (result["sources_after"] == sources
                               and len(result["arms"]) == 2
                               and all(arm["completed"] for arm in result["arms"]))
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        save(output/"study.json", result)
    return 0 if result["completed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--wout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True, help="full reviewed producer commit")
    args = parser.parse_args()
    raise SystemExit(run(args.snapshot.resolve(), args.wout.resolve(), args.output.resolve(),
                         args.revision))
