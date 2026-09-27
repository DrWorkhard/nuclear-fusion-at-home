"""Dev-only release controls: no scientific packages or local artifacts required."""

from pathlib import Path
from unittest.mock import patch

import pytest

from fusion_baselines.documentation import check_documentation
from fusion_baselines.documentation_policy import (
    ROADMAP_NAMES,
    STATUS_ROW_LIMIT,
    WORD_LIMITS,
    check_overview_policy,
    overview_sizes,
    table_rows,
)


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


def test_roadmap_names_statuses_and_readme_order():
    root = Path(__file__).resolve().parents[1]
    tables = {}
    for name in ("README.md", "docs/README.md", "docs/STATUS.md", "docs/PROJECT_PLAN.md"):
        content = (root / name).read_text(encoding="utf-8")
        rows = []
        for line in content.splitlines():
            cells = [cell.strip().replace("**", "") for cell in line.split("|")]
            if len(cells) >= 5 and cells[1].startswith(("1.", "2.", "3.", "4.",
                                                      "5.", "MS0.", "MS1.", "MSX.")):
                rows.append((cells[1], cells[3]))
        tables[name] = rows
    # D-026: the roadmap table lives only in the front page and the roadmap.
    assert len(tables["README.md"]) == 8
    assert tables["README.md"] == tables["docs/PROJECT_PLAN.md"]
    assert tables["docs/README.md"] == tables["docs/STATUS.md"] == []
    assert tables["README.md"][3] == ("4. Develop plasma and coils together", "In progress")
    content = (root / "README.md").read_text(encoding="utf-8")
    headings = [line for line in content.splitlines() if line.startswith("## ")]
    index = headings.index("## Project plan and progress")
    assert headings[index + 1] == "## Start in three commands"


@pytest.fixture
def project(tmp_path):
    (tmp_path / "docs").mkdir()
    table = "| Step | Goal | Status |\n| --- | --- | --- |\n"
    table += "".join(f"| **{name}** | Requirement | Planned |\n" for name in ROADMAP_NAMES)
    for name in ("README.md", "docs/PROJECT_PLAN.md"):
        (tmp_path / name).write_text(table, encoding="utf-8")
    for name in ("docs/STATUS.md", "docs/README.md"):
        (tmp_path / name).write_text("# Overview\n", encoding="utf-8")
    return tmp_path


def test_real_overviews_fit_policy():
    assert check_overview_policy(Path(__file__).resolve().parents[1]) == []


def test_table_headers_rules_code_and_multiple_tables():
    text = """| Header | Value |
| :--- | ---: |
| A | 1 |

```text
| Skip | It |
| --- | --- |
| Wrong | 2 |
```
~~~text
| Skip | It |
| --- | --- |
| Wrong | 3 |
~~~
| Other | Value |
| --- | --- |
| **B** | 4 |
"""
    assert list(table_rows(text)) == [["A", "1"], ["B", "4"]]


@pytest.mark.parametrize("name", list(WORD_LIMITS))
def test_word_boundaries(project, name):
    path = project / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("word " * WORD_LIMITS[name], encoding="utf-8")
    assert overview_sizes(project)[name] == WORD_LIMITS[name]
    assert not any("word budget" in error for error in check_overview_policy(project))
    path.write_text("word " * (WORD_LIMITS[name] + 1), encoding="utf-8")
    assert any("word budget" in error for error in check_overview_policy(project))


def test_status_table_cap_counts_data_only(project):
    path = project / "docs/STATUS.md"
    table = "| Work | Evidence |\n| --- | --- |\n"
    path.write_text(table + "| Result | Measured |\n" * STATUS_ROW_LIMIT, encoding="utf-8")
    assert check_overview_policy(project) == []
    path.write_text(table + "| Result | Measured |\n" * (STATUS_ROW_LIMIT + 1), encoding="utf-8")
    assert any("row budget" in error for error in check_overview_policy(project))


@pytest.mark.parametrize("mutation", ["duplicate", "status", "name", "missing", "order", "columns"])
def test_roadmap_homes_and_consistency(project, mutation):
    path = project / "docs/PROJECT_PLAN.md"
    text = path.read_text(encoding="utf-8")
    if mutation == "duplicate":
        (project / "docs/STATUS.md").write_text(text, encoding="utf-8")
    elif mutation == "status":
        path.write_text(text.replace("Planned", "Complete", 1), encoding="utf-8")
    elif mutation == "name":
        path.write_text(text.replace("MS0.", "MS9."), encoding="utf-8")
    elif mutation == "missing":
        path.unlink()
    elif mutation == "order":
        lines = text.splitlines()
        lines[2], lines[3] = lines[3], lines[2]
        path.write_text("\n".join(lines), encoding="utf-8")
    else:
        path.write_text(text.replace(" | Requirement | Planned", ""), encoding="utf-8")
    assert check_overview_policy(project)


def test_utf8_and_no_native_imports(project):
    path = project / "docs/STATUS.md"
    path.write_text("# Scientific status — ‘reviewed’ → not accepted\n", encoding="utf-8")
    assert check_overview_policy(project) == []
