"""Synthetic input, publication, deadline and source-gate tests; no real bounds."""

import copy
import hashlib
import json
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_local_curvature as run  # noqa: E402


class Clock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now


def save(tmp_path, name, document):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(run.encode(document))
    return run.reference(path)


def bound_result(passed=True, reason="complete"):
    return dict(
        schema_version=1,
        kind="local-homotopy-curvature",
        caps=dict(run.CAPS),
        nodes=[["", "pass" if passed else "depth", 1.0, 5.0 if passed else 13.0, 0.0, 0.0]],
        attempted=1,
        curvature_pass=passed,
        stop_reason=reason,
        interval_arithmetic=False,
        field_pass=False,
        step4_pass=False,
    )


def phase_data(copies=3, old_curvature=True):
    matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    coeff = [[0.0, 0.0, 0.2], [0.0, 0.2, 0.0], [0.0, 0.0, 0.0]]
    gates = {key: key != "curvature" or old_curvature for key in run.GATES}
    return dict(
        row=dict(label="synthetic", state_sha256="a" * 64),
        seed=dict(
            base_coefficients=[coeff],
            physical=[
                dict(base_index=0, matrix=copy.deepcopy(matrix), period=i, flip=False)
                for i in range(copies)
            ],
        ),
        candidate=[copy.deepcopy(coeff)],
        geometry={},
        old_proof=dict(result=dict(gates=gates, certified=old_curvature)),
    )


def old(data, phase):
    return copy.deepcopy(data["old_proof"]["result"])


def produce(data, physical, phase, recorded, deadline, clock):
    assert phase == "producer"
    return bound_result()


def audit(data, physical, phase, recorded, deadline, clock):
    assert phase == "audit" and recorded["caps"] == run.CAPS
    return dict(
        schema_version=1,
        kind="local-homotopy-curvature-audit",
        audit_pass=True,
        curvature_pass=recorded["curvature_pass"],
        attempted=recorded["attempted"],
        interval_arithmetic=False,
        field_pass=False,
        step4_pass=False,
    )


def phase(
    tmp_path,
    *,
    data=None,
    curve=produce,
    clock=None,
    writer=run.publish,
    phase="producer",
    producer_index=None,
):
    output = tmp_path / phase
    output.mkdir()
    events = []
    result = run.run_phase(
        data or phase_data(),
        phase,
        output,
        deadline=120.0,
        clock=clock or Clock(),
        old=old,
        curve=curve,
        writer=writer,
        producer_index=producer_index,
        emit=events.append,
    )
    return result, run.read(result["index"]), events


def test_complete_phase_and_audit_preserve_every_copy(tmp_path):
    data = phase_data(old_curvature=False)
    result, index, events = phase(tmp_path, data=data)
    assert result["complete"] and index["local_geometry_pass"]
    assert not index["old_geometry_pass"]
    assert [r["index"] for r in events] == [0, 1, 2]
    assert [run.read(r["reference"])["physical"] for r in index["curves"]] == data["seed"][
        "physical"
    ]
    checked, report, _ = phase(
        tmp_path, data=data, curve=audit, phase="audit", producer_index=index
    )
    assert checked["complete"] and report["local_geometry_pass"]
    assert all(report[key] is False for key in run.SCOPE)


def test_complete_negative_is_not_geometry_pass(tmp_path):
    def negative(*args):
        return bound_result(False)

    result, index, _ = phase(tmp_path, curve=negative)
    assert result["complete"] and not index["curvature_pass"] and not index["local_geometry_pass"]


@pytest.mark.parametrize("when", ["before", "during", "after-last"])
def test_expiration_never_passes(tmp_path, when):
    clock = Clock(120 if when == "before" else 0)
    calls = []

    def timed(*args):
        calls.append(1)
        clock.now = 120
        return bound_result(reason="deadline" if when == "during" else "complete")

    result, index, events = phase(tmp_path, data=phase_data(1), clock=clock, curve=timed)
    assert result["status"] == index["status"] == "deadline"
    assert not result["complete"] and not index["curvature_pass"]
    assert len(calls) == (0 if when == "before" else 1)
    assert len(events) == len(calls)


