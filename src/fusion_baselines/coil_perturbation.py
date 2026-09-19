"""Pure cumulative Fourier perturbation certificates, not source-file admission.

The caller must independently bind the original snapshot and selected geometry
audit set. Their original schemas omit the snapshot hash and support Z origin;
structural/proof checks here cannot replace that external provenance binding.
Frozen seed-proof primitives are reused; all new perturbation bounds are local.
No native fields, file reads, LPs, sampling of candidate curves or mutations.
"""

import copy
import math
from pathlib import PurePosixPath

import numpy as np

from fusion_baselines import clear_coil_geometry_audit as legacy

EPS = 128 * np.finfo(float).eps
TARGETS = ("reference", "selected")
GATES = (
    "regularity",
    "projection",
    "length",
    "curvature",
    "direct_plasma",
    "analytic_plasma",
    "direct_coil",
    "analytic_coil",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value, shape=None):
    data = np.asarray(value)
    require(data.dtype.kind in "iuf", "real numerical values without coercion required")
    require(shape is None or data.shape == shape, "exact numerical array shape required")
    require(np.isfinite(data).all(), "finite seed/proof values required")
    return np.array(data, dtype=float, copy=True)


def scalar(value):
    return float(finite(value, ()))


def close(actual, expected, label):
    a, b = finite(actual), finite(expected)
    require(a.shape == b.shape and np.all(abs(a - b) <= 5e-12), label)


def pad(*terms):
    return float(EPS * max(1.0, math.fsum(abs(float(x)) for x in terms)))


def upper(*terms):
    return float(math.fsum(terms) + pad(*terms))


def lower(first, *losses):
    return float(first - math.fsum(losses) - pad(first, *losses))


def derivative_bounds(coefficient_magnitudes):
    """Bounds from already nonnegative, outward-padded coefficient magnitudes."""
    magnitudes = np.asarray(coefficient_magnitudes)
    amplitudes = np.hypot(magnitudes[:, 1::2], magnitudes[:, 2::2])
    omega = 2 * np.pi * np.arange(1, amplitudes.shape[1] + 1)
    vectors = [magnitudes[:, 0] + amplitudes.sum(axis=1)]
    vectors += [(amplitudes * omega**k).sum(axis=1) for k in (1, 2)]
    return [upper(float(np.linalg.norm(v))) for v in vectors]


def _source_schema(sources):
    require(isinstance(sources, dict) and set(sources) == set(TARGETS), "both target sources")
    for target in sources.values():
        require(isinstance(target, dict) and set(target) == {"input", "wout"}, "source pair")
        for reference in target.values():
            require(
                isinstance(reference, dict)
                and set(reference) == {"path", "sha256"}
                and type(reference["path"]) is str
                and PurePosixPath(reference["path"]).is_absolute()
                and type(reference["sha256"]) is str
                and len(reference["sha256"]) == 64
                and all(c in "0123456789abcdef" for c in reference["sha256"]),
                "original absolute hash-bound source reference required",
            )


def _lp_chain(rows, length):
    require(isinstance(rows, list) and len(rows) == 2, "two original LP certificates required")
    for row in rows:
        require(
            set(row)
            == {"solved", "errors", "objective", "dual_objective", "passed", "infeasibility_proven"}
            and row["solved"] is True
            and row["passed"] is True
            and row["infeasibility_proven"] is False,
            "original positive LP proof chain required",
        )
        limits = dict(
            primal=1e-10,
            dual_sign=1e-8,
            stationarity=1e-8,
            complementarity=1e-8,
            primal_dual_gap=1e-8,
            reported_objective=5e-12,
            reported_slack=5e-12,
        )
        require(set(row["errors"]) == set(limits), "all original LP residuals required")
        require(
            all(0 <= scalar(row["errors"][k]) <= v for k, v in limits.items()),
            "LP residual limits required, not only pass flags",
        )
        close(row["objective"], length, "LP/support length identity")
        require(
            abs(scalar(row["objective"]) - scalar(row["dual_objective"])) <= 1e-8,
            "LP primal-dual objective agreement",
        )


