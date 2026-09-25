"""Dev-only release controls: no scientific packages or local artifacts required."""

import hashlib
from pathlib import Path
from unittest.mock import patch

from fusion_baselines.documentation import check_documentation
from fusion_baselines.operational_preservation import APPROVED, approved_change


def test_utf8_docs_and_python_under_cp1252_default(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name in ("README.md", "STATUS.md", "PROJECT_PLAN.md"):
        (docs / name).write_text('# A Unicode ” and → test\n', encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "unicode.py").write_text('"""Unicode ” and → source."""\n', encoding="utf-8")
    original = Path.read_text

    def windows_read(path, encoding=None, **kwargs):
        return original(path, encoding=encoding or "cp1252", **kwargs)

    with patch.object(Path, "read_text", windows_read):
        assert check_documentation(tmp_path) == []


def test_operational_exception_checks_both_versions_and_missing_file(tmp_path):
    path = "operational.sh"
    target = tmp_path / path
    target.write_bytes(b"reviewed replacement")
    old = b"original"
    pair = tuple(hashlib.sha256(raw).hexdigest() for raw in (old, target.read_bytes()))
    with patch.dict(APPROVED, {path: pair}), patch(
        "fusion_baselines.operational_preservation.subprocess.check_output", return_value=old
    ) as show:
        assert approved_change(tmp_path, "baseline", path)
        show.assert_called_with(["git", "show", f"baseline:{path}"], cwd=tmp_path)
        assert not approved_change(tmp_path, "baseline", "scientific.py")
        target.write_bytes(b"reviewed replacement ")
        assert not approved_change(tmp_path, "baseline", path)
        target.write_bytes(b"reviewed replacement")
        show.return_value = b"different original"
        assert not approved_change(tmp_path, "baseline", path)
        target.unlink()
        assert not approved_change(tmp_path, "baseline", path)


def test_reviewed_operational_replacements_have_exact_hashes():
    root = Path(__file__).resolve().parents[1]
    assert set(APPROVED) == {"scripts/run_core_ci.sh", "src/fusion_baselines/documentation.py"}
    for path, (_, expected) in APPROVED.items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected


def test_operational_exception_refuses_symlink_before_reading(tmp_path):
    with patch.object(Path, "is_symlink", return_value=True), patch(
        "fusion_baselines.operational_preservation.subprocess.check_output"
    ) as show:
        assert not approved_change(tmp_path, "baseline", "scripts/run_core_ci.sh")
        show.assert_not_called()


def test_roadmap_names_statuses_and_readme_order():
    root = Path(__file__).resolve().parents[1]
    tables = {}
    for name in ("README.md", "docs/README.md", "docs/STATUS.md", "docs/PROJECT_PLAN.md"):
        content = (root / name).read_text(encoding="utf-8")
        rows = []
        for line in content.splitlines():
            cells = [cell.strip().replace("**", "") for cell in line.split("|")]
            if len(cells) >= 5 and cells[1].startswith(("1.", "2.", "3.", "4.",
                                                      "5.", "MS1.", "MSX.")):
                rows.append((cells[1], cells[3]))
        tables[name] = rows
    # D-026: the roadmap table lives only in the front page and the roadmap.
    assert len(tables["README.md"]) == 7
    assert tables["README.md"] == tables["docs/PROJECT_PLAN.md"]
    assert tables["docs/README.md"] == tables["docs/STATUS.md"] == []
    assert tables["README.md"][3] == ("4. Develop plasma and coils together", "In progress")
    content = (root / "README.md").read_text(encoding="utf-8")
    headings = [line for line in content.splitlines() if line.startswith("## ")]
    index = headings.index("## Project plan and progress")
    assert headings[index + 1] == "## Start in three commands"
