"""Synthetic saved-data wiring; no native model, field, equilibrium or search."""

import copy
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from test_protected_fine_native import inputs, raw_arrays

from fusion_baselines.protected_run_snapshots import SnapshotStore
from fusion_baselines.protected_search_journal import _encode

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_protected_fine_fields as fields  # noqa: E402

REAL_FIELD_ROW = fields.legacy.field_row
REAL_FLUX_GRID = fields.legacy.flux_grid
REAL_INITIALIZER = fields._initializer_flux


def fixture(tmp_path, monkeypatch, nbase=6, method="N", target="reference", changed=True):
    context, archive = inputs(nbase, method, target, changed)
    store = SnapshotStore(tmp_path / "raw")
    context["coarse"]["selected_snapshot"] = store.json("snapshot", context["selected"]["snapshot"])
    original, snapshot = context["original_context"], context["selected"]["snapshot"]
    seed, calls = original["seed"], dict(initializer=[], field=[], flux=[], guard=0, arrays=[])
    target_context = dict(
        input=dict(synthetic=True),
        B2_scale=snapshot["B2_scale"],
        target_flux=snapshot["target_flux"],
        targets={n: dict(B2_scale=snapshot["B2_scale"]) for n in (32, 64)},
    )
    initializations, operations = [], []
    scopes = (
        "complete_execution",
        "arithmetic_consistency",
        "fine_numerical_qualification",
        "absolute_field_geometry_pass",
        "physical_admission",
        "step4_pass",
        "sota_advance",
        "ms1_reached",
        "resolved_fine_grid_improvement",
        "pareto_dominance",
        "realized_field_transfer",
    )
    for spec in fields.plan.model_plan(context["case"]):
        metadata = dict(
            spec=copy.deepcopy(spec),
            case=copy.deepcopy(context["case"]),
            original_seed=copy.deepcopy(original["seed_reference"]),
            geometry_audit=copy.deepcopy(original["geometry_audit_reference"]),
            target_sources=copy.deepcopy(original["target_sources"]),
            coarse=copy.deepcopy(context["coarse"]),
            names=seed["names"].copy(),
            seed_x=np.asarray(seed["base_coefficients"]).ravel().tolist(),
            selected_x=context["selected"]["state"]["x"].copy(),
            original_seed_unit_flux=0.125 if spec["grid"]["ncoil"] == 256 else 0.124,
            initializer_physical_currents=[-1e5 if r["flip"] else 1e5 for r in seed["physical"]],
            initialization_work=dict(seed_A_calls=1, seed_A_points=256),
            initialization_native_calls=[
                dict(
                    index=0,
                    field="loop",
                    quantity="A",
                    points=256,
                    status="completed",
                    native_started=True,
                    native_completed=True,
                    started_monotonic=2.0,
                    completed_monotonic=3.0,
                )
            ],
            **{k: snapshot[k] for k in ("scale", "B2_scale", "target_flux")},
            **{k: False for k in scopes},
        )
        initialized = dict(
            schema_version=1,
            kind="protected-fine-initialization",
            case=copy.deepcopy(context["case"]),
            spec=copy.deepcopy(spec),
            metadata=metadata,
        )
        initializations.append(initialized)
        init_ref = store.json("init-" + spec["id"], initialized)
        for operation in fields.plan.operation_plan(spec, context["selected"]["state"]["x"]):
            record = dict(
                snapshot=copy.deepcopy(context["coarse"]["selected_snapshot"]),
                **{k: snapshot[k] for k in ("scale", "B2_scale", "target_flux")},
            )
            if spec["kind"] == "diagnostic":
                record["metrics"] = dict(
                    normal_rms=1e-6,
                    normal_max=1e-5,
                    vector_rms=1e-4,
                    current=1e5 * snapshot["scale"],
                    lengths=[2.0] * nbase,
                    kappa_max=[3.0] * nbase,
                    coil_distance=0.1,
                    surface_distance=0.1,
                )
            else:
                record["flux"] = snapshot["target_flux"]
            raw_ref = store.arrays(
                operation["operation_id"], dict(marker=np.arange(3, dtype=np.int32))
            )
            operations.append(
                dict(
                    schema_version=1,
                    kind="protected-fine-operation",
                    status="completed",
                    case=copy.deepcopy(context["case"]),
                    spec=copy.deepcopy(spec),
                    operation={k: copy.deepcopy(v) for k, v in operation.items() if k != "x"},
                    arrays=raw_ref,
                    record=record,
                    initialization=init_ref,
                )
            )

    def initializer(original_seed, target, ncoil, guard):
        assert original_seed == seed and target is target_context
        calls["initializer"].append(ncoil)
        guard()
        return 0.125 if ncoil == 256 else 0.124

    def field(row, selected_snapshot, target, level, evidence, *, method, diagnostic):
        assert selected_snapshot == snapshot and target is target_context
        assert method == context["case"]["method"] and diagnostic is True
        raw = evidence.array(row["arrays"])
        assert raw["marker"].dtype == np.dtype(np.int32)
        calls["field"].append((level.copy(), method, diagnostic))
        return dict(
            metrics=dict(
                copy.deepcopy(row["metrics"]),
                direct_errors={
                    key: 1e-12
                    for key in (
                        "boundary_B",
                        "boundary_A",
                        "inner_B",
                        "inner_A",
                        "loop_B",
                        "loop_A",
                    )
                },
            )
        )

    def flux(row, form, selected_snapshot, data, ncoil, evidence):
        assert selected_snapshot == snapshot and data is target_context["input"]
        assert evidence.array(row["arrays"])["marker"].dtype == np.dtype(np.int32)
        calls["flux"].append((ncoil, form, row.get("nrho"), row["ntheta"]))
        return dict(flux=row["flux"], direct_errors=dict(B=1e-12, A=1e-12))

    def target(binding, case, evidence):
        assert (
            binding
            == archive["archived_source"]["physics_sources"]["native_sources"]["cell_sources"]
        )
        assert case == context["case"] and type(evidence) is fields.legacy.Evidence
        return target_context

    def guard():
        calls["guard"] += 1

    monkeypatch.setattr(fields.legacy, "target", target)
    monkeypatch.setattr(fields, "_initializer_flux", initializer)
    monkeypatch.setattr(fields.legacy, "field_row", field)
    monkeypatch.setattr(fields.legacy, "flux_grid", flux)
    monkeypatch.setattr(
        fields.legacy.Evidence, "array", lambda *a: pytest.fail("new arrays via old reader")
    )
    h = SimpleNamespace(
        context=context,
        archive=archive,
        store=store,
        initializations=initializations,
        operations=operations,
        calls=calls,
        target=target_context,
        guard=guard,
    )
    h.run = lambda: fields.audit_fields(context, archive, initializations, operations, h.guard)
    return h


