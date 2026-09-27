"""Synthetic local-current gradients, selection/caps and mocked fine-field replay."""

import copy
import importlib.util
import io
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
        "explore_local_currents", ROOT/"scripts/explore_local_currents.py")
    experiment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(experiment)


def synthetic_response():
    rng = np.random.default_rng(619)
    arrays = dict(B=rng.normal(size=(13, 3, 6)), A=rng.normal(size=(11, 3, 6)),
                  normals=rng.normal(size=(13, 3)), loop_tangent=rng.normal(size=(11, 3)))
    normalization = dict(B2_scale=1.7, target_flux=-.3)
    rebuilt = experiment.current.quadratic_system(
        arrays["B"], arrays["normals"], arrays["A"], arrays["loop_tangent"], 1.7, -.3)
    arrays.update(zip(("M", "phi", "c", "weights", "nullspace"), rebuilt[:5], strict=True))
    return experiment.Response(arrays, normalization)


def test_analytic_gradient_matches_each_current_and_flux_null_direction():
    response, q = synthetic_response(), np.array([.8, .9, 1., 1.1, 1.2, 1.05])
    value, gradient, metrics = response.evaluate(q)
    assert value == pytest.approx(.5*metrics["normal_rms"]**2, rel=1e-14)
    directions = [*np.eye(6), *(experiment.projected_direction(response.c, f)
                               for f in (np.sin, np.cos))]
    for direction in directions:
        for h in (1e-5, 5e-6):
            finite = (response.evaluate(q+h*direction)[0]
                      - response.evaluate(q-h*direction)[0])/(2*h)
            assert gradient@direction == pytest.approx(finite, abs=1e-9, rel=1e-6)
    assert q@gradient == pytest.approx(0., abs=1e-15)
    assert metrics["raw_objective"] == pytest.approx(.5*np.linalg.norm(response.M@q)**2)
    assert metrics["min_b"] == pytest.approx(np.min(np.linalg.norm(response.B@q, axis=1)))


@pytest.mark.parametrize("scale", [.5, 2., -1.5])
def test_nonzero_common_scale_invariance_is_not_flux_renormalization(scale):
    response, q = synthetic_response(), np.ones(6)
    value, gradient, before = response.evaluate(q)
    after_value, after_gradient, after = response.evaluate(scale*q)
    assert after_value == pytest.approx(value, rel=1e-14)
    np.testing.assert_allclose(after_gradient, gradient/scale, rtol=1e-13, atol=1e-14)
    assert after["measured_flux"] == pytest.approx(scale*before["measured_flux"])
    assert after["raw_objective"] == pytest.approx(scale**2*before["raw_objective"])
    assert after["base_reversed"] == (list(range(6)) if scale < 0 else [])


@pytest.mark.parametrize("q", [np.zeros(6), np.ones(5), np.full(6, np.nan), np.full(6, 5.01)])
def test_undefined_field_or_invalid_current_fails_without_clipping(q):
    with pytest.raises(ValueError):
        synthetic_response().evaluate(q)


def test_response_reconstruction_rejects_changed_saved_weights():
    response = synthetic_response()
    response.arrays["weights"][0] += .001
    with pytest.raises(ValueError, match="reconstruction mismatch: weights"):
        experiment.Response(response.arrays, response.norm)


def test_probe_projection_is_flux_null_and_rejects_degeneracy():
    c = np.arange(1., 7)
    for function in (np.sin, np.cos):
        direction = experiment.projected_direction(c, function)
        assert c@direction == pytest.approx(0., abs=1e-14)
        assert np.linalg.norm(direction) == pytest.approx(1.)
    with pytest.raises(ValueError, match="degenerate"):
        experiment.projected_direction(np.sin(np.arange(6)+1), np.sin)


class Quadratic:
    c = np.ones(6)/6
    target = np.array([0., 2., 1., 1., 1., 1.])

    def evaluate(self, q):
        if np.max(abs(q)) > 5:
            raise ValueError("probe outside unchanged box")
        value = .25+.5*np.linalg.norm(q-self.target)**2
        metrics = dict.fromkeys(("normal_max", "min_b", "area_mean_b", "parameter_mean_b",
                                 "area_mean_abs_ratio", "raw_quadratic_flux", "local_flux",
                                 "raw_objective", "measured_flux"), float(value))
        metrics.update(normal_rms=float(np.sqrt(2*value)),
                       selection_feasible=bool(abs(self.c@q-1) <= 1e-10))
        return value, q-self.target, metrics


