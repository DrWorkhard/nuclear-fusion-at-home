"""Synthetic mathematical controls, without project Wouts or target fields."""

import copy
import json

import numpy as np
import pytest

from fusion_baselines import clear_coil_field_audit as audit
from fusion_baselines import clear_coil_geometry_audit as geometry
from fusion_baselines import coupled_coil_audit as frozen


def torus(radius=0.30):
    return dict(
        lasym=False,
        nfp=2,
        mpol=2,
        ntor=0,
        rbc=[dict(m=0, n=0, value=1.0), dict(m=1, n=0, value=radius)],
        zbs=[dict(m=1, n=0, value=radius)],
    )


def synthetic_snapshot(nbase=6, order=5, active_pair=True):
    coefficients = np.zeros((nbase, 3, 2 * order + 1))
    for i in range(nbase):
        phi = (i + 0.5) * np.pi / (2 * nbase)
        if i == 1 and active_pair:
            phi = 0.5 * np.pi / (2 * nbase) + 0.02
        coefficients[i, :, 0] = [np.cos(phi), np.sin(phi), 0]
        coefficients[i, :, 2] = 0.325 * np.array([np.cos(phi), np.sin(phi), 0])
        coefficients[i, 2, 1] = -0.325
    scale, unit_flux = 0.25, 0.125
    physical = geometry.physical_rows(nbase)
    for row in physical:
        row["current"] = 1e5 * scale * (-1 if row["flip"] else 1)
    return dict(
        schema_version=1,
        nfp=2,
        nbase=nbase,
        order=order,
        method="N",
        names=frozen.parameter_names(nbase, order),
        base_coefficients=coefficients.tolist(),
        physical=physical,
        scale=scale,
        unit_flux=unit_flux,
        target_flux=scale * unit_flux,
        seed_unit_flux=unit_flux,
        B2_scale=1.0,
        construction=dict(
            ncoil=256,
            nphi=64,
            ntheta=64,
            ninner=32,
            offset=0,
            nloop=256,
            geometry_nphi=128,
            geometry_ntheta=128,
            geometry_full_torus=True,
            geometry_offset=0,
        ),
        sources={},
    )


def archives():
    phi, theta = np.meshgrid(
        np.pi * np.arange(64) / 64, 2 * np.pi * np.arange(64) / 64, indexing="ij"
    )
    rows = []
    for s in (0.25, 0.5, 0.75):
        radius = 1 + 0.3 * np.sqrt(s) * np.cos(theta)
        height = 0.3 * np.sqrt(s) * np.sin(theta)
        et = np.stack((np.zeros_like(phi), np.zeros_like(phi), np.ones_like(phi)), axis=-1)
        ep = np.stack((-np.sin(phi), np.cos(phi), np.zeros_like(phi)), axis=-1)
        bt = np.full_like(phi, 0.02 * s)
        bp = 1 + 0.1 * np.cos(32 * theta)
        native = bt[..., None] * et + bp[..., None] * ep
        rows.append(
            dict(
                s=s,
                n=64,
                arrays=dict(
                    phi=phi.copy(),
                    theta=theta.copy(),
                    radius=radius,
                    height=height,
                    et=et,
                    ep=ep,
                    bt=bt,
                    bp=bp,
                    native=native,
                ),
            )
        )
    return rows


def test_exact_four_physical_eight_methods_and_six_registered_levels():
    assert len(audit.physical_cases()) == 4 and len(audit.cases()) == 8
    assert [c["method"] for c in audit.cases()] == ["N", "V"] * 4
    assert [c["seed_label"] for c in audit.physical_cases()] == [
        "n6-shape-d100mm",
        "n8-shape-d100mm",
    ] * 2
    assert [(r["nphi"], r["ncoil"], r["ninner"], r["offset"]) for r in audit.levels()] == [
        (64, 256, 32, 0),
        (128, 256, 32, 0),
        (128, 512, 32, 0),
        (128, 512, 32, 0.5),
        (64, 256, 64, 0),
        (64, 512, 64, 0),
    ]


