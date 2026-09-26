"""Structural boundaries for a protected cell, not physical/source admission.

Only the separately qualified source binder can authenticate historical artifacts.
These checks bind supplied identities and complete numerical schemas. They neither
reconstruct fields nor establish that a geometry report is physically correct.
"""

import copy
import hashlib
import math
from pathlib import Path

import numpy as np

from fusion_baselines import clear_coil_field_audit as field_schema
from fusion_baselines import clear_coil_geometry_audit as geometry_schema
from fusion_baselines.protected_coil_search import _state, weights
from fusion_baselines.protected_search_journal import _encode

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
INITIALIZATION = dict(seed_A_calls=1, seed_A_points=256)
METRICS = frozenset(
    (
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
    )
)
CONTEXT_KEYS = frozenset(
    (
        "case",
        "seed",
        "seed_reference",
        "geometry_report",
        "geometry_audit_reference",
        "geometry_report_index",
        "target_sources",
        "B2_scale",
        "historical_seed",
        "historical_seed_reference",
    )
)
SNAPSHOT_KEYS = frozenset(
    (
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
    )
)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, label):
    _need(_encode(actual) == _encode(expected), "exact typed identity: " + label)


def _real(value, shape, label):
    def leaves(item):
        if type(item) in (list, tuple):
            for entry in item:
                leaves(entry)
        else:
            _need(type(item) in (int, float), "plain real values: " + label)

    if not isinstance(value, np.ndarray):
        leaves(value)
    array = np.asarray(value)
    _need(
        array.shape == shape and array.dtype.kind in "iuf" and np.isfinite(array).all(),
        "complete finite real shape: " + label,
    )
    return array


def _scalar(value, label):
    return float(_real(value, (), label))


def _reference(value):
    _need(
        type(value) is dict and set(value) in ({"path", "sha256"}, {"path", "sha256", "bytes"}),
        "explicit historical reference required",
    )
    _need(
        type(value["path"]) is str and Path(value["path"]).is_absolute(),
        "absolute historical reference path required",
    )
    digest = value["sha256"]
    _need(
        type(digest) is str and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
        "historical SHA256 required",
    )
    if "bytes" in value:
        _need(
            type(value["bytes"]) is int and value["bytes"] > 0,
            "positive integer historical bytes required",
        )


def array_shapes(nbase):
    """All sixteen raw arrays, including diagnostic A/A/B calls."""
    _need(type(nbase) is int and nbase in (6, 8), "registered base coil count")
    return dict(
        boundary_points=(4096, 3),
        boundary_normals=(4096, 3),
        boundary_B=(4096, 3),
        boundary_A=(4096, 3),
        boundary_weights=(4096,),
        inner_points=(3072, 3),
        inner_target=(3072, 3),
        inner_B=(3072, 3),
        inner_A=(3072, 3),
        loop_points=(256, 3),
        loop_tangents=(256, 3),
        loop_A=(256, 3),
        loop_B=(256, 3),
        coil_positions=(4 * nbase, 256, 3),
        coil_tangents=(4 * nbase, 256, 3),
        coil_currents=(4 * nbase,),
    )


def _coordinates(context, x):
    seed = context["seed"]
    nbase, order = seed["nbase"], seed["order"]
    expected = (
        _real(seed["base_coefficients"], (nbase, 3, 2 * order + 1), "seed").astype(float).ravel()
    )
    actual = _real(x, expected.shape, "coordinates").astype(float)
    inactive = weights(nbase, order) == 0
    _need(
        actual[inactive].tobytes() == expected[inactive].tobytes(),
        "inactive original-seed coefficient bits required",
    )
    return actual


def coordinate_identity(context, x):
    """Stable SHA over schema, canonical names and float64 coordinates only."""
    names = geometry_schema.parameter_names(context["seed"]["nbase"], context["seed"]["order"])
    _same(context["seed"]["names"], names, "canonical names")
    actual = _coordinates(context, x)
    return hashlib.sha256(
        _encode(dict(schema_version=1, names=names, x=actual.tolist()))
    ).hexdigest()


def context_metadata(context):
    """Persist supplied bindings; the historical array bytes retain their old loader."""
    metadata = {k: copy.deepcopy(v) for k, v in context.items() if k != "historical_seed"}
    _encode(metadata)
    return metadata


