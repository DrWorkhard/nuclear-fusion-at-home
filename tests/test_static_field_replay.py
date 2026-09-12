import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "static_field_replay",
    Path(__file__).resolve().parents[1] / "scripts/audit_upstream_reconstruction.py",
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_independent_component_replay_circle_axis():
    t = np.arange(200) * 2 * np.pi / 200
    pos = np.column_stack((2 * np.cos(t), 2 * np.sin(t), np.zeros_like(t)))[None]
    vel = 4 * np.pi * np.column_stack((-np.sin(t), np.cos(t), np.zeros_like(t)))[None]
    points = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    actual = AUDIT.replay_field(points, pos, vel, np.array([7.0]))
    expected = np.zeros((2, 3))
    expected[:, 2] = 4 * np.pi * 1e-7 * 7 * 4 / (2 * (4 + points[:, 2] ** 2) ** 1.5)
    np.testing.assert_allclose(actual, expected, rtol=1e-14, atol=1e-21)


def test_replay_rejects_singular_or_nonfinite_displacements():
    pos = np.zeros((1, 1, 3))
    vel = np.ones_like(pos)
    for point in ([0.0, 0.0, 0.0], [float("nan"), 1.0, 1.0]):
        with pytest.raises(ValueError):
            AUDIT.replay_field(np.array([point]), pos, vel, np.ones(1))
