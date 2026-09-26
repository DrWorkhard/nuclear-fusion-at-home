"""Synthetic saved-graph audit controls, not physical coil acceptance."""

import copy

import pytest
from test_protected_run_cell import Harness

from fusion_baselines import protected_cell_audit as audit
from fusion_baselines.protected_run_snapshots import SnapshotStore, _array_bytes, read_json


@pytest.fixture(scope="module")
def histories(tmp_path_factory):
    result = {}
    for strategy in (
        "null",
        "gapped",
        "geometry-budget",
        "geometry-reject",
        "overcurrent",
        "armijo-reject",
    ):
        h = Harness(tmp_path_factory.mktemp(strategy), strategy=strategy)
        reference = h.run()
        result[strategy] = h, reference, read_json(reference)
    return result


@pytest.mark.parametrize(
    "strategy",
    ["null", "gapped", "geometry-budget", "geometry-reject", "overcurrent", "armijo-reject"],
)
def test_completed_graphs_reconstructed_without_producer_or_native_work(histories, strategy):
    h, reference, result = histories[strategy]
    before = len(h.adapter.native_calls)
    verdict = audit.audit_cell(reference, h.context)
    assert verdict["integration_integrity_pass"], verdict
    assert verdict["counts"] == result["counts"]
    assert verdict["complete_bundles"] == len(result["bundles"])
    assert verdict["checkpoint_prefixes"] == len(result["checkpoints"])
    assert all(verdict[k] is False for k in audit.SCOPE)
    assert len(h.adapter.native_calls) == before


@pytest.mark.parametrize(
    "key",
    [
        "producer_complete",
        "independent_audit_pass",
        "physical_admission",
        "step4_pass",
        "schema_version",
        "kind",
        "case",
        "counts",
        "selected_bundle",
        "replay_bundle",
        "selected_replay",
    ],
)
def test_rehashed_result_identity_changes_rejected(histories, tmp_path, key):
    h, _, result = histories["gapped"]
    changed = copy.deepcopy(result)
    changed[key] = None
    reference = SnapshotStore(tmp_path / "new").json("result", changed)
    assert not audit.audit_cell(reference, h.context)["integration_integrity_pass"]


@pytest.mark.parametrize("key", ["models", "certificates", "bundles", "checkpoints"])
@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate", "reverse"])
def test_manifest_collections_exact_complete_and_ordered(histories, tmp_path, key, mutation):
    h, _, result = histories["gapped"]
    changed = copy.deepcopy(result)
    if mutation == "missing":
        changed[key].pop()
    elif mutation == "extra":
        changed[key].append(changed[key][0])
    elif mutation == "duplicate":
        changed[key][1] = changed[key][0]
    else:
        changed[key].reverse()
    reference = SnapshotStore(tmp_path / "new").json("result", changed)
    assert not audit.audit_cell(reference, h.context)["integration_integrity_pass"]


@pytest.mark.parametrize("journal", ["native", "controller"])
@pytest.mark.parametrize("mutation", ["receipt", "directory", "alias"])
def test_no_guessed_receipts_or_aliased_journals(histories, tmp_path, journal, mutation):
    h, _, result = histories["gapped"]
    changed = copy.deepcopy(result)
    entry = changed["journals"][journal]
    if mutation == "receipt":
        entry["receipt"]["records"] -= 1
    elif mutation == "directory":
        entry["directory"] = str(tmp_path / "absent")
    else:
        changed["journals"][journal] = changed["journals"][
            "controller" if journal == "native" else "native"
        ]
    reference = SnapshotStore(tmp_path / "new").json("result", changed)
    assert not audit.audit_cell(reference, h.context)["integration_integrity_pass"]