def validate_context(context):
    _need(type(context) is dict and set(context) == CONTEXT_KEYS, "exact cell context schema")
    context_metadata(context)
    case, seed, report = (context[k] for k in ("case", "seed", "geometry_report"))
    _need(
        any(_encode(case) == _encode(row) for row in field_schema.cases()),
        "registered exact eight-cell identity",
    )
    geometry_schema.validate_snapshot(seed)
    expected_case = next(c for c in geometry_schema.cases() if c["label"] == case["seed_label"])
    _same(seed["case"], expected_case, "original shaped seed case")
    for key in ("nbase", "order"):
        _same(seed[key], case[key], key)
    _need(
        type(report) is dict
        and set(report)
        == {
            "case",
            "coils",
            "distances",
            "geometry_pass",
            "available_geometry",
            "sum_base_lengths",
            "analytic_coil_lower",
        },
        "complete supplied geometry report required",
    )
    _same(report["case"], seed["case"], "geometry report case")
    _need(
        report["geometry_pass"] is True
        and report["available_geometry"] is True
        and type(report["coils"]) is list
        and len(report["coils"]) == seed["nbase"]
        and type(report["distances"]) is list
        and len(report["distances"]) == 6,
        "positive complete supplied geometry report; external admission still required",
    )
    _same(
        context["geometry_report_index"],
        3 if seed["nbase"] == 6 else 9,
        "selected geometry report index",
    )
    for key in ("seed_reference", "geometry_audit_reference", "historical_seed_reference"):
        _reference(context[key])
    for sources in seed["sources"].values():
        _need(type(sources) is dict and set(sources) == {"input", "wout"}, "target source pair")
        for reference in sources.values():
            _reference(reference)
    _same(context["target_sources"], seed["sources"][case["target"]], "target source selection")
    _need(_scalar(context["B2_scale"], "fixed B2") > 0, "positive fixed B2 required")
    x = np.asarray(seed["base_coefficients"], dtype=float).ravel()
    validate_bundle(context["historical_seed"], x, context)
    snapshot = context["historical_seed"]["snapshot"]
    _same(snapshot["seed_unit_flux"], snapshot["unit_flux"], "original seed unit flux")
    _need(
        abs(context["historical_seed"]["state"]["metrics"]["current"]) <= 500000.0,
        "historical seed must satisfy current limit",
    )
    return True


