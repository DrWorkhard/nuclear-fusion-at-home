"""Saved nonphysical graphs: independent order and byte-binding negative controls."""

import copy
import hashlib
from pathlib import Path

import pytest
from test_protected_fine_cell import setup

from fusion_baselines import protected_fine_graph as graph
from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_fine_process import SCOPE
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_arrays, read_json


def create(monkeypatch, directory, case=None):
    runner, _ = setup(monkeypatch, directory, case)
    runner.source = SnapshotStore(directory / "sources").json("source", {"synthetic": True})
    ref = runner.call(runner.run)
    return dict(reference=ref, context=copy.deepcopy(runner.context), source=runner.source,
                core=read_json(ref))


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    directory = tmp_path_factory.mktemp("fine-graph")
    with pytest.MonkeyPatch.context() as patch:
        return create(patch, directory)


def audit(base, guard=lambda: None):
    return graph.audit_fine_graph(base["reference"], base["context"], base["source"], guard)


def intercept_json(monkeypatch, target, change):
    original = graph.read_json

    def altered(reference):
        row = original(reference)
        if reference == target:
            change(row)
        return row

    monkeypatch.setattr(graph, "read_json", altered)


@pytest.mark.parametrize("case", plan.cases(), ids=lambda case: case["label"])
def test_complete_saved_graph_all_cases(monkeypatch, tmp_path, case):
    base = create(monkeypatch, tmp_path, case)
    result = audit(base)
    assert result["graph_consistency"] is True
    assert all(result[key] is False for key in ("complete_execution", *SCOPE))
    assert result["counts"]["native"] == dict(attempted=80, completed=80)
    assert result["counts"]["points"] == dict(attempted=552960, completed=552960)
    assert len(result["initialization_rows"]) == 8
    assert len(result["operation_rows"]) == 24
    assert len(result["geometry_rows"]) == 4
    assert result["geometry_work"] == base["core"]["geometry_work"]
    assert result["case"] == case


@pytest.mark.parametrize("key", ["complete_execution", *SCOPE])
@pytest.mark.parametrize("value", [True, 0])
def test_core_cannot_self_assert_acceptance(monkeypatch, base, key, value):
    intercept_json(monkeypatch, base["reference"], lambda row: row.update({key: value}))
    with pytest.raises(ValueError):
        audit(base)


@pytest.mark.parametrize("fault", ["version", "kind", "case", "source", "counts",
                                  "producer", "missing", "extra", "models", "operations",
                                  "geometry", "journal-location", "journal-receipt"])
def test_top_level_mutations(monkeypatch, base, fault):
    def change(row):
        if fault == "version":
            row["schema_version"] = True
        elif fault == "kind":
            row["kind"] = "protected-cell-execution"
        elif fault == "case":
            row["case"] = plan.cases()[1]
        elif fault == "source":
            row["source"]["sha256"] = "f" * 64
        elif fault == "counts":
            row["counts"]["native"]["completed"] = 79
        elif fault == "producer":
            row["producer_complete"] = 1
        elif fault == "missing":
            row.pop("geometry_work")
        elif fault == "extra":
            row["extra"] = 1
        elif fault in ("models", "operations", "geometry"):
            row["initializations" if fault == "models" else fault].pop()
        elif fault == "journal-location":
            row["journal"]["directory"] = str(Path(base["reference"]["path"]).parent)
        else:
            row["journal"]["receipt"]["head_sha256"] = "f" * 64

    intercept_json(monkeypatch, base["reference"], change)
    with pytest.raises(ValueError):
        audit(base)


@pytest.mark.parametrize("fault", ["order", "coordinate-sha", "model", "sequence", "native-index",
                                  "points", "quantity", "status", "flags", "start", "end",
                                  "extra-native", "missing", "completion-ref", "totals"])
