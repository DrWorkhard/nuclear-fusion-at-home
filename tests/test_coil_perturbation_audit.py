"""Pure synthetic perturbation proofs; no project target or native field calls."""

import copy
import json
import math

import numpy as np
import pytest

from fusion_baselines import clear_coil_geometry_audit as frozen
from fusion_baselines import coil_perturbation_audit as audit


def synthetic_seed(nbase=6):
    case = next(c for c in frozen.cases() if c["label"] == f"n{nbase}-shape-d100mm")
    order, k = case["order"], case["K"]
    coefficients, coils = [], []
    h = np.zeros(2 * k + 1)
    h[0] = 0.2
    center = np.array([1.2, 0.0])
    model = dict(K=k, nangle=1024, angles=2 * np.pi * np.arange(1024) / 1024)
    disks = dict(centers=np.zeros((1, 2)), radii=np.array([0.15]))
    for i in range(nbase):
        phi = (i + 0.5) * np.pi / (2 * nbase)
        coefficient = frozen.export_coefficients(h, center, phi, order)
        continuous = frozen.continuous_certificate(model, h, disks, center, case["r_floor"])
        exported = frozen.export_certificate(
            continuous, h, coefficient, coefficient, case["r_floor"], case["d"]
        )
        coefficients.append(coefficient.tolist())
        lp = dict(
            solved=True,
            passed=True,
            infeasibility_proven=False,
            objective=float(2 * np.pi * h[0]),
            dual_objective=float(2 * np.pi * h[0]),
            errors={
                key: 0.0
                for key in (
                    "primal",
                    "dual_sign",
                    "stationarity",
                    "complementarity",
                    "primal_dual_gap",
                    "reported_objective",
                    "reported_slack",
                )
            },
        )
        coils.append(
            dict(
                base_index=i,
                available_geometry=True,
                exact_repeat=True,
                lp_certificates=[copy.deepcopy(lp), copy.deepcopy(lp)],
                support_coefficients=h.tolist(),
                continuous=continuous,
                export_transfer=exported,
            )
        )
    snapshot = dict(
        schema_version=1,
        kind="geometry-only",
        nfp=2,
        nbase=nbase,
        order=order,
        names=frozen.parameter_names(nbase, order),
        base_coefficients=coefficients,
        physical=frozen.physical_rows(nbase),
        case=case,
        parameter_orientation="alpha=-2*pi*t",
        sources={
            target: {
                kind: dict(path=f"/synthetic/{target}/{kind}", sha256="a" * 64)
                for kind in ("input", "wout")
            }
            for target in ("reference", "selected")
        },
    )
    distances = []
    count = 4 * nbase
    cover, surface_cover, pad = 0.005, 0.035, 5e-14
    for target in ("reference", "selected"):
        for n, shift in ((256, 0), (512, 0), (512, 0.5)):
            distances.append(
                dict(
                    target=target,
                    ncoil=1024,
                    nphi=n,
                    ntheta=n,
                    offset=shift,
                    full_torus=True,
                    interval_arithmetic=False,
                    coil_pass=True,
                    plasma_pass=True,
                    sampled_length_pass=True,
                    sampled_curvature_pass=True,
                    curve_cover=[cover] * count,
                    surface_cover=surface_cover,
                    floating_pad=pad,
                    lengths_sampled=[2 * np.pi * 0.2] * count,
                    curvature_sampled=[5.0] * count,
                    plasma_distances=[
                        dict(i=i, sampled=0.12 + cover + surface_cover + pad, lower=0.12)
                        for i in range(count)
                    ],
                    coil_pairs=[
                        dict(i=i, j=j, sampled=0.15 + 2 * cover + pad, lower=0.15)
                        for i in range(count)
                        for j in range(i + 1, count)
                    ],
                )
            )
    radial_min = min(c["continuous"]["radial_lower"] for c in coils)
    export_error = max(
        c["export_transfer"]["position_error"] + c["export_transfer"]["coefficient_rounding_pad"]
        for c in coils
    )
    report = dict(
        case=case,
        geometry_pass=True,
        available_geometry=True,
        coils=coils,
        distances=distances,
        sum_base_lengths=nbase * 2 * np.pi * 0.2,
        analytic_coil_lower=2 * radial_min * np.sin(np.pi / (4 * nbase)) - 2 * export_error,
    )
    return snapshot, report


