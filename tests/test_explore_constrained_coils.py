"""Synthetic constrained-search tests; no native fields or real fixture evaluations."""

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
with pytest.MonkeyPatch.context() as patch:
    patch.syspath_prepend(str(ROOT/"scripts"))
    spec = importlib.util.spec_from_file_location(
        "explore_constrained_coils", ROOT/"scripts/explore_constrained_coils.py")
    experiment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(experiment)

ANCHORS = dict(unit_flux=-.5, scale=.2, normal_rms=.4, flux_normalized_raw=.03)


@pytest.fixture
def clock(monkeypatch):
    now = [0.]
    monkeypatch.setattr(experiment.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(experiment.common.shutil, "disk_usage",
                        lambda _: SimpleNamespace(free=8*1024**3))
    return now


def test_named_modes_and_unchanged_geometry_gates():
    assert len(experiment.active_indices("full")) == 198
    low = experiment.active_indices("low2")
    np.testing.assert_array_equal(low, [33*i+11*axis+k for i in range(6)
                                       for axis in range(3) for k in range(5)])
    assert len(low) == 90
    assert experiment.Model.geometry_metrics is experiment.common.Model.geometry_metrics
    with pytest.raises(ValueError):
        experiment.active_indices("other")


def test_reduced_mapping_box_and_immutable_high_modes():
    model = experiment.Model.__new__(experiment.Model)
    model.indices, model.x0 = experiment.active_indices("low2"), np.arange(198)*.001
    model.curves = [SimpleNamespace(local_full_dof_names=experiment.common.names())
                    for _ in range(6)]
    values = model.x0[model.indices]+.02
    full = experiment.expand(values, model.x0, model.indices)
    model.set_x(full)
    np.testing.assert_array_equal(np.concatenate([c.local_full_x for c in model.curves]), full)
    fixed = np.setdiff1d(np.arange(198), model.indices)
    np.testing.assert_array_equal(full[fixed], model.x0[fixed])
    full[fixed[0]] += 1e-12
    with pytest.raises(ValueError, match="inactive"):
        model.set_x(full)
    with pytest.raises(ValueError, match="box"):
        experiment.expand(values+1e-12, model.x0, model.indices)


def geometry(case):
    from fusion_baselines.clear_coil_geometry_audit import cases, parameter_names, physical_rows

    return dict(schema_version=1, kind="geometry-only", nfp=2, nbase=6, order=5,
                names=parameter_names(6, 5), base_coefficients=np.zeros((6, 3, 11)).tolist(),
                physical=physical_rows(6), case=next(r for r in cases() if r["label"] == case),
                parameter_orientation="alpha=-2*pi*t", sources={"selected": {}, "reference": {
                    "input": {"sha256": experiment.INPUTS[experiment.common.INPUT]}}})


def test_magnetic_seeds_use_case_specific_normalization_without_mutation():
    norm = dict(target_flux=-.1, B2_scale=2.)
    rows = []
    for case, phi in zip(experiment.CASES, (-.5, -.2), strict=True):
        scale = norm["target_flux"]/phi
        rows.append(dict(case=case, n=64, nodes=256, shift=0., checks_pass=True,
                         metrics=dict(ANCHORS, unit_flux=phi, scale=scale, base_current=1e5*scale)))
    report = dict(completed=True, sources_unchanged=True, rows=rows, normalization=norm)
    seeds = []
    for case in experiment.CASES:
        source = geometry(case)
        before = copy.deepcopy(source)
        seed, anchors = experiment.magnetic_seed(source, report, case)
        assert source == before and anchors["scale"] == seed["scale"]
        assert seed["physical"][0]["current"] == 1e5*seed["scale"]
        assert seed["physical"][6]["current"] == -1e5*seed["scale"]
        seeds.append(seed)
    assert seeds[0]["scale"] != seeds[1]["scale"]
    report["rows"][0]["metrics"]["base_current"] += 1
    with pytest.raises(ValueError, match="current"):
        experiment.magnetic_seed(geometry(experiment.CASES[0]), report, experiment.CASES[0])


class SyntheticModel:
    def __init__(self, mode="low2"):
        self.x0, self.indices = np.zeros(198), experiment.active_indices(mode)
        self.calls = 0

    def set_x(self, x):
        self.x = np.asarray(x).copy()

    def evaluate(self, x):
        self.calls += 1
        self.set_x(x)
        gradient = x.copy()
        gradient[0] += 1
        return float(1+x[0]+.5*x@x), gradient, dict(
            ANCHORS, normal_rms=.4+x[0], sampled_geometry_limits_met=bool(x[0] >= -.01),
            current_limit_met=True)


@pytest.mark.parametrize("mode", ["full", "low2"])
def test_objective_and_sampled_feasible_rms_have_distinct_selections(tmp_path, clock, mode):
    def solver(function, initial, **kwargs):
        assert len(initial) == (198 if mode == "full" else 90)
        for offset in (-.015, -.005):
            proposal = initial.copy()
            proposal[0] = offset
            function(proposal)
        return SimpleNamespace(success=False, message="bounded synthetic search")

    record, model = experiment.common.Recorder(tmp_path/"run", 1), SyntheticModel(mode)
    result = experiment.search(model, record, ANCHORS, solver)
    assert result["startup_pass"] and result["bundles_completed"] == 12
    assert result["lowest_objective"]["index"] == 10
    assert result["lowest_feasible_rms"]["index"] == result["fine_selected"]["index"] == 11
    assert result["fine_selection"] == "sampled-feasible"
    assert result["physical_admission"] is False
    assert model.x[0] == -.005
    assert all(r["passed"] for r in result["derivative_checks"])


def test_strict_240_bundle_cap_includes_startup(tmp_path, clock):
    def solver(function, initial, **kwargs):
        for _ in range(300):
            function(initial)
        pytest.fail("240 cap not enforced")

    model, record = SyntheticModel(), experiment.common.Recorder(tmp_path/"run", 1)
    result = experiment.search(model, record, ANCHORS, solver)
    assert result["startup_pass"] and result["status"]["reason"] == "budget"
    assert result["bundles_attempted"] == result["bundles_completed"] == model.calls == 240
    assert result["lowest_objective"]["index"] == 0  # Better FD probes are excluded.
    assert not (record.output/"trial-240-attempt.json").exists()


@pytest.mark.parametrize("failure", ["anchor", "gradient", "repeat", "late", "exception"])
def test_startup_failures_retain_trials_and_never_search(tmp_path, clock, failure):
    model, record = SyntheticModel(), experiment.common.Recorder(tmp_path/"run", 1)
    original = model.evaluate

    def evaluate(x):
        value, gradient, metrics = original(x)
        if failure == "anchor":
            metrics["scale"] += 1
        if failure == "gradient":
            gradient = -gradient
        if failure == "repeat" and model.calls == 10:
            value += .001
        if failure == "late":
            clock[0] = 2
        if failure == "exception":
            raise ValueError("synthetic native failure")
        return value, gradient, metrics

    model.evaluate = evaluate
    result = experiment.search(model, record, ANCHORS, lambda *_a, **_k: pytest.fail("search"))
    assert not result["startup_pass"]
    assert result["status"]["reason"] == ("budget" if failure == "late" else "failure")
    assert (record.output/"trial-000-attempt.json").exists()
    first = json.loads((record.output/"trial-000.json").read_text(encoding="utf-8"))
    assert len(first["x"]) == 198 and "native_after" in first
    if failure in ("late", "exception"):
        assert first["status"] == "failed" and result["fine_selected"] is None


def test_infeasible_seed_fallback_is_explicit(tmp_path, clock):
    model, record = SyntheticModel(), experiment.common.Recorder(tmp_path/"run", 1)
    original = model.evaluate

    def evaluate(x):
        value, gradient, metrics = original(x)
        metrics["current_limit_met"] = False
        return value, gradient, metrics

    model.evaluate = evaluate
    result = experiment.search(model, record, ANCHORS, lambda *_a, **_k: SimpleNamespace(
        success=True, message="no search points"))
    assert result["startup_pass"] and result["lowest_feasible_rms"] is None
    assert result["fine_selection"] == "seed-fallback" and result["fine_selected"]["index"] == 0


@pytest.mark.parametrize("mismatch", [False, True])
def test_fine_saves_full_loop_freezes_current_and_checks_independent_BA(
        tmp_path, clock, monkeypatch, mismatch):
    from fusion_baselines import coupled_coil_audit

    record = experiment.common.Recorder(tmp_path/"run", 1)
    record.counts["independent_BA"] = dict(attempted=0, completed=0)
    vectors, block_sizes = dict(B=np.array([3., 4., .5]), A=np.array([-.6, 0., 0.])), []

    class Field:
        def set_points(self, points):
            self.points = points

        def get(self, name):
            block_sizes.append(len(self.points))
            return record.call(name, lambda: np.tile(vectors[name], (len(self.points), 1)))

        def B(self):
            return self.get("B")

        def A(self):
            return self.get("A")

    class Model:
        def __init__(self, *args, **kwargs):
            assert kwargs == dict(n=128, ncoil=512, offset=.5)
            self.points = np.ones((16, 16, 3))
            self.normals = np.broadcast_to([0., 0., 1.], self.points.shape)
            self.field, self.loop_field = Field(), Field()
            self.loop_points = np.ones((512, 3))
            self.loop_tangent = np.tile([1., 0., 0.], (512, 1))

        def set_x(self, x):
            pass

        def geometry_metrics(self):
            return dict(sampled_geometry_limits_met=False, geometry_certified=False)

    monkeypatch.setattr(experiment, "Model", Model)
    monkeypatch.setattr(coupled_coil_audit, "physical_curves", lambda seed, nodes: dict(
        positions=np.ones((2, nodes, 3)), tangents=np.ones((2, nodes, 3)),
        currents=np.array([row["current"] for row in seed["physical"]])))
    monkeypatch.setattr(coupled_coil_audit, "filament_field_and_potential", lambda p, *_: (
        np.tile(2*vectors["B"]+(1 if mismatch else 0), (len(p), 1)),
        np.tile(2*vectors["A"], (len(p), 1))))
    seed = dict(target_flux=-1., physical=[dict(flip=False), dict(flip=True)])
    chosen = dict(index=11, x=np.zeros(198), metrics=dict(scale=2., unit_flux=-.5))
    if mismatch:
        with pytest.raises(ValueError, match="independent fine"):
            experiment.fine(seed, {}, experiment.active_indices("low2"), chosen, record, .5)
    else:
        experiment.fine(seed, {}, experiment.active_indices("low2"), chosen, record, .5)
    row = json.loads((record.output/"fine-0.5.json").read_text(encoding="utf-8"))
    assert row["checks_pass"] is not mismatch
    assert row["metrics"]["flux_relative_error"] == pytest.approx(.2)
    assert row["metrics"]["current"] == 200000
    assert max(block_sizes) == 128
    with np.load(record.output/"fine-0.5.npz", allow_pickle=False) as saved:
        assert saved["A"].shape == saved["loop_tangent"].shape == (512, 3)
        np.testing.assert_array_equal(saved["currents"], [200000, -200000])
        assert saved["independent_B"].shape == saved["independent_A"].shape == (64, 3)
