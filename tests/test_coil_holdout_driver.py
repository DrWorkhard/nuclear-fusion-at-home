import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "coil_holdout_driver", Path(__file__).resolve().parents[1] / "scripts/run_coil_holdouts.py"
)
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)


@pytest.mark.parametrize("name", ["holdout", "native"])
@pytest.mark.parametrize("passed", [True, False])
def test_completed_rejection_is_not_execution_failure(name, passed):
    record = dict(status="completed", candidates=[{}, {}], all_pass=passed)
    DRIVER.validate_phase(name, record, 0 if passed else 2)


@pytest.mark.parametrize(
    "change,code",
    [
        ({"status": "error"}, 2),
        ({"candidates": [{}]}, 0),
        ({"all_pass": False}, 0),
        ({"all_pass": True}, 2),
        ({"all_pass": 1}, 0),
        ({}, 1),
    ],
)
def test_false_completion_rejected(change, code):
    record = dict(status="completed", candidates=[{}, {}], all_pass=True)
    record.update(change)
    with pytest.raises(ValueError):
        DRIVER.validate_phase("holdout", record, code)


def test_all_curvature_levels_required_even_when_unresolved():
    record = dict(status="completed", fields=[dict(levels=[{}] * 7) for _ in range(3)])
    DRIVER.validate_phase("curvature", record, 0)
    record["fields"][2]["levels"].pop()
    with pytest.raises(ValueError):
        DRIVER.validate_phase("curvature", record, 0)


def test_clearance_requires_both_candidates():
    DRIVER.validate_phase("clearance", {"candidates": [{}, {}]}, 0)
    with pytest.raises(ValueError):
        DRIVER.validate_phase("clearance", {"candidates": [{}]}, 0)


def test_unknown_phase_rejected():
    with pytest.raises(ValueError):
        DRIVER.validate_phase("other", {}, 0)
