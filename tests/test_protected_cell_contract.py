"""Synthetic complete schemas; zero arrays are deliberately not physical fields."""

import copy
import hashlib
from types import SimpleNamespace

import numpy as np
import pytest
from test_protected_coil_fit_inputs import seed_fixture

from fusion_baselines import protected_cell_contract as contract
from fusion_baselines.protected_coil_search import weights
from fusion_baselines.protected_search_journal import _encode


def context_fixture(nbase=6, method="N", target="reference"):
    order = 5 if nbase == 6 else 7
    case = dict(
        label=f"{target}-n{nbase}-{method}",
        target=target,
        nbase=nbase,
        order=order,
        seed_label=f"n{nbase}-shape-d100mm",
        method=method,
    )
    _, snapshot, case, seed, source = seed_fixture(case)

    def ref(path):
        return dict(path="/synthetic/" + path, sha256="a" * 64)

    context = dict(
        case=case,
        seed=seed,
        seed_reference=ref("geometry-seed.json"),
        geometry_report=dict(
            case=copy.deepcopy(seed["case"]),
            coils=[{} for _ in range(nbase)],
            distances=[{} for _ in range(6)],
            geometry_pass=True,
            available_geometry=True,
            sum_base_lengths=12.0,
            analytic_coil_lower=0.12,
        ),
        geometry_audit_reference=ref("geometry-audit.json"),
        geometry_report_index=3 if nbase == 6 else 9,
        target_sources=source["targets"][target],
        B2_scale=2.0,
        historical_seed=dict(snapshot=snapshot),
        historical_seed_reference=ref("seed-operation.json"),
    )
    context["historical_seed"] = bundle_fixture(context)
    return context


def bundle_fixture(context, x=None, value=0.1, gradient=None, current=100000.0):
    seed = context["seed"]
    x = np.array(seed["base_coefficients"] if x is None else x, dtype=float).ravel()
    gradient = np.zeros_like(x) if gradient is None else np.asarray(gradient, dtype=float)
    snapshot = copy.deepcopy(context["historical_seed"]["snapshot"])
    snapshot["base_coefficients"] = x.reshape(seed["nbase"], 3, 2 * seed["order"] + 1).tolist()
    snapshot["scale"] = current / 1e5
    snapshot["unit_flux"] = snapshot["target_flux"] / snapshot["scale"]
    for row in snapshot["physical"]:
        row["current"] = current * (-1 if row["flip"] else 1)
    metrics = dict(
        J=value,
        JN=value,
        JV=0.0,
        geometry_penalty=0.0,
        frozen_scale=False,
        lengths=[2.0] * seed["nbase"],
        kappa_max=[3.0] * seed["nbase"],
        normal_rms=0.27,
        normal_max=0.4,
        vector_rms=0.0,
        boundary_B_rms=1.0,
        coil_distance=0.12,
        surface_distance=0.1,
        current=current,
        flux=snapshot["scale"] * snapshot["unit_flux"],
        **{k: snapshot[k] for k in ("scale", "B2_scale", "unit_flux", "target_flux")},
    )
    arrays = {k: np.zeros(shape) for k, shape in contract.array_shapes(seed["nbase"]).items()}
    arrays["coil_currents"] = np.array([r["current"] for r in snapshot["physical"]])
    return dict(
        state=dict(x=x.tolist(), value=value, gradient=gradient.tolist(), metrics=metrics),
        snapshot=snapshot,
        arrays=arrays,
    )


def model_fixture(context):
    seed, snapshot = context["seed"], context["historical_seed"]["snapshot"]
    return SimpleNamespace(
        seed_x=np.asarray(seed["base_coefficients"]).ravel().copy(),
        x=np.asarray(seed["base_coefficients"]).ravel().copy(),
        _cache=None,
        names=seed["names"].copy(),
        _seed_geometry=copy.deepcopy(seed),
        method=context["case"]["method"],
        nbase=seed["nbase"],
        order=seed["order"],
        nfp=2,
        target=dict(sources=context["target_sources"]),
        initialization_work=contract.INITIALIZATION.copy(),
        **{k: snapshot[k] for k in ("B2_scale", "target_flux", "seed_unit_flux")},
        **{k: contract.CONSTRUCTION[k] for k in ("ncoil", "nphi", "ntheta", "ninner", "offset")},
    )


