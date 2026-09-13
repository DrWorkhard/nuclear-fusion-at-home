"""Inspect the locked source archive and installed declarations; never build or install."""

import argparse
import hashlib
import importlib.metadata
import io
import json
import tarfile
import urllib.request
from pathlib import Path

from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic

URL = "https://files.pythonhosted.org/packages/34/b6/0370bb3af66a12098da06dc5843f3b349b7c83ccbdf7306e7afa6248b533/netcdf4-1.7.4.tar.gz"
SHA = "cdbfdc92d6f4d7192ca8506c9b3d4c1d9892969ff28d8e8e1fc97ca08bf12164"
MEMBERS = (
    "netcdf4-1.7.4/include/netCDF4.pxi",
    "netcdf4-1.7.4/setup.py",
    "netcdf4-1.7.4/src/netCDF4/_netCDF4.pyx",
    "netcdf4-1.7.4/pyproject.toml",
)


def archive_contents(payload, expected_sha=SHA):
    if hashlib.sha256(payload).hexdigest() != expected_sha:
        raise ValueError("locked netCDF4 source archive hash mismatch")
    with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
        names = archive.getnames()
        if any(names.count(name) != 1 for name in MEMBERS):
            raise ValueError("unique exact source members required")
        result = {}
        for name in MEMBERS:
            member = archive.getmember(name)
            if not member.isfile() or member.size > 2_000_000:
                raise ValueError("bounded ordinary source files required")
            result[name] = archive.extractfile(member).read()
    return result


def snippets(data, markers):
    return [
        dict(line=i + 1, text=line)
        for i, line in enumerate(data.decode().splitlines())
        if any(marker in line for marker in markers)
    ]


def ref(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable source inventory paths required")
    root = Path(__file__).resolve().parents[1]
    require_committed(root, Path(__file__))
    lock = (root / "uv.lock").read_text()
    if URL not in lock or "sha256:" + SHA not in lock:
        raise ValueError("source archive must match current lock")
    with urllib.request.urlopen(URL, timeout=30) as response:
        payload = response.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError("unexpected archive size")
    members = archive_contents(payload)
    numpy = importlib.metadata.distribution("numpy")
    netcdf = importlib.metadata.distribution("netCDF4")
    paths = dict(
        numpy_header=Path(numpy.locate_file("numpy/_core/include/numpy/ndarraytypes.h")),
        numpy_cython=Path(numpy.locate_file("numpy/__init__.cython-30.pxd")),
        installed_pyx=Path(netcdf.locate_file("netCDF4/_netCDF4.pyx")),
        wheel=Path(netcdf.locate_file("netcdf4-1.7.4.dist-info/WHEEL")),
        binary=Path(netcdf.locate_file("netCDF4/_netCDF4.abi3.so")),
    )
    markers = (
        "numpy.ndarray",
        "NPY_NO_DEPRECATED_API",
        "NPY_1_7_API_VERSION",
        "PyObject_HEAD",
        "tagPyArrayObject",
        "check_size",
    )
    native_sources = {
        key: dict(**ref(path), snippets=snippets(path.read_bytes(), markers))
        for key, path in paths.items()
        if key != "binary"
    }
    native_sources["binary"] = ref(paths["binary"])
    pxi, setup, pyx, _ = [members[name] for name in MEMBERS]
    manual_declaration = b"ctypedef extern class numpy.ndarray [object PyArrayObject]:"
    numpy_declaration = b"ctypedef class numpy.ndarray [object PyArrayObject, check_size ignore]:"
    checks = dict(
        installed_pyx_exact=paths["installed_pyx"].read_bytes() == pyx,
        opaque_array_macro=b'("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")' in setup,
        manual_array_without_check_size=manual_declaration in pxi,
        numpy_array_explicit_ignore=numpy_declaration in paths["numpy_cython"].read_bytes(),
    )
    args.raw.mkdir(parents=True)
    archive_path = args.raw / "netcdf4-1.7.4.tar.gz"
    with archive_path.open("xb") as stream:
        stream.write(payload)
    report = dict(
        repository=git_state(root),
        code=ref(Path(__file__)),
        lock=ref(root / "uv.lock"),
        archive=dict(**ref(archive_path), url=URL, size=len(payload)),
        members={
            name: dict(
                sha256=hashlib.sha256(data).hexdigest(),
                size=len(data),
                snippets=snippets(data, markers),
            )
            for name, data in members.items()
        },
        installed=native_sources,
        versions=dict(numpy=numpy.version, netCDF4=netcdf.version),
        checks=checks,
        all_pass=all(checks.values()),
        status="completed",
        new_physical_calls=0,
        environment_changed=False,
        native_abi_certified=False,
        strict_import_repaired=False,
        cython_reference="https://docs.cython.org/en/latest/src/userguide/extension_types.html#name-specification-clause",
    )
    write_json_atomic(args.output, report)
    print(json.dumps(dict(all_pass=report["all_pass"], environment_changed=False)))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