def validate_bundle(bundle, x, context):
    """Complete schema/identity consistency, never independent physical verification."""
    _need(
        type(bundle) is dict and set(bundle) == {"state", "snapshot", "arrays"},
        "exact complete numerical bundle required",
    )
    requested = _coordinates(context, x)
    state, snapshot, arrays = (bundle[k] for k in ("state", "snapshot", "arrays"))
    _encode(state)
    _real(state["x"], requested.shape, "state coordinates")
    _real(state["gradient"], requested.shape, "full canonical gradient")
    _scalar(state["value"], "objective")
    _state(state, requested)
    _need(type(snapshot) is dict and set(snapshot) == SNAPSHOT_KEYS, "complete snapshot schema")
    _encode(snapshot)
    field_schema.validate_snapshot(snapshot)
    case, seed = context["case"], context["seed"]
    expected = dict(
        schema_version=1,
        nfp=2,
        nbase=case["nbase"],
        order=case["order"],
        method=case["method"],
        names=seed["names"],
        seed_geometry=seed,
        sources=context["target_sources"],
        construction=CONSTRUCTION,
        initialization_work=INITIALIZATION,
        B2_scale=context["B2_scale"],
    )
    for key, value in expected.items():
        _same(snapshot[key], value, "snapshot " + key)
    anchor = context["historical_seed"]["snapshot"]
    for key in ("target_flux", "seed_unit_flux"):
        _scalar(snapshot[key], key)
        _same(snapshot[key], anchor[key], "original " + key)
    _need(
        abs(snapshot["seed_unit_flux"]) > 1e-12
        and np.sign(snapshot["unit_flux"]) == np.sign(snapshot["seed_unit_flux"]),
        "original unit-flux orientation required",
    )
    shape = (case["nbase"], 3, 2 * case["order"] + 1)
    coefficients = _real(snapshot["base_coefficients"], shape, "snapshot coefficients")
    _need(
        coefficients.astype(float).ravel().tobytes() == requested.tobytes(),
        "snapshot/requested coordinate bits differ",
    )
    for actual, original in zip(snapshot["physical"], seed["physical"], strict=True):
        _same(
            {k: v for k, v in actual.items() if k != "current"}, original, "physical copy mapping"
        )
    metrics = state["metrics"]
    _need(type(metrics) is dict and set(metrics) == METRICS, "complete physical metrics schema")
    for key in METRICS - {"frozen_scale", "lengths", "kappa_max"}:
        _scalar(metrics[key], "metric " + key)
    for key in ("lengths", "kappa_max"):
        _real(metrics[key], (case["nbase"],), key)
    _same(metrics["frozen_scale"], False, "unfrozen current normalization")
    _same(metrics["J"], state["value"], "objective metric")
    for key in ("scale", "B2_scale", "unit_flux", "target_flux"):
        _same(metrics[key], snapshot[key], "metric " + key)
    _same(metrics["current"], 1e5 * snapshot["scale"], "signed current metric")
    _same(metrics["flux"], snapshot["scale"] * snapshot["unit_flux"], "flux metric")
    _need(
        metrics["JN"] >= 0 and metrics["JV"] >= 0 and metrics["geometry_penalty"] >= 0,
        "nonnegative objective components required",
    )
    _same(
        metrics["J"],
        metrics["JN"]
        + (0.05 * metrics["JV"] if case["method"] == "V" else 0)
        + metrics["geometry_penalty"],
        "objective composition",
    )
    _same(metrics["vector_rms"], math.sqrt(2 * metrics["JV"]), "vector RMS composition")
    shapes = array_shapes(case["nbase"])
    _need(type(arrays) is dict and set(arrays) == set(shapes), "exact sixteen raw arrays required")
    for key, shape in shapes.items():
        _real(arrays[key], shape, key)
    for key in (
        "boundary_points",
        "boundary_normals",
        "boundary_weights",
        "inner_points",
        "inner_target",
        "loop_points",
        "loop_tangents",
    ):
        actual, original = (
            np.asarray(arrays[key]),
            np.asarray(context["historical_seed"]["arrays"][key]),
        )
        _need(
            actual.dtype == original.dtype
            and actual.shape == original.shape
            and actual.tobytes() == original.tobytes(),
            "fixed input array identity: " + key,
        )
    currents = np.asarray([row["current"] for row in snapshot["physical"]], dtype=float)
    _need(
        np.asarray(arrays["coil_currents"], dtype=float).tobytes() == currents.tobytes(),
        "signed physical array currents differ from snapshot",
    )
    return True


def model_metadata(model, context):
    """Serialize the initialized original-seed identity, not the native object."""
    validate_model(model, context)
    return dict(
        seed_x=np.asarray(model.seed_x, dtype=float).tolist(),
        names=model.names.copy(),
        seed_geometry=copy.deepcopy(model._seed_geometry),
        method=model.method,
        B2_scale=float(model.B2_scale),
        target_flux=float(model.target_flux),
        seed_unit_flux=float(model.seed_unit_flux),
        initialization_work=copy.deepcopy(model.initialization_work),
        construction=CONSTRUCTION.copy(),
        sources=copy.deepcopy(model.target["sources"]),
    )


def validate_model(model, context):
    seed, case = context["seed"], context["case"]
    anchor = context["historical_seed"]["snapshot"]
    x = _coordinates(context, model.seed_x)
    _need(
        x.tobytes() == np.asarray(seed["base_coefficients"], dtype=float).ravel().tobytes(),
        "initialize model at original seed, not selected candidate",
    )
    _need(
        _coordinates(context, model.x).tobytes() == x.tobytes(),
        "actual initialized model coordinates must equal original seed",
    )
    _need(model._cache is None, "empty initialized model cache required")
    expected = dict(
        names=seed["names"],
        _seed_geometry=seed,
        method=case["method"],
        nbase=case["nbase"],
        order=case["order"],
        nfp=2,
        initialization_work=INITIALIZATION,
        **{k: CONSTRUCTION[k] for k in ("ncoil", "nphi", "ntheta", "ninner", "offset")},
    )
    for key, value in expected.items():
        _same(getattr(model, key), value, "initialized model " + key)
    for key in ("B2_scale", "target_flux", "seed_unit_flux"):
        value = getattr(model, key)
        _need(type(value) in (int, float, np.float64), "real initialized model " + key)
        _same(float(value), anchor[key], "initialized model " + key)
    _same(model.target["sources"], context["target_sources"], "initialized model sources")
    return True