def change_lower(distance, lower):
    distance["sampled"] += lower - distance["lower"]
    distance["lower"] = lower


@pytest.fixture(scope="module", params=[6, 8])
def seed(request):
    return synthetic_seed(request.param)


def evaluate(coefficients, points):
    """Independent direct trigonometric derivatives with normalized t."""
    c = np.asarray(coefficients)
    out = []
    for derivative in range(3):
        value = np.zeros((len(points), 3))
        if derivative == 0:
            value += c[:, 0]
        for m in range(1, (c.shape[1] - 1) // 2 + 1):
            angle = 2 * np.pi * m * points + derivative * np.pi / 2
            value += (2 * np.pi * m) ** derivative * (
                np.sin(angle)[:, None] * c[:, 2 * m - 1] + np.cos(angle)[:, None] * c[:, 2 * m]
            )
        out.append(value)
    return out


def test_seed_certified_json_types_and_complete_physical_pairs(seed):
    snapshot, report = seed
    result = audit.independent_certificate(snapshot, report, snapshot["base_coefficients"])
    assert result["certified"] and result["calculation_complete"]
    assert all(result["gates"].values())
    n = 4 * snapshot["nbase"]
    assert len(result["curves"]) == n
    assert len(result["pairs"]) == n * (n - 1) // 2
    assert all(len(rows) == n for rows in result["plasma"].values())
    assert result["field_calls"] == result["gradient_calls"] == result["equilibrium_solves"] == 0
    assert not any(
        result[k] for k in ("field_pass", "step4_pass", "search_allowed", "transfer_pass")
    )
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    assert (
        audit.audit_certificate(snapshot, report, snapshot["base_coefficients"], result) == result
    )


def test_translation_consumes_only_position_and_roundoff(seed):
    snapshot, report = seed
    candidate = np.array(snapshot["base_coefficients"])
    candidate[0, 2, 0] += 0.005
    result = audit.independent_certificate(snapshot, report, candidate)
    assert result["certified"]
    changed = result["curves"][0]
    assert 0.005 < changed["D0"] < 0.005 + 1e-10
    assert 0 < changed["D1"] < 1e-8 and 0 < changed["D2"] < 1e-7
    assert result["plasma"]["reference"][0]["analytic_lower"] < 0.095


def test_one_ulp_change_never_produces_negative_error_bound(seed):
    snapshot, report = seed
    candidate = np.array(snapshot["base_coefficients"])
    candidate[0, 0, 0] = np.nextafter(candidate[0, 0, 0], -np.inf)
    result = audit.independent_certificate(snapshot, report, candidate)
    assert result["certified"]
    assert all(c[k] > 0 for c in result["curves"] for k in ("D0", "D1", "D2"))


@pytest.mark.parametrize("amplitude", [1e-5, -1e-5, 1e-3, -1e-3, 0.03])
def test_high_mode_direct_derivatives_and_certified_curvature_enclosed(seed, amplitude):
    snapshot, report = seed
    c0 = np.array(snapshot["base_coefficients"])
    c1 = c0.copy()
    c1[0, 2, -2] += amplitude
    result = audit.independent_certificate(snapshot, report, c1)
    t = (np.arange(1024) + 0.5) / 1024
    for row, mapping in zip(result["curves"], snapshot["physical"], strict=True):
        q = np.array(mapping["matrix"]).T
        initial = evaluate(q @ c0[mapping["base_index"]], t)
        actual = evaluate(q @ c1[mapping["base_index"]], t)
        for derivative in range(3):
            assert (
                np.max(np.linalg.norm(actual[derivative] - initial[derivative], axis=1))
                <= row[f"D{derivative}"]
            )
        cross = np.cross(actual[1], actual[2])
        speed = np.linalg.norm(actual[1], axis=1)
        assert speed.min() >= row["v_lower"]
        assert (cross @ row["normal"]).min() >= row["S_lower"]
        if row["kappa_upper"] is not None:
            assert (np.linalg.norm(cross, axis=1) / speed**3).max() <= row["kappa_upper"]
        assert speed.mean() - np.linalg.norm(initial[1], axis=1).mean() <= row["D1"]


def test_negative_speed_retains_finite_other_bounds_without_division(seed):
    snapshot, report = seed
    candidate = np.array(snapshot["base_coefficients"])
    candidate[0, 2, -2] += 1.0
    result = audit.independent_certificate(snapshot, report, candidate)
    assert result["status"] == "uncertified" and result["calculation_complete"]
    row = result["curves"][0]
    assert row["v_lower"] < 0 and row["kappa_upper"] is None
    assert row["kappa_status"] == "not_available"
    assert row["D0"] > 0 and row["D1"] > 0 and row["D2"] > 0
    assert not row["length_pass"] and not row["curvature_pass"]
    json.dumps(result, allow_nan=False)


def test_direct_and_analytic_distance_gates_both_required(seed):
    snapshot, report = seed
    candidate = np.array(snapshot["base_coefficients"])
    candidate[0, 2, 0] += 0.021
    result = audit.independent_certificate(snapshot, report, candidate)
    assert result["gates"]["direct_plasma"]
    assert not result["gates"]["analytic_plasma"]
    assert not result["certified"]
    altered = copy.deepcopy(report)
    change_lower(altered["distances"][0]["plasma_distances"][0], 0.081)
    candidate[0, 2, 0] -= 0.019
    result = audit.independent_certificate(snapshot, altered, candidate)
    assert not result["gates"]["direct_plasma"]
    assert result["gates"]["analytic_plasma"]


def test_minimum_all_source_grids_not_most_favorable(seed):
    snapshot, report = seed
    altered = copy.deepcopy(report)
    change_lower(altered["distances"][1]["plasma_distances"][0], 0.085)
    change_lower(altered["distances"][4]["coil_pairs"][0], 0.065)
    result = audit.independent_certificate(snapshot, altered, snapshot["base_coefficients"])
    assert result["plasma"]["reference"][0]["direct_seed_lower"] == 0.085
    assert result["pairs"][0]["direct_seed_lower"] == 0.065


def test_pair_budget_consumes_both_changed_physical_coils(seed):
    snapshot, report = seed
    altered = copy.deepcopy(report)
    for row in altered["distances"]:
        change_lower(row["coil_pairs"][0], 0.065)
    candidate = np.array(snapshot["base_coefficients"])
    candidate[:2, 2, 0] += 0.003
    result = audit.independent_certificate(snapshot, altered, candidate)
    pair = result["pairs"][0]
    assert pair["direct_lower"] < 0.059 and not pair["direct_pass"]
    assert not result["certified"]


def test_cumulative_endpoint_identical_no_reset_at_intermediate(seed):
    snapshot, report = seed
    candidate = np.array(snapshot["base_coefficients"])
    delta = np.zeros_like(candidate)
    delta[0, 2, 0] = 0.005
    for factor in range(1, 6):
        endpoint = candidate + factor * delta
        result = audit.independent_certificate(snapshot, report, endpoint)
        direct = audit.independent_certificate(snapshot, report, candidate + factor * delta)
        assert result == direct
    assert not result["certified"]
    assert result["curves"][0]["D0"] > 0.025


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf, 1e308])
def test_nonfinite_or_overflow_is_json_safe_uncertified(seed, bad):
    snapshot, report = seed
    candidate = np.array(snapshot["base_coefficients"])
    candidate[0, 2, -2] = bad
    result = audit.independent_certificate(snapshot, report, candidate)
    assert not result["certified"] and not result["calculation_complete"]
    assert not result["curves"] and not any(result["gates"].values())
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("bad", ["shape", "complex", "string", "bool"])
def test_bad_candidate_schema_raises(seed, bad):
    snapshot, report = seed
    candidate = np.array(snapshot["base_coefficients"])
    if bad == "shape":
        candidate = candidate.ravel()
    else:
        candidate = candidate.astype({"complex": complex, "string": str, "bool": bool}[bad])
    with pytest.raises(ValueError):
        audit.independent_certificate(snapshot, report, candidate)


