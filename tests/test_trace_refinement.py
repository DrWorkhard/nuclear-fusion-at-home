"""Chronological section pairing must not silently compare different transits."""
import runpy
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
study = runpy.run_path(str(ROOT/'scripts/diagnose_trace_refinement.py'))
controls = runpy.run_path(str(ROOT/'tests/test_axis_center.py'))


def test_period_map_composition_matches_analytic_rotation():
    field = controls['RotatingField']()
    point = np.array([.942, .001])
    for i in range(11):
        orbit, _ = study['axis'].period_map(field, point, lambda: None, 1e-11, 1e-13)
        point = orbit[-1]
        phi = (i+1)*np.pi
        assert point == pytest.approx([.937+.005*np.cos(.6*phi), .001+.005*np.sin(.6*phi)],
                                     abs=1e-10)


def test_saved_crossing_pairing_rejects_shifted_plane_order():
    hits = np.zeros((641, 5))
    hits[:, 0] = np.arange(641)
    hits[:, 1] = np.arange(641) % 2
    hits[:, 2] = 1
    points, planes = study['saved_crossings'](hits)
    assert len(points) == 640 and planes[0] == 1 and planes[-1] == 0
    hits[1, 1] = 0
    with pytest.raises(ValueError, match='chronological'):
        study['saved_crossings'](hits)
