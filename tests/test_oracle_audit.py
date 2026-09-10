import copy

import numpy as np
import pytest

from fusion_baselines.budgeted_oracle import BudgetedOracle, BudgetExhausted
from fusion_baselines.oracle_audit import audit_ledger


def fixture():
    oracle = BudgetedOracle(lambda x: (x, np.eye(len(x))), 2, 1)
    oracle.evaluate([2.0])
    oracle.evaluate([1.0])
    oracle.evaluate([1.0])
    with pytest.raises(BudgetExhausted):
        oracle.evaluate([0.0])
    return {"evaluations": oracle.records, "counters": oracle.counters(),
            "best": oracle.best, "status": "budget_exhausted", "gradient_screen_pass": True,
            "coordinate_map": {"scale": 0.01, "oracle_records_physical_coordinates": True}}


def test_real_ledger_and_arrays():
    arm = fixture()
    assert all(audit_ledger(arm, np.array([1.0]), np.array([1.0]), 2).values())
    assert not all(audit_ledger(arm, np.array([1.1]), np.array([1.0]), 2).values())
    assert not all(audit_ledger(arm, np.array([1.0]), np.array([1.1]), 2).values())


@pytest.mark.parametrize("path,value", [
    (("counters", "requests"), 9), (("counters", "attempts"), 1),
    (("counters", "denied"), 0), (("counters", "limit"), 3),
    (("best", "attempt"), 1), (("best", "merit"), 0.0),
    (("gradient_screen_pass",), False), (("status",), "running"),
    (("coordinate_map", "scale"), 1.0),
    (("evaluations", 0, "attempt"), 7), (("evaluations", 0, "merit"), 9.0),
    (("evaluations", 0, "status"), "error"),
])
def test_corrupted_ledger_rejected(path, value):
    arm = copy.deepcopy(fixture())
    target = arm
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert not all(audit_ledger(arm, np.array([1.0]), np.array([1.0]), 2).values())


def test_empty_ledger_is_not_a_pass():
    arm = fixture()
    arm["evaluations"] = []
    with pytest.raises(ValueError, match="empty"):
        audit_ledger(arm, np.array([1.0]), np.array([1.0]), 2)
