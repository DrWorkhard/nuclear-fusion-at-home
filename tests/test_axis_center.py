"""A known periodic center and degenerate-field rejection qualify the new map."""
import runpy
from pathlib import Path

import numpy as np
import pytest

study = runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/diagnose_axis_center.py'))


class RotatingField:
    def set_points(self, xyz):
        self.xyz = xyz

    def B(self):
        x, y, z = self.xyz.T
        r = np.hypot(x, y)
        c, s = x/r, y/r
        br, bz = -.6*(z-.001)/r, .6*(r-.937)/r
        return np.column_stack((br*c-s, br*s+c, bz))


def test_periodic_center_is_recovered_from_displaced_initial_center():
    row = study['axis_estimate'](RotatingField(), [.934, 0.], lambda: None, 1e-10, 1e-12)
    assert row['center_RZ'] == pytest.approx([.937, .001], abs=1e-10)
    assert row['residual_m'] < 1e-10


def test_period_map_matches_analytic_rotation():
    points, _ = study['period_map'](RotatingField(), [.942, .001], lambda: None)
    phi = np.linspace(0, np.pi, 9)
    expected = np.column_stack((.937+.005*np.cos(.6*phi), .001+.005*np.sin(.6*phi)))
    assert np.max(abs(points-expected)) < 1e-10


def test_zero_toroidal_field_cannot_produce_an_axis():
    field = RotatingField()
    field.B = lambda: np.zeros((1, 3))
    with pytest.raises(ValueError, match='nondegenerate toroidal'):
        study['period_map'](field, [.934, 0.], lambda: None)
