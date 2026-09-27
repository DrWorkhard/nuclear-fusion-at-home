"""Real short synthetic subprocesses; never load project field arrays."""

import json
import sys
from pathlib import Path

import pytest

from scripts import run_field_residuals as launcher


def worker(output, *, exit_code=0, returned=True, complete=True, changed=False):
    # A synthetic explicit receipt, not a scientific qualification.
    report = dict(complete=complete, comparisons=list(range(8)),
                  sources_before={"commit": "synthetic"},
                  sources_after={"commit": "changed" if changed else "synthetic"})
    program = (
        "import hashlib,json,pathlib; "
        f"p=pathlib.Path({str(output / 'analysis/result.json')!r}); "
        "p.parent.mkdir(); "
        f"p.write_text({json.dumps(report)!r}); "
        "raw=p.read_bytes(); "
        "r=dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()); "
        + ("print(json.dumps(r)); " if returned else "")
        + f"raise SystemExit({exit_code})"
    )
    return [sys.executable, "-c", program]


def test_explicit_success_and_exclusive_output(tmp_path):
    output = tmp_path / "run with spaces"
    result = launcher.supervise(worker(output), output)
    assert result["complete"] is True and result["returncode"] == 0
    assert result["result"] == launcher.reference(output / "analysis/result.json")
    assert json.loads((output / "execution.json").read_bytes()) == result
    with pytest.raises(FileExistsError):
        launcher.supervise(worker(output), output)


@pytest.mark.parametrize("kwargs", [dict(exit_code=2), dict(returned=False),
                                   dict(complete=False), dict(changed=True)])
def test_file_presence_is_not_success(tmp_path, kwargs):
    output = tmp_path / "run"
    result = launcher.supervise(worker(output, **kwargs), output)
    assert (output / "analysis/result.json").exists()
    assert result["complete"] is False and result["result"] is None


def test_hard_timeout_kills_worker_and_records_failure(tmp_path):
    output = tmp_path / "run"
    command = [sys.executable, "-c", "import time; print('started',flush=True); time.sleep(30)"]
    result = launcher.supervise(command, output, timeout=0.15)
    assert result["complete"] is False and result["timed_out"] is True
    assert result["returncode"] < 0 and result["elapsed_seconds"] < 5
    assert (output / "stdout.txt").read_bytes() == b"started\n"


def test_launch_error_is_recorded(tmp_path):
    result = launcher.supervise([str(tmp_path / "absent")], tmp_path / "run")
    assert result["complete"] is False and result["returncode"] is None
    assert result["error"].startswith("FileNotFoundError:")


def test_console_cap_does_not_publish_oversize_log(tmp_path):
    output = tmp_path / "run"
    command = [sys.executable, "-c", f"print('x'*{launcher.LOG_LIMIT + 1})"]
    result = launcher.supervise(command, output)
    assert result["complete"] is False and result["console_truncated"] is True
    assert (output / "stdout.txt").stat().st_size == launcher.LOG_LIMIT


def test_default_timeout_is_registered():
    assert launcher.HARD_TIMEOUT == 65


@pytest.mark.parametrize("name", ["stdout.txt", "stderr.txt", "execution.json"])
def test_short_publication_cannot_return_success(tmp_path, monkeypatch, name):
    output = tmp_path / "run"
    original = Path.open

    class ShortWriter:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, raw):
            # Even an empty stderr write returning an invalid count must fail.
            return len(raw) - 1

    def open_file(path, mode="r", *args, **kwargs):
        stream = original(path, mode, *args, **kwargs)
        return ShortWriter(stream) if mode == "xb" and path.name == name else stream

    monkeypatch.setattr(Path, "open", open_file)
    with pytest.raises(OSError, match="short launcher"):
        launcher.supervise(worker(output), output)
