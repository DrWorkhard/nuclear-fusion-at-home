"""Synthetic supervisor/auditor wiring only; never construct a native model."""

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import protected_native_inputs as native  # noqa: E402
import run_protected_coil_fit as launcher  # noqa: E402

from fusion_baselines.protected_process import _configuration, _returned  # noqa: E402
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json  # noqa: E402
from fusion_baselines.protected_search_journal import _encode  # noqa: E402
from fusion_baselines.protected_worker_control import ControlReader  # noqa: E402

AUDIT_SCOPE = {
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
    for key, value in launcher.THREADS.items():
        monkeypatch.setenv(key, value)


def wiring(tmp_path, monkeypatch):
    matrix = native.previous.matrix()
    source = dict(
        physics_sources=dict(native_sources=dict(cell_sources=dict(matrix=matrix))),
        execution_admission=dict(checkpoint="synthetic-only"),
    )
    calls = dict(
        sources=0,
        cases=[],
        configs=[],
        commands=[],
        audit=[],
        graph=[],
        reserves=[],
        publications=[],
    )
    graph = dict(
        integration_integrity_pass=True,
        complete_bundles=13,
        counts=dict(
            native=dict(attempted=119, completed=119),
            certificate={
                key: dict(attempted=count, completed=count)
                for key, count in (("startup", 10), ("search-seed", 1), ("trial", 1), ("replay", 1))
            },
        ),
        reason="backtracking_exhausted",
        selected_index=None,
    )
    calls["graph_result"] = graph

    def sources(root):
        calls["sources"] += 1
        return copy.deepcopy(source)

    def context(source, case):
        return dict(case=copy.deepcopy(case), original="synthetic original seed")

    def audit_cell(reference, original):
        assert read_json(reference)["case"] == original["case"]
        calls["graph"].append(reference)
        return copy.deepcopy(graph)

    def supervise(config, command, output, *, source_check, validate_return):
        output.mkdir()
        parent = SnapshotStore(output / "parent")
        configuration = config(1000.0, 12345, launcher.THREADS.copy())
        calls["configs"].append(config)
        calls["cases"].append(copy.deepcopy(configuration["case"]))
        config_ref = parent.json("config", configuration)
        assert source_check(configuration) is True
        calls["commands"].append(command(config_ref, 99))
        worker = SnapshotStore(Path(configuration["output"]))
        cell_ref = worker.json(
            "cell",
            dict(
                schema_version=1,
                kind="protected-cell-execution",
                case=configuration["case"],
                producer_complete=True,
                independent_audit_pass=False,
                physical_admission=False,
                step4_pass=False,
            ),
        )
        envelope = dict(
            schema_version=1,
            kind="protected-cell-worker-return",
            case=configuration["case"],
            config=config_ref,
            cell_result=cell_ref,
            source_before=worker.json("source-before", source),
            source_after=worker.json("source-after", source),
            threads=launcher.THREADS.copy(),
            parent_pid=12345,
            worker_pid=12346,
            started_monotonic=1000.0,
            returned_monotonic=1006.0,
            physical_admission=False,
            step4_pass=False,
        )
        returned = worker.json("returned", envelope)
        assert validate_return(returned, configuration) is True
        assert source_check(configuration) is True
        messages = [
            dict(schema_version=1, kind=kind, monotonic=at)
            for kind, at in (
                ("search_started", 1002.0),
                ("search_ended", 1004.0),
                ("returned_result", 1007.0),
            )
        ]
        messages[-1]["reference"] = returned
        observations = [
            parent.json(
                "control-" + str(index),
                dict(
                    schema_version=1,
                    kind="protected-parent-control-observation",
                    observed_monotonic=message["monotonic"] + 0.1,
                    worker_pid=12346,
                    message=message,
                ),
            )
            for index, message in enumerate(messages)
        ]
        return parent.json(
            "acknowledgement",
            dict(
                schema_version=1,
                kind="protected-parent-acknowledgement",
                parent_acknowledged=True,
                case=configuration["case"],
                config=config_ref,
                source=configuration["source"],
                threads=launcher.THREADS.copy(),
                parent_pid=12345,
                worker_pid=12346,
                owned_process_group=12346,
                returncode=0,
                started_monotonic=1000.0,
                spawned_monotonic=1001.0,
                exited_monotonic=1008.0,
                acknowledged_monotonic=1009.0,
                minimum_observed_free_bytes=10 * 1024**3,
                control_observations=observations,
                returned_result=returned,
                physical_admission=False,
                step4_pass=False,
                independent_physical_audit_pass=False,
            ),
        )

    def audit(reference, original, supplied, *, output):
        calls["audit"].append((reference, copy.deepcopy(original["case"])))
        assert supplied == source["physics_sources"]["native_sources"]
        store = SnapshotStore(output)
        changes = {
            key: dict(search_seed=1.0, selected=1.0, difference=0.0, relative_change=0.0)
            for key in ("J", "normal_rms", "normal_max", "vector_rms")
        }
        bundle_count = graph["complete_bundles"]
        certificate_count = sum(row["completed"] for row in graph["counts"]["certificate"].values())
        return store.json(
            "result",
            dict(
                schema_version=1,
                kind="protected-saved-physics-audit",
                status="completed",
                cell_result=reference,
                case=original["case"],
                supplied_source=store.json("source", supplied),
                supplied_context=store.json(
                    "context", dependencies.native.contract.context_metadata(original)
                ),
                graph_audit=store.json("graph", graph),
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
                    certified=certificate_count,
                    uncertified=0,
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
                **AUDIT_SCOPE,
            ),
        )

    class Store(SnapshotStore):
        def json(self, name, payload):
            calls["publications"].append(name)
            return super().json(name, payload)

    def space(path, reserve):
        calls["reserves"].append(reserve)
        return dict(free_bytes=10 * 1024**3)

    dependencies = SimpleNamespace(
        inputs=SimpleNamespace(sources=sources),
        native=SimpleNamespace(
            same=native.same,
            previous=SimpleNamespace(
                matrix=native.previous.matrix, _fields=native.previous._fields
            ),
            build_context=context,
            contract=SimpleNamespace(context_metadata=copy.deepcopy),
        ),
        physics=SimpleNamespace(audit_saved_cell=audit, SCOPE=AUDIT_SCOPE),
        audit_cell=audit_cell,
        supervise_cell=supervise,
        Store=Store,
        read=read_json,
        GIB=1024**3,
        space=space,
        configuration=_configuration,
        returned=_returned,
        ControlReader=ControlReader,
        encode=_encode,
    )
    monkeypatch.setattr(launcher, "_dependencies", lambda: dependencies)
    return dependencies, calls, source


def test_eight_serial_negative_searches_and_no_fine_or_physical_claim(tmp_path, monkeypatch):
    _, calls, _ = wiring(tmp_path, monkeypatch)
    reference = launcher.run(tmp_path / "run")
    result = read_json(reference)
    assert calls["cases"] == native.previous.matrix()
    assert [row[1] for row in calls["audit"]] == native.previous.matrix()
    assert result["completed_cases"] == 8
    assert result["all_eight_constructions_complete"] is True
    assert result["all_eight_independent_coarse_verifications_pass"] is True
    assert result["confirmed_work"] == dict(native_requests=952, bundles=104, certificates=104)
    assert (
        result["fine_phase"] == "required-not-run"
        and result["failure_policy"] == "stop-without-retry"
    )
    assert all(result[key] is False for key in launcher.SCOPE)
    assert calls["reserves"][0] == 3 * 1024**3 and set(calls["reserves"][1:]) == {2 * 1024**3}
    for ref in result["cases"]:
        row = read_json(ref)
        assert row["construction_seconds"] == 9.0 and row["independent_audit_seconds"] >= 0
        assert row["diagnostic_changes"]["J"]["difference"] == 0.0
        assert all(row[key] is False for key in launcher.SCOPE)
    assert all(
        command[2] == "worker"
        and json.loads(command[4])["path"].endswith("config.json")
        and command[-1] == "99"
        for command in calls["commands"]
    )


def test_each_configuration_closure_retains_its_original_case_index_and_output(
    tmp_path, monkeypatch
):
    _, calls, _ = wiring(tmp_path, monkeypatch)
    launcher.run(tmp_path / "run")
    for index, (callback, case) in enumerate(
        zip(calls["configs"], native.previous.matrix(), strict=True)
    ):
        assert callback.__kwdefaults__["case"] == case
        assert callback.__kwdefaults__["index"] == index
        assert callback.__kwdefaults__["cell_output"].name == f"cell-{index:02d}-{case['label']}"


@pytest.mark.parametrize("key", launcher.THREADS)
def test_parent_and_worker_check_threads_before_scientific_imports(tmp_path, monkeypatch, key):
    monkeypatch.delenv(key)
    monkeypatch.setattr(
        launcher, "_dependencies", lambda: pytest.fail("unapproved scientific import")
    )
    with pytest.raises(ValueError, match="thread variables"):
        launcher.run(tmp_path / "run")
    with pytest.raises(ValueError, match="thread variables"):
        launcher.worker({}, 9)


def test_worker_uses_only_explicit_unwrapped_native_dependencies(tmp_path, monkeypatch):
    dependencies, _, source = wiring(tmp_path, monkeypatch)
    calls = []
    context = dict(original=True)
    dependencies.native.build_context = lambda bound, case: (
        calls.append(("context", bound, case)) or context
    )
    dependencies.NativeAdapter = lambda original, bound: (
        calls.append(("adapter", original, bound)) or "native-adapter-stub"
    )

    def worker(config, fd, **kwargs):
        assert config == dict(config="explicit") and fd == 9 and kwargs["root"] == tmp_path
        assert kwargs["bind_sources"] is dependencies.inputs.sources
        original = kwargs["build_context"](source, dict(case="synthetic"))
        assert kwargs["adapter_factory"](original, source) == "native-adapter-stub"
        return "returned-worker-reference"

    dependencies.run_worker = worker
    assert launcher.worker(dict(config="explicit"), 9, root=tmp_path) == "returned-worker-reference"
    assert calls[0][1] == calls[1][2] == source["physics_sources"]["native_sources"]
    assert calls[1][1] is context


@pytest.mark.parametrize(
    "stage", ["supervisor", "graph", "auditor", "post-audit-source", "audit-clock", "live-disk"]
)
def test_failed_first_case_stops_study_without_retry_and_records_unknown_tail(
    tmp_path, monkeypatch, stage
):
    dependencies, calls, source = wiring(tmp_path, monkeypatch)
    output = tmp_path / "failed"

    def fail(*args, **kwargs):
        raise OSError("injected " + stage)

    if stage == "supervisor":
        dependencies.supervise_cell = fail
    elif stage == "graph":
        dependencies.audit_cell = lambda *args: dict(integration_integrity_pass=False)
    elif stage == "auditor":
        dependencies.physics.audit_saved_cell = fail
    elif stage == "post-audit-source":
        old = dependencies.physics.audit_saved_cell

        def audit(*args, **kwargs):
            ref = old(*args, **kwargs)
            source["changed"] = True
            return ref

        dependencies.physics.audit_saved_cell = audit
    elif stage == "audit-clock":
        times = iter((100.0, 99.0))
        monkeypatch.setattr(launcher.time, "monotonic", lambda: next(times))
    else:
        old = dependencies.supervise_cell

        def supervise(*args, **kwargs):
            ref = old(*args, **kwargs)
            dependencies.space = fail
            return ref

        dependencies.supervise_cell = supervise
    with pytest.raises((ValueError, OSError, AssertionError)):
        launcher.run(output)
    assert len(calls["cases"]) <= 1 and not (output / "summary.json").exists()
    if stage != "live-disk":
        failures = list(output.glob("failure-*.json"))
        assert len(failures) == 1
        failure = json.loads(failures[0].read_text(encoding="utf-8"))
        assert failure["status"] == "failed"
        assert failure["complete_failed_tail_work_count_known"] is False
        assert len(failure["following_cases_unexecuted"]) == 7
        assert all(failure[key] is False for key in launcher.SCOPE)


@pytest.mark.parametrize(
    "target,key,value",
    [
        ("ack", "parent_acknowledged", 1),
        ("ack", "returncode", False),
        ("ack", "threads", {}),
        ("ack", "case", {}),
        ("ack", "physical_admission", True),
        ("ack", "owned_process_group", 12345),
        ("ack", "worker_pid", True),
        ("ack", "spawned_monotonic", 999.0),
        ("ack", "acknowledged_monotonic", 2800.0),
        ("config", "case", {}),
        ("config", "threads", {}),
        ("config", "output", "/tmp/unrelated-worker"),
        ("observation", "worker_pid", 999),
        ("observation", "observed_monotonic", 999.0),
    ],
)
def test_parent_link_mutations_cannot_reach_independent_reconstruction(
    tmp_path, monkeypatch, target, key, value
):
    dependencies, calls, _ = wiring(tmp_path, monkeypatch)
    original = dependencies.read

    def changed(ref):
        row = original(ref)
        kinds = dict(
            ack="protected-parent-acknowledgement",
            config="protected-cell-worker-config",
            observation="protected-parent-control-observation",
        )
        if row.get("kind") == kinds[target]:
            row[key] = value
        return row

    dependencies.read = changed
    with pytest.raises((ValueError, TimeoutError)):
        launcher.run(tmp_path / "mutated")
    assert calls["audit"] == [] and not (tmp_path / "mutated" / "summary.json").exists()


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", True),
        ("startup_reconstruction_timing", "pre-search"),
        ("case", {}),
        ("cell_result", {}),
        ("status", "pending"),
        ("reconstruction_component_pass", 1),
        ("protected_directional_startup_pass", False),
        ("field_values_verified", True),
        ("gradients_verified", True),
        ("physical_admission", True),
        ("pareto_dominance", True),
        ("changes_are_resolved_fine_grid_improvements", True),
    ],
)
def test_independent_report_identity_and_scope_mutations_fail(tmp_path, monkeypatch, key, value):
    dependencies, calls, _ = wiring(tmp_path, monkeypatch)
    original = dependencies.read

    def changed(ref):
        row = original(ref)
        if row.get("kind") == "protected-saved-physics-audit":
            row[key] = value
        return row

    dependencies.read = changed
    with pytest.raises(ValueError):
        launcher.run(tmp_path / "bad-audit")
    assert len(calls["audit"]) == 1
    assert not (tmp_path / "bad-audit" / "summary.json").exists()


