"""Independent saved-data reconstruction, not source or execution admission.

The caller supplies the explicitly returned cell reference and original admitted
context/source manifest. Matching supplied data cannot authenticate its admission.
No native model/field, producer certificate, equilibrium or search is invoked.
NumPy/SciPy field and geometry reconstructions are real independent calculations.
"""

import copy
from pathlib import Path

import audit_clear_coil_field_start as legacy
import numpy as np
from protected_native_inputs import build_context

from fusion_baselines import coil_perturbation_audit as certificates
from fusion_baselines import protected_cell_contract as contract
from fusion_baselines.protected_cell_audit import audit_cell
from fusion_baselines.protected_run_ledger import _reference
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_arrays, read_json
from fusion_baselines.protected_search_journal import _encode
from fusion_baselines.protected_startup import derivative_screen, exact_bundle_replay
from fusion_baselines.resource_guard import GIB, space_check

SCOPE = dict(
    source_admission_verified=False,
    external_execution_acknowledgement_verified=False,
    field_values_verified=False,
    gradients_verified=False,
    physical_admission=False,
    fine_grid_acceptance=False,
    realized_field_transfer=False,
    step4_pass=False,
    sota_advance=False,
    ms1_reached=False,
)
DIRECT_NAMES = (
    "boundary_B",
    "boundary_A",
    "inner_B",
    "inner_A",
    "loop_B",
    "loop_A",
)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, label):
    _need(_encode(actual) == _encode(expected), "physics identity: " + label)


class _BundleArrays:
    """One already schema-checked in-memory bundle, not a historical file loader."""

    def __init__(self, arrays):
        self.arrays = arrays
        self.token = object()

    def array(self, token):
        _need(token is self.token, "exact in-memory bundle array routing")
        return self.arrays


def reconstruct_bundle(bundle, context, target_context):
    """Reconstruct one complete bundle with frozen metric/direct-field primitives.

    Accepts numerical data, so old noncanonical archives and new canonical
    snapshots share the same calculation after their respective checked loaders.
    Caller binds context/target provenance separately. This helper does not verify
    every full-grid field value, gradient component or physical acceptance gate.
    """
    contract.validate_context(context)
    contract.validate_bundle(bundle, bundle["state"]["x"], context)
    _same(target_context["B2_scale"], context["B2_scale"], "fixed archived normalization")
    _same(
        target_context["target_flux"],
        bundle["snapshot"]["target_flux"],
        "independently oriented target flux",
    )
    _same(
        target_context["targets"][32]["B2_scale"],
        context["B2_scale"],
        "active interior normalization",
    )
    evidence = _BundleArrays(bundle["arrays"])
    row = dict(
        status="completed",
        arrays=evidence.token,
        J=bundle["state"]["value"],
        metrics=bundle["state"]["metrics"],
    )
    level = legacy.numerical.levels()[0]
    # Do not invoke the older snapshot_identity or full-space FD helpers: their
    # seed-only index assumptions and probe directions differ from this study.
    own = legacy.field_row(
        row,
        bundle["snapshot"],
        target_context,
        level,
        evidence,
        method=context["case"]["method"],
        diagnostic=False,
    )
    _need(own["status"] == "completed", "complete independent field-row reconstruction")
    metrics = copy.deepcopy(own["metrics"])
    errors = metrics.pop("direct_errors")
    _need(
        type(errors) is dict and set(errors) == set(DIRECT_NAMES),
        "all six direct B/A comparisons required",
    )
    for key in DIRECT_NAMES:
        value = errors[key]
        _need(
            type(value) in (int, float) and np.isfinite(value) and 0 <= value <= 5e-10,
            "finite registered direct B/A tolerance: " + key,
        )
    result = dict(
        metrics=metrics,
        direct_errors=errors,
        level=level,
        method=context["case"]["method"],
        complete_bundle_schema_pass=True,
        saved_metrics_reconstruction_pass=True,
        sampled_direct_BA_pass=True,
        comparison_statistics=6,
        sampled_vectors=384,
        sampled_scalar_components=1152,
        **SCOPE,
    )
    _encode(result)
    return result


