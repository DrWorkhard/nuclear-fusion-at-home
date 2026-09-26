"""Exclusive POSIX raw-result storage; references prove bytes, not physical truth.

Owned single-writer directory only. Failed tails remain; no recovery or overwrite.
The caller journals returned references only after the persistence barriers pass.
"""

import hashlib
import io
import json
import math
import os
import re
import struct
import zipfile
from pathlib import Path

import numpy as np

from fusion_baselines.protected_search_journal import (
    MAX_RECORD_BYTES as MAX_JSON_BYTES,
)
from fusion_baselines.protected_search_journal import (
    _encode,
    _sync_directory,
    _unique_object,
)

MAX_BYTES = 64 * 1024**2
MAX_ARRAYS = 64
_STEM = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}\Z")
_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,95}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _arrays(values):
    require(type(values) is dict and 0 < len(values) <= MAX_ARRAYS,
            "nonempty bounded named array mapping required")
    result, size = {}, 0
    for key, value in values.items():
        require(type(key) is str and _KEY.fullmatch(key), "plain named array keys required")
        array = np.asarray(value)
        require(array.dtype.kind in "iuf" and array.ndim <= 8,
                "real numeric arrays of at most eight dimensions required")
        size += array.nbytes
        require(size <= MAX_BYTES, "array byte limit exceeded")
        require(np.isfinite(array).all(), "finite numeric arrays required")
        result[key] = array.copy(order="C")
    return result


def _array_bytes(values):
    values = _arrays(values)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for key in sorted(values):
            item = io.BytesIO()
            np.lib.format.write_array(item, values[key], allow_pickle=False)
            # Fixed ZIP metadata makes same-array snapshots byte reproducible.
            archive.writestr(zipfile.ZipInfo(key + ".npy"), item.getvalue())
    result = output.getvalue()
    require(len(result) <= MAX_BYTES, "snapshot byte limit exceeded")
    return result


class SnapshotStore:
    """A fresh directory; all validation or I/O failures poison this instance."""

    def __init__(self, directory):
        self.directory = Path(directory).absolute()
        self._failed = False
        self.directory.mkdir(exist_ok=False)
        _sync_directory(self.directory.parent)

    def _write(self, name, payload, suffix, encode):
        if self._failed:
            raise RuntimeError("snapshot store failed; preserve it and use a fresh run")
        try:
            require(type(name) is str and _STEM.fullmatch(name), "simple snapshot name required")
            raw = encode(payload)
            require(len(raw) <= MAX_BYTES, "snapshot byte limit exceeded")
            path = self.directory / (name + suffix)
            with path.open("xb") as stream:
                if stream.write(raw) != len(raw):
                    raise OSError("short snapshot write")
                stream.flush()
                os.fsync(stream.fileno())
            _sync_directory(self.directory)
            return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        except BaseException:
            self._failed = True
            raise

    def json(self, name, payload):
        """Finite canonical UTF-8 JSON, with the journal's 8 MiB/depth bounds."""
        return self._write(name, payload, ".json", _encode)

    def arrays(self, name, values):
        """Finite named arrays in deterministic uncompressed NPZ, never pickle."""
        return self._write(name, values, ".npz", _array_bytes)


def checked_bytes(reference, suffix, *, max_bytes=None):
    """Read a bounded regular local file with externally supplied byte identity."""
    require(type(reference) is dict and set(reference) == {"path", "sha256", "bytes"},
            "exact snapshot reference required")
    name, digest, size = (reference[k] for k in ("path", "sha256", "bytes"))
    require(type(name) is str and Path(name).is_absolute(), "absolute snapshot path required")
    require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest),
            "lowercase SHA256 required")
    limit = MAX_BYTES if max_bytes is None else min(max_bytes, MAX_BYTES)
    require(type(size) is int and 0 < size <= limit, "bounded snapshot byte count required")
    path = Path(name)
    require(path.suffix == suffix and not path.is_symlink() and path.is_file(),
            "regular nonsymlink snapshot of expected type required")
    with path.open("rb") as stream:
        raw = stream.read(size + 1)
    require(len(raw) == size and hashlib.sha256(raw).hexdigest() == digest,
            "snapshot identity mismatch")
    return raw


def read_json(reference):
    raw = checked_bytes(reference, ".json", max_bytes=MAX_JSON_BYTES)
    value = json.loads(raw, object_pairs_hook=_unique_object)
    require(_encode(value) == raw, "finite canonical JSON snapshot required")
    return value


def read_arrays(reference):
    raw = checked_bytes(reference, ".npz")
    # Our writer cannot need ZIP64 (<64 MiB, <=64 files), comments or extra
    # records. Bound the central directory before ZipFile eagerly allocates it.
    require(len(raw) >= 22, "complete ZIP end record required")
    require(raw[-42:-38] != b"PK\x06\x07", "ZIP64 metadata is not part of the snapshot format")
    signature, disk, start_disk, disk_count, count, size, offset, comment = struct.unpack(
        "<4s4H2LH", raw[-22:])
    require(signature == b"PK\x05\x06" and disk == start_disk == comment == 0
            and disk_count == count and 0 < count <= MAX_ARRAYS
            and size <= MAX_ARRAYS * (46 + 100) and offset + size == len(raw) - 22,
            "bounded canonical ZIP directory required")
    position, end = offset, offset + size
    for _ in range(count):
        require(position + 46 <= end and raw[position:position + 4] == b"PK\x01\x02",
                "complete canonical ZIP directory entry required")
        name_size, extra_size, comment_size = struct.unpack_from("<HHH", raw, position + 28)
        require(0 < name_size <= 100 and extra_size == comment_size == 0,
                "bounded canonical ZIP directory metadata required")
        position += 46 + name_size
        require(position <= end, "complete ZIP entry name required")
    require(position == end, "declared ZIP entry count must match actual directory")
    with zipfile.ZipFile(io.BytesIO(raw), "r") as archive:
        infos = archive.infolist()
        require(len(infos) == count and len({r.filename for r in infos}) == len(infos),
                "bounded unique array entries required")
        require(all(r.compress_type == zipfile.ZIP_STORED and not r.flag_bits & 1
                    and r.file_size == r.compress_size for r in infos)
                and sum(r.file_size for r in infos) <= MAX_BYTES,
                "uncompressed bounded unencrypted arrays required")
        values = {}
        for info in infos:
            require(info.filename.endswith(".npy") and _KEY.fullmatch(info.filename[:-4]),
                    "plain named NPY entries required")
            stream = io.BytesIO(archive.read(info))
            version = np.lib.format.read_magic(stream)
            require(version in ((1, 0), (2, 0)), "registered NPY header version required")
            header = (np.lib.format.read_array_header_1_0 if version == (1, 0)
                      else np.lib.format.read_array_header_2_0)
            shape, fortran, dtype = header(stream, max_header_size=4096)
            require(dtype.kind in "iuf" and len(shape) <= 8
                    and all(type(n) is int and n >= 0 for n in shape),
                    "real bounded numeric array header required")
            count = math.prod(shape)
            require(count * dtype.itemsize <= MAX_BYTES, "array byte limit exceeded")
            data = stream.read()
            require(len(data) == count * dtype.itemsize, "exact array payload length required")
            # Verify header-declared size before allocating any numerical array.
            array = np.frombuffer(data, dtype=dtype).reshape(shape, order="F" if fortran else "C")
            values[info.filename[:-4]] = array
    # Canonical archive identity also rejects extra files/headers/trailing bytes.
    require(_array_bytes(values) == raw, "canonical numeric array archive required")
    return values