@pytest.mark.parametrize(
    "nbase,method,target,changed",
    [
        (n, m, t, c)
        for n in (6, 8)
        for m in ("N", "V")
        for t in ("reference", "selected")
        for c in (False, True)
    ],
)
def test_complete_ordered_work_scopes_and_fallback(
    tmp_path, monkeypatch, nbase, method, target, changed
):
    h = fixture(tmp_path, monkeypatch, nbase, method, target, changed)
    result = h.run()
    assert result["status"] == "completed"
    assert result["arithmetic_consistency"] is result["fine_numerical_qualification"] is True
    assert result["field_limits_pass"] is True
    assert h.calls["initializer"] == [256, 256, 512, 512, 256, 512, 256, 512]
    assert [
        tuple(row[0][k] for k in ("nphi", "ntheta", "ncoil", "ninner", "offset"))
        for row in h.calls["field"]
    ] == [
        (64, 64, 256, 32, 0),
        (128, 128, 256, 32, 0),
        (128, 128, 512, 32, 0),
        (128, 128, 512, 32, 0.5),
        (64, 64, 256, 64, 0),
        (64, 64, 512, 64, 0),
    ]
    assert [row[1:] for row in h.calls["field"]] == [(method, True)] * 6
    assert h.calls["flux"] == [
        (c, form, r, t)
        for c in (256, 512)
        for form, r in (("line", None), ("area", 16), ("area", 32))
        for t in (256, 512, 1024)
    ]
    assert result["independent_work"] == dict(
        initializer_scalar_checks=8,
        diagnostic_reconstructions=6,
        flux_grid_reconstructions=18,
        sampled_BA_statistics=72,
        sampled_vectors=4608,
        sampled_scalar_components=13824,
        refinement_checks=5,
        flux_checks=63,
        native_requests=0,
        native_model_constructions=0,
        producer_certificates=0,
        equilibrium_solves=0,
        search_calls=0,
    )
    assert len(result["refinements"]["checks"]) == 5
    assert [len(b["checks"]) for b in result["flux_blocks"]] == [27, 27]
    assert len(result["flux_coil_comparison"]["checks"]) == 9
    assert sum(len(r["direct_errors"]) for r in result["diagnostics"]) == 36
    assert sum(len(g["direct_errors"]) for b in result["flux_blocks"] for g in b["grids"]) == 36
    for key in (
        "source_admission_verified",
        "external_execution_acknowledgement_verified",
        "complete_execution",
        "complete_graph_verified",
        "continuous_geometry_verified",
        "sampled_geometry_verified",
        "absolute_field_geometry_pass",
        "physical_admission",
        "fine_grid_acceptance",
        "field_values_verified",
        "gradients_verified",
        "resolved_fine_grid_improvement",
        "pareto_dominance",
        "realized_field_transfer",
        "step4_pass",
        "sota_advance",
        "ms1_reached",
    ):
        assert result[key] is False
    assert "sampled geometry" in result["field_limits_scope"]
    _encode(result)


