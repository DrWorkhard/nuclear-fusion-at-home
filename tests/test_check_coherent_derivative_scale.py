"""Synthetic component derivatives and bounded diagnostic orchestration; no fields."""

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
        "check_coherent_derivative_scale", ROOT/"scripts/check_coherent_derivative_scale.py")
    experiment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(experiment)


@pytest.fixture
def clock(monkeypatch):
    now = [0.]
    monkeypatch.setattr(experiment.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(experiment.shutil, "disk_usage", lambda _: SimpleNamespace(free=8*1024**3))
    return now


class SyntheticModel:
    def __init__(self):
        self.x0, self.calls = np.zeros(198), 0
        names = experiment.paired.previous.common.names()
        self.curves = [SimpleNamespace(index=i, local_full_dof_names=names,
                                      local_dof_names=names) for i in range(6)]
        self.geometry = SimpleNamespace(dJ=self.geometry_derivative)

    def geometry_derivative(self, partials):
        assert partials is True
        return lambda curve: self.geometry_gradient.reshape(6, 33)[curve.index]

    def evaluate(self, x):
        self.calls += 1
        flux = .2+x[0]+.5*x[1]**2
        geometry = .1+3*x[2]+.5*x[2]**2+1000*x[3]**3
        flux_gradient = np.zeros(198)
        flux_gradient[:2] = [1., x[1]]
        self.geometry_gradient = np.zeros(198)
        self.geometry_gradient[2:4] = [3+x[2], 3000*x[3]**2]
        metrics = dict(flux_objective=float(flux), geometry_penalty=float(geometry),
                       scale=.2, normal_rms=.15)
        return float(flux+geometry), flux_gradient+self.geometry_gradient, metrics


def test_thirty_exact_bundles_components_directions_and_repeat(tmp_path, clock):
    model, record = SyntheticModel(), experiment.Recorder(tmp_path/"run", 180)
    result = experiment.diagnose(model, record, dict(scale=.2, normal_rms=.15))
    assert result["completed"] and result["exact_repeat"]
    assert model.calls == result["bundles_attempted"] == result["bundles_completed"] == 30
    assert len(result["comparisons"]) == 14
    assert result["counts"]["component_geometry_dJ"] == dict(attempted=30, completed=30)
    assert not result["search_authorized"] and not result["derivative_policy_changed"]
    assert not result["physical_admission"]
    for label in ("sin", "cos"):
        rows = [r for r in result["comparisons"] if r["direction"] == label]
        assert [r["h"] for r in rows] == list(experiment.STEPS)
        direction = np.asarray(rows[0]["vector"])
        assert np.linalg.norm(direction) == pytest.approx(1.)
        for row in rows:
            assert row["components"]["flux"]["analytic"] == pytest.approx(direction[0])
            assert row["components"]["geometry"]["analytic"] == pytest.approx(3*direction[2])
            assert row["components"]["total"]["analytic"] == pytest.approx(
                direction[0]+3*direction[2])
    first = json.loads((record.output/"trial-00.json").read_text(encoding="utf-8"))
    last = json.loads((record.output/"trial-29.json").read_text(encoding="utf-8"))
    assert first["role"] == "seed" and last["role"] == "repeat"
    assert first["gradients"] == last["gradients"]
    assert len(first["gradients"]["geometry"]) == 198
    assert (record.output/"trial-29-attempt.json").exists()
    assert not (record.output/"trial-30-attempt.json").exists()


def test_component_formula_threshold_or_and_zero_safe_convergence_ratio():
    seed = dict(gradients=dict(total=[1.], flux=[.01], geometry=[0.]))
    plus = dict(values=dict(total=1.00005, flux=.01000009, geometry=0.))
    minus = dict(values=dict(total=-1.00005, flux=-.01000009, geometry=0.))
    direction = np.ones(1)
    first = experiment.component_comparison(seed, plus, minus, direction, 1.)
    assert first["total"]["threshold_met"]  # Relative criterion only.
    assert first["total"]["error"] > 1e-7
    assert first["flux"]["threshold_met"]  # Absolute criterion.
    assert first["geometry"]["preceding_error_ratio"] is None
    second = experiment.component_comparison(seed, plus, minus, direction, 1., first)
    assert second["total"]["preceding_error_ratio"] == 1.
    assert second["geometry"]["preceding_error_ratio"] is None
    plus["values"]["flux"], minus["values"]["flux"] = .01001, -.01001
    assert not experiment.component_comparison(seed, plus, minus, direction, 1.)["flux"][
        "threshold_met"]


@pytest.mark.parametrize("h,large", [(1e-300, True), (0., False), (float("inf"), False)])
def test_nonfinite_derived_difference_cannot_pass_relative_threshold(h, large):
    seed = dict(gradients={key: [1.] for key in experiment.COMPONENTS})
    plus = dict(values={key: 1e300 if large else 1. for key in experiment.COMPONENTS})
    minus = dict(values={key: 0. for key in experiment.COMPONENTS})
    with pytest.raises(ValueError, match="finite"):
        experiment.component_comparison(seed, plus, minus, np.ones(1), h)


@pytest.mark.parametrize("fault", ["anchor", "repeat", "identity", "nonfinite", "late",
                                   "exception"])
def test_failed_prefixes_are_retained_without_completed_diagnostic(tmp_path, clock, fault):
    model, record = SyntheticModel(), experiment.Recorder(tmp_path/"run", 180)
    original = model.evaluate

    def evaluate(x):
        value, gradient, metrics = original(x)
        if fault == "anchor":
            metrics["scale"] = .3
        if fault == "repeat" and model.calls == 30:
            gradient[0] += 1e-12
        if fault == "identity":
            value += .1
        if fault == "nonfinite":
            model.geometry_gradient[0] = np.nan
        if fault == "late":
            clock[0] = 181.
        if fault == "exception":
            raise ValueError("synthetic model failure")
        return value, gradient, metrics

    model.evaluate = evaluate
    result = experiment.diagnose(model, record, dict(scale=.2))
    assert not result["completed"] and "error" in result
    assert not result["search_authorized"] and not result["derivative_policy_changed"]
    assert (record.output/"trial-00-attempt.json").exists()
    row = json.loads((record.output/"trial-00.json").read_text(encoding="utf-8"))
    if fault in ("identity", "nonfinite", "late", "exception"):
        assert row["status"] == "failed" and result["bundles_completed"] == 0
    if fault == "anchor":
        assert model.calls == 1
    if fault == "repeat":
        assert model.calls == 30 and not result["exact_repeat"]


def test_exact_cap_prevents_an_extra_bundle_and_native_dispatch(tmp_path, clock):
    model, record = SyntheticModel(), experiment.Recorder(tmp_path/"run", 180)
    record.bundles = 30
    result = experiment.diagnose(model, record, {})
    assert not result["completed"] and model.calls == 0
    assert result["bundles_attempted"] == 30 and result["bundles_completed"] == 0
    clock[0] = 181.
    native = Mock()
    with pytest.raises(TimeoutError):
        record.call("B", native)
    assert not native.called


def test_tighter_byte_cap_and_final_expiration_are_enforced(tmp_path, clock, monkeypatch):
    record = experiment.Recorder(tmp_path/"run", 180)
    monkeypatch.setattr(experiment, "MAX_BYTES", 10)
    record.save("prefix.json", b"12345")
    with pytest.raises(OSError, match="64 MiB"):
        record.save("extra.json", b"123456")
    monkeypatch.setattr(experiment, "MAX_BYTES", 64*1024**2)
    clock[0] = 181.
    report = dict(completed=True, search_authorized=False)
    assert experiment.paired.publish(record, report, 0.) == 1
    saved = json.loads((record.output/"result.json").read_text(encoding="utf-8"))
    assert not saved["completed"] and not saved["search_authorized"]


def test_fresh_output_rejected_before_native_model_construction(tmp_path):
    with pytest.raises(FileExistsError):
        experiment.run(tmp_path)
