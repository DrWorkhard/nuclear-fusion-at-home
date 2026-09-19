"""Synthetic pure cumulative certificates; no target geometry, LPs or fields."""

import copy
import json

import numpy as np
import pytest

from fusion_baselines import clear_coil_geometry_audit as historical
from fusion_baselines import coil_perturbation as producer


def fixture(nbase=6, radius=0.3):
    order = 5 if nbase == 6 else 7
    case = next(c for c in historical.cases() if c["label"] == f"n{nbase}-shape-d100mm")
    h = np.zeros(2 * (order - 1) + 1)
    h[0] = radius
    center = np.array([1.2, 0.025])
    floating_pad = producer.EPS * center[0]
    rho = radius - floating_pad
    continuous = dict(
        enclosure_lower=0.01,
        rho_lower=rho,
        radial_lower=center[0] - radius - floating_pad,
        length=2 * np.pi * radius,
        length_upper=2 * np.pi * radius + 2 * np.pi * floating_pad,
        curvature_upper=1 / rho,
        L_h=0.0,
        L_rho=0.0,
        L_S=0.0,
        floating_pad=floating_pad,
        interval_arithmetic=False,
        support_pass=True,
        length_pass=True,
        curvature_pass=True,
        planar_self_disjoint=True,
    )
    residuals = {
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
    }
    lp = dict(
        solved=True,
        errors=residuals,
        objective=continuous["length"],
        dual_objective=continuous["length"],
        passed=True,
        infeasibility_proven=False,
    )
    coefficients, coils = [], []
    for i in range(nbase):
        phi = (i + 0.5) * np.pi / (2 * nbase)
        c = historical.export_coefficients(h, center, phi, order)
        coefficients.append(c.tolist())
        transfer = historical.export_certificate(continuous, h, c, c, case["r_floor"], 0.1)
        coils.append(
            dict(
                base_index=i,
                lp_certificates=[copy.deepcopy(lp), copy.deepcopy(lp)],
                exact_repeat=True,
                continuous=copy.deepcopy(continuous),
                export_transfer=transfer,
                support_coefficients=h.tolist(),
                available_geometry=True,
            )
        )
    sources = {
        label: {
            key: dict(path=f"/synthetic/{label}/{key}", sha256="a" * 64)
            for key in ("input", "wout")
        }
        for label in producer.TARGETS
    }
    snapshot = dict(
        schema_version=1,
        kind="geometry-only",
        nfp=2,
        nbase=nbase,
        order=order,
        names=historical.parameter_names(nbase, order),
        base_coefficients=coefficients,
        physical=historical.physical_rows(nbase),
        case=copy.deepcopy(case),
        sources=sources,
        parameter_orientation="alpha=-2*pi*t",
    )
    distances = []
    count = 4 * nbase
    for target in producer.TARGETS:
        for level, (n, offset) in enumerate(((256, 0), (512, 0), (512, 0.5))):
            pair_lower = 0.12 + 0.001 * level + (0.0001 if target == "selected" else 0.0)
            cp_lower = 0.095 + 0.001 * level + (0.0001 if target == "selected" else 0.0)
            cover, surface_cover, tiny = 0.002, 0.01, producer.EPS
            pairs = [
                dict(i=i, j=j, lower=pair_lower, sampled=pair_lower + 2 * cover + tiny)
                for i in range(count)
                for j in range(i + 1, count)
            ]
            plasma = [
                dict(i=i, lower=cp_lower, sampled=cp_lower + cover + surface_cover + tiny)
                for i in range(count)
            ]
            distances.append(
                dict(
                    target=target,
                    ncoil=1024,
                    nphi=n,
                    ntheta=n,
                    offset=offset,
                    full_torus=True,
                    curve_cover=[cover] * count,
                    surface_cover=surface_cover,
                    floating_pad=tiny,
                    interval_arithmetic=False,
                    coil_pairs=pairs,
                    plasma_distances=plasma,
                    lengths_sampled=[2 * np.pi * radius] * count,
                    curvature_sampled=[1 / radius] * count,
                    sampled_length_pass=True,
                    sampled_curvature_pass=True,
                    coil_pass=True,
                    plasma_pass=True,
                )
            )
    export_error = max(
        c["export_transfer"]["position_error"] + c["export_transfer"]["coefficient_rounding_pad"]
        for c in coils
    )
    report = dict(
        case=copy.deepcopy(case),
        coils=coils,
        distances=distances,
        geometry_pass=True,
        available_geometry=True,
        sum_base_lengths=nbase * continuous["length"],
        analytic_coil_lower=2 * continuous["radial_lower"] * np.sin(np.pi / (4 * nbase))
        - 2 * export_error,
    )
    return snapshot, report


