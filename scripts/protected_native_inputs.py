"""Pinned native-plumbing sources and read-only construction of eight cell contexts.

Predecessors own their historical source graphs. This additive layer binds the
completed synthetic qualification, its exact sources/artifacts and new plumbing.
No native model, field, certificate or equilibrium calculation is performed.
"""

import copy
from pathlib import Path

import numpy as np
import protected_coil_fit_inputs as previous
from current_diagnostic_inputs import reference
from run_jac_scaled_study import require_committed

from fusion_baselines import protected_cell_contract as contract
from fusion_baselines.provenance import git_state

PROTOCOL = "docs/optimization/PROTECTED_NATIVE_PLUMBING_PROTOCOL.md"
CODE = (
    "scripts/protected_native_inputs.py",
    "scripts/protected_native_adapter.py",
    "tests/test_protected_native_inputs.py",
    "tests/test_protected_native_adapter.py",
    "src/fusion_baselines/protected_worker_control.py",
    "tests/test_protected_worker_control.py",
    "src/fusion_baselines/protected_process.py",
    "tests/test_protected_process.py",
    "scripts/run_protected_cell_worker.py",
    "tests/test_protected_cell_worker.py",
    "tests/test_protected_native_pipeline.py",
)
QUALIFICATION = "evidence/protected-cell-synthetic-v1.json"
QUALIFICATION_REVISION = "ef23278"
QUALIFICATION_HASH = "8ab6729adb7b842835bf76f4761835ff20b138a7974f8a2ad49f480cef19d714"
QUALIFIED_NAMES = (
    "docs/optimization/PROTECTED_CELL_PROTOCOL.md",
    "docs/optimization/PROTECTED_RUNNER_PROTOCOL.md",
    "docs/optimization/PROTECTED_METHOD_REVIEW.md",
    "scripts/protected_coil_fit_inputs.py",
    "src/fusion_baselines/protected_cell_contract.py",
    "src/fusion_baselines/protected_run_cell.py",
    "src/fusion_baselines/protected_cell_audit.py",
    "tests/test_protected_cell_contract.py",
    "tests/test_protected_run_cell.py",
    "tests/test_protected_cell_audit.py",
    "src/fusion_baselines/protected_run_ledger.py",
    "src/fusion_baselines/protected_run_snapshots.py",
    "src/fusion_baselines/protected_startup.py",
    "src/fusion_baselines/protected_search_journal.py",
    "src/fusion_baselines/protected_coil_search.py",
    "src/fusion_baselines/protected_coil_search_audit.py",
    "src/fusion_baselines/clear_coil_field_audit.py",
    "src/fusion_baselines/clear_coil_geometry_audit.py",
    "src/fusion_baselines/coupled_coil_audit.py",
)
ARTIFACT_NAMES = tuple(
    "artifacts/protected-cell-v1/" + name
    for name in (
        "audit-crc-red.xml",
        "audit-initial.xml",
        "audit-review-fixed.xml",
        "cell-expanded.xml",
        "cell-final.xml",
        "cell-independent.xml",
        "cell-initial.xml",
        "cell-model-routing-red.xml",
        "cell-review-fixed.xml",
        "cell-review-red.xml",
        "contract-independent.xml",
        "contract-initial.xml",
        "contract-review-fixed.xml",
        "contract-review-red.xml",
        "docs-fixed.xml",
        "docs-initial.xml",
        "full-regression.log",
        "full-regression.xml",
        "native-contract-check/result.json",
        "native-contract-check-v2/result.json",
        "native-contract-check-v2.py",
        "native-contract-check.py",
    )
)
QUALIFICATION_LIMITS = (
    "native_plumbing_qualified",
    "new_native_search_executed",
    "physical_reconstruction_integrated",
    "source_admission_rerun_in_this_stage",
    "external_execution_acknowledgement_verified",
    "field_values_verified",
    "gradients_verified",
    "geometry_certificates_verified",
    "physical_admission",
    "step4_pass",
    "sota_advance",
    "ms1_reached",
    "external_peer_review",
    "thread_safety_qualified",
    "hardware_power_loss_tested",
    "untrusted_pr_sandbox",
)
require, same, read, checked = previous.require, previous.same, previous.read, previous.checked


