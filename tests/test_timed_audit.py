import copy

import numpy as np
import pytest

from fusion_baselines.budgeted_oracle import BudgetExhausted
from fusion_baselines.timed_audit import audit_common_prefix, audit_timed_arm
from fusion_baselines.timed_oracle import TimedOracle


def fixture(n=2):
    clock = [0.0]
    oracle = TimedOracle(lambda x: (x, np.eye(len(x))), 10, 1, 3.0, clock=lambda: clock[0])
    for i in range(n):
        oracle.evaluate(np.array([1.0 / (i + 1)]))
    clock[0] = 3.1
    with pytest.raises(BudgetExhausted):
        oracle.evaluate([5.0])
    return {
        "evaluations": oracle.records,
        "counters": oracle.counters(),
        "best": oracle.best,
        "status": "budget_exhausted",
        "gradient_screen_pass": True,
        "coordinate_map": {"scale": 0.01, "oracle_records_physical_coordinates": True},
        "timing": {**oracle.timing(), "early_return_end_to_end_upper_bound": False},
    }


def test_exact_deadline_ledger_and_unequal_counts_with_identical_prefix():
    first, second = fixture(), fixture(3)
    assert all(
        audit_timed_arm(
            first, first["best"]["x"], first["best"]["values"], seconds=3.0, safety_limit=10
        ).values()
    )
    result = audit_common_prefix(first, second)
    assert result["pass"] and result["common_prefix_length"] == 2 and result["counts"] == [2, 3]


@pytest.mark.parametrize(
    "key,value",
    [
        ("budget_seconds", 4.0),
        ("time_denials", 0),
        ("elapsed_to_stop_seconds", 2.0),
        ("overrun_seconds", 0.0),
        ("overrun_seconds", np.nan),
    ],
)
def test_bad_timing_rejected(key, value):
    arm = fixture()
    arm["timing"][key] = value
    assert not all(
        audit_timed_arm(
            arm, arm["best"]["x"], arm["best"]["values"], seconds=3.0, safety_limit=10
        ).values()
    )


def test_changed_prefix_empty_and_early_return_mismatch():
    first, second = fixture(), fixture(3)
    bad = copy.deepcopy(second)
    bad["evaluations"][0]["x_sha256"] = "wrong"
    assert not audit_common_prefix(first, bad)["pass"]
    bad = copy.deepcopy(second)
    bad["evaluations"][1]["values"] = [99.0]
    assert not audit_common_prefix(first, bad)["pass"]
    bad["evaluations"] = []
    assert not audit_common_prefix(first, bad)["pass"]
    first["status"] = second["status"] = "solver_returned"
    assert not audit_common_prefix(first, second)["pass"]
