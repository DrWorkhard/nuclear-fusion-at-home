"""Independent saved-array composition for the fixed four-state field probe.

No native producer, file loading or CLI. Callers bind immutable inputs and own
execution/source/resource checks. Successful numerical diagnostics are neither
full flux qualification nor physical admission.
"""

import copy
import hashlib
import json
import math
import numbers

import numpy as np

from fusion_baselines import clear_coil_field_audit as numerical
from fusion_baselines import coupled_coil_audit as frozen
from fusion_baselines import protected_coil_search_audit as search_audit

SCOPE = dict(
    field_pass=False,
    physical_admission=False,
    step4_pass=False,
    ms1_reached=False,
    sota_advance=False,
    pareto_dominance=False,
    full_flux_qualification=False,
)
DIRECT = {
    prefix + "_" + quantity for prefix in ("boundary", "inner", "loop") for quantity in ("B", "A")
}
METRICS = {
    "JN",
    "JV",
    "scale",
    "B2_scale",
    "unit_flux",
    "target_flux",
    "flux",
    "current",
    "normal_rms",
    "normal_max",
    "vector_rms",
    "boundary_B_rms",
    "lengths",
    "kappa_max",
    "coil_distance",
    "surface_distance",
    "geometry_penalty",
    "J",
    "frozen_scale",
}
RAW = DIRECT | {
    "boundary_points",
    "boundary_normals",
    "boundary_weights",
    "inner_points",
    "inner_target",
    "loop_points",
    "loop_tangents",
    "coil_positions",
    "coil_tangents",
    "coil_currents",
}
WORK = dict(
    initializer_scalar_checks=1,
    metric_reconstructions=1,
    direct_statistics=6,
    direct_vectors=384,
    direct_scalar_components=1152,
    diagnostic_flux_checks=1,
)
CONSTRUCTION = dict(
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
)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _json(value):
    return numerical.json_value(value)


