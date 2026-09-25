"""Real tiny-file I/O and synthetic failures, not native coil calculations."""

import hashlib
import json
import math
from contextlib import contextmanager
from pathlib import Path

import pytest
from test_protected_coil_search import certificate, linear_run

from fusion_baselines import protected_search_journal as storage
from fusion_baselines.protected_coil_search_audit import audit


def journal(tmp_path):
    path = tmp_path / "events"
    return path, storage.EventJournal(path)


def test_roundtrip_unicode_signed_zero_and_private_data(tmp_path):
    path, record = journal(tmp_path)
    payload = {"label": "Spule → σ", "values": [-0.0, 1, True, None]}
    receipt = record(payload)
    payload["values"][0] = 99
    received = storage.read_events(path, receipt)
    assert received[0]["label"] == "Spule → σ"
    assert math.copysign(1, received[0]["values"][0]) == -1
    assert receipt["head_sha256"] == hashlib.sha256((path / "000000.json").read_bytes()).hexdigest()
    receipt["records"] = 99
    assert record.receipt["records"] == 1


def test_empty_and_nonempty_journal_never_overwritten(tmp_path):
    path, record = journal(tmp_path)
    assert storage.read_events(path, record.receipt) == []
    with pytest.raises(FileExistsError):
        storage.EventJournal(path)
    record({"event": "first"})
    original = (path / "000000.json").read_bytes()
    with pytest.raises(FileExistsError):
        storage.EventJournal(path)
    assert (path / "000000.json").read_bytes() == original


@pytest.mark.parametrize("payload", [float("nan"), float("inf"), object(), (1, 2),
                                     {1: "not a string"}, 10**400])
def test_invalid_payload_poisons_writer_without_touching_prefix(tmp_path, payload):
    path, record = journal(tmp_path)
    receipt = record({"event": "first"})
    with pytest.raises(ValueError):
        record(payload)
    with pytest.raises(RuntimeError, match="failed"):
        record({"event": "must not write"})
    assert storage.read_events(path, receipt) == [{"event": "first"}]


@pytest.mark.parametrize("key,value", [("records", True), ("records", -1), ("records", 2049),
    ("schema_version", True), ("head_sha256", "a" * 64), ("head_sha256", []),
])
def test_bad_empty_receipt_fails(tmp_path, key, value):
    path, record = journal(tmp_path)
    receipt = dict(record.receipt, **{key: value})
    with pytest.raises(ValueError):
        storage.read_events(path, receipt)


@pytest.mark.parametrize("fault", ["bytes", "missing", "extra", "partial", "duplicate", "nan",
    "reencoded", "index", "version", "previous", "head", "schema", "symlink", "directory",
])
def test_changed_journal_fails(tmp_path, fault):
    path, record = journal(tmp_path)
    record({"first": 1})
    receipt = record({"second": 2})
    target = path / "000001.json"
    raw = target.read_bytes()
    document = json.loads(raw)
    if fault == "bytes":
        target.write_bytes(raw.replace(b'"second":2', b'"second":3'))
    elif fault == "missing":
        target.unlink()
    elif fault == "extra":
        (path / "000002.json").write_bytes(raw)
    elif fault == "partial":
        target.write_bytes(raw[:20])
    elif fault == "duplicate":
        target.write_bytes(raw.replace(b'"index":1', b'"index":1,"index":1'))
    elif fault == "nan":
        target.write_bytes(raw.replace(b'"second":2', b'"second":NaN'))
    elif fault == "reencoded":
        target.write_text(json.dumps(document, indent=2), encoding="utf-8")
    elif fault in ("index", "version", "previous", "schema"):
        if fault == "index":
            document["index"] = True
        elif fault == "version":
            document["schema_version"] = True
        elif fault == "previous":
            document["previous_sha256"] = "0" * 64
        else:
            document["extra"] = False
        target.write_bytes(storage._encode(document))
    elif fault == "head":
        receipt["head_sha256"] = "0" * 64
    elif fault == "symlink":
        other = tmp_path / "other.json"
        other.write_bytes(raw)
        target.unlink()
        target.symlink_to(other)
    else:
        target.unlink()
        target.mkdir()
    with pytest.raises((ValueError, OSError)):
        storage.read_events(path, receipt)


@pytest.mark.parametrize("fault", ["open", "short-write", "flush", "close",
                                   "file-fsync", "directory-fsync"])
def test_io_failure_preserves_prefix_and_poisoned_writer(tmp_path, monkeypatch, fault):
    path, record = journal(tmp_path)
    receipt = record({"event": "good"})
    first = (path / "000000.json").read_bytes()
    original_open = Path.open

    class BrokenStream:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()
            if fault == "close":
                raise OSError("injected close failure")

        def write(self, data):
            if fault == "short-write":
                return self.stream.write(data[:10])
            return self.stream.write(data)

        def flush(self):
            if fault == "flush":
                raise OSError("injected flush failure")
            return self.stream.flush()

        def fileno(self):
            return self.stream.fileno()

    def opening(p, mode="r", *args, **kwargs):
        if p == path / "000001.json" and mode == "xb":
            if fault == "open":
                raise OSError("injected open failure")
            return BrokenStream(original_open(p, mode, *args, **kwargs))
        return original_open(p, mode, *args, **kwargs)

    def fail(*args):
        raise OSError("injected fsync failure")

    monkeypatch.setattr(Path, "open", opening)
    if fault == "file-fsync":
        monkeypatch.setattr(storage.os, "fsync", fail)
    elif fault == "directory-fsync":
        monkeypatch.setattr(storage, "_sync_directory", fail)
    with pytest.raises(OSError):
        record({"event": "failure"})
    assert record.receipt == receipt
    assert (path / "000000.json").read_bytes() == first
    tail_before = {p.name: p.read_bytes() for p in path.iterdir()}
    with pytest.raises(RuntimeError):
        record({"event": "never"})
    assert {p.name: p.read_bytes() for p in path.iterdir()} == tail_before
    if fault == "open":
        assert storage.read_events(path, receipt) == [{"event": "good"}]
    else:
        with pytest.raises(ValueError, match="sequence"):
            storage.read_events(path, receipt)