@pytest.mark.parametrize(
    "nbase,method,target",
    [(n, m, t) for n in (6, 8) for m in ("N", "V") for t in ("reference", "selected")],
)
def test_all_eight_synthetic_cases(nbase, method, target):
    context = context_fixture(nbase, method, target)
    assert contract.validate_context(context) is True
    assert contract.validate_model(model_fixture(context), context) is True
    metadata = contract.model_metadata(model_fixture(context), context)
    assert metadata["seed_geometry"] == context["seed"]
    assert "historical_seed" not in contract.context_metadata(context)
    x = np.asarray(context["historical_seed"]["state"]["x"])
    expected = hashlib.sha256(
        _encode(dict(schema_version=1, names=context["seed"]["names"], x=x.tolist()))
    ).hexdigest()
    assert contract.coordinate_identity(context, x) == expected


@pytest.mark.parametrize("key", list(contract.CONTEXT_KEYS))
def test_missing_context_fields(key):
    context = context_fixture()
    del context[key]
    with pytest.raises(ValueError):
        contract.validate_context(context)


@pytest.mark.parametrize("key", list(contract.SNAPSHOT_KEYS))
def test_missing_snapshot_fields(key):
    context = context_fixture()
    del context["historical_seed"]["snapshot"][key]
    with pytest.raises(ValueError):
        contract.validate_context(context)


@pytest.mark.parametrize("key", list(contract.METRICS))
def test_missing_metrics(key):
    context = context_fixture()
    del context["historical_seed"]["state"]["metrics"][key]
    with pytest.raises(ValueError):
        contract.validate_context(context)


@pytest.mark.parametrize("key", list(contract.array_shapes(6)))
@pytest.mark.parametrize("mutation", ["absent", "shape", "nonfinite", "complex", "boolean"])
def test_every_raw_array_boundary(key, mutation):
    context = context_fixture()
    arrays = context["historical_seed"]["arrays"]
    if mutation == "absent":
        del arrays[key]
    elif mutation == "shape":
        arrays[key] = arrays[key][:-1]
    elif mutation == "nonfinite":
        arrays[key].flat[0] = np.nan
    elif mutation == "complex":
        arrays[key] = arrays[key].astype(complex)
    else:
        arrays[key] = arrays[key].astype(bool)
    with pytest.raises(ValueError):
        contract.validate_context(context)


@pytest.mark.parametrize(
    "key",
    [
        "schema_version",
        "nfp",
        "nbase",
        "order",
        "method",
        "names",
        "sources",
        "seed_geometry",
        "construction",
        "initialization_work",
        "B2_scale",
    ],
)
def test_snapshot_identity_mutations(key):
    context = context_fixture()
    context["historical_seed"]["snapshot"][key] = None
    with pytest.raises((ValueError, TypeError)):
        contract.validate_context(context)


@pytest.mark.parametrize("key", ["x", "gradient", "value"])
def test_state_rejects_boolean_numerics(key):
    context = context_fixture()
    state = context["historical_seed"]["state"]
    if key == "value":
        state[key] = True
    else:
        state[key][0] = True
    with pytest.raises(ValueError):
        contract.validate_context(context)