def _encoded(value):
    return (
        json.dumps(_json(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _same(actual, expected, label):
    _need(_encoded(actual) == _encoded(expected), "exact " + label)


def _numeric(value, shape=None):
    raw = np.asarray(value, dtype=object)
    _need(
        all(isinstance(v, numbers.Real) and not isinstance(v, (bool, np.bool_)) for v in raw.flat),
        "real values without boolean/string aliases",
    )
    try:
        data = np.array(value, dtype=float, copy=True)
    except (TypeError, OverflowError) as error:
        raise ValueError("finite binary64 values") from error
    _need(data.size > 0 and np.isfinite(data).all(), "complete finite values")
    _need(shape is None or data.shape == shape, "exact numeric shape")
    return data


def _scalar(value):
    return float(_numeric(value, ()))


def _bits(actual, expected, label):
    a, b = _numeric(actual), _numeric(expected)
    _need(
        a.shape == b.shape and a.tobytes() == b.tobytes(), "exact coordinate/current bits: " + label
    )


def _comparison(actual, expected, *, rtol=5e-10, atol=1e-12):
    a, b = _numeric(actual), _numeric(expected)
    _need(a.shape == b.shape, "comparison shape")
    error, scale = float(np.max(abs(a - b))), float(np.max(abs(b)))
    _need(
        math.isfinite(error) and (error <= atol or error <= rtol * scale),
        "independent numerical mismatch",
    )
    return dict(
        actual=_json(actual),
        independent=_json(expected),
        absolute_error=error,
        relative_error=error / scale if scale else None,
        rtol=rtol,
        atol=atol,
        passed=True,
    )


def _case(case):
    _need(type(case) is dict, "case mapping")
    n = case.get("nbase")
    _need(type(n) is int and n in (6, 8), "registered coil class")
    _same(
        case,
        dict(
            label=f"reference-n{n}-N",
            method="N",
            nbase=n,
            order=5 if n == 6 else 7,
            seed_label=f"n{n}-shape-d100mm",
            target="reference",
        ),
        "fixed reference N case",
    )


def _initializer(seed, input_data, ncoil, guard):
    # Reuse the already qualified pure scalar reconstruction, not its file-I/O driver.
    from audit_protected_fine_fields import _initializer_flux

    return _initializer_flux(seed, dict(input=input_data), ncoil, guard)


def _direct(snapshot, arrays, ncoil):
    from audit_clear_coil_field_start import direct_fields

    return direct_fields(snapshot, arrays, ncoil)


def _identity(seed, x, case, snapshot):
    _case(case)
    _need(
        type(snapshot) is dict
        and set(snapshot)
        == {
            "schema_version",
            "nfp",
            "nbase",
            "order",
            "names",
            "base_coefficients",
            "physical",
            "scale",
            "B2_scale",
            "unit_flux",
            "target_flux",
            "seed_unit_flux",
            "method",
            "sources",
            "construction",
            "initialization_work",
            "seed_geometry",
        },
        "complete coarse snapshot schema",
    )
    _same(snapshot["construction"], CONSTRUCTION, "registered coarse construction")
    _same(
        snapshot["initialization_work"],
        dict(seed_A_calls=1, seed_A_points=256),
        "original initialization work",
    )
    _same(seed["schema_version"], 1, "original seed schema")
    _same(snapshot["schema_version"], 1, "snapshot schema")
    n, order = case["nbase"], case["order"]
    names = frozen.parameter_names(n, order)
    _same(seed["names"], names, "original canonical names")
    _same(snapshot["names"], names, "candidate canonical names")
    for key, value in dict(nbase=n, order=order, nfp=2).items():
        _same(seed[key], value, "original " + key)
        _same(snapshot[key], value, "snapshot " + key)
    _same(snapshot["method"], "N", "method")
    seed_x = _numeric(seed["base_coefficients"], (n, 3, 2 * order + 1)).ravel()
    x = _numeric(x, seed_x.shape)
    _bits(_numeric(snapshot["base_coefficients"]).ravel(), x, "requested state")
    _same(snapshot["seed_geometry"], seed, "original seed geometry")
    _same(snapshot["sources"], seed["sources"]["reference"], "reference target sources")
    numerical.validate_snapshot(snapshot)
    unit_flux, target_flux = _scalar(snapshot["unit_flux"]), _scalar(snapshot["target_flux"])
    _need(
        abs(unit_flux) > 1e-12
        and target_flux != 0
        and abs(_scalar(snapshot["seed_unit_flux"])) > 1e-12,
        "nondegenerate coarse and original seed flux",
    )
    _same(_scalar(snapshot["scale"]), target_flux / unit_flux, "exact coarse normalization")
    _need(len(snapshot["physical"]) == len(seed["physical"]) == 4 * n, "all physical copies")
    for actual, original in zip(snapshot["physical"], seed["physical"], strict=True):
        _same({k: v for k, v in actual.items() if k != "current"}, original, "actual matrix copy")
        expected = 1e5 * snapshot["scale"] * (-1 if original["flip"] else 1)
        _bits([actual["current"]], [expected], "signed physical current")
    return names, x, seed_x


def _flux(metrics):
    target, actual = _scalar(metrics["target_flux"]), _scalar(metrics["flux"])
    _need(target != 0, "nonzero signed target flux")
    relative = abs(actual - target) / abs(target)
    _need(math.isfinite(relative), "finite diagnostic flux discrepancy")
    return dict(
        flux=actual,
        target_flux=target,
        relative_error=relative,
        relative_limit=1e-6,
        passed=bool(relative <= 1e-6),
    )


def _gates(metrics):
    _need(
        all(_scalar(metrics[key]) >= 0 for key in ("normal_rms", "normal_max", "vector_rms")),
        "nonnegative field errors",
    )
    return dict(
        normal_rms=bool(_scalar(metrics["normal_rms"]) <= 1e-4),
        normal_max=bool(_scalar(metrics["normal_max"]) <= 1e-3),
        vector_rms=bool(_scalar(metrics["vector_rms"]) <= 0.01),
        current=bool(abs(_scalar(metrics["current"])) <= 500000),
    )


def audit_model(
    seed,
    x,
    case,
    level,
    snapshot,
    initialization,
    metrics,
    arrays,
    *,
    input_data,
    target,
    control_bundle=None,
    control_snapshot=None,
    guard=lambda: None,
):
    """Reconstruct one complete model; inconsistent inputs raise, flux failure is retained.

    ``target`` is the independent archived target at this level's ninner. Historical
    control bundle/snapshot are required together for a control's level zero only.
    The same new coarse ``snapshot`` must be supplied for all six state levels.
    """
    _need(callable(guard), "callable phase deadline/resource guard")
    guard()
    numerical.validate_level(level)
    names, coordinates, seed_x = _identity(seed, x, case, snapshot)
    _need(
        type(initialization) is dict
        and set(initialization)
        == {"seed_unit_flux", "names", "seed_x", "ncoil", "initialization_work"},
        "exact original initializer schema",
    )
    _same(initialization["names"], names, "initializer names")
    _bits(initialization["seed_x"], seed_x, "initializer ORIGINAL seed")
    _same(initialization["ncoil"], level["ncoil"], "initializer coil resolution")
    _same(
        initialization["initialization_work"],
        dict(seed_A_calls=1, seed_A_points=256),
        "initializer work",
    )
    _same(snapshot["initialization_work"], initialization["initialization_work"], "snapshot work")
    _same(snapshot["B2_scale"], target["B2_scale"], "fixed archived B2")
    _same(snapshot["target_flux"], target["target_flux"], "independent signed target flux")
    _same(target["ninner"], level["ninner"], "interior resolution")
    _need(
        _scalar(snapshot["B2_scale"]) > 0 and _scalar(snapshot["target_flux"]) != 0,
        "positive normalization and nonzero signed target flux",
    )
    _need(type(arrays) is dict and set(arrays) == RAW, "complete raw array names")
    for value in arrays.values():
        _numeric(value)
    for key in ("inner_points", "inner_target"):
        _bits(arrays[key], target[key], "active archived64 " + key)
    guard()
    independent_initializer = _initializer(seed, input_data, level["ncoil"], guard)
    guard()
    _need(abs(_scalar(independent_initializer)) > 1e-12, "nondegenerate seed initializer")
    initializer_check = _comparison(
        initialization["seed_unit_flux"], independent_initializer, rtol=5e-10, atol=0
    )
    if level["index"] == 0:
        _bits([snapshot["seed_unit_flux"]], [initialization["seed_unit_flux"]], "coarse seed flux")
    guard()
    own = numerical.composed_metrics(snapshot, input_data, arrays, target, "N", level)
    guard()
    _need(type(metrics) is dict and set(metrics) == METRICS, "complete native metric schema")
    _need(metrics["frozen_scale"] is (level["index"] != 0), "coarse/fine normalization flag")
    metric_checks = {
        key: _comparison(metrics[key], own[key]) for key in sorted(METRICS - {"frozen_scale"})
    }
    own_metrics = {key: _json(own[key]) for key in METRICS - {"frozen_scale"}}
    own_metrics["frozen_scale"] = metrics["frozen_scale"]
    for key in ("scale", "B2_scale", "target_flux"):
        _same(metrics[key], snapshot[key], "unchanged " + key)
    _bits([metrics["current"]], [1e5 * snapshot["scale"]], "recorded current")
    _need(
        _scalar(metrics["unit_flux"]) * _scalar(initialization["seed_unit_flux"]) > 0,
        "unchanged signed unit-flux orientation",
    )
    coarse = None
    if level["index"] == 0:
        coarse = dict(
            unit_flux=_comparison(own["unit_flux"], snapshot["unit_flux"], atol=0),
            calibrated_flux=_comparison(own["flux"], snapshot["target_flux"], rtol=1e-12, atol=0),
        )
    guard()
    direct = _direct(snapshot, arrays, level["ncoil"])
    guard()
    _need(type(direct) is dict and set(direct) == DIRECT, "six direct B/A statistics")
    _need(all(0 <= _scalar(value) <= 5e-10 for value in direct.values()), "direct field limit")
    replay = None
    _need((control_bundle is None) == (control_snapshot is None), "both historical control inputs")
    if control_bundle is not None:
        _need(level["index"] == 0, "historical control replay only at coarse level")
        _identity(seed, coordinates, case, control_snapshot)
        _bits(control_bundle["state"]["x"], coordinates, "historical control coordinates")
        for key in ("B2_scale", "target_flux", "sources", "names", "seed_geometry", "construction"):
            _same(snapshot[key], control_snapshot[key], "control " + key)
        old_metrics = control_bundle["state"]["metrics"]
        _need(
            set(old_metrics) == METRICS and old_metrics["frozen_scale"] is False,
            "historical coarse metric schema",
        )
        replay = {
            key: _comparison(metrics[key], old_metrics[key])
            for key in sorted(METRICS - {"frozen_scale"})
        }
        replay["snapshot_scale"] = _comparison(snapshot["scale"], control_snapshot["scale"])
        replay["bundle_value"] = _comparison(metrics["J"], control_bundle["state"]["value"])
    flux = _flux(own_metrics)
    guard()
    return _json(
        dict(
            schema_version=1,
            kind="fixed-field-probe-model-audit",
            complete=True,
            case=copy.deepcopy(case),
            level=copy.deepcopy(level),
            names=names,
            x=coordinates.tolist(),
            state_sha256=hashlib.sha256(
                _encoded(dict(schema_version=1, names=names, x=coordinates.tolist()))
            ).hexdigest(),
            snapshot=copy.deepcopy(snapshot),
            metrics=own_metrics,
            metric_checks=metric_checks,
            initializer_check=initializer_check,
            direct_errors=direct,
            control_replay=replay,
            coarse_normalization=coarse,
            diagnostic_flux=flux,
            absolute_gates=_gates(own_metrics),
            numerical_pass=flux["passed"],
            work=WORK.copy(),
            work_expected=WORK.copy(),
            **SCOPE,
        )
    )


def _check_comparison(check, *, rtol=5e-10, atol=1e-12):
    _need(type(check) is dict and check.get("passed") is True, "successful comparison")
    _same(
        check,
        _comparison(check["actual"], check["independent"], rtol=rtol, atol=atol),
        "reconstructed comparison",
    )


def _model_report(row, level):
    _need(
        type(row) is dict
        and set(row)
        == {
            "schema_version",
            "kind",
            "complete",
            "case",
            "level",
            "names",
            "x",
            "state_sha256",
            "snapshot",
            "metrics",
            "metric_checks",
            "initializer_check",
            "direct_errors",
            "control_replay",
            "coarse_normalization",
            "diagnostic_flux",
            "absolute_gates",
            "numerical_pass",
            "work",
            "work_expected",
        }
        | set(SCOPE),
        "exact saved model-audit schema",
    )
    _need(
        type(row["schema_version"]) is int
        and row["schema_version"] == 1
        and row["kind"] == "fixed-field-probe-model-audit"
        and row["complete"] is True,
        "completed model audit",
    )
    _need(all(row[key] is False for key in SCOPE), "unchanged nonphysical scope")
    _same(row["work"], WORK, "complete scalar and vector work")
    _same(row["work_expected"], WORK, "required scalar and vector work")
    _same(row["level"], level, "ordered six grids")
    _identity(row["snapshot"]["seed_geometry"], row["x"], row["case"], row["snapshot"])
    _same(row["names"], row["snapshot"]["names"], "saved names")
    digest = hashlib.sha256(
        _encoded(dict(schema_version=1, names=row["names"], x=row["x"]))
    ).hexdigest()
    _same(row["state_sha256"], digest, "named state digest")
    metrics = row["metrics"]
    _need(type(metrics) is dict and set(metrics) == METRICS, "saved metrics")
    _need(metrics["frozen_scale"] is (level["index"] != 0), "saved normalization flag")
    _need(set(row["metric_checks"]) == METRICS - {"frozen_scale"}, "every metric comparison")
    for key, check in row["metric_checks"].items():
        _check_comparison(check)
        _same(check["independent"], metrics[key], "independent metric " + key)
    _check_comparison(row["initializer_check"], atol=0)
    _need(
        abs(_scalar(row["initializer_check"]["independent"])) > 1e-12,
        "nondegenerate independent initializer",
    )
    if level["index"] == 0:
        _bits(
            [row["initializer_check"]["actual"]],
            [row["snapshot"]["seed_unit_flux"]],
            "saved coarse initializer",
        )
        coarse = dict(
            unit_flux=_comparison(metrics["unit_flux"], row["snapshot"]["unit_flux"], atol=0),
            calibrated_flux=_comparison(
                metrics["flux"], row["snapshot"]["target_flux"], rtol=1e-12, atol=0
            ),
        )
        _same(row["coarse_normalization"], coarse, "coarse normalization comparisons")
    else:
        _need(row["coarse_normalization"] is None, "no finer recalibration")
    _need(
        set(row["direct_errors"]) == DIRECT
        and all(0 <= _scalar(error) <= 5e-10 for error in row["direct_errors"].values()),
        "every sampled direct comparison",
    )
    replay = row["control_replay"]
    if replay is not None:
        _need(
            level["index"] == 0
            and type(replay) is dict
            and set(replay) == METRICS - {"frozen_scale"} | {"snapshot_scale", "bundle_value"},
            "complete coarse replay comparisons",
        )
        for check in replay.values():
            _check_comparison(check)
    _same(row["diagnostic_flux"], _flux(metrics), "diagnostic flux gate")
    _same(row["absolute_gates"], _gates(metrics), "absolute metric gates")
    _need(
        type(row["numerical_pass"]) is bool
        and row["numerical_pass"] is row["diagnostic_flux"]["passed"],
        "model numerical flag",
    )


def audit_state(reports):
    """Aggregate exactly six complete ordered model audits; keep negative checks."""
    _need(type(reports) is list and len(reports) == 6, "six complete ordered model audits")
    for row, level in zip(reports, numerical.levels(), strict=True):
        _model_report(row, level)
        for key in ("case", "names", "x", "state_sha256", "snapshot"):
            _same(row[key], reports[0][key], "same frozen state " + key)
    refinements = numerical.refinement_checks(
        [dict(level=row["level"], status="completed", metrics=row["metrics"]) for row in reports]
    )
    flux_pass = all(row["diagnostic_flux"]["passed"] for row in reports)
    qualified = bool(refinements["passed"] and flux_pass)
    return dict(
        schema_version=1,
        kind="fixed-field-probe-state-audit",
        complete=True,
        case=copy.deepcopy(reports[0]["case"]),
        state_sha256=reports[0]["state_sha256"],
        models=copy.deepcopy(reports),
        is_control=reports[0]["control_replay"] is not None,
        refinements=refinements,
        diagnostic_flux_pass=flux_pass,
        numerical_pass=qualified,
        work={key: value * 6 for key, value in WORK.items()},
        work_expected={key: value * 6 for key, value in WORK.items()},
        **SCOPE,
    )


def _gain(control, proposal, metric, indices, pairs, final):
    left = [_scalar(row["metrics"][metric]) for row in control["models"]]
    right = [_scalar(row["metrics"][metric]) for row in proposal["models"]]
    _need(all(value >= 0 for value in left + right), "nonnegative RMS errors")
    errors = [max(abs(values[i] - values[j]) for i, j in pairs) for values in (left, right)]
    margin = 1e-7 + 4 * sum(errors)
    deltas = [left[i] - right[i] for i in indices]
    qualified = control["numerical_pass"] and proposal["numerical_pass"]
    passed = (
        qualified
        and all(delta > 0 for delta in deltas)
        and min(left[i] - right[i] for i in final) > margin
    )
    return dict(
        metric=metric,
        levels=indices,
        deltas=deltas,
        control_sensitivity=errors[0],
        proposal_sensitivity=errors[1],
        margin=margin,
        both_states_numerically_qualified=qualified,
        resolved_diagnostic_gain=bool(passed),
        rigorous_error_bound=False,
    )


def compare_pair(control_state, proposal_state, pair_context):
    """Two metric-specific empirical labels and the unrelaxed original Armijo test."""
    for state in (control_state, proposal_state):
        _same(state, audit_state(state["models"]), "reconstructed complete state audit")
    _need(
        control_state["is_control"] is True and proposal_state["is_control"] is False,
        "one independently replayed control then one proposal",
    )
    case = control_state["case"]
    _case(case)
    _same(proposal_state["case"], case, "same case pair")
    _same(pair_context["case"], case, "original pair case")
    control, proposal = control_state["models"][0], proposal_state["models"][0]
    for key in (
        "seed_geometry",
        "sources",
        "names",
        "B2_scale",
        "target_flux",
        "construction",
        "initialization_work",
    ):
        _same(proposal["snapshot"][key], control["snapshot"][key], "same original pair " + key)
    pred, trial = pair_context["predecessor"], pair_context["proposal"]
    for supplied, expected in ((pred["x"], control["x"]), (trial["x"], proposal["x"])):
        _bits(supplied, expected, "frozen predecessor/proposal")
    expected_indices = (93, 94, 2, 10) if case["nbase"] == 6 else (49, 50, 4, 11)
    _same(
        [
            pred["index"],
            trial["index"],
            pair_context["control_manifest_index"],
            pair_context["proposal_manifest_index"],
        ],
        list(expected_indices),
        "fixed pair indices",
    )
    _same(trial["parent_index"], pred["index"], "immediate predecessor")
    _need(
        pred["accepted"] is True
        and trial["accepted"] is False
        and trial["evaluation"] is None
        and trial["reason"] == "geometry-rejected"
        and pair_context["proposal_field_observed"] is False,
        "preserved historical rejection",
    )
    _need(
        pair_context["immediate_saved_predecessor_verified"] is True
        and pair_context["original_proposal_bits_verified"] is True,
        "bound predecessor context",
    )
    size = len(control["names"])
    gradient = _numeric(pair_context["predecessor_gradient"], (size,))
    direction = _numeric(pair_context["direction"], (size,))
    _bits(gradient, pred["evaluation"]["gradient"], "saved original gradient")
    _bits(direction, trial["direction"], "saved original direction")
    _bits(pred["evaluation"]["x"], pred["x"], "predecessor evaluation")
    independent, modes = search_audit._direction(gradient.tolist(), case["order"])
    _need(independent is not None, "nonzero original descent")
    direction_check = _comparison(direction, independent, rtol=5e-12, atol=1e-12)
    _need(
        all(direction[i] == 0 for i, mode in enumerate(modes) if mode > 2),
        "unchanged inactive direction",
    )
    alpha = _scalar(pair_context["alpha"])
    _same(alpha, trial["alpha"], "saved step")
    _need(
        type(trial["backtrack"]) is int and trial["backtrack"] == 0 and alpha == 0.001,
        "registered first rejected backtrack",
    )
    seed_x = _numeric(control["snapshot"]["seed_geometry"]["base_coefficients"]).ravel()
    expected = [
        control["x"][i] + alpha * direction[i] if mode <= 2 else seed_x[i]
        for i, mode in enumerate(modes)
    ]
    _bits(proposal["x"], expected, "original active update and inactive bits")
    _need(
        all(
            _numeric([control["x"][i]]).tobytes() == _numeric([seed_x[i]]).tobytes()
            for i, mode in enumerate(modes)
            if mode > 2
        ),
        "inactive predecessor bits",
    )
    slope = math.fsum(float(g) * float(d) for g, d in zip(gradient, direction, strict=True))
    saved_slope = _scalar(pair_context["saved_directional_derivative"])
    _same(saved_slope, trial["directional_derivative"], "saved slope")
    _same(pair_context["gradient_dot_direction_relative_tolerance"], 5e-15, "slope tolerance")
    slope_check = _comparison(saved_slope, slope, rtol=5e-15, atol=1e-12)
    _need(slope < 0 and saved_slope < 0, "strict original descent")
    before = _scalar(pair_context["predecessor_objective"])
    _same(before, pred["evaluation"]["value"], "original SEARCH predecessor scalar")
    _same(pair_context["armijo_constant"], 1e-4, "original Armijo constant")
    rhs = _scalar(pair_context["armijo_rhs"])
    _same(rhs, trial["armijo_rhs"], "exact saved Armijo RHS")
    _same(rhs, before + 1e-4 * alpha * saved_slope, "original Armijo expression")
    rhs_check = _comparison(rhs, before + 1e-4 * alpha * slope)
    actual_j = _scalar(proposal["metric_checks"]["J"]["actual"])
    own_j = _scalar(proposal["metrics"]["J"])
    armijo = dict(
        saved_rhs=rhs,
        reconstructed_rhs=before + 1e-4 * alpha * slope,
        predecessor_objective=before,
        proposal_objective=actual_j,
        independent_proposal_objective=own_j,
        direction_check=direction_check,
        slope_check=slope_check,
        rhs_check=rhs_check,
        counterfactual_armijo_pass=bool(actual_j <= rhs),
        independent_armijo_pass=bool(own_j <= rhs),
        current_pass=bool(abs(_scalar(proposal["metric_checks"]["current"]["actual"])) <= 500000),
        historical_step_accepted=False,
    )
    return _json(
        dict(
            schema_version=1,
            kind="fixed-field-probe-paired-diagnostic",
            case=copy.deepcopy(case),
            control_state_sha256=control["state_sha256"],
            proposal_state_sha256=proposal["state_sha256"],
            normal_rms=_gain(
                control_state,
                proposal_state,
                "normal_rms",
                [0, 1, 2, 3],
                [(0, 1), (1, 2), (2, 3)],
                [2, 3],
            ),
            vector_rms=_gain(
                control_state, proposal_state, "vector_rms", [0, 4, 5], [(0, 4), (4, 5)], [5]
            ),
            armijo=armijo,
            tradeoffs=[
                dict(
                    level=i,
                    normal_max_delta=left["metrics"]["normal_max"] - right["metrics"]["normal_max"],
                    current_delta=right["metrics"]["current"] - left["metrics"]["current"],
                )
                for i, (left, right) in enumerate(
                    zip(control_state["models"], proposal_state["models"], strict=True)
                )
            ],
            **SCOPE,
        )
    )
