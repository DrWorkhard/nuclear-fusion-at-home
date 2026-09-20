"""Real producer persistence→independent workflow wiring with explicit math mocks.

These fixtures qualify schemas, counters, source/reference handling and clocks,
not numerical geometry. Actual mathematical and direct geometry are covered by
the separate108 primitive and28 direct-audit controls.
"""

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_coil_perturbation as audit  # noqa: E402
from test_coil_perturbation_workflow import runner, setup_fake, worker_config  # noqa: E402


def mock_certificate(seed, report, coefficients):
    accepted = bool(np.max(abs(np.asarray(coefficients) - seed["base_coefficients"])) < 1e-4)
    return dict(
        status="certified" if accepted else "uncertified",
        certified=accepted,
        calculation_complete=True,
        mock_only=True,
        checksum=float(np.sum(coefficients)),
    )


def mock_direct(snapshot, coefficients, certificate, level, raw, surfaces):
    assert set(raw) == {"mock_only"} and set(surfaces) == {"reference", "selected"}
    nphysical, ncoil = 4 * snapshot["nbase"], level["ncoil"]
    return dict(
        passed=True,
        nphysical=nphysical,
        ncoil=ncoil,
        offset=level["offset"],
        cp_distances_checked=2 * nphysical * ncoil,
        coil_pairs_checked=nphysical * (nphysical - 1) // 2,
        work=audit.direct.bounded_work(nphysical, ncoil),
    )


@pytest.fixture(scope="module")
def saved(tmp_path_factory):
    directory = tmp_path_factory.mktemp("synthetic-perturbation-wiring")
    with pytest.MonkeyPatch.context() as monkeypatch:
        source = setup_fake(monkeypatch, directory)
        qualification = directory / "qualification.json"
        runner.save(
            qualification, dict(sources=[dict(path="historical/relative", sha256="a" * 64)])
        )
        source.update(
            primitive_qualification=runner.ref(qualification),
            repository=dict(head="original", dirty=False),
        )
        # Historical synthetic snapshots use placeholder source paths; replace
        # them with real fixture references before building the raw evidence graph.
        for item in source["seeds"].values():
            path = Path(item["snapshot"]["path"])
            seed = runner.read(path)
            seed["sources"] = {
                target: {kind: source["targets"][target] for kind in ("input", "wout")}
                for target in ("reference", "selected")
            }
            runner.save(path, seed)
            item["snapshot"] = {k: v for k, v in runner.ref(path).items() if k != "bytes"}
        monkeypatch.setattr(runner, "candidate_certificate", mock_certificate)
        raw, registry, rows, workers = directory / "raw", None, [], []
        for i, case in enumerate(audit.matrix()):
            output = worker_config(raw, source, i, registry)
            assert runner.worker(output / "config.json") == 0
            worker = runner.read(output / "worker.json")
            config = runner.read(output / "config.json")
            workers.append(worker)
            registry = worker["surface_registry"]
            runner.save(
                output / "launch.json",
                dict(
                    command=[
                        sys.executable,
                        str(audit.ROOT / "scripts/run_coil_perturbation.py"),
                        "--worker",
                        str(output / "config.json"),
                    ],
                    case=case,
                    started_monotonic=config["started_monotonic"],
                ),
            )
            runner.save(
                output / "process.json",
                dict(
                    returncode=0,
                    timed_out=False,
                    elapsed_seconds=time.monotonic() - config["started_monotonic"],
                    minimum_observed_free_bytes=4 * audit.GIB,
                ),
            )
            result = dict(
                index=i,
                case=case,
                status="completed",
                config=runner.ref(output / "config.json"),
                launch=runner.ref(output / "launch.json"),
                process=runner.ref(output / "process.json"),
                worker=runner.ref(output / "worker.json"),
                retained=[runner.ref(p) for p in sorted(output.rglob("*")) if p.is_file()],
            )
            runner.save(output / "result.json", result)
            rows.append(runner.ref(output / "result.json"))
        document = dict(
            schema_version=1,
            kind="coil-perturbation",
            status="completed",
            source_before=source,
            source_after=copy.deepcopy(source),
            source_unchanged=True,
            producer_complete=True,
            matrix=audit.matrix(),
            rows=rows,
            surface_registry=registry,
            fixed_surfaces=workers[0]["fixed_surfaces"],
            retained_surfaces=[
                runner.ref(p) for p in sorted((raw / "surfaces").rglob("*")) if p.is_file()
            ],
            limits=audit.LIMITS,
            admission_status="pending-independent-audit",
            **audit.SCOPE,
            **audit.PENDING,
        )
        runner.save(raw / "checkpoint.json", dict(rows=rows))
        document["checkpoint"] = runner.ref(raw / "checkpoint.json")
        runner.save(raw / "run.json", document)
        yield dict(path=raw / "run.json", run=document, source=source, workers=workers)