@pytest.mark.parametrize(
    "bad",
    [
        "name",
        "source",
        "map",
        "orientation",
        "support_missing",
        "projection_false",
        "rho",
        "double_circle",
        "distance_missing",
        "pair_identity",
        "report_case",
        "nonfinite_seed",
    ],
)
def test_missing_or_false_seed_proof_never_inherited(seed, bad):
    snapshot, report = map(copy.deepcopy, seed)
    if bad == "name":
        snapshot["names"][0] = "unknown"
    elif bad == "source":
        snapshot["sources"]["reference"] = {}
    elif bad == "map":
        snapshot["physical"][1]["base_index"] = 0
    elif bad == "orientation":
        snapshot["parameter_orientation"] = "alpha=2*pi*t"
    elif bad == "support_missing":
        del report["coils"][0]["support_coefficients"]
    elif bad == "projection_false":
        report["coils"][0]["export_transfer"]["controlled_projection_self_disjoint"] = False
    elif bad == "rho":
        report["coils"][0]["continuous"]["rho_lower"] = 0.3
    elif bad == "double_circle":
        c = np.array(snapshot["base_coefficients"])
        c[0, :, 3:5] = c[0, :, 1:3]
        c[0, :, 1:3] = 0
        snapshot["base_coefficients"] = c.tolist()
    elif bad == "distance_missing":
        report["distances"].pop()
    elif bad == "pair_identity":
        report["distances"][0]["coil_pairs"][0]["j"] = 2
    elif bad == "report_case":
        report["case"] = dict(report["case"], label="other")
    else:
        snapshot["base_coefficients"][0][0][0] = float("nan")
    with pytest.raises(ValueError):
        audit.independent_certificate(snapshot, report, snapshot["base_coefficients"])


