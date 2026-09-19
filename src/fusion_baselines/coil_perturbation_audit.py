"""Independent, field-free audit of cumulative Fourier-coil perturbations.

This module never imports the perturbation producer.  Upstream file hashes are
the caller's responsibility; the complete accepted seed proof and its named
geometry are checked here before any candidate receives a certificate.
"""

import math
from pathlib import Path

import numpy as np

from fusion_baselines import clear_coil_geometry_audit as frozen

RTOL = 5e-12
ATOL = 1e-12
EPS_FACTOR = 128 * np.finfo(float).eps


def require(condition, message):
    if not condition:
        raise ValueError(message)


def real(value, label, *, finite=True):
    array = np.asarray(value)
    require(array.dtype.kind in "iuf", f"{label}: real numerical data required")
    array = array.astype(float)
    require(not finite or np.isfinite(array).all(), f"{label}: finite values required")
    return array


def scalar(value, label, *, positive=False):
    array = real(value, label)
    require(array.shape == (), f"{label}: scalar required")
    number = float(array)
    require(not positive or number > 0, f"{label}: strictly positive required")
    return number


def close(actual, expected, label):
    a, b = real(actual, label), real(expected, label)
    require(a.shape == b.shape, f"{label}: shape differs")
    error = abs(a - b)
    require(np.all((error <= ATOL) | (error <= RTOL * abs(b))), f"{label}: value differs")


def proof_close(actual, expected, label):
    a, b = real(actual, label), real(expected, label)
    require(
        a.shape == b.shape and np.all(abs(a - b) <= 5e-12),
        f"{label}: original absolute reconstruction tolerance",
    )


def true_flags(record, keys, label):
    require(isinstance(record, dict), f"{label}: mapping required")
    require(all(record.get(key) is True for key in keys), f"{label}: missing proof")


def source_reference(ref):
    require(
        isinstance(ref, dict)
        and set(ref) == {"path", "sha256"}
        and type(ref.get("path")) is str
        and Path(ref["path"]).is_absolute()
        and type(ref.get("sha256")) is str
        and len(ref["sha256"]) == 64
        and all(c in "0123456789abcdef" for c in ref["sha256"]),
        "seed source reference requires an absolute path and SHA256",
    )


def keys(record, expected, label):
    require(
        isinstance(record, dict) and set(record) == set(expected.split()),
        f"{label}: complete original keys",
    )


def lp_proofs(rows, length):
    limits = dict(
        primal=1e-10,
        dual_sign=1e-8,
        stationarity=1e-8,
        complementarity=1e-8,
        primal_dual_gap=1e-8,
        reported_objective=5e-12,
        reported_slack=5e-12,
    )
    require(type(rows) is list and len(rows) == 2, "two complete seed LP certificates")
    for row in rows:
        keys(row, "solved errors objective dual_objective passed infeasibility_proven", "LP")
        true_flags(row, ("solved", "passed"), "seed LP proof")
        require(row["infeasibility_proven"] is False, "accepted LP is not infeasible")
        require(
            type(row["errors"]) is dict and set(row["errors"]) == set(limits),
            "all original LP residuals",
        )
        for key, limit in limits.items():
            require(0 <= scalar(row["errors"][key], key) <= limit, "LP residual acceptance")
        require(
            abs(scalar(row["objective"], "LP objective") - length) <= 5e-12,
            "LP objective/support identity",
        )
        require(
            abs(row["objective"] - scalar(row["dual_objective"], "LP dual objective")) <= 1e-8,
            "LP primal-dual objective difference",
        )


def scalar_pad(*terms):
    return float(EPS_FACTOR * max(1.0, math.fsum(abs(float(t)) for t in terms)))


def upper_sum(*terms):
    result = math.fsum(float(t) for t in terms)
    return float(result + scalar_pad(*terms))


def lower_difference(first, *subtracted):
    result = math.fsum([float(first), *[-float(t) for t in subtracted]])
    return float(result - scalar_pad(first, *subtracted))


