"""Synthetic independent clear-start certification; no actual target inputs."""

import json

import numpy as np
import pytest

from fusion_baselines import clear_coil_geometry as producer
from fusion_baselines import clear_coil_geometry_audit as audit


def torus():
    return dict(
        nfp=2,
        lasym=False,
        mpol=4,
        ntor=2,
        rbc=[
            dict(m=0, n=0, value=1.2),
            dict(m=1, n=0, value=0.1),
            dict(m=1, n=1, value=0.008),
            dict(m=2, n=-1, value=0.003),
        ],
        zbs=[dict(m=1, n=0, value=0.1), dict(m=1, n=-1, value=0.004)],
    )


def snapshot(nbase=6, order=5, radius=0.3):
    case = next(c for c in audit.cases() if c["nbase"] == nbase and c["method"] == "circle")
    coefficients = [
        audit.export_coefficients(
            [radius, 0, 0], [1.2, 0], (i + 0.5) * np.pi / (2 * nbase), order
        ).tolist()
        for i in range(nbase)
    ]
    return dict(
        schema_version=1,
        kind="geometry-only",
        nfp=2,
        nbase=nbase,
        order=order,
        names=audit.parameter_names(nbase, order),
        base_coefficients=coefficients,
        physical=audit.physical_rows(nbase),
        case=case,
        sources=dict(reference={}, selected={}),
        parameter_orientation="alpha=-2*pi*t",
    )


def test_complete_registered_geometry_matrix_matches_producer():
    assert audit.cases() == producer.cases()
    assert len(audit.cases()) == 12
    assert sum(c["nbase"] for c in audit.cases()) == 84


@pytest.mark.parametrize("shift", [0, 0.5])
def test_nonaxisymmetric_native_surface_and_continuous_cover(shift):
    data = torus()
    a, b = producer.surface(data, 48, 64, shift), audit.surface(data, 48, 64, shift)
    audit.compare(a["points"], b["points"], "independent fulltorus")
    for key in ("cover", "radius_lower", "pad"):
        audit.compare(a[key], b[key], key)
    assert b["radius_lower"] > 0 and b["cover"] > 0
    fine = audit.surface(data, 96, 128)
    from scipy.spatial import cKDTree

    assert (
        cKDTree(b["points"].reshape(-1, 3)).query(fine["points"].reshape(-1, 3))[0].max()
        < b["cover"]
    )


@pytest.mark.parametrize("bad", ["duplicate", "asymmetric", "negative_radius", "nonfinite"])
def test_invalid_boundary_never_receives_positive_radius_certificate(bad):
    data = torus()
    if bad == "duplicate":
        data["rbc"].append(data["rbc"][0].copy())
    elif bad == "asymmetric":
        data["rbs"] = [dict(m=1, n=0, value=0.1)]
    elif bad == "negative_radius":
        data["rbc"][0]["value"] = -1.0
    else:
        data["zbs"][0]["value"] = np.nan
    with pytest.raises(ValueError):
        audit.surface(data, 16, 16)


def test_tangent_disks_are_outward_padded_and_negative_branch_not_assumed():
    points = np.array(
        [
            [1.2, 0, 0],
            [-1.2, 0, 0],
            [1.2, 0.2, 0],
            [1.2, 0.2 + 5e-13, 0],
            [1.2, 0.201, 0],
            [-0.01, 0, 0],
        ]
    )
    row = dict(points=points, cover=0.1, full_torus=True, radius_lower=0.01)
    a = audit.envelope([row], 0.0, 0.1, 0.1, [1.2, 0])
    b = producer.envelope([row], 0.0, 0.1, 0.1, [1.2, 0])
    assert a["grid_index"].tolist() == [0, 2, 3, 5]
    for key in ("centers", "radii", "expansions", "pads"):
        audit.compare(a[key], b[key], key)
    assert a["radii"][0] > 0.2 and a["radii"][1] > 0 and a["radii"][2] > 0
    # The negative projected center at -0.01 must remain because its sphere
    # reaches R_floor. Sign-only branch exclusion would incorrectly omit it.
    assert a["centers"][-1, 0] == pytest.approx(-1.21)