def test_expiration_during_curve_publication_preserves_report(tmp_path):
    clock = Clock()

    def writer(directory, name, payload, **kw):
        if name == "curve-00.json":
            clock.now = 120
            raise TimeoutError("synthetic persistence boundary")
        return run.publish(directory, name, payload, **kw)

    result, index, events = phase(tmp_path, clock=clock, writer=writer)
    assert not result["complete"] and len(events) == 1
    assert events[0]["reference"]["path"].endswith("curve-00-deadline.json")
    assert run.read(events[0]["reference"])["timed_failure"]
    assert [r["status"] for r in index["curves"]] == ["published", "unchecked", "unchecked"]


def test_expiration_during_index_publication_is_not_success(tmp_path):
    clock = Clock()

    def writer(directory, name, payload, **kw):
        if name == "index.json":
            clock.now = 120
            raise TimeoutError("late index")
        return run.publish(directory, name, payload, **kw)

    result, index, _ = phase(tmp_path, clock=clock, writer=writer)
    assert not result["complete"] and not index["complete"]
    assert result["index"]["path"].endswith("failure-index.json")
    assert index["status"] == "deadline"


def test_last_postpublication_clock_check_cannot_pass(tmp_path):
    clock = Clock()

    def writer(directory, name, payload, **kw):
        ref = run.publish(directory, name, payload, **kw)
        if name == "index.json":
            clock.now = 120
        return ref

    result, index, _ = phase(tmp_path, clock=clock, writer=writer)
    assert index["complete"]  # Retained bytes do not override the explicit failed return.
    assert not result["complete"] and result["status"] == "deadline"


def test_old_certificate_mismatch_stops_before_new_bounds(tmp_path):
    output = tmp_path / "phase"
    output.mkdir()
    data = phase_data()
    calls = []

    def wrong(data, phase):
        result = old(data, phase)
        result["gates"]["length"] = False
        return result

    result = run.run_phase(
        data,
        "producer",
        output,
        deadline=120,
        clock=Clock(),
        old=wrong,
        curve=lambda *args: calls.append(1),
    )
    assert not result["complete"] and not calls
    assert not run.read(result["index"])["old_certificate_matched"]


@pytest.mark.parametrize("key", ["field_pass", "step4_pass", "interval_arithmetic"])
def test_curve_scope_promotion_rejects(tmp_path, key):
    def wrong(*args):
        result = bound_result()
        result[key] = True
        return result

    result, index, _ = phase(tmp_path, curve=wrong)
    assert result["status"] == "error" and not index["curvature_pass"]


def test_curve_caps_cannot_be_lowered_for_study(tmp_path):
    def wrong(*args):
        result = bound_result()
        result["caps"]["evaluations"] = 1
        return result

    result, _, _ = phase(tmp_path, curve=wrong)
    assert result["status"] == "error"


def test_reservation_stops_before_next_curve(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "STATE_BYTES", run.CURVE_BYTES + run.INDEX_BYTES + 1)
    result, index, events = phase(tmp_path)
    assert result["status"] == "report-budget" and len(events) == 1
    assert index["curves"][1]["status"] == "unchecked"


def test_oversized_report_is_retained_as_execution_error(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "CURVE_BYTES", 100)
    result, index, events = phase(tmp_path)
    assert result["status"] == "error" and not events
    assert index["curves"][0]["status"] == "unchecked"


def test_audit_rejects_tampered_matrix(tmp_path):
    _, index, _ = phase(tmp_path)
    envelope = run.read(index["curves"][0]["reference"])
    envelope["physical"]["matrix"][0][0] = -1.0
    index["curves"][0]["reference"] = save(tmp_path, "changed-copy.json", envelope)
    result, _, _ = phase(tmp_path, phase="audit", curve=audit, producer_index=index)
    assert result["status"] == "error"