def _change(initial, selected):
    initial, selected = float(initial), float(selected)
    _need(np.isfinite(initial) and np.isfinite(selected), "finite diagnostic endpoints")
    difference = selected - initial
    relative = None if initial == 0 else difference / abs(initial)
    _need(
        np.isfinite(difference) and (relative is None or np.isfinite(relative)),
        "finite diagnostic changes",
    )
    return dict(
        search_seed=initial, selected=selected, difference=difference, relative_change=relative
    )


class _Audit:
    def __init__(self, output):
        self.output = Path(output)
        _need(self.output.is_absolute(), "absolute fresh physics-audit directory required")
        space_check(self.output.parent, 3 * GIB)
        self.output.mkdir(exist_ok=False)
        self.store = SnapshotStore(self.output / "records")
        self.failed = False

    def healthy(self):
        _need(not self.failed and self.store._failed is False, "physics audit publication poisoned")

    def guard(self):
        self.healthy()
        space_check(self.output, 2 * GIB)
        self.healthy()

    def save(self, name, value):
        self.guard()
        reference = self.store.json(name, value)
        self.healthy()
        return reference

    def run(self, result_reference, context, source_manifest):
        self.guard()
        _reference(result_reference)
        # Own copies prevent accidental caller mutations from changing the
        # meaning of later identities. Arrays keep exact dtype and signed bits.
        result_reference, context, source_manifest = copy.deepcopy(
            (result_reference, context, source_manifest)
        )
        _encode(source_manifest)
        expected = build_context(source_manifest, context["case"])
        contract.validate_context(context)
        _same(
            contract.context_metadata(context),
            contract.context_metadata(expected),
            "rebuilt complete original context",
        )
        exact_bundle_replay(context["historical_seed"], expected["historical_seed"])
        self.guard()
        graph = audit_cell(result_reference, context)
        _need(
            graph.get("integration_integrity_pass") is True,
            "complete saved-graph audit required: " + graph.get("error", ""),
        )
        # All structure/order/selection/replay checks precede any reconstruction.
        result = read_json(result_reference)
        source_ref = self.save("supplied-source", source_manifest)
        context_ref = self.save("supplied-context", contract.context_metadata(context))
        graph_ref = self.save("graph-audit", graph)
        evidence = legacy.Evidence()
        target = legacy.target(source_manifest["cell_sources"], context["case"], evidence)
        _same(target["B2_scale"], context["B2_scale"], "independent target normalization")
        _same(
            target["target_flux"],
            context["historical_seed"]["snapshot"]["target_flux"],
            "independent original signed target flux",
        )
        target_ref = self.save(
            "target",
            dict(
                case=context["case"],
                sources=context["target_sources"],
                normalization=source_manifest["cell_sources"]["normalization"][
                    context["case"]["target"]
                ],
                archives=source_manifest["cell_sources"]["target_archives"][
                    context["case"]["target"]
                ],
                checked_historical_references=evidence.references,
                B2_scale=target["B2_scale"],
                target_flux=target["target_flux"],
                ns=401,
                archive_resolution=64,
                active_inner_resolution=32,
            ),
        )
        certificate_rows, bundle_rows = [], []
        certified = uncertified = 0
        for index, reference in enumerate(result["certificates"]):
            self.guard()
            record = read_json(reference)
            coefficients = np.asarray(record["x"], dtype=float).reshape(
                context["case"]["nbase"], 3, 2 * context["case"]["order"] + 1
            )
            independent = certificates.audit_certificate(
                context["seed"], context["geometry_report"], coefficients, record["result"]
            )
            _need(
                type(independent.get("certified")) is bool,
                "independent certificate has a typed decision",
            )
            certified += independent["certified"] is True
            uncertified += independent["certified"] is False
            certificate_rows.append(
                self.save(
                    f"certificate-{index:03d}",
                    dict(
                        manifest=reference,
                        operation_id=record["operation_id"],
                        phase=record["phase"],
                        state_sha256=record["state_sha256"],
                        original_seed=context["seed_reference"],
                        geometry_report=context["geometry_audit_reference"],
                        geometry_report_index=context["geometry_report_index"],
                        independent_certificate=independent,
                        certificate_verified=True,
                        **SCOPE,
                    ),
                )
            )
        startup_states, startup_values = [], []
        seed_metrics = selected_metrics = None
        search_seed_ref = None
        for index, reference in enumerate(result["bundles"]):
            self.guard()
            record = read_json(reference)
            bundle = dict(
                state=record["state"],
                snapshot=read_json(record["snapshot"]),
                arrays=read_arrays(record["arrays"]),
            )
            own = reconstruct_bundle(bundle, context, target)
            bundle_rows.append(
                self.save(
                    f"bundle-{index:03d}",
                    dict(
                        manifest=reference,
                        operation_id=record["operation_id"],
                        phase=record["phase"],
                        snapshot=record["snapshot"],
                        arrays=record["arrays"],
                        certificate=record["certificate"],
                        reconstruction=own,
                    ),
                )
            )
            if record["phase"] == "startup":
                startup_states.append(record["state"])
                startup_values.append(own["metrics"]["J"])
            if record["phase"] == "search-seed":
                _need(seed_metrics is None, "one independently reconstructed search seed")
                seed_metrics, search_seed_ref = own["metrics"], reference
            if reference == result["selected_bundle"]:
                _need(selected_metrics is None, "one independently reconstructed selection")
                selected_metrics = own["metrics"]
        self.guard()
        case = context["case"]
        startup = derivative_screen(
            context["historical_seed"]["state"]["x"],
            case["nbase"],
            case["order"],
            startup_states,
            independent_values=startup_values,
        )
        _need(
            startup["startup_screen_pass"] is True
            and startup["independently_supplied_values"] is True
            and len(startup["checks"]) == 8,
            "independently reconstructed protected startup screen failed",
        )
        startup_ref = self.save("startup-reconstruction", startup)
        _need(
            seed_metrics is not None and selected_metrics is not None,
            "reconstructed search seed and selected state required",
        )
        changes = {
            key: _change(seed_metrics[key], selected_metrics[key])
            for key in ("J", "normal_rms", "normal_max", "vector_rms")
        }
        certificate_count, bundle_count = len(certificate_rows), len(bundle_rows)
        _need(
            certificate_count
            == certified + uncertified
            == sum(v["completed"] for v in graph["counts"]["certificate"].values())
            and bundle_count == graph["complete_bundles"],
            "complete independent audit counts",
        )
        final = dict(
            schema_version=1,
            kind="protected-saved-physics-audit",
            status="completed",
            cell_result=result_reference,
            case=case,
            supplied_source=source_ref,
            supplied_context=context_ref,
            graph_audit=graph_ref,
            target_reconstruction=target_ref,
            certificates=certificate_rows,
            bundles=bundle_rows,
            startup_reconstruction=startup_ref,
            search_seed_bundle=search_seed_ref,
            selected_bundle=result["selected_bundle"],
            diagnostic_changes=changes,
            changes_are_resolved_fine_grid_improvements=False,
            pareto_dominance=False,
            reconstruction_component_pass=True,
            saved_graph_integrity_pass=True,
            saved_metrics_reconstruction_pass=True,
            sampled_direct_BA_pass=True,
            cumulative_certificates_verified=True,
            protected_directional_startup_pass=True,
            startup_reconstruction_timing="posthoc",
            independent_work=dict(
                certificate_recomputations=certificate_count,
                certified=certified,
                uncertified=uncertified,
                bundle_reconstructions=bundle_count,
                sampled_comparison_statistics=6 * bundle_count,
                sampled_vectors=384 * bundle_count,
                sampled_scalar_components=1152 * bundle_count,
                startup_directional_checks=8,
                native_requests=0,
                native_model_constructions=0,
                producer_certificate_calls=0,
                equilibrium_solves=0,
                search_calls=0,
            ),
            **SCOPE,
        )
        # No resource callback after final publication. A failed fsync may leave
        # a file, but only a successfully returned reference acknowledges it.
        return self.save("result", final)


def audit_saved_cell(result_reference, context, source_manifest, *, output):
    """Publish a complete posthoc reconstruction or raise, preserving failed tails.

    This component never authenticates source admission or the parent execution
    acknowledgement. Bind both externally before treating its report as experiment
    evidence. Existing directories and failed attempts cannot be resumed.
    """
    audit = _Audit(output)
    try:
        return audit.run(result_reference, context, source_manifest)
    except BaseException:
        audit.failed = True
        raise


if __name__ == "__main__":
    raise SystemExit("Saved-data reconstruction API only; no native execution entry point.")
