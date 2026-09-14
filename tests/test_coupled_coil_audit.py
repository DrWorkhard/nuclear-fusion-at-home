"""Synthetic independent reconstruction checks; no registered physical target runs."""

import copy

import numpy as np
import pytest

from fusion_baselines.coupled_coil_audit import (
    boundary,
    derivative_suprema,
    entry_gates,
    fan_area,
    filament_field_and_potential,
    fourier_curves,
    geometry_certificates,
    geometry_penalties,
    inner_metrics,
    loop,
    metrics,
    parameter_names,
    physical_curves,
    refinement_pass,
    surface_derivative_bounds,
    validate_snapshot,
)


def circle_surface(radius=0.2, major=1.0):
    return dict(
        lasym=False,
        nfp=2,
        mpol=2,
        ntor=0,
        rbc=[dict(m=0, n=0, value=major), dict(m=1, n=0, value=radius)],
        zbs=[dict(m=1, n=0, value=radius)],
        rbs=None,
        zbc=None,
    )


def snapshot():
    nbase, order = 6, 5
    coefficients = np.zeros((nbase, 3, 2 * order + 1))
    for i in range(nbase):
        angle = (i + 0.5) * np.pi / (2 * nbase)
        coefficients[i, :, 0] = [np.cos(angle), np.sin(angle), 0]
        coefficients[i, :, 2] = 0.35 * np.array([np.cos(angle), np.sin(angle), 0])
        coefficients[i, 2, 1] = 0.35
    answer = dict(
        schema_version=1,
        nfp=2,
        nbase=nbase,
        order=order,
        names=parameter_names(nbase, order),
        base_coefficients=coefficients.tolist(),
        B2_scale=1.0,
        scale=0.25,
        unit_flux=0.04,
        target_flux=0.01,
    )
    rows = []
    for period in range(2):
        angle = np.pi * period
        c, s = np.cos(angle), np.sin(angle)
        rotation = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        for flip in (False, True):
            matrix = rotation.T @ (np.diag([1, -1, -1]) if flip else np.eye(3))
            for i in range(nbase):
                rows.append(
                    dict(
                        base_index=i,
                        period=period,
                        flip=flip,
                        matrix=matrix.tolist(),
                        current=100000 * answer["scale"] * (-1 if flip else 1),
                    )
                )
    answer["physical"] = rows
    return answer


def test_snapshot_exact_mapping_and_symmetry():
    value = snapshot()
    validate_snapshot(value)
    curves = physical_curves(value, 64)
    assert curves["positions"].shape == (24, 64, 3)
    assert value["names"][:4] == [
        "coil[0]/xc(0)",
        "coil[0]/xs(1)",
        "coil[0]/xc(1)",
        "coil[0]/xs(2)",
    ]
    for row, p in zip(value["physical"], curves["positions"], strict=True):
        np.testing.assert_allclose(
            p, curves["positions"][row["base_index"]] @ row["matrix"], atol=3e-16, rtol=3e-16
        )
    np.testing.assert_array_equal(curves["currents"][:6], 25000)
    np.testing.assert_array_equal(curves["currents"][6:12], -25000)


@pytest.mark.parametrize(
    "change",
    [
        lambda x: x["names"].reverse(),
        lambda x: x["physical"].pop(),
        lambda x: x["physical"][6].update(current=25000),
        lambda x: x["physical"][0].update(flip=0),
        lambda x: x["physical"][12]["matrix"][0].__setitem__(1, 0.0),
        lambda x: x["base_coefficients"][0][0].__setitem__(0, np.nan),
        lambda x: x.update(scale=0.5),
        lambda x: x.update(B2_scale=0),
        lambda x: x.update(unit_flux=0),
        lambda x: x.update(nbase=8),
    ],
)
def test_reject_malformed_snapshot(change):
    value = snapshot()
    change(value)
    with pytest.raises(ValueError):
        validate_snapshot(value)


def test_fourier_all_derivatives_and_bounds():
    coefficient = np.zeros((1, 3, 7))
    coefficient[0, 0, 2] = 0.4
    coefficient[0, 1, 1] = 0.4
    coefficient[0, 2, 5] = 0.03
    curves = fourier_curves(coefficient, 128)
    t = 2 * np.pi * np.arange(128) / 128
    np.testing.assert_allclose(curves["positions"][0, :, 2], 0.03 * np.sin(3 * t), atol=1e-15)
    np.testing.assert_allclose(curves["tangents"][0, :, 0], -0.8 * np.pi * np.sin(t), atol=2e-15)
    np.testing.assert_allclose(
        curves["second"][0, :, 1], -0.4 * (2 * np.pi) ** 2 * np.sin(t), atol=1e-14
    )
    np.testing.assert_allclose(
        curves["third"][0, :, 2], -0.03 * (6 * np.pi) ** 3 * np.cos(3 * t), atol=5e-13
    )
    bounds = derivative_suprema(coefficient)[0]
    for k, key in enumerate(("tangents", "second", "third")):
        assert np.linalg.norm(curves[key], axis=-1).max() <= bounds[k] * (1 + 1e-14)