def test_changed_active_coordinate_is_valid_but_inactive_and_negative_zero_are_not():
    context = context_fixture()
    x = np.array(context["historical_seed"]["state"]["x"])
    x[0] += 1e-5
    candidate = bundle_fixture(context, x)
    assert contract.validate_bundle(candidate, x, context)
    assert contract.coordinate_identity(context, x) != contract.coordinate_identity(
        context, context["historical_seed"]["state"]["x"]
    )
    inactive = np.flatnonzero(weights(6, 5) == 0)[0]
    for value in (1e-30, -0.0):
        x[inactive] = value
        with pytest.raises(ValueError, match="inactive"):
            contract.coordinate_identity(context, x)


def test_finite_overcurrent_trial_retained_for_controller_rejection():
    context = context_fixture()
    x = context["historical_seed"]["state"]["x"]
    assert contract.validate_bundle(bundle_fixture(context, x, current=600000.0), x, context)


@pytest.mark.parametrize(
    "key",
    [
        "current",
        "flux",
        "J",
        "scale",
        "target_flux",
        "B2_scale",
        "unit_flux",
        "vector_rms",
        "frozen_scale",
    ],
)
def test_inconsistent_metrics_rejected(key):
    context = context_fixture()
    metrics = context["historical_seed"]["state"]["metrics"]
    metrics[key] = True if key == "frozen_scale" else metrics[key] + 1.0
    with pytest.raises(ValueError):
        contract.validate_context(context)


def test_current_array_order_and_physical_mapping_are_bound():
    context = context_fixture()
    context["historical_seed"]["arrays"]["coil_currents"][0] *= -1
    with pytest.raises(ValueError, match="currents"):
        contract.validate_context(context)
    context = context_fixture()
    context["historical_seed"]["snapshot"]["physical"][0]["extra"] = False
    with pytest.raises(ValueError, match="mapping"):
        contract.validate_context(context)


@pytest.mark.parametrize(
    "key,value",
    [
        ("nfp", True),
        ("method", "V"),
        ("ncoil", 512),
        ("names", []),
        ("B2_scale", True),
        ("seed_unit_flux", 0.5),
    ],
)
def test_model_identity_mutations(key, value):
    context = context_fixture()
    model = model_fixture(context)
    setattr(model, key, value)
    with pytest.raises(ValueError):
        contract.validate_model(model, context)


def test_replay_model_must_initialize_at_original_seed():
    context = context_fixture()
    model = model_fixture(context)
    model.seed_x[0] += 1e-5
    with pytest.raises(ValueError, match="original seed"):
        contract.validate_model(model, context)


@pytest.mark.parametrize(
    "key,value", [("geometry_report_index", True), ("geometry_report_index", 9), ("B2_scale", -1.0)]
)
def test_context_scalar_identity(key, value):
    context = context_fixture()
    context[key] = value
    with pytest.raises(ValueError):
        contract.validate_context(context)


def test_source_and_name_changes_rejected():
    context = context_fixture()
    context["target_sources"]["input"]["sha256"] = "b" * 64
    with pytest.raises(ValueError):
        contract.validate_context(context)
    context = context_fixture()
    context["seed"]["names"].reverse()
    with pytest.raises(ValueError):
        contract.validate_context(context)


@pytest.mark.parametrize(
    "key",
    [
        "boundary_points",
        "boundary_normals",
        "boundary_weights",
        "inner_points",
        "inner_target",
        "loop_points",
        "loop_tangents",
    ],
)
def test_fixed_grid_and_target_array_substitutions_rejected(key):
    context = context_fixture()
    bundle = bundle_fixture(context)
    bundle["arrays"][key].flat[0] += 1.0
    with pytest.raises(ValueError, match="fixed input"):
        contract.validate_bundle(bundle, bundle["state"]["x"], context)


def test_actual_initialized_dofs_and_cache_checked_not_only_claimed_seed():
    context = context_fixture()
    model = model_fixture(context)
    model.x[0] += 1e-5
    with pytest.raises(ValueError, match="actual initialized"):
        contract.validate_model(model, context)
    model = model_fixture(context)
    model._cache = {}
    with pytest.raises(ValueError, match="empty initialized"):
        contract.validate_model(model, context)
