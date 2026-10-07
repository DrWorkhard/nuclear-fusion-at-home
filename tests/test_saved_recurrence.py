"""Known circle trajectories guard against interpreting sparse samples as islands."""
import runpy
from pathlib import Path

import numpy as np
import pytest

study = runpy.run_path(str(Path(__file__).resolve().parents[1]
                          /'scripts/diagnose_saved_recurrence.py'))


def test_regular_rational_circle_has_recurrence_and_large_sampling_gaps():
    rational, near, dense = study['controls']()
    assert rational['return_rms_m']['11'] < 1e-12
    assert rational['return_rms_m']['10'] > .1
    assert rational['prefix_gap_rad']['320'] == pytest.approx(2*np.pi/11)
    assert near['prefix_gap_rad']['320'] > .4
    assert dense['prefix_gap_rad']['320'] < .04


def test_recurrence_direction_is_measured_on_each_residue_class():
    theta = 2*np.pi*(-6/11+1e-5)*np.arange(320)
    rz = np.column_stack((1+.2*np.cos(theta), .2*np.sin(theta)))
    row = study['recurrence'](rz, np.array([1., 0.]))
    for group in row['residue_classes']:
        assert group['resolved_direction_changes'] == 0
        assert group['net_advance_rad'] > 0
        assert group['net_advance_rad'] == pytest.approx(group['total_variation_rad'], abs=1e-12)
