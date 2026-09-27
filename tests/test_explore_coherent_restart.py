"""Synthetic absolute-box restart controls; no native fields or real optimization."""

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
with pytest.MonkeyPatch.context() as patch:
    patch.syspath_prepend(str(ROOT/"scripts"))
    spec = importlib.util.spec_from_file_location(
        "explore_coherent_restart", ROOT/"scripts/explore_coherent_restart.py")
    experiment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(experiment)


def start_and_bounds():
    center = np.arange(198)*.001
    lower, upper = experiment.bounds(center, "control")
    start = center.copy()
    start[0], start[5], start[6] = upper[0], lower[5], lower[6]+1e-6
    return center, start, lower, upper


def test_absolute_boxes_change_only_ninety_low_modes_without_recentering():
    center, start, lower, upper = start_and_bounds()
    wide_lower, wide_upper = experiment.bounds(center, "expanded-low")
    low = [33*i+11*a+k for i in range(6) for a in range(3) for k in range(5)]
    high = np.setdiff1d(np.arange(198), low)
    np.testing.assert_allclose((lower+upper)/2, center, atol=1e-16)
    np.testing.assert_allclose((wide_lower+wide_upper)/2, center, atol=1e-16)
    assert not np.array_equal(center, start)
    np.testing.assert_allclose((wide_upper-upper)[low], .04, atol=1e-16)
    np.testing.assert_array_equal(wide_upper[high], upper[high])
    np.testing.assert_array_equal(wide_lower[high], lower[high])


def test_shared_mask_and_all_central_probes_stay_in_both_boxes():
    center, start, lower, upper = start_and_bounds()
    free, directions = experiment.masked_directions(start, lower, upper)
    assert not free[[0, 5, 6]].any() and free.sum() == 195
    for vector in directions.values():
        np.testing.assert_array_equal(vector[~free], 0.)
        assert np.linalg.norm(vector) == pytest.approx(1.)
        for arm in experiment.ARMS:
            lo, hi = experiment.bounds(center, arm)
            for h in experiment.PROBE_STEPS:
                for sign in (-1, 1):
                    x = start+sign*h*vector
                    assert np.all(x >= lo) and np.all(x <= hi)
    with pytest.raises(ValueError, match="two free"):
        experiment.masked_directions(lower, lower, upper)
    with pytest.raises(ValueError, match="inside"):
        experiment.masked_directions(upper+1e-9, lower, upper)


def test_scoped_model_mapping_uses_absolute_bounds_and_restores_after_exception():
    _, start, lower, upper = start_and_bounds()
    old = experiment.previous.expand
    with pytest.raises(RuntimeError), experiment.absolute_box(start, lower, upper):
        # Moving inward from an old active upper bound is permitted; recentering is not.
        moved = start.copy()
        moved[0] -= .01
        np.testing.assert_array_equal(
            experiment.previous.expand(moved, start, np.arange(198)), moved)
        moved[0] = upper[0]+1e-9
        with pytest.raises(ValueError, match="absolute"):
            experiment.previous.expand(moved, start, np.arange(198))
        with pytest.raises(ValueError, match="absolute"):
            experiment.previous.expand(start, start+.001, np.arange(198))
        with pytest.raises(ValueError, match="nested"):
            with experiment.absolute_box(start, lower, upper):
                pass
        raise RuntimeError("synthetic interruption")
    assert experiment.previous.expand is old


class Recorder:
    def __init__(self):
        self.bundles, self.counts, self.saved = 0, {}, {}
        self.expired = False

    def guard(self):
        if self.expired:
            raise TimeoutError("synthetic late evaluation")

    def save(self, name, value):
        json.dumps(value, allow_nan=False)
        self.saved[name] = copy.deepcopy(value)


class Model:
    def __init__(self, start):
        self.x0, self.calls = start.copy(), 0

    def set_x(self, x):
        self.x = experiment.previous.expand(x, self.x0, np.arange(198))

    def evaluate(self, x):
        self.set_x(x)
        self.calls += 1
        delta = x-self.x0
        gradient = delta.copy()
        gradient[1] += 1
        return float(1+delta[1]+.5*delta@delta), gradient, dict(
            scale=.2, normal_rms=.4+delta[1], current_limit_met=True,
            sampled_geometry_limits_met=bool(delta[1] >= -.01))


def test_exact_startup_and_twelve_hundred_cap_keep_same_selection_and_probes():
    _, start, lower, upper = start_and_bounds()
    _, directions = experiment.masked_directions(start, lower, upper)
    record, model = Recorder(), Model(start)

    def solver(function, initial, **kwargs):
        assert record.bundles == 10
        assert kwargs["options"] == dict(maxiter=1190, maxfun=1190, maxls=20,
                                          ftol=1e-12, gtol=1e-9)
        np.testing.assert_array_equal(np.asarray(kwargs["bounds"])[:, 0], lower)
        for offset in (-.02, -.005):
            x = start.copy()
            x[1] += offset
            function(x)
        for _ in range(1201):
            function(initial)

    with experiment.absolute_box(start, lower, upper):
        result = experiment.search(model, record, dict(scale=.2, normal_rms=.4),
                                   lower, upper, directions, solver)
    assert result["startup_pass"] and result["status"]["reason"] == "budget"
    assert result["bundles_attempted"] == result["bundles_completed"] == model.calls == 1200
    assert result["lowest_objective"]["index"] == 10 and result["fine_selected"]["index"] == 11
    assert [r["h"] for r in result["derivative_checks"]] == list(experiment.PROBE_STEPS)*2
    assert "trial-1200-attempt.json" not in record.saved and len(record.saved) == 2400
    assert not result["physical_admission"]
    first_probe = np.asarray(record.saved["trial-0001.json"]["x"])
    np.testing.assert_array_equal(first_probe, start+experiment.PROBE_STEPS[0]*directions["sin"])