@pytest.mark.parametrize(
    "group,size",
    [("initializations", 7), ("initializations", 9), ("operations", 23), ("operations", 25)],
)
def test_exact_counts(tmp_path, monkeypatch, group, size):
    h = fixture(tmp_path, monkeypatch)
    rows = getattr(h, group)
    rows[:] = (rows + rows)[:size]
    with pytest.raises(ValueError):
        h.run()


@pytest.mark.parametrize(
    "group,first,second",
    [
        ("initializations", 0, 1),
        ("initializations", 6, 7),
        ("operations", 0, 1),
        ("operations", 6, 7),
        ("operations", 9, 12),
        ("operations", 6, 15),
    ],
)
def test_order_is_fixed(tmp_path, monkeypatch, group, first, second):
    h = fixture(tmp_path, monkeypatch)
    rows = getattr(h, group)
    rows[first], rows[second] = rows[second], rows[first]
    with pytest.raises(ValueError):
        h.run()


@pytest.mark.parametrize(
    "key",
    [
        "original_seed",
        "geometry_audit",
        "target_sources",
        "coarse",
        "names",
        "seed_x",
        "selected_x",
        "initializer_physical_currents",
        "initialization_work",
        "spec",
        "case",
        "scale",
        "B2_scale",
        "target_flux",
        "complete_execution",
        "arithmetic_consistency",
        "fine_numerical_qualification",
        "absolute_field_geometry_pass",
        "physical_admission",
        "step4_pass",
        "sota_advance",
        "ms1_reached",
        "resolved_fine_grid_improvement",
        "pareto_dominance",
        "realized_field_transfer",
    ],
)
def test_each_initializer_binding(tmp_path, monkeypatch, key):
    h = fixture(tmp_path, monkeypatch)
    h.initializations[0]["metadata"][key] = True
    with pytest.raises((ValueError, TypeError)):
        h.run()


@pytest.mark.parametrize(
    "value",
    [
        0.0,
        1e-12,
        -1e-12,
        True,
        np.float64(0.125),
        [0.125],
        float("nan"),
        float("inf"),
        0.125 * (1 + 1e-8),
    ],
)
def test_original_initializer_invalid_or_inconsistent(tmp_path, monkeypatch, value):
    h = fixture(tmp_path, monkeypatch)
    h.initializations[0]["metadata"]["original_seed_unit_flux"] = value
    with pytest.raises((ValueError, TypeError)):
        h.run()


@pytest.mark.parametrize(
    "key,value",
    [
        ("index", False),
        ("field", "boundary"),
        ("quantity", "B"),
        ("points", 512),
        ("status", "attempted"),
        ("native_started", 1),
        ("native_completed", False),
        ("started_monotonic", True),
        ("completed_monotonic", 1.0),
        ("started_monotonic", -1.0),
        ("completed_monotonic", float("nan")),
    ],
)
def test_initializer_event_exactness(tmp_path, monkeypatch, key, value):
    h = fixture(tmp_path, monkeypatch)
    h.initializations[0]["metadata"]["initialization_native_calls"][0][key] = value
    with pytest.raises(ValueError):
        h.run()


