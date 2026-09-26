"""Stubbed historical qualification wiring; no actual saved-seed reconstruction."""

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from test_protected_cell_contract import context_fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import protected_native_inputs as native  # noqa: E402
import qualify_protected_cell_physics as driver  # noqa: E402

from fusion_baselines.protected_run_snapshots import (  # noqa: E402
    SnapshotStore,
    checked_bytes,
    read_json,
)

ROOT = Path(__file__).resolve().parents[1]
LEVEL = dict(index=0, nphi=64, ntheta=64, ncoil=256, ninner=32, offset=0)
PHYSICS_SCOPE = {
    key: False
    for key in (
        "source_admission_verified",
        "external_execution_acknowledgement_verified",
        "field_values_verified",
        "gradients_verified",
        "physical_admission",
        "fine_grid_acceptance",
        "realized_field_transfer",
        "step4_pass",
        "sota_advance",
        "ms1_reached",
    )
}


@pytest.fixture(autouse=True)
def threads(monkeypatch):
    for key, value in driver.THREADS.items():
        monkeypatch.setenv(key, value)


def binding_fixture(tmp_path):
    document = json.loads((ROOT / driver.QUALIFICATION).read_text(encoding="utf-8"))
    calls = dict(checked=[], committed=[], historical=[])
    qualification_ref = dict(path="original-qualification", sha256=driver.QUALIFICATION_HASH)

    def historical(*args):
        calls["historical"].append(args)
        return qualification_ref

    helper = SimpleNamespace(
        sources=lambda root: dict(admitted="native"),
        PROTOCOL=native.PROTOCOL,
        CODE=native.CODE,
        previous=SimpleNamespace(
            _fields=native.previous._fields, previous=SimpleNamespace(historical=historical)
        ),
        read=lambda ref: copy.deepcopy(document),
        same=native.same,
        checked=lambda ref: calls["checked"].append(ref),
        require_committed=lambda root, path: calls["committed"].append(path),
        reference=lambda path: dict(path=str(path), sha256="b" * 64),
        git_state=lambda root: dict(commit="new qualification"),
    )
    return helper, document, calls


def test_binding_retains_all_plumbing_sources_artifacts_and_requires_new_commits(tmp_path):
    helper, _, calls = binding_fixture(tmp_path)
    result = driver._bind(tmp_path, helper)
    assert result["native_sources"] == dict(admitted="native")
    assert calls["historical"] == [
        (tmp_path, driver.QUALIFICATION, driver.QUALIFICATION_REVISION, driver.QUALIFICATION_HASH)
    ]
    assert len(calls["checked"]) == 41
    assert len(result["qualification"]["sources"]) == 13
    assert len(result["qualification"]["artifacts"]) == 28
    assert calls["committed"][-5:] == [tmp_path / name for name in (driver.PROTOCOL, *driver.CODE)]
    assert [row["path"] for row in result["code"]] == [str(tmp_path / name) for name in driver.CODE]


@pytest.mark.parametrize("name", (driver.PROTOCOL, *driver.CODE))
def test_each_new_component_must_be_committed(tmp_path, name):
    helper, _, _ = binding_fixture(tmp_path)

    def fail(root, path):
        if path == tmp_path / name:
            raise ValueError("uncommitted")

    helper.require_committed = fail
    with pytest.raises(ValueError, match="uncommitted"):
        driver._bind(tmp_path, helper)


@pytest.mark.parametrize(
    "mutation",
    [
        "complete",
        "implementation",
        "component",
        "regression",
        "native-work",
        "scope",
        "source-count",
        "source-order",
        "artifact-count",
        "artifact-path",
    ],
)
def test_qualified_plumbing_gate_mutations_reject(tmp_path, mutation):
    helper, doc, _ = binding_fixture(tmp_path)
    if mutation == "complete":
        doc["native_plumbing_qualification_pass"] = 1
    elif mutation == "implementation":
        doc["implementation_commit"] = "wrong"
    elif mutation == "component":
        doc["components"]["pipeline_tests"] = 10
    elif mutation == "regression":
        doc["regression"]["exit_code"] = False
    elif mutation == "native-work":
        doc["real_source_preflight"]["native_requests"] = 1
    elif mutation == "scope":
        doc["limits"]["physical_admission"] = True
    elif mutation == "source-count":
        doc["sources"].pop()
    elif mutation == "source-order":
        doc["sources"].reverse()
    elif mutation == "artifact-count":
        doc["artifacts"].pop()
    else:
        doc["artifacts"][0]["path"] = "../external.json"
    with pytest.raises(ValueError):
        driver._bind(tmp_path, helper)


