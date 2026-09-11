import hashlib
import subprocess

from fusion_baselines.evidence_integrity import reference_records, resolve_reference


def test_explicit_pairs_and_current_relocated_tampered_missing(tmp_path):
    (tmp_path / "new.md").write_text("frozen protocol\n")
    record = {
        "path": "/archived/repo/old.md",
        "sha256": hashlib.sha256(b"frozen protocol\n").hexdigest(),
    }
    assert list(reference_records({"list": [record]})) == [record]
    resolved = resolve_reference(record, tmp_path, "/archived/repo", None, {"old.md": "new.md"})
    assert resolved["status"] == "relocated_identical"
    current = {**record, "path": "/archived/repo/new.md"}
    assert resolve_reference(current, tmp_path, "/archived/repo", None)["status"] == "current"
    (tmp_path / "new.md").write_text("modified protocol\n")
    assert resolve_reference(current, tmp_path, "/archived/repo", None)["status"] == "unresolved"
    assert resolve_reference(record, tmp_path, "/archived/repo", None)["status"] == "unresolved"


def test_historical_bytes_are_not_claimed_current(tmp_path):
    def git(*args):
        return subprocess.run(
            ["git", "-C", str(tmp_path), *args], capture_output=True, check=True, text=True
        ).stdout.strip()

    git("init")
    (tmp_path / "code.py").write_text("original\n")
    git("add", "code.py")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "original")
    revision = git("rev-parse", "HEAD")
    (tmp_path / "code.py").write_text("new code\n")
    record = {
        "path": str(tmp_path / "code.py"),
        "sha256": hashlib.sha256(b"original\n").hexdigest(),
    }
    assert resolve_reference(record, tmp_path, tmp_path, revision)["status"] == "historical_git"
    assert resolve_reference(record, tmp_path, tmp_path, "not-a-revision")["status"] == "unresolved"
    assert resolve_reference({**record, "sha256": "bad"}, tmp_path, tmp_path, revision)[
        "status"
    ] == ("unresolved")