@pytest.mark.parametrize(
    "target,key",
    [
        ("certificate", "case"),
        ("certificate", "operation_id"),
        ("certificate", "x"),
        ("certificate", "state_sha256"),
        ("certificate", "original_seed"),
        ("certificate", "geometry_report"),
        ("certificate", "geometry_report_index"),
        ("bundle", "case"),
        ("bundle", "phase"),
        ("bundle", "operation_id"),
        ("bundle", "certificate"),
        ("checkpoint", "counts"),
        ("checkpoint", "journals"),
        ("checkpoint", "certificates"),
        ("checkpoint", "bundles"),
        ("checkpoint", "phase"),
        ("initialization", "metadata"),
        ("screen", "startup_screen_pass"),
    ],
)
def test_semantic_mutations_after_hash_reader_reject(histories, monkeypatch, target, key):
    """Mock the already-hash-checked reader to isolate semantic linkage checks."""
    h, reference, result = histories["gapped"]
    target_ref = dict(
        certificate=result["certificates"][11],
        bundle=result["bundles"][11],
        checkpoint=result["checkpoints"][12],
        initialization=result["models"][0],
        screen=result["startup_screen"],
    )[target]

    def changed_read(ref):
        data = read_json(ref)
        if ref == target_ref:
            data[key] = None
        return data

    monkeypatch.setattr(audit, "read_json", changed_read)
    assert not audit.audit_cell(reference, h.context)["integration_integrity_pass"]


def test_controller_view_must_equal_full_certificate_decision(histories, monkeypatch):
    h, reference, result = histories["gapped"]
    original = read_json(result["certificates"][11])
    assert original["result"]["certified"] is False

    def changed_read(ref):
        data = read_json(ref)
        if ref == result["certificates"][11]:
            data["result"]["calculation_complete"] = False
        return data

    monkeypatch.setattr(audit, "read_json", changed_read)
    verdict = audit.audit_cell(reference, h.context)
    assert not verdict["integration_integrity_pass"]
    assert "compact decision" in verdict["error"]


@pytest.mark.parametrize("mutation", ["count", "clock", "flags", "points", "model", "reference"])
def test_semantic_ledger_mutations_after_journal_reader_reject(histories, monkeypatch, mutation):
    h, reference, result = histories["null"]
    original_reader = audit.read_events

    def changed_read(directory, receipt):
        events = original_reader(directory, receipt)
        if directory == result["journals"]["native"]["directory"]:
            if mutation == "count":
                events.pop()
            elif mutation == "clock":
                events[2]["native"]["completed_monotonic"] = -1.0
            elif mutation == "flags":
                events[1]["native"]["native_started"] = True
            elif mutation == "points":
                events[1]["native"]["points"] = 255
            elif mutation == "model":
                events[1]["model_id"] = "replay"
            else:
                events[3]["raw_reference"] = result["models"][1]
        return events

    monkeypatch.setattr(audit, "read_events", changed_read)
    assert not audit.audit_cell(reference, h.context)["integration_integrity_pass"]


def test_false_context_completeness_and_wrong_hash_fail_closed(histories):
    h, reference, _ = histories["null"]
    context = copy.deepcopy(h.context)
    del context["historical_seed"]["arrays"]["boundary_A"]
    assert not audit.audit_cell(reference, context)["integration_integrity_pass"]
    changed = dict(reference, sha256="0" * 64)
    assert not audit.audit_cell(changed, h.context)["integration_integrity_pass"]


def test_correctly_hash_bound_corrupt_archive_returns_failed_verdict(tmp_path):
    class CrcBrokenStore(SnapshotStore):
        def arrays(self, name, values):
            raw = bytearray(_array_bytes(values))
            raw[1000] ^= 1
            return self._write(name, values, ".npz", lambda _: bytes(raw))

    h = Harness(tmp_path, store_type=CrcBrokenStore)
    reference = h.run()
    verdict = audit.audit_cell(reference, h.context)
    assert verdict["integration_integrity_pass"] is False
    assert "CRC" in verdict["error"]
    assert all(verdict[k] is False for k in audit.SCOPE)