def memory_recorder():
    saved = {}

    def save(name, value, diagnostic=False):
        assert name not in saved
        saved[name] = copy.deepcopy(value)

    return saved, save


def solver_result():
    return SimpleNamespace(success=True, message="synthetic solver", nit=1, nfev=1, njev=1)


def run_search(response=None, solver=None, guard=lambda: None, start=None, anchor=None):
    response = response or Quadratic()
    start = np.ones(6) if start is None else start
    anchor = response.evaluate(start)[2] if anchor is None else anchor
    saved, save = memory_recorder()
    solver = solver or Mock(return_value=solver_result())
    result = experiment.search(response, start, anchor, "arm", save, guard, solver)
    return result, saved, solver


def test_startup_consumes_ten_and_excludes_even_better_probe_points():
    result, saved, solver = run_search()
    assert result["startup_pass"] and result["attempted"] == result["completed"] == 10
    assert solver.called and result["selected"]["role"] == "seed"
    rows = [v for k, v in saved.items() if not k.endswith("-attempt.json")]
    assert any(r["value"] < result["selected"]["value"] for r in rows if r["role"] == "probe")
    assert len(saved) == 20 and all(p["passed"] for p in result["directional_checks"])


def test_selection_keeps_feasible_search_and_excludes_better_infeasible_point():
    def solver(fun, start, **kwargs):
        assert kwargs["jac"] and kwargs["options"] == dict(maxiter=200, ftol=1e-12)
        feasible = Quadratic.target+np.array([.1, -.1, 0, 0, 0, 0])
        infeasible = Quadratic.target+np.array([0, 0, .01, 0, 0, 0])
        fun(feasible)
        fun(infeasible)
        return solver_result()

    result, saved, _ = run_search(solver=solver)
    assert result["selected"]["index"] == 10 and result["selected"]["role"] == "search"
    rejected = saved["arm-trial-011.json"]
    assert rejected["value"] < result["selected"]["value"]
    assert not rejected["metrics"]["selection_feasible"]
    assert not result["physical_admission"] and not result["convex_optimality_claim"]


def test_exact_total_bundle_cap_includes_all_startup_calls():
    def solver(fun, start, **kwargs):
        for _ in range(401):
            fun(start)

    result, saved, _ = run_search(solver=solver)
    assert result["status"]["reason"] == "budget" and result["startup_pass"]
    assert result["attempted"] == result["completed"] == 400
    assert len(saved) == 800 and "arm-trial-400-attempt.json" not in saved


@pytest.mark.parametrize("fault", ["gradient", "repeat", "anchor", "box", "infeasible-start"])
def test_startup_fault_never_enters_solver_and_retains_prefix(fault):
    response, start = Quadratic(), np.ones(6)
    if fault == "box":
        start[0], start[1] = 5., -3.
    if fault == "infeasible-start":
        start[0] = .99
    original, anchor, count = response.evaluate, response.evaluate(start)[2], [0]

    def changed(q):
        count[0] += 1
        value, gradient, metrics = original(q)
        if fault == "gradient":
            gradient = gradient+np.arange(6)
        if fault == "repeat" and count[0] == 10:
            value += 1e-6
        return value, gradient, metrics

    response.evaluate = changed
    if fault == "anchor":
        anchor["min_b"] += 1.
    result, saved, solver = run_search(response=response, start=start, anchor=anchor)
    assert not result["startup_pass"] and not solver.called
    assert result["status"]["reason"] == "failure" and saved
    if fault == "box":
        assert any(row.get("status") == "failed" for row in saved.values())


