import numpy as np
import pytest

from fusion_baselines.budgeted_oracle import BudgetExhausted
from fusion_baselines.timed_oracle import TimedOracle


def test_deadline_also_blocks_cache_without_new_backend_call():
    now, calls = [0.0], []

    def backend(x):
        calls.append(x.copy())
        return x, np.eye(len(x))

    oracle = TimedOracle(backend, 100, 1, 2.0, clock=lambda: now[0])
    oracle.evaluate([1.0])
    now[0] = 1.9
    oracle.evaluate([1.0])
    now[0] = 2.0
    with pytest.raises(BudgetExhausted):
        oracle.evaluate([1.0])
    assert len(calls) == 1
    assert oracle.counters() == {
        "limit": 100,
        "attempts": 1,
        "requests": 3,
        "cache_hits": 1,
        "denied": 1,
        "failed_attempts": 0,
    }
    assert oracle.timing()["elapsed_to_stop_seconds"] == 2.0


def test_inflight_work_finishes_and_overrun_is_reported():
    now = [0.0]

    def backend(x):
        now[0] += 3.0
        return x, np.eye(len(x))

    oracle = TimedOracle(backend, 100, 1, 2.0, clock=lambda: now[0])
    oracle.evaluate([1.0])
    with pytest.raises(BudgetExhausted):
        oracle.evaluate([2.0])
    assert oracle.timing()["overrun_seconds"] == 1.0
    now[0] += 100.0  # final artifact writing does not change the recorded stop time
    assert oracle.timing()["elapsed_to_stop_seconds"] == 3.0
    assert oracle.counters()["attempts"] == 1


@pytest.mark.parametrize("seconds", [0, -1, np.nan, np.inf, True])
def test_invalid_deadline(seconds):
    with pytest.raises(ValueError):
        TimedOracle(None, 1, 1, seconds)
