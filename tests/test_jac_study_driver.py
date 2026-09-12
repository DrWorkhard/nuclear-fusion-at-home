import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "jac_study_driver", Path(__file__).resolve().parents[1] / "scripts/run_jac_scaled_study.py"
)
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)
sys.path.pop(0)


def report():
    return dict(
        status="completed",
        all_four_phases_completed=True,
        used_for_optimizer_feedback=False,
        steps=[
            dict(name=name, status="completed")
            for name in ("holdout", "curvature", "clearance", "native")
        ],
    )


def test_complete_report_passes():
    DRIVER.require_closed(report())


@pytest.mark.parametrize("kind", ["running", "missing", "duplicate", "failed", "feedback"])
def test_unclosed_or_feedback_reports_rejected(kind):
    record = report()
    if kind == "running":
        record["status"] = "running"
    elif kind == "missing":
        record["steps"].pop()
    elif kind == "duplicate":
        record["steps"][1]["name"] = "holdout"
    elif kind == "failed":
        record["steps"][2]["status"] = "error"
    else:
        record["used_for_optimizer_feedback"] = True
    with pytest.raises(ValueError):
        DRIVER.require_closed(record)


def test_only_committed_unchanged_prerequisite_allowed(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    path = tmp_path / "record.json"
    path.write_text("original")
    subprocess.run(["git", "add", "record.json"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=tmp_path,
        check=True,
    )
    DRIVER.require_committed(tmp_path, path)
    path.write_text("changed")
    with pytest.raises(ValueError, match="committed unchanged"):
        DRIVER.require_committed(tmp_path, path)