def qualification_gate(document):
    """Typed named gates; immutable evidence/source hashes are separately checked."""
    previous._fields(
        document,
        dict(
            schema_version=1,
            kind="protected-cell-synthetic-qualification",
            status="completed",
            synthetic_integration_qualification_pass=True,
            implementation_commit="c17123aef40b2f3accc80d506be5e0c72c36d01a",
        ),
        "completed original synthetic integration qualification",
    )
    require(
        same(
            document.get("components"),
            dict(contract_tests=179, cell_tests=54, graph_audit_tests=66, total_focused_tests=299),
        ),
        "all original component qualifications",
    )
    require(
        same(document.get("limits"), {key: False for key in QUALIFICATION_LIMITS}),
        "synthetic qualification cannot acquire physical/native scope",
    )
    previous._fields(
        document.get("regression"),
        dict(exit_code=0, passed=2918, failures=0, errors=0, skipped=0, warnings=334),
        "successful full recorded regression",
    )
    previous._fields(
        document.get("historical_compatibility"),
        dict(
            historical_contexts_passed=8,
            identity_mutations_rejected=72,
            finite_overcurrent_synthetic_bundles_retained=8,
            individual_input_references_checked=28,
            native_requests=0,
            equilibrium_solves=0,
            geometry_certificate_calculations=0,
            full_source_graph_re_admitted=False,
        ),
        "bounded read-only historical compatibility",
    )
    for key, names in (("sources", QUALIFIED_NAMES), ("artifacts", ARTIFACT_NAMES)):
        rows = document.get(key)
        require(type(rows) is list and len(rows) == len(names), "complete qualification " + key)
        require(all(type(row) is dict for row in rows), "qualification reference objects")
        require(
            [row.get("path") for row in rows] == list(names),
            "exact ordered original qualification " + key,
        )
        for row in rows:
            require(
                set(row) == {"path", "sha256", "bytes"}
                or (key == "artifacts" and set(row) == {"path", "sha256", "bytes", "junit"}),
                "original qualification reference schema",
            )


def prerequisites(root):
    root = Path(root).resolve()
    cell_sources = previous.sources(root)
    qualification_ref = previous.previous.historical(
        root, QUALIFICATION, QUALIFICATION_REVISION, QUALIFICATION_HASH
    )
    qualification = read(qualification_ref)
    qualification_gate(qualification)
    sources, artifacts = [], []
    for key, collection in (("sources", sources), ("artifacts", artifacts)):
        for row in qualification[key]:
            ref = dict(path=str(root / row["path"]), sha256=row["sha256"], bytes=row["bytes"])
            checked(ref)
            if key == "sources":
                require_committed(root, root / row["path"])
            collection.append(ref)
    return dict(
        cell_sources=cell_sources,
        qualification=qualification_ref,
        qualified_sources=sources,
        qualification_artifacts=artifacts,
    )


def sources(root):
    root = Path(root).resolve()
    bound = prerequisites(root)
    for name in (PROTOCOL, *CODE):
        require_committed(root, root / name)
    return dict(
        cell_sources=bound.pop("cell_sources"),
        plumbing=dict(
            **bound,
            protocol=reference(root / PROTOCOL),
            code=[reference(root / name) for name in CODE],
        ),
        repository=git_state(root),
    )


def build_context(source_manifest, case):
    """Load exact saved original data with the historical noncanonical NPZ loader."""
    require(
        type(source_manifest) is dict
        and set(source_manifest) == {"cell_sources", "plumbing", "repository"},
        "complete native source manifest",
    )
    source = source_manifest["cell_sources"]
    require(
        type(source) is dict and same(source.get("matrix"), previous.matrix()),
        "source-bound eight-cell matrix",
    )
    require(any(same(case, item) for item in source["matrix"]), "exact registered cell identity")
    case = copy.deepcopy(case)
    old_field_source = source["startup"]["source"]
    for key in ("targets", "normalization", "target_archives"):
        require(same(source[key], old_field_source[key]), "unchanged inherited field " + key)
    seed_entry = source["seeds"][case["seed_label"]]
    require(
        same(seed_entry["geometry_report_index"], 3 if case["nbase"] == 6 else 9),
        "exact original geometry report selection",
    )
    seed = read(seed_entry["snapshot"])
    geometry_audit = read(source["geometry"]["audit"])
    report = geometry_audit["sets"][seed_entry["geometry_report_index"]]
    refs = source["startup_seed_bundles"][case["label"]]
    row = read(refs["operation"])
    require(
        same(row.get("snapshot"), refs["snapshot"]) and same(row.get("arrays"), refs["arrays"]),
        "historical seed operation owns the exact snapshot and arrays",
    )
    snapshot = read(refs["snapshot"])
    previous.seed_bundle_gate(row, snapshot, case, seed, old_field_source)
    with np.load(checked(refs["arrays"]), allow_pickle=False) as archive:
        arrays = {key: archive[key].copy() for key in archive.files}
    context = dict(
        case=case,
        seed=seed,
        seed_reference=seed_entry["snapshot"],
        geometry_report=report,
        geometry_audit_reference=source["geometry"]["audit"],
        geometry_report_index=seed_entry["geometry_report_index"],
        target_sources=source["targets"][case["target"]],
        B2_scale=source["normalization"][case["target"]]["B2_scale"],
        historical_seed=dict(
            state=dict(
                x=row["x"], value=row["J"], gradient=row["gradient"], metrics=row["metrics"]
            ),
            snapshot=snapshot,
            arrays=arrays,
        ),
        historical_seed_reference=refs["operation"],
    )
    contract.validate_context(context)
    return copy.deepcopy(context)
