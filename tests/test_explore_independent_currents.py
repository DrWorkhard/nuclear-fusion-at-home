"""Small exact convex controls and synthetic linear fields; no native field calls."""

import importlib.util
import json
import math
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
        "explore_independent_currents", ROOT/"scripts/explore_independent_currents.py")
    experiment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(experiment)


@pytest.mark.parametrize("active", [False, True])
def test_exact_convex_qp_solution_and_independent_certificate(active):
    diagonal = np.array([.01, 1, 1, 1, 1, 1]) if active else np.arange(1, 7, dtype=float)
    M, c = np.diag(diagonal), np.ones(6)/6
    expected = np.r_[5., np.full(5, .2)] if active else 6/diagonal**2/(1/diagonal**2).sum()
    analytic = experiment.kkt_certificate(M, c, expected)
    assert analytic["passed"]
    assert analytic["convex_lower_bound"] == pytest.approx(analytic["objective"], abs=1e-12)
    result = experiment.solve_qp(M, c, np.ones(6))
    assert result["solver_success"] and result["certificate"]["passed"]
    np.testing.assert_allclose(result["q"], expected, atol=1e-7)
    assert result["certificate"]["upper_active"] == ([0] if active else [])


def test_degenerate_multiplier_and_reversed_current_vertex():
    M, c, q = np.eye(6), np.array([.1, -.1, 0, 0, 0, 0]), np.array([5., -5., 0, 0, 0, 0])
    result = experiment.kkt_certificate(M, c, q)
    assert result["passed"]
    assert result["lower_active"] == [1] and result["upper_active"] == [0]
    assert result["equality_multiplier"] == pytest.approx(-50.)


def test_single_polish_preserves_active_set_and_recovers_exact_interior_point():
    M, c = np.diag(np.arange(1., 7)), np.ones(6)/6
    expected = 6/np.arange(1., 7)**2/(1/np.arange(1., 7)**2).sum()
    raw = expected+np.array([1e-5, -1e-5, 0, 0, 0, 0])
    before = raw.copy()
    certificate = experiment.kkt_certificate(M, c, raw)
    assert not certificate["passed"]
    polished = experiment.polish_active_set(M, c, raw, certificate)
    assert polished["selected"] and polished["same_active_set"]
    np.testing.assert_allclose(polished["q"], expected, rtol=1e-14, atol=1e-14)
    np.testing.assert_array_equal(raw, before)


def test_polish_rejects_changed_active_set_and_singular_system():
    M, c, raw = np.diag([.01, 1, 1, 1, 1, 1]), np.ones(6)/6, np.ones(6)
    polished = experiment.polish_active_set(M, c, raw, experiment.kkt_certificate(M, c, raw))
    assert not polished["selected"] and not polished["same_active_set"]
    assert polished["q"][0] > 5 and polished["certificate"]["errors"]["box"] > 0
    M = np.zeros((6, 6))
    singular = experiment.polish_active_set(M, c, raw, experiment.kkt_certificate(M, c, raw))
    assert not singular["selected"] and "singular" in singular["reason"]
    q, c = np.array([5., -5., 0, 0, 0, 0]), np.array([.1, -.1, 0, 0, 0, 0])
    unavailable = experiment.polish_active_set(np.eye(6), c, q,
                                               experiment.kkt_certificate(np.eye(6), c, q))
    assert not unavailable["selected"] and "free" in unavailable["reason"]


def test_rank_deficiency_needs_no_regularization():
    result = experiment.solve_qp(np.zeros((6, 6)), np.ones(6)/6, np.ones(6))
    assert result["certificate"]["passed"] and result["certificate"]["objective"] == 0
    np.testing.assert_array_equal(result["q"], np.ones(6))
    _, _, _, _, nullspace, conditioning = experiment.quadratic_system(
        np.zeros((1, 3, 6)), np.array([[1., 0, 0]]),
        np.ones((2, 3, 6)), np.ones((2, 3)), 1., 1.)
    assert conditioning["singular_values"] == [0.]*5
    assert conditioning["rank"] == 0 and conditioning["condition_number"] is None
    np.testing.assert_allclose(nullspace.T@nullspace, np.eye(5), atol=1e-14)


@pytest.mark.parametrize("q", [np.zeros(6), np.array([6., 0, 0, 0, 0, 0]), np.ones(6)])
def test_infeasible_or_nonstationary_candidate_fails(q):
    assert not experiment.kkt_certificate(np.diag(np.arange(1., 7)), np.ones(6)/6, q)["passed"]


def test_supporting_plane_bound_is_below_exact_optimum_for_nonoptimal_controls():
    diagonal = np.arange(1., 7)
    expected = 6/diagonal**2/(1/diagonal**2).sum()
    optimum = .5*np.linalg.norm(diagonal*expected)**2
    rng = np.random.default_rng(2026)
    for _ in range(12):
        q = rng.uniform(-1, 1, 6)
        q += 1-q.mean()
        result = experiment.kkt_certificate(np.diag(diagonal), np.ones(6)/6, q)
        assert result["convex_lower_bound"] <= optimum+1e-12


def test_impossible_flux_box_and_nonfinite_data_fail():
    with pytest.raises(ValueError, match="infeasible"):
        experiment.solve_qp(np.eye(6), np.full(6, .01), np.ones(6))
    with pytest.raises(ValueError, match="finite"):
        experiment.kkt_certificate(np.eye(6), np.ones(6), np.full(6, np.nan))