def test_audit_of_failed_producer_cannot_complete(tmp_path):
    _, index, _ = phase(tmp_path)
    index.update(status="deadline", complete=False)
    result, report, _ = phase(tmp_path, phase="audit", curve=audit, producer_index=index)
    assert result["status"] == "incomplete-producer" and not report["curvature_pass"]


@pytest.mark.parametrize(
    "failure,now,allowed",
    [(False, 119, True), (False, 120, False), (True, 124, True), (True, 125, False)],
)
def test_publication_clock_bounds(tmp_path, failure, now, allowed):
    if allowed:
        ref = run.publish(
            tmp_path,
            "result.json",
            {"ok": True},
            limit=100,
            deadline=120,
            clock=Clock(now),
            failure=failure,
        )
        assert run.read(ref) == {"ok": True}
    else:
        with pytest.raises(TimeoutError):
            run.publish(
                tmp_path,
                "result.json",
                {"ok": True},
                limit=100,
                deadline=120,
                clock=Clock(now),
                failure=failure,
            )


def test_publication_is_exclusive_and_bounded(tmp_path):
    kwargs = dict(limit=100, deadline=120, clock=Clock())
    run.publish(tmp_path, "result.json", {"a": 1}, **kwargs)
    with pytest.raises(FileExistsError):
        run.publish(tmp_path, "result.json", {"a": 2}, **kwargs)
    assert json.loads((tmp_path / "result.json").read_bytes()) == {"a": 1}
    with pytest.raises(ValueError, match="byte limit"):
        run.publish(tmp_path, "big.json", {"a": "x" * 101}, **kwargs)


def input_fixture(tmp_path, role="original-seed"):
    n, order = 6, 5
    coefficients = [
        [[float(i + j + k) / 100 for k in range(11)] for j in range(3)] for i in range(n)
    ]
    physical = [
        dict(
            base_index=i % n,
            period=i // (2 * n),
            flip=bool(i // n % 2),
            matrix=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        )
        for i in range(24)
    ]
    seed = dict(
        nbase=n,
        order=order,
        nfp=2,
        names=run.names(n, order),
        base_coefficients=coefficients,
        physical=physical,
        parameter_orientation="alpha=-2*pi*t",
        case=dict(label="seed"),
    )
    seed_ref = save(tmp_path, "seed.json", seed)
    geometry = dict(case=seed["case"], geometry_pass=True)
    geometry_ref = save(tmp_path, "geometry.json", dict(sets=[None, None, None, geometry]))
    case = dict(label="reference-n6-N", nbase=n, order=order, target="reference", method="N")
    x = run.flatten(coefficients)
    state_sha = hashlib.sha256(
        run.encode(dict(schema_version=1, names=seed["names"], x=x))
    ).hexdigest()
    gates = dict.fromkeys(run.GATES, True)
    proof = dict(
        case=case,
        original_seed=seed_ref,
        geometry_report=geometry_ref,
        geometry_report_index=3,
        x=x,
        state_sha256=state_sha,
        result=dict(gates=gates, certified=True),
    )
    proof_ref = save(tmp_path, "proof.json", proof)
    context = dict(
        case=case,
        original_context=dict(
            case=case,
            seed=seed,
            seed_reference=seed_ref,
            geometry_report=geometry,
            geometry_report_index=3,
            geometry_audit_reference=geometry_ref,
        ),
    )
    context_ref = save(tmp_path, "context.json", context)
    row = dict(
        label="seed-n6",
        role=role,
        seed=seed_ref,
        context=context_ref,
        old_certificate=proof_ref,
        geometry_report=geometry_ref,
        geometry_report_index=3,
        case=case,
        named_parameter_count=198,
        physical_copies=24,
        state_sha256=state_sha,
        old_gates=gates,
    )
    return dict(states=[row] * 12)


def test_metadata_loader_never_calls_bound_apis(tmp_path, monkeypatch):
    manifest = input_fixture(tmp_path)
    monkeypatch.setitem(sys.modules, "fusion_baselines.local_curvature", None)
    monkeypatch.setitem(sys.modules, "fusion_baselines.local_curvature_audit", None)
    data = run.load_state(manifest, 0)
    assert data["candidate"] == data["seed"]["base_coefficients"]


@pytest.mark.parametrize(
    "mutation",
    [
        "name",
        "coordinate",
        "state-sha",
        "geometry-index",
        "matrix",
        "inactive",
        "old-gate",
        "physical-count",
    ],
)
def test_input_identity_tamper_rejects(tmp_path, mutation):
    manifest = input_fixture(tmp_path)
    row = manifest["states"][0]
    if mutation in ("name", "matrix"):
        value = run.read(row["seed"])
        if mutation == "name":
            value["names"][0] = "coil[0]/yc(0)"
        else:
            value["physical"][0]["matrix"][0][0] = -1.0
        row["seed"] = save(tmp_path, "altered-seed.json", value)
    elif mutation in ("coordinate", "inactive"):
        value = run.read(row["old_certificate"])
        value["x"][0 if mutation == "coordinate" else 7] += 0.001
        row["old_certificate"] = save(tmp_path, "altered-proof.json", value)
    elif mutation == "state-sha":
        row["state_sha256"] = "f" * 64
    elif mutation == "geometry-index":
        row["geometry_report_index"] = 9
    elif mutation == "old-gate":
        row["old_gates"]["length"] = False
    else:
        row["physical_copies"] = 23
    with pytest.raises(ValueError):
        run.load_state(manifest, 0)


def test_reference_reads_hash_the_same_bytes_that_are_parsed(tmp_path):
    ref = save(tmp_path, "reference.json", {"a": 1})
    (tmp_path / "reference.json").write_bytes(b'{"a":2}')
    with pytest.raises(ValueError, match="hash changed"):
        run.read(ref)
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_bytes(b'{"a":1,"a":2}')
    with pytest.raises(ValueError, match="duplicate"):
        run.read(run.reference(duplicate))


def git(root, *args):
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            *args,
        ],
        stderr=subprocess.DEVNULL,
    )