@pytest.mark.parametrize(
    "location,key",
    [
        ("initialization", "kind"),
        ("initialization", "schema_version"),
        ("metadata", "original_seed_unit_flux"),
        ("metadata", "initialization_native_calls"),
        ("operation", "arrays"),
        ("operation", "initialization"),
        ("operation", "spec"),
        ("record", "snapshot"),
        ("record", "scale"),
        ("record", "metrics"),
    ],
)
@pytest.mark.parametrize("extra", [False, True])
def test_missing_extra_schema(tmp_path, monkeypatch, location, key, extra):
    h = fixture(tmp_path, monkeypatch)
    container = dict(
        initialization=h.initializations[0],
        metadata=h.initializations[0]["metadata"],
        operation=h.operations[0],
        record=h.operations[0]["record"],
    )[location]
    if extra:
        container["unregistered"] = True
    else:
        del container[key]
    with pytest.raises((ValueError, KeyError)):
        h.run()


@pytest.mark.parametrize("key", ["schema_version", "kind", "status", "case", "spec", "operation"])
def test_operation_identity(tmp_path, monkeypatch, key):
    h = fixture(tmp_path, monkeypatch)
    h.operations[0][key] = True
    with pytest.raises(ValueError):
        h.run()


@pytest.mark.parametrize("key", ["snapshot", "scale", "B2_scale", "target_flux"])
def test_frozen_coarse_binding(tmp_path, monkeypatch, key):
    h = fixture(tmp_path, monkeypatch)
    h.operations[0]["record"][key] = True
    with pytest.raises(ValueError):
        h.run()


def test_operation_cannot_borrow_another_initializer(tmp_path, monkeypatch):
    h = fixture(tmp_path, monkeypatch)
    h.operations[0]["initialization"] = h.operations[1]["initialization"]
    with pytest.raises(ValueError, match="own initialized model"):
        h.run()


@pytest.mark.parametrize(
    "change",
    [
        "original_target",
        "B2",
        "target_flux",
        "inner32",
        "inner64",
        "snapshot",
        "selected_x",
        "case",
    ],
)
def test_context_and_independent_target_bindings(tmp_path, monkeypatch, change):
    h = fixture(tmp_path, monkeypatch)
    if change == "original_target":
        h.archive["archived_source"]["physics_sources"]["native_sources"]["cell_sources"][
            "targets"
        ] = {}
    elif change in ("B2", "target_flux"):
        h.target["B2_scale" if change == "B2" else change] += 1
    elif change.startswith("inner"):
        h.target["targets"][int(change[5:])]["B2_scale"] += 1
    elif change == "snapshot":
        h.context["coarse"]["selected_snapshot"] = h.store.json("other", dict(wrong=True))
    elif change == "selected_x":
        h.context["selected"]["state"]["x"][0] += 0.001
    else:
        h.context["case"]["method"] = "V"
    with pytest.raises((ValueError, AssertionError)):
        h.run()


@pytest.mark.parametrize("kind", ["refinement", "flux", "field", "current", "geometry"])
def test_threshold_failures_complete_all_work(tmp_path, monkeypatch, kind):
    h = fixture(tmp_path, monkeypatch)
    if kind == "refinement":
        h.operations[1]["record"]["metrics"]["normal_rms"] = 2e-6
    elif kind == "flux":
        h.operations[6]["record"]["flux"] *= 1.001
    elif kind == "field":
        for row in h.operations[:6]:
            row["record"]["metrics"]["normal_rms"] = 0.27
    elif kind == "current":
        h.operations[5]["record"]["metrics"]["current"] = 600000.0
    else:
        h.operations[5]["record"]["metrics"]["coil_distance"] = 0.059
    report = h.run()
    assert len(h.calls["field"]) == 6 and len(h.calls["flux"]) == 18
    assert report["arithmetic_consistency"] is True
    assert report["fine_numerical_qualification"] is (kind not in ("refinement", "flux"))
    assert report["field_limits_pass"] is (kind in ("refinement", "flux"))
    assert report["physical_admission"] is report["step4_pass"] is False


def test_canonical_new_array_identity_and_no_writes(tmp_path, monkeypatch):
    h = fixture(tmp_path, monkeypatch)
    real, observed = fields.read_arrays, []

    def read(reference):
        observed.append(copy.deepcopy(reference))
        return real(reference)

    monkeypatch.setattr(fields, "read_arrays", read)
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    h.run()
    after = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after
    assert observed == [row["arrays"] for row in h.operations]


def test_changed_array_bytes_stop_audit(tmp_path, monkeypatch):
    h = fixture(tmp_path, monkeypatch)
    h.operations[0]["arrays"]["sha256"] = "f" * 64
    with pytest.raises(ValueError, match="identity mismatch"):
        h.run()