def derivative_bounds(coefficients, coefficient_pad, *, constant=True, extra=None):
    """Axiswise Fourier amplitudes, not a sampled maximum or RMS quantity."""
    coef = real(coefficients, "Fourier coefficients")
    require(coef.ndim == 2 and coef.shape[0] == 3, "Cartesian Fourier coefficient shape")
    require(coef.shape[1] >= 3 and coef.shape[1] % 2 == 1, "odd Fourier coefficient width")
    order = (coef.shape[1] - 1) // 2
    magnitude = abs(coef) + coefficient_pad
    if extra is not None:
        require(np.shape(extra) == coef.shape, "extra Fourier rounding shape")
        magnitude += real(extra, "extra Fourier rounding")
    amplitudes = np.hypot(magnitude[:, 1::2], magnitude[:, 2::2])
    results = []
    for derivative in range(3):
        axis = np.array(
            [
                math.fsum(
                    float(amplitudes[a, m - 1]) * (2 * math.pi * m) ** derivative
                    for m in range(1, order + 1)
                )
                for a in range(3)
            ]
        )
        if derivative == 0 and constant:
            axis += magnitude[:, 0]
        raw = math.hypot(*(float(v) for v in axis))
        results.append(upper_sum(raw))
    return results


def _seed_curve(snapshot, report, index):
    """Recover the degree-one support proof; a positive sampled cross is not enough."""
    row = report["coils"][index]
    keys(
        row,
        "base_index lp_certificates exact_repeat continuous export_transfer "
        "support_coefficients available_geometry",
        "seed base",
    )
    require(
        type(row.get("base_index")) is int and row["base_index"] == index,
        "ordered seed base indices",
    )
    true_flags(row, ("available_geometry", "exact_repeat"), "seed coil")
    continuous, exported = row.get("continuous"), row.get("export_transfer")
    keys(
        continuous,
        "enclosure_lower rho_lower radial_lower length length_upper curvature_upper "
        "L_h L_rho L_S floating_pad interval_arithmetic support_pass length_pass curvature_pass "
        "planar_self_disjoint",
        "support proof",
    )
    true_flags(
        continuous,
        ("support_pass", "length_pass", "curvature_pass", "planar_self_disjoint"),
        "support proof",
    )
    true_flags(
        exported,
        (
            "support_pass",
            "length_pass",
            "curvature_pass",
            "plasma_pass",
            "controlled_projection_self_disjoint",
        ),
        "actual export proof",
    )
    require(
        continuous.get("interval_arithmetic") is False
        and exported.get("interval_arithmetic") is False,
        "declared ordinary padded arithmetic",
    )
    case = snapshot["case"]
    h = real(row.get("support_coefficients"), "complete seed support coefficients")
    require(h.shape == (2 * case["K"] + 1,), "support order must match seed case")
    lp_proofs(row["lp_certificates"], 2 * math.pi * h[0])
    actual = np.asarray(snapshot["base_coefficients"], dtype=float)[index]
    phi = (index + 0.5) * math.pi / (2 * snapshot["nbase"])
    radial = np.array([math.cos(phi), math.sin(phi), 0.0])
    normal = np.array([-math.sin(phi), math.cos(phi), 0.0])
    center = np.array([radial @ actual[:, 0] - h[2], actual[2, 0] - h[1]])
    expected = frozen.export_coefficients(h, center, phi, snapshot["order"])
    # Original raw export tolerance, not the later scalar comparison tolerance.
    require(np.all(abs(actual - expected) <= 5e-12), "support-to-actual export identity")
    frequency = np.repeat(np.arange(1, case["K"] + 1), 2)
    lh = float(frequency @ abs(h[1:]))
    lrho = float((frequency * abs(1 - frequency**2)) @ abs(h[1:]))
    ls = scalar(continuous.get("L_S"), "original disk support Lipschitz")
    require(ls >= 0, "nonnegative disk support Lipschitz")
    pad = EPS_FACTOR * max(1.0, float(abs(h).sum()), float(abs(center).max()), ls)
    theta = 2 * np.pi * np.arange(1024) / 1024
    rho = np.full(1024, h[0])
    for m in range(1, case["K"] + 1):
        rho += (1 - m * m) * (h[2 * m - 1] * np.sin(m * theta) + h[2 * m] * np.cos(m * theta))
    rho_lower = float(rho.min() - math.pi / 1024 * lrho - pad)
    require(rho_lower >= 0.10 and h[0] > 0, "degree-one strictly convex support seed")
    proof_close(continuous.get("rho_lower"), rho_lower, "seed rho lower")
    proof_close(continuous.get("L_h"), lh, "seed support Lipschitz")
    proof_close(continuous.get("L_rho"), lrho, "seed rho Lipschitz")
    proof_close(continuous.get("floating_pad"), pad, "seed support pad")
    proof_close(continuous.get("length"), 2 * math.pi * h[0], "seed support length")
    proof_close(continuous.get("length_upper"), 2 * math.pi * (h[0] + pad), "seed length upper")
    proof_close(continuous.get("curvature_upper"), 1 / rho_lower, "seed ideal curvature")
    require(
        scalar(continuous.get("enclosure_lower"), "seed enclosure") >= 0, "seed support enclosure"
    )
    expected_radial = (
        center[0] - h[0] - sum((-1) ** m * h[2 * m] for m in range(1, case["K"] + 1)) - pad
    )
    proof_close(continuous.get("radial_lower"), expected_radial, "seed support radial lower")
    transferred = frozen.export_certificate(
        continuous, h, expected, actual, case["r_floor"], case["d"]
    )
    require(
        isinstance(exported, dict) and set(exported) == set(transferred),
        "complete original export transfer",
    )
    for key in transferred:
        if isinstance(transferred[key], bool):
            require(exported.get(key) is transferred[key], f"seed export {key}")
        else:
            proof_close(exported.get(key), transferred[key], f"seed export {key}")
    values = {
        key: scalar(exported.get(key), f"seed {key}", positive=True)
        for key in (
            "speed_lower",
            "signed_projection_cross_lower",
            "curvature_upper",
            "length_upper",
            "analytic_plasma_lower",
        )
    }
    require(
        values["curvature_upper"] <= 12
        and values["length_upper"] <= 3.5
        and values["analytic_plasma_lower"] >= 0.08,
        "accepted actual seed physical bounds",
    )
    return dict(values, normal=normal)


