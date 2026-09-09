import subprocess
from pathlib import Path

from fusion_baselines.provenance import build_run_record, git_state


def test_git_state_for_project_checkout():
    state = git_state(__import__("pathlib").Path.cwd())
    assert state["available"] is True
    assert isinstance(state["branch"], str)
    assert len(state["commit"]) == 40


def test_git_state_detached_head(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.test",
            "commit",
            "--allow-empty",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "--detach", "-q"], check=True)
    state = git_state(tmp_path)
    assert state["available"] and not state["dirty"]
    assert state["branch"] == ""
    assert len(state["commit"]) == 40


def test_run_record_has_required_sections(tmp_path):
    record = build_run_record(Path.cwd(), {"missing": tmp_path})
    assert record["schema_version"] == 1
    assert record["repository"]["available"] is True
    assert record["external_repositories"]["missing"]["available"] is False