@pytest.mark.parametrize("sign,relative", [(s, r) for s in (-1, 1) for r in (0.0, 4e-10, 6e-10)])
def test_initializer_signed_relative_tolerance_without_absolute_slack(
    tmp_path, monkeypatch, sign, relative
):
    h = fixture(tmp_path, monkeypatch)
    own = sign * 2e-12
    # Close to the nondegeneracy floor: an inappropriate 1e-12 absolute slack
    # would conceal the deliberately out-of-tolerance relative discrepancy.
    monkeypatch.setattr(fields, "_initializer_flux", lambda *a: own)
    for index, row in enumerate(h.initializations):
        row["metadata"]["original_seed_unit_flux"] = own * (1 + relative)
        reference = h.store.json("tolerance-init-" + str(index), row)
        for operation in h.operations:
            if operation["spec"]["id"] == row["spec"]["id"]:
                operation["initialization"] = reference
    if relative > 5e-10:
        with pytest.raises(ValueError, match="original-seed initializer A flux"):
            h.run()
    else:
        result = h.run()
        assert len(result["original_initializers"]) == 8
        assert all(r["independent"] == own for r in result["original_initializers"])


@pytest.mark.parametrize("phase", ["field", "flux"])
def test_incomplete_direct_comparison_reports_rejected(tmp_path, monkeypatch, phase):
    h = fixture(tmp_path, monkeypatch)
    name = "field_row" if phase == "field" else "flux_grid"
    original = getattr(fields.legacy, name)

    def missing(*args, **kwargs):
        result = original(*args, **kwargs)
        errors = result["metrics"]["direct_errors"] if phase == "field" else result["direct_errors"]
        del errors[next(iter(errors))]
        return result

    monkeypatch.setattr(fields.legacy, name, missing)
    with pytest.raises(ValueError, match="direct"):
        h.run()


def test_required_guard_is_not_optional(tmp_path, monkeypatch):
    h = fixture(tmp_path, monkeypatch)
    h.guard = None
    with pytest.raises(ValueError, match="guard"):
        h.run()


@pytest.mark.parametrize("stage", [1, 2, 3, 6, 15, 30, 75, "last"])
def test_guard_failure_never_returns_completed_report(tmp_path, monkeypatch, stage):
    h = fixture(tmp_path, monkeypatch)
    if stage == "last":
        h.run()
        stage = h.calls["guard"]
    count = 0

    def fail():
        nonlocal count
        count += 1
        if count == stage:
            raise TimeoutError("synthetic independent audit deadline")

    h.guard = fail
    with pytest.raises(TimeoutError):
        h.run()


def test_returned_report_has_no_mutable_input_aliases(tmp_path, monkeypatch):
    h = fixture(tmp_path, monkeypatch)
    report = h.run()
    frozen = _encode(report)
    h.context["case"]["label"] = "changed"
    h.context["coarse"]["selected_bundle"]["sha256"] = "f" * 64
    h.operations[0]["record"]["metrics"]["lengths"][0] = 999.0
    assert _encode(report) == frozen


@pytest.mark.parametrize("nbase,method,ncoil", [(6, "N", 256), (8, "V", 512)])
def test_initializer_uses_original_coefficients_signed_100k_and_full_loop(
    tmp_path, monkeypatch, nbase, method, ncoil
):
    h = fixture(tmp_path, monkeypatch, nbase, method)
    seed = h.context["original_context"]["seed"]
    seen = []
    nphysical = 4 * nbase

    def curves(coefficients, nodes):
        expected = np.stack(
            [
                np.asarray(row["matrix"]).T
                @ np.asarray(seed["base_coefficients"])[row["base_index"]]
                for row in seed["physical"]
            ]
        )
        np.testing.assert_array_equal(coefficients, expected)
        assert nodes == ncoil
        seen.append("original curves")
        return dict(
            positions=np.zeros((nphysical, nodes, 3)), tangents=np.ones((nphysical, nodes, 3))
        )

    def loop(data, nodes):
        assert data is h.target["input"] and nodes == 256
        seen.append("unshifted 256-node loop")
        return np.zeros((256, 3)), np.ones((256, 3))

    def direct(points, positions, tangents, currents):
        assert positions.shape == tangents.shape == (nphysical, ncoil, 3)
        assert points.shape == (256, 3)
        np.testing.assert_array_equal(
            currents, [-1e5 if r["flip"] else 1e5 for r in seed["physical"]]
        )
        assert abs(currents).max() != h.context["selected"]["snapshot"]["scale"] * 1e5
        seen.append("direct original A")
        return np.ones((256, 3)), np.full((256, 3), -0.125 / 3)

    monkeypatch.setattr(fields.legacy.frozen, "fourier_curves", curves)
    monkeypatch.setattr(fields.legacy.frozen, "loop", loop)
    monkeypatch.setattr(fields.legacy.frozen, "filament_field_and_potential", direct)
    assert REAL_INITIALIZER(seed, h.target, ncoil, h.guard) == -0.125
    assert seen == ["original curves", "unshifted 256-node loop", "direct original A"]


