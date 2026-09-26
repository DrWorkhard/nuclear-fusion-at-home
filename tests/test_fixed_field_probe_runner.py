"""Injected runner composition; never touches real registered proposal fields."""

import copy
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_fixed_field_probe as run  # noqa: E402

from fusion_baselines import fixed_field_probe_native as native  # noqa: E402
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json  # noqa: E402
from fusion_baselines.protected_search_journal import _encode, read_events  # noqa: E402


def context(monkeypatch, nbase=6):
    from test_fixed_field_probe_native import setup

    for key in run.THREADS:
        monkeypatch.setenv(key, "1")
    args, models, _ = setup(monkeypatch, nbase=nbase)
    row = dict(
        case=args["case"],
        seed=args["seed"],
        x=args["x"].tolist(),
        names=args["seed"]["names"],
        row=dict(state_sha256="a" * 64),
    )
    admitted = dict(cell_sources=args["source"], states=[copy.deepcopy(row) for _ in range(4)])
    return admitted, models


@pytest.mark.parametrize("pair_index", (0, 1))
def test_complete_producer(monkeypatch, tmp_path, pair_index):
    admitted, models = context(monkeypatch, nbase=6 if pair_index == 0 else 8)
    budget = run.PayloadBudget()
    writer = run.Writer(tmp_path / "records", budget, lambda: None)
    progress = []
    result = run.produce(
        admitted, pair_index, tmp_path, writer, budget, lambda: None, progress.append
    )
    assert (result["models"], result["native_requests"], result["native_points"]) == (
        12,
        84,
        402432,
    )
    assert len(models) == 12
    assert len([r for r in progress if r.get("operation") == "model-returned"]) == 12
    for state in result["states"]:
        assert len(state["models"]) == 6
        rows = [read_json(ref) for ref in state["models"]]
        assert all(r["snapshot"] == rows[0]["snapshot"] for r in rows)
        for row in rows:
            assert len(read_events(row["event_directory"], row["event_receipt"])) == 14
    assert budget.used == sum(p.stat().st_size for p in tmp_path.rglob("*") if p.is_file())
    assert all(r["acknowledged"] for r in writer.attempts)