def test_changed_qualified_bytes_reject(tmp_path):
    helper, _, _ = binding_fixture(tmp_path)
    helper.checked = lambda ref: (_ for _ in ()).throw(ValueError("changed source"))
    with pytest.raises(ValueError, match="changed source"):
        driver._bind(tmp_path, helper)


def original_fixture(tmp_path, nbase=6):
    context = context_fixture(nbase)
    store = SnapshotStore(tmp_path / "historical")
    seed = context["seed"]
    seed_ref = store.json("seed", seed)
    context["seed_reference"] = seed_ref
    candidate = store.arrays("candidate", dict(coefficients=np.asarray(seed["base_coefficients"])))
    certificate = dict(
        kind="cumulative-coil-perturbation",
        status="certified",
        certified=True,
        calculation_complete=True,
        case=seed["case"],
        recorded_producer=True,
    )
    certs = [store.json("certificate-" + str(i), certificate) for i in range(2)]
    operations = [
        store.json(
            "operation-" + str(i),
            dict(
                kind="certificates",
                status="completed",
                state_id="state-00",
                state_index=0,
                repeat=i,
                candidate=candidate,
                certificate=certs[i],
            ),
        )
        for i in range(2)
    ]
    state = dict(
        index=0,
        state_id="state-00",
        kind="seed",
        direction_index=None,
        radius=0.0,
        sign=0,
        status="completed",
        repeat_exact=True,
        seed_snapshot=seed_ref,
        candidate=candidate,
        certificates=certs,
        certificate_operations=operations,
    )
    state_ref = store.json("state", state)
    cases = [
        dict(label=f"n{n}-shape-d100mm", nbase=n, order=m, geometry_report_index=i)
        for n, m, i in ((6, 5, 3), (8, 7, 9))
    ]
    at = 0 if nbase == 6 else 1
    worker = dict(
        case=cases[at], status="completed", seed_snapshot=seed_ref, states=[state_ref] * 26
    )
    worker_ref = store.json("worker", worker)
    result = dict(case=cases[at], status="completed", worker=worker_ref)
    result_ref = store.json("result", result)
    run = dict(matrix=cases, rows=[result_ref] * 2)
    source = dict(
        perturbation=dict(run=store.json("run", run)),
        seeds={cases[at]["label"]: dict(snapshot=seed_ref)},
    )

    def checked(ref):
        checked_bytes(ref, ".npz")
        return Path(ref["path"])

    helper = SimpleNamespace(
        read=read_json,
        checked=checked,
        same=native.same,
        previous=SimpleNamespace(_fields=native.previous._fields),
    )
    return (
        context,
        source,
        SimpleNamespace(native=helper, np=np),
        dict(
            state=state,
            state_ref=state_ref,
            worker=worker,
            worker_ref=worker_ref,
            result=result,
            result_ref=result_ref,
            certificate=certificate,
            certificate_ref=certs[0],
            operation_ref=operations[0],
            operation=read_json(operations[0]),
        ),
    )


@pytest.mark.parametrize("nbase", [6, 8])
def test_original_recorded_certificate_graph_is_loaded_not_regenerated(tmp_path, nbase):
    context, source, dependencies, expected = original_fixture(tmp_path, nbase)
    result = driver.original_certificates(source, context, dependencies)
    assert result["state"] == expected["state_ref"]
    assert len(result["records"]) == 2
    assert result["records"][0]["certificate"] == expected["certificate"]
    assert result["records"][0]["reference"]["path"] != result["records"][1]["reference"]["path"]


@pytest.mark.parametrize(
    "target,key,value",
    [
        ("result", "case", {}),
        ("worker", "case", {}),
        ("state", "kind", "probe"),
        ("state", "index", False),
        ("state", "repeat_exact", 1),
        ("state", "seed_snapshot", {}),
        ("worker", "seed_snapshot", {}),
        ("operation", "repeat", True),
        ("operation", "candidate", {}),
        ("operation", "certificate", {}),
        ("certificate", "case", {}),
        ("certificate", "certified", 1),
        ("certificate", "calculation_complete", False),
    ],
)
def test_original_proof_semantic_substitution_rejects_after_checked_read(
    tmp_path, target, key, value
):
    context, source, dependencies, records = original_fixture(tmp_path)
    original = dependencies.native.read

    def changed(ref):
        row = original(ref)
        if ref == records[target + "_ref"]:
            row[key] = value
        return row

    dependencies.native.read = changed
    with pytest.raises(ValueError):
        driver.original_certificates(source, context, dependencies)