@pytest.mark.parametrize("bad", ["missing", "flag", "numpy_bool", "number", "normal", "scope"])
def test_recorded_certificate_mutations_rejected(seed, bad):
    snapshot, report = seed
    result = audit.independent_certificate(snapshot, report, snapshot["base_coefficients"])
    if bad == "missing":
        del result["curves"][0]["D2"]
    elif bad == "flag":
        result["certified"] = False
    elif bad == "numpy_bool":
        result["certified"] = np.bool_(True)
    elif bad == "number":
        result["curves"][0]["D2"] += 1e-6
    elif bad == "normal":
        result["curves"][0]["normal"][0] *= -1
    else:
        result["search_allowed"] = True
    with pytest.raises(ValueError):
        audit.audit_certificate(snapshot, report, snapshot["base_coefficients"], result)


def test_scalar_comparison_is_relative_or_absolute_not_their_sum():
    audit.close(1.0 + 4e-12, 1.0, "relative")
    audit.close(5e-13, 0.0, "absolute")
    with pytest.raises(ValueError):
        audit.close(1.0 + 5.5e-12, 1.0, "not relative or absolute")


def test_direct_circle_uses_t_parameter_and_correct_projection_orientation():
    snapshot, report = synthetic_seed()
    row = audit.independent_certificate(snapshot, report, snapshot["base_coefficients"])["curves"][
        0
    ]
    _, tangent, second = evaluate(snapshot["base_coefficients"][0], np.arange(64) / 64)
    assert np.allclose(np.linalg.norm(tangent, axis=1), 2 * math.pi * 0.2)
    assert np.allclose(np.cross(tangent, second) @ row["normal"], (2 * math.pi) ** 3 * 0.2**2)
    assert row["S_lower"] > 0