@pytest.mark.parametrize("K", [1, 4, 6])
def test_independent_support_lp_and_primal_dual_certificate(K):
    disks = dict(centers=np.array([[0.02, -0.01], [-0.02, 0.015]]), radii=np.array([0.25, 0.24]))
    a, b = producer.problem(disks, K, 1.2, 0.25), audit.problem(disks, K, 1.2, 0.25)
    for key in ("A", "b", "c", "lower", "upper", "angles", "support"):
        audit.compare(a[key], b[key], key)
    solved = producer.solve(a)
    assert audit.dual_certificate(b, solved)["passed"]
    repeated = producer.solve(a)
    for key in ("x", "slack", "inequality_marginals", "lower_marginals", "upper_marginals"):
        assert np.array_equal(solved[key], repeated[key])
    cert = audit.continuous_certificate(
        b, np.array(solved["x"])[: 2 * K + 1], disks, [1.2, 0], 0.25
    )
    assert cert["support_pass"] and cert["length_pass"] and cert["curvature_pass"]
    json.dumps(cert, allow_nan=False)


@pytest.mark.parametrize(
    "bad", ["x", "dual_sign", "dual_stationarity", "slack", "objective", "missing"]
)
def test_forged_lp_solution_fails_independent_certificate(bad):
    disks = dict(centers=np.array([[0.0, 0.0]]), radii=np.array([0.25]))
    model = audit.problem(disks, 1, 1.2, 0.25)
    solved = producer.solve(model)
    if bad == "x":
        solved["x"][0] -= 0.01
    elif bad == "dual_sign":
        solved["inequality_marginals"][0] = 0.1
    elif bad == "dual_stationarity":
        solved["lower_marginals"][0] += 0.1
    elif bad == "slack":
        solved["slack"][0] += 0.01
    elif bad == "objective":
        solved["objective"] += 0.01
    else:
        solved["x"].pop()
        with pytest.raises(ValueError):
            audit.dual_certificate(model, solved)
        return
    assert not audit.dual_certificate(model, solved)["passed"]


def test_unsolved_lp_is_not_a_proof_of_infeasibility():
    model = audit.problem(dict(centers=np.array([[0.0, 0.0]]), radii=np.array([5.0])), 1, 1.2, 0.25)
    result = audit.dual_certificate(model, producer.solve(model))
    assert result == dict(solved=False, passed=False, infeasibility_proven=False)


@pytest.mark.parametrize("K,order", [(1, 5), (4, 5), (6, 7)])
def test_independent_real_export_matches_complex_native_orientation(K, order):
    h = np.zeros(2 * K + 1)
    h[0] = 0.35
    h[1:] = 0.001 * np.sin(np.arange(2 * K) + 1)
    h[1:3] = [0.02, -0.03]
    center, phi = np.array([1.1, -0.01]), 0.4
    a = audit.export_coefficients(h, center, phi, order)
    audit.compare(a, producer.export_coefficients(h, center, phi, order), "exact export")
    t = np.arange(128) / 128
    alpha = -2 * np.pi * t
    basis = audit.support_basis(K, alpha)
    hv = basis @ h
    hp = sum(
        m * (h[2 * m - 1] * np.cos(m * alpha) - h[2 * m] * np.sin(m * alpha))
        for m in range(1, K + 1)
    )
    r = center[0] + hv * np.cos(alpha) - hp * np.sin(alpha)
    z = center[1] + hv * np.sin(alpha) + hp * np.cos(alpha)
    expected = np.column_stack((r * np.cos(phi), r * np.sin(phi), z))
    reconstructed = np.tile(a[:, 0], (len(t), 1))
    for m in range(1, order + 1):
        reconstructed += (
            a[:, 2 * m - 1] * np.sin(2 * np.pi * m * t)[:, None]
            + a[:, 2 * m] * np.cos(2 * np.pi * m * t)[:, None]
        )
    np.testing.assert_allclose(expected, reconstructed, rtol=0, atol=2e-15)


def test_between_normal_nodes_must_use_actual_coefficient_lipschitz_bounds():
    h = np.array([0.35, 0.0, 0.0, 0.0, 0.03])
    disks = dict(centers=np.array([[0, 0]]), radii=np.array([0.36]))
    model = audit.problem(disks, 2, 1.2, 0.25, nangle=8)
    cert = audit.continuous_certificate(model, h, disks, [1.2, 0], 0.25)
    assert cert["enclosure_lower"] < 0 and not cert["support_pass"]
    assert cert["L_h"] == pytest.approx(0.06)
    assert cert["L_rho"] == pytest.approx(0.18)


