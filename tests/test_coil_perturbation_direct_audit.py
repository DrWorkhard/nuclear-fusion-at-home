"""Synthetic direct geometry; no actual target, matrix worker or field calls."""

import copy

import numpy as np
import pytest
from scipy.spatial import cKDTree
from test_coil_perturbation_audit import synthetic_seed

from fusion_baselines import coil_perturbation_audit as mathematical
from fusion_baselines import coil_perturbation_direct_audit as audit


def surface_points():
    phi = 2 * np.pi * np.arange(128) / 128
    theta = 2 * np.pi * np.arange(16) / 16
    radius = 1.2 + 0.03 * np.cos(theta)
    x = np.cos(phi)[:, None] * radius
    y = np.sin(phi)[:, None] * radius
    z = np.broadcast_to(0.03 * np.sin(theta), x.shape)
    return np.stack((x, y, z), axis=-1)


def raw_fixture(snapshot, coefficients, level):
    raw, points = audit.reconstruct(snapshot, coefficients, level)
    surfaces = {key: surface_points() for key in audit.TARGETS}
    for target, plasma in surfaces.items():
        d, index = cKDTree(plasma.reshape(-1, 3)).query(points.reshape(-1, 3), workers=1)
        raw[f"cp_{target}_distances"] = d.reshape(points.shape[:2])
        raw[f"cp_{target}_indices"] = index.reshape(points.shape[:2])
    pairs, minima, witnesses = [], [], []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            distance, index = cKDTree(points[j]).query(points[i], workers=1)
            k = int(distance.argmin())
            pairs.append((i, j))
            minima.append(distance[k])
            witnesses.append((k, int(index[k])))
    raw.update(
        pairs=np.array(pairs, dtype=int),
        pair_distances=np.array(minima),
        pair_witnesses=np.array(witnesses, dtype=int),
    )
    return raw, surfaces


@pytest.fixture(scope="module")
def sample():
    snapshot, report = synthetic_seed()
    candidate = np.array(snapshot["base_coefficients"])
    candidate[0, 2, -2] += 1e-5
    level = dict(ncoil=64, offset=0.5)
    certificate = mathematical.independent_certificate(snapshot, report, candidate)
    raw, surfaces = raw_fixture(snapshot, candidate, level)
    return snapshot, candidate, certificate, level, raw, surfaces


def test_fixed_plan_has_all_26_ordered_states_and_four_registered_grids():
    plan = audit.plan()
    assert len(plan) == 26
    assert [r["index"] for r in plan] == list(range(26))
    assert plan[0]["kind"] == "seed" and plan[-1]["kind"] == "seed-repeat"
    assert len([r for r in plan if r["radius"] == 1e-5]) == 6
    assert [(r["direction_index"], r["radius"], r["sign"]) for r in plan[1:5]] == [
        (0, 1e-5, 1),
        (0, 1e-5, -1),
        (0, 1e-4, 1),
        (0, 1e-4, -1),
    ]
    assert audit.levels() == [
        dict(ncoil=256, offset=0),
        dict(ncoil=512, offset=0),
        dict(ncoil=1024, offset=0),
        dict(ncoil=1024, offset=0.5),
    ]


@pytest.mark.parametrize("nbase", [6, 8])
def test_directions_exact_named_order_and_unpadded_position_normalization(nbase):
    snapshot, _ = synthetic_seed(nbase)
    directions = audit.directions(snapshot)
    for direction in directions:
        amplitude = np.hypot(direction[..., 1::2], direction[..., 2::2])
        bound = np.linalg.norm(abs(direction[..., 0]) + amplitude.sum(axis=-1), axis=1)
        assert bound.max() == pytest.approx(1, abs=1e-15)
    assert np.count_nonzero(directions[2]) == 1
    assert directions[2][0, 2, 2 * snapshot["order"] - 1] == 1
    assert np.array_equal(audit.candidate(snapshot, audit.plan()[0]), snapshot["base_coefficients"])
    assert np.array_equal(
        audit.candidate(snapshot, audit.plan()[25]), snapshot["base_coefficients"]
    )
    plus, minus = [audit.candidate(snapshot, audit.plan()[i]) for i in (1, 2)]
    assert np.allclose(
        plus + minus, 2 * np.array(snapshot["base_coefficients"]), rtol=0, atol=1e-15
    )


