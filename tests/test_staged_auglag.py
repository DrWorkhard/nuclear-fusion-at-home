from types import SimpleNamespace

import numpy as np

from fusion_baselines.inequality_oracle import InequalityOracle
from fusion_baselines.natural_flux_backend import NaturalFluxBackend
from fusion_baselines.staged_auglag import solve_stages


def fixture():
    state = {}

    def direct(x):
        state["x"] = x.copy()
        return np.array([0.5 * x[0] ** 2, 1 - x[0]]), np.array([[x[0]], [-1.0]]), {}

    backend = NaturalFluxBackend(
        direct, lambda: (state["x"], np.ones((1, 1))), lambda: state["x"], flux_scale=1.0
    )
    oracle = InequalityOracle(backend.evaluate, 1033, 1, 1)
    return backend, oracle


def test_stage_caps_count_trials_but_cache_hits_do_not_consume_budget():
    backend, oracle = fixture()
    initial, _ = oracle.evaluate([2.0])
    stages = []

    def fake(fun, x, jac, **options):
        for i in range(200):
            point = x + i + 0.5
            fun(point)
            jac(point)  # exact cache reuse
        raise AssertionError("stage cap must interrupt")

    reason = solve_stages(
        oracle, backend, [2.0], initial, minimizer=fake, stages=stages, target_enabled=False
    )
    assert reason == "eight_stages_completed"
    assert len(stages) == 8
    assert all(r["end_attempts"] - r["start_attempts"] == 128 and r["denied"] == 1 for r in stages)
    assert oracle.counters()["attempts"] == 1025  # only one qualification call in this fixture
    assert oracle.counters()["cache_hits"] == 1024
    assert oracle.counters()["denied"] == 0


def test_early_solver_return_does_not_transfer_unused_bundles():
    backend, oracle = fixture()
    initial, _ = oracle.evaluate([2.0])
    stages = []

    def fake(fun, x, jac, **options):
        fun(x)
        jac(x)
        return SimpleNamespace(status=1, success=True, nfev=1, njev=1)

    assert (
        solve_stages(
            oracle, backend, [2.0], initial, minimizer=fake, stages=stages, target_enabled=False
        )
        == "eight_stages_completed"
    )
    assert len(stages) == 8 and oracle.counters()["attempts"] == 1
    assert all(r["denied"] == 0 for r in stages)


def test_construction_target_is_separate_from_solver_convergence():
    backend, oracle = fixture()
    initial, _ = oracle.evaluate([0.01])
    stages = []

    def fake(fun, x, jac, **options):
        fun(x)
        raise AssertionError("target must interrupt before any solver return")

    assert (
        solve_stages(oracle, backend, [0.01], initial, minimizer=fake, stages=stages)
        == "construction_target"
    )
    assert len(stages) == 1 and "solver" not in stages[0]
