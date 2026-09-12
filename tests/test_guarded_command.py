import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_guarded_command.py"


@pytest.mark.parametrize("code", [0, 2])
def test_real_wrapper_preserves_output_and_exit(tmp_path, code):
    output = tmp_path / "run"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(output),
            "--",
            sys.executable,
            "-c",
            f"import sys; print('synthetic command'); sys.exit({code})",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == code
    report = json.loads((output / "summary.json").read_text())
    assert report["status"] == ("completed" if code == 0 else "command_failed")
    assert report["returncode"] == code
    assert report["minimum_observed_free_bytes"] >= 2 * 1024**3
    log = (output / "command.log").read_bytes()
    assert log == b"synthetic command\n"
    assert report["log"]["sha256"] == hashlib.sha256(log).hexdigest()


def test_existing_output_not_overwritten(tmp_path):
    output = tmp_path / "run"
    output.mkdir()
    sentinel = output / "summary.json"
    sentinel.write_text("prior data")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(output), "--", sys.executable, "-c", "print('not run')"],
        cwd=ROOT,
        capture_output=True,
    )
    assert result.returncode != 0 and sentinel.read_text() == "prior data"
    assert not (output / "command.log").exists()


def test_empty_command_rejected_without_output(tmp_path):
    output = tmp_path / "run"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(output)], cwd=ROOT, capture_output=True
    )
    assert result.returncode != 0 and not output.exists()