@pytest.mark.parametrize("mutation", ["coefficients", "duplicate-cert", "duplicate-operation"])
def test_original_seed_bits_and_distinct_record_identity_required(tmp_path, mutation):
    context, source, dependencies, records = original_fixture(tmp_path)
    if mutation == "coefficients":
        context["seed"]["base_coefficients"][0][0][0] += 1e-4
    else:
        original = dependencies.native.read

        def changed(ref):
            row = original(ref)
            if ref == records["state_ref"]:
                key = "certificates" if mutation == "duplicate-cert" else "certificate_operations"
                row[key][1] = row[key][0]
            return row

        dependencies.native.read = changed
    with pytest.raises(ValueError):
        driver.original_certificates(source, context, dependencies)


def wiring(tmp_path, monkeypatch):
    calls = dict(
        sources=0, certificate=[], compare=[], reconstruction=[], reserves=[], publications=[]
    )
    matrix = native.previous.matrix()
    source = dict(
        matrix=matrix,
        startup_seed_bundles={row["label"]: dict(saved=row["label"]) for row in matrix},
    )
    bound = dict(native_sources=dict(cell_sources=source), source_identity="synthetic")

    def bind(root):
        calls["sources"] += 1
        return copy.deepcopy(bound)

    def reconstruct(bundle, context, target):
        calls["reconstruction"].append((copy.deepcopy(context["case"]), target))
        assert bundle is context["historical_seed"]
        return dict(
            metrics=copy.deepcopy(bundle["state"]["metrics"]),
            direct_errors={
                key: 0.0
                for key in ("boundary_B", "boundary_A", "inner_B", "inner_A", "loop_B", "loop_A")
            },
            level=LEVEL,
            method=context["case"]["method"],
            complete_bundle_schema_pass=True,
            saved_metrics_reconstruction_pass=True,
            sampled_direct_BA_pass=True,
            comparison_statistics=6,
            sampled_vectors=384,
            sampled_scalar_components=1152,
            **PHYSICS_SCOPE,
        )

    def original(source, context, dependencies):
        proof = dict(recorded_producer=True, nbase=context["case"]["nbase"])
        return dict(
            records=[
                dict(
                    reference=dict(recorded=i),
                    operation=dict(operation=i),
                    certificate=proof.copy(),
                )
                for i in range(2)
            ]
        )

    def audit(seed, report, candidate, recorded):
        assert recorded["recorded_producer"] is True
        assert candidate == seed["base_coefficients"]
        calls["certificate"].append(recorded.copy())
        return recorded.copy()

    def compare(recorded, independent):
        assert recorded == independent and recorded is not independent
        calls["compare"].append(recorded.copy())

    class Store(SnapshotStore):
        def json(self, name, payload):
            calls["publications"].append(name)
            return super().json(name, payload)

    def space(path, reserve):
        calls["reserves"].append(reserve)
        return dict(free_bytes=10 * driver.GIB - len(calls["reserves"]))

    dependencies = SimpleNamespace(
        native=SimpleNamespace(
            same=native.same,
            previous=SimpleNamespace(
                matrix=native.previous.matrix, _fields=native.previous._fields
            ),
            build_context=lambda source, case: context_fixture(
                case["nbase"], case["method"], case["target"]
            ),
        ),
        physics=SimpleNamespace(reconstruct_bundle=reconstruct, SCOPE=PHYSICS_SCOPE),
        historical=SimpleNamespace(
            target=lambda source, case, evidence: dict(target=case["target"]),
            Evidence=lambda: object(),
            numerical=SimpleNamespace(levels=lambda: [LEVEL]),
        ),
        certificate=SimpleNamespace(audit_certificate=audit, compare_certificate=compare),
        Store=Store,
        space_check=space,
    )
    monkeypatch.setattr(driver, "_dependencies", lambda: dependencies)
    monkeypatch.setattr(driver, "sources", bind)
    monkeypatch.setattr(driver, "original_certificates", original)
    return dependencies, calls, bound


def test_all_eight_saved_cases_two_actual_recorded_proof_comparisons_and_scope(
    tmp_path, monkeypatch
):
    _, calls, _ = wiring(tmp_path, monkeypatch)
    reference = driver.qualify(tmp_path / "qualification")
    summary = read_json(reference)
    assert summary["historical_saved_physics_qualification_pass"] is True
    assert len(summary["cases"]) == 8 and len(summary["certificates"]) == 2
    assert [row[0] for row in calls["reconstruction"]] == native.previous.matrix()
    assert [row["nbase"] for row in calls["certificate"]] == [6, 8]
    assert len(calls["compare"]) == 2 and calls["sources"] == 2
    assert calls["reserves"][0] == 3 * driver.GIB
    assert set(calls["reserves"][1:]) == {2 * driver.GIB}
    assert summary["minimum_observed_free_bytes"] == 10 * driver.GIB - len(calls["reserves"])
    assert summary["sampled_BA_comparisons"] == 48 and summary["sampled_vectors"] == 3072
    assert summary["sampled_scalar_components"] == 9216
    assert all(summary[key] is False for key in driver.SCOPE)
    assert all(
        summary[key] == 0
        for key in (
            "native_models_initialized",
            "native_requests",
            "producer_certificates",
            "equilibrium_solves",
            "search_calls",
        )
    )
    assert calls["publications"][-1] == "summary"
    for ref in summary["certificates"]:
        assert all("certificate" not in row for row in read_json(ref)["historical"]["records"])


