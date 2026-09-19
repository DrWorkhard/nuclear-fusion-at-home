"""Full-dimensional synthetic saved-data workflow, never a native/target evaluation.

The smooth artificial objective deliberately tests the admission machinery, not
the native CP formula. Native formula equivalence has separate registered tests.
"""

import copy
import hashlib
import json
from pathlib import Path

import audit_block_native_reference as audit
import numpy as np
import pytest


def reference(path):
    return dict(
        path=str(path),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        bytes=path.stat().st_size,
    )


def save(path, value):
    path.write_text(json.dumps(value, allow_nan=False, sort_keys=True))
    return reference(path)


def arrays(path, value):
    np.savez_compressed(path, **value)
    return reference(path)


def geometry(x, case):
    n, m, q = case["nbase"], case["order"], case["ncoil"]
    coefficients = x.reshape(n, 3, 2 * m + 1)
    u = np.arange(q) / q
    positions, derivatives = [], []
    for c in coefficients:
        p = np.broadcast_to(c[:, 0], (q, 3)).copy()
        t = np.zeros_like(p)
        for mode in range(1, m + 1):
            angle = 2 * np.pi * mode * u[:, None]
            p += np.sin(angle) * c[:, 2 * mode - 1] + np.cos(angle) * c[:, 2 * mode]
            t += (
                2
                * np.pi
                * mode
                * (np.cos(angle) * c[:, 2 * mode - 1] - np.sin(angle) * c[:, 2 * mode])
            )
        positions.append(p)
        derivatives.append(t)
    result = dict(gamma=[], gammadash=[])
    for period in range(2):
        angle = np.pi * period
        rotation = np.array(
            [[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]]
        )
        for flip in (False, True):
            for p, t in zip(positions, derivatives, strict=True):
                reflection = np.diag([1.0, -1.0, -1.0]) if flip else np.eye(3)
                result["gamma"].append(p @ (reflection @ rotation).T)
                result["gammadash"].append(t @ (reflection @ rotation).T)
    return {k: np.array(v) for k, v in result.items()}


def seed(case):
    n, m = case["nbase"], case["order"]
    result = np.zeros((n, 3, 2 * m + 1))
    phi = (np.arange(n) + 0.5) * np.pi / (2 * n)
    result[:, 0, 0], result[:, 1, 0] = 0.3 * np.cos(phi), 0.3 * np.sin(phi)
    result[:, 0, 2], result[:, 1, 2] = 0.28 * np.cos(phi), 0.28 * np.sin(phi)
    result[:, 2, 1] = -0.28
    return result.ravel()


def surface():
    p, t = np.meshgrid(
        np.arange(128) * 2 * np.pi / 128, np.arange(128) * 2 * np.pi / 128, indexing="ij"
    )
    radius = 0.3 + 0.25 * np.cos(t)
    points = np.stack((radius * np.cos(p), radius * np.sin(p), 0.25 * np.sin(t)), axis=-1)
    normals = (
        (2 * np.pi) ** 2
        * radius[..., None]
        * 0.25
        * np.stack((np.cos(t) * np.cos(p), np.cos(t) * np.sin(p), np.sin(t)), axis=-1)
    )
    return dict(points=points.reshape(-1, 3), normals=normals.reshape(-1, 3))


