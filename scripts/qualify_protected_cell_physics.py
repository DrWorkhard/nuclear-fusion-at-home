"""Qualify independent reconstruction of saved seeds, never a new native run.

Scientific imports are lazy. The public function and CLI require the registered
single-thread environment first; neither changes the existing environment.
"""

import argparse
import math
import os
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
THREADS = {
    key: "1"
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    )
}
GIB = 1024**3
PROTOCOL = "docs/optimization/PROTECTED_PHYSICS_PROTOCOL.md"
CODE = (
    "scripts/audit_protected_cell_physics.py",
    "tests/test_protected_cell_physics.py",
    "scripts/qualify_protected_cell_physics.py",
    "tests/test_qualify_protected_cell_physics.py",
)
QUALIFICATION = "evidence/protected-native-plumbing-v1.json"
QUALIFICATION_REVISION = "721774b"
QUALIFICATION_HASH = "1f8dcb5e4c9772770f61b127b47946013c1de0c4dedda251b3eac1787ebfdd6f"
SCOPE = dict(
    source_admission_verified=False,
    external_execution_acknowledgement_verified=False,
    field_values_verified=False,
    gradients_verified=False,
    new_protected_startup_qualified=False,
    native_runtime_screen_qualified=False,
    full_grid_fields_verified=False,
    all_gradient_components_verified=False,
    physical_admission=False,
    fine_grid_acceptance=False,
    realized_field_transfer=False,
    step4_pass=False,
    sota_advance=False,
    ms1_reached=False,
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def thread_guard():
    require(
        {key: os.environ.get(key) for key in THREADS} == THREADS,
        "all four registered single-thread environment values must already equal '1'",
    )


def _dependencies():
    import audit_clear_coil_field_start as historical
    import audit_protected_cell_physics as physics
    import numpy as np
    import protected_native_inputs as native

    from fusion_baselines import coil_perturbation_audit as certificate
    from fusion_baselines.protected_run_snapshots import SnapshotStore
    from fusion_baselines.resource_guard import space_check

    return SimpleNamespace(
        historical=historical,
        physics=physics,
        native=native,
        np=np,
        certificate=certificate,
        Store=SnapshotStore,
        space_check=space_check,
    )


def _bind(root, native):
    root = Path(root).resolve()
    bound = native.sources(root)
    qualification_ref = native.previous.previous.historical(
        root, QUALIFICATION, QUALIFICATION_REVISION, QUALIFICATION_HASH
    )
    qualification = native.read(qualification_ref)
    fields = native.previous._fields
    fields(
        qualification,
        dict(
            schema_version=1,
            kind="protected-native-plumbing-qualification",
            status="completed",
            native_plumbing_qualification_pass=True,
            implementation_commit="fd069e91ee62bc86771eb27e9898456a7b6bfe4c",
        ),
        "completed immutable native plumbing qualification",
    )
    require(
        native.same(
            qualification["components"],
            dict(
                source_adapter_tests=131,
                control_tests=46,
                worker_tests=26,
                process_tests=101,
                pipeline_tests=11,
                total_focused_tests=315,
            ),
        ),
        "complete qualified plumbing components",
    )
    fields(
        qualification["regression"],
        dict(
            exit_code=0,
            passed=3233,
            failures=0,
            errors=0,
            skipped=0,
            warnings=334,
        ),
        "recorded full plumbing regression",
    )
    fields(
        qualification["real_source_preflight"],
        dict(
            contexts_passed=8,
            source_bound_adapters=8,
            native_models_initialized=0,
            native_requests=0,
            producer_certificates=0,
            equilibrium_solves=0,
        ),
        "original read-only eight-context qualification",
    )
    require(
        type(qualification["limits"]) is dict
        and len(qualification["limits"]) == 17
        and all(value is False for value in qualification["limits"].values()),
        "preserve every plumbing scope exclusion",
    )
    expected = (native.PROTOCOL, *native.CODE, "src/fusion_baselines/resource_guard.py")
    require(
        [row["path"] for row in qualification["sources"]] == list(expected)
        and len(expected) == 13
        and len(qualification["artifacts"]) == 28,
        "complete 13-source/28-artifact plumbing identity",
    )
    pins = {}
    for key in ("sources", "artifacts"):
        pins[key] = []
        for row in qualification[key]:
            path = Path(row["path"])
            require(
                not path.is_absolute() and ".." not in path.parts,
                "repository-relative qualification reference",
            )
            ref = dict(path=str(root / path), sha256=row["sha256"], bytes=row["bytes"])
            native.checked(ref)
            if key == "sources":
                native.require_committed(root, root / path)
            pins[key].append(ref)
    for name in (PROTOCOL, *CODE):
        native.require_committed(root, root / name)
    return dict(
        native_sources=bound,
        qualification=dict(evidence=qualification_ref, **pins),
        protocol=native.reference(root / PROTOCOL),
        code=[native.reference(root / name) for name in CODE],
        repository=native.git_state(root),
    )


def sources(root=ROOT):
    import protected_native_inputs as native

    return _bind(root, native)


def original_certificates(source, context, dependencies):
    """Read both recorded producer proofs, bound through the admitted run graph."""
    native, np = dependencies.native, dependencies.np
    nbase, order = context["case"]["nbase"], context["case"]["order"]
    index = 0 if nbase == 6 else 1
    case = dict(
        label=f"n{nbase}-shape-d100mm",
        nbase=nbase,
        order=order,
        geometry_report_index=3 if nbase == 6 else 9,
    )
    run = native.read(source["perturbation"]["run"])
    result_ref = run["rows"][index]
    result = native.read(result_ref)
    worker = native.read(result["worker"])
    require(
        all(
            native.same(value, case)
            for value in (run["matrix"][index], result["case"], worker["case"])
        ),
        "original two-class geometry case",
    )
    require(
        result["status"] == worker["status"] == "completed" and len(worker["states"]) == 26,
        "completed original 26-state worker",
    )
    state_ref = worker["states"][0]
    state = native.read(state_ref)
    descriptor = dict(
        index=0,
        state_id="state-00",
        kind="seed",
        direction_index=None,
        radius=0.0,
        sign=0,
        status="completed",
        repeat_exact=True,
    )
    native.previous._fields(state, descriptor, "original seed, not perturbation or terminal repeat")
    seed_ref = context["seed_reference"]
    require(
        all(
            native.same(value, seed_ref)
            for value in (
                source["seeds"][case["label"]]["snapshot"],
                worker["seed_snapshot"],
                state["seed_snapshot"],
            )
        ),
        "unchanged original cumulative seed reference",
    )
    with np.load(native.checked(state["candidate"]), allow_pickle=False) as archive:
        require(archive.files == ["coefficients"], "original seed coefficient archive only")
        coefficients = archive["coefficients"].copy()
    expected = np.asarray(context["seed"]["base_coefficients"], dtype=float)
    require(
        coefficients.dtype == expected.dtype
        and coefficients.shape == expected.shape
        and coefficients.tobytes() == expected.tobytes(),
        "bit-identical recorded seed candidate",
    )
    require(
        len(state["certificates"]) == len(state["certificate_operations"]) == 2,
        "both original repeated certificates required",
    )
    require(
        len({ref["path"] for ref in state["certificates"]}) == 2
        and len({ref["path"] for ref in state["certificate_operations"]}) == 2,
        "two distinct original producer records and operations",
    )
    records = []
    for repeat, ref in enumerate(state["certificates"]):
        operation_ref = state["certificate_operations"][repeat]
        operation = native.read(operation_ref)
        native.previous._fields(
            operation,
            dict(
                kind="certificates",
                status="completed",
                state_id="state-00",
                state_index=0,
                repeat=repeat,
                candidate=state["candidate"],
                certificate=ref,
            ),
            "original producer certificate operation",
        )
        certificate = native.read(ref)
        native.previous._fields(
            certificate,
            dict(
                kind="cumulative-coil-perturbation",
                status="certified",
                certified=True,
                calculation_complete=True,
                case=context["seed"]["case"],
            ),
            "actual original producer seed proof",
        )
        records.append(dict(reference=ref, operation=operation_ref, certificate=certificate))
    require(
        state["certificates"][0]["sha256"] == state["certificates"][1]["sha256"],
        "recorded original certificate repeats must have identical bytes",
    )
    return dict(
        result=result_ref,
        worker=result["worker"],
        state=state_ref,
        candidate=state["candidate"],
        seed=seed_ref,
        records=records,
    )


def reconstruction_gate(result, context, dependencies):
    dependencies.native.previous._fields(
        result,
        dict(
            method=context["case"]["method"],
            level=dependencies.historical.numerical.levels()[0],
            complete_bundle_schema_pass=True,
            saved_metrics_reconstruction_pass=True,
            sampled_direct_BA_pass=True,
            comparison_statistics=6,
            sampled_vectors=384,
            sampled_scalar_components=1152,
        ),
        "complete independent saved-bundle reconstruction",
    )
    errors = result["direct_errors"]
    require(
        type(errors) is dict
        and set(errors)
        == {
            "boundary_B",
            "boundary_A",
            "inner_B",
            "inner_A",
            "loop_B",
            "loop_A",
        },
        "all six independent B/A comparison statistics",
    )
    require(
        all(
            type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 5e-10
            for value in errors.values()
        ),
        "unchanged direct-field error limit",
    )
    require(
        all(result[key] is False for key in dependencies.physics.SCOPE),
        "historical reconstruction does not broaden scientific scope",
    )


def qualify(output, root=ROOT):
    """Return only a successfully published complete historical qualification."""
    thread_guard()
    dependencies = _dependencies()
    output = Path(output).absolute()
    initial = dependencies.space_check(output.parent, 3 * GIB)
    minimum = initial["free_bytes"]
    store = dependencies.Store(output)

    def healthy():
        require(store._failed is False, "qualification publication poisoned")

    def guard():
        nonlocal minimum
        healthy()
        thread_guard()
        minimum = min(minimum, dependencies.space_check(output, 2 * GIB)["free_bytes"])
        healthy()

    def publish(name, payload):
        reference = store.json(name, payload)
        healthy()
        return reference

    def save(name, payload):
        guard()
        return publish(name, payload)

    guard()
    before = sources(root)
    guard()
    before_ref = save("source-before", before)
    native_source = before["native_sources"]
    source = native_source["cell_sources"]
    require(
        dependencies.native.same(source["matrix"], dependencies.native.previous.matrix()),
        "exact ordered eight-case qualification matrix",
    )
    contexts = [dependencies.native.build_context(native_source, case) for case in source["matrix"]]
    require(
        all(
            dependencies.native.same(context["case"], case)
            for context, case in zip(contexts, source["matrix"], strict=True)
        ),
        "every loaded context preserves its exact case",
    )
    proofs = {}
    for at in (0, 2):
        guard()
        context = contexts[at]
        original = original_certificates(source, context, dependencies)
        guard()
        proof = dependencies.certificate.audit_certificate(
            context["seed"],
            context["geometry_report"],
            context["seed"]["base_coefficients"],
            original["records"][0]["certificate"],
        )
        dependencies.certificate.compare_certificate(original["records"][1]["certificate"], proof)
        original = dict(
            original,
            records=[
                {key: value for key, value in record.items() if key != "certificate"}
                for record in original["records"]
            ],
        )
        guard()
        proofs[context["case"]["nbase"]] = save(
            f"certificate-n{context['case']['nbase']}",
            dict(
                kind="original-seed-certificate-reconstruction",
                historical=original,
                independent=proof,
                recorded_proofs_checked=2,
                **SCOPE,
            ),
        )
    reports = []
    for context in contexts:
        guard()
        target = dependencies.historical.target(
            source, context["case"], dependencies.historical.Evidence()
        )
        guard()
        reconstruction = dependencies.physics.reconstruct_bundle(
            context["historical_seed"], context, target
        )
        reconstruction_gate(reconstruction, context, dependencies)
        guard()
        reports.append(
            save(
                "case-" + context["case"]["label"],
                dict(
                    kind="historical-seed-physics-reconstruction",
                    case=context["case"],
                    original_seed=context["seed_reference"],
                    historical_bundle=source["startup_seed_bundles"][context["case"]["label"]],
                    certificate=proofs[context["case"]["nbase"]],
                    reconstruction=reconstruction,
                    **SCOPE,
                ),
            )
        )
    guard()
    after = sources(root)
    require(dependencies.native.same(before, after), "unchanged complete before/after source graph")
    guard()
    after_ref = save("source-after", after)
    guard()
    return publish(
        "summary",
        dict(
            schema_version=1,
            kind="protected-physics-historical-qualification",
            status="completed",
            historical_saved_physics_qualification_pass=True,
            source_before=before_ref,
            source_after=after_ref,
            cases=reports,
            certificates=list(proofs.values()),
            historical_contexts_reconstructed=8,
            original_certificate_recomputations=2,
            recorded_original_certificates_checked=4,
            sampled_BA_comparisons=48,
            sampled_vectors=3072,
            sampled_scalar_components=9216,
            native_models_initialized=0,
            native_requests=0,
            producer_certificates=0,
            equilibrium_solves=0,
            search_calls=0,
            threads=THREADS.copy(),
            minimum_observed_free_bytes=minimum,
            **SCOPE,
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    reference = qualify(args.output)
    print(reference["path"])


if __name__ == "__main__":
    main()
