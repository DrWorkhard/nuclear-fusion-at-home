"""Synthetic field-free sampling, complete query accounting and immutable inputs."""

import copy

import numpy as np
import pytest
from test_coil_perturbation import fixture

from fusion_baselines import coil_perturbation_samples as samples


def torus():
    return dict(
        nfp=2,
        lasym=False,
        rbc=[dict(m=0, n=0, value=1.2), dict(m=1, n=0, value=0.1)],
        zbs=[dict(m=1, n=0, value=0.1)],
    )


def targets():
    points = samples.surface_points(torus(), 16, 16)
    return {key: points.copy() for key in samples.TARGETS}


@pytest.mark.parametrize("nbase", [6, 8])
def test_registered_states_directions_and_exact_seed_repeat(nbase):
    seed, _ = fixture(nbase)
    original = copy.deepcopy(seed)
    vectors = samples.directions(seed)
    plan = samples.state_plan()
    assert len(plan) == 26
    assert [row["index"] for row in plan] == list(range(26))
    for vector in vectors:
        amplitudes = np.hypot(vector[..., 1::2], vector[..., 2::2])
        bound = np.linalg.norm(abs(vector[..., 0]) + amplitudes.sum(axis=-1), axis=1).max()
        assert bound == pytest.approx(1, abs=3e-16)
    assert np.count_nonzero(vectors[2]) == 1
    assert vectors[2, 0, 2, 2 * seed["order"] - 1] == 1
    np.testing.assert_array_equal(
        samples.candidate(seed, vectors, plan[0]), seed["base_coefficients"]
    )
    np.testing.assert_array_equal(
        samples.candidate(seed, vectors, plan[-1]), seed["base_coefficients"]
    )
    assert plan[1]["sign"] == 1 and plan[2]["sign"] == -1
    assert plan[1]["radius"] == 1e-5 and plan[7]["radius"] == 0.03
    assert seed == original


def test_named_flattening_uses_all_three_axes_and_fourier_modes():
    seed, _ = fixture()
    vectors = samples.directions(seed)
    shape = np.asarray(seed["base_coefficients"]).shape
    mode = np.tile(np.r_[0, np.repeat(np.arange(1, 6), 2)], (6, 3, 1))
    expected = np.sin(np.arange(np.prod(shape)).reshape(shape) + 1) / (1 + mode**2) ** 2
    ratio = vectors[0] / expected
    np.testing.assert_allclose(ratio, ratio.flat[0], rtol=5e-16)


@pytest.mark.parametrize("offset", [0, 0.5])
def test_circle_independent_fourier_derivatives(offset):
    coefficients = np.zeros((1, 3, 5))
    coefficients[0, 0, 0] = 2
    coefficients[0, 0, 2] = 0.3
    coefficients[0, 2, 1] = -0.3
    t = (np.arange(64) + offset) / 64
    p, v, a = samples.fourier(coefficients, t)
    np.testing.assert_allclose(p[0, :, 0], 2 + 0.3 * np.cos(2 * np.pi * t))
    np.testing.assert_allclose(p[0, :, 2], -0.3 * np.sin(2 * np.pi * t))
    np.testing.assert_allclose(v[0, :, 0], -0.6 * np.pi * np.sin(2 * np.pi * t), atol=1e-14)
    np.testing.assert_allclose(
        a[0, :, 2], 0.3 * (2 * np.pi) ** 2 * np.sin(2 * np.pi * t), atol=1e-13
    )


def test_surface_full_torus_orientation_and_modes():
    points = samples.surface_points(torus(), 8, 8).reshape(8, 8, 3)
    np.testing.assert_allclose(points[0, 0], [1.3, 0, 0])
    np.testing.assert_allclose(points[2, 2], [0, 1.2, 0.1], atol=1e-15)
    np.testing.assert_allclose(points[4, 0], [-1.3, 0, 0], atol=1e-15)


@pytest.mark.parametrize(
    "change",
    [
        lambda x: x.update(nfp=True),
        lambda x: x.update(lasym=True),
        lambda x: x["rbc"].append(x["rbc"][0].copy()),
        lambda x: x["rbc"][0].update(value=np.nan),
    ],
)
def test_bad_surface_rejected(change):
    data = torus()
    change(data)
    with pytest.raises(ValueError):
        samples.surface_points(data, 8, 8)


def test_all_physical_curves_complete_cp_cc_witnesses_and_counters():
    seed, _ = fixture()
    points = targets()
    sampler = samples.Sampler(seed, points)
    level = samples.levels()[0]
    raw = sampler.sample(seed["base_coefficients"], level)
    assert sampler.work() == samples.grid_budget(24, 256)
    assert raw["delta_norms"].shape == (24, 256, 3)
    assert raw["pairs"].shape == (276, 2)
    physical = np.stack(
        [
            np.asarray(row["matrix"]).T @ np.asarray(seed["base_coefficients"])[row["base_index"]]
            for row in seed["physical"]
        ]
    )
    p, _, _ = samples.fourier(physical, raw["parameters"])
    for target in samples.TARGETS:
        witness = points[target][raw[f"cp_{target}_indices"]]
        np.testing.assert_allclose(
            np.linalg.norm(p - witness, axis=-1), raw[f"cp_{target}_distances"], atol=1e-15
        )
    for index in (0, 20, 275):
        i, j = raw["pairs"][index]
        a, b = raw["pair_witnesses"][index]
        assert np.linalg.norm(p[i, a] - p[j, b]) == pytest.approx(raw["pair_distances"][index])
        exact = np.linalg.norm(p[i, :, None] - p[j, None], axis=-1).min()
        assert raw["pair_distances"][index] == pytest.approx(exact)
    np.testing.assert_allclose(raw["curvature"], 1 / 0.3, rtol=1e-14)
    assert raw["curvature_available"].all() and (raw["projection"] > 0).all()
    assert raw["delta_norms"].max() < 1e-12


