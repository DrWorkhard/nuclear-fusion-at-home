"""Small synthetic current/field-orchestration tests, without native field calls."""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location(
    "explore_coil_starts", Path(__file__).resolve().parents[1]/"scripts/explore_coil_starts.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


@pytest.mark.parametrize("target, phi", [(0, 1), (1, 0), (1, 1e-13), (1, float("nan")),
                                         (float("inf"), 1)])
def test_degenerate_normalization_rejected(target, phi):
    with pytest.raises(ValueError):
        experiment.normalize(target, phi)


def test_fresh_scale_sign_and_crosscheck_normalization():
    assert experiment.normalize(-2, -1) == 2
    assert experiment.normalize(-2, 1) == -2
    assert experiment.error([[3, 0, 0]], [[2, 0, 0]]) == .5
    assert experiment.error([[.3, 0, 0]], [[.2, 0, 0]]) == pytest.approx(.1)
    with pytest.raises(ValueError):
        experiment.error([[float("nan"), 0, 0]], [[1, 0, 0]])


def test_source_seed_replay_checks_all_four_quantities():
    original = dict(unit_flux=-.01065067732193652, scale=2.9496646632221735,
                    JN=.039344660151591306, normal_rms=.2760512774968315)
    metrics = dict(original, flux_normalized_raw=original["JN"])
    assert all(row["passed"] for row in experiment.seed_replay(metrics, original).values())
    for key in ("unit_flux", "scale", "normal_rms", "flux_normalized_raw"):
        perturbed = dict(metrics)
        perturbed[key] *= 1.00001
        assert experiment.seed_replay(perturbed, original)[key]["passed"] is False


def test_fixed_schedule_and_fresh_output(tmp_path):
    assert experiment.SCHEDULE == ((64, 256, 0.), (128, 512, 0.), (128, 512, .5))
    assert list(experiment.CASES) == ["n6-circle-d100mm", "n6-shape-d100mm",
                                    "n6-shape-d140mm", "n6-shape-d180mm"]
    with pytest.raises(FileExistsError):
        experiment.run(tmp_path)


def test_screen_uses_fresh_current_then_freezes_it_and_blocks_fields(monkeypatch):
    from fusion_baselines import coupled_coil_audit

    samples, independent_sizes = [], []
    field_vector = np.array([3., 4., .5])

    class Field:
        def __init__(self, coils):
            self.amplitude = 1 if coils[0] == 128 else .8

        def set_points(self, points):
            self.points = points

        def A(self):
            samples.append(("A", len(self.points)))
            return np.tile([-self.amplitude, 0., 0.], (len(self.points), 1))

        def B(self):
            samples.append(("B", len(self.points)))
            return np.tile(field_vector, (len(self.points), 1))

    def coils(snapshot, nodes):
        positions = np.full((1, 4, 3), nodes, dtype=float)
        return [nodes], dict(positions=positions, tangents=positions,
                             currents=np.array([1e5])), dict(position=0., tangent=0.)

    def boundary(data, n, m, shift):
        assert shift in (False, True)
        return dict(points=np.ones((n, m, 3)), normal=np.broadcast_to([0., 0., 1.], (n, m, 3)))

    def independent(points, positions, tangents, currents):
        independent_sizes.append(len(points))
        scale = currents[0]/1e5
        amplitude = 1 if positions[0, 0, 0] == 128 else .8
        return (np.tile(scale*field_vector, (len(points), 1)),
                np.tile([-scale*amplitude, 0., 0.], (len(points), 1)))

    monkeypatch.setitem(sys.modules, "simsopt.field", SimpleNamespace(BiotSavart=Field))
    monkeypatch.setattr(experiment, "native_coils", coils)
    monkeypatch.setattr(coupled_coil_audit, "boundary", boundary)
    monkeypatch.setattr(coupled_coil_audit, "loop", lambda data, n: (
        np.ones((n, 3)), np.tile([1., 0., 0.], (n, 1))))
    monkeypatch.setattr(coupled_coil_audit, "filament_field_and_potential", independent)
    reference = dict(target_flux=-2., B2_scale=1., scale=999., unit_flux=999.)
    counts = {name: dict(attempted=0, completed=0) for name in ("B", "A", "independent")}
    coarse, coarse_arrays, scale = experiment.screen(
        {}, {}, reference, 16, 128, 0., None, lambda: None, counts)
    fine, fine_arrays, fine_scale = experiment.screen(
        {}, {}, reference, 32, 256, .5, scale, lambda: None, counts)
    assert coarse["checks_pass"] and fine["checks_pass"]
    assert scale == fine_scale == 2  # Old normalization reference's 999 is never reused.
    assert fine["metrics"]["base_current"] == 200000
    assert fine["metrics"]["flux_relative_error"] == pytest.approx(.2)
    assert fine["metrics"]["flux_limit_met"] is False
    assert coarse["metrics"]["normal_rms"] == pytest.approx(fine["metrics"]["normal_rms"])
    np.testing.assert_array_equal(coarse_arrays["currents"], fine_arrays["currents"])
    assert max(length for _, length in samples) == 128
    assert independent_sizes == [64]*4
    assert counts == dict(B=dict(attempted=10, completed=10), A=dict(attempted=3, completed=3),
                          independent=dict(attempted=4, completed=4))


@pytest.mark.parametrize("late", [False, True])
def test_failed_or_late_row_retained_without_completed_claim(tmp_path, monkeypatch, late):
    case, now = "synthetic", [0.]
    path = experiment.PREFIX+case+"/snapshot.json"
    source = {
        experiment.TARGET: {}, experiment.REFERENCE: dict(target_flux=-2., B2_scale=1.),
        experiment.AUDIT: {"geometry_pass": True,
                           "sets": [dict(case=dict(label=case), geometry_pass=True)]},
        path: dict(case=dict(label=case), sources={"reference": {"input": {"sha256": "target"}}}),
    }
    for name, value in source.items():
        file = tmp_path/name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(experiment, "ROOT", tmp_path)
    monkeypatch.setattr(experiment, "INPUTS", {name: "target" for name in source})
    monkeypatch.setattr(experiment, "CASES", {case: "target"})
    monkeypatch.setattr(experiment, "sha256_file", lambda _: "target")
    monkeypatch.setattr(experiment, "fingerprints", lambda: dict(synthetic="target"))
    monkeypatch.setattr(experiment, "git_state", lambda _: {})
    monkeypatch.setattr(experiment.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(experiment.shutil, "disk_usage", lambda _: SimpleNamespace(free=8*1024**3))

    def screen(*args):
        if late:
            now[0] = 181
        return dict(checks_pass=False), dict(B=np.ones((1, 3))), 1.

    monkeypatch.setattr(experiment, "screen", screen)
    output = tmp_path/"out"
    assert experiment.run(output) == 1
    result = json.loads((output/"result.json").read_text(encoding="utf-8"))
    assert result["completed"] is False and result["physical_admission"] is False
    assert result["sources_unchanged"] is True
    assert (output/(case+"-0-attempt.json")).is_file()
    assert (output/(case+"-0.json")).exists() is not late