@pytest.mark.parametrize("target", ["source", "context", "graph", "count"])
def test_report_source_context_graph_and_counts_must_match(tmp_path, monkeypatch, target):
    dependencies, _, _ = wiring(tmp_path, monkeypatch)
    original = dependencies.read

    def changed(ref):
        row = original(ref)
        path = Path(ref["path"])
        if path.parent.name.startswith("audit-"):
            if target == "source" and path.stem == "source":
                row["changed"] = True
            elif target == "context" and path.stem == "context":
                row["original"] = "another seed"
            elif target == "graph" and path.stem == "graph":
                row["complete_bundles"] = 12
            elif target == "count" and path.stem == "result":
                row["independent_work"]["certificate_recomputations"] = 12
        return row

    dependencies.read = changed
    with pytest.raises(ValueError):
        launcher.run(tmp_path / "bad-report")


@pytest.mark.parametrize("name", ["source-before", "case-00", "summary"])
@pytest.mark.parametrize("swallow", [False, True])
def test_publication_failures_never_acknowledge_study_completion(
    tmp_path, monkeypatch, name, swallow
):
    dependencies, calls, _ = wiring(tmp_path, monkeypatch)
    Store = dependencies.Store

    class Failed(Store):
        def json(self, target, payload):
            if target == name and not swallow:
                raise OSError("injected publication failure")
            ref = super().json(target, payload)
            if target == name:
                try:
                    super().json(target, payload)
                except FileExistsError:
                    pass
            return ref

    dependencies.Store = Failed
    with pytest.raises((ValueError, OSError), match="publication|poison"):
        launcher.run(tmp_path / "poisoned")
    assert len(calls["cases"]) == {"source-before": 0, "case-00": 1, "summary": 8}[name]