def test_journal_semantics_after_canonical_chain_read(monkeypatch, base, fault):
    original = graph.read_events

    def changed(directory, receipt):
        rows = original(directory, receipt)
        if fault == "order":
            rows[1], rows[2] = rows[2], rows[1]
        elif fault == "coordinate-sha":
            rows[0]["selected_coordinate_sha256"] = "c" * 64
        elif fault == "model":
            rows[1]["model_id"] = "diagnostic-1"
        elif fault == "sequence":
            rows[0]["sequence"] = False
        elif fault == "native-index":
            rows[1]["native"]["index"] = True
        elif fault == "points":
            rows[1]["native"]["points"] = 256.0
        elif fault == "quantity":
            rows[1]["native"]["quantity"] = "B"
        elif fault == "status":
            rows[2]["native"]["status"] = "error"
        elif fault == "flags":
            rows[1]["native"]["native_started"] = True
        elif fault == "start":
            rows[2]["native"]["started_monotonic"] += 0.001
        elif fault == "end":
            rows[2]["native"]["completed_monotonic"] = 0.0
        elif fault == "extra-native":
            rows[1]["native"]["extra"] = 1
        elif fault == "missing":
            rows.pop()
        elif fault == "completion-ref":
            rows[3]["raw_reference"]["sha256"] = "f" * 64
        else:
            rows[-1]["counts"]["points"]["completed"] -= 1
        return rows

    monkeypatch.setattr(graph, "read_events", changed)
    with pytest.raises(ValueError):
        audit(base)


@pytest.mark.parametrize("fault", ["case", "method", "initializer-callback", "context-x",
                                  "operation-model", "operation-order", "operation-source",
                                  "raw-path", "geometry-level", "geometry-pairs", "geometry-total"])
def test_raw_reference_linkage_mutations(monkeypatch, base, fault):
    core = base["core"]
    if fault in ("case", "method", "initializer-callback"):
        target = core["initializations"][0]
    elif fault == "context-x":
        target = core["context"]
    elif fault.startswith("geometry-"):
        target = base["reference"] if fault == "geometry-total" else core["geometry"][0]
    else:
        target = core["operations"][0]

    def change(row):
        if fault == "case":
            row["case"] = plan.cases()[1]
        elif fault == "method":
            row["spec"]["method"] = "V"
        elif fault == "initializer-callback":
            row["metadata"]["initialization_native_calls"][0]["points"] = 1
        elif fault == "context-x":
            row["selected"]["state"]["x"][0] += 1.0
        elif fault == "operation-model":
            row["initialization"] = core["initializations"][1]
        elif fault == "operation-order":
            row["operation"]["index"] = 1
        elif fault == "operation-source":
            row["initialization"]["sha256"] = "f" * 64
        elif fault == "raw-path":
            row["arrays"]["path"] = str(Path(row["arrays"]["path"]).parent / "other.npz")
        elif fault == "geometry-level":
            row["record"]["level"]["ncoil"] = 512
        elif fault == "geometry-pairs":
            row["record"]["sampling_work"]["cc"]["completed"] -= 1
        else:
            row["geometry_work"]["surfaces"]["completed"] = 1

    intercept_json(monkeypatch, target, change)
    with pytest.raises(ValueError):
        audit(base)


def test_actual_saved_array_byte_tamper_is_rejected(monkeypatch, tmp_path):
    base = create(monkeypatch, tmp_path)
    ref = read_json(base["core"]["operations"][0])["arrays"]
    path = Path(ref["path"])
    original = path.read_bytes()
    path.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    with pytest.raises(ValueError, match="identity"):
        audit(base)


def test_source_reference_bytes_are_checked_before_raw_work(monkeypatch, base):
    changed = copy.deepcopy(base)
    changed["source"]["sha256"] = "f" * 64
    intercept_json(monkeypatch, base["reference"], lambda row: row.update(source=changed["source"]))
    with pytest.raises(ValueError, match="identity"):
        audit(changed)


def test_each_archive_is_rehashed_and_decoded(monkeypatch, base):
    refs = []

    def capture(reference):
        refs.append(copy.deepcopy(reference))
        return read_arrays(reference)

    monkeypatch.setattr(graph, "read_arrays", capture)
    audit(base)
    assert len(refs) == 28 and len({row["path"] for row in refs}) == 28


def test_guard_failure_stops_audit_before_reading_anything(monkeypatch, base):
    def fail():
        raise OSError("synthetic audit disk guard")

    def forbidden(reference):
        pytest.fail("read happened after failing initial guard")

    monkeypatch.setattr(graph, "read_json", forbidden)
    with pytest.raises(OSError):
        audit(base, fail)


def test_guard_after_last_read_still_required(base):
    calls = []
    audit(base, lambda: calls.append(True))
    total = len(calls)
    at = 0

    def last():
        nonlocal at
        at += 1
        if at == total:
            raise TimeoutError("synthetic audit guard after complete reconstruction")

    with pytest.raises(TimeoutError):
        audit(base, last)


def test_core_reference_must_be_explicit_and_named(base):
    changed = copy.deepcopy(base)
    changed["reference"]["sha256"] = hashlib.sha256(b"not the explicit result").hexdigest()
    with pytest.raises(ValueError):
        audit(changed)
