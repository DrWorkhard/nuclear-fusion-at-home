"""Synthetic checks and one native-circle cache regression; no real fixtures."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location(
    "explore_normalized_coils", Path(__file__).resolve().parents[1]
    / "scripts/explore_normalized_coils.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


@pytest.fixture
def clock(monkeypatch):
    now = [0.]
    monkeypatch.setattr(experiment.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(experiment.shutil, "disk_usage", lambda _: SimpleNamespace(free=8*1024**3))
    return now


def test_raw_chain_rule_and_current_basis_invariance():
    def evaluate(x, scale=1):
        q, phi = scale**2*(2+x*x), scale*(-3+x)
        return experiment.combine_flux("raw", q, np.array([scale**2*2*x]), 4, 5, -7,
                                       phi, np.array([scale]))
    value, gradient = evaluate(.2)
    h = 1e-5
    fd = (evaluate(.2+h)[0]-evaluate(.2-h)[0])/(2*h)
    assert gradient[0] == pytest.approx(fd, rel=1e-9)
    for scale in (0.1, 10, -3):
        scaled_value, scaled_gradient = evaluate(.2, scale)
        assert scaled_value == pytest.approx(value)
        np.testing.assert_allclose(scaled_gradient, gradient, rtol=1e-14)


def test_local_half_rms_squared_and_scale_independence():
    for phi in (-10., -.01, 5.):
        value, gradient = experiment.combine_flux(
            "local", .5*7*.3**2, np.array([2., 3.]), 7, 4, -2, phi, np.array([9., 8.]))
        assert value == pytest.approx(.5*.3**2)
        np.testing.assert_allclose(gradient, np.array([2., 3.])/7)


@pytest.mark.parametrize("q", [-1, 0, 1e-12, 1e-10, float("nan"), float("inf")])
@pytest.mark.parametrize("arm", ["raw", "local"])
def test_clipped_native_gradient_region_rejected(q, arm):
    with pytest.raises(ValueError):
        experiment.combine_flux(arm, q, np.ones(1), 1, 1, 1, 1, np.ones(1))


def test_named_mapping_handles_free_permutation_and_rejects_missing_coordinates():
    names = experiment.names()
    assert names[:3] == ["xc(0)", "xs(1)", "xc(1)"]
    assert names[11] == "yc(0)" and names[22] == "zc(0)" and len(set(names)) == 33
    curves = [SimpleNamespace(local_full_dof_names=names, local_dof_names=names[::-1])
              for _ in range(6)]
    result = experiment.canonical_gradient(curves, lambda _: np.arange(33)[::-1])
    np.testing.assert_array_equal(result, np.tile(np.arange(33), 6))
    curves[0].local_dof_names = names[:-1]
    with pytest.raises(ValueError, match="named"):
        experiment.canonical_gradient(curves, lambda _: np.arange(33))


class SyntheticModel:
    def __init__(self):
        self.x0 = np.zeros(198)
        self.linear = np.cos(np.arange(198)+1)
        self.calls, self.x = 0, self.x0.copy()

    def set_x(self, x):
        assert np.max(abs(x-self.x0)) <= .01
        self.x = np.asarray(x).copy()

    def evaluate(self, x):
        self.calls += 1
        self.set_x(x)
        return float(1+self.linear@x+.5*(x@x)), self.linear+x, dict(experiment.SEED_ANCHORS)


def seed_solver(function, x, **kwargs):
    function(x)
    return SimpleNamespace(success=True, message="synthetic")


def test_startup_counts_repeat_and_probe_exclusion(tmp_path, clock):
    model = SyntheticModel()
    record = experiment.Recorder(tmp_path/"run", 1)
    result = experiment.run_search(model, record, seed_solver)
    assert result["startup_pass"] and result["bundles_completed"] == 11
    assert all(row["passed"] for row in result["seed_replay"].values())
    assert result["selected"]["index"] == 0  # FD probes with lower values are ineligible.
    assert result["physical_admission"] is False
    assert len(list(record.output.glob("trial-*-attempt.json"))) == 11
    np.testing.assert_array_equal(model.x, model.x0)


def test_strict_80_total_cap_includes_ten_startup_bundles(tmp_path, clock):
    def greedy(function, x, **kwargs):
        for _ in range(100):
            function(x)
        pytest.fail("strict cap did not interrupt")

    record = experiment.Recorder(tmp_path/"run", 1)
    model = SyntheticModel()
    result = experiment.run_search(model, record, greedy)
    assert result["startup_pass"] and result["status"]["reason"] == "budget"
    assert result["bundles_completed"] == result["bundles_attempted"] == model.calls == 80
    assert not (record.output/"trial-080-attempt.json").exists()


@pytest.mark.parametrize("failure", ["gradient", "repeat", "anchor", "exception", "late"])
def test_failed_startup_never_starts_search_and_retains_prefix(tmp_path, clock, failure):
    model, record = SyntheticModel(), experiment.Recorder(tmp_path/"run", 1)
    original = model.evaluate

    def evaluate(x):
        value, gradient, metrics = original(x)
        if failure == "gradient":
            gradient = -gradient
        if failure == "repeat" and model.calls == 10:
            value += 1e-6
        if failure == "anchor":
            metrics["normal_rms"] *= 1.0001
        if failure == "exception":
            raise ValueError("synthetic failure")
        if failure == "late":
            clock[0] = 2
        return value, gradient, metrics

    model.evaluate = evaluate
    result = experiment.run_search(model, record, lambda *_args, **_kw: pytest.fail("search"))
    assert not result["startup_pass"]
    assert result["status"]["reason"] == ("budget" if failure == "late" else "failure")
    assert (record.output/"trial-000-attempt.json").is_file()
    if failure in ("exception", "late"):
        assert result["selected"] is None
    if failure == "late":
        assert json.loads((record.output/"trial-000.json").read_text())["deadline_met"] is False


def test_native_counts_failure_prefix_and_late_completion(tmp_path, clock):
    record = experiment.Recorder(tmp_path/"run", 1)

    def fail():
        raise ValueError("native error")

    with pytest.raises(ValueError):
        record.call("B", fail)
    assert record.counts["B"] == dict(attempted=1, completed=0)

    def late():
        clock[0] = 2
        return 42

    with pytest.raises(TimeoutError):
        record.call("A", late)
    assert record.counts["A"] == dict(attempted=1, completed=1)
    saved = json.loads((record.output/"progress.json").read_text())
    assert saved["native"] == record.counts


def test_shared_cap_counts_atomic_temporary_and_fresh_paths(tmp_path, clock, monkeypatch):
    shared = [0]
    left = experiment.Recorder(tmp_path/"left", 1, shared)
    right = experiment.Recorder(tmp_path/"right", 1, shared)
    monkeypatch.setattr(experiment, "MAX_BYTES", 10)
    left.save("a", b"1234")
    right.save("b", b"5678")
    assert shared == [8]
    with pytest.raises(OSError, match="output-byte"):
        left.save("a", b"123")  # Existing 4 + other 4 + temporary 3 exceeds 10.
    assert (left.output/"a").read_bytes() == b"1234"
    with pytest.raises(FileExistsError):
        experiment.Recorder(left.output, 1)


@pytest.mark.parametrize("mismatch", [False, True])
def test_fine_freezes_current_blocks_field_and_rejects_crosscheck(
        tmp_path, clock, monkeypatch, mismatch):
    from fusion_baselines import coupled_coil_audit, filament_field

    calls, snapshots = [], []
    field_value = np.array([1., 0., .1])
    record = experiment.Recorder(tmp_path/"run", 1)

    class Field:
        def set_points(self, points):
            self.points = points

        def B(self):
            calls.append(len(self.points))
            return record.call("B", lambda: np.tile(field_value, (len(self.points), 1)))

    class FineModel:
        def __init__(self, *args, **kwargs):
            assert kwargs == dict(ncoil=512, n=128, offset=.5)
            self.points = np.ones((20, 15, 3))
            self.normals = np.broadcast_to([0., 0., 1.], self.points.shape)
            self.field = Field()

        def set_x(self, x):
            pass

        def unit_flux(self):
            return -1.01  # Deliberately different from the coarse value.

        def geometry_metrics(self):
            return dict(sampled_geometry_limits_met=False, geometry_certified=False)

    def physical(snapshot, ncoil):
        snapshots.append(snapshot)
        assert ncoil == 512
        return dict(positions=None, tangents=None, currents=None)

    monkeypatch.setattr(experiment, "Model", FineModel)
    monkeypatch.setattr(coupled_coil_audit, "physical_curves", physical)
    monkeypatch.setattr(filament_field, "filament_field", lambda points, *_: np.tile(
        2*field_value+(1 if mismatch else 0), (len(points), 1)))
    seed = dict(target_flux=-2., physical=[dict(flip=False), dict(flip=True)])
    chosen = dict(index=7, x=np.zeros(198), metrics=dict(scale=2., unit_flux=-1.))
    if mismatch:
        with pytest.raises(ValueError, match="independent endpoint"):
            experiment.fine_endpoint(seed, {}, "local", chosen, record, .5)
    else:
        experiment.fine_endpoint(seed, {}, "local", chosen, record, .5)
    saved = json.loads((record.output/"fine-0.5.json").read_text())["metrics"]
    assert saved["independent_B_pass"] is not mismatch
    assert saved["current"] == 200000 and saved["flux_relative_error"] == pytest.approx(.01)
    assert saved["sampled_geometry_limits_met"] is False
    assert (record.output/"fine-0.5.npz").is_file()
    assert calls == [128, 128, 44]
    assert [row["current"] for row in snapshots[0]["physical"]] == [200000, -200000]


def test_module_load_has_no_native_field_symbols():
    assert "BiotSavart" not in experiment.__dict__
    assert "SquaredFlux" not in experiment.__dict__


def test_two_native_circle_fields_have_distinct_names_and_invalidate(tmp_path, clock):
    pytest.importorskip("simsopt")
    from simsopt.field import BiotSavart, Coil, Current
    from simsopt.geo import CurveXYZFourier

    curve = CurveXYZFourier(64, 1)
    curve.set("xc(1)", 1.)
    curve.set("ys(1)", 1.)
    coils = [Coil(curve, Current(1e5))]
    records = [experiment.Recorder(tmp_path/f"field-{i}", 1) for i in range(2)]
    fields = [experiment.tracked_field(BiotSavart, coils, record) for record in records]
    points = np.array([[.2, .1, .3], [-.3, .2, .4], [.1, -.2, -.5]])
    for field in fields:
        field.set_points(points)
    before = [[field.B().copy(), field.A().copy()] for field in fields]
    curve.set("xc(0)", .05)
    reference = BiotSavart(coils)
    reference.set_points(points)
    for i, field in enumerate(fields):
        for j, name in enumerate(("B", "A")):
            after, expected = getattr(field, name)(), getattr(reference, name)()
            assert not np.array_equal(after, before[i][j]), f"stale {name} for field {i}"
            np.testing.assert_allclose(after, expected, rtol=1e-12, atol=1e-14)
    assert fields[0].name != fields[1].name and fields[0] != fields[1]
    assert type(fields[0]) is type(fields[1])
    assert len({*fields, reference}) == 3
    curve.set("xc(0)", 0.)
    for i, field in enumerate(fields):
        np.testing.assert_allclose(field.B(), before[i][0], rtol=1e-12, atol=1e-14)
        np.testing.assert_allclose(field.A(), before[i][1], rtol=1e-12, atol=1e-14)
    assert all(record.counts["B"] == dict(attempted=3, completed=3) for record in records)
    assert all(record.counts["A"] == dict(attempted=3, completed=3) for record in records)