@pytest.mark.parametrize("nbase,order", [(6, 5), (8, 7)])
def test_all_geometry_only_copies_and_direct_circle_certificates(nbase, order):
    snap = snapshot(nbase, order)
    audit.validate_snapshot(snap)
    curves = audit.physical_curves(snap, 128)
    np.testing.assert_allclose(curves["speed"], 2 * np.pi * 0.3, rtol=2e-15, atol=2e-15)
    data = torus()
    target = audit.surface(data, 64, 64)
    report = audit.distance_certificate(snap, target, 128)
    assert len(report["coil_pairs"]) == 4 * nbase * (4 * nbase - 1) // 2
    assert len(report["plasma_distances"]) == 4 * nbase
    assert report["coil_pass"]
    assert min(row["sampled"] for row in report["plasma_distances"]) > 0.18
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.update(current=1e5),
        lambda s: s["physical"][0].update(current=1e5),
        lambda s: s["physical"].pop(),
        lambda s: s["names"].reverse(),
        lambda s: s["physical"][0].update(flip=0),
        lambda s: s.update(parameter_orientation="alpha=2*pi*t"),
        lambda s: s["base_coefficients"][0][0].__setitem__(0, np.nan),
    ],
)
def test_geometry_snapshot_refuses_fields_wrong_orientation_or_mapping(mutation):
    value = snapshot()
    mutation(value)
    with pytest.raises(ValueError):
        audit.validate_snapshot(value)


def test_raw_match_screen_is_absolute_and_failclosed():
    audit.compare([1.0], [1.0 + 1e-12], "within")
    with pytest.raises(ValueError):
        audit.compare([1000.0], [1000.0 + 1e-10], "no relative escape")
    with pytest.raises(ValueError):
        audit.compare([1], [1, 2], "shape")
    with pytest.raises(ValueError):
        audit.compare([1], [2], "ids", exact=True)


@pytest.mark.parametrize("value", [[1 + 1j], ["1.0"], np.array([1.0], dtype=object), [True]])
def test_numerical_input_does_not_discard_imaginary_parts_or_coerce_strings(value):
    with pytest.raises(ValueError):
        audit.finite(value)


def test_length_acceptance_has_an_explicit_floating_upper_bound():
    disks = dict(centers=np.array([[0.0, 0.0]]), radii=np.array([0.2]))
    model = audit.problem(disks, 1, 1.2, 0.25)
    cert = audit.continuous_certificate(model, [3.5 / (2 * np.pi), 0, 0], disks, [1.2, 0], 0.25)
    assert cert["length"] == pytest.approx(3.5) and cert["length_upper"] > 3.5
    assert not cert["length_pass"]


def test_disk_envelope_rejects_infinite_radius_certificate():
    row = dict(points=np.array([[1.0, 0.0, 0.0]]), cover=0.1, full_torus=True, radius_lower=np.inf)
    with pytest.raises(ValueError):
        audit.envelope([row], 0.0, 0.1, 0.25, [1.0, 0.0])


def test_export_tolerance_is_not_a_length_margin_waiver():
    radius = (3.5 - 5e-12) / (2 * np.pi)
    h = np.array([radius, 0.0, 0.0])
    disks = dict(centers=np.array([[0.0, 0.0]]), radii=np.array([0.2]))
    model = audit.problem(disks, 1, 1.2, 0.25)
    ideal = audit.continuous_certificate(model, h, disks, [1.2, 0], 0.25)
    expected = audit.export_coefficients(h, [1.2, 0], 0.0, 5)
    actual = expected.copy()
    actual[0, 2] += 4e-12
    actual[2, 1] -= 4e-12
    audit.compare(actual, expected, "inside raw coefficient tolerance")
    result = audit.export_certificate(ideal, h, expected, actual, 0.25, 0.1)
    assert ideal["length_pass"] and ideal["support_pass"]
    assert 2 * np.pi * (radius + 4e-12) > 3.5
    assert not result["length_pass"] and result["length_upper"] > 3.5


def test_export_tolerance_is_not_a_curvature_margin_waiver():
    radius = 1 / 12 + 1e-13
    h = np.array([radius, 0.0, 0.0])
    disks = dict(centers=np.array([[0.0, 0.0]]), radii=np.array([0.02]))
    model = audit.problem(disks, 1, 1.2, 0.25)
    ideal = audit.continuous_certificate(model, h, disks, [1.2, 0], 0.25)
    expected = audit.export_coefficients(h, [1.2, 0], 0.0, 5)
    actual = expected.copy()
    actual[0, 2] -= 2e-12
    actual[2, 1] += 2e-12
    result = audit.export_certificate(ideal, h, expected, actual, 0.25, 0.1)
    assert ideal["curvature_pass"] and 1 / (radius - 2e-12) > 12
    assert not result["curvature_pass"] and result["curvature_upper"] > 12
