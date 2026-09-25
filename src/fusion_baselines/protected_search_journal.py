"""POSIX, single-writer event persistence; integrity is not scientific admission.

Receipts must be bound by the caller's source/checkpoint protocol. Failed tails
are preserved and cannot be resumed. No field work, path execution or network.
"""

import hashlib
import json
import math
import os
from pathlib import Path

MAX_RECORD_BYTES = 8 * 1024**2
MAX_RECORDS = 2048
MAX_DEPTH = 64


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _finite(value, depth=0):
    _require(depth <= MAX_DEPTH, "JSON nesting limit exceeded")
    if type(value) is dict:
        _require(all(type(k) is str for k in value), "JSON keys must be strings")
        for item in value.values():
            _finite(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _finite(item, depth + 1)
    elif type(value) in (int, float):
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        _require(finite, "finite JSON numbers required")
    else:
        _require(value is None or type(value) in (str, bool), "plain JSON payload required")


def _encode(value):
    _finite(value)
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    _require(len(raw) <= MAX_RECORD_BYTES, "record byte limit exceeded")
    return raw


def _sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


class EventJournal:
    """Synchronous record callback in a fresh directory; never resume or overwrite.

    Single-threaded owned research workspace only, not a concurrent filesystem
    security boundary. File/directory fsync does not certify hardware power-loss
    behavior. A partial tail after failure is evidence, not a completed event.
    """

    def __init__(self, directory):
        self._directory = Path(directory)
        self._failed, self._count, self._head = False, 0, None
        self._directory.mkdir(exist_ok=False)
        _sync_directory(self._directory.parent)

    @property
    def receipt(self):
        """Last acknowledged prefix; not proof that no later work was attempted."""
        return dict(schema_version=1, records=self._count, head_sha256=self._head)

    def __call__(self, payload):
        if self._failed:
            raise RuntimeError("journal writer failed; preserve it and use a fresh run")
        try:
            _require(self._count < MAX_RECORDS, "journal record limit exceeded")
            raw = _encode(dict(schema_version=1, index=self._count,
                               previous_sha256=self._head, payload=payload))
            path = self._directory / f"{self._count:06d}.json"
            with path.open("xb") as stream:
                if stream.write(raw) != len(raw):
                    raise OSError("short event write")
                stream.flush()
                os.fsync(stream.fileno())
            _sync_directory(self._directory)
            # Acknowledgement follows every persistence barrier, including close.
            self._head, self._count = _digest(raw), self._count + 1
            return self.receipt
        except BaseException:
            self._failed = True
            raise


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def read_events(directory, receipt):
    """Verify a complete supplied prefix; a partial/extra tail fails closed.

    No head is guessed from files. Caller must bind the receipt independently;
    this neither authenticates its author nor certifies callback/physics truth.
    """
    _require(type(receipt) is dict and set(receipt) == {
        "schema_version", "records", "head_sha256"}, "exact receipt schema required")
    _require(type(receipt["schema_version"]) is int and receipt["schema_version"] == 1,
             "receipt schema version must be integer 1")
    count, head = receipt["records"], receipt["head_sha256"]
    _require(type(count) is int and 0 <= count <= MAX_RECORDS, "bounded integer record count")
    _require(head is None if count == 0 else (
        type(head) is str and len(head) == 64 and all(c in "0123456789abcdef" for c in head)),
        "receipt head must match empty/nonempty prefix")
    directory = Path(directory)
    _require(not directory.is_symlink() and directory.is_dir(), "real journal directory required")
    names = [f"{i:06d}.json" for i in range(count)]
    found = []
    with os.scandir(directory) as entries:
        for entry in entries:
            _require(len(found) < count, "exact journal file sequence")
            found.append(entry.name)
    _require(sorted(found) == names, "exact journal file sequence")
    events, previous = [], None
    for index, name in enumerate(names):
        path = directory / name
        _require(not path.is_symlink() and path.is_file(), "regular nonsymlink event required")
        with path.open("rb") as stream:
            raw = stream.read(MAX_RECORD_BYTES + 1)
        _require(len(raw) <= MAX_RECORD_BYTES, "record byte limit exceeded")
        record = json.loads(raw, object_pairs_hook=_unique_object)
        _require(type(record) is dict and set(record) == {
            "schema_version", "index", "previous_sha256", "payload"}, "exact event schema")
        _require(type(record["schema_version"]) is int and record["schema_version"] == 1
                 and type(record["index"]) is int and record["index"] == index,
                 "exact event version/index")
        _require(record["previous_sha256"] == previous, "broken previous-record hash")
        _require(_encode(record) == raw, "finite canonical UTF-8 JSON event required")
        previous = _digest(raw)
        events.append(record["payload"])
    _require(previous == head, "receipt head mismatch")
    return events