@pytest.fixture
def configured(monkeypatch, saved):
    monkeypatch.setattr(audit, "sources", lambda root: copy.deepcopy(saved["source"]))
    monkeypatch.setattr(audit.mathematical, "independent_certificate", mock_certificate)
    monkeypatch.setattr(audit.direct, "audit_samples", mock_direct)
    monkeypatch.setattr(
        audit.geometry,
        "surface",
        lambda *a, **kw: dict(points=np.tile([1.0, 0.0, 0.0], (256**2, 1))),
    )
    return saved


def test_full_two_worker_actual_producer_persistence_to_independent_audit(configured):
    result = audit.audit(configured["path"])
    assert result["all_pass"] and result["qualification_pass"]
    assert result["independent_audit_pass"] and result["arithmetic_and_source_pass"]
    assert len(result["cells"]) == 2
    assert all(len(c["states"]) == 26 for c in result["cells"])
    assert any(not r["certified"] for c in result["cells"] for r in c["states"])
    assert result["independent_work"]["direct_grids"] == 208
    assert result["independent_work"]["surface_reconstructions"] == 2
    assert not any(
        result[k] for k in ("field_pass", "search_allowed", "transfer_pass", "step4_pass")
    )


def test_only_current_outer_repository_metadata_may_differ(configured, monkeypatch):
    current = copy.deepcopy(configured["source"])
    current["repository"] = dict(head="later-documentation-commit", dirty=True)
    monkeypatch.setattr(audit, "sources", lambda root: current)
    result = audit.audit(configured["path"])
    assert result["all_pass"] and result["source"]["repository"] != current["repository"]
    assert result["auditor_repository"] == current["repository"]
    current["targets"]["reference"]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        audit.audit(configured["path"])


def context(configured):
    ev = audit.Evidence(opaque_json=[configured["source"]["primitive_qualification"]])
    run = configured["run"]
    result = ev.read(run["rows"][0])
    surfaces, records = audit.surface_audit(ev, run, configured["source"])
    return ev, result, surfaces, records


@pytest.mark.parametrize(
    "mutation",
    [
        "return_bool",
        "return_nonzero",
        "timeout",
        "wall",
        "elapsed",
        "threads",
        "scope",
        "free",
        "start_free",
        "start_clock",
        "command",
        "missing_state",
    ],
)
def test_process_and_complete_work_are_fail_closed(configured, mutation):
    ev, result, surfaces, records = context(configured)
    process, config, worker, launch = [
        ev.read(result[k]) for k in ("process", "config", "worker", "launch")
    ]
    if mutation == "return_bool":
        process["returncode"] = False
    elif mutation == "return_nonzero":
        process["returncode"] = 7
    elif mutation == "timeout":
        process["timed_out"] = True
    elif mutation == "wall":
        process["elapsed_seconds"] = 1800.0
    elif mutation == "elapsed":
        worker["elapsed_seconds"] += 0.1
    elif mutation == "threads":
        worker["threads"]["OMP_NUM_THREADS"] = "2"
    elif mutation == "scope":
        worker["scope"]["field_calls"] = 1
    elif mutation == "free":
        worker["minimum_observed_free_bytes"] = audit.GIB
    elif mutation == "start_free":
        config["start_space"]["free_bytes"] = 2 * audit.GIB
    elif mutation == "start_clock":
        worker["started_monotonic"] += 1
    elif mutation == "command":
        launch["command"][1] = "/unbound/producer.py"
    else:
        worker["states"].pop()
    with pytest.raises(ValueError):
        audit.cell_audit(
            ev,
            result,
            audit.matrix()[0],
            configured["source"],
            configured["run"],
            surfaces,
            records,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "attempt_prefix",
        "sampling_reservation",
        "sampling_prefix",
        "state_radius",
        "original_seed",
        "extra_attempt",
        "repeat",
        "operation_clock",
        "state_clock",
        "operation_order",
    ],
)
def test_every_ledger_prefix_and_deterministic_state_is_checked(configured, mutation):
    ev, result, surfaces, records = context(configured)
    worker = ev.read(result["worker"])
    state = ev.read(worker["states"][1])
    operation = ev.read(state["direct"][0])
    if mutation == "attempt_prefix":
        ev.read(operation["attempt"])["work_before"]["certificates"]["completed"] += 1
    elif mutation == "sampling_reservation":
        ev.read(operation["attempt"])["sampling_reservation"]["cp"]["points_attempted"] -= 1
    elif mutation == "sampling_prefix":
        operation["sampling_work_after"]["cc"]["completed"] -= 1
    elif mutation == "state_radius":
        state["radius"] = 0.05
    elif mutation == "original_seed":
        state["seed_snapshot"] = state["candidate"]
    elif mutation == "extra_attempt":
        worker["operation_attempts"].append(worker["operation_attempts"][-1])
    elif mutation == "repeat":
        state["repeat_exact"] = False
    elif mutation == "operation_clock":
        operation["ended_monotonic"] = worker["ended_monotonic"] + 1
    elif mutation == "state_clock":
        state["ended_monotonic"] = state["started_monotonic"]
    else:
        worker["operations"][0], worker["operations"][1] = (
            worker["operations"][1],
            worker["operations"][0],
        )
    with pytest.raises(ValueError):
        audit.cell_audit(
            ev,
            result,
            audit.matrix()[0],
            configured["source"],
            configured["run"],
            surfaces,
            records,
        )