def _seed_proofs(seed, report):
    legacy.validate_snapshot(seed)
    _source_schema(seed["sources"])
    require(
        all(
            isinstance(row["matrix"], list)
            and len(row["matrix"]) == 3
            and all(
                isinstance(axis, list)
                and len(axis) == 3
                and all(type(value) is float for value in axis)
                for axis in row["matrix"]
            )
            for row in seed["physical"]
        ),
        "original floating-point symmetry matrices without boolean aliases required",
    )
    nbase, order = seed["nbase"], seed["order"]
    expected_case = next(c for c in legacy.cases() if c["label"] == f"n{nbase}-shape-d100mm")
    require(
        seed["case"] == expected_case
        and all(type(seed["case"][k]) is type(v) for k, v in expected_case.items()),
        "exact selected shaped100mm case required",
    )
    require(
        set(report)
        == {
            "case",
            "coils",
            "distances",
            "geometry_pass",
            "available_geometry",
            "sum_base_lengths",
            "analytic_coil_lower",
        }
        and report["case"] == seed["case"]
        and report["geometry_pass"] is True
        and report["available_geometry"] is True
        and isinstance(report["coils"], list)
        and len(report["coils"]) == nbase,
        "complete original selected geometric audit set required",
    )
    base = finite(seed["base_coefficients"], (nbase, 3, 2 * order + 1))
    for i, row in enumerate(report["coils"]):
        require(
            set(row)
            == {
                "base_index",
                "lp_certificates",
                "exact_repeat",
                "continuous",
                "export_transfer",
                "support_coefficients",
                "available_geometry",
            }
            and type(row["base_index"]) is int
            and row["base_index"] == i
            and row["exact_repeat"] is True
            and row["available_geometry"] is True,
            "ordered complete base proof chain required",
        )
        h = finite(row["support_coefficients"], (2 * (order - 1) + 1,))
        continuous, exported = row["continuous"], row["export_transfer"]
        require(
            set(continuous)
            == {
                "enclosure_lower",
                "rho_lower",
                "radial_lower",
                "length",
                "length_upper",
                "curvature_upper",
                "L_h",
                "L_rho",
                "L_S",
                "floating_pad",
                "interval_arithmetic",
                "support_pass",
                "length_pass",
                "curvature_pass",
                "planar_self_disjoint",
            },
            "complete original support certificate required",
        )
        require(
            all(
                continuous[k] is True
                for k in ("support_pass", "length_pass", "curvature_pass", "planar_self_disjoint")
            )
            and continuous["interval_arithmetic"] is False,
            "simple strictly convex original support proof required",
        )
        for key, value in continuous.items():
            if key not in {
                "support_pass",
                "length_pass",
                "curvature_pass",
                "planar_self_disjoint",
                "interval_arithmetic",
            }:
                require(scalar(value) >= 0, "nonnegative finite support proof scalars")
        require(
            continuous["rho_lower"] >= 0.10
            and continuous["floating_pad"] > 0
            and continuous["radial_lower"] >= expected_case["r_floor"]
            and 0 < continuous["length_upper"] <= 3.5
            and 0 < continuous["curvature_upper"] <= 12,
            "original support physical gates required",
        )
        frequencies = np.repeat(np.arange(1, order), 2)
        close(continuous["L_h"], frequencies @ abs(h[1:]), "support derivative bound")
        close(
            continuous["L_rho"],
            frequencies * abs(1 - frequencies**2) @ abs(h[1:]),
            "support curvature-radius derivative bound",
        )
        close(continuous["length"], 2 * np.pi * h[0], "support contour length")
        close(
            continuous["length_upper"],
            continuous["length"] + 2 * np.pi * continuous["floating_pad"],
            "padded original length",
        )
        close(continuous["curvature_upper"], 1 / continuous["rho_lower"], "support curvature")
        # The historical report lacks the original origin. Recover the only
        # translation consistent with this actual exported curve; its immutable
        # association with the original LP/targets remains the binder's job.
        phi = (i + 0.5) * np.pi / (2 * nbase)
        radial = np.array([math.cos(phi), math.sin(phi), 0.0])
        center = [float(radial @ base[i, :, 0] - h[2]), float(base[i, 2, 0] - h[1])]
        expected_pad = EPS * max(1.0, abs(h).sum(), max(abs(v) for v in center), continuous["L_S"])
        close(continuous["floating_pad"], expected_pad, "original support coefficient pad")
        angles = np.arange(1024) * 2 * np.pi / 1024
        rho_samples = legacy.support_basis(order - 1, angles) @ (h * np.r_[1, 1 - frequencies**2])
        rho_lower = float(rho_samples.min() - np.pi / 1024 * continuous["L_rho"] - expected_pad)
        close(continuous["rho_lower"], rho_lower, "original1024 support radius lower bound")
        expected = legacy.export_coefficients(h, center, phi, order)
        close(base[i], expected, "actual seed must match once-traversed support export")
        close(
            continuous["radial_lower"],
            center[0]
            - h[0]
            - sum((-1) ** m * h[2 * m] for m in range(1, order))
            - continuous["floating_pad"],
            "support radial identity",
        )
        replay = legacy.export_certificate(
            continuous, h, expected, base[i], expected_case["r_floor"], expected_case["d"]
        )
        require(set(exported) == set(replay), "complete original export transfer required")
        for key, expected_value in replay.items():
            if type(expected_value) is bool:
                require(exported[key] is expected_value, "exact export proof classification")
            else:
                close(exported[key], expected_value, "export transfer arithmetic identity")
        require(
            all(
                exported[k] is True
                for k in (
                    "support_pass",
                    "length_pass",
                    "curvature_pass",
                    "plasma_pass",
                    "controlled_projection_self_disjoint",
                )
            )
            and scalar(exported["speed_lower"]) > 0
            and scalar(exported["signed_projection_cross_lower"]) > 0,
            "positive regular simple exported seed projection required",
        )
        _lp_chain(row["lp_certificates"], continuous["length"])
    close(
        report["sum_base_lengths"],
        sum(r["continuous"]["length"] for r in report["coils"]),
        "total original support length",
    )
    radial_min = min(r["continuous"]["radial_lower"] for r in report["coils"])
    export_error = max(
        r["export_transfer"]["position_error"] + r["export_transfer"]["coefficient_rounding_pad"]
        for r in report["coils"]
    )
    close(
        report["analytic_coil_lower"],
        2 * radial_min * np.sin(np.pi / (4 * nbase)) - 2 * export_error,
        "original analytic pair-distance arithmetic",
    )
    require(report["analytic_coil_lower"] >= 0.06, "original analytic pair-distance gate")
    return base