def test_archived64_b2_is_fixed_when32_subsample_has_different_field_energy():
    source = archives()
    coarse, fine = [audit.archived_target(source, n) for n in (32, 64)]
    assert coarse["B2_scale"] == fine["B2_scale"]
    assert not np.isclose(coarse["B2_scale"], np.mean(np.sum(coarse["inner_target"] ** 2, axis=1)))
    for key in ("inner_points", "inner_target"):
        np.testing.assert_array_equal(
            coarse[key], fine[key].reshape(3, 64, 64, 3)[:, ::2, ::2].reshape(-1, 3)
        )
    assert coarse["inner_points"].shape == (3 * 32**2, 3)
    assert coarse["radii"] == [0.25, 0.5, 0.75]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda a: a.pop(),
        lambda a: a.reverse(),
        lambda a: a[0].update(n=128),
        lambda a: a[0].update(n=64.0),
        lambda a: a[0].update(s=0.3),
        lambda a: a[0]["arrays"].update(phi=a[0]["arrays"]["phi"] + 1e-8),
        lambda a: a[0]["arrays"].update(theta=a[0]["arrays"]["theta"] + 1e-8),
        lambda a: a[0]["arrays"].update(native=a[0]["arrays"]["native"] + 1e-6),
        lambda a: a[0]["arrays"].update(radius=-a[0]["arrays"]["radius"]),
        lambda a: a[0]["arrays"].update(ep=a[0]["arrays"]["ep"][::2]),
        lambda a: a[0]["arrays"].update(bp=np.full((64, 64), np.nan)),
        lambda a: a[0]["arrays"].update(bp=np.full((64, 64), 1j)),
    ],
)
def test_archive_identity_or_coordinate_mutation_fails(mutation):
    value = archives()
    mutation(value)
    with pytest.raises((ValueError, KeyError)):
        audit.archived_target(value, 32)


@pytest.mark.parametrize("n", [16, 128, True, 32.0])
def test_unqualified_inner_grid_not_substituted(n):
    with pytest.raises(ValueError):
        audit.archived_target(archives(), n)


def test_distance_penalty_matches_dense_sum_and_true_minimum():
    rng = np.random.default_rng(401)
    left, right = rng.uniform(0, 0.2, (13, 3)), rng.uniform(0, 0.2, (27, 3))
    vl, vr = rng.uniform(0.3, 2, 13), rng.uniform(0.4, 3, 27)
    value = audit.distance_penalty(left, right, vl, vr, 0.08)
    distance = np.linalg.norm(left[:, None] - right, axis=-1)
    expected = np.mean(vl[:, None] * vr * np.maximum(0.08 - distance, 0) ** 2)
    assert expected > 0
    assert value["value"] == pytest.approx(expected, rel=2e-15)
    assert value["minimum"] == pytest.approx(distance.min(), rel=2e-15)


def test_outward_broadphase_does_not_change_hinge_or_drop_near_threshold_pairs():
    left = np.array([[0.0, 0.0, 0.0]])
    right = np.array([[0.08 - 1e-15, 0.0, 0.0], [0.08, 0.0, 0.0], [0.08 + 1e-15, 0.0, 0.0]])
    result = audit.distance_penalty(left, right, [2.0], [3.0, 4.0, 5.0], 0.08)
    assert result["value"] == pytest.approx(2 * 3 * (0.08 - right[0, 0]) ** 2 / 3, rel=1e-15)
    assert result["value"] > 0


@pytest.mark.parametrize("fault", ["coincidence", "zero_weight", "nan", "complex", "wrong_tree"])
def test_distance_degeneracy_is_explicit(fault):
    from scipy.spatial import cKDTree

    left, right, weights = np.array([[0.0, 0.0, 0.0]]), np.array([[0.1, 0.0, 0.0]]), [1.0]
    tree = None
    if fault == "coincidence":
        right[:] = 0
    if fault == "zero_weight":
        weights = [0.0]
    if fault == "nan":
        right[0, 0] = np.nan
    if fault == "complex":
        right = right.astype(complex)
    if fault == "wrong_tree":
        tree = cKDTree([[10.0, 0.0, 0.0]])
    with pytest.raises(ValueError):
        audit.distance_penalty(left, right, weights, [1.0], 0.08, tree)