@pytest.mark.parametrize("bad", ["short", "nan", "zero"])
def test_degenerate_independent_initializer_rejected(tmp_path, monkeypatch, bad):
    h = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        fields.legacy.frozen, "fourier_curves", lambda *a: dict(positions=0, tangents=0)
    )
    monkeypatch.setattr(
        fields.legacy.frozen, "loop", lambda *a: (np.ones((256, 3)), np.ones((256, 3)))
    )
    potential = np.ones((255 if bad == "short" else 256, 3))
    if bad == "nan":
        potential[0, 0] = np.nan
    elif bad == "zero":
        potential[:] = 0
    monkeypatch.setattr(
        fields.legacy.frozen, "filament_field_and_potential", lambda *a: (None, potential)
    )
    with pytest.raises(ValueError):
        REAL_INITIALIZER(h.context["original_context"]["seed"], h.target, 256, h.guard)


@pytest.mark.parametrize("corrupt", [False, True])
def test_actual_frozen_field_bridge_rejects_metric_mismatch(tmp_path, monkeypatch, corrupt):
    h = fixture(tmp_path, monkeypatch, method="V")
    wrapper = h.operations[0]
    spec, op, snapshot = wrapper["spec"], wrapper["operation"], h.context["selected"]["snapshot"]
    raw = raw_arrays(spec, op, snapshot)
    wrapper["arrays"] = h.store.arrays("full-field", raw)
    h.target["targets"][32].update({k: raw[k] for k in ("inner_points", "inner_target")})
    metrics = dict(copy.deepcopy(h.context["selected"]["state"]["metrics"]), frozen_scale=True)
    # A changed fine flux is diagnostic, not an implicit current recalibration.
    metrics["unit_flux"] *= 1.03
    metrics["flux"] *= 1.03
    wrapper["record"]["metrics"] = copy.deepcopy(metrics)
    own = {k: v for k, v in metrics.items() if k != "frozen_scale"}
    own.update(geometry={}, mean_B=1.0, raw_bn_rms=1.0, raw_bn_max=1.0)

    def compose(snap, data, arrays, target, method, level):
        assert snap == snapshot and method == "V" and level == spec["level"]
        assert set(arrays) == fields.legacy.RAW_KEYS
        return copy.deepcopy(own)

    monkeypatch.setattr(fields.legacy.numerical, "composed_metrics", compose)
    monkeypatch.setattr(fields.legacy, "direct_fields", lambda *a: {k: 0.0 for k in fields._DIRECT})
    row = fields._operation(
        wrapper,
        dict(op, x=np.array(h.context["selected"]["state"]["x"])),
        spec,
        h.initializations[0],
        h.context,
        h.guard,
    )
    if corrupt:
        row["metrics"]["JN"] += 0.01
        with pytest.raises(ValueError, match="independent JN"):
            REAL_FIELD_ROW(
                row,
                snapshot,
                h.target,
                spec["level"],
                fields._NewArrays(h.guard),
                method="V",
                diagnostic=True,
            )
    else:
        result = REAL_FIELD_ROW(
            row,
            snapshot,
            h.target,
            spec["level"],
            fields._NewArrays(h.guard),
            method="V",
            diagnostic=True,
        )
        assert result["metrics"]["flux"] != snapshot["target_flux"]


