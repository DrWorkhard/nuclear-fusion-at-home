from copy import deepcopy

import numpy as np
import pytest

from fusion_baselines.inequality_audit import audit_inequality_arm
from fusion_baselines.inequality_oracle import InequalityOracle


def fixture():
    oracle = InequalityOracle(
        lambda x: (np.r_[x[0] ** 2, np.full(137, x[0] - 1)], np.zeros((138, 1)), {}),
        256,
        1,
        137,
    )
    for point in [0.5, 2, 1]:
        oracle.evaluate([point])
    return {
        "evaluations": oracle.records,
        "counters": oracle.counters(),
        "best": oracle.best,
        "selection_tolerance": 1e-8,
        "gradient_screen_pass": True,
        "status": "solver_returned",
        "stop_reason": "solver_returned",
    }


def test_independent_selection_and_counters():
    arm = fixture()
    assert all(audit_inequality_arm(arm, [1], arm["best"]["values"]).values())


@pytest.mark.parametrize("corruption", ["best", "tolerance", "requests", "violation", "key"])
def test_detect_corrupt_ledger(corruption):
    arm = deepcopy(fixture())
    if corruption == "best":
        arm["best"]["attempt"] = 2
    elif corruption == "tolerance":
        arm["selection_tolerance"] = 0.01
    elif corruption == "requests":
        arm["counters"]["requests"] += 1
    elif corruption == "violation":
        arm["evaluations"][0]["maximum_violation"] = 0
    elif corruption == "key":
        arm["evaluations"][0]["selection_key"] = [0, 0, 0.25]
    assert not all(audit_inequality_arm(arm, [1], arm["best"]["values"]).values())
