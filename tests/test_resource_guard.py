import os
import shutil
import subprocess
import sys

import pytest

from fusion_baselines.resource_guard import guarded_run, space_check, sparse_patterns


def test_reserve_boundary_and_invalid_limits(tmp_path):
    usage = shutil.disk_usage(tmp_path)
    fake = lambda _: usage._replace(free=100)  # noqa: E731
    assert space_check(tmp_path, 100, disk_usage=fake)["sufficient"]
    with pytest.raises(OSError, match="reserve not met"):
        space_check(tmp_path, 101, disk_usage=fake)
    with pytest.raises(ValueError):
        space_check(tmp_path, 0, disk_usage=fake)


@pytest.mark.parametrize("path", ["../escape", "/absolute", "sub/*", "!negate", "a\nb"])
def test_sparse_paths_are_literal(path):
    with pytest.raises(ValueError):
        sparse_patterns([path])


def test_sparse_checkout_keeps_pin_and_excludes_submission_archive(tmp_path):
    source, dest = tmp_path / "source", tmp_path / "dest"
    source.mkdir()

    def git(*args, cwd=source):
        return subprocess.check_output(["git", *args], cwd=cwd, stderr=subprocess.STDOUT)

    git("init")
    for path in (
        "README.md",
        "src/a.py",
        "cases/basic.yaml",
        "cases/large.bin",
        "submissions/large.bin",
    ):
        file = source / path
        file.parent.mkdir(exist_ok=True)
        file.write_text(path)
    git("add", ".")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture")
    pin = git("rev-parse", "HEAD").decode().strip()
    (source / "src/a.py").write_text("user change must not be copied")
    before = git("status", "--porcelain")
    git("clone", "--no-hardlinks", "--no-checkout", str(source), str(dest))
    git(
        "sparse-checkout",
        "set",
        "--no-cone",
        *sparse_patterns(["src", "cases/basic.yaml"]),
        cwd=dest,
    )
    git("checkout", "--detach", pin, cwd=dest)
    assert git("rev-parse", "HEAD", cwd=dest).decode().strip() == pin
    assert (dest / "src/a.py").read_text() == "src/a.py"
    assert (dest / "README.md").exists() and (dest / "cases/basic.yaml").exists()
    assert not (dest / "submissions").exists() and not (dest / "cases/large.bin").exists()
    assert git("status", "--porcelain", cwd=dest) == b""
    assert git("status", "--porcelain") == before


def test_subprocess_not_launched_without_reserve(tmp_path):
    def reject(*_):
        raise OSError("low space")

    with pytest.raises(OSError, match="low space"):
        guarded_run(
            ["nonexistent-command"],
            cwd=tmp_path,
            env=os.environ,
            stdout=subprocess.DEVNULL,
            space_root=tmp_path,
            reserve_bytes=1,
            check=reject,
        )


def test_guard_stops_own_process_when_space_drops(tmp_path, monkeypatch):
    launched = []
    original = subprocess.Popen

    def capture(*args, **kwargs):
        process = original(*args, **kwargs)
        launched.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", capture)
    calls = 0

    def check(*_):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise OSError("low space")
        return dict(free_bytes=100)

    with pytest.raises(OSError, match="low space"):
        guarded_run(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            cwd=tmp_path,
            env=os.environ,
            stdout=subprocess.DEVNULL,
            space_root=tmp_path,
            reserve_bytes=1,
            check=check,
            interval=0.001,
        )
    assert len(launched) == 1 and launched[0].poll() is not None


def test_guard_returns_child_failure_and_space_measurement(tmp_path):
    record = guarded_run(
        [sys.executable, "-c", "raise SystemExit(7)"],
        cwd=tmp_path,
        env=os.environ,
        stdout=subprocess.DEVNULL,
        space_root=tmp_path,
        reserve_bytes=1,
        interval=0.001,
    )
    assert record["returncode"] == 7 and record["minimum_observed_free_bytes"] > 0