@pytest.mark.parametrize("fault", ["anchor", "repeat", "gradient", "late", "overflow"])
def test_startup_failures_retain_prefix_and_never_optimize(fault):
    _, start, lower, upper = start_and_bounds()
    _, directions = experiment.masked_directions(start, lower, upper)
    model, record, optimizer = Model(start), Recorder(), Mock()
    original = model.evaluate

    def evaluate(x):
        value, gradient, metrics = original(x)
        if fault == "anchor":
            metrics["scale"] = .3
        if fault == "repeat" and model.calls == 10:
            value += 1e-9
        if fault == "gradient":
            gradient[1] += 1.
        if fault == "late":
            record.expired = True
        if fault == "overflow":
            value = 1e308 if x[1] >= start[1] else 5e307
        return value, gradient, metrics

    model.evaluate = evaluate
    with experiment.absolute_box(start, lower, upper):
        result = experiment.search(model, record, dict(scale=.2), lower, upper,
                                   directions, optimizer)
    assert not optimizer.called and not result["startup_pass"] and record.saved
    if fault == "overflow":
        assert not result["derivative_checks"][-1]["finite"]
        assert result["derivative_checks"][-1]["fd"] is None
    if fault == "late":
        assert record.saved["trial-0000.json"]["status"] == "failed"
    assert experiment.previous.expand is experiment.ORIGINAL_EXPAND


def source_fixture(monkeypatch):
    from fusion_baselines.clear_coil_geometry_audit import parameter_names, physical_rows

    center, start, lower, upper = start_and_bounds()
    seed = dict(schema_version=1, nfp=2, nbase=6, order=5, names=parameter_names(6, 5),
                base_coefficients=start.reshape(6, 3, 11).tolist(), physical=physical_rows(6),
                target_flux=-.1, B2_scale=2., scale=.25, unit_flux=-.4, seed_unit_flux=-.5)
    for row in seed["physical"]:
        row["current"] = 25000*(-1 if row["flip"] else 1)
    center_seed = dict(seed, base_coefficients=center.reshape(6, 3, 11).tolist())
    monkeypatch.setattr(experiment.paired, "seed_inputs", lambda source: (center_seed, {}))
    metrics = dict(unit_flux=-.4, scale=.25, current=25000., normal_rms=.015,
                   flux_normalized_raw=.001, flux_objective=.0001, geometry_penalty=.00001,
                   min_b=1., coil_distance=.075, surface_distance=.13)
    trial = dict(index=598, role="search", status="completed", deadline_met=True,
                 x=start.tolist(), metrics=metrics)
    return {
        experiment.SNAPSHOT: seed, experiment.TRIAL: trial,
        experiment.RESULT: dict(completed=True, sources_unchanged=True, arms=[dict(
            arm="coherent", fine_selected=copy.deepcopy(trial), startup_pass=True,
            fine=[dict(checks_pass=True)]*2, active_names=seed["names"],
            lower_bounds=lower.tolist(), upper_bounds=upper.tolist())]),
        experiment.GEOMETRY: dict(completed=True, sources_unchanged=True,
            source=dict(sha256=experiment.INPUTS[experiment.RESULT]), rows=[dict(
                label="coherent", eligible=True, snapshot=dict(sha256=experiment.INPUTS[
                    experiment.SNAPSHOT]), levels=[dict(combined_scoped_pass=True)])]),
    }, center


def test_exact_source_binding_and_nine_original_anchors(monkeypatch):
    source, expected_center = source_fixture(monkeypatch)
    before = copy.deepcopy(source)
    seed, center, anchors = experiment.seed_inputs(source)
    np.testing.assert_array_equal(center, expected_center)
    assert len(anchors) == 9 and source == before
    assert seed == source[experiment.SNAPSHOT] and seed is not source[experiment.SNAPSHOT]


@pytest.mark.parametrize("fault", ["center", "geometry", "current", "names", "trial", "source"])
def test_mismatched_seed_geometry_current_and_recentered_box_rejected(monkeypatch, fault):
    source, _ = source_fixture(monkeypatch)
    if fault == "center":
        source[experiment.RESULT]["arms"][0]["lower_bounds"][0] += .001
    if fault == "geometry":
        source[experiment.GEOMETRY]["rows"][0]["levels"][0]["combined_scoped_pass"] = False
    if fault == "current":
        source[experiment.SNAPSHOT]["physical"][0]["current"] += 1
    if fault == "names":
        source[experiment.SNAPSHOT]["names"][0] = "invalid physical name"
    if fault == "trial":
        source[experiment.TRIAL]["x"][0] += .001
    if fault == "source":
        source[experiment.GEOMETRY]["source"]["sha256"] = "f"*64
    with pytest.raises(ValueError):
        experiment.seed_inputs(source)


def test_fresh_output_and_stale_hash_fail_before_native_work(tmp_path, monkeypatch):
    with pytest.raises(FileExistsError):
        experiment.run(tmp_path)
    monkeypatch.setattr(experiment, "ROOT", tmp_path)
    monkeypatch.setattr(experiment.shutil, "disk_usage", lambda _: SimpleNamespace(free=8*1024**3))
    (tmp_path/"source.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(experiment, "INPUTS", {"source.json": "0"*64})
    with pytest.raises(ValueError, match="identity"):
        experiment.run(tmp_path/"out")
    assert not (tmp_path/"out").exists()
