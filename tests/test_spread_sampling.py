"""Frozen layout and area-weighted RMS have analytic structural checks."""

import runpy
from pathlib import Path

import pytest

study = runpy.run_path(str(Path(__file__).resolve().parents[1]
                          /'scripts/check_spread_sampling.py'))


def test_spread_layout_has_64_distinct_midpoints_without_mirror_pairs():
    selected = study['indices']()
    pairs = {divmod(index, 64) for index in selected}
    assert len(selected) == len(pairs) == 64
    assert {j for j, _ in pairs} == set(range(2, 32, 4))
    assert {i for _, i in pairs} == set(range(4, 64, 8))
    assert not any(j in (0, 32) for j, _ in pairs)
    assert not any(((-j) % 64, (-i) % 64) in pairs for j, i in pairs)


def test_weighted_rms_renormalizes_selected_areas_and_preserves_sign_invariance():
    metric = study['metric']
    assert metric([3., -4., 100.], [.2, .3, .5], [0, 1]) == pytest.approx(13.2**.5)
    assert metric([3., 4., 100.], [2., 3., 5.], [0, 1]) == pytest.approx(13.2**.5)