def test_native_small_active_cp_and_cc_values_have_independent_dense_countercheck():
    from simsopt.geo import (
        CurveCurveDistance,
        CurveSurfaceDistance,
        CurveXYZFourier,
        SurfaceRZFourier,
    )

    from fusion_baselines.sparse_coil_surface import SparseCurveSurfaceDistance

    curves = []
    for shift in (0.0, 0.02):
        c = CurveXYZFourier(48, 3)
        c.set("xc(0)", 1.0)
        c.set("yc(0)", shift)
        c.set("xc(1)", 0.325)
        c.set("zs(1)", -0.325)
        curves.append(c)
    surface = SurfaceRZFourier(
        nfp=2,
        stellsym=True,
        mpol=1,
        ntor=0,
        quadpoints_phi=np.arange(24) / 24,
        quadpoints_theta=np.arange(20) / 20,
    )
    surface.set_rc(0, 0, 1.0)
    surface.set_rc(1, 0, 0.30)
    surface.set_zs(1, 0, 0.30)
    surface.fix_all()
    p, area = surface.gamma().reshape(-1, 3), np.linalg.norm(surface.normal(), axis=-1).ravel()
    values = [
        audit.distance_penalty(c.gamma(), p, np.linalg.norm(c.gammadash(), axis=1), area, 0.08)
        for c in curves
    ]
    cp = sum(v["value"] for v in values)
    sparse = SparseCurveSurfaceDistance(curves, p, surface.normal().reshape(-1, 3), 0.08)
    assert cp > 0 and cp == pytest.approx(
        CurveSurfaceDistance(curves, surface, 0.08).J(), rel=5e-10, abs=1e-12
    )
    assert cp == pytest.approx(sparse.J(), rel=5e-10, abs=1e-12)
    cc = audit.distance_penalty(
        curves[0].gamma(),
        curves[1].gamma(),
        np.linalg.norm(curves[0].gammadash(), axis=1),
        np.linalg.norm(curves[1].gammadash(), axis=1),
        0.06,
    )
    assert cc["value"] > 0 and cc["value"] == pytest.approx(
        CurveCurveDistance(curves, 0.06).J(), rel=5e-10, abs=1e-12
    )


@pytest.mark.parametrize("nbase,order,ncoil", [(6, 5, 256), (6, 5, 512), (8, 7, 256), (8, 7, 512)])
def test_registered_geometry_complete_copies_and_active128_surface(nbase, order, ncoil):
    from simsopt.geo import CurveXYZFourier

    from fusion_baselines.sparse_coil_surface import SparseCurveSurfaceDistance

    snap = synthetic_snapshot(nbase, order)
    report = audit.geometry_penalties(snap, torus(), ncoil)
    physical = frozen.physical_curves(snap, ncoil)
    curves = []
    for coefficient in physical["coefficients"]:
        curve = CurveXYZFourier(ncoil, order)
        curve.local_full_x = coefficient.ravel().copy()
        curves.append(curve)
    surface = frozen.boundary(torus(), 128, 128, full_torus=True)
    sparse = SparseCurveSurfaceDistance(
        curves, surface["points"].reshape(-1, 3), surface["normal"].reshape(-1, 3), 0.08
    )
    assert report["cc"] > 0 and report["cs"] > 0
    assert report["cs"] == pytest.approx(sparse.J(), rel=5e-10, abs=1e-12)
    assert report["surface_distance"] == pytest.approx(sparse.shortest_distance(), abs=1e-14)
    assert report["geometry_nphi"] == report["geometry_ntheta"] == 128
    assert len(report["lengths"]) == nbase and sparse.stats()["physical_curves"] == 4 * nbase
    json.dumps(report, allow_nan=False)


def raw_state():
    data, snap = torus(), synthetic_snapshot(active_pair=False)
    target = audit.archived_target(archives(), 32)
    snap["B2_scale"] = target["B2_scale"]
    surface = frozen.boundary(data, 64, 64)
    curves = frozen.physical_curves(snap, 256)
    lp, lt = frozen.loop(data, 256)
    points = surface["points"].reshape(-1, 3)
    phi = surface["phi"].ravel()
    raw = dict(
        boundary_points=points,
        boundary_normals=surface["unitnormal"].reshape(-1, 3),
        boundary_weights=surface["weights"].ravel(),
        boundary_B=np.stack((-np.sin(phi), np.cos(phi), np.full_like(phi, 0.03)), axis=-1),
        boundary_A=np.ones_like(points),
        inner_points=target["inner_points"],
        inner_target=target["inner_target"],
        inner_B=target["inner_target"] + 0.01,
        inner_A=np.ones_like(target["inner_points"]),
        loop_points=lp,
        loop_tangents=lt,
        loop_A=lt * snap["target_flux"] / np.mean(np.sum(lt**2, axis=1)),
        loop_B=np.ones_like(lp),
        coil_positions=curves["positions"],
        coil_tangents=curves["tangents"],
        coil_currents=curves["currents"],
    )
    return data, snap, target, raw


