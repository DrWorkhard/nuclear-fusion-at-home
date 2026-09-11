from pathlib import Path

import pytest

from fusion_baselines.documentation import check_documentation, local_links


@pytest.fixture
def project(tmp_path):
    docs = tmp_path / "docs"
    group = docs / "example"
    group.mkdir(parents=True)
    (docs / "README.md").write_text("[Example](example/README.md)\n")
    (docs / "STATUS.md").write_text("# Status\n")
    (docs / "PROJECT_PLAN.md").write_text("# Plan\n")
    (group / "README.md").write_text("[Result](RESULT.md)\n")
    (group / "RESULT.md").write_text("# Result\n")
    return tmp_path


def test_repository_documentation():
    assert check_documentation(Path(__file__).resolve().parents[1]) == []


def test_valid_structure_and_link_resolution(project):
    assert check_documentation(project) == []
    path = project / "docs" / "example" / "RESULT.md"
    path.write_text(
        "[back](../README.md#topic) [web](https://example.org) [section](#local)\n"
        "```\n[sample](absent.md)\n```\n"
    )
    assert local_links(path) == {(project / "docs" / "README.md").resolve()}
    assert check_documentation(project) == []


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("root_file", "root documents"),
        ("nested", "hierarchy too deep"),
        ("missing_index", "missing overview"),
        ("unindexed", "unindexed document"),
        ("broken", "broken local link"),
        ("stale_script", "stale script document path"),
        ("missing_root_link", "folder not in root overview"),
    ],
)
def test_reject_layout_regressions(project, mutation, expected):
    docs = project / "docs"
    group = docs / "example"
    if mutation == "root_file":
        (docs / "REPORT.md").write_text("# Wrong layer\n")
    elif mutation == "nested":
        (group / "nested").mkdir()
    elif mutation == "missing_index":
        (group / "README.md").unlink()
    elif mutation == "unindexed":
        (group / "UNLISTED.md").write_text("# Hidden result\n")
    elif mutation == "broken":
        (group / "RESULT.md").write_text("[missing](absent.md)\n")
    elif mutation == "stale_script":
        (project / "scripts").mkdir()
        (project / "scripts" / "run.py").write_text('protocol = "docs/OLD.md"\n')
    elif mutation == "missing_root_link":
        (docs / "README.md").write_text("# Overview without directory link\n")
    assert any(expected in error for error in check_documentation(project))
