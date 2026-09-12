import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1] / "scripts/run_natural_auglag_recovery.py"
spec = importlib.util.spec_from_file_location("al_recovery", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def valid():
    return dict(
        status="completed",
        all_pass=True,
        copied_solver_outputs=False,
        steps=[
            dict(name=name, status="passed")
            for name in ("fresh-vmecpp-w7x", "fresh-vmec852-w7x", "strict-six-test-integration")
        ],
    )


def test_running_prerequisite_waits_and_complete_can_proceed():
    assert not module.native_ready(dict(status="running"))
    assert module.native_ready(valid())


@pytest.mark.parametrize(
    "change",
    [dict(status="error"), dict(all_pass=False), dict(copied_solver_outputs=True), dict(steps=[])],
)
def test_failed_or_incomplete_native_prerequisite_never_starts_search(change):
    with pytest.raises(ValueError):
        module.native_ready({**valid(), **change})


def test_duplicate_native_phase_is_not_completion():
    record = valid()
    record["steps"].append(record["steps"][0].copy())
    with pytest.raises(ValueError):
        module.native_ready(record)


def test_failed_phase_is_not_hidden_by_global_success_flag():
    record = valid()
    record["steps"][0]["status"] = "failed"
    with pytest.raises(ValueError):
        module.native_ready(record)