def test_circle_direct_B_A_and_signed_stokes():
    coefficient = np.zeros((1, 3, 3))
    coefficient[0, 0, 0] = 3.0
    coefficient[0, 0, 2] = 1.0
    coefficient[0, 2, 1] = 1.0
    coils = fourier_curves(coefficient, 512)
    current = np.array([123.0])
    p = np.array([[3.0, 0.0, 0.0], [3.0, 0.3, 0.0]])
    B, A = filament_field_and_potential(p, coils["positions"], coils["tangents"], current)
    expected = -2e-7 * np.pi * current[0] / (1 + p[:, 1] ** 2) ** 1.5
    np.testing.assert_allclose(B[:, 1], expected, atol=1e-18, rtol=2e-14)
    np.testing.assert_allclose(B[:, (0, 2)], 0, atol=1e-18)
    np.testing.assert_allclose(A, 0, atol=1e-18)
    target = circle_surface(radius=0.4, major=3.0)
    points, tangents = loop(target, 128)
    _, potential = filament_field_and_potential(
        points, coils["positions"], coils["tangents"], current
    )
    line_flux = np.mean(np.sum(potential * tangents, axis=-1))
    area_points, normals = fan_area(target, 16, 128)
    magnetic, _ = filament_field_and_potential(
        area_points, coils["positions"], coils["tangents"], current
    )
    area_flux = np.sum(magnetic * normals)
    assert np.all(normals[:, 1] < 0)
    assert area_flux > 0 and line_flux > 0
    assert abs(area_flux / line_flux - 1) < 2e-13
    reverse = copy.deepcopy(target)
    reverse["zbs"][0]["value"] *= -1
    reverse_points, reverse_normals = fan_area(reverse, 16, 128)
    reverse_field, _ = filament_field_and_potential(
        reverse_points, coils["positions"], coils["tangents"], current
    )
    assert abs(np.sum(reverse_field * reverse_normals) / area_flux + 1) < 2e-13


def test_field_failclosed_and_chunk_invariance():
    coefficients = np.array([[[0, 0, 1.0], [0, 1.0, 0], [0, 0, 0]]])
    coils = fourier_curves(coefficients, 64)
    points = np.array([[0, 0, 0.1], [0.1, 0.3, 0.2], [0.4, 0.5, 0.2]])
    first = filament_field_and_potential(points, coils["positions"], coils["tangents"], [2], 1)
    second = filament_field_and_potential(points, coils["positions"], coils["tangents"], [2], 32)
    for a, b in zip(first, second, strict=True):
        np.testing.assert_array_equal(a, b)
    with pytest.raises(ValueError, match="coincides"):
        filament_field_and_potential(
            coils["positions"][0, :1], coils["positions"], coils["tangents"], [2]
        )
    with pytest.raises(ValueError):
        filament_field_and_potential([[np.nan, 0, 0]], coils["positions"], coils["tangents"], [2])


def test_boundary_normals_full_torus_all_modes_and_shift():
    target = circle_surface()
    target["ntor"] = 2
    target["mpol"] = 4
    target["rbc"].append(dict(m=3, n=-2, value=0.0003))
    surface = boundary(target, 24, 28, full_torus=True, shift=True)
    theta, phi = surface["theta"], surface["phi"]
    phase = 3 * theta + 4 * phi
    radius = 1 + 0.2 * np.cos(theta) + 0.0003 * np.cos(phase)
    np.testing.assert_allclose(np.hypot(*surface["points"][..., :2].transpose(2, 0, 1)), radius)
    np.testing.assert_allclose(surface["dtheta"][..., 2], 2 * np.pi * 0.2 * np.cos(theta))
    np.testing.assert_allclose(np.linalg.norm(surface["unitnormal"], axis=-1), 1)
    assert abs(surface["weights"].sum() - 1) < 1e-14
    bound = surface_derivative_bounds(target)
    assert np.linalg.norm(surface["dtheta"], axis=-1).max() <= bound["theta"]
    assert np.linalg.norm(surface["dphi"], axis=-1).max() <= bound["phi"]
    symmetric = boundary(circle_surface(), 8, 12, full_torus=True)
    assert symmetric["normal"][0, 0, 0] > 0


