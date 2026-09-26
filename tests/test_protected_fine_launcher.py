"""Serial launcher wiring only; all scientific reconstruction is stubbed."""

import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_protected_fine as launch  # noqa: E402

from fusion_baselines import protected_fine_geometry as geometry  # noqa: E402
from fusion_baselines import protected_fine_process as process  # noqa: E402
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json  # noqa: E402
from fusion_baselines.protected_search_journal import _encode  # noqa: E402

WORK = dict(
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
FIELD_SCOPE = dict.fromkeys(
    (
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
    ),
    False,
)


def fixture(monkeypatch, tmp_path):
    for key in launch.THREADS:
        monkeypatch.setenv(key, "1")
    source = dict(archive=dict(synthetic=True), revision="fixed")
    calls = dict(
        supervise=[], sources=[], contexts=[], fields=[], geometry=[], reserves=[], imports=[]
    )
    active = False

    def sources(root):
        assert active  # First source/import admission is within supervisor's clock.
        calls["sources"].append(root)
        return copy.deepcopy(source)

    def context(manifest, case):
        assert manifest == source
        calls["contexts"].append(copy.deepcopy(case))
        return dict(case=copy.deepcopy(case), coarse=dict(selected="fixed"))

    def graph(reference, context, source_reference, guard):
        guard()
        return dict(
            schema_version=1,
            kind="protected-fine-graph-audit",
            graph_consistency=True,
            reference=reference,
            source=source_reference,
            case=context["case"],
            counts={
                k: dict(attempted=n, completed=n)
                for k, n in (
                    ("initialization", 8),
                    ("operation", 24),
                    ("native", 80),
                    ("points", 552960),
                )
            },
            initialization_rows=["synthetic-init"] * 8,
            operation_rows=["synthetic-operation"] * 24,
            geometry_rows=["synthetic-grid"] * 4,
            geometry_work=dict(synthetic=True),
            complete_execution=False,
            **process.SCOPE,
        )

    def fields(context, archive, init, operations, guard):
        guard()
        assert archive == source["archive"] and len(init) == 8 and len(operations) == 24
        calls["fields"].append(context["case"])
        return dict(
            schema_version=1,
            kind="protected-fine-saved-field-audit",
            status="completed",
            case=context["case"],
            coarse=context["coarse"],
            arithmetic_consistency=True,
            fine_numerical_qualification=True,
            field_limits_pass=True,
            independent_work=copy.deepcopy(WORK),
            **FIELD_SCOPE,
        )

    def geometrical(context, archive, rows, guard):
        guard()
        assert archive == source["archive"] and len(rows) == 4
        calls["geometry"].append(context["case"])
        return dict(
            schema_version=1,
            kind="protected-fine-independent-geometry",
            case=context["case"],
            geometry_consistency=True,
            continuous_geometry_pass=True,
            sampled_geometry_pass=True,
            producer_work=dict(synthetic=True),
            independent_work=dict(
                certificate_recomputations=1, surface_reconstructions=2, direct_grids=4
            ),
            field_calls=0,
            gradient_calls=0,
            equilibrium_solves=0,
            **geometry.SCOPE,
        )

    def space(path, reserve):
        calls["reserves"].append((path, reserve))
        return dict(free_bytes=10 * 1024**3)

    d = SimpleNamespace(
        inputs=SimpleNamespace(sources=sources, build_context=context),
        fields=SimpleNamespace(SCOPE=FIELD_SCOPE, audit_fields=fields),
        geometry=SimpleNamespace(SCOPE=geometry.SCOPE, audit_geometry=geometrical),
        graph=graph,
        Store=SnapshotStore,
        read=read_json,
        encode=_encode,
        GIB=1024**3,
        space=space,
        process=process,
    )

    def dependencies():
        assert active
        calls["imports"].append("inside-clock")
        return d

    def supervise(builder, command, output, *, source_check, validate_return):
        nonlocal active
        started = time.monotonic()
        active = True
        calls["supervise"].append(output)
        output.mkdir()
        parent = SnapshotStore(output / "parent")
        config = builder(started, os.getpid(), copy.deepcopy(launch.THREADS))
        process._configuration(config, started=started, parent_pid=os.getpid(), output=output)
        assert source_check(config) is True
        config_ref = parent.json("config", config)
        args = command(config_ref, 789)
        assert "--root" in args and "--control-fd" in args
        worker = SnapshotStore(Path(config["output"]))
        before = worker.json("source-before", read_json(config["source"]))
        after = worker.json("source-after", read_json(config["source"]))
        core = worker.json(
            "core",
            dict(
                schema_version=1,
                kind="protected-fine-cell-execution",
                case=config["case"],
                source=config["source"],
                producer_complete=True,
                complete_execution=False,
                **process.SCOPE,
            ),
        )
        spawned = time.monotonic()
        worker_pid = os.getpid() + 10000
        returned = worker.json(
            "returned",
            dict(
                schema_version=1,
                kind="protected-fine-worker-return",
                case=config["case"],
                config=config_ref,
                fine_result=core,
                source_before=before,
                source_after=after,
                threads=copy.deepcopy(launch.THREADS),
                parent_pid=os.getpid(),
                worker_pid=worker_pid,
                started_monotonic=started,
                returned_monotonic=time.monotonic(),
                complete_execution=False,
                **process.SCOPE,
            ),
        )
        message = dict(
            schema_version=1,
            kind="fine_returned_result",
            monotonic=time.monotonic(),
            reference=returned,
        )
        observed = parent.json(
            "control-0",
            dict(
                schema_version=1,
                kind="protected-fine-parent-control-observation",
                worker_pid=worker_pid,
                observed_monotonic=time.monotonic(),
                message=message,
            ),
        )
        assert validate_return(returned, config) is True
        assert source_check(config) is True
        return parent.json(
            "acknowledgement",
            dict(
                schema_version=1,
                kind="protected-fine-parent-acknowledgement",
                parent_acknowledged=True,
                complete_execution=True,
                case=config["case"],
                config=config_ref,
                source=config["source"],
                threads=copy.deepcopy(launch.THREADS),
                parent_pid=os.getpid(),
                worker_pid=worker_pid,
                owned_process_group=worker_pid,
                returncode=0,
                started_monotonic=started,
                spawned_monotonic=spawned,
                exited_monotonic=time.monotonic(),
                acknowledged_monotonic=time.monotonic(),
                acknowledgement_clock_scope="before-terminal-publication",
                minimum_observed_free_bytes=5 * 1024**3,
                control_observations=[observed],
                returned_result=returned,
                independent_physical_audit_pass=False,
                **process.SCOPE,
            ),
        )

    monkeypatch.setattr(launch, "_dependencies", dependencies)
    monkeypatch.setattr(launch, "_supervise", supervise)
    return SimpleNamespace(
        d=d,
        source=source,
        calls=calls,
        output=tmp_path / "study",
        supervise=supervise,
        root=tmp_path.resolve(),
    )


def test_eight_serial_cases_explicit_returns_and_separate_scopes(monkeypatch, tmp_path):
    f = fixture(monkeypatch, tmp_path)
    summary = read_json(launch.run(f.output, root=f.root))
    assert summary["matrix"] == launch._cases()
    assert summary["completed_cases"] == summary["numerical_qualified_cases"] == 8
    assert summary["absolute_qualified_cases"] == 8
    assert summary["complete_execution"] is summary["arithmetic_consistency"] is True
    assert all(summary[k] is False for k in launch.SCOPE)
    assert summary["confirmed_work"]["native_requests"] == 640
    assert f.calls["imports"] == ["inside-clock"]
    assert f.calls["contexts"] == f.calls["fields"] == f.calls["geometry"] == launch._cases()
    assert len(f.calls["supervise"]) == 8
    assert all(root == f.root for root in f.calls["sources"])
    for i, ref in enumerate(summary["cases"]):
        case = read_json(ref)
        assert case["case"] == launch._cases()[i]
        report = read_json(case["independent_audit"])
        assert report["cell_result"] == case["cell_result"]
        assert report["parent_acknowledgement"] == case["parent_acknowledgement"]
        assert report["independent_audit_seconds"] >= 0
        assert report["absolute_field_geometry_pass"] is True
        for key in ("graph", "fields", "geometry"):
            read_json(report[key])


@pytest.mark.parametrize(
    "component,key",
    [
        ("fields", "fine_numerical_qualification"),
        ("fields", "field_limits_pass"),
        ("geometry", "continuous_geometry_pass"),
        ("geometry", "sampled_geometry_pass"),
    ],
)
def test_threshold_negative_is_completed_and_next_cases_continue(
    monkeypatch, tmp_path, component, key
):
    f = fixture(monkeypatch, tmp_path)
    owner = getattr(f.d, component)
    name = "audit_fields" if component == "fields" else "audit_geometry"
    original = getattr(owner, name)

    def negative(*args):
        result = original(*args)
        if result["case"] == launch._cases()[0]:
            result[key] = False
        return result

    monkeypatch.setattr(owner, name, negative)
    summary = read_json(launch.run(f.output, root=f.root))
    assert summary["completed_cases"] == 8 and summary["absolute_qualified_cases"] == 7
    assert summary["absolute_field_geometry_pass"] is False
    assert summary["complete_execution"] is summary["arithmetic_consistency"] is True
    assert read_json(summary["cases"][0])["absolute_field_geometry_pass"] is False


@pytest.mark.parametrize(
    "component,key,value",
    [
        ("graph", "graph_consistency", False),
        ("graph", "complete_execution", True),
        ("fields", "arithmetic_consistency", False),
        ("fields", "fine_numerical_qualification", 1),
        ("fields", "field_limits_pass", 0),
        ("fields", "step4_pass", True),
        ("geometry", "geometry_consistency", False),
        ("geometry", "sampled_geometry_pass", 1),
        ("geometry", "absolute_field_geometry_pass", True),
        ("geometry", "field_calls", True),
    ],
)
def test_bad_audit_stops_without_retry_or_later_cases(monkeypatch, tmp_path, component, key, value):
    f = fixture(monkeypatch, tmp_path)
    owner = f.d if component == "graph" else getattr(f.d, component)
    name = {"graph": "graph", "fields": "audit_fields", "geometry": "audit_geometry"}[component]
    original = getattr(owner, name)

    def changed(*args):
        result = original(*args)
        result[key] = value
        return result

    monkeypatch.setattr(owner, name, changed)
    with pytest.raises(ValueError):
        launch.run(f.output, root=f.root)
    assert len(f.calls["supervise"]) == 1
    failure = json.loads((f.output / "study/failure-00.json").read_text())
    assert failure["following_cases_unexecuted"] == launch._cases()[1:]
    assert not (f.output / "study/summary.json").exists()


@pytest.mark.parametrize("component", ["graph", "fields", "geometry"])
def test_auditor_exception_preserves_completed_parent_not_fake_case(
    monkeypatch, tmp_path, component
):
    f = fixture(monkeypatch, tmp_path)
    owner = f.d if component == "graph" else getattr(f.d, component)
    name = {"graph": "graph", "fields": "audit_fields", "geometry": "audit_geometry"}[component]

    def broken(*args):
        raise ArithmeticError("synthetic reconstruction mismatch")

    monkeypatch.setattr(owner, name, broken)
    with pytest.raises(ArithmeticError):
        launch.run(f.output, root=f.root)
    failure = json.loads((f.output / "study/failure-00.json").read_text())
    assert read_json(failure["parent_acknowledgement"])["complete_execution"] is True
    assert failure["independent_audit"] is None
    assert not (f.output / "study/case-00.json").exists()


def test_closed_source_gate_never_builds_context_or_launches_command(monkeypatch, tmp_path):
    f = fixture(monkeypatch, tmp_path)

    def closed(root):
        raise ValueError("missing committed execution checkpoint")

    monkeypatch.setattr(f.d.inputs, "sources", closed)
    monkeypatch.setattr(launch, "_command", lambda *a: pytest.fail("closed gate launched child"))
    with pytest.raises(ValueError, match="checkpoint"):
        launch.run(f.output, root=f.root)
    assert f.calls["contexts"] == [] and len(f.calls["supervise"]) == 1


@pytest.mark.parametrize(
    "name",
    ["source-before", "fields-00", "geometry-00", "audit-00", "case-00", "source-after", "summary"],
)
def test_swallowed_publication_poison_cannot_return_success(monkeypatch, tmp_path, name):
    f = fixture(monkeypatch, tmp_path)
    original = SnapshotStore.json

    def poisoned(self, stem, value):
        reference = original(self, stem, value)
        if self.directory.name == "study" and stem == name:
            self._failed = True
        return reference

    monkeypatch.setattr(SnapshotStore, "json", poisoned)
    with pytest.raises(ValueError, match="poisoned"):
        launch.run(f.output, root=f.root)
    assert (f.output / "study" / (name + ".json")).exists()


def test_source_drift_after_first_completed_case_stops_next_launch(monkeypatch, tmp_path):
    f = fixture(monkeypatch, tmp_path)
    original = f.d.inputs.sources

    def drift(root):
        result = original(root)
        if len(f.calls["supervise"]) > 1:
            result["revision"] = "changed"
        return result

    monkeypatch.setattr(f.d.inputs, "sources", drift)
    with pytest.raises(ValueError, match="next-cell source"):
        launch.run(f.output, root=f.root)
    failure = json.loads((f.output / "study/failure-01.json").read_text())
    assert len(failure["completed_cases"]) == 1
    assert failure["following_cases_unexecuted"] == launch._cases()[2:]
    assert len(f.calls["contexts"]) == 1


def test_reentrant_run_swallowed_by_callback_still_poisons_outer_run(monkeypatch, tmp_path):
    f = fixture(monkeypatch, tmp_path)
    original = f.d.inputs.sources

    def reentrant(root):
        with pytest.raises(ValueError, match="serial"):
            launch.run(tmp_path / "nested")
        return original(root)

    monkeypatch.setattr(f.d.inputs, "sources", reentrant)
    with pytest.raises(ValueError, match="poisoned"):
        launch.run(f.output, root=f.root)
    assert f.calls["contexts"] == []


def test_bad_threads_fail_before_import_or_source_admission(monkeypatch, tmp_path):
    fixture(monkeypatch, tmp_path)
    monkeypatch.setenv("OMP_NUM_THREADS", "2")
    monkeypatch.setattr(
        launch, "_dependencies", lambda: pytest.fail("premature scientific imports")
    )
    with pytest.raises(ValueError, match="four registered"):
        launch.run(tmp_path / "rejected")


def test_fresh_output_cannot_resume_or_overwrite(monkeypatch, tmp_path):
    f = fixture(monkeypatch, tmp_path)
    f.output.mkdir()
    with pytest.raises(FileExistsError):
        launch.run(f.output, root=f.root)
    assert f.calls["supervise"] == [] and f.calls["imports"] == []


def test_import_is_science_free_in_fresh_interpreter():
    code = (
        "import run_protected_fine,sys; assert not any(k in sys.modules for k in "
        "('numpy','scipy','simsopt','jax','run_clear_coil_field_start'))"
    )
    env = dict(
        os.environ, PYTHONPATH=str(launch.ROOT / "scripts") + os.pathsep + str(launch.ROOT / "src")
    )
    subprocess.run([sys.executable, "-c", code], env=env, check=True, timeout=15)


def test_command_forwards_root_explicit_reference_and_fd(tmp_path):
    ref = dict(path="/synthetic/config.json", sha256="a" * 64, bytes=20)
    args = launch._command(ref, 123, tmp_path)
    assert args[0] == sys.executable and args[1].endswith("run_protected_fine_worker.py")
    assert json.loads(args[args.index("--config-reference") + 1]) == ref
    assert args[-4:] == ["--control-fd", "123", "--root", str(tmp_path)]


@pytest.mark.parametrize(
    "change",
    [
        "kind",
        "extra",
        "parent-boolean",
        "worker-equal",
        "group",
        "negative-clock",
        "clock-backward",
        "clock-deadline",
        "case",
        "threads",
        "source",
        "returncode",
        "missing-observation",
        "duplicate-observation",
        "returned-reference",
        "reserve",
        "observation-pid",
        "observation-clock",
        "observation-extra",
        "message-reference",
        "core-source",
    ],
)
def test_acknowledgement_linkage_cannot_be_substituted(monkeypatch, tmp_path, change):
    f = fixture(monkeypatch, tmp_path)

    def substituted(*args, **kwargs):
        ref = f.supervise(*args, **kwargs)
        ack = read_json(ref)
        storage = SnapshotStore(Path(ref["path"]).parent / "mutations")
        if change == "kind":
            ack["kind"] = "protected-parent-acknowledgement"
        elif change == "extra":
            ack["extra"] = False
        elif change == "parent-boolean":
            ack["parent_pid"] = True
        elif change == "worker-equal":
            ack["worker_pid"] = ack["parent_pid"]
        elif change == "group":
            ack["owned_process_group"] += 1
        elif change == "negative-clock":
            ack["spawned_monotonic"] = -1
        elif change == "clock-backward":
            ack["exited_monotonic"] = ack["started_monotonic"] - 1
        elif change == "clock-deadline":
            ack["acknowledged_monotonic"] += 1800
        elif change == "case":
            ack["case"] = launch._cases()[1]
        elif change == "threads":
            ack["threads"]["MKL_NUM_THREADS"] = "2"
        elif change == "source":
            ack["source"] = ack["config"]
        elif change == "returncode":
            ack["returncode"] = False
        elif change == "missing-observation":
            ack["control_observations"] = []
        elif change == "duplicate-observation":
            ack["control_observations"] *= 2
        elif change == "returned-reference":
            ack["returned_result"] = ack["source"]
        elif change == "reserve":
            ack["minimum_observed_free_bytes"] = 2 * 1024**3 - 1
        elif change == "core-source":
            envelope = read_json(ack["returned_result"])
            raw = Path(envelope["fine_result"]["path"])
            raw.write_bytes(raw.read_bytes() + b" ")
        else:
            observation = read_json(ack["control_observations"][0])
            if change == "observation-pid":
                observation["worker_pid"] += 1
            elif change == "observation-clock":
                observation["observed_monotonic"] = ack["exited_monotonic"] + 1
            elif change == "observation-extra":
                observation["extra"] = False
            else:
                observation["message"]["reference"] = ack["source"]
            ack["control_observations"] = [storage.json("observation", observation)]
        return storage.json("acknowledgement", ack)

    monkeypatch.setattr(launch, "_supervise", substituted)
    with pytest.raises((ValueError, TimeoutError)):
        launch.run(f.output, root=f.root)
    assert f.calls["contexts"] == []
    assert len(f.calls["supervise"]) == 1


@pytest.mark.parametrize(
    "component,key",
    [
        ("graph", "reference"),
        ("graph", "source"),
        ("graph", "counts"),
        ("graph", "case"),
        ("fields", "coarse"),
        ("fields", "independent_work"),
        ("fields", "case"),
        ("geometry", "producer_work"),
        ("geometry", "independent_work"),
        ("geometry", "case"),
    ],
)
def test_complete_audit_work_and_cross_links_are_required(monkeypatch, tmp_path, component, key):
    f = fixture(monkeypatch, tmp_path)
    owner = f.d if component == "graph" else getattr(f.d, component)
    name = {"graph": "graph", "fields": "audit_fields", "geometry": "audit_geometry"}[component]
    original = getattr(owner, name)

    def changed(*args):
        result = original(*args)
        result[key] = {}
        return result

    monkeypatch.setattr(owner, name, changed)
    with pytest.raises(ValueError):
        launch.run(f.output, root=f.root)
    assert len(f.calls["supervise"]) == 1


def test_resource_error_stops_without_starting_later_cell(monkeypatch, tmp_path):
    f = fixture(monkeypatch, tmp_path)

    def low_space(*args):
        raise OSError("synthetic disk reserve")

    monkeypatch.setattr(f.d, "space", low_space)
    with pytest.raises(OSError, match="disk reserve"):
        launch.run(f.output, root=f.root)
    assert f.calls["contexts"] == [] and len(f.calls["supervise"]) == 1


def test_persisted_audit_mutation_cannot_be_acknowledged(monkeypatch, tmp_path):
    f = fixture(monkeypatch, tmp_path)
    original = f.d.geometry.audit_geometry

    def tamper(*args):
        result = original(*args)
        path = f.output / "study/fields-00.json"
        path.write_bytes(path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(f.d.geometry, "audit_geometry", tamper)
    with pytest.raises(ValueError):
        launch.run(f.output, root=f.root)
    assert not (f.output / "study/case-00.json").exists()
