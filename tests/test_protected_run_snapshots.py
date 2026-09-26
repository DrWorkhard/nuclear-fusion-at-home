"""Small owned temporary files, injected failures; no physical calculations."""

import copy
import hashlib
import io
import json
import math
import struct
import zipfile
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines import protected_run_snapshots as store
from fusion_baselines.protected_search_journal import EventJournal, read_events


def fixture(tmp_path):
    return store.SnapshotStore(tmp_path / "raw")


def ref(path):
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def test_json_and_arrays_roundtrip_private_and_deterministic(tmp_path):
    writer = fixture(tmp_path)
    metadata = {"x": [-0.0, 1.5], "label": "Spule → σ"}
    first = writer.json("state-000", metadata)
    metadata["x"][0] = 5
    assert math.copysign(1, store.read_json(first)["x"][0]) == -1
    values = {"field": np.arange(12, dtype=float).reshape(4, 3), "x": np.array([-0.0])}
    raw = writer.arrays("arrays-000", values)
    repeat = writer.arrays("arrays-001", dict(reversed(list(values.items()))))
    assert raw["sha256"] == repeat["sha256"]
    values["field"][:] = 88
    decoded = store.read_arrays(raw)
    np.testing.assert_array_equal(decoded["field"], np.arange(12).reshape(4, 3))
    assert math.copysign(1, decoded["x"][0]) == -1
    with np.load(raw["path"], allow_pickle=False) as compatible:
        np.testing.assert_array_equal(compatible["field"], decoded["field"])
    log = EventJournal(tmp_path / "journal")
    receipt = log(dict(metadata=first, arrays=raw, physical_admission=False))
    assert read_events(tmp_path / "journal", receipt)[0]["arrays"] == raw


def test_fresh_directory_and_no_overwrite(tmp_path):
    writer = fixture(tmp_path)
    with pytest.raises(FileExistsError):
        fixture(tmp_path)
    old = writer.json("one", {"x": 1})
    with pytest.raises(FileExistsError):
        writer.json("one", {"x": 2})
    assert store.read_json(old) == {"x": 1}
    with pytest.raises(RuntimeError, match="failed"):
        writer.json("two", {"x": 2})


@pytest.mark.parametrize("name", ["../escape", "a/b", "", ".", "x.json", "a" * 97, 1])
def test_names_fail_closed(tmp_path, name):
    writer = fixture(tmp_path)
    with pytest.raises(ValueError, match="name"):
        writer.json(name, {})
    with pytest.raises(RuntimeError):
        writer.arrays("later", {"x": [1.]})
    assert list(writer.directory.iterdir()) == []


@pytest.mark.parametrize("values", [{}, {"bad/key": [1.]}, {"x": [float("nan")]},
    {"x": [float("inf")]}, {"x": [True]}, {"x": ["value"]}, {"x": [complex(1)]},
    {"x": np.array([object()], dtype=object)}, {"x": np.ones((1,) * 9)},
])
def test_bad_arrays_fail_before_writes(tmp_path, values):
    writer = fixture(tmp_path)
    with pytest.raises(ValueError):
        writer.arrays("bad", values)
    assert not list(writer.directory.iterdir())
    with pytest.raises(RuntimeError):
        writer.json("later", {})


@pytest.mark.parametrize("fault", ["open", "short", "flush", "close", "file-sync", "dir-sync",
                                   "interrupt"])
def test_io_faults_poison_store_and_keep_prefix(tmp_path, monkeypatch, fault):
    writer = fixture(tmp_path)
    old = writer.json("good", {"status": "complete"})
    original_open = Path.open

    class Broken:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()
            if fault == "close":
                raise OSError("injected close")

        def write(self, data):
            return self.stream.write(data[:4] if fault == "short" else data)

        def flush(self):
            if fault == "flush":
                raise OSError("injected flush")
            self.stream.flush()

        def fileno(self):
            return self.stream.fileno()

    def opening(path, mode="r", *args, **kwargs):
        if path.name == "bad.npz" and mode == "xb":
            if fault == "open":
                raise OSError("injected open")
            return Broken(original_open(path, mode, *args, **kwargs))
        return original_open(path, mode, *args, **kwargs)

    def fail(*args):
        if fault == "interrupt":
            raise KeyboardInterrupt("injected interrupt")
        raise OSError("injected fsync")

    monkeypatch.setattr(Path, "open", opening)
    if fault == "file-sync":
        monkeypatch.setattr(store.os, "fsync", fail)
    if fault in ("dir-sync", "interrupt"):
        monkeypatch.setattr(store, "_sync_directory", fail)
    with pytest.raises(KeyboardInterrupt if fault == "interrupt" else OSError):
        writer.arrays("bad", {"field": np.ones((3, 3))})
    assert store.read_json(old) == {"status": "complete"}
    before = {p.name: p.read_bytes() for p in writer.directory.iterdir()}
    with pytest.raises(RuntimeError):
        writer.json("retry", {})
    assert before == {p.name: p.read_bytes() for p in writer.directory.iterdir()}