@pytest.mark.parametrize(
    "change",
    [
        lambda x: x.update(lasym=True),
        lambda x: x["rbc"].append(x["rbc"][0]),
        lambda x: x["rbc"][0].update(value=-3.0),
        lambda x: x["zbs"][0].update(value=np.nan),
        lambda x: x["rbc"][0].update(n=1),
    ],
)
def test_bad_boundary_rejected(change):
    target = circle_surface()
    change(target)
    with pytest.raises(ValueError):
        boundary(target, 8, 16)


def test_metrics_fixed_normalization_and_refinement():
    magnetic = np.array([[0.1, 2, 0], [0.2, 3, 0]])
    normal = np.array([[2, 0, 0], [3, 0, 0]])
    weights = np.array([1.0, 3.0])
    value = metrics(magnetic, normal, weights, 9.0)
    assert value["JN"] == pytest.approx(0.5 * (0.01 / 4 + 0.04 * 3 / 4) / 9)
    expected = np.sqrt((0.01 / 4.01) / 4 + (0.04 / 9.04) * 3 / 4)
    assert value["normal_rms"] == pytest.approx(expected)
    doubled = metrics(2 * magnetic, normal, weights, 9.0)
    assert doubled["JN"] == pytest.approx(4 * value["JN"])
    assert doubled["normal_rms"] == value["normal_rms"]
    inner = inner_metrics(magnetic, magnetic + 1, 9)
    assert inner["JV"] == pytest.approx(1 / 6)
    assert inner["vector_rms"] == pytest.approx(np.sqrt(1 / 3))
    assert refinement_pass(1.0, 1.005)
    assert not refinement_pass(1.0, 1.1)
    assert refinement_pass(0, 1e-8)
    assert not refinement_pass(np.nan, 0)
    with pytest.raises(ValueError):
        metrics(np.zeros((2, 3)), normal, weights, 9)
    with pytest.raises(ValueError):
        inner_metrics(magnetic, magnetic, 0)


def test_penalties_native_formulas_against_dense_synthetic_sum():
    value, target = snapshot(), circle_surface(0.32)
    n = 16
    report = geometry_penalties(value, target, n)
    coils = physical_curves(value, n)
    points, tangents = coils["positions"], coils["tangents"]
    speed = np.linalg.norm(tangents, axis=-1)
    expected = 0
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = np.linalg.norm(points[i, :, None, :] - points[j, None, :, :], axis=-1)
            expected += np.mean(
                np.maximum(0.06 - d, 0) ** 2 * speed[i, :, None] * speed[j, None, :]
            )
    assert report["cc"] == pytest.approx(expected, abs=1e-16)
    surface = boundary(target, 64, 32, full_torus=True)
    area = np.linalg.norm(surface["normal"], axis=-1).ravel()
    plasma = surface["points"].reshape(-1, 3)
    expected = 0
    for p, v in zip(points, speed, strict=True):
        d = np.linalg.norm(p[:, None, :] - plasma[None, :, :], axis=-1)
        expected += np.mean(np.maximum(0.08 - d, 0) ** 2 * v[:, None] * area[None, :])
    assert report["cs"] == pytest.approx(expected, abs=1e-15)
    assert report["length"] == 0 and report["curvature"] == 0


def test_geometry_bounds_dominate_between_node_circle_values():
    value = snapshot()
    report = geometry_certificates(value, circle_surface(0.1), 64, 24, 32)
    assert len(report["coil_pairs"]) == 24 * 23 // 2
    assert len(report["plasma_distances"]) == 24
    assert all(x >= 2 * np.pi * 0.35 for x in report["length_upper"])
    assert all(x >= 1 / 0.35 for x in report["curvature_upper"])
    assert all(x > 0 for x in report["speed_lower"])
    fine = physical_curves(value, 2048)["positions"]
    # Two explicitly paired physical curves, with a much finer independent grid.
    row = report["coil_pairs"][0]
    d = np.linalg.norm(fine[row["i"], :, None, :] - fine[row["j"], None, :, :], axis=-1).min()
    assert row["lower"] <= d <= row["sampled"] + 1e-12
    assert all(r["complete_self_proof"] is False for r in report["self_nearness"])
    assert report["interval_arithmetic"] is False


def test_clearance_bound_catches_between_node_violation():
    value = snapshot()
    c = np.asarray(value["base_coefficients"])
    c[:2] = 0
    c[0, 0, 0] = 1.0
    c[1, 0, 0] = 1.059
    # The curves themselves are parallel circles with exact distance .059m.
    # Half-grid phase offset makes the 64-node distance misleadingly >.06m.
    delta = np.pi / 64
    c[0, 1, 2] = c[0, 2, 1] = 0.35
    c[1, 1, 2] = c[1, 2, 1] = 0.35 * np.cos(delta)
    c[1, 1, 1] = -0.35 * np.sin(delta)
    c[1, 2, 2] = 0.35 * np.sin(delta)
    value["base_coefficients"] = c.tolist()
    report = geometry_certificates(value, circle_surface(0.1), 64, 16, 16)
    pair = report["coil_pairs"][0]
    assert pair["i"] == 0 and pair["j"] == 1
    assert pair["sampled"] > 0.06
    assert pair["lower"] < 0.059


