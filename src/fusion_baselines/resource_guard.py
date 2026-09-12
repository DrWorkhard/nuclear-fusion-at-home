"""Bound scratch checkouts and stop owned subprocesses before exhausting disk."""

import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

GIB = 1024**3
STELLCOILBENCH_PATHS = (
    "src",
    "plasma_surfaces",
    "cases/basic_LandremanPaulQA.yaml",
    "cases/basic_W7X.yaml",
)


def space_check(path, required_bytes, *, disk_usage=shutil.disk_usage):
    if required_bytes <= 0:
        raise ValueError("positive reserve required")
    usage = disk_usage(path)
    record = dict(
        path=str(Path(path).resolve()),
        free_bytes=usage.free,
        required_bytes=required_bytes,
        sufficient=usage.free >= required_bytes,
    )
    if not record["sufficient"]:
        raise OSError(f"disk reserve not met: {record}")
    return record


def sparse_patterns(paths):
    """Explicit literal paths only; root metadata plus selected descendants."""
    for path in paths:
        if (
            not path
            or path.startswith("/")
            or ".." in Path(path).parts
            or any(c in path for c in "*?[]!\\\n\r")
        ):
            raise ValueError("literal repository-relative paths required")
    return ["/*", "!/*/", *(f"/{path}" for path in paths)]


def stop_owned_process(process):
    """Only called for a process we launched in its own new session."""
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def guarded_run(
    command, *, cwd, env, stdout, space_root, reserve_bytes, check=space_check, interval=0.5
):
    before = check(space_root, reserve_bytes)
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=stdout,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    minimum = before["free_bytes"]
    try:
        while process.poll() is None:
            minimum = min(minimum, check(space_root, reserve_bytes)["free_bytes"])
            time.sleep(interval)
        after = check(space_root, reserve_bytes)
        minimum = min(minimum, after["free_bytes"])
        return dict(returncode=process.returncode, minimum_observed_free_bytes=minimum)
    finally:
        stop_owned_process(process)
