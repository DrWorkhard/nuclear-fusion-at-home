"""Independent saved fine-field arithmetic, not source/execution/geometry admission.

Uses only frozen NumPy/SciPy reconstruction primitives. No native models, fields,
equilibria, searches, producer certificates, file discovery or report publication.
Threshold failures are complete negative results; malformed or arithmetically
inconsistent evidence raises and cannot produce a completed report.
"""

import copy
import math

import audit_clear_coil_field_start as legacy
import numpy as np

from fusion_baselines import protected_cell_contract as contract
from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_run_ledger import _reference
from fusion_baselines.protected_run_snapshots import read_arrays, read_json
from fusion_baselines.protected_search_journal import _encode

SCOPE = dict(
    source_admission_verified=False,
    external_execution_acknowledgement_verified=False,
    complete_execution=False,
    complete_graph_verified=False,
    continuous_geometry_verified=False,
    sampled_geometry_verified=False,
    absolute_field_geometry_pass=False,
    physical_admission=False,
    fine_grid_acceptance=False,
    field_values_verified=False,
    gradients_verified=False,
    resolved_fine_grid_improvement=False,
    pareto_dominance=False,
    realized_field_transfer=False,
    step4_pass=False,
    sota_advance=False,
    ms1_reached=False,
)
_MODEL_SCOPE = (
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
_COARSE_KEYS = {
    "case_record",
    "parent_acknowledgement",
    "cell_result",
    "independent_reconstruction",
    "selected_bundle",
    "selected_snapshot",
    "selected_certificate",
}
_DIRECT = {"boundary_B", "boundary_A", "inner_B", "inner_A", "loop_B", "loop_A"}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, label):
    _need(_encode(actual) == _encode(expected), "fine field identity: " + label)


def _scalar(value, label):
    _need(type(value) in (int, float) and math.isfinite(value), "finite plain scalar: " + label)
    return float(value)


def _context(context, archive):
    _need(
        type(context) is dict
        and set(context) == {"case", "original_context", "coarse", "selected"},
        "exact supplied fine context",
    )
    case, original, selected = context["case"], context["original_context"], context["selected"]
    plan.validate_case(case)
    contract.validate_context(original)
    _same(original["case"], case, "original case")
    _need(
        type(context["coarse"]) is dict and set(context["coarse"]) == _COARSE_KEYS,
        "complete coarse binding references",
    )
    for reference in context["coarse"].values():
        _reference(reference)
    _need(
        type(selected) is dict and set(selected) == {"state", "snapshot", "arrays", "certificate"},
        "complete selected coarse context",
    )
    contract.validate_bundle(
        {k: selected[k] for k in ("state", "snapshot", "arrays")}, selected["state"]["x"], original
    )
    _same(
        read_json(context["coarse"]["selected_snapshot"]),
        selected["snapshot"],
        "immutable original selected snapshot",
    )
    binding = archive["archived_source"]["physics_sources"]["native_sources"]["cell_sources"]
    _same(binding["targets"], original["seed"]["sources"], "both original target sources")
    _same(binding["targets"][case["target"]], original["target_sources"], "selected target source")
    _same(
        binding["normalization"][case["target"]]["B2_scale"],
        original["B2_scale"],
        "original fixed normalization",
    )
    return binding


class _NewArrays:
    """New archives exclusively use the canonical, dtype-preserving reader."""

    def __init__(self, guard):
        self.guard = guard

    def array(self, reference):
        self.guard()
        result = read_arrays(reference)
        self.guard()
        return result


