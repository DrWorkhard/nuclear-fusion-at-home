import numpy as np
import pytest

from fusion_baselines.budgeted_oracle import BudgetExhausted
from fusion_baselines.inequality_oracle import InequalityOracle, candidate_key


def backend(x):
    return np.array([x[0] ** 2, x[0] - 1]), np.array([[2 * x[0]], [1]]), {"x": x.tolist()}


def test_feasibility_first_then_objective_selection_and_exact_budget():
    oracle = InequalityOracle(backend, 4, 1, 1)
    for x in [0, 0.5, 2, 1]:
        oracle.evaluate([x])
    assert oracle.best["attempt"] == 4
    assert oracle.best["construction_screen_pass"]
    np.testing.assert_array_equal(oracle.best["x"], [1])
    values, _ = oracle.evaluate([1])
    values[:] = 999
    np.testing.assert_array_equal(oracle.evaluate([1])[0], [1, 0])
    with pytest.raises(BudgetExhausted):
        oracle.evaluate([3])
    assert oracle.counters() == dict(
        limit=4, attempts=4, requests=7, cache_hits=2, denied=1, failed_attempts=0
    )


def test_infeasible_selection_is_violation_then_objective_and_first_tie():
    assert candidate_key([100, -0.1], 1e-8) < candidate_key([1, -0.2], 1e-8)
    assert candidate_key([1, -0.1], 1e-8) < candidate_key([100, -0.1], 1e-8)
    oracle = InequalityOracle(lambda x: (np.array([1, -1]), np.zeros((2, 1)), {}), 2, 1, 1)
    oracle.evaluate([1])
    oracle.evaluate([2])
    assert oracle.best["attempt"] == 1
    assert candidate_key([1, -1e-8], 1e-8)[0] == 0
    assert candidate_key([1, -1.01e-8], 1e-8)[0] == 1


def test_failed_proposal_invalidates_last_state_cache_and_consumes_attempt():
    calls = []

    def stateful(x):
        calls.append(x[0])
        if x[0] == -1:
            raise ValueError("failure after state mutation")
        return backend(x)

    oracle = InequalityOracle(stateful, 3, 1, 1)
    oracle.evaluate([1])
    with pytest.raises(ValueError):
        oracle.evaluate([-1])
    oracle.evaluate([1])
    assert calls == [1, -1, 1]
    assert oracle.counters()["failed_attempts"] == 1
    assert oracle.counters()["cache_hits"] == 0


@pytest.mark.parametrize(
    "values,jac",
    [
        ([1], [[1]]),
        ([1, 2], [[1, 2], [1, 2]]),
        ([np.nan, 1], [[1], [1]]),
        ([1, 1], [[np.inf], [1]]),
    ],
)
def test_reject_malformed_bundle(values, jac):
    oracle = InequalityOracle(lambda x: (values, jac, {}), 1, 1, 1)
    with pytest.raises(ValueError):
        oracle.evaluate([1])
    assert oracle.counters()["failed_attempts"] == 1
    assert oracle.best is None