def test_existing_tail_not_overwritten(tmp_path):
    path, record = journal(tmp_path)
    target = path / "000000.json"
    target.write_bytes(b"retained partial prior write")
    with pytest.raises(FileExistsError):
        record({"event": "attempt"})
    assert target.read_bytes() == b"retained partial prior write"
    with pytest.raises(RuntimeError):
        record({"event": "retry"})


def test_caps_and_deep_payload(tmp_path, monkeypatch):
    path, record = journal(tmp_path)
    monkeypatch.setattr(storage, "MAX_RECORDS", 1)
    receipt = record({"event": "one"})
    with pytest.raises(ValueError, match="record limit"):
        record({"event": "two"})
    assert len(storage.read_events(path, receipt)) == 1
    other = storage.EventJournal(tmp_path / "deep")
    payload = []
    for _ in range(66):
        payload = [payload]
    with pytest.raises(ValueError, match="nesting"):
        other(payload)
    capped = storage.EventJournal(tmp_path / "capped")
    monkeypatch.setattr(storage, "MAX_RECORD_BYTES", 100)
    with pytest.raises(ValueError, match="byte limit"):
        capped({"large": "a" * 101})


@pytest.mark.parametrize("size", [198, 360])
def test_controller_journal_reader_and_separate_auditor(tmp_path, size):
    path, record = journal(tmp_path)
    seed, report, _ = linear_run(size, record=record)
    events = storage.read_events(path, record.receipt)
    verdict = audit(seed.tolist(), report["initial"], report, events)
    assert len(events) == 82 and verdict["control_flow_pass"], verdict
    assert not verdict["physical_admission"]


def test_failed_reservation_prevents_callback_work(tmp_path, monkeypatch):
    path, record = journal(tmp_path)
    calls = []
    original = Path.open

    def opening(p, mode="r", *args, **kwargs):
        if p.name == "000001.json" and mode == "xb":
            raise OSError("reservation unavailable")
        return original(p, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opening)
    with pytest.raises(OSError, match="reservation unavailable"):
        linear_run(record=record, certify=lambda a, b: calls.append(1) or certificate())
    assert not calls
    events = storage.read_events(path, record.receipt)
    assert [e["event"] for e in events] == ["search_started"]


def test_creation_sync_failure_keeps_directory_and_refuses_resume(tmp_path, monkeypatch):
    path = tmp_path / "new"

    def fail(*args):
        raise OSError("creation sync unavailable")

    monkeypatch.setattr(storage, "_sync_directory", fail)
    with pytest.raises(OSError, match="creation sync"):
        storage.EventJournal(path)
    assert path.is_dir()
    with pytest.raises(FileExistsError):
        storage.EventJournal(path)


@pytest.mark.parametrize("bad", [None, {}, {"schema_version": 1, "records": 0,
                                           "head_sha256": None, "extra": False}])
def test_exact_receipt_schema(tmp_path, bad):
    path, _ = journal(tmp_path)
    with pytest.raises(ValueError, match="receipt schema"):
        storage.read_events(path, bad)


def test_symlink_directory_and_oversized_read_rejected(tmp_path, monkeypatch):
    path, record = journal(tmp_path)
    receipt = record({"text": "large enough to exceed a tiny test cap"})
    link = tmp_path / "alias"
    link.symlink_to(path, target_is_directory=True)
    with pytest.raises(ValueError, match="real journal"):
        storage.read_events(link, receipt)
    monkeypatch.setattr(storage, "MAX_RECORD_BYTES", 40)
    with pytest.raises(ValueError, match="byte limit"):
        storage.read_events(path, receipt)


def test_sync_occurs_before_acknowledgement_and_interrupt_poisons(tmp_path, monkeypatch):
    path, record = journal(tmp_path)
    empty = record.receipt
    seen = []

    def interrupt(directory):
        assert directory == path
        # Bytes have been written/closed, but the receipt is not advanced yet.
        assert (path / "000000.json").is_file()
        assert record.receipt == empty
        seen.append("directory sync")
        raise KeyboardInterrupt

    monkeypatch.setattr(storage, "_sync_directory", interrupt)
    with pytest.raises(KeyboardInterrupt):
        record({"event": "attempt"})
    assert seen == ["directory sync"] and record.receipt == empty
    with pytest.raises(RuntimeError):
        record({"event": "retry"})
    with pytest.raises(ValueError, match="sequence"):
        storage.read_events(path, empty)


def test_hash_integrity_does_not_authenticate_physics_or_author(tmp_path):
    path, record = journal(tmp_path)
    receipt = record({"physical_admission": True, "invented": "not verified"})
    # Storage faithfully returns arbitrary assertions; only the scientific auditor
    # can evaluate them, against a separately trusted receipt/source/checkpoint.
    assert storage.read_events(path, receipt)[0]["physical_admission"] is True


def test_extra_file_rejected_without_unbounded_directory_enumeration(tmp_path, monkeypatch):
    path, record = journal(tmp_path)

    def entries():
        yield object()  # Count must fail before even inspecting this unexpected entry.
        pytest.fail("reader consumed more than receipt count plus one entry")

    @contextmanager
    def directory(*args):
        yield entries()

    monkeypatch.setattr(storage.os, "scandir", directory)
    with pytest.raises(ValueError, match="sequence"):
        storage.read_events(path, record.receipt)