def test_fresh_cli_output_and_retained_failure(configured, monkeypatch, tmp_path):
    output = tmp_path / "audit.json"
    monkeypatch.setattr(
        sys, "argv", ["audit", "--run", str(configured["path"]), "--output", str(output)]
    )
    assert audit.main() == 0
    assert json.loads(output.read_text())["all_pass"]
    original = output.read_bytes()
    with pytest.raises(ValueError):
        audit.main()
    assert output.read_bytes() == original
    failed = tmp_path / "failed.json"
    monkeypatch.setattr(
        sys, "argv", ["audit", "--run", str(configured["path"]), "--output", str(failed)]
    )
    monkeypatch.setattr(
        audit, "audit", lambda path: (_ for _ in ()).throw(ValueError("synthetic corruption"))
    )
    assert audit.main() == 1
    assert json.loads(failed.read_text())["status"] == "error"


def test_independent_hash_binding_and_dtype_preservation(tmp_path):
    path = tmp_path / "arrays.npz"
    ref = runner.storage.arrays(path, dict(mask=np.array([True]), index=np.array([1], dtype=int)))
    arrays = audit.Evidence().array(ref)
    assert arrays["mask"].dtype.kind == "b" and arrays["index"].dtype.kind in "iu"
    path.write_bytes(b"changed synthetic evidence")
    with pytest.raises(ValueError):
        audit.Evidence().array(ref)


@pytest.mark.parametrize("index", [0, 1, 2, 9, 10, 17, 18, 25])
def test_every_seed_and_signed_smallest_probe_is_required(index):
    rows = [dict(row, certified=True) for row in audit.direct.plan()]
    assert audit.required_certification(rows)
    rows[3]["certified"] = False
    assert audit.required_certification(rows)
    rows[index]["certified"] = False
    assert not audit.required_certification(rows)


@pytest.mark.parametrize("mutation", ["plan", "checkpoint", "schema_bool", "state_index_bool"])
def test_saved_plan_checkpoint_and_boolean_aliases_fail_closed(configured, mutation):
    ev, result, surfaces, records = context(configured)
    worker = ev.read(result["worker"])
    directory = Path(result["worker"]["path"]).parent
    if mutation in ("plan", "checkpoint"):
        filename = "plan.json" if mutation == "plan" else "checkpoint.json"
        ref = next(r for r in result["retained"] if r["path"] == str(directory / filename))
        document = ev.read(ref)
        if mutation == "plan":
            document["levels"].pop()
        else:
            document["states"].pop()
    elif mutation == "schema_bool":
        worker["schema_version"] = True
    else:
        ev.read(worker["states"][0])["index"] = False
    with pytest.raises(ValueError):
        audit.cell_audit(
            ev,
            result,
            audit.matrix()[0],
            configured["source"],
            configured["run"],
            surfaces,
            records,
        )


