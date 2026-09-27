"""Synthetic paired-box controls; no real fixtures, native fields or optimization."""

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
with pytest.MonkeyPatch.context() as patch:
    patch.syspath_prepend(str(ROOT/"scripts"))
    spec = importlib.util.spec_from_file_location(
        "explore_coherent_coils", ROOT/"scripts/explore_coherent_coils.py")
    experiment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(experiment)


@pytest.fixture
def clock(monkeypatch):
    now = [0.]
    monkeypatch.setattr(experiment.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(experiment.shutil, "disk_usage", lambda _: SimpleNamespace(free=8*1024**3))
    return now


def test_named_coherent_box_changes_exactly_ninety_low_coefficients_and_restores():
    previous = experiment.previous
    low = [33*i+11*axis+k for i in range(6) for axis in range(3) for k in range(5)]
    high = np.setdiff1d(np.arange(198), low)
    for arm in experiment.ARMS:
        with experiment.configuration(arm) as widths:
            assert previous.BUNDLES == 600
            np.testing.assert_array_equal(widths[high], .02)
            np.testing.assert_array_equal(widths[low], .08 if arm == "coherent" else .02)
            original = np.arange(198)*.001
            expanded = previous.expand(original+widths, original, previous.active_indices("full"))
            np.testing.assert_array_equal(expanded, original+widths)
            with pytest.raises(ValueError, match="box"):
                previous.expand(expanded+1e-10, original, previous.active_indices("full"))
        assert previous.BOX == .02 and previous.BUNDLES == 240
    with pytest.raises(RuntimeError), experiment.configuration("coherent"):
        raise RuntimeError("synthetic interrupted search")
    assert previous.BOX == .02 and previous.BUNDLES == 240
    with pytest.raises(ValueError):
        experiment.half_widths("other")


def test_nested_override_is_rejected_and_solver_adapter_changes_only_two_options():
    with experiment.configuration("control"):
        with pytest.raises(ValueError, match="nested"):
            with experiment.configuration("coherent"):
                pass
    minimize, initial = Mock(return_value="answer"), np.zeros(198)
    options = dict(maxiter=230, maxfun=230, maxls=20, ftol=1e-12, gtol=1e-9)
    kwargs = dict(method="L-BFGS-B", jac=True, bounds=[(-.02, .02)]*198, options=options)
    assert experiment.solver_adapter(minimize)(sum, initial, **kwargs) == "answer"
    actual = minimize.call_args.kwargs
    assert actual == dict(kwargs, options=dict(options, maxiter=590, maxfun=590))
    assert options["maxfun"] == 230
    with pytest.raises(ValueError, match="settings"):
        experiment.solver_adapter(minimize)(sum, initial, **dict(kwargs, method="BFGS"))


def sources():
    from fusion_baselines.clear_coil_geometry_audit import parameter_names, physical_rows

    original = dict(schema_version=1, nfp=2, nbase=6, order=5, names=parameter_names(6, 5),
                    base_coefficients=np.zeros((6, 3, 11)).tolist(), physical=physical_rows(6),
                    target_flux=-.1, B2_scale=2., unit_flux=-.5, scale=.2, seed_unit_flux=-.5)
    for row in original["physical"]:
        row["current"] = 20000*(-1 if row["flip"] else 1)
    seed = copy.deepcopy(original)
    seed.update(unit_flux=-.4, scale=.25)
    seed["base_coefficients"][0][0][0] = .01
    for row in seed["physical"]:
        row["current"] = 25000*(-1 if row["flip"] else 1)
    metrics = dict(unit_flux=-.4, scale=.25, normal_rms=.15, flux_normalized_raw=.012,
                   flux_objective=.01125, geometry_penalty=.001, min_b=1.,
                   coil_distance=.15, surface_distance=.09)
    trial = dict(index=52, role="search", status="completed", deadline_met=True,
                 x=np.asarray(seed["base_coefficients"]).ravel().tolist(), metrics=metrics)
    return {
        experiment.SNAPSHOT: seed, experiment.TRIAL: trial, experiment.SEED: original,
        experiment.ADAPTIVE: dict(completed=True, sources_unchanged=True, arms=[dict(
            case="n6-shape-d100mm", mode="full", fine_selected=copy.deepcopy(trial),
            fine=[dict(checks_pass=True), dict(checks_pass=True)])]),
        experiment.GEOMETRY: dict(completed=True, sources_unchanged=True, rows=[dict(
            label="n6-shape-d100mm-full",
            snapshot=dict(sha256=experiment.INPUTS[experiment.SNAPSHOT]),
            levels=[dict(combined_scoped_pass=False), dict(combined_scoped_pass=True)])]),
        experiment.SELECTION: dict(frozen={"n6-shape-d100mm-full": 52}),
    }


def test_exact_trial_seed_and_adaptive_geometry_binding_without_mutation():
    source = sources()
    before = copy.deepcopy(source)
    seed, anchors = experiment.seed_inputs(source)
    assert source == before and seed is not source[experiment.SNAPSHOT]
    assert anchors == source[experiment.TRIAL]["metrics"]
    assert seed["scale"] == .25 and seed["physical"][0]["current"] == 25000


@pytest.mark.parametrize("fault", ["geometry", "trial", "names", "normalization", "selection"])
def test_stale_or_mismatched_source_fails_closed(fault):
    source = sources()
    if fault == "geometry":
        source[experiment.GEOMETRY]["rows"][0]["levels"][-1]["combined_scoped_pass"] = False
    if fault == "trial":
        source[experiment.TRIAL]["x"][0] += .001
    if fault == "names":
        source[experiment.SNAPSHOT]["names"][0] = "wrong physical parameter"
    if fault == "normalization":
        source[experiment.SEED]["B2_scale"] = 3.
    if fault == "selection":
        source[experiment.SELECTION]["frozen"]["n6-shape-d100mm-full"] = 53
    with pytest.raises(ValueError):
        experiment.seed_inputs(source)


class SyntheticModel:
    def __init__(self):
        self.x0, self.indices = np.zeros(198), np.arange(198)

    def set_x(self, x):
        self.x = np.asarray(x).copy()

    def evaluate(self, x):
        gradient = x.copy()
        gradient[0] += 1
        return float(1+x[0]+.5*x@x), gradient, dict(normal_rms=.4+x[0], scale=.2,
            sampled_geometry_limits_met=bool(x[0] >= -.05), current_limit_met=True)


def test_six_hundred_total_bundles_and_selection_use_new_box_not_old_defaults(tmp_path, clock):
    record, model = experiment.Recorder(tmp_path/"run", 900), SyntheticModel()

    def solver(function, initial, **kwargs):
        assert kwargs["options"]["maxfun"] == kwargs["options"]["maxiter"] == 590
        assert kwargs["bounds"][0] == (-.08, .08)
        assert kwargs["bounds"][5] == (-.02, .02)
        for offset in (-.07, -.03):
            candidate = initial.copy()
            candidate[0] = offset
            function(candidate)
        for _ in range(601):
            function(initial)

    with experiment.configuration("coherent"):
        result = experiment.previous.search(model, record, dict(scale=.2, normal_rms=.4),
                                             experiment.solver_adapter(solver))
    assert result["startup_pass"] and result["status"]["reason"] == "budget"
    assert result["bundles_attempted"] == result["bundles_completed"] == 600
    assert result["lowest_objective"]["index"] == 10
    assert result["fine_selected"]["index"] == 11 and model.x[0] == -.03
    assert not (record.output/"trial-600-attempt.json").exists()
    assert experiment.previous.BOX == .02 and experiment.previous.BUNDLES == 240


def writer_fault(monkeypatch, clock, fault):
    original, triggered = Path.open, [False]

    class Writer:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            result = self.stream.__exit__(*args)
            if fault == "slow-close":
                clock[0] = 901.
            return result

        def write(self, data):
            count = self.stream.write(data[:-1] if fault == "short" else data)
            if fault == "slow-write":
                clock[0] = 901.
            return count

    def open_file(path, mode="r", *args, **kwargs):
        stream = original(path, mode, *args, **kwargs)
        if path.name == "result.json.tmp" and mode == "xb" and not triggered[0]:
            triggered[0] = True
            return Writer(stream)
        return stream

    monkeypatch.setattr(Path, "open", open_file)


@pytest.mark.parametrize("fault", ["slow-write", "slow-close", "short", "expired"])
def test_late_or_partial_final_publication_is_never_success(tmp_path, clock, monkeypatch, fault):
    record = experiment.Recorder(tmp_path/"run", 900)
    clock[0] = 901. if fault == "expired" else 899.
    writer_fault(monkeypatch, clock, fault)
    report = dict(completed=True, physical_admission=False, elapsed_s=899.)
    assert experiment.publish(record, report, 0.) == 1
    result = json.loads((record.output/"result.json").read_text(encoding="utf-8"))
    assert not result["completed"] and "publication_error" in result
    assert (record.output/"late-publication.json").exists()
    if fault == "short":
        assert (record.output/"rejected-partial-result.json").exists()
    if fault in ("slow-write", "slow-close"):
        assert (record.output/"rejected-late-result.json").exists()
    assert record.storage[0] == sum(p.stat().st_size for p in record.output.iterdir())


def test_nested_outputs_share_cap_and_failed_prefixes_can_be_written(tmp_path, clock, monkeypatch):
    overall = experiment.Recorder(tmp_path/"run", 900)
    arm = experiment.Recorder(overall.output/"arm", 300, overall.storage)
    overall.save("inputs.json", b"12345")
    arm.save("trial.json", b"67890")
    assert overall.storage[0] == 10
    clock[0] = 301.
    arm.save("failure.json", b"failed")  # Diagnostic writes allowed; guard still fails.
    with pytest.raises(TimeoutError):
        arm.guard()
    monkeypatch.setattr(experiment.previous.common, "MAX_BYTES", 20)
    with pytest.raises(OSError, match="aggregate"):
        overall.save("result.json", b"new report")
    assert overall.storage[0] == 16


def test_progress_write_crossing_deadline_cannot_start_native_call(tmp_path, clock):
    record = experiment.Recorder(tmp_path/"run", 300)
    original, native = record.save, Mock()

    def save(name, value):
        original(name, value)
        clock[0] = 301.

    record.save = save
    with pytest.raises(TimeoutError):
        record.call("B", native)
    assert not native.called and record.counts["B"] == dict(attempted=1, completed=0)


def test_fresh_output_rejected_before_native_calls(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "scipy.optimize", SimpleNamespace(minimize=None))
    with pytest.raises(FileExistsError):
        experiment.run(tmp_path)