def _seed_context(snapshot, report):
    """Validate the source-bound historical proof; never manufacture missing flags."""
    frozen.validate_snapshot(snapshot)
    require(
        snapshot["case"]["label"] in ("n6-shape-d100mm", "n8-shape-d100mm"),
        "only the two preregistered accepted seed classes",
    )
    expected_case = next(c for c in frozen.cases() if c["label"] == snapshot["case"]["label"])
    require(
        all(type(snapshot["case"][k]) is type(v) for k, v in expected_case.items()),
        "original typed seed case",
    )
    for target in ("reference", "selected"):
        source = snapshot["sources"][target]
        require(
            isinstance(source, dict) and set(source) == {"input", "wout"},
            "both complete seed target sources",
        )
        for ref in source.values():
            source_reference(ref)
    keys(
        report,
        "case coils distances geometry_pass available_geometry sum_base_lengths "
        "analytic_coil_lower",
        "selected geometry report",
    )
    require(
        report.get("case") == snapshot["case"]
        and all(type(report["case"][k]) is type(v) for k, v in expected_case.items()),
        "matching selected geometry report",
    )
    true_flags(report, ("geometry_pass", "available_geometry"), "selected seed report")
    require(
        type(report.get("coils")) is list and len(report["coils"]) == snapshot["nbase"],
        "complete base proofs",
    )
    bases = [_seed_curve(snapshot, report, i) for i in range(snapshot["nbase"])]
    proof_close(
        report["sum_base_lengths"],
        sum(row["continuous"]["length"] for row in report["coils"]),
        "seed total length",
    )
    count = len(snapshot["physical"])
    pair_order = [(i, j) for i in range(count) for j in range(i + 1, count)]
    cp = {target: [] for target in ("reference", "selected")}
    cc = []
    expected_levels = [
        (target, n, shift) for target in cp for n, shift in ((256, 0), (512, 0), (512, 0.5))
    ]
    require(
        type(report.get("distances")) is list and len(report["distances"]) == 6,
        "all six seed direct distance proofs",
    )
    for row, (target, n, shift) in zip(report["distances"], expected_levels, strict=True):
        keys(
            row,
            "target ncoil nphi ntheta offset full_torus curve_cover surface_cover "
            "floating_pad interval_arithmetic coil_pairs plasma_distances lengths_sampled "
            "curvature_sampled sampled_length_pass sampled_curvature_pass coil_pass plasma_pass",
            "seed direct distance",
        )
        require(
            row.get("target") == target
            and row.get("ncoil") == 1024
            and row.get("nphi") == row.get("ntheta") == n
            and row.get("offset") == shift
            and all(type(row[k]) is int for k in ("ncoil", "nphi", "ntheta"))
            and type(row["offset"]) is type(shift)
            and row.get("full_torus") is True
            and row.get("interval_arithmetic") is False,
            "exact seed distance target/grid",
        )
        true_flags(
            row,
            ("coil_pass", "plasma_pass", "sampled_length_pass", "sampled_curvature_pass"),
            "seed direct distance",
        )
        require(
            type(row.get("plasma_distances")) is list
            and type(row.get("coil_pairs")) is list
            and len(row.get("plasma_distances", [])) == count
            and len(row.get("coil_pairs", [])) == len(pair_order),
            "complete physical seed distances",
        )
        covers = real(row["curve_cover"], "seed curve covering radii")
        surface_cover = scalar(row["surface_cover"], "seed surface cover", positive=True)
        pad = scalar(row["floating_pad"], "seed direct pad", positive=True)
        require(covers.shape == (count,) and np.all(covers > 0), "all positive curve covers")
        sampled_length = real(row["lengths_sampled"], "seed sampled lengths")
        sampled_kappa = real(row["curvature_sampled"], "seed sampled curvature")
        require(
            sampled_length.shape == sampled_kappa.shape == (count,)
            and np.all((sampled_length > 0) & (sampled_length <= 3.5))
            and np.all((sampled_kappa >= 0) & (sampled_kappa <= 12)),
            "all seed sampled geometric gates",
        )
        cp_values, cc_values = [], []
        for i, distance in enumerate(row["plasma_distances"]):
            keys(distance, "i sampled lower", "seed CP distance")
            require(
                type(distance.get("i")) is int and distance["i"] == i,
                "ordered physical plasma distance",
            )
            value = scalar(distance.get("lower"), "seed plasma lower")
            sampled = scalar(distance["sampled"], "seed CP sampled distance")
            proof_close(value, max(0.0, sampled - covers[i] - surface_cover - pad), "seed CP cover")
            require(0.08 <= value <= sampled, "accepted seed plasma distance")
            cp_values.append(value)
        for pair, distance in zip(pair_order, row["coil_pairs"], strict=True):
            keys(distance, "i j sampled lower", "seed pair distance")
            require(
                type(distance.get("i")) is int
                and type(distance.get("j")) is int
                and (distance["i"], distance["j"]) == pair,
                "ordered physical coil pair",
            )
            value = scalar(distance.get("lower"), "seed coil lower")
            sampled = scalar(distance["sampled"], "seed pair sampled distance")
            i, j = pair
            proof_close(value, max(0.0, sampled - covers[i] - covers[j] - pad), "seed pair cover")
            require(0.06 <= value <= sampled, "accepted seed coil distance")
            cc_values.append(value)
        cp[target].append(cp_values)
        cc.append(cc_values)
    analytic_cc = scalar(report.get("analytic_coil_lower"), "analytic seed pair bound")
    radial = min(row["continuous"]["radial_lower"] for row in report["coils"])
    error = max(
        row["export_transfer"]["position_error"]
        + row["export_transfer"]["coefficient_rounding_pad"]
        for row in report["coils"]
    )
    proof_close(
        analytic_cc,
        2 * radial * math.sin(math.pi / (4 * snapshot["nbase"])) - 2 * error,
        "analytic seed pair proof",
    )
    require(analytic_cc >= 0.06, "accepted analytic seed pair distance")
    return dict(
        coefficients=real(snapshot["base_coefficients"], "seed coefficients"),
        bases=bases,
        cp={k: np.min(v, axis=0) for k, v in cp.items()},
        cc=np.min(cc, axis=0),
        pair_order=pair_order,
        analytic_cc=analytic_cc,
    )