@pytest.mark.parametrize("key", driver.THREADS)
def test_bad_environment_rejects_before_scientific_imports(tmp_path, monkeypatch, key):
    monkeypatch.delenv(key)
    monkeypatch.setattr(
        driver, "_dependencies", lambda: pytest.fail("scientific import before guard")
    )
    with pytest.raises(ValueError, match="single-thread"):
        driver.qualify(tmp_path / "new")
    assert not (tmp_path / "new").exists()


@pytest.mark.parametrize(
    "failure",
    [
        "source-before",
        "certificate",
        "recorded-repeat",
        "bundle",
        "source-after",
        "thread-drift",
        "initial-disk",
        "live-disk",
        "publication",
        "terminal-publication",
    ],
)
def test_failures_never_return_a_complete_qualification(tmp_path, monkeypatch, failure):
    dependencies, calls, bound = wiring(tmp_path, monkeypatch)
    output = tmp_path / "failed"

    def fail(*args, **kwargs):
        raise OSError("injected failure")

    if failure == "source-before":
        monkeypatch.setattr(driver, "sources", fail)
    elif failure == "certificate":
        dependencies.certificate.audit_certificate = fail
    elif failure == "recorded-repeat":
        dependencies.certificate.compare_certificate = fail
    elif failure == "bundle":
        dependencies.physics.reconstruct_bundle = fail
    elif failure == "source-after":

        def drift(root):
            calls["sources"] += 1
            return (
                dict(bound, source_identity="changed")
                if calls["sources"] > 1
                else copy.deepcopy(bound)
            )

        monkeypatch.setattr(driver, "sources", drift)
    elif failure == "thread-drift":

        def drift(*args):
            monkeypatch.setenv("MKL_NUM_THREADS", "2")
            return dict(records=[dict(certificate={})] * 2)

        monkeypatch.setattr(driver, "original_certificates", drift)
    elif failure in ("initial-disk", "live-disk"):
        space = dependencies.space_check

        def disk(path, reserve):
            if failure == "initial-disk" or calls["reserves"]:
                fail()
            return space(path, reserve)

        dependencies.space_check = disk
    else:
        Store = dependencies.Store

        class FailingStore(Store):
            def json(self, name, payload):
                if name == ("summary" if failure == "terminal-publication" else "certificate-n6"):
                    fail()
                return super().json(name, payload)

        dependencies.Store = FailingStore
    with pytest.raises((ValueError, OSError)):
        driver.qualify(output)
    assert not (output / "summary.json").exists()


@pytest.mark.parametrize(
    "key,value",
    [
        ("saved_metrics_reconstruction_pass", 1),
        ("sampled_direct_BA_pass", False),
        ("comparison_statistics", 5),
        ("sampled_vectors", 383),
        ("method", "wrong"),
        ("physical_admission", True),
        ("direct_errors", {}),
    ],
)
def test_incomplete_reconstruction_cannot_acquire_summary_pass(tmp_path, monkeypatch, key, value):
    dependencies, _, _ = wiring(tmp_path, monkeypatch)
    original = dependencies.physics.reconstruct_bundle
    dependencies.physics.reconstruct_bundle = lambda *args: dict(original(*args), **{key: value})
    with pytest.raises(ValueError):
        driver.qualify(tmp_path / "bad")
    assert not (tmp_path / "bad" / "summary.json").exists()


@pytest.mark.parametrize(
    "name,certificate_calls,bundle_calls",
    [
        ("source-before", 0, 0),
        ("certificate-n6", 1, 0),
        ("case-reference-n6-N", 2, 1),
        ("summary", 2, 8),
    ],
)
def test_swallowed_store_failure_stops_further_work_and_terminal_acknowledgement(
    tmp_path,
    monkeypatch,
    name,
    certificate_calls,
    bundle_calls,
):
    dependencies, calls, _ = wiring(tmp_path, monkeypatch)
    Store = dependencies.Store

    class PoisonStore(Store):
        def json(self, target, payload):
            reference = super().json(target, payload)
            if target == name:
                try:
                    super().json(target, payload)
                except FileExistsError:
                    pass
            return reference

    dependencies.Store = PoisonStore
    with pytest.raises((ValueError, RuntimeError), match="poison|failed"):
        driver.qualify(tmp_path / "poisoned")
    assert len(calls["certificate"]) == certificate_calls
    assert len(calls["reconstruction"]) == bundle_calls
