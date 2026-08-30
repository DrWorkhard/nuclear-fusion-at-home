from fusion_baselines.provenance import build_run_record, git_state


def test_git_state_for_project_checkout():
    state = git_state(__import__("pathlib").Path.cwd())
    assert state["available"] is True
    assert state["branch"] == "main"


def test_run_record_has_required_sections(tmp_path):
    record = build_run_record(__import__("pathlib").Path.cwd(), {"missing": tmp_path})
    assert record["schema_version"] == 1
    assert record["repository"]["available"] is True
    assert record["external_repositories"]["missing"]["available"] is False
