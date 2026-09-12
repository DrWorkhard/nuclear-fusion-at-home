import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_slsqp_polish import initial_replay_check
from run_slsqp_polish import SelectedBackend

from fusion_baselines.direct_constraints import DirectConstraintBackend


def test_first_request_is_counted_and_guarded(monkeypatch):
    calls = []
    values = np.ones(138)

    def evaluate(self, x):
        calls.append(x.copy())
        return values.copy(), np.zeros((138, 207)), {}

    monkeypatch.setattr(DirectConstraintBackend, "evaluate", evaluate)
    backend = object.__new__(SelectedBackend)
    backend.reset_start_guard(np.zeros(207), values)
    with pytest.raises(ValueError, match="first counted"):
        backend.evaluate(np.ones(207))
    assert len(calls) == 0
    backend.evaluate(np.zeros(207))
    assert len(calls) == 1 and backend.start_verified
    assert backend.initial_replay_error == 0
    backend.reset_start_guard(np.zeros(207), values * 2)
    with pytest.raises(ValueError, match="replay"):
        backend.evaluate(np.zeros(207))
    assert len(calls) == 2 and not backend.start_verified


def test_independent_first_record_rejects_corruption():
    arm = dict(evaluations=[dict(values=np.ones(138).tolist())])
    assert initial_replay_check(arm, np.ones(138)) == (True, 0)
    arm["evaluations"][0]["values"][13] = 1.01
    assert not initial_replay_check(arm, np.ones(138))[0]