def make_worker(directory, case, source, index, *, legacy=False):
    directory.mkdir()
    start = float(100 + 200 * index)
    metadata = save(directory / "metadata.json", audit.original_metadata(case))
    surf = arrays(directory / "surface.npz", surface())
    config = save(
        directory / "config.json",
        dict(
            output=str(directory), case=case, source=source, started_monotonic=start, parent_pid=123
        ),
    )
    launch = save(
        directory / "launch.json",
        dict(
            case=case,
            started_monotonic=start,
            command=["python", "synthetic-fixture.py", "--worker", config["path"]],
        ),
    )
    process = save(
        directory / "process.json",
        dict(
            returncode=0,
            timed_out=False,
            elapsed_seconds=16.0,
            minimum_observed_free_bytes=3 * 1024**3,
        ),
    )
    model = dict(metadata=metadata, surface=surf)
    if not legacy:
        model.update(
            block_size=256, blocks=64, block_weight=1 / 64, kernel_work=audit.zero_kernels()
        )
    model = save(directory / "model.json", model)
    rows, attempts, events = [], [], []
    work, kernels = audit.zero_work(), audit.zero_kernels()
    for i, state in enumerate(audit.state_plan(seed(case))):
        attempt = dict(
            index=i,
            label=state["label"],
            gradient=state["gradient"],
            started_monotonic=start + i + 0.1,
            work_before=copy.deepcopy(work),
        )
        if not legacy:
            attempt.update(
                kernel_work_before=copy.deepcopy(kernels), kernel_progress_events_before=len(events)
            )
        attempt_ref = save(directory / f"attempt-{i:02d}.json", attempt)
        attempts.append(attempt_ref)
        x = state["x"]
        raw, metrics = dict(x=x, **geometry(x, case)), {}
        minimum = i in (0, 10, 12)
        for name, factor in (("cp", 0.001), ("cc", 0.002)):
            metrics[name] = dict(J=float(0.01 + factor * (x @ x)))
            work[name]["J_calls"] += 1
            if state["gradient"]:
                raw[name + "_gradient"] = 2 * factor * x
                work[name]["dJ_calls"] += 1
                work[name]["named_local_extractions"] += case["nbase"]
                work[name]["requested_physical_curve_vjp_pairs"] += 4 * case["nbase"]
            if minimum:
                metrics[name]["shortest_distance"] = 0.012
                work[name]["shortest_distance_calls"] += 1
        if not legacy:
            phases = (
                ["J"] + (["dJ"] if state["gradient"] else []) + (["minimum"] if minimum else [])
            )
            groups = len(phases) * 4 * case["nbase"]
            cursor = 0
            for phase in phases:
                reservation = dict.fromkeys(audit.KERNELS, 0)
                if phase == "dJ":
                    reservation.update(position=64, tangent=64, position_vjp=1, tangent_vjp=1)
                else:
                    reservation[phase] = 64
                for curve in range(4 * case["nbase"]):
                    upper = {
                        q: {
                            kind: kernels[q][kind] + reservation[q]
                            for kind in ("attempted", "completed")
                        }
                        for q in audit.KERNELS
                    }
                    group = len(events) // 2
                    for status in ("reserved", "completed"):
                        event = dict(
                            index=group,
                            curve_index=curve,
                            phase=phase,
                            status=status,
                            reservation=reservation.copy(),
                            work_before=copy.deepcopy(kernels),
                            work=copy.deepcopy(kernels if status == "reserved" else upper),
                            upper_work=copy.deepcopy(upper),
                        )
                        events.append(
                            dict(
                                state_index=i,
                                state_label=state["label"],
                                event=event,
                                monotonic=start + i + 0.2 + 0.6 * cursor / (2 * groups),
                            )
                        )
                        cursor += 1
                    kernels = upper
        row = dict(
            index=i,
            label=state["label"],
            gradient=state["gradient"],
            metrics=metrics,
            arrays=arrays(directory / f"raw-{i:02d}.npz", raw),
            work=copy.deepcopy(work),
            ended_monotonic=start + i + 0.9,
        )
        if not legacy:
            row.update(
                attempt=attempt_ref,
                kernel_work=copy.deepcopy(kernels),
                kernel_progress_events=len(events),
            )
        rows.append(save(directory / f"raw-{i:02d}.json", row))
    checkpoint = dict(rows=rows, work=work)
    if not legacy:
        checkpoint.update(kernel_work=kernels, kernel_progress_events=len(events))
    save(directory / "checkpoint.json", checkpoint)
    save(
        directory / "work-inflight.json",
        dict(
            index=12,
            label="restored-seed",
            attempted_calls=work,
            partial_failure_accounting="attempts, not successful returns",
        ),
    )
    rss = (
        audit.RSS_LIMIT + 1024
        if case["label"] in {"n6-q512-native", "n8-q256-native", "n8-q512-native"}
        else audit.RSS_LIMIT - 1024
    )
    worker = dict(
        schema_version=1,
        status="completed",
        case=case,
        source_before=source,
        source_after=source,
        metadata=metadata,
        surface=surf,
        rows=rows,
        work=work,
        elapsed_seconds=14.5,
        ended_monotonic=start + 15.0,
        peak_rss_bytes=rss,
        rss_pass=rss <= audit.RSS_LIMIT,
        scope=audit.OLD_SCOPE if legacy else audit.SCOPE,
        threads=audit.THREADS,
    )
    if not legacy:
        path = directory / "kernel-progress.jsonl"
        path.write_text("".join(json.dumps(event, allow_nan=False) + "\n" for event in events))
        worker.update(
            attempts=attempts,
            model=model,
            kernel_work=kernels,
            kernel_progress=reference(path),
            kernel_progress_events=len(events),
            kernel_inflight=save(directory / "kernel-inflight.json", events[-1]),
        )
    worker_ref = save(directory / "worker.json", worker)
    result = dict(
        index=index,
        case=case,
        status="completed",
        worker=worker_ref,
        process=process,
        config=config,
        launch=launch,
        peak_rss_bytes=rss,
        resource_pass=rss <= audit.RSS_LIMIT,
        retained=[reference(path) for path in sorted(directory.iterdir())],
    )
    return save(directory / "result.json", result), worker_ref


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    directory = tmp_path_factory.mktemp("block-native-independent-fullshape")
    legacy_source = dict(kind="synthetic-independent-auditor-test", no_native_evaluation=True)
    old_rows, old_workers = [], {}
    for i, case in enumerate(audit.matrix(True)):
        row, worker = make_worker(directory / case["label"], case, legacy_source, i, legacy=True)
        old_rows.append(row)
        old_workers[case["label"]] = worker
    old = dict(
        status="completed",
        all_pass=False,
        source_before=legacy_source,
        source_after=legacy_source,
        source_unchanged=True,
        scope=audit.OLD_SCOPE,
        matrix=audit.matrix(True),
        rows=old_rows,
    )
    binding = dict(
        old_reference=save(directory / "legacy-run.json", old),
        old_workers=old_workers,
        legacy_source=legacy_source,
        matrix=audit.matrix(),
        repository=dict(
            path=str(directory), available=True, commit="1" * 40, branch="test", dirty=False
        ),
        numerical_test_pin="unchanged",
    )
    rows = [
        make_worker(directory / case["label"], case, binding, i)[0]
        for i, case in enumerate(audit.matrix())
    ]
    run = dict(
        schema_version=1,
        kind="block-native-reference-qualification",
        status="completed",
        source_before=binding,
        source_after=copy.deepcopy(binding),
        source_unchanged=True,
        scope=audit.SCOPE,
        matrix=audit.matrix(),
        rows=rows,
        old_reference=binding["old_reference"],
        producer_checks_pass=True,
        bounded_reference_pass=False,
        all_pass=False,
        independent_audit_pass=False,
        admission_status="pending-independent-audit",
        limits=dict(
            wall_seconds=120.0,
            peak_rss_bytes=audit.RSS_LIMIT,
            parent_poll_seconds=0.5,
            termination_grace_seconds=5,
        ),
    )
    run_ref = save(directory / "run.json", run)
    return run, binding, run_ref