def direct(coefficients, t, derivative):
    """Test-only independent complex exponential evaluation of arbitrary order."""
    c = np.asarray(coefficients)
    result = np.zeros((len(t), 3), dtype=complex)
    if derivative == 0:
        result += c[:, 0]
    for m in range(1, (c.shape[1] - 1) // 2 + 1):
        omega = 2 * np.pi * m
        amplitude = c[:, 2 * m] - 1j * c[:, 2 * m - 1]
        result += np.exp(1j * omega * t)[:, None] * (1j * omega) ** derivative * amplitude
    return result.real


@pytest.mark.parametrize("nbase", [6, 8])
def test_exact_null_seed_certificate_is_complete_json_and_does_not_mutate(nbase):
    seed, report = fixture(nbase)
    before_seed, before_report = copy.deepcopy(seed), copy.deepcopy(report)
    candidate = np.asarray(seed["base_coefficients"])
    original = candidate.copy()
    answer = producer.candidate_certificate(seed, report, candidate)
    assert answer["certified"] is answer["calculation_complete"] is True
    assert answer["status"] == "certified" and answer["reason"] is None
    assert len(answer["curves"]) == 4 * nbase
    assert len(answer["pairs"]) == 4 * nbase * (4 * nbase - 1) // 2
    assert all(answer["gates"].values())
    assert all(r["D0"] > 0 and r["D1"] > 0 and r["D2"] > 0 for r in answer["curves"])
    assert answer["plasma"]["reference"][0]["direct_seed_lower"] == 0.095
    assert answer["plasma"]["selected"][0]["direct_seed_lower"] == 0.0951
    assert answer["pairs"][0]["direct_seed_lower"] == 0.12
    assert all(
        answer[k] is False for k in ("search_allowed", "field_pass", "transfer_pass", "step4_pass")
    )
    json.dumps(answer, allow_nan=False)
    assert seed == before_seed and report == before_report and np.array_equal(candidate, original)
    answer["case"]["label"] = "mutable output"
    assert seed == before_seed and report == before_report


@pytest.mark.parametrize("kind", ["translation", "rotation", "high-mode", "ulp", "smooth"])
def test_all_symmetries_direct_derivative_curvature_projection_and_length_enclosures(kind):
    seed, report = fixture()
    original = np.asarray(seed["base_coefficients"])
    candidate = original.copy()
    if kind == "translation":
        candidate[:, :, 0] += [1e-4, -2e-4, 3e-4]
    elif kind == "rotation":
        angle = 1e-4
        q = np.array(
            [[np.cos(angle), 0, np.sin(angle)], [0, 1, 0], [-np.sin(angle), 0, np.cos(angle)]]
        )
        candidate = np.einsum("ij,bjk->bik", q, candidate)
    elif kind == "high-mode":
        candidate[0, 2, -2] += 1e-5
    elif kind == "ulp":
        candidate[0, 0, 0] = np.nextafter(candidate[0, 0, 0], np.inf)
    else:
        candidate += 1e-5 * np.sin(np.arange(candidate.size).reshape(candidate.shape) + 1)
    record = producer.candidate_certificate(seed, report, candidate)
    assert record["certified"]
    t = (np.arange(513) + 0.37) / 513
    for mapping, row in zip(seed["physical"], record["curves"], strict=True):
        matrix = np.asarray(mapping["matrix"]).T
        a, b = matrix @ original[mapping["base_index"]], matrix @ candidate[mapping["base_index"]]
        base_values, values = [], []
        for k in (0, 1, 2):
            old, new = direct(a, t, k), direct(b, t, k)
            assert np.linalg.norm(new - old, axis=1).max() <= row[f"D{k}"]
            base_values.append(old)
            values.append(new)
        speed = np.linalg.norm(values[1], axis=1)
        cross = np.cross(values[1], values[2])
        assert speed.min() >= row["v_lower"]
        assert (cross @ row["normal"]).min() >= row["S_lower"]
        assert (np.linalg.norm(cross, axis=1) / speed**3).max() <= row["kappa_upper"]
        assert abs(speed.mean() - np.linalg.norm(base_values[1], axis=1).mean()) <= row["D1"]


def test_negative_coefficients_receive_positive_outward_pad():
    magnitudes = np.zeros((3, 11))
    magnitudes[0, 9] = 0.002
    d = producer.derivative_bounds(magnitudes + producer.EPS)
    assert d[0] >= 0.002
    assert d[1] >= 0.002 * 2 * np.pi * 5
    assert d[2] >= 0.002 * (2 * np.pi * 5) ** 2
    seed, report = fixture()
    x = np.asarray(seed["base_coefficients"])
    plus, minus = x.copy(), x.copy()
    plus[0, 2, -2] += 0.002
    minus[0, 2, -2] -= 0.002
    a, b = [producer.candidate_certificate(seed, report, v) for v in (plus, minus)]
    assert all(
        a["curves"][i][key] == b["curves"][i][key] for i in range(24) for key in ("D0", "D1", "D2")
    )


def test_cumulative_reference_does_not_reset_at_previous_candidate():
    seed, report = fixture()
    original = np.asarray(seed["base_coefficients"])
    step = np.zeros_like(original)
    step[:, 2, 0] = 0.001
    intermediate = original + step
    final = intermediate + step
    before = producer.candidate_certificate(seed, report, intermediate)
    chained = producer.candidate_certificate(seed, report, final)
    direct_result = producer.candidate_certificate(seed, report, original + 2 * step)
    assert chained == direct_result
    assert chained["curves"][0]["D0"] > 1.9 * before["curves"][0]["D0"]


@pytest.mark.parametrize("kind", ["speed", "curvature", "plasma", "length", "coil"])
def test_finite_uncertified_candidates_keep_all_curves_pairs_and_direct_gates(kind):
    seed, report = fixture()
    x = np.asarray(seed["base_coefficients"])
    if kind == "speed":
        x[0, 2, -2] += 0.3
    elif kind == "curvature":
        x[0, 2, -2] += 0.025
    elif kind == "plasma":
        x[:, 2, 0] += 0.03
    elif kind == "length":
        x[:, :, 1:] *= 3
    else:
        x[:, 2, 0] += 0.04
    result = producer.candidate_certificate(seed, report, x)
    assert result["calculation_complete"] and not result["certified"]
    assert result["status"] == "uncertified" and len(result["curves"]) == 24
    assert len(result["pairs"]) == 276
    gate = {
        "speed": "regularity",
        "curvature": "curvature",
        "plasma": "direct_plasma",
        "length": "length",
        "coil": "direct_coil",
    }[kind]
    assert result["gates"][gate] is False
    if kind == "speed":
        assert result["curves"][0]["kappa_upper"] is None
        assert result["curves"][0]["kappa_status"] == "not_available"
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf, 1e308])
def test_nonfinite_or_overflowing_candidate_is_explicit_json_negative(value):
    seed, report = fixture()
    x = np.asarray(seed["base_coefficients"])
    x[0, 0, 1] = value
    result = producer.candidate_certificate(seed, report, x)
    assert result["certified"] is result["calculation_complete"] is False
    assert result["curves"] == [] and not any(result["gates"].values())
    assert result["reason"] in ("nonfinite candidate coefficients", "nonfinite bound arithmetic")
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "mutation",
    [
        "name",
        "source",
        "selected-case",
        "schema",
        "symmetry",
        "twice-circle",
        "support",
        "export",
        "rho",
        "lp",
        "missing-grid",
        "missing-pair",
        "pair-order",
        "cp-cover",
        "cc-analytic",
    ],
)
def test_missing_or_forged_seed_proof_is_rejected(mutation):
    seed, report = fixture()
    x = np.asarray(seed["base_coefficients"])
    if mutation == "name":
        seed["names"][0] = "renamed"
    elif mutation == "source":
        seed["sources"]["reference"]["input"]["path"] = "relative"
    elif mutation == "selected-case":
        seed["case"]["label"] = "unregistered"
    elif mutation == "schema":
        seed["invented_source_pass"] = True
    elif mutation == "symmetry":
        seed["physical"][0]["matrix"][0][0] = -1.0
    elif mutation == "twice-circle":
        doubled = np.zeros_like(x)
        doubled[:, :, 0] = x[:, :, 0]
        doubled[:, :, 3:5] = x[:, :, 1:3]
        seed["base_coefficients"] = doubled.tolist()
    elif mutation == "support":
        report["coils"][0]["continuous"]["planar_self_disjoint"] = False
    elif mutation == "export":
        report["coils"][0]["export_transfer"]["speed_lower"] += 0.001
    elif mutation == "rho":
        report["coils"][0]["continuous"]["rho_lower"] = -1.0
    elif mutation == "lp":
        report["coils"][0]["lp_certificates"][0]["errors"]["primal"] = 1e-3
    elif mutation == "missing-grid":
        report["distances"].pop()
    elif mutation == "missing-pair":
        report["distances"][0]["coil_pairs"].pop()
    elif mutation == "pair-order":
        report["distances"][0]["coil_pairs"].reverse()
    elif mutation == "cp-cover":
        report["distances"][0]["plasma_distances"][0]["lower"] += 0.001
    else:
        report["analytic_coil_lower"] += 0.001
    with pytest.raises(ValueError):
        producer.candidate_certificate(seed, report, x)