def test_late_bundle_is_retained_but_not_completed_or_selected():
    response, clock, calls = Quadratic(), [0.], [0]
    original, anchor = response.evaluate, response.evaluate(np.ones(6))[2]

    def evaluate(q):
        result = original(q)
        calls[0] += 1
        if calls[0] == 11:
            clock[0] = 241.
        return result

    def guard():
        if clock[0] >= 240:
            raise TimeoutError("synthetic late bundle")

    response.evaluate = evaluate

    def solver(fun, start, **kwargs):
        fun(Quadratic.target)

    result, saved, _ = run_search(response, solver, guard, anchor=anchor)
    assert result["attempted"] == 11 and result["completed"] == 10
    assert result["selected"]["role"] == "seed" and result["status"]["reason"] == "budget"
    assert saved["arm-trial-010.json"]["status"] == "failed"


@pytest.mark.parametrize("mismatch", [False, True])
def test_mock_fine_freezes_currents_saves_full_loop_fields_and_checks_independent(
        monkeypatch, mismatch):
    import fusion_baselines.coupled_coil_audit as audit

    q, blocks, assigned = np.array([1., -.2, .7, .8, .9, 1.1]), [], []
    points = np.arange(256*3, dtype=float).reshape(-1, 3)/1000
    loop_points = np.arange(512*3, dtype=float).reshape(-1, 3)/1000
    tangent = np.tile([1., 0., 0.], (512, 1))
    normal = np.tile([0., 0., 2.], (256, 1))

    def fields(p):
        return p*.01+[.2, .1, 2.], np.tile([.5, .1, .2], (len(p), 1))

    class Field:
        def __init__(self, coils):
            pass

        def set_points(self, p):
            blocks.append(len(p))
            self.points = p

        def B(self):
            return fields(self.points)[0]

        def A(self):
            return fields(self.points)[1]

    monkeypatch.setitem(sys.modules, "simsopt.field", SimpleNamespace(BiotSavart=Field))
    own = dict(positions=np.zeros((24, 512, 3)), tangents=np.ones((24, 512, 3)))
    monkeypatch.setattr(experiment.current.geometry_tools, "native_coils",
                        lambda snapshot, nodes: ([], own, dict(curve_identity=0.)))

    def set_currents(coils, proposed, snapshot):
        assigned.append(proposed.copy())
        return np.concatenate((proposed, -proposed, proposed, -proposed))*1e5

    def independent(p, positions, tangents, currents):
        B, A = fields(p)
        return B+(1e-6 if mismatch else 0.), A

    monkeypatch.setattr(experiment.current, "set_currents", set_currents)
    monkeypatch.setattr(audit, "boundary", lambda *args, **kwargs:
                        dict(points=points, normal=normal))
    monkeypatch.setattr(audit, "loop", lambda *args: (loop_points, tangent))
    monkeypatch.setattr(audit, "filament_field_and_potential", independent)
    saved, save = memory_recorder()
    counts = {name: dict(attempted=0, completed=0) for name in ("B", "A", "independent_BA")}
    args = ({}, {}, dict(B2_scale=1.7, target_flux=.5), q, .5, "arm", save, lambda: None, counts)
    if mismatch:
        with pytest.raises(ValueError, match="independent"):
            experiment.fine(*args)
    else:
        assert experiment.fine(*args)["checks_pass"]
    np.testing.assert_array_equal(assigned[0], q)
    assert max(blocks) == 128 and counts["B"] == dict(attempted=6, completed=6)
    assert counts["A"] == dict(attempted=4, completed=4)
    assert counts["independent_BA"] == dict(attempted=1, completed=1)
    row = saved["arm-fine-0.5.json"]
    assert row["checks_pass"] is (not mismatch) and not row["physical_admission"]
    assert row["metrics"]["flux_limit_met"] and row["q"] == q.tolist()
    with np.load(io.BytesIO(saved["arm-fine-0.5.npz"]), allow_pickle=False) as data:
        np.testing.assert_array_equal(data["q"], q)
        np.testing.assert_array_equal(data["loop_B"], fields(loop_points)[0])
        np.testing.assert_array_equal(data["A"], fields(loop_points)[1])
        assert data["independent_loop_B"].shape == (64, 3)


def test_fresh_output_required_without_native_execution(tmp_path):
    with pytest.raises(FileExistsError):
        experiment.run(tmp_path)