def _initialized(row, spec, context):
    _need(
        type(row) is dict and set(row) == {"schema_version", "kind", "case", "spec", "metadata"},
        "complete saved fine initialization",
    )
    for key, expected in dict(
        schema_version=1, kind="protected-fine-initialization", case=context["case"], spec=spec
    ).items():
        _same(row[key], expected, "initializer " + key)
    metadata, original, selected = row["metadata"], context["original_context"], context["selected"]
    seed, snapshot = original["seed"], selected["snapshot"]
    x = plan._coordinates(context["case"], selected["state"]["x"])
    seed_x = np.asarray(seed["base_coefficients"], dtype=np.float64).ravel()
    physical_currents = [float(-1e5 if coil["flip"] else 1e5) for coil in seed["physical"]]
    expected = dict(
        spec=spec,
        case=context["case"],
        original_seed=original["seed_reference"],
        geometry_audit=original["geometry_audit_reference"],
        target_sources=original["target_sources"],
        coarse=context["coarse"],
        names=seed["names"],
        seed_x=seed_x.tolist(),
        selected_x=x.tolist(),
        initializer_physical_currents=physical_currents,
        initialization_work=dict(seed_A_calls=1, seed_A_points=256),
        **{key: snapshot[key] for key in ("scale", "B2_scale", "target_flux")},
        **{key: False for key in _MODEL_SCOPE},
    )
    _need(
        type(metadata) is dict
        and set(metadata)
        == set(expected) | {"original_seed_unit_flux", "initialization_native_calls"},
        "exact initialized model metadata",
    )
    for key, value in expected.items():
        _same(metadata[key], value, "original initialization " + key)
    flux = _scalar(metadata["original_seed_unit_flux"], "original seed flux")
    _need(abs(flux) > 1e-12, "nondegenerate original seed flux")
    calls = metadata["initialization_native_calls"]
    _need(type(calls) is list and len(calls) == 1, "single initialization native request")
    fixed = dict(
        index=0,
        field="loop",
        quantity="A",
        points=256,
        status="completed",
        native_started=True,
        native_completed=True,
    )
    event = calls[0]
    _need(
        type(event) is dict
        and set(event) == set(fixed) | {"started_monotonic", "completed_monotonic"},
        "complete initializer native event",
    )
    for key, value in fixed.items():
        _same(event[key], value, "initializer native " + key)
    started = _scalar(event["started_monotonic"], "initializer start")
    completed = _scalar(event["completed_monotonic"], "initializer completion")
    _need(0 <= started <= completed, "forward initializer request times")
    return flux


def _initializer_flux(original_seed, target_context, ncoil, guard):
    """Original coefficients and signed 100 kA currents, never selected scale/x.

    The existing direct kernel also computes B; only the complete 256-node A
    contour integral is compared here. These are eight scalar comparisons,
    separate from the 72 sampled B/A comparisons of selected candidate fields.
    """
    guard()
    base = np.asarray(original_seed["base_coefficients"], dtype=float)
    physical = np.stack(
        [
            np.asarray(row["matrix"], dtype=float).T @ base[row["base_index"]]
            for row in original_seed["physical"]
        ]
    )
    curves = legacy.frozen.fourier_curves(physical, ncoil)
    currents = np.array([-1e5 if row["flip"] else 1e5 for row in original_seed["physical"]])
    points, tangents = legacy.frozen.loop(target_context["input"], 256)
    guard()
    _, potential = legacy.frozen.filament_field_and_potential(
        points, curves["positions"], curves["tangents"], currents
    )
    guard()
    _need(
        potential.shape == tangents.shape == (256, 3) and np.isfinite(potential).all(),
        "complete independently reconstructed initialization potential",
    )
    value = float(np.mean(np.sum(potential * tangents, axis=1)))
    _need(np.isfinite(value) and abs(value) > 1e-12, "nondegenerate independent seed initializer")
    return value


def _operation(row, expected, spec, initialization, context, guard):
    _need(
        type(row) is dict
        and set(row)
        == {
            "schema_version",
            "kind",
            "status",
            "case",
            "spec",
            "operation",
            "arrays",
            "record",
            "initialization",
        },
        "complete saved fine operation",
    )
    for key, value in dict(
        schema_version=1,
        kind="protected-fine-operation",
        status="completed",
        case=context["case"],
        spec=spec,
        operation={k: v for k, v in expected.items() if k != "x"},
    ).items():
        _same(row[key], value, "operation " + key)
    _reference(row["arrays"])
    _reference(row["initialization"])
    guard()
    _same(read_json(row["initialization"]), initialization, "operation's own initialized model")
    record, snapshot = row["record"], context["selected"]["snapshot"]
    _need(
        type(record) is dict
        and set(record)
        == {
            "snapshot",
            "scale",
            "B2_scale",
            "target_flux",
            "metrics" if spec["kind"] == "diagnostic" else "flux",
        },
        "exact frozen fine field record",
    )
    _same(
        record["snapshot"], context["coarse"]["selected_snapshot"], "selected coarse snapshot ref"
    )
    for key in ("scale", "B2_scale", "target_flux"):
        _same(record[key], snapshot[key], "frozen selected " + key)
    return dict(status="completed", arrays=row["arrays"], **record, **row["operation"])


