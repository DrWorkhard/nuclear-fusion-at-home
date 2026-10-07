"""Analytic interval/sign and dimensional checks for the one-off desk screen."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('envelope',
    Path(__file__).resolve().parents[1]/'scripts/screen_reactor_envelope.py')
envelope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(envelope)


@pytest.mark.parametrize('plasma,coil,expected', [
    ([-1, -.1], [1, 2], 'excluded'), ([1, 2], [-2, -.1], 'excluded'),
    ([-1, 1], [1, 2], 'unresolved'), ([1, 2], [-1, 1], 'unresolved'),
    ([0, 1], [0, 1], 'clears-two-separation-checks'), ([-1, 0], [1, 2], 'unresolved')])
def test_only_an_upper_bound_failure_excludes(plasma, coil, expected):
    assert envelope.classify(plasma, coil) == expected


def test_critical_scale_solves_known_quadratic():
    assert envelope.critical_scale(2, 1, 6) == pytest.approx(4)


def test_current_area_units_and_homothetic_scaling():
    base = dict(current_A=-100000, plasma_distance_m=[.1, .2],
                coil_distance_m=[.3, .4], R00_m=1, normalized_boundary_rms=.002)
    row = envelope.scenario(base, 10, 5, 100, .05, 1.04)
    assert row['ampere_turns_A'] == 5000000
    assert row['winding_area_m2'] == .05
    assert row['outer_radius_m'] == pytest.approx((.05/3.141592653589793)**.5+.05)
    assert row['normalized_boundary_rms'] == .002
    assert row['existing_pilot_current_limit_met'] is False
    assert row['physical_admission'] is False