def test_strict_cp_enclosures_use_independent_not_merely_close_producer_surface(
    configured, monkeypatch
):
    independent = np.tile([1.0 + 5e-13, 0.0, 0.0], (256**2, 1))
    monkeypatch.setattr(audit.geometry, "surface", lambda *a, **kw: dict(points=independent))
    ev = audit.Evidence(opaque_json=[configured["source"]["primitive_qualification"]])
    surfaces, records = audit.surface_audit(ev, configured["run"], configured["source"])
    for target in audit.direct.TARGETS:
        assert np.array_equal(surfaces[target], independent)
        assert not np.array_equal(surfaces[target], ev.array(records[target]["arrays"])["points"])


@pytest.mark.parametrize("temporary", [False, True])
def test_cli_refuses_broken_output_or_temporary_symlinks(
    configured, monkeypatch, tmp_path, temporary
):
    output = tmp_path / "audit.json"
    link = output.with_suffix(".json.tmp") if temporary else output
    link.symlink_to(tmp_path / "absent")
    monkeypatch.setattr(
        sys, "argv", ["audit", "--run", str(configured["path"]), "--output", str(output)]
    )
    with pytest.raises(ValueError):
        audit.main()
    assert link.is_symlink() and not (tmp_path / "absent").exists()


@pytest.mark.parametrize(
    "mutation", ["missing", "mutable", "old_state", "wrong_attempt", "live_wrong"]
)
def test_immutable_checkpoint_marker_is_bound_separately_from_live_marker(configured, mutation):
    ev, result, surfaces, records = context(configured)
    worker = ev.read(result["worker"])
    directory = Path(result["worker"]["path"]).parent
    checkpoint_ref = next(
        r for r in result["retained"] if r["path"] == str(directory / "checkpoint.json")
    )
    checkpoint = ev.read(checkpoint_ref)
    if mutation == "missing":
        checkpoint.pop("inflight")
    elif mutation == "mutable":
        checkpoint["inflight"] = worker["inflight"]
    elif mutation == "old_state":
        checkpoint["inflight"] = next(
            r
            for r in result["retained"]
            if r["path"] == str(directory / "state-00/checkpoint-inflight.json")
        )
    elif mutation == "wrong_attempt":
        ev.read(checkpoint["inflight"])["attempt"] = worker["operation_attempts"][0]
    else:
        ev.read(worker["inflight"])["attempt"] = worker["operation_attempts"][0]
    with pytest.raises((ValueError, KeyError)):
        audit.cell_audit(
            ev,
            result,
            audit.matrix()[0],
            configured["source"],
            configured["run"],
            surfaces,
            records,
        )


@pytest.mark.parametrize("failure", [OSError("synthetic IO"), TimeoutError("synthetic timeout")])
def test_failed_next_state_preserves_transitively_hash_valid_checkpoint(
    configured, monkeypatch, tmp_path, failure
):
    source = configured["source"]
    monkeypatch.setattr(runner, "sources", lambda root: copy.deepcopy(source))
    output = worker_config(tmp_path / "failed-prefix", source)
    calls, previous_bytes = 0, None

    def fail_after_first(seed, report, coefficients):
        nonlocal calls, previous_bytes
        calls += 1
        if calls == 3:
            previous_bytes = (output / "checkpoint.json").read_bytes()
            raise failure
        return mock_certificate(seed, report, coefficients)

    monkeypatch.setattr(runner, "candidate_certificate", fail_after_first)
    assert runner.worker(output / "config.json") == 1
    assert (
        previous_bytes is not None and (output / "checkpoint.json").read_bytes() == previous_bytes
    )
    checkpoint = runner.read(output / "checkpoint.json")
    evidence = audit.Evidence(opaque_json=[source["primitive_qualification"]])
    evidence.bind(checkpoint)
    assert len(checkpoint["states"]) == 1
    assert checkpoint["inflight"]["path"] == str(output / "state-00/checkpoint-inflight.json")
    stable = evidence.read(checkpoint["inflight"])
    live = runner.read(output / "inflight.json")
    assert stable == dict(attempt=checkpoint["operation_attempts"][-1])
    assert stable != live
    assert evidence.references