def test_analytic_circle_positions_derivatives_and_oriented_projection():
    snapshot, _ = synthetic_seed()
    level = dict(ncoil=64, offset=0.5)
    raw, positions = audit.reconstruct(snapshot, snapshot["base_coefficients"], level)
    assert np.allclose(raw["speed"], 2 * np.pi * 0.2)
    assert np.allclose(raw["curvature"], 5)
    assert raw["curvature_available"].all()
    assert np.allclose(raw["projection"], (2 * np.pi) ** 3 * 0.2**2)
    phi = 0.5 * np.pi / (2 * snapshot["nbase"])
    t = raw["parameters"]
    radius = 1.2 + 0.2 * np.cos(2 * np.pi * t)
    assert np.allclose(positions[0, :, 0], np.cos(phi) * radius)
    assert np.allclose(positions[0, :, 2], -0.2 * np.sin(2 * np.pi * t))


def test_full_synthetic_direct_recomputation_and_all_enclosures(sample):
    result = audit.audit_samples(*sample)
    assert result["passed"] and result["coil_pairs_checked"] == 276
    assert result["cp_distances_checked"] == 2 * 24 * 64
    assert result["work"] == audit.bounded_work(24, 64)


@pytest.mark.parametrize(
    "mutation",
    [
        "cp_value",
        "cp_index",
        "pair_value",
        "pair_witness",
        "pair_order",
        "mask",
        "projection",
        "delta",
        "seed_speed",
        "seed_length",
        "parameter",
        "normal",
        "missing",
    ],
)
def test_every_saved_direct_quantity_is_rechecked(sample, mutation):
    data = copy.deepcopy(sample)
    raw = data[4]
    if mutation == "cp_value":
        raw["cp_reference_distances"][0, 0] += 1e-4
    elif mutation == "cp_index":
        raw["cp_reference_indices"][0, 0] = 10**9
    elif mutation == "pair_value":
        raw["pair_distances"][0] += 1e-4
    elif mutation == "pair_witness":
        raw["pair_witnesses"][0] = (0, 1)
    elif mutation == "pair_order":
        raw["pairs"][[0, 1]] = raw["pairs"][[1, 0]]
    elif mutation == "mask":
        raw["curvature_available"] = raw["curvature_available"].astype(float)
    elif mutation == "projection":
        raw["projection"][0, 0] *= -1
    elif mutation == "delta":
        raw["delta_norms"][0, 0, 2] = 0
    elif mutation == "seed_speed":
        raw["seed_speed"][0, 0] = 0
    elif mutation == "seed_length":
        raw["seed_lengths"][0] = 0
    elif mutation == "parameter":
        raw["parameters"][0] += 1e-4
    elif mutation == "normal":
        raw["normals"][0] *= -1
    else:
        del raw["pair_witnesses"]
    with pytest.raises(ValueError):
        audit.audit_samples(*data)


def test_tied_cp_nearest_indices_not_required_to_match_tree_choice(sample):
    data = copy.deepcopy(sample)
    raw, surfaces = data[4:]
    for target in audit.TARGETS:
        points = surfaces[target].reshape(-1, 3)
        surfaces[target] = np.concatenate((points, points))
        raw[f"cp_{target}_indices"] += len(points)
    assert audit.audit_samples(*data)["passed"]


@pytest.mark.parametrize("key", ["D2", "V0", "A0", "v_lower", "S_lower", "kappa_upper"])
def test_bound_violations_rejected_independent_of_saved_pass_flags(sample, key):
    data = copy.deepcopy(sample)
    row = data[2]["curves"][0]
    row[key] = 1e6 if key in ("v_lower", "S_lower") else 0.0
    with pytest.raises(ValueError):
        audit.audit_samples(*data)


def test_uncertified_high_mode_still_receives_every_available_direct_check():
    snapshot, report = synthetic_seed()
    candidate = np.array(snapshot["base_coefficients"])
    candidate[0, 2, -2] += 0.03
    cert = mathematical.independent_certificate(snapshot, report, candidate)
    assert not cert["certified"]
    level = dict(ncoil=64, offset=0)
    raw, surfaces = raw_fixture(snapshot, candidate, level)
    assert audit.audit_samples(snapshot, candidate, cert, level, raw, surfaces)["passed"]


def test_degenerate_point_curve_records_boolean_unavailable_curvature_without_nan():
    snapshot, _ = synthetic_seed()
    candidate = np.array(snapshot["base_coefficients"])
    candidate[:, :, 1:] = 0
    raw, _ = audit.reconstruct(snapshot, candidate, dict(ncoil=16, offset=0))
    assert not raw["curvature_available"].any()
    assert np.isfinite(raw["curvature"]).all() and not raw["curvature"].any()


def test_enclosures_have_no_second_tolerance_beyond_certificate_padding():
    with pytest.raises(ValueError):
        audit._enclosed_lower(np.array([1.0]), np.nextafter(1.0, np.inf), "strict lower")
    with pytest.raises(ValueError):
        audit._enclosed_upper(np.array([1.0]), np.nextafter(1.0, -np.inf), "strict upper")