def checkpoint_fixture(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    for name in run.SOURCE_PATHS:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic source\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "synthetic implementation")
    commit = git(repo, "rev-parse", "HEAD").decode().strip()
    sources = run.source_snapshot(repo)["sources"]
    artifacts = [
        save(tmp_path, f"artifact-{i}.json", dict(synthetic=True, index=i)) for i in range(5)
    ]
    qualification = dict(
        kind="local-curvature-implementation-qualification",
        status="completed",
        implementation_commit=commit,
        sources=sources,
        registration=run.reference(repo / run.REGISTRATION),
        artifacts=artifacts,
        checks=dict.fromkeys(
            ("focused", "public", "docs", "full_regression", "independent_review"), True
        ),
        field_pass=False,
        step4_pass=False,
    )
    qualification_ref = save(repo, "evidence/qualification.json", qualification)
    checkpoint = dict(
        schema_version=1,
        kind="local-curvature-execution-checkpoint",
        registration=qualification["registration"],
        qualification=qualification_ref,
        implementation_commit=commit,
        sources=sources,
        execution_allowed=True,
        field_pass=False,
        step4_pass=False,
    )
    checkpoint_ref = save(repo, "evidence/checkpoint.json", checkpoint)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "synthetic qualification checkpoint")
    return repo, checkpoint_ref


def test_gate_accepts_clean_committed_descendant(tmp_path):
    repo, checkpoint = checkpoint_fixture(tmp_path)
    source = run.execution_gate(checkpoint, repo)
    assert source["commit"] == git(repo, "rev-parse", "HEAD").decode().strip()


@pytest.mark.parametrize("mutation", ["dirty", "artifact", "source", "omit-source", "uncommitted"])
def test_gate_rejects_incomplete_or_changed_qualification(tmp_path, mutation):
    repo, checkpoint = checkpoint_fixture(tmp_path)
    if mutation == "dirty":
        (repo / "untracked.txt").write_text("dirty")
    elif mutation == "artifact":
        (tmp_path / "artifact-0.json").write_text("changed")
    elif mutation == "source":
        (repo / "scripts/run_local_curvature.py").write_text("changed")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "changed code")
    elif mutation == "omit-source":
        doc = run.read(checkpoint)
        doc["sources"].pop()
        checkpoint = save(repo, "evidence/checkpoint.json", doc)
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "bad checkpoint")
    else:
        checkpoint = save(tmp_path, "uncommitted.json", run.read(checkpoint))
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        run.execution_gate(checkpoint, repo)