def test_explicit_physical_current_mapping_and_native_assignments():
    from fusion_baselines.clear_coil_geometry_audit import physical_rows

    class Current:
        def __init__(self):
            self.local_full_x = np.zeros(1)

        def get_value(self):
            return self.local_full_x[0]

    base = [Current() for _ in range(6)]
    rows = physical_rows(6)
    coils = [SimpleNamespace(current=base[row["base_index"]] if not row["flip"] else
             SimpleNamespace(get_value=lambda row=row: -base[row["base_index"]].get_value()))
             for row in rows]
    q = np.array([1., -2., .3, 0., 4., -5.])
    expected = np.concatenate((q, -q, q, -q))*1e5
    actual = experiment.set_currents(coils, q, dict(physical=rows))
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal([coil.current.get_value() for coil in coils], expected)
    with pytest.raises(ValueError, match="six"):
        experiment.physical_currents(q[:5], dict(physical=rows))


def test_synthetic_basis_linearity_area_weights_flux_and_nullspace():
    rng = np.random.default_rng(12)
    B, A = rng.normal(size=(9, 3, 6)), rng.normal(size=(7, 3, 6))
    normals, tangents = rng.normal(size=(9, 3)), rng.normal(size=(7, 3))
    M, phi, c, weights, Z, conditioning = experiment.quadratic_system(
        B, normals, A, tangents, 2., -.4)
    q = np.array([.8, .9, 1, 1.1, 1.2, 1.05])
    field = sum(q[j]*B[:, :, j] for j in range(6))
    potential = sum(q[j]*A[:, :, j] for j in range(6))
    np.testing.assert_allclose(B@q, field, rtol=1e-14, atol=1e-14)
    np.testing.assert_allclose(A@q, potential, rtol=1e-14, atol=1e-14)
    bn = [math.fsum(b[k]*n[k] for k in range(3))/math.sqrt(math.fsum(x*x for x in n))
          for b, n in zip(field, normals, strict=True)]
    objective = .5*math.fsum(w*b*b for w, b in zip(weights, bn, strict=True))/2
    assert .5*np.linalg.norm(M@q)**2 == pytest.approx(objective, rel=1e-14)
    flux = math.fsum(math.fsum(a[k]*t[k] for k in range(3))
                     for a, t in zip(potential, tangents, strict=True))/7
    assert phi@q == pytest.approx(flux, rel=1e-14)
    np.testing.assert_allclose(c@Z, np.zeros(5), atol=1e-14)
    assert len(conditioning["singular_values"]) == 5
    assert conditioning["rank"] == 5 and conditioning["condition_number"] >= 1


def test_fresh_output_required_without_native_execution(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "simsopt.field", SimpleNamespace(BiotSavart=None))
    with pytest.raises(FileExistsError):
        experiment.run(tmp_path)


def writer_control(monkeypatch, clock, filename, fault):
    original = Path.open
    triggered = [False]

    class Writer:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            answer = self.stream.__exit__(*args)
            if fault == "slow-close":
                clock[0] = 181.
            return answer

        def write(self, payload):
            if fault == "short":
                return self.stream.write(payload[:-1])
            count = self.stream.write(payload)
            if fault == "slow-write":
                clock[0] = 181.
            return count

    def open_file(path, mode="r", *args, **kwargs):
        stream = original(path, mode, *args, **kwargs)
        if path.name == filename and mode == "xb" and not triggered[0]:
            triggered[0] = True
            return Writer(stream)
        return stream

    monkeypatch.setattr(Path, "open", open_file)


@pytest.mark.parametrize("fault", ["slow-write", "slow-close", "short", "already-expired"])
def test_final_publication_cannot_accept_late_or_partial_write(tmp_path, monkeypatch, fault):
    clock = [181. if fault == "already-expired" else 179.]
    monkeypatch.setattr(experiment.time, "monotonic", lambda: clock[0])
    writer_control(monkeypatch, clock, "result.json", fault)

    def guard():
        if clock[0] >= 180:
            raise TimeoutError("synthetic publication deadline")

    report = dict(completed=True, physical_admission=False, elapsed_s=179.)
    assert experiment.publish_result(tmp_path, report, guard, 0.) == 1
    saved = json.loads((tmp_path/"result.json").read_text(encoding="utf-8"))
    marker = json.loads((tmp_path/"late-publication.json").read_text(encoding="utf-8"))
    assert saved["completed"] is False and marker["completed"] is False
    assert "publication_error" in saved
    assert (tmp_path/"rejected-late-result.json").exists() is (fault != "already-expired")
    if fault == "short":
        assert "short output write" in marker["error"]


def test_basis_write_crossing_deadline_prevents_next_qp(tmp_path, monkeypatch):
    clock, qp = [179.], Mock()
    writer_control(monkeypatch, clock, "basis.npz", "slow-close")

    def guard():
        if clock[0] >= 180:
            raise TimeoutError("synthetic basis deadline")

    with pytest.raises(TimeoutError):
        experiment.save_output(tmp_path, "basis.npz", b"retained late basis", guard)
        guard()
        qp()
    assert not qp.called
    assert (tmp_path/"basis.npz").read_bytes() == b"retained late basis"


def test_on_time_complete_write_and_diagnostic_byte_cap(tmp_path, monkeypatch):
    report = dict(completed=True)
    assert experiment.publish_result(tmp_path, report, lambda: None, 0.) == 0
    assert json.loads((tmp_path/"result.json").read_text())["completed"] is True
    monkeypatch.setattr(experiment, "MAX_BYTES", 1)
    with pytest.raises(OSError, match="output ceiling"):
        experiment.save_output(tmp_path, "extra.json", {}, lambda: None, diagnostic=True)
