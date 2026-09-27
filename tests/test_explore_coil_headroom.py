"""Construction selection must not admit the old no-margin seed or change gates."""

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
with pytest.MonkeyPatch.context() as patch:
    patch.syspath_prepend(str(ROOT/"scripts"))
    spec = importlib.util.spec_from_file_location(
        "headroom", ROOT/"scripts/explore_coil_headroom.py")
    study = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(study)


def row(index, rms, length=3.44):
    return dict(index=index, status="completed", role="search", metrics=dict(
        lengths=[length]*6, normal_rms=rms, sampled_geometry_limits_met=True,
        current_limit_met=True))


def test_select_excludes_better_field_without_headroom_and_preserves_rows():
    rows = [row(0, .001, 3.499), row(1, .003), row(2, .002)]
    original = copy.deepcopy(rows)
    assert study.select(rows, 3) == rows[2]
    assert rows == original
    assert study.PENALTY_LENGTH < study.SELECT_LENGTH < 3.5


@pytest.mark.parametrize("key,value", [("role", "probe"), ("status", "failed"), ("index", 2)])
def test_select_excludes_probes_failures_and_uncommitted_deadline_rows(key, value):
    best, fallback = row(0, .001), row(1, .003)
    best[key] = value
    assert study.select([best, fallback], 2) == fallback


@pytest.mark.parametrize("flag", ["sampled_geometry_limits_met", "current_limit_met"])
def test_geometry_and_current_failures_remain_ineligible(flag):
    candidate = row(0, .001)
    candidate["metrics"][flag] = False
    with pytest.raises(ValueError, match="no completed candidate"):
        study.select([candidate], 1)


def test_no_margin_candidate_is_not_silently_replaced_by_seed():
    with pytest.raises(ValueError, match="no completed candidate"):
        study.select([row(0, .001, 3.451)], 1)


def test_tie_breaking_is_by_trial_not_file_order():
    a, b = row(12, .002), row(5, .002)
    assert study.select([a, b], 13) == b


def test_native_penalty_assembly_changes_only_the_length_target(monkeypatch):
    import numpy as np
    from simsopt.geo import CurveLength, CurveXYZFourier
    from simsopt.objectives import QuadraticPenalty

    curve = CurveXYZFourier(64, 1)
    curve.set("xc(1)", 3.48/(2*np.pi))
    curve.set("ys(1)", 3.48/(2*np.pi))
    length = CurveLength(curve)
    zero = QuadraticPenalty(length, 100, "max")

    def initialize(self, *args, **kwargs):
        self.curves, self.lengths = [curve]*6, [length]*6
        self.cc = self.cp = self.geometry = zero

    monkeypatch.setattr(study.restart.previous.Model, "__init__", initialize)
    model = study.Model()
    assert model.geometry.J() == pytest.approx(6*.5*(3.48-3.44)**2)
    gradient = model.geometry.dJ().copy()
    original = curve.get("xc(1)")
    curve.set("xc(1)", original+1e-6)
    right = model.geometry.J()
    curve.set("xc(1)", original-1e-6)
    left = model.geometry.J()
    curve.set("xc(1)", original)
    index = model.geometry.dof_names.index(curve.name+":xc(1)")
    assert (right-left)/2e-6 == pytest.approx(gradient[index], rel=1e-6)