def test_full_four_worker_saved_data_admission(fixture, monkeypatch):
    run, binding, _ = fixture
    monkeypatch.setattr(audit, "sources", lambda root: copy.deepcopy(binding))
    result = audit.audit(run)
    assert result["bounded_reference_pass"] is True
    assert result["arithmetic_and_source_pass"] is True
    assert result["legacy_all_pass"] is False
    assert result["legacy_sparse_pass"] is True
    assert result["compared_quantities"] == 336
    assert sum(len(r["finite_differences"]) for r in result["workers"]) == 32
    assert sum(len(r["comparisons"]) for r in result["legacy_pairs"]) == 168
    for report in result["workers"]:
        n = report["case"]["nbase"]
        assert report["state_count"] == 13
        expected = dict(
            J=13 * 4 * n * 64,
            position=5 * 4 * n * 64,
            tangent=5 * 4 * n * 64,
            minimum=3 * 4 * n * 64,
            position_vjp=5 * 4 * n,
            tangent_vjp=5 * 4 * n,
        )
        assert report["kernels"]["kernel_work"] == {
            k: dict(attempted=v, completed=v) for k, v in expected.items()
        }
    assert all(
        result[k] is False
        for k in (
            "startup_pass",
            "physical_seed_pass",
            "search_allowed",
            "transfer_pass",
            "step4_pass",
        )
    )
    assert json.loads(json.dumps(result, allow_nan=False)) == result