@pytest.mark.parametrize("form,corrupt", [(f, c) for f in ("line", "area") for c in (False, True)])
def test_actual_frozen_flux_bridge_and_canonical_reader(tmp_path, monkeypatch, form, corrupt):
    h = fixture(tmp_path, monkeypatch)
    wrapper = h.operations[6 if form == "line" else 9]
    op, snapshot = wrapper["operation"], h.context["selected"]["snapshot"]
    n = op["ntheta"] * op.get("nrho", 1)
    geometry = np.full((n, 3), 1.0 / (3 if form == "line" else 3 * n))
    raw = dict(points=np.zeros((n, 3)), B=np.ones((n, 3)), A=np.ones((n, 3)))
    raw["tangents" if form == "line" else "weighted_normals"] = geometry
    wrapper["arrays"] = h.store.arrays("full-flux", raw)
    wrapper["record"]["flux"] = 1.1 if corrupt else 1.0
    monkeypatch.setattr(fields.legacy.frozen, "loop", lambda *a: (raw["points"], geometry))
    monkeypatch.setattr(fields.legacy.frozen, "fan_area", lambda *a: (raw["points"], geometry))
    monkeypatch.setattr(
        fields.legacy.frozen, "direct_field", lambda *a, **kw: (np.ones((64, 3)), np.ones((64, 3)))
    )
    row = fields._operation(
        wrapper,
        dict(op, x=np.array(h.context["selected"]["state"]["x"])),
        wrapper["spec"],
        h.initializations[6],
        h.context,
        h.guard,
    )
    if corrupt:
        with pytest.raises(ValueError, match="signed flux arithmetic"):
            REAL_FLUX_GRID(row, form, snapshot, h.target["input"], 256, fields._NewArrays(h.guard))
    else:
        result = REAL_FLUX_GRID(
            row, form, snapshot, h.target["input"], 256, fields._NewArrays(h.guard)
        )
        assert result["flux"] == pytest.approx(1.0)
        assert result["direct_errors"] == dict(B=0.0, A=0.0)


def test_actual_core_graph_wrapper_compatibility_without_physical_claim(tmp_path, monkeypatch):
    from test_protected_fine_graph import create

    from fusion_baselines.protected_fine_graph import audit_fine_graph

    base = create(monkeypatch, tmp_path)
    context = base["context"]
    original, snapshot = context["original_context"], context["selected"]["snapshot"]
    source = dict(
        targets=original["seed"]["sources"],
        normalization={k: dict(B2_scale=original["B2_scale"]) for k in ("reference", "selected")},
    )
    archive = dict(
        archived_source=dict(physics_sources=dict(native_sources=dict(cell_sources=source)))
    )
    graph = audit_fine_graph(base["reference"], context, base["source"], lambda: None)
    # The existing core fixture deliberately has nonphysical synthetic coarse
    # refs. Only that unavailable snapshot read is injected; the fine graph,
    # initializer manifests, raw archives and accounting remain real.
    real_read = fields.read_json
    monkeypatch.setattr(
        fields,
        "read_json",
        lambda ref: (
            copy.deepcopy(snapshot)
            if ref == context["coarse"]["selected_snapshot"]
            else real_read(ref)
        ),
    )
    target = dict(
        input={},
        B2_scale=snapshot["B2_scale"],
        target_flux=snapshot["target_flux"],
        targets={n: dict(B2_scale=snapshot["B2_scale"]) for n in (32, 64)},
    )
    monkeypatch.setattr(fields.legacy, "target", lambda *a: target)
    monkeypatch.setattr(
        fields, "_initializer_flux", lambda s, t, n, g: 0.125 if n == 256 else 0.124
    )
    reads = []

    def field(row, snap, target, level, evidence, *, method, diagnostic):
        arrays = evidence.array(row["arrays"])
        assert set(arrays) == fields.legacy.RAW_KEYS
        reads.append("field")
        return dict(metrics=dict(row["metrics"], direct_errors={k: 0.0 for k in fields._DIRECT}))

    def flux(row, form, snap, target, ncoil, evidence):
        assert len(evidence.array(row["arrays"])) == 4
        reads.append("flux")
        return dict(flux=row["flux"], direct_errors=dict(B=0.0, A=0.0))

    monkeypatch.setattr(fields.legacy, "field_row", field)
    monkeypatch.setattr(fields.legacy, "flux_grid", flux)
    report = fields.audit_fields(
        context, archive, graph["initialization_rows"], graph["operation_rows"], lambda: None
    )
    assert reads == ["field"] * 6 + ["flux"] * 18
    assert report["arithmetic_consistency"] is True
    assert report["fine_numerical_qualification"] is report["field_limits_pass"] is False
    assert report["physical_admission"] is report["step4_pass"] is False