def test_composed_objective_metrics_use_raw_fields_and_frozen64_scale():
    data, snap, target, raw = raw_state()
    n = audit.composed_metrics(snap, data, raw, target, "N")
    v = audit.composed_metrics(snap, data, raw, target, "V")
    assert n["B2_scale"] == target["B2_scale"]
    assert v["J"] - n["J"] == pytest.approx(0.05 * n["JV"], abs=1e-14)
    assert n["JV"] == pytest.approx(0.5 * 0.0003 / target["B2_scale"], rel=1e-13)
    assert n["flux"] == pytest.approx(snap["target_flux"], rel=1e-14)
    assert n["J"] == n["JN"] + n["geometry_penalty"]
    json.dumps(v, allow_nan=False)


@pytest.mark.parametrize("fault", ["b2", "target", "point", "loop", "coil", "current", "mode"])
def test_composed_identity_rejects_mutated_inputs_before_numeric_admission(fault):
    data, snap, target, raw = raw_state()
    if fault == "b2":
        snap["B2_scale"] *= 2
    elif fault == "mode":
        data["rbc"][0]["value"] = "1.0"
    else:
        key = dict(
            target="inner_target",
            point="inner_points",
            loop="loop_tangents",
            coil="coil_positions",
            current="coil_currents",
        )[fault]
        raw[key] = raw[key].copy()
        raw[key].flat[0] += 1e-4
    with pytest.raises((ValueError, TypeError)):
        audit.composed_metrics(snap, data, raw, target, "N")


def quadratic_rows():
    seed = np.linspace(0.001, 0.05, 33)
    rows = [
        dict(status="completed", x=x, J=float(x @ x), gradient=2 * x)
        for x in audit.qualification_points(seed)
    ]
    return seed, rows


def test_all_ten_ordered_fd_rows_and_exact_repeat():
    seed, rows = quadratic_rows()
    result = audit.derivative_checks(rows, seed, [r["J"] for r in rows])
    assert result["passed"] and result["exact_repeat"] and len(result["checks"]) == 8
    assert {r["step"] for r in result["checks"]} == {1e-5, 5e-6}
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "fault", ["missing", "swap", "gradient", "repeat", "own", "complex", "status"]
)
def test_fd_failure_or_missing_probe_cannot_be_hidden(fault):
    seed, rows = quadratic_rows()
    if fault == "missing":
        rows.pop(1)
    if fault == "swap":
        rows[1], rows[2] = rows[2], rows[1]
    if fault == "gradient":
        rows[0]["gradient"] *= 2
        rows[-1]["gradient"] *= 2
    if fault == "repeat":
        rows[-1]["gradient"][0] += 1e-15
    if fault == "complex":
        rows[0]["gradient"] = rows[0]["gradient"].astype(complex)
    if fault == "status":
        rows[1]["status"] = "failed"
    own = [r["J"] for r in rows]
    if fault == "own":
        own[1] += 0.01
    if fault in ("gradient", "repeat"):
        assert not audit.derivative_checks(rows, seed, own)["passed"]
    else:
        with pytest.raises(ValueError):
            audit.derivative_checks(rows, seed, own)


def identity_rows():
    _, snap, _, raw = raw_state()
    metric = dict(
        J=1.0,
        JN=0.1,
        JV=0.2,
        scale=snap["scale"],
        B2_scale=snap["B2_scale"],
        unit_flux=snap["unit_flux"],
        target_flux=snap["target_flux"],
        flux=snap["target_flux"],
        current=1e5 * snap["scale"],
        normal_rms=0.2,
        normal_max=0.3,
        vector_rms=0.4,
        boundary_B_rms=1.0,
        lengths=[2.0] * 6,
        kappa_max=[3.0] * 6,
        coil_distance=0.1,
        surface_distance=0.1,
        geometry_penalty=0.0,
        frozen_scale=False,
    )
    normal = dict(status="completed", snapshot=snap, arrays=raw, metrics=metric, gradient=[1.0])
    vector = copy.deepcopy(normal)
    vector["snapshot"]["method"] = "V"
    vector["metrics"]["J"] = 2.0
    vector["gradient"] = [5.0]
    return normal, vector