def test_cli_fresh_serializable_independent_output(fixture, monkeypatch, tmp_path):
    run, binding, run_ref = fixture
    output = tmp_path / "audit.json"
    monkeypatch.setattr(audit, "sources", lambda root: copy.deepcopy(binding))
    monkeypatch.setattr("sys.argv", ["audit", "--run", run_ref["path"], "--output", str(output)])
    assert audit.main() == 0
    assert json.loads(output.read_text())["bounded_reference_pass"] is True
    assert json.loads(Path(run_ref["path"]).read_text()) == run
    with pytest.raises(ValueError, match="fresh output"):
        audit.main()


def test_only_root_repository_bookkeeping_can_change(fixture, monkeypatch):
    run, binding, _ = fixture
    current = copy.deepcopy(binding)
    current["repository"].update(commit="2" * 40, dirty=True, branch="results-documentation")
    monkeypatch.setattr(audit, "sources", lambda root: current)
    result = audit.audit(run)
    assert result["bounded_reference_pass"] is True
    assert result["source"] == binding
    assert result["auditor_repository"] == current["repository"]
    current["numerical_test_pin"] = "changed"
    with pytest.raises(ValueError, match="numerical sources"):
        audit.audit(run)


def test_changed_numerical_source_hash_and_inrun_repository_rejected(fixture, monkeypatch):
    run, binding, _ = fixture
    current = copy.deepcopy(binding)
    current["old_reference"]["sha256"] = "0" * 64
    monkeypatch.setattr(audit, "sources", lambda root: current)
    with pytest.raises(ValueError, match="evidence hash"):
        audit.audit(run)
    monkeypatch.setattr(audit, "sources", lambda root: binding)
    changed = copy.deepcopy(run)
    changed["source_after"]["repository"]["dirty"] = True
    with pytest.raises(ValueError, match="entire follow-up"):
        audit.audit(changed)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_unchanged", False),
        ("schema_version", True),
        ("all_pass", True),
        ("bounded_reference_pass", True),
        ("independent_audit_pass", True),
        ("producer_checks_pass", 1),
        ("rows", []),
        ("matrix", []),
    ],
)
def test_top_level_mutations_fail_closed(fixture, monkeypatch, key, value):
    run, binding, _ = fixture
    monkeypatch.setattr(audit, "sources", lambda root: binding)
    changed = copy.deepcopy(run)
    changed[key] = value
    with pytest.raises((ValueError, KeyError)):
        audit.audit(changed)


@pytest.mark.parametrize("value", [True, 0, None])
def test_physical_scope_flags_require_literal_false(fixture, monkeypatch, value):
    run, binding, _ = fixture
    monkeypatch.setattr(audit, "sources", lambda root: binding)
    changed = copy.deepcopy(run)
    changed["scope"]["startup_pass"] = value
    with pytest.raises(ValueError, match="admission"):
        audit.audit(changed)


def worker_fixture(fixture):
    run, binding, _ = fixture
    evidence = audit.Evidence()
    result = evidence.read(run["rows"][0])
    worker = evidence.read(result["worker"])
    return result, worker, binding, evidence