def audit_fields(context, archive, initializations, operations, guard):
    """Audit ordered decoded wrappers; the whole-graph auditor binds their refs.

    field_limits_pass includes current and sampled geometry limits on all six
    diagnostic rows. It is separate from refinement/flux qualification, the
    continuous certificate and four direct geometry grids. This component does
    not authenticate the source archive or acknowledge successful execution.
    """
    _need(callable(guard), "resource guard required")
    guard()
    binding = _context(context, archive)
    case, snapshot = context["case"], context["selected"]["snapshot"]
    _need(
        type(initializations) is list and len(initializations) == 8,
        "all eight ordered fine initializations required",
    )
    _need(
        type(operations) is list and len(operations) == 24,
        "all twenty-four ordered fine operations required",
    )
    target = legacy.target(binding, case, legacy.Evidence())
    guard()
    _same(target["B2_scale"], snapshot["B2_scale"], "independent fixed B2")
    _same(target["target_flux"], snapshot["target_flux"], "independently oriented target flux")
    for ninner in (32, 64):
        _same(
            target["targets"][ninner]["B2_scale"],
            snapshot["B2_scale"],
            "independent archived normalization",
        )
    evidence = _NewArrays(guard)
    initial_reports, diagnostics, blocks = [], [], []
    position = 0
    for spec, initialized in zip(plan.model_plan(case), initializations, strict=True):
        guard()
        recorded = _initialized(initialized, spec, context)
        own = _initializer_flux(
            context["original_context"]["seed"], target, spec["grid"]["ncoil"], guard
        )
        error = legacy.close(recorded, own, "original-seed initializer A flux", rtol=5e-10, atol=0)
        initial_reports.append(
            dict(
                model_id=spec["id"],
                ncoil=spec["grid"]["ncoil"],
                recorded=recorded,
                independent=own,
                absolute_error=error,
                relative_error=error / abs(own),
                passed=True,
                original_physical_current_A=100000.0,
                loop_points=256,
            )
        )
        flux_rows = []
        for expected in plan.operation_plan(spec, context["selected"]["state"]["x"]):
            guard()
            wrapper = operations[position]
            position += 1
            row = _operation(wrapper, expected, spec, initialized, context, guard)
            if spec["kind"] == "diagnostic":
                result = legacy.field_row(
                    row,
                    snapshot,
                    target,
                    spec["level"],
                    evidence,
                    method=case["method"],
                    diagnostic=True,
                )
                metrics = copy.deepcopy(result["metrics"])
                errors = metrics.pop("direct_errors")
                _need(set(errors) == _DIRECT, "all six direct diagnostic B/A comparisons")
                diagnostics.append(
                    dict(
                        operation_id=expected["operation_id"],
                        level=copy.deepcopy(spec["level"]),
                        status="completed",
                        metrics=metrics,
                        direct_errors=errors,
                        arrays=copy.deepcopy(row["arrays"]),
                    )
                )
            else:
                result = legacy.flux_grid(
                    row,
                    expected["form"],
                    snapshot,
                    target["input"],
                    spec["grid"]["ncoil"],
                    evidence,
                )
                _need(set(result["direct_errors"]) == {"B", "A"}, "both direct flux fields")
                flux_rows.append(
                    dict(
                        operation_id=expected["operation_id"],
                        arrays=copy.deepcopy(row["arrays"]),
                        **result,
                    )
                )
            guard()
        if flux_rows:
            checks = legacy.flux_checks(
                [r["flux"] for r in flux_rows[:3]],
                [r["flux"] for r in flux_rows[3:]],
                snapshot["target_flux"],
            )
            _need(len(checks["checks"]) == 27, "complete twenty-seven flux-block checks")
            blocks.append(dict(ncoil=spec["grid"]["ncoil"], grids=flux_rows, **checks))
    _need(
        position == 24 and len(diagnostics) == 6 and len(blocks) == 2,
        "complete registered fine numerical work",
    )
    refinements = legacy.numerical.refinement_checks(diagnostics)
    across = legacy.flux_coil_comparison(blocks[0], blocks[1], snapshot["target_flux"])
    _need(
        len(refinements["checks"]) == 5 and len(across["checks"]) == 9,
        "complete refinement and cross-coil comparisons",
    )
    # True here means initializer arithmetic passed and supplied coarse startup
    # was already qualified elsewhere; there are no new fine derivative probes.
    limits = legacy.physical_gates(snapshot, diagnostics, startup_pass=True)
    numerical_pass = refinements["passed"] and across["passed"] and all(r["passed"] for r in blocks)
    result = dict(
        schema_version=1,
        kind="protected-fine-saved-field-audit",
        status="completed",
        case=copy.deepcopy(case),
        coarse=copy.deepcopy(context["coarse"]),
        original_initializers=initial_reports,
        diagnostics=diagnostics,
        flux_blocks=blocks,
        refinements=refinements,
        flux_coil_comparison=across,
        diagnostic_limits=limits["checks"],
        arithmetic_consistency=True,
        fine_numerical_qualification=bool(numerical_pass),
        field_limits_pass=bool(limits["physical_seed_pass"]),
        field_limits_scope=(
            "all six rows: field, current and sampled geometry; not continuous geometry"
        ),
        independent_work=dict(
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
        ),
        **SCOPE,
    )
    guard()
    return legacy.numerical.json_value(result)