def test_supervisor_rejects_silent_worker(tmp_path):
    def child(command, **kwargs):
        return subprocess.Popen([sys.executable, "-c", "pass"], **kwargs)

    config = dict(
        root=str(tmp_path),
        output=str(tmp_path / "phase"),
        phase="producer",
        checkpoint={},
        index=0,
        producer_index=None,
    )
    result, ref = run.supervise(config, popen=child)
    assert not result["complete"] and result["returned"] is None
    assert run.read(ref)["prefix"] == []


def test_hard_timeout_retains_failure_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "PHASE_SECONDS", 0.02)
    monkeypatch.setattr(run, "HARD_SECONDS", 0.07)

    def child(command, **kwargs):
        return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"], **kwargs)

    config = dict(
        root=str(tmp_path),
        output=str(tmp_path / "phase"),
        phase="producer",
        checkpoint={},
        index=0,
        producer_index=None,
    )
    started = time.monotonic()
    result, ref = run.supervise(config, popen=child)
    assert time.monotonic() - started < 2
    assert not result["complete"] and result["error"]["type"] == "TimeoutError"
    assert not run.read(ref)["complete"]


def test_parent_rejects_vacuous_complete_index(tmp_path):
    def child(command, **kwargs):
        config = run.read(json.loads(command[-1]))
        index = dict(complete=True, status="complete", curves=[])
        ref = save(Path(config["output"]), "index.json", index)
        event = dict(event="return", result=dict(index=ref, complete=True, status="complete"))
        return subprocess.Popen(
            [sys.executable, "-c", "print(" + repr(json.dumps(event)) + ")"], **kwargs
        )

    config = dict(
        root=str(tmp_path),
        output=str(tmp_path / "phase"),
        phase="producer",
        checkpoint={},
        index=0,
        producer_index=None,
        state_identity=dict(
            label="seed-n6", state_sha256="a" * 64, physical=phase_data()["seed"]["physical"]
        ),
    )
    result, _ = run.supervise(config, popen=child)
    assert not result["complete"]


def test_postlink_timeout_does_not_publish_duplicate_curve(tmp_path):
    clock = Clock()

    def writer(directory, name, payload, **kw):
        ref = run.publish(directory, name, payload, **kw)
        if name == "curve-00.json":
            clock.now = 120
            raise TimeoutError("already linked, post-persistence timeout")
        return ref

    result, index, events = phase(tmp_path, clock=clock, writer=writer)
    files = list((tmp_path / "producer").glob("curve-*.json"))
    assert not result["complete"] and len(events) == 1
    assert len(files) == 1
    assert index["curve_report_bytes"] == sum(p.stat().st_size for p in files)


@pytest.mark.parametrize("mutation", ["boolean-version", "integer-check", "float-check"])
def test_gate_rejects_json_type_aliases(tmp_path, mutation):
    repo, ref = checkpoint_fixture(tmp_path)
    checkpoint = run.read(ref)
    if mutation == "boolean-version":
        checkpoint["schema_version"] = True
    else:
        qualification = run.read(checkpoint["qualification"])
        qualification["checks"]["focused"] = 1 if mutation == "integer-check" else 1.0
        checkpoint["qualification"] = save(repo, "evidence/qualification.json", qualification)
    ref = save(repo, "evidence/checkpoint.json", checkpoint)
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "wrong JSON types")
    with pytest.raises(ValueError):
        run.execution_gate(ref, repo)