@pytest.mark.parametrize(
    "mutation",
    [
        "lp_missing",
        "lp_primal",
        "lp_dual",
        "lp_objective",
        "source_extra",
        "fake_cover",
        "fake_analytic_cc",
        "typed_grid",
        "length_sum",
        "rho_chain",
    ],
)
def test_seed_proof_numbers_not_only_flags(seed, mutation):
    snapshot, report = map(copy.deepcopy, seed)
    row = report["coils"][0]
    if mutation == "lp_missing":
        del row["lp_certificates"][0]["errors"]
    elif mutation == "lp_primal":
        row["lp_certificates"][0]["errors"]["primal"] = 1e-5
    elif mutation == "lp_dual":
        row["lp_certificates"][0]["dual_objective"] += 1e-4
    elif mutation == "lp_objective":
        for lp in row["lp_certificates"]:
            lp["objective"] += 1e-3
            lp["dual_objective"] += 1e-3
    elif mutation == "source_extra":
        snapshot["sources"]["reference"]["input"]["bytes"] = 10
    elif mutation == "fake_cover":
        report["distances"][0]["curve_cover"][0] = 0.0001
    elif mutation == "fake_analytic_cc":
        report["analytic_coil_lower"] += 0.001
    elif mutation == "typed_grid":
        report["distances"][0]["ncoil"] = 1024.0
    elif mutation == "length_sum":
        report["sum_base_lengths"] += 0.001
    else:
        row["continuous"]["rho_lower"] += 0.001
        row["continuous"]["curvature_upper"] = 1 / row["continuous"]["rho_lower"]
        h = row["support_coefficients"]
        actual = np.array(snapshot["base_coefficients"])[0]
        row["export_transfer"] = frozen.export_certificate(
            row["continuous"], h, actual, actual, snapshot["case"]["r_floor"], 0.1
        )
    with pytest.raises(ValueError):
        audit.independent_certificate(snapshot, report, snapshot["base_coefficients"])


def test_small_joint_orthogonal_rotation_stays_enclosed(seed):
    snapshot, report = seed
    base = np.array(snapshot["base_coefficients"])
    angle = 1e-5
    rotation = np.array(
        [[np.cos(angle), 0, np.sin(angle)], [0, 1, 0], [-np.sin(angle), 0, np.cos(angle)]]
    )
    candidate = np.einsum("ij,bjm->bim", rotation, base)
    result = audit.independent_certificate(snapshot, report, candidate)
    assert result["certified"]
    for row, mapping in zip(result["curves"], snapshot["physical"], strict=True):
        transform = np.array(mapping["matrix"]).T
        b = mapping["base_index"]
        t = np.arange(257) / 257
        old, new = evaluate(transform @ base[b], t), evaluate(transform @ candidate[b], t)
        for d in range(3):
            assert np.linalg.norm(new[d] - old[d], axis=1).max() <= row[f"D{d}"]


def test_unrelaxed_plasma_boundary_consumes_rounding(seed):
    snapshot, report = seed
    candidate = np.array(snapshot["base_coefficients"])
    candidate[0, 2, 0] += 0.02 - 1e-8
    accepted = audit.independent_certificate(snapshot, report, candidate)
    assert accepted["certified"]
    candidate[0, 2, 0] += 1e-8
    rejected = audit.independent_certificate(snapshot, report, candidate)
    assert rejected["calculation_complete"] and not rejected["certified"]
    assert not rejected["gates"]["analytic_plasma"]
    assert rejected["plasma"]["reference"][0]["analytic_lower"] < 0.08


@pytest.mark.parametrize(
    "which", ["snapshot_none", "report_none", "report_coils_none", "snapshot_missing"]
)
def test_bad_top_level_input_is_value_error(which):
    snapshot, report = synthetic_seed()
    candidate = snapshot["base_coefficients"]
    if which == "snapshot_none":
        snapshot = None
    elif which == "report_none":
        report = None
    elif which == "report_coils_none":
        report["coils"] = None
    else:
        del snapshot["base_coefficients"]
    with pytest.raises(ValueError):
        audit.independent_certificate(snapshot, report, candidate)