def test_curvature_bound_covers_unsampled_harmonic_peak():
    value = snapshot()
    coefficients = np.asarray(value["base_coefficients"])
    coefficients[0] = 0
    delta = np.pi / 128
    coefficients[0, 0, 0] = 1
    for mode, amplitude in ((1, 0.35), (5, 0.002)):
        coefficients[0, 1, 2 * mode] = amplitude * np.cos(mode * delta)
        coefficients[0, 1, 2 * mode - 1] = -amplitude * np.sin(mode * delta)
        coefficients[0, 2, 2 * mode - 1] = amplitude * np.cos(mode * delta)
        coefficients[0, 2, 2 * mode] = amplitude * np.sin(mode * delta)
    value["base_coefficients"] = coefficients.tolist()
    report = geometry_certificates(value, circle_surface(0.1), 128, 16, 16)
    fine = physical_curves(value, 8192)
    velocity, acceleration = fine["tangents"][0], fine["second"][0]
    fine_curvature = (
        np.linalg.norm(np.cross(velocity, acceleration), axis=-1)
        / np.linalg.norm(velocity, axis=-1) ** 3
    )
    assert fine_curvature.max() > report["curvature_sampled"][0]
    assert fine_curvature.max() <= report["curvature_upper"][0]


def test_degenerate_curve_and_impossible_speed_bound_rejected():
    value = snapshot()
    value["base_coefficients"][0] = np.zeros((3, 11)).tolist()
    with pytest.raises(ValueError, match="speed"):
        physical_curves(value, 32)
    value = snapshot()
    value["base_coefficients"][0][0][10] = 1.0
    with pytest.raises(ValueError, match="speed"):
        geometry_certificates(value, circle_surface(), 8, 8, 8)


def test_figure_eight_self_crossing_rejected_despite_trig_roundoff():
    value = snapshot()
    coefficients = np.asarray(value["base_coefficients"])
    coefficients[0] = 0
    coefficients[0, 0, 0] = 1.0
    coefficients[0, 1, 1] = 0.35
    coefficients[0, 2, 3] = 0.1
    value["base_coefficients"] = coefficients.tolist()
    with pytest.raises(ValueError, match="coincident"):
        geometry_certificates(value, circle_surface(0.1), 128, 16, 16)


def test_entry_never_claims_transfer_or_step4_and_missing_rows_failclosed():
    bounds = dict(geometry_pass=True, ncoil=1024, nphi=256, ntheta=256, full_torus=True)
    bounds.update(
        length_upper=[3.0] * 24,
        curvature_upper=[8.0] * 24,
        speed_lower=[1.0] * 24,
        coil_pairs=[dict(i=i, j=j, lower=0.07) for i in range(24) for j in range(i + 1, 24)],
        plasma_distances=[dict(i=i, lower=0.09) for i in range(24)],
        self_nearness=[
            dict(i=i, exact_repeated_node=False, sampled_nonlocal_minimum=0.1) for i in range(24)
        ],
    )
    b = [dict(normal_rms=1e-5, normal_max=1e-4) for _ in range(4)]
    inner = [dict(vector_rms=1e-3) for _ in range(3)]
    flux = [dict(relative_error=1e-8, stokes_error=1e-8, angular_error=1e-8) for _ in range(6)]
    refinements = [(1.0, 1.001)] * 5
    result = entry_gates(snapshot(), b, inner, flux, bounds, refinements, [True])
    assert result["entry_pass"] is True
    assert result["transfer_pass"] is False and result["step4_pass"] is False
    assert not entry_gates(snapshot(), b[:-1], inner, flux, bounds, refinements, [True])[
        "entry_pass"
    ]
    broken = copy.deepcopy(bounds)
    broken["coil_pairs"][0]["lower"] = 0.05
    assert not entry_gates(snapshot(), b, inner, flux, broken, refinements, [True])["entry_pass"]
    broken = copy.deepcopy(bounds)
    broken["coil_pairs"].pop()
    assert not entry_gates(snapshot(), b, inner, flux, broken, refinements, [True])["entry_pass"]
    broken = dict(geometry_pass=True, ncoil=1024, nphi=256, ntheta=256, full_torus=True)
    assert not entry_gates(snapshot(), b, inner, flux, broken, refinements, [True])["entry_pass"]
    b[0]["normal_rms"] = np.nan
    assert not entry_gates(snapshot(), b, inner, flux, bounds, refinements, [True])["entry_pass"]