def test_parent_nonmapping_control_is_retained_failure(tmp_path):
    def child(command, **kwargs):
        return subprocess.Popen([sys.executable, "-c", "print('[]')"], **kwargs)

    config = dict(
        root=str(tmp_path),
        output=str(tmp_path / "phase"),
        phase="producer",
        checkpoint={},
        index=0,
        producer_index=None,
    )
    result, ref = run.supervise(config, popen=child)
    assert not result["complete"] and result["error"] is not None
    assert run.read(ref)["error"] == result["error"]


def producer_child(data, mutate=None):
    def child(command, **kwargs):
        config = run.read(json.loads(command[-1]))
        events = []
        result = run.run_phase(
            data,
            "producer",
            config["output"],
            deadline=config["deadline"],
            old=old,
            curve=produce,
            emit=events.append,
        )
        if mutate is not None:
            index = run.read(result["index"])
            mutate(index)
            result["index"] = save(Path(config["output"]), "index.json", index)
        events.append(dict(event="return", result=result))
        lines = "\n".join(json.dumps(e) for e in events)
        return subprocess.Popen([sys.executable, "-c", "print(" + repr(lines) + ")"], **kwargs)

    return child


def test_successful_subprocess_requires_complete_explicit_identity(tmp_path):
    data = phase_data()
    config = dict(
        root=str(tmp_path),
        output=str(tmp_path / "phase"),
        phase="producer",
        checkpoint={},
        index=0,
        producer_index=None,
        state_identity=run.state_identity(data),
    )
    result, ref = run.supervise(config, popen=producer_child(data))
    assert result["complete"] and result["returned_validated"]
    assert len(result["prefix"]) == 3 and run.read(ref)["complete"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("field_pass", True),
        ("label", "wrong"),
        ("phase", "audit"),
        ("state_sha256", "f" * 64),
        ("curve_report_bytes", 0),
        ("local_geometry_pass", False),
        ("complete", 1),
        ("old_geometry_pass", 1),
    ],
)
def test_parent_rejects_poisoned_index(tmp_path, key, value):
    data = phase_data()
    config = dict(
        root=str(tmp_path),
        output=str(tmp_path / "phase"),
        phase="producer",
        checkpoint={},
        index=0,
        producer_index=None,
        state_identity=run.state_identity(data),
    )
    result, ref = run.supervise(
        config, popen=producer_child(data, lambda row: row.update({key: value}))
    )
    assert not result["complete"] and result["error"] is not None
    assert len(result["prefix"]) == 3 and not run.read(ref)["complete"]


def test_shared_audit_reservation_includes_producer_bytes(tmp_path, monkeypatch):
    _, producer, _ = phase(tmp_path)
    output = tmp_path / "audit"
    output.mkdir()
    prior = run.STATE_BYTES - run.CURVE_BYTES
    result = run.run_phase(
        phase_data(),
        "audit",
        output,
        deadline=120,
        clock=Clock(),
        producer_index=producer,
        old=old,
        curve=audit,
        prior_bytes=prior,
        index_reserve=run.INDEX_BYTES // 2,
    )
    index = run.read(result["index"])
    assert result["status"] == "report-budget"
    assert all(row["status"] == "unchecked" for row in index["curves"])
    assert prior + result["index"]["bytes"] <= run.STATE_BYTES


def study_fixture(monkeypatch, tmp_path, *, free=run.RESERVE_BYTES):
    calls = []
    monkeypatch.setattr(run, "execution_gate", lambda *a, **k: dict(commit="synthetic"))
    monkeypatch.setattr(run, "source_snapshot", lambda *a: dict(commit="synthetic"))
    monkeypatch.setattr(run, "intake", lambda *a: (None, {}))
    monkeypatch.setattr(run, "load_state", lambda *a: phase_data())
    monkeypatch.setattr(run.shutil, "disk_usage", lambda *a: SimpleNamespace(free=free))

    def supervise(config):
        calls.append(copy.deepcopy(config))
        output = Path(config["output"])
        output.mkdir()
        index = save(output, "index.json", dict(synthetic=True))
        prefix = [save(output, "curve-00.json", dict(synthetic=True))]
        result = dict(
            returned=dict(index=index), returned_validated=True, prefix=prefix, complete=True
        )
        return result, save(output, "parent.json", result)

    monkeypatch.setattr(run, "supervise", supervise)
    return calls