def overlay(evidence, ref):
    """Semantic mutations after hash loading; raw provenance has separate controls."""
    value = copy.deepcopy(evidence.read(ref))
    evidence.documents[ref["path"]] = value
    return value


@pytest.mark.parametrize(
    "target,key,value",
    [
        ("process", "returncode", False),
        ("process", "returncode", 1),
        ("process", "timed_out", True),
        ("process", "elapsed_seconds", 120.0),
        ("process", "minimum_observed_free_bytes", 1),
        ("worker", "elapsed_seconds", float("nan")),
        ("worker", "ended_monotonic", 5000.0),
        ("worker", "peak_rss_bytes", True),
        ("worker", "rss_pass", 1),
        ("worker", "rows", []),
        ("worker", "kernel_progress_events", 0),
        ("worker", "kernel_progress_events", True),
    ],
)
def test_process_and_complete_worker_guards(fixture, target, key, value):
    result, worker, binding, evidence = worker_fixture(fixture)
    changed = overlay(evidence, result[target])
    changed[key] = value
    with pytest.raises((ValueError, KeyError)):
        audit.worker_audit(result, result["case"], binding, evidence)


@pytest.mark.parametrize(
    "key,value",
    [
        ("index", True),
        ("label", "wrong"),
        ("gradient", 1),
        ("kernel_progress_events_before", 1),
        ("kernel_progress_events_before", False),
        ("started_monotonic", 0.0),
    ],
)
def test_attempt_mutations_fail_closed(fixture, key, value):
    result, worker, binding, evidence = worker_fixture(fixture)
    attempt = overlay(evidence, worker["attempts"][0])
    attempt[key] = value
    with pytest.raises(ValueError):
        audit.worker_audit(result, result["case"], binding, evidence)


@pytest.mark.parametrize("key", ["native_local_names", "physical", "names", "surface_shape"])
def test_geometry_metadata_is_not_trusted(fixture, key):
    result, worker, binding, evidence = worker_fixture(fixture)
    overlay(evidence, worker["metadata"])[key] = []
    with pytest.raises(ValueError, match="metadata"):
        audit.worker_audit(result, result["case"], binding, evidence)


@pytest.mark.parametrize("key", ["gamma", "gammadash", "x"])
def test_raw_actual_geometry_and_names_reconstructed(fixture, key):
    result, worker, binding, evidence = worker_fixture(fixture)
    row = evidence.read(worker["rows"][0])
    raw = {k: v.copy() for k, v in evidence.array(row["arrays"]).items()}
    raw[key].flat[0] += 1e-5
    evidence.arrays[row["arrays"]["path"]] = raw
    with pytest.raises(ValueError):
        audit.worker_audit(result, result["case"], binding, evidence)


def test_negative_fd_and_repeat_cannot_become_admission(fixture):
    result, worker, binding, evidence = worker_fixture(fixture)
    row = evidence.read(worker["rows"][0])
    raw = {k: v.copy() for k, v in evidence.array(row["arrays"]).items()}
    raw["cp_gradient"] += 0.1
    evidence.arrays[row["arrays"]["path"]] = raw
    checked = audit.worker_audit(result, result["case"], binding, evidence)
    assert checked["report"]["mathematical_pass"] is False
    assert not all(checked["report"]["repetitions"])
    assert not all(x["passed"] for x in checked["report"]["finite_differences"])


def test_restored_minimum_requires_exact_repeat_not_backend_tolerance(fixture):
    result, worker, binding, evidence = worker_fixture(fixture)
    row = overlay(evidence, worker["rows"][12])
    row["metrics"]["cp"]["shortest_distance"] += 1e-14
    checked = audit.worker_audit(result, result["case"], binding, evidence)
    assert checked["report"]["repetitions"] == [True, True, False]
    assert checked["report"]["mathematical_pass"] is False


def test_backend_comparisons_check_every_component(fixture):
    result, worker, binding, evidence = worker_fixture(fixture)
    first = audit.worker_audit(result, result["case"], binding, evidence)
    second = copy.deepcopy(first)
    second["arrays"][12]["cc_gradient"][-1] += 1e-6
    comparison = audit.pair_audit(first, second)
    assert len(comparison["comparisons"]) == 42
    assert sum(not row["passed"] for row in comparison["comparisons"]) == 1
    assert comparison["passed"] is False