@pytest.mark.parametrize("fault", ["hash", "size", "bool-size", "relative", "symlink", "mutate",
                                   "extra-key", "missing", "wrong-suffix"])
def test_bad_reference_rejected(tmp_path, fault):
    writer = fixture(tmp_path)
    reference = writer.json("good", {"x": 1})
    path = Path(reference["path"])
    if fault == "hash":
        reference["sha256"] = "0" * 64
    elif fault == "size":
        reference["bytes"] += 1
    elif fault == "bool-size":
        reference["bytes"] = True
    elif fault == "relative":
        reference["path"] = "good.json"
    elif fault == "symlink":
        link = tmp_path / "link.json"
        link.symlink_to(path)
        reference["path"] = str(link)
    elif fault == "mutate":
        path.write_bytes(b"corrupt")
    elif fault == "extra-key":
        reference["admitted"] = True
    elif fault == "missing":
        path.unlink()
    else:
        reference["path"] = str(tmp_path / "other.npz")
    with pytest.raises(ValueError):
        store.read_json(reference)


@pytest.mark.parametrize("payload", [b'{"x":NaN}\n', b'{"x":1,"x":2}\n', b'{ "x": 1 }'])
def test_correct_hash_does_not_admit_bad_json(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_bytes(payload)
    with pytest.raises(ValueError):
        store.read_json(ref(path))


@pytest.mark.parametrize("fault", ["pickle", "nan", "compressed", "name", "extra-array-bytes",
                                   "extra-zip-bytes"])
def test_correct_hash_does_not_admit_bad_archive(tmp_path, fault):
    data = io.BytesIO()
    array = (np.array([object()]) if fault == "pickle"
             else np.array([np.nan if fault == "nan" else 1.]))
    np.lib.format.write_array(data, array, allow_pickle=True)
    raw = data.getvalue() + (b"trailing" if fault == "extra-array-bytes" else b"")
    path = tmp_path / "bad.npz"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../x.npy" if fault == "name" else "x.npy", raw,
                         compress_type=zipfile.ZIP_DEFLATED if fault == "compressed"
                         else zipfile.ZIP_STORED)
    if fault == "extra-zip-bytes":
        path.write_bytes(path.read_bytes() + b"trailing")
    with pytest.raises(ValueError):
        store.read_arrays(ref(path))


def test_storage_caps(tmp_path, monkeypatch):
    writer = fixture(tmp_path)
    monkeypatch.setattr(store, "MAX_ARRAYS", 1)
    with pytest.raises(ValueError, match="mapping"):
        writer.arrays("many", {"a": [1.], "b": [2.]})
    other = store.SnapshotStore(tmp_path / "other")
    monkeypatch.setattr(store, "MAX_BYTES", 100)
    with pytest.raises(ValueError, match="limit"):
        other.arrays("large", {"x": np.ones(101)})
    third = store.SnapshotStore(tmp_path / "third")
    with pytest.raises(ValueError, match="limit"):
        third.arrays("header", {"x": [1.]})


def test_header_cannot_allocate_more_than_recorded_bytes(tmp_path, monkeypatch):
    data = io.BytesIO()
    np.lib.format.write_array_header_1_0(
        data, dict(descr="<f8", fortran_order=False, shape=(10**12,)))
    path = tmp_path / "huge-header.npz"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("x.npy", data.getvalue())

    def forbidden(*args, **kwargs):
        pytest.fail("oversized header reached numerical allocation")

    monkeypatch.setattr(store.np, "frombuffer", forbidden)
    with pytest.raises(ValueError, match="byte limit"):
        store.read_arrays(ref(path))