def seed_context(snapshot, report):
    try:
        return _seed_context(snapshot, report)
    except (KeyError, TypeError, IndexError, AttributeError, OverflowError) as exc:
        raise ValueError(f"malformed original seed proof: {exc}") from exc


GATE_NAMES = (
    "regularity",
    "projection",
    "length",
    "curvature",
    "direct_plasma",
    "analytic_plasma",
    "direct_coil",
    "analytic_coil",
)
SCOPE = dict(
    field_calls=0,
    gradient_calls=0,
    equilibrium_solves=0,
    search_allowed=False,
    field_pass=False,
    transfer_pass=False,
    step4_pass=False,
)


def _empty_report(snapshot, reason):
    return dict(
        schema_version=1,
        kind="cumulative-coil-perturbation",
        status="uncertified",
        calculation_complete=False,
        certified=False,
        reason=reason,
        case=dict(snapshot["case"]),
        curves=[],
        plasma=dict(reference=[], selected=[]),
        pairs=[],
        gates={key: False for key in GATE_NAMES},
        **SCOPE,
    )


def _calculate(snapshot, context, candidate):
    curves = []
    for index, mapping in enumerate(snapshot["physical"]):
        base = mapping["base_index"]
        seed = context["coefficients"][base]
        actual_rotation = np.asarray(mapping["matrix"], dtype=float).T
        sign = -1.0 if mapping["period"] else 1.0
        ideal_rotation = np.diag(
            [sign, -sign if mapping["flip"] else sign, -1.0 if mapping["flip"] else 1.0]
        )
        require(
            np.max(abs(actual_rotation - ideal_rotation)) <= 5e-12
            and np.linalg.det(ideal_rotation) == 1.0,
            "proper canonical physical symmetry",
        )
        physical_seed = actual_rotation @ seed
        physical_candidate = actual_rotation @ candidate[base]
        ideal_seed = ideal_rotation @ seed
        symmetry_error = abs((actual_rotation - ideal_rotation) @ seed)
        pad = EPS_FACTOR * max(
            1.0, float(abs(physical_seed).max()), float(abs(physical_candidate).max())
        )
        d0, d1, d2 = derivative_bounds(
            physical_candidate - physical_seed, pad, extra=symmetry_error
        )
        seed_pad = EPS_FACTOR * max(1.0, float(abs(ideal_seed).max()))
        _, vmax, amax = derivative_bounds(ideal_seed, seed_pad)
        proof = context["bases"][base]
        v0 = proof["speed_lower"]
        s0 = proof["signed_projection_cross_lower"]
        k0 = proof["curvature_upper"]
        l0 = proof["length_upper"]
        v = lower_difference(v0, d1)
        error = upper_sum(d1 * amax, vmax * d2, d1 * d2)
        signed = lower_difference(s0, error)
        length = upper_sum(l0, d1)
        curvature = None
        if v > 0:
            curvature = upper_sum(k0 * (v0 / v) ** 3, error / v**3)
        projection_pass = bool(v > 0 and signed > 0)
        length_pass = bool(length <= 3.5)
        curvature_pass = bool(curvature is not None and curvature <= 12)
        curves.append(
            dict(
                index=index,
                base_index=base,
                normal=(ideal_rotation @ proof["normal"]).tolist(),
                D0=d0,
                D1=d1,
                D2=d2,
                V0=vmax,
                A0=amax,
                v0=v0,
                S0=s0,
                kappa0=k0,
                L0=l0,
                E=error,
                v_lower=v,
                S_lower=signed,
                kappa_upper=curvature,
                kappa_status="not_available" if curvature is None else "available",
                L_upper=length,
                projection_pass=projection_pass,
                length_pass=length_pass,
                curvature_pass=curvature_pass,
                certified=bool(projection_pass and length_pass and curvature_pass),
            )
        )
    plasma = {}
    for target in ("reference", "selected"):
        plasma[target] = []
        for curve in curves:
            i, b = curve["index"], curve["base_index"]
            direct_seed = float(context["cp"][target][i])
            analytic_seed = context["bases"][b]["analytic_plasma_lower"]
            direct = lower_difference(direct_seed, curve["D0"])
            analytic = lower_difference(analytic_seed, curve["D0"])
            plasma[target].append(
                dict(
                    index=i,
                    base_index=b,
                    direct_seed_lower=direct_seed,
                    direct_lower=direct,
                    direct_pass=bool(direct >= 0.08),
                    analytic_seed_lower=analytic_seed,
                    analytic_lower=analytic,
                    analytic_pass=bool(analytic >= 0.08),
                )
            )
    pairs = []
    for pair_index, (i, j) in enumerate(context["pair_order"]):
        direct_seed = float(context["cc"][pair_index])
        analytic_seed = context["analytic_cc"]
        direct = lower_difference(direct_seed, curves[i]["D0"], curves[j]["D0"])
        analytic = lower_difference(analytic_seed, curves[i]["D0"], curves[j]["D0"])
        pairs.append(
            dict(
                i=i,
                j=j,
                direct_seed_lower=direct_seed,
                direct_lower=direct,
                direct_pass=bool(direct >= 0.06),
                analytic_seed_lower=analytic_seed,
                analytic_lower=analytic,
                analytic_pass=bool(analytic >= 0.06),
            )
        )
    plasma_rows = plasma["reference"] + plasma["selected"]
    gates = dict(
        regularity=all(row["v_lower"] > 0 for row in curves),
        projection=all(row["projection_pass"] for row in curves),
        length=all(row["length_pass"] for row in curves),
        curvature=all(row["curvature_pass"] for row in curves),
        direct_plasma=all(row["direct_pass"] for row in plasma_rows),
        analytic_plasma=all(row["analytic_pass"] for row in plasma_rows),
        direct_coil=all(row["direct_pass"] for row in pairs),
        analytic_coil=all(row["analytic_pass"] for row in pairs),
    )
    certified = all(gates.values())
    return dict(
        schema_version=1,
        kind="cumulative-coil-perturbation",
        status="certified" if certified else "uncertified",
        calculation_complete=True,
        certified=certified,
        reason=None if certified else "one or more geometric gates not certified",
        case=dict(snapshot["case"]),
        curves=curves,
        plasma=plasma,
        pairs=pairs,
        gates=gates,
        **SCOPE,
    )