def test_new_rss_failure_is_not_a_legacy_waiver(fixture):
    result, worker, binding, evidence = worker_fixture(fixture)
    worker = overlay(evidence, result["worker"])
    worker.update(peak_rss_bytes=audit.RSS_LIMIT + 1, rss_pass=False)
    result = dict(result, peak_rss_bytes=audit.RSS_LIMIT + 1, resource_pass=False)
    checked = audit.worker_audit(result, result["case"], binding, evidence)
    assert checked["report"]["mathematical_pass"] is True
    assert checked["report"]["passed"] is False


@pytest.mark.parametrize(
    "kind",
    [
        "event_index",
        "wrong_curve",
        "status",
        "reservation",
        "partial",
        "time_backward",
        "time_outside",
        "state_index",
        "prefix",
        "missing",
    ],
)
def test_kernel_history_mutations_fail_closed(fixture, tmp_path, kind):
    result, worker, binding, evidence = worker_fixture(fixture)
    worker = overlay(evidence, result["worker"])
    events = [
        json.loads(line)
        for line in Path(worker["kernel_progress"]["path"]).read_text().splitlines()
    ]
    event = events[1]["event"]
    if kind == "event_index":
        event["index"] = 1
    elif kind == "wrong_curve":
        event["curve_index"] = True
    elif kind == "status":
        event["status"] = "error"
    elif kind == "reservation":
        event["reservation"].pop("tangent")
    elif kind == "partial":
        event["work"]["J"]["completed"] -= 1
    elif kind == "time_backward":
        events[1]["monotonic"] = events[0]["monotonic"] - 1e-3
    elif kind == "time_outside":
        events[1]["monotonic"] += 1000
    elif kind == "state_index":
        events[1]["state_index"] = True
    elif kind == "prefix":
        overlay(evidence, worker["rows"][0])["kernel_progress_events"] -= 2
    elif kind == "missing":
        events.pop()
    path = tmp_path / "mutated-progress.jsonl"
    path.write_text("".join(json.dumps(e) + "\n" for e in events))
    worker["kernel_progress"] = reference(path)
    with pytest.raises(ValueError):
        audit.worker_audit(result, result["case"], binding, evidence)


@pytest.mark.parametrize("mutation", ["hash", "bytes", "missing_bytes", "relative", "alias"])
def test_immutable_reference_controls(tmp_path, mutation):
    path = tmp_path / "test.json"
    ref = save(path, {"value": 1})
    evidence = audit.Evidence()
    if mutation == "hash":
        ref["sha256"] = "0" * 64
    elif mutation == "bytes":
        ref["bytes"] += 1
    elif mutation == "missing_bytes":
        ref.pop("bytes")
    elif mutation == "relative":
        ref["path"] = "test.json"
    elif mutation == "alias":
        evidence.bind(ref)
        ref["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        evidence.bind(ref)


@pytest.mark.parametrize(
    "value", [np.array([1j]), np.array(["1"]), np.array([True]), np.array([np.inf])]
)
def test_nonfinite_complex_string_or_bool_arrays_rejected(value):
    with pytest.raises(ValueError):
        audit.finite(value)


def test_registered_case_and_state_counts():
    assert len(audit.matrix()) == 4 and len(audit.matrix(True)) == 8
    states = audit.state_plan(seed(audit.matrix()[0]))
    assert [s["label"] for s in states] == [
        "seed",
        "sin-1e-05-+1",
        "sin-1e-05--1",
        "sin-5e-06-+1",
        "sin-5e-06--1",
        "cos-1e-05-+1",
        "cos-1e-05--1",
        "cos-5e-06-+1",
        "cos-5e-06--1",
        "seed-repeat",
        "changed-base",
        "changed-repeat",
        "restored-seed",
    ]
    assert sum(s["gradient"] for s in states) == 5
