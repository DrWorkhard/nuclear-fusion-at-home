"""Physical and failure controls for tracing actual coil fields for period actions."""

from types import SimpleNamespace

import numpy as np
import pytest

from fusion_baselines import coil_bounce as bounce


class HelicalField:
    def __init__(self, vertical=0.0):
        self.vertical = vertical

    def set_points(self, points):
        self.points = points

    def B(self):
        x, y, _ = self.points.T
        r2 = x*x+y*y
        return np.column_stack((-y/r2, x/r2, np.full(len(x), self.vertical)))


def trace_input():
    target = SimpleNamespace(rz=lambda s, theta, phi: (np.full(len(theta), 2.),
                                                      np.zeros(len(theta))))
    ideal = dict(phi=np.linspace(0, 2*np.pi, 801), alpha=np.arange(4.),
                 theta=np.zeros((801, 4)))
    return target, ideal


def test_actual_toroidal_field_has_analytic_length_and_magnitude():
    target, ideal = trace_input()
    result = bounce.trace_coils(HelicalField(), target, 0.5, ideal)
    assert result["B"] == pytest.approx(np.full((801, 4), 0.5), abs=1e-12)
    assert result["length"] == pytest.approx(np.tile(2*ideal["phi"][:, None], (1, 4)),
                                              abs=1e-11)


def test_coil_trajectory_is_not_forced_onto_target_surface():
    target, ideal = trace_input()
    result = bounce.trace_coils(HelicalField(vertical=0.1), target, 0.5, ideal)
    assert result["xyz"][-1, :, 2] == pytest.approx(np.full(4, 0.4*2*np.pi), abs=1e-11)


def test_missing_wells_are_retained_without_aggregate_score():
    result = bounce.measure(dict(B=np.ones((801, 4)),
                                  length=np.tile(np.linspace(0, 10, 801)[:, None], (1, 4)),
                                  phi=np.linspace(0, 2*np.pi, 801), alpha=np.arange(4.)))
    assert result["score"] is None
    assert len(result["errors"]) == len(bounce.HOLD_PITCHES)


def test_deadline_interrupts_before_native_field_call():
    target, ideal = trace_input()

    def expired():
        raise TimeoutError("expired")

    with pytest.raises(TimeoutError):
        bounce.trace_coils(HelicalField(), target, 0.5, ideal, expired)