@pytest.mark.parametrize(
    "candidate", [np.zeros((6, 3, 10)), [["0"]], np.zeros((6, 3, 11), dtype=bool)]
)
def test_wrong_candidate_shape_or_type_is_not_a_physical_negative(candidate):
    seed, report = fixture()
    with pytest.raises(ValueError):
        producer.candidate_certificate(seed, report, candidate)


def test_forged_larger_support_radius_with_matching_export_chain_is_rejected():
    seed, report = fixture()
    row = report["coils"][0]
    row["continuous"]["rho_lower"] += 0.01
    row["continuous"]["curvature_upper"] = 1 / row["continuous"]["rho_lower"]
    actual = np.asarray(seed["base_coefficients"])[0]
    row["export_transfer"] = historical.export_certificate(
        row["continuous"],
        row["support_coefficients"],
        actual,
        actual,
        seed["case"]["r_floor"],
        0.1,
    )
    with pytest.raises(ValueError, match="original1024 support radius"):
        producer.candidate_certificate(seed, report, seed["base_coefficients"])


@pytest.mark.parametrize("gate", ["analytic_plasma", "analytic_coil"])
def test_analytic_distance_gate_cannot_be_replaced_by_better_direct_certificate(gate):
    seed, report = fixture()
    x = np.asarray(seed["base_coefficients"])
    delta = 0.021 if gate == "analytic_plasma" else 0.1
    x[:, 2, 0] += delta
    key = "plasma_distances" if gate == "analytic_plasma" else "coil_pairs"
    for level in report["distances"]:
        for row in level[key]:
            row["lower"] += 0.3
            row["sampled"] += 0.3
    answer = producer.candidate_certificate(seed, report, x)
    assert answer["gates"][gate] is False
    assert answer["gates"][gate.replace("analytic", "direct")] is True
    assert not answer["certified"]