def test_one_real_qualified_synthetic_pipeline_links_into_launcher_then_stops(
    tmp_path, monkeypatch
):
    """One isolated nonphysical child; reuse the already qualified pipeline stub."""
    from test_protected_cell_contract import context_fixture
    from test_protected_native_pipeline import CHILD, ROOT

    from fusion_baselines.protected_cell_audit import audit_cell
    from fusion_baselines.protected_process import supervise_cell

    dependencies, calls, _ = wiring(tmp_path, monkeypatch)
    dependencies.native.build_context = lambda source, case: context_fixture(
        case["nbase"], case["method"], case["target"]
    )
    dependencies.native.contract = native.contract
    dependencies.audit_cell = audit_cell
    launched = []

    def supervise(config, command, output, **kwargs):
        if launched:
            raise OSError("intentional synthetic one-case stop; no second worker")
        launched.append(output)
        reference = supervise_cell(
            config,
            lambda ref, fd: [
                sys.executable,
                "-c",
                CHILD,
                str(ROOT),
                json.dumps(ref),
                str(fd),
                "normal",
            ],
            output,
            **kwargs,
        )
        acknowledgement = read_json(reference)
        envelope = read_json(acknowledgement["returned_result"])
        context = dependencies.native.build_context({}, acknowledgement["case"])
        graph = audit_cell(envelope["cell_result"], context)
        assert graph["integration_integrity_pass"] is True
        calls["graph_result"].clear()
        calls["graph_result"].update(graph)
        return reference

    dependencies.supervise_cell = supervise
    output = tmp_path / "real-synthetic-pipeline"
    with pytest.raises(OSError, match="intentional synthetic one-case stop"):
        launcher.run(output)
    assert len(launched) == len(calls["audit"]) == 1
    completed = json.loads((output / "case-00.json").read_text(encoding="utf-8"))
    failure = json.loads((output / "failure-01.json").read_text(encoding="utf-8"))
    assert completed["construction_completed"] is True
    assert completed["independent_coarse_verification_pass"] is True
    assert completed["counts"] == dict(native_requests=110, bundles=12, certificates=12)
    assert all(completed[key] is False for key in launcher.SCOPE)
    assert failure["parent_acknowledgement"] is None
    assert len(failure["following_cases_unexecuted"]) == 6
    assert not (output / "summary.json").exists()
