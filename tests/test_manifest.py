from __future__ import annotations

import hashlib

from fusion_baselines.manifest import validate_manifest


def _manifest(digest: str) -> dict:
    return {
        "schema_version": 1,
        "case_id": "test-case",
        "kind": "open_qi",
        "source": {"url": "https://example.test/data", "citation": "Test et al."},
        "conventions": {
            "length_unit": "m",
            "field_unit": "T",
            "coordinate_system": "right-handed cylindrical (R, phi, Z)",
            "current_sign": "right-hand rule about curve parameterization",
        },
        "files": [{"role": "vmec_input", "path": "input.test", "sha256": digest}],
    }


def test_manifest_hash_validation(tmp_path):
    payload = b"&INDATA\n/\n"
    (tmp_path / "input.test").write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    assert validate_manifest(_manifest(digest), tmp_path) == []


def test_manifest_rejects_changed_file(tmp_path):
    (tmp_path / "input.test").write_text("changed")
    errors = validate_manifest(_manifest("0" * 64), tmp_path)
    assert any("sha256 does not match" in error for error in errors)


def test_structure_only_supports_pre_intake_templates(tmp_path):
    errors = validate_manifest(_manifest("pending"), tmp_path, verify_files=False)
    assert errors == []


def test_manifest_rejects_path_outside_explicit_data_root(tmp_path):
    outside = tmp_path.parent / "outside-input"
    outside.write_text("not trusted")
    data = _manifest(hashlib.sha256(b"not trusted").hexdigest())
    data["files"][0]["path"] = "../outside-input"
    errors = validate_manifest(data, tmp_path)
    assert any("escapes" in error for error in errors)