@pytest.mark.parametrize(
    "mutation", ["bool-matrix", "none-report", "missing-coil-proof", "none-seed"]
)
def test_invalid_original_schema_types_fail_as_value_errors(mutation):
    seed, report = fixture()
    x = seed["base_coefficients"]
    if mutation == "bool-matrix":
        seed["physical"][0]["matrix"][0][0] = True
    elif mutation == "none-report":
        report = None
    elif mutation == "missing-coil-proof":
        report["coils"][0] = None
    else:
        seed = None
    with pytest.raises(ValueError):
        producer.candidate_certificate(seed, report, x)


@pytest.mark.parametrize("nbase", [6, 8])
@pytest.mark.parametrize("mode", ["null", "high-plus", "high-minus", "translation", "large", "nan"])
def test_synthetic_producer_report_passes_separate_independent_auditor(nbase, mode):
    from fusion_baselines import coil_perturbation_audit as independent

    seed, report = fixture(nbase)
    x = np.asarray(seed["base_coefficients"])
    if mode == "high-plus":
        x[0, 2, -2] += 1e-5
    elif mode == "high-minus":
        x[0, 2, -2] -= 1e-5
    elif mode == "translation":
        x[:, 2, 0] += 0.03
    elif mode == "large":
        x[0, 2, -2] += 0.3
    elif mode == "nan":
        x[0, 2, -2] = np.nan
    actual = producer.candidate_certificate(seed, report, x)
    own = independent.audit_certificate(seed, report, x, actual)
    assert own["certified"] is actual["certified"]
