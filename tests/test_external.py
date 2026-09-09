from __future__ import annotations

import hashlib
import json
import subprocess

from fusion_baselines.external import verify_external_spec


def test_verify_external_spec(tmp_path):
    repository = tmp_path / "checkout"
    repository.mkdir()
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(["git", "-C", str(repository), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.email", "test@example.test"],
        check=True,
    )
    payload = b"baseline"
    sample = repository / "sample.dat"
    sample.write_bytes(payload)
    subprocess.run(["git", "-C", str(repository), "add", "sample.dat"], check=True)
    subprocess.run(["git", "-C", str(repository), "commit", "-qm", "fixture"], check=True)
    commit = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    spec = {
        "repository": {"path": "checkout", "commit": commit},
        "files": [
            {
                "path": "checkout/sample.dat",
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        ],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    assert verify_external_spec(tmp_path, spec_path) == []
    sample.write_bytes(b"modified after commit")
    spec["files"][0]["sha256"] = hashlib.sha256(sample.read_bytes()).hexdigest()
    spec_path.write_text(json.dumps(spec))
    assert any("working-tree changes" in e for e in verify_external_spec(tmp_path, spec_path))


def test_verify_external_spec_detects_mutation(tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "repository": {"path": "missing", "commit": "expected"},
                "files": [{"path": "missing.dat", "sha256": "expected"}],
            }
        )
    )
    errors = verify_external_spec(tmp_path, spec_path)
    assert len(errors) == 2


def test_external_repository_cannot_escape_root(tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps({"repository": {"path": "..", "commit": "x"}, "files": []}))
    assert verify_external_spec(tmp_path, spec_path) == ["repository path escapes project root"]
