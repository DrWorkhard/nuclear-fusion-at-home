"""Temporary-repository controls for the limited, read-only publication inventory."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/publication_inventory.py"


@pytest.fixture
def repository(tmp_path):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True, env=env)

    def git(*args):
        return subprocess.check_output(
            ["git", "-c", "user.name=Inventory Fixture", "-c",
             "user.email=inventory@example.invalid", "-c", "commit.gpgsign=false", *args],
            cwd=tmp_path, env=env,
        )

    def inventory():
        before = git("status", "--porcelain")
        completed = subprocess.run(
            [sys.executable, "-I", "-S", str(SCRIPT)], cwd=tmp_path, env=env,
            check=True, stdout=subprocess.PIPE, text=True,
        )
        assert git("status", "--porcelain") == before
        report = json.loads(completed.stdout)
        assert report["source_revision"] == git("rev-parse", "HEAD").decode().strip()
        assert report["regex_selftests"] == {"positive": 7, "negative": 7, "passed": True}
        assert report["publication_approved"] is False
        assert report["provider_exhaustive_secret_scan"] is False
        assert report["license_rights_clearance"] is False
        return report, completed.stdout

    return tmp_path, git, inventory


def test_removed_credentials_and_home_paths_still_appear_in_history(repository):
    directory, git, inventory = repository
    credential = "ghp_" + "A" * 36
    home_path = "/Users/" + "example-private-name/work/"
    (directory / "history.txt").write_text(credential + "\n" + home_path)
    (directory / "keep.txt").write_text("ordinary text")
    git("add", "history.txt", "keep.txt")
    git("commit", "--quiet", "-m", "first fixture")
    git("rm", "--quiet", "history.txt")
    git("commit", "--quiet", "-m", "second fixture")
    report, output = inventory()
    assert report["reachable_object_counts"]["commit"] == 2
    assert report["head_tracked_files"] == 1
    for name in ("github_credential_shape", "unix_home_path"):
        assert report["matched_head_file_counts"][name] == 0
        assert report["matched_reachable_blob_counts"][name] == 1
    location = report["credential_shape_locations"]["github_credential_shape"][0]
    assert location["path"] == "history.txt"
    assert location["present_at_head"] is False
    assert credential not in output and home_path not in output


def test_each_reported_pattern_detects_a_tracked_synthetic_fixture(repository):
    directory, git, inventory = repository
    patterns = [
        "-----BEGIN " + "PRIVATE KEY-----",
        "ghp_" + "A" * 36,
        "sk-" + "B" * 32,
        "AKIA" + "C" * 16,
        "https://" + "example:placeholder-password@example.invalid",
        "/Users/" + "example-private-name/work/",
        "C:" + chr(92) + "Users" + chr(92) + "private-name" + chr(92),
    ]
    (directory / "samples.txt").write_text("\n".join(patterns))
    git("add", "samples.txt")
    git("commit", "--quiet", "-m", "synthetic patterns")
    report, output = inventory()
    assert set(report["matched_head_file_counts"].values()) == {1}
    assert set(report["matched_reachable_blob_counts"].values()) == {1}
    assert report["head_tracked_files"] == 1
    assert report["distinct_commit_author_or_committer_emails"] == 1
    assert report["matched_values_disclosed"] is False
    assert all(value not in output for value in patterns)


def test_untracked_content_is_not_silently_claimed_as_scanned(repository):
    directory, git, inventory = repository
    (directory / "keep.txt").write_text("ordinary text")
    git("add", "keep.txt")
    git("commit", "--quiet", "-m", "clean fixture")
    (directory / "untracked.txt").write_text("ghp_" + "A" * 36)
    report, _ = inventory()
    assert report["ignored_or_untracked_files_scanned"] is False
    assert report["head_tracked_files"] == 1
    assert set(report["matched_reachable_blob_counts"].values()) == {0}