def test_json_size_limit_precedes_parser(tmp_path, monkeypatch):
    writer = fixture(tmp_path)
    reference = writer.json("over-small-test-cap", {"x": "1234567890"})
    monkeypatch.setattr(store, "MAX_JSON_BYTES", 10)

    def forbidden(*args, **kwargs):
        pytest.fail("oversized JSON reached parser")

    monkeypatch.setattr(store.json, "loads", forbidden)
    with pytest.raises(ValueError, match="byte count"):
        store.read_json(reference)


def test_entry_limit_precedes_zipfile_directory_allocation(tmp_path, monkeypatch):
    path = tmp_path / "too-many.npz"
    with zipfile.ZipFile(path, "w") as archive:
        for k in range(65):
            archive.writestr(f"x{k}.npy", b"")

    def forbidden(*args, **kwargs):
        pytest.fail("oversized central directory reached ZipFile")

    monkeypatch.setattr(store.zipfile, "ZipFile", forbidden)
    with pytest.raises(ValueError, match="ZIP directory"):
        store.read_arrays(ref(path))


def test_false_directory_count_rejected_before_zipfile(tmp_path, monkeypatch):
    path = tmp_path / "false-count.npz"
    with zipfile.ZipFile(path, "w") as archive:
        for k in range(65):
            archive.writestr(f"x{k}.npy", b"")
    raw = bytearray(path.read_bytes())
    struct.pack_into("<HH", raw, len(raw) - 22 + 8, 1, 1)
    path.write_bytes(raw)

    def forbidden(*args, **kwargs):
        pytest.fail("false directory count reached ZipFile")

    monkeypatch.setattr(store.zipfile, "ZipFile", forbidden)
    with pytest.raises(ValueError, match="entry count"):
        store.read_arrays(ref(path))


def test_zip64_cannot_override_preflight_directory(tmp_path, monkeypatch):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for k in range(65):
            archive.writestr(f"x{k}.npy", b"")
    original = output.getvalue()
    _, _, _, n1, n2, size, offset, _ = struct.unpack("<4s4H2LH", original[-22:])
    body = original[:-22]
    fake = bytearray(body[offset:offset + 46])
    struct.pack_into("<HHH", fake, 28, 76, 0, 0)
    end64 = struct.pack("<4sQ2H2L4Q", b"PK\x06\x06", 44, 45, 45, 0, 0,
                        n1, n2, size + 46, offset)
    locator = struct.pack("<4sLQL", b"PK\x06\x07", 0, len(body) + 46, 1)
    end = struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, 1, 1, 122, len(body), 0)
    raw = body + fake + end64 + locator + end
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert len(archive.infolist()) == 66
    path = tmp_path / "zip64-override.npz"
    path.write_bytes(raw)

    def forbidden(*args, **kwargs):
        pytest.fail("ZIP64 override reached standard eager directory parser")

    monkeypatch.setattr(store.zipfile, "ZipFile", forbidden)
    with pytest.raises(ValueError, match="ZIP64"):
        store.read_arrays(ref(path))


def test_duplicate_entries_fail(tmp_path):
    data = io.BytesIO()
    np.lib.format.write_array(data, np.array([1.]), allow_pickle=False)
    path = tmp_path / "duplicate.npz"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("x.npy", data.getvalue())
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("x.npy", data.getvalue())
    with pytest.raises(ValueError, match="unique"):
        store.read_arrays(ref(path))


@pytest.mark.parametrize("value", [np.asfortranarray(np.arange(6.).reshape(2, 3)),
    np.array([1., -0.], dtype=">f8"), np.array(7, dtype="i2"), np.array([], dtype="u1"),
])
def test_valid_numeric_layouts(tmp_path, value):
    writer = fixture(tmp_path)
    reference = writer.arrays("layout", {"x": value})
    got = store.read_arrays(reference)["x"]
    assert got.shape == value.shape and got.dtype == value.dtype
    assert got.tobytes(order="C") == value.tobytes(order="C")


def test_creation_sync_failure_is_not_recoverable(tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("creation sync failed")

    monkeypatch.setattr(store, "_sync_directory", fail)
    with pytest.raises(OSError):
        fixture(tmp_path)
    assert (tmp_path / "raw").is_dir()
    with pytest.raises(FileExistsError):
        fixture(tmp_path)


def test_physical_claim_is_data_not_endorsement(tmp_path):
    writer = fixture(tmp_path)
    payload = dict(physical_admission=True, fabricated=True)
    reference = writer.json("untrusted-claim", payload)
    assert store.read_json(copy.deepcopy(reference)) == payload
    assert json.loads(Path(reference["path"]).read_text()) == payload