def test_study_serial_order_and_shared_index_reservation(tmp_path, monkeypatch):
    calls = study_fixture(monkeypatch, tmp_path)
    result = run.run_study(tmp_path / "study", {}, root=tmp_path)
    assert result["complete"] and len(calls) == 24
    assert [(c["index"], c["phase"]) for c in calls] == [
        (i, p) for i in range(12) for p in ("producer", "audit")
    ]
    for c in calls[1::2]:
        assert c["prior_bytes"] > 0
        assert c["index_reserve"] == run.INDEX_BYTES - c["producer_index"]["bytes"]
    assert all(result[key] is False for key in run.SCOPE)


def test_low_disk_stops_without_deleting_or_dispatching(tmp_path, monkeypatch):
    calls = study_fixture(monkeypatch, tmp_path, free=run.RESERVE_BYTES - 1)
    preserved = tmp_path / "old.json"
    preserved.write_text("old evidence")
    result = run.run_study(tmp_path / "study", {}, root=tmp_path)
    assert not result["complete"] and result["stop_reason"] == "low-disk" and not calls
    assert result["unchecked"] == run.state_labels() and preserved.read_text() == "old evidence"


def test_real_pure_apis_on_one_synthetic_circle(tmp_path):
    data = phase_data(1)
    produced, producer_index, events = phase(tmp_path, data=data, curve=run._curve)
    producer_config = dict(
        output=str(tmp_path / "producer"),
        phase="producer",
        state_identity=run.state_identity(data),
        producer_index=None,
    )
    assert run.validate_return(producer_config, produced, [e["reference"] for e in events])
    audited, _, checked = phase(
        tmp_path, data=data, curve=run._curve, phase="audit", producer_index=producer_index
    )
    audit_config = dict(
        output=str(tmp_path / "audit"),
        phase="audit",
        state_identity=run.state_identity(data),
        producer_index=produced["index"],
    )
    assert run.validate_return(audit_config, audited, [e["reference"] for e in checked])


def test_parent_postpublication_expiration_returns_negative_ack(tmp_path, monkeypatch):
    clock = Clock(time.monotonic())
    started = clock.now
    original_publish = run.publish

    def publish(directory, name, payload, **kwargs):
        ref = original_publish(directory, name, payload, **kwargs)
        if name == "parent.json":
            clock.now = started + run.PHASE_SECONDS
        return ref

    monkeypatch.setattr(run, "publish", publish)
    data = phase_data(1)
    config = dict(
        root=str(tmp_path),
        output=str(tmp_path / "phase"),
        phase="producer",
        checkpoint={},
        index=0,
        producer_index=None,
        state_identity=run.state_identity(data),
    )
    result, ref = run.supervise(config, clock=clock, popen=producer_child(data))
    assert not result["complete"]
    assert not run.read(ref)["complete"]
    assert ref["path"].endswith("parent-failure.json")
    prior = run.read(ref)["superseded_acknowledgement"]
    assert prior["path"].endswith("parent.json") and run.read(prior)["complete"]


def test_directory_fsync_failure_retains_linked_curve_and_bytes(tmp_path, monkeypatch):
    original_fsync = run.os.fsync
    failed = False

    def fsync(fd):
        nonlocal failed
        if not failed and stat.S_ISDIR(run.os.fstat(fd).st_mode):
            failed = True
            raise OSError("synthetic directory persistence failure after link")
        return original_fsync(fd)

    monkeypatch.setattr(run.os, "fsync", fsync)
    result, index, events = phase(tmp_path)
    assert not result["complete"] and index["status"] == "error"
    assert index["error"]["type"] == "OSError"
    assert index["curves"][0]["status"] == "published" and len(events) == 1
    published = list((tmp_path / "producer").glob("curve-*.json"))
    assert len(published) == 1
    assert index["curve_report_bytes"] == sum(p.stat().st_size for p in published)