def _finite_report(value):
    if isinstance(value, dict):
        return all(_finite_report(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite_report(v) for v in value)
    if type(value) is float:
        return math.isfinite(value)
    return value is None or type(value) in (bool, int, str)


def independent_certificate(seed_snapshot, selected_geometry_report, candidate_coefficients):
    """Return a complete independent certificate, including scientific rejection."""
    context = seed_context(seed_snapshot, selected_geometry_report)
    candidate = real(candidate_coefficients, "candidate coefficients", finite=False)
    require(candidate.shape == context["coefficients"].shape, "candidate coefficient shape")
    if not np.isfinite(candidate).all():
        return _empty_report(seed_snapshot, "nonfinite candidate coefficients")
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            result = _calculate(seed_snapshot, context, candidate)
        if not _finite_report(result):
            return _empty_report(seed_snapshot, "nonfinite bound arithmetic")
        return result
    except (OverflowError, FloatingPointError):
        return _empty_report(seed_snapshot, "nonfinite bound arithmetic")


def compare_certificate(actual, expected, path="certificate"):
    """Every key and classification is mandatory; no float coercion of flags."""
    require(type(actual) is type(expected), f"{path}: exact JSON type required")
    if isinstance(expected, dict):
        require(set(actual) == set(expected), f"{path}: exact keys required")
        for key, value in expected.items():
            compare_certificate(actual[key], value, f"{path}.{key}")
    elif isinstance(expected, list):
        require(len(actual) == len(expected), f"{path}: complete ordered records required")
        for i, value in enumerate(expected):
            compare_certificate(actual[i], value, f"{path}[{i}]")
    elif isinstance(expected, float):
        close(actual, expected, path)
    else:
        require(actual == expected, f"{path}: identity or classification differs")


def audit_certificate(seed_snapshot, selected_geometry_report, candidate_coefficients, recorded):
    expected = independent_certificate(
        seed_snapshot, selected_geometry_report, candidate_coefficients
    )
    compare_certificate(recorded, expected)
    return expected