def _distances(report, nphysical):
    rows = report["distances"]
    expected_levels = [
        (target, n, offset) for target in TARGETS for n, offset in ((256, 0), (512, 0), (512, 0.5))
    ]
    require(isinstance(rows, list) and len(rows) == 6, "all six original distance reports")
    pairs = [(i, j) for i in range(nphysical) for j in range(i + 1, nphysical)]
    cp = {target: [[] for _ in range(nphysical)] for target in TARGETS}
    cc = [[] for _ in pairs]
    for row, (target, n, offset) in zip(rows, expected_levels, strict=True):
        require(
            set(row)
            == {
                "target",
                "ncoil",
                "nphi",
                "ntheta",
                "offset",
                "full_torus",
                "curve_cover",
                "surface_cover",
                "floating_pad",
                "interval_arithmetic",
                "coil_pairs",
                "plasma_distances",
                "lengths_sampled",
                "curvature_sampled",
                "sampled_length_pass",
                "sampled_curvature_pass",
                "coil_pass",
                "plasma_pass",
            },
            "complete original direct-distance report required",
        )
        require(
            row["target"] == target
            and type(row["ncoil"]) is int
            and row["ncoil"] == 1024
            and type(row["nphi"]) is int
            and row["nphi"] == n
            and type(row["ntheta"]) is int
            and row["ntheta"] == n
            and type(row["offset"]) is type(offset)
            and row["offset"] == offset
            and row["full_torus"] is True
            and row["interval_arithmetic"] is False,
            "ordered original distance grid identities required",
        )
        require(
            all(
                row[k] is True
                for k in (
                    "sampled_length_pass",
                    "sampled_curvature_pass",
                    "coil_pass",
                    "plasma_pass",
                )
            ),
            "all separate original direct geometry gates required",
        )
        cover = finite(row["curve_cover"], (nphysical,))
        surface_cover, floating_pad = scalar(row["surface_cover"]), scalar(row["floating_pad"])
        require(
            np.all(cover > 0) and surface_cover > 0 and floating_pad > 0,
            "positive continuous covering bounds required",
        )
        lengths = finite(row["lengths_sampled"], (nphysical,))
        curvature = finite(row["curvature_sampled"], (nphysical,))
        require(
            np.all((lengths > 0) & (lengths <= 3.5))
            and np.all((curvature >= 0) & (curvature <= 12)),
            "original sampled geometry thresholds required",
        )
        require(
            len(row["coil_pairs"]) == len(pairs) and len(row["plasma_distances"]) == nphysical,
            "all original pairs and curves",
        )
        for k, (item, (i, j)) in enumerate(zip(row["coil_pairs"], pairs, strict=True)):
            require(
                set(item) == {"i", "j", "sampled", "lower"}
                and type(item["i"]) is type(item["j"]) is int
                and (item["i"], item["j"]) == (i, j),
                "exact original pair identity",
            )
            value, sampled = scalar(item["lower"]), scalar(item["sampled"])
            close(
                value,
                max(0.0, sampled - cover[i] - cover[j] - floating_pad),
                "pair continuous cover",
            )
            require(0.06 <= value <= sampled, "original continuous pair gate")
            cc[k].append(value)
        for i, item in enumerate(row["plasma_distances"]):
            require(
                set(item) == {"i", "sampled", "lower"}
                and type(item["i"]) is int
                and item["i"] == i,
                "exact original CP identity",
            )
            value, sampled = scalar(item["lower"]), scalar(item["sampled"])
            close(
                value,
                max(0.0, sampled - cover[i] - surface_cover - floating_pad),
                "CP continuous cover",
            )
            require(0.08 <= value <= sampled, "original continuous plasma gate")
            cp[target][i].append(value)
    return {target: [min(v) for v in cp[target]] for target in TARGETS}, [min(v) for v in cc]


