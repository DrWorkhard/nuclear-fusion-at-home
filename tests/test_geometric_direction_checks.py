import numpy as np
import pytest

from fusion_baselines.geometric_direction_checks import EPS, direction_gate, trial_metrics


def example():
    jac, p = np.zeros((138, 207)), np.zeros(207)
    p[3], jac[0, 3] = 1, 2
    fd = np.array([[sign * eps * (jac @ p) for sign in (1, -1)] for eps in EPS])
    return jac, p, fd, np.zeros((2, 120))


def test_both_fixed_fd_steps_are_required():
    jac, p, fd, pairs = example()
    assert direction_gate(jac, p, fd, pairs)["all_pass"]
    fd[1, 0, 0] += 1e-13
    result = direction_gate(jac, p, fd, pairs)
    assert result["finite_differences"][0]["passed"]
    assert not result["finite_differences"][1]["passed"] and not result["all_pass"]


def test_pair_and_nonfinite_gate_rejection():
    jac, p, fd, pairs = example()
    pairs[1, 0] = 1e-6
    assert not direction_gate(jac, p, fd, pairs)["all_pass"]
    pairs[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        direction_gate(jac, p, fd, pairs)


def test_flux_improvement_does_not_override_geometry_or_admit_design():
    before, after, jac, step = np.ones(138), np.ones(138), np.zeros((138, 207)), np.zeros(207)
    after[0], after[1], jac[0, 3], step[3] = 0.8, -1e-7, -1, 0.1
    result = trial_metrics(before, jac, step, after)
    assert result["flux_improves"] and not result["construction_screen_pass"]
    assert not result["physical_admission"]
    assert result["actual_to_predicted_change"] == pytest.approx(2.0)
    assert trial_metrics(before, jac * 0, step, after)["actual_to_predicted_change"] is None