def test_mutable_inputs_are_private_copies():
    seed, _ = fixture()
    points = targets()
    original = copy.deepcopy(seed)
    sampler = samples.Sampler(seed, points)
    seed["base_coefficients"][0][0][0] += 1
    for p in points.values():
        p[:] = 0
    raw = sampler.sample(original["base_coefficients"], samples.levels()[0])
    assert raw["delta_norms"].max() < 1e-12
    assert raw["cp_reference_distances"].max() < 0.4


def test_degenerate_current_curve_has_explicit_unavailable_curvature():
    seed, _ = fixture()
    c = np.asarray(seed["base_coefficients"]).copy()
    c[..., 1:] = 0
    raw = samples.Sampler(seed, targets()).sample(c, samples.levels()[0])
    assert not raw["curvature_available"].any()
    assert (raw["curvature"] == 0).all()
    assert all(np.isfinite(a).all() for a in raw.values())


def test_failed_query_retains_attempted_not_completed_and_honors_single_thread(monkeypatch):
    seed, _ = fixture()
    sampler = samples.Sampler(seed, targets())

    class Fail:
        def query(self, points, **kwargs):
            assert kwargs == dict(k=1, eps=0, workers=1)
            raise ValueError("synthetic query failure")

    sampler._trees["reference"] = Fail()
    with pytest.raises(ValueError, match="synthetic"):
        sampler.sample(seed["base_coefficients"], samples.levels()[0])
    assert sampler.work()["cp"] == dict(
        attempted=1, completed=0, points_attempted=24 * 256, points_completed=0
    )
    assert sampler.work()["fourier"]["completed"] == 3
    assert sampler.work()["cc"]["attempted"] == 0


def test_guard_stops_before_any_dispatch():
    seed, _ = fixture()

    def stop():
        raise TimeoutError("synthetic deadline")

    sampler = samples.Sampler(seed, targets(), check=stop)
    with pytest.raises(TimeoutError):
        sampler.sample(seed["base_coefficients"], samples.levels()[0])
    assert sampler.work() == samples.empty_work()


def test_cap_precedes_query_dispatch():
    seed, _ = fixture()
    sampler = samples.Sampler(seed, targets())
    sampler._start = samples.empty_work()
    sampler._budget = samples.grid_budget(24, 256)
    sampler._work["cp"]["attempted"] = 2
    with pytest.raises(RuntimeError, match="before dispatch"):
        sampler._call("cp", 1, lambda: pytest.fail("over-budget work dispatched"))


@pytest.mark.parametrize(
    "level", [dict(ncoil=128, offset=0), dict(ncoil=True, offset=0), dict(ncoil=256, offset=False)]
)
def test_unregistered_levels_rejected(level):
    seed, _ = fixture()
    with pytest.raises(ValueError):
        samples.Sampler(seed, targets()).sample(seed["base_coefficients"], level)


@pytest.mark.parametrize("nbase", [6, 8])
def test_actual_synthetic_derivative_projection_and_length_bounds(nbase):
    from fusion_baselines.coil_perturbation import candidate_certificate

    seed, report = fixture(nbase)
    vector = samples.directions(seed)
    coefficients = samples.candidate(seed, vector, samples.state_plan()[17])
    certificate = candidate_certificate(seed, report, coefficients)
    raw = samples.Sampler(seed, targets()).sample(coefficients, samples.levels()[3])
    for i, curve in enumerate(certificate["curves"]):
        for order in range(3):
            assert raw["delta_norms"][i, :, order].max() <= curve[f"D{order}"] + 1e-12
        assert raw["seed_speed"][i].max() <= curve["V0"] + 1e-12
        assert raw["seed_acceleration"][i].max() <= curve["A0"] + 1e-12
        assert raw["speed"][i].min() >= curve["v_lower"] - 1e-12
        assert raw["projection"][i].min() >= curve["S_lower"] - 1e-12
        assert raw["curvature_available"][i].all()
        assert raw["curvature"][i].max() <= curve["kappa_upper"] + 1e-12
        assert abs(raw["lengths"][i] - raw["seed_lengths"][i]) <= curve["D1"] + 1e-12


def test_boolean_alias_is_not_a_registered_state():
    seed, _ = fixture()
    state = samples.state_plan()[1]
    state["sign"] = True
    with pytest.raises(ValueError, match="state descriptor"):
        samples.candidate(seed, samples.directions(seed), state)
