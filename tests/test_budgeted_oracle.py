import numpy as np
import pytest

from fusion_baselines.budgeted_oracle import BudgetedOracle, BudgetExhausted, NamedVectorBackend


def _backend(x):
    return np.array([x @ x]), 2 * x[None, :]


def test_exact_cap_cache_and_defensive_copies():
    calls = []

    def backend(x):
        calls.append(x.copy())
        return _backend(x)

    oracle = BudgetedOracle(backend, 2, 2)
    x = np.array([1.0, 2.0])
    values, jac = oracle.evaluate(x)
    values[:] = -1
    jac[:] = -1
    assert oracle.evaluate(x)[0][0] == 5
    x[0] = 3
    oracle.evaluate(x)
    assert len(calls) == 2
    oracle.evaluate(x)  # cached point remains available after the cap
    with pytest.raises(BudgetExhausted):
        oracle.evaluate([1.0, 2.0])  # return to an older point is a new evaluation
    assert len(calls) == 2
    assert oracle.counters() == {
        "limit": 2,
        "attempts": 2,
        "requests": 5,
        "cache_hits": 2,
        "denied": 1,
        "failed_attempts": 0,
    }
    np.testing.assert_array_equal(oracle.best["x"], [1, 2])


def test_failed_attempts_are_charged_and_not_cached():
    oracle = BudgetedOracle(lambda x: (_ for _ in ()).throw(RuntimeError("bad physics")), 2, 1)
    for _ in range(2):
        with pytest.raises(RuntimeError, match="bad physics"):
            oracle.evaluate([1])
    with pytest.raises(BudgetExhausted):
        oracle.evaluate([1])
    assert oracle.counters()["failed_attempts"] == 2
    assert oracle.best is None


def test_invalid_proposals_and_backend_output():
    for x in [[np.nan], [1, 2]]:
        oracle = BudgetedOracle(_backend, 1, 1)
        with pytest.raises(ValueError):
            oracle.evaluate(x)
        assert oracle.counters()["attempts"] == 1
    for value, jac in [([np.nan], [[1]]), ([1], [[np.inf]]), ([1], [[1, 2]])]:
        oracle = BudgetedOracle(lambda x, a=value, b=jac: (a, b), 1, 1)
        with pytest.raises(ValueError):
            oracle.evaluate([1])
    for limit in [0, True, 1.5]:
        with pytest.raises(ValueError):
            BudgetedOracle(_backend, limit, 1)


def test_success_cache_is_invalidated_by_failed_proposal():
    oracle = BudgetedOracle(_backend, 3, 1)
    oracle.evaluate([1])
    with pytest.raises(ValueError):
        oracle.evaluate([np.nan])
    oracle.evaluate([1])
    assert oracle.counters()["attempts"] == 3


def test_gradient_columns_follow_names_not_position():
    class Global:
        dof_names = ["a", "b", "c"]
        x = np.array([0.0, 0.0, 0.0])

    root = Global()

    class Local:
        dof_names = ["c", "a"]

        @property
        def x(self):
            return root.x[[2, 0]]

        def J(self):
            return self.x @ [2.0, 3.0]

        def dJ(self):
            return np.array([2.0, 3.0])

    local = Local()
    backend = NamedVectorBackend(root, [local], [2])
    value, gradient = backend(np.array([1.0, 4.0, 5.0]))
    np.testing.assert_array_equal(value, [26])
    np.testing.assert_array_equal(gradient, [[6, 0, 4]])
    local.dof_names = ["z", "a"]
    with pytest.raises(ValueError, match="missing from global"):
        NamedVectorBackend(root, [local], [2])