@pytest.mark.parametrize("at", (0, 1, 5, 6, 11))
def test_model_failure_preserves_only_prefix(monkeypatch, tmp_path, at):
    admitted, models = context(monkeypatch)
    original = native.evaluate_model
    calls = []

    def evaluate(*args, **kwargs):
        calls.append(1)
        if len(calls) == at + 1:
            raise RuntimeError("synthetic native failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(native, "evaluate_model", evaluate)
    writer = run.Writer(tmp_path / "records", run.PayloadBudget(), lambda: None)
    progress = []
    with pytest.raises(RuntimeError):
        run.produce(admitted, 0, tmp_path, writer, writer.budget, lambda: None, progress.append)
    assert len(models) == at
    assert len([r for r in progress if r.get("operation") == "model-returned"]) == at
    assert len([r for r in progress if r.get("operation") == "model-attempted"]) == at + 1


def test_writer_guard_after_publication_retains_reference(tmp_path):
    count = []

    def guard():
        count.append(1)
        if len(count) == 2:
            raise TimeoutError("after publication")

    writer = run.Writer(tmp_path / "raw", run.PayloadBudget(), guard)
    with pytest.raises(TimeoutError):
        writer.json("test", dict(value=1))
    assert read_json(writer.references[0]) == dict(value=1)
    assert writer.attempts[0]["acknowledged"] is True


def test_failed_store_preserves_attempt_and_charge(tmp_path, monkeypatch):
    writer = run.Writer(tmp_path / "raw", run.PayloadBudget(), lambda: None)

    def fail(*args):
        raise OSError("synthetic writer failure")

    monkeypatch.setattr(writer.store, "json", fail)
    with pytest.raises(OSError):
        writer.json("test", dict(value=1))
    assert not writer.references
    assert writer.attempts[0]["acknowledged"] is False
    assert writer.budget.used == len(_encode(dict(value=1)))


def test_array_budget(tmp_path):
    writer = run.Writer(tmp_path / "raw", run.PayloadBudget(), lambda: None)
    reference = writer.arrays("arrays", dict(x=np.arange(5.0)))
    assert writer.budget.used == reference["bytes"]


def test_safe_phase_never_discovers_files(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise OSError("parent acknowledgement fsync")

    monkeypatch.setattr(run, "run_phase", fail)
    row = run.safe_phase(tmp_path, "producer", 0, {}, run.PayloadBudget())
    assert row["complete"] is False and row["result"] is None
    assert row["acknowledgement"] is None


def test_second_pair_after_parent_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(run, "execution_gate", lambda *a, **k: {"synthetic": True})
    monkeypatch.setattr(run.shutil, "disk_usage", lambda p: SimpleNamespace(free=run.START_FREE))
    attempts = []

    def phase(directory, kind, index, *args, **kwargs):
        attempts.append((index, kind))
        if index == 0:
            raise OSError("first pair parent failure")
        return dict(complete=True, result={"synthetic": True})

    monkeypatch.setattr(run, "run_phase", phase)
    result = read_json(run.run_study(tmp_path / "run", {}))
    assert attempts == [(0, "producer"), (1, "producer"), (1, "audit")]
    assert result["pairs"][0]["producer"]["complete"] is False
    assert result["pairs"][0]["audit"] is None
    assert result["step4_pass"] is False


def test_source_failure_leaves_rest_unchecked(monkeypatch, tmp_path):
    calls = []

    def gate(*a, **k):
        calls.append(1)
        if len(calls) > 1:
            raise ValueError("source changed")
        return {"synthetic": True}

    monkeypatch.setattr(run, "execution_gate", gate)
    monkeypatch.setattr(run.shutil, "disk_usage", lambda p: SimpleNamespace(free=run.START_FREE))
    result = read_json(run.run_study(tmp_path / "run", {}))
    assert len(result["pairs"]) == 2 and all(r["unchecked"] for r in result["pairs"])
    assert result["final_source_error"]


@pytest.mark.parametrize("failure", (None, "source", "producer", "after_source", "admission"))
def test_worker_explicit_return(monkeypatch, tmp_path, failure):
    import fixed_field_probe_inputs as inputs

    monkeypatch.setattr(run, "_ACTIVE", False)
    for key in run.THREADS:
        monkeypatch.setenv(key, "1")
    called = []

    def gate(*args, **kwargs):
        called.append(1)
        if failure == "source" or (failure == "after_source" and len(called) > 1):
            raise ValueError("synthetic source failure")
        return {"synthetic": True}

    admitted = dict(
        metadata_identity={},
        current_admission=dict(
            current_provenance={}, checked_inputs={}, source_before={}, source_after={}
        ),
    )

    def intake(*args, **kwargs):
        if failure == "admission":
            raise ValueError("synthetic admission failure")
        return admitted

    def produce(*args, **kwargs):
        if failure == "producer":
            raise ValueError("synthetic model failure")
        return {"synthetic": True}

    monkeypatch.setattr(run, "execution_gate", gate)
    monkeypatch.setattr(inputs, "intake", intake)
    monkeypatch.setattr(run, "produce", produce)
    config = dict(
        phase="producer",
        pair_index=0,
        output=str(tmp_path / "worker"),
        started_monotonic=time.monotonic(),
        payload_charged_bytes=0,
        checkpoint={},
        root=str(tmp_path),
    )
    ref = SnapshotStore(tmp_path / "config").json("config", config)
    rd, wr = os.pipe()
    try:
        status = run.worker(ref, wr)
        os.close(wr)
        wr = None
        frames = [json.loads(line) for line in os.read(rd, 10000).splitlines()]
    finally:
        os.close(rd)
        if wr is not None:
            os.close(wr)
    assert status == (0 if failure is None else 1)
    assert frames[-1]["kind"] == ("returned" if failure is None else "failed")
    saved = read_json(frames[-1]["payload"]["reference"])
    assert saved["status"] == ("completed" if failure is None else "failed")
    assert saved["physical_admission"] is False
    assert frames[-1]["payload"]["payload_charged_bytes"] >= sum(
        p.stat().st_size for p in (tmp_path / "worker").rglob("*") if p.is_file()
    )


def test_execution_rejects_dirty_tree(monkeypatch):
    monkeypatch.setattr(run, "git", lambda *a: b"?? source.py\n")
    with pytest.raises(ValueError, match="clean"):
        run.execution_gate({})


def test_execution_rejects_missing_qualification(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "git", lambda *a: b"")
    ref = SnapshotStore(tmp_path / "store").json("fake", dict(kind="unregistered"))
    with pytest.raises(ValueError, match="checkpoint"):
        run.execution_gate(ref)


@pytest.mark.parametrize("failure_level", (None, 0, 3, 5))
def test_saved_audit_composition(monkeypatch, tmp_path, failure_level):
    from fusion_baselines import fixed_field_probe_audit as audit

    admitted, _ = context(monkeypatch)
    for state in admitted["states"]:
        state.update(
            input_data={"synthetic": True},
            control_bundle={"old": "bundle"},
            control_snapshot={"old": "snapshot"},
        )
    admitted["pairs"] = [dict(original={"original": 0}), dict(original={"original": 1})]
    budget = run.PayloadBudget()
    producer_writer = run.Writer(tmp_path / "producer", budget, lambda: None)
    produced = run.produce(
        admitted, 0, tmp_path, producer_writer, budget, lambda: None, lambda e: None
    )
    ref = producer_writer.json(
        "result", dict(status="completed", phase="producer", pair_index=0, result=produced)
    )
    calls = []

    def model(seed, x, case, level, snapshot, init, metrics, arrays, **kwargs):
        i = len(calls)
        assert level == run.LEVELS[i % 6]
        assert kwargs["target"] == dict(ninner=level["ninner"])
        assert (kwargs["control_bundle"] is not None) is (i == 0)
        assert (kwargs["control_snapshot"] is not None) is (i == 0)
        assert kwargs["input_data"] == {"synthetic": True}
        assert callable(kwargs["guard"])
        calls.append(level)
        return dict(numerical_pass=i != failure_level)

    def state(rows):
        assert len(rows) == 6
        return dict(numerical_pass=all(row["numerical_pass"] for row in rows))

    def compare(left, right, pair):
        assert pair == {"original": 0}
        return dict(
            synthetic=True,
            numerical_pass=left["numerical_pass"] and right["numerical_pass"],
            **run.SCOPE,
        )

    monkeypatch.setattr(audit, "audit_model", model)
    monkeypatch.setattr(audit, "audit_state", state)
    monkeypatch.setattr(audit, "compare_pair", compare)
    monkeypatch.setattr(run, "targets", lambda *a: {n: dict(ninner=n) for n in (32, 64)})
    writer = run.Writer(tmp_path / "audit", budget, lambda: None)
    result = run.audit(admitted, 0, ref, writer, budget, lambda: None, lambda e: None)
    assert len(calls) == 12 and len(result["states"]) == 2
    assert read_json(result["comparison"])["numerical_pass"] is (failure_level is None)


def gate_fixture(monkeypatch, tmp_path):
    store = SnapshotStore(tmp_path / "records")
    source_ref = store.json("source", dict(synthetic="source"))
    registration = store.json("registration", dict(synthetic="registration"))
    artifacts = [store.json(f"check-{i}", dict(synthetic=i)) for i in range(5)]
    source = dict(commit="b" * 40, sources=[source_ref])
    base = dict(
        schema_version=1,
        implementation_commit="a" * 40,
        sources=[source_ref],
        registration=registration,
        **run.SCOPE,
    )
    qualification = dict(
        base,
        kind="fixed-field-probe-implementation-qualification",
        status="completed",
        checks=dict.fromkeys(
            ("focused", "public", "docs", "full_regression", "independent_review"), True
        ),
        artifacts=artifacts,
    )
    qualification["evidence"] = dict(zip(qualification["checks"], artifacts, strict=True))

    def checkpoint(q=qualification, **changes):
        qref = store.json("qualification", q)
        return store.json(
            "checkpoint",
            dict(
                base,
                qualification=qref,
                kind="fixed-field-probe-execution-checkpoint",
                execution_allowed=True,
                **changes,
            ),
        )

    def git(root, *args):
        if args[0] == "show":
            return (tmp_path / args[1].split(":", 1)[1]).read_bytes()
        return b""

    monkeypatch.setattr(run, "git", git)
    monkeypatch.setattr(run, "source_snapshot", lambda *a, **k: copy.deepcopy(source))
    monkeypatch.setattr(run, "REGISTRATION", "records/registration.json")
    return checkpoint, qualification, source


def test_complete_gate_synthetic(monkeypatch, tmp_path):
    checkpoint, _, source = gate_fixture(monkeypatch, tmp_path)
    assert run.execution_gate(checkpoint(), tmp_path) == source


@pytest.mark.parametrize(
    "fault",
    (
        "status",
        "check",
        "bool_alias",
        "scope",
        "sources",
        "registration",
        "implementation",
        "artifact",
        "schema_bool",
        "missing_roles",
        "duplicate_artifact",
        "duplicate_role",
    ),
)
def test_gate_qualification_mutations(monkeypatch, tmp_path, fault):
    checkpoint, qualification, _ = gate_fixture(monkeypatch, tmp_path)
    if fault == "status":
        qualification["status"] = "pending"
    elif fault == "check":
        qualification["checks"].pop("full_regression")
    elif fault == "bool_alias":
        qualification["checks"]["full_regression"] = 1
    elif fault == "scope":
        qualification["physical_admission"] = True
    elif fault == "sources":
        qualification["sources"] = []
    elif fault == "registration":
        qualification["registration"] = {}
    elif fault == "implementation":
        qualification["implementation_commit"] = "c" * 40
    elif fault == "artifact":
        qualification["artifacts"][0]["sha256"] = "0" * 64
    elif fault == "schema_bool":
        qualification["schema_version"] = True
    elif fault == "missing_roles":
        qualification.pop("evidence")
    elif fault == "duplicate_artifact":
        qualification["artifacts"][1] = qualification["artifacts"][0]
    elif fault == "duplicate_role":
        qualification["evidence"]["public"] = qualification["evidence"]["focused"]
    with pytest.raises(ValueError):
        run.execution_gate(checkpoint(), tmp_path)


def test_checkpoint_schema_boolean_rejected(monkeypatch, tmp_path):
    checkpoint, _, _ = gate_fixture(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="checkpoint"):
        run.execution_gate(checkpoint(schema_version=True), tmp_path)
