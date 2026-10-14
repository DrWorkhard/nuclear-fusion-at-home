"""acceptance-v2 verdicts from saved run files; synthetic arrays only."""

import json

import numpy as np
import pytest

from fusion_baselines import acceptance_v2 as acceptance


def write_run(tmp_path, error, interior=(0.009, 0.009, 0.009), geometry="pass", spike=None):
    """A completed run whose boundary has constant |B.n|/|B| = error (optional spike)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    n = 16
    normals = np.zeros((n, n, 3))
    normals[..., 2] = 1.0 + np.arange(n*n).reshape(n, n)/(n*n)  # unequal area weights
    field = np.zeros((n*n, 3))
    field[:, 0], field[:, 2] = 1.0, error
    if spike is not None:
        field[0, 2] = spike
    field /= np.linalg.norm(field, axis=1, keepdims=True)
    stats = None
    for shift in acceptance.SHIFTS:
        np.savez(tmp_path/f"fine-{shift:.1f}.npz", normals=normals, B=field)
        stats = acceptance.boundary_errors(tmp_path/f"fine-{shift:.1f}.npz")
    metrics = dict(normal_rms=stats["area_rms"], flux_limit_met=True, current_limit_met=True)
    report = dict(completed=True, geometry=dict(status=geometry),
                  fine=[dict(shift=s, checks_pass=True, metrics=metrics)
                        for s in acceptance.SHIFTS],
                  interior=[dict(checks_pass=True, metrics=dict(vector_rms=v)) for v in interior])
    (tmp_path/"result.json").write_text(json.dumps(report), encoding="utf-8")
    return tmp_path


def test_frozen_v2_values_and_calibration_identity():
    assert acceptance.V2["boundary_mean_max"] == 0.0018
    assert acceptance.V2["boundary_max_max"] == 0.013
    assert acceptance.V2["interior_vector_rms_max"] == acceptance.V1["interior_vector_rms_max"]
    assert acceptance.V1["boundary_rms_max"] == 1e-4 and acceptance.V1["boundary_max_max"] == 1e-3
    assert acceptance.V2["calibration"]["passing"] == 820
    assert acceptance.V2["calibration"]["cases"] == 8058


def test_boundary_statistics_on_a_constant_error_with_one_spike(tmp_path):
    write_run(tmp_path, 0.001, spike=0.02)
    stats = acceptance.boundary_errors(tmp_path/"fine-0.0.npz")
    assert stats["max"] == pytest.approx(0.02/np.hypot(1, 0.02), rel=1e-9)
    assert 0.001 < stats["mean"] < 0.002 and stats["area_rms"] > stats["mean"]


@pytest.mark.parametrize("error, v2", [(0.0015, True), (0.0019, False)])
def test_v2_boundary_threshold_and_v1_reported_alongside(tmp_path, error, v2):
    verdict = acceptance.evaluate(write_run(tmp_path, error))
    assert verdict["boundary"][0]["mean"] == pytest.approx(error/np.hypot(1, error), rel=1e-12)
    assert verdict["v2"]["passed"] is v2
    assert verdict["v1"]["passed"] is False  # 1e-4 RMS is not met at these errors
    assert not verdict["physical_admission"] and not verdict["step4_pass"]


def test_maximum_and_interior_and_geometry_still_gate_v2(tmp_path):
    assert not acceptance.evaluate(write_run(tmp_path/"a", 0.001, spike=0.02))["v2"]["passed"]
    hot_interior = write_run(tmp_path/"b", 0.001, interior=(0.009, 0.011, 0.009))
    assert not acceptance.evaluate(hot_interior)["v2"]["passed"]
    assert not acceptance.evaluate(write_run(tmp_path/"c", 0.001, geometry="fail"))["v2"]["passed"]
    assert acceptance.evaluate(write_run(tmp_path/"d", 0.001))["v2"]["passed"]


def test_saved_arrays_must_reproduce_the_recorded_rms(tmp_path):
    run = write_run(tmp_path, 0.001)
    report = json.loads((run/"result.json").read_text(encoding="utf-8"))
    report["fine"][0]["metrics"]["normal_rms"] *= 1.01
    (run/"result.json").write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="reproduce the recorded"):
        acceptance.evaluate(run)