def _empty(case, reason):
    return dict(
        schema_version=1,
        kind="cumulative-coil-perturbation",
        status="uncertified",
        calculation_complete=False,
        certified=False,
        reason=reason,
        case=copy.deepcopy(case),
        curves=[],
        plasma={key: [] for key in TARGETS},
        pairs=[],
        gates={key: False for key in GATES},
        field_calls=0,
        gradient_calls=0,
        equilibrium_solves=0,
        search_allowed=False,
        field_pass=False,
        transfer_pass=False,
        step4_pass=False,
    )


def candidate_certificate(seed_snapshot, selected_geometry_report, candidate_coefficients):
    """Return a cumulative geometric certificate against an immutable bound seed.

    Malformed/unproven seed inputs raise ValueError. Finite candidates outside
    this sufficient certificate's domain return ordinary negative certificates.
    """
    seed, report = copy.deepcopy(seed_snapshot), copy.deepcopy(selected_geometry_report)
    try:
        base = _seed_proofs(seed, report)
        cp0, cc0 = _distances(report, 4 * seed["nbase"])
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("malformed original seed or proof schema") from error
    candidate = np.asarray(candidate_coefficients)
    require(
        candidate.dtype.kind in "iuf" and candidate.shape == base.shape,
        "candidate must preserve the complete real named Fourier shape",
    )
    if not np.isfinite(candidate).all():
        return _empty(seed["case"], "nonfinite candidate coefficients")
    candidate = np.array(candidate, dtype=float, copy=True)
    result = _empty(seed["case"], None)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            for index, mapping in enumerate(seed["physical"]):
                i, q = mapping["base_index"], np.asarray(mapping["matrix"]).T
                signs = np.array([-1.0, -1.0, 1.0]) if mapping["period"] else np.ones(3)
                if mapping["flip"]:
                    signs *= [1.0, -1.0, -1.0]
                ideal = np.diag(signs)
                require(
                    np.linalg.det(q) > 0 and np.max(abs(q.T @ q - np.eye(3))) <= EPS,
                    "proper orthogonal physical symmetry required",
                )
                actual_seed, actual_candidate = q @ base[i], q @ candidate[i]
                coefficient_pad = EPS * max(
                    1.0, abs(actual_seed).max(), abs(actual_candidate).max()
                )
                magnitude = (
                    abs(actual_candidate - actual_seed)
                    + abs((q - ideal) @ base[i])
                    + coefficient_pad
                )
                d0, d1, d2 = derivative_bounds(magnitude)
                ideal_seed = ideal @ base[i]
                seed_pad = EPS * max(1.0, abs(ideal_seed).max())
                _, vmax, amax = derivative_bounds(abs(ideal_seed) + seed_pad)
                proof = report["coils"][i]["export_transfer"]
                v0, s0, k0, l0 = [
                    float(proof[k])
                    for k in (
                        "speed_lower",
                        "signed_projection_cross_lower",
                        "curvature_upper",
                        "length_upper",
                    )
                ]
                error = upper(d1 * amax, vmax * d2, d1 * d2)
                v_lower, s_lower, length = lower(v0, d1), lower(s0, error), upper(l0, d1)
                curvature = None
                if v_lower > 0:
                    curvature = upper(k0 * (v0 / v_lower) ** 3, error / v_lower**3)
                phi = (i + 0.5) * np.pi / (2 * seed["nbase"])
                normal = ideal @ np.array([-math.sin(phi), math.cos(phi), 0.0])
                projection = bool(v_lower > 0 and s_lower > 0)
                length_pass, curvature_pass = (
                    bool(length <= 3.5),
                    bool(curvature is not None and curvature <= 12),
                )
                result["curves"].append(
                    dict(
                        index=index,
                        base_index=i,
                        normal=normal.tolist(),
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
                        v_lower=v_lower,
                        S_lower=s_lower,
                        kappa_upper=curvature,
                        kappa_status="available" if curvature is not None else "not_available",
                        L_upper=length,
                        projection_pass=projection,
                        length_pass=length_pass,
                        curvature_pass=curvature_pass,
                        certified=projection and length_pass and curvature_pass,
                    )
                )
                analytic0 = scalar(proof["analytic_plasma_lower"])
                for target in TARGETS:
                    direct, analytic = lower(cp0[target][index], d0), lower(analytic0, d0)
                    result["plasma"][target].append(
                        dict(
                            index=index,
                            base_index=i,
                            direct_seed_lower=cp0[target][index],
                            direct_lower=direct,
                            direct_pass=bool(direct >= 0.08),
                            analytic_seed_lower=analytic0,
                            analytic_lower=analytic,
                            analytic_pass=bool(analytic >= 0.08),
                        )
                    )
            k = 0
            for i in range(len(result["curves"])):
                for j in range(i + 1, len(result["curves"])):
                    a, b = result["curves"][i]["D0"], result["curves"][j]["D0"]
                    direct, analytic = (
                        lower(cc0[k], a, b),
                        lower(report["analytic_coil_lower"], a, b),
                    )
                    result["pairs"].append(
                        dict(
                            i=i,
                            j=j,
                            direct_seed_lower=cc0[k],
                            direct_lower=direct,
                            direct_pass=bool(direct >= 0.06),
                            analytic_seed_lower=float(report["analytic_coil_lower"]),
                            analytic_lower=analytic,
                            analytic_pass=bool(analytic >= 0.06),
                        )
                    )
                    k += 1
    except (FloatingPointError, OverflowError, ZeroDivisionError):
        return _empty(seed["case"], "nonfinite bound arithmetic")
    result["gates"] = dict(
        regularity=all(r["v_lower"] > 0 for r in result["curves"]),
        projection=all(r["projection_pass"] for r in result["curves"]),
        length=all(r["length_pass"] for r in result["curves"]),
        curvature=all(r["curvature_pass"] for r in result["curves"]),
        direct_plasma=all(r["direct_pass"] for rows in result["plasma"].values() for r in rows),
        analytic_plasma=all(r["analytic_pass"] for rows in result["plasma"].values() for r in rows),
        direct_coil=all(r["direct_pass"] for r in result["pairs"]),
        analytic_coil=all(r["analytic_pass"] for r in result["pairs"]),
    )
    accepted = all(result["gates"].values())
    result.update(
        calculation_complete=True,
        certified=accepted,
        status="certified" if accepted else "uncertified",
        reason=None if accepted else "one or more geometric gates not certified",
    )
    return result
