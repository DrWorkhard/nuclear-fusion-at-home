"""One fixed offline diagnostic, with an external 65-second worker timeout."""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARD_TIMEOUT = 65
LOG_LIMIT = 64 * 1024
TOTAL_LIMIT = 8 * 1024**2


def reference(path):
    raw = path.read_bytes()
    return dict(path=str(path.absolute()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def supervise(command, output, *, timeout=HARD_TIMEOUT):
    """Accept only an explicit receipt from a successful worker, never file discovery.

    Used only for the trusted, serial saved-data worker. Captured console output
    is expected to be small; this is not a process-memory sandbox.
    """
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    record = dict(complete=False, command=command, hard_timeout_seconds=timeout,
                  launcher=reference(Path(__file__)), returncode=None, timed_out=False,
                  result=None, error=None)
    stdout, stderr = b"", b""
    process = None
    try:
        env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
               "VECLIB_MAXIMUM_THREADS": "1"}
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except BaseException:
            # Kill the owned group before reaping its leader; no grace-period work.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            finally:
                stdout, stderr = process.communicate(timeout=5)
            raise
        record["returncode"] = process.returncode
        if process.returncode != 0:
            raise ValueError("worker failed; any published result remains incomplete")
        if len(stdout) + len(stderr) > LOG_LIMIT:
            raise ValueError("console output limit")
        returned = json.loads(stdout)
        expected = output / "analysis" / "result.json"
        if expected.is_symlink() or not expected.is_file() or expected.stat().st_size > TOTAL_LIMIT:
            raise ValueError("bounded regular returned result required")
        if returned != reference(expected):
            raise ValueError("explicit returned reference differs from saved result")
        result = json.loads(expected.read_bytes())
        if result.get("complete") is not True or len(result.get("comparisons", [])) != 8:
            raise ValueError("complete eight-comparison worker result required")
        if result.get("sources_before") != result.get("sources_after"):
            raise ValueError("worker sources changed")
        payload_bytes = sum(p.stat().st_size for p in (output / "analysis").iterdir())
        if payload_bytes + len(stdout) + len(stderr) + LOG_LIMIT > TOTAL_LIMIT:
            raise ValueError("8 MiB combined output cap including receipt reserve")
        record.update(complete=True, result=returned, scientific_bytes=payload_bytes)
    except Exception as error:
        record.update(error=f"{type(error).__name__}: {error}",
                      timed_out=isinstance(error, subprocess.TimeoutExpired))
        if process is not None:
            record["returncode"] = process.returncode
    finally:
        record["elapsed_seconds"] = time.monotonic() - started
        record["console_truncated"] = len(stdout) + len(stderr) > LOG_LIMIT
        stdout = stdout[:LOG_LIMIT]
        stderr = stderr[:LOG_LIMIT - len(stdout)]
        for name, raw in (("stdout.txt", stdout), ("stderr.txt", stderr)):
            with (output / name).open("xb") as stream:
                if stream.write(raw) != len(raw):
                    raise OSError("short launcher log write")
                stream.flush()
                os.fsync(stream.fileno())
            if (output / name).read_bytes() != raw:
                raise OSError("launcher log readback differs")
        raw = (json.dumps(record, sort_keys=True, allow_nan=False) + "\n").encode()
        if len(raw) > LOG_LIMIT:
            raise ValueError("launcher receipt limit")
        with (output / "execution.json").open("xb") as stream:
            if stream.write(raw) != len(raw):
                raise OSError("short launcher receipt write")
            stream.flush()
            os.fsync(stream.fileno())
        if (output / "execution.json").read_bytes() != raw:
            raise OSError("launcher receipt readback differs")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.absolute()
    command = [sys.executable, str(ROOT / "scripts/analyze_field_residuals.py"),
               "--output", str(output / "analysis")]
    record = supervise(command, output)
    print(json.dumps(record, sort_keys=True))
    return 0 if record["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