def test_n_v_identity_excludes_only_intentionally_different_j_and_gradient():
    normal, vector = identity_rows()
    result = audit.physical_identity(normal, vector)
    assert result["passed"] and result["search_allowed"] is False and result["step4_pass"] is False
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "fault", ["field", "missing", "b2", "metrics", "sources", "method", "seed_flag"]
)
def test_n_v_physical_identity_is_exact_complete_and_source_bound(fault):
    normal, vector = identity_rows()
    if fault == "field":
        vector["arrays"]["inner_B"].flat[0] += 1e-15
    if fault == "missing":
        vector["arrays"].pop("loop_B")
    if fault == "b2":
        vector["snapshot"]["B2_scale"] *= 2
    if fault == "metrics":
        vector["metrics"].pop("unit_flux")
    if fault == "sources":
        vector["snapshot"]["sources"] = {"changed": True}
    if fault == "method":
        vector["snapshot"]["method"] = "N"
    if fault == "seed_flag":
        vector["metrics"]["frozen_scale"] = np.bool_(False)
    with pytest.raises(ValueError):
        audit.physical_identity(normal, vector)


def refinement_rows():
    return [
        dict(status="completed", level=level, metrics=dict(normal_rms=0.2, vector_rms=0.3))
        for level in audit.levels()
    ]


def test_five_fixed_refinements_typed_and_no_hidden_physical_pass():
    rows = refinement_rows()
    result = audit.refinement_checks(rows)
    assert result["passed"] and len(result["checks"]) == 5
    assert [(c["coarse_level"], c["fine_level"]) for c in result["checks"]] == [
        (0, 1),
        (1, 2),
        (2, 3),
        (0, 4),
        (4, 5),
    ]
    rows[3]["metrics"]["normal_rms"] += 0.01
    result = audit.refinement_checks(rows)
    assert not result["passed"] and not result["checks"][2]["passed"]
    assert result["search_allowed"] is result["transfer_pass"] is result["step4_pass"] is False
    assert type(result["checks"][2]["passed"]) is bool
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "fault", ["missing", "swap", "grid", "status", "nan", "float_grid", "bool_offset"]
)
def test_refinement_grid_identity_and_completeness(fault):
    rows = refinement_rows()
    if fault == "missing":
        rows.pop()
    if fault == "swap":
        rows[2], rows[3] = rows[3], rows[2]
    if fault == "grid":
        rows[3]["level"]["offset"] = 0
    if fault == "status":
        rows[3]["status"] = "failed"
    if fault == "nan":
        rows[1]["metrics"]["normal_rms"] = np.nan
    if fault == "float_grid":
        rows[0]["level"]["nphi"] = 64.0
    if fault == "bool_offset":
        rows[0]["level"]["offset"] = False
    with pytest.raises(ValueError):
        audit.refinement_checks(rows)


def test_currentless_seed_is_not_a_magnetic_snapshot_and_sources_must_match():
    snap = synthetic_snapshot()
    sources = {
        label: {
            key: dict(path=f"/synthetic/{label}-{key}", sha256="a" * 64)
            for key in ("input", "wout")
        }
        for label in ("reference", "selected")
    }
    case = next(c for c in geometry.cases() if c["label"] == "n6-shape-d100mm")
    seed = {
        k: copy.deepcopy(snap[k])
        for k in ("schema_version", "nfp", "nbase", "order", "names", "base_coefficients")
    }
    seed.update(
        kind="geometry-only",
        case=case,
        sources=sources,
        physical=geometry.physical_rows(6),
        parameter_orientation="alpha=-2*pi*t",
    )
    snap.update(seed_geometry=copy.deepcopy(seed), sources=sources["reference"])
    assert audit.seed_identity(snap, seed, sources["reference"])
    with pytest.raises((ValueError, KeyError)):
        audit.validate_snapshot(seed)
    with pytest.raises(ValueError):
        audit.seed_identity(snap, seed, sources["selected"])
    changed = copy.deepcopy(snap)
    changed["base_coefficients"][0][0][0] += 1e-15
    with pytest.raises(ValueError):
        audit.seed_identity(changed, seed, sources["reference"])
    circle = copy.deepcopy(seed)
    circle["case"] = next(c for c in geometry.cases() if c["label"] == "n6-circle-d100mm")
    changed = copy.deepcopy(snap)
    changed["seed_geometry"] = circle
    with pytest.raises(ValueError):
        audit.seed_identity(changed, circle, sources["reference"])


def test_json_scalar_normalization_does_not_repeat_historical_np_bool_bug():
    normalized = audit.json_value(
        dict(flags=[np.bool_(False), np.bool_(True)], value=np.float64(0.25))
    )
    assert normalized["flags"][0] is False and normalized["flags"][1] is True
    assert json.loads(json.dumps(normalized, allow_nan=False)) == normalized
    for bad in (np.nan, np.inf, np.complex128(1j), object()):
        with pytest.raises(ValueError):
            audit.json_value(bad)
