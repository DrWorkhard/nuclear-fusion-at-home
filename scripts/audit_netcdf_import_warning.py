"""Record default/visible/strict native import behavior without changing the environment."""

import argparse
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable import diagnostic required")
    root = Path(__file__).resolve().parents[1]
    cases = []
    for label, action in (
        ("numpy_default_filter", None),
        ("visible_after_numpy", "always"),
        ("strict_after_numpy", "error"),
    ):
        code = "import numpy, warnings; "
        if action is not None:
            code += f"warnings.simplefilter({action!r}, RuntimeWarning); "
        code += "import netCDF4; print(numpy.__version__, netCDF4.__version__)"
        command = [sys.executable, "-c", code]
        process = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        cases.append(
            dict(
                name=label,
                command=command,
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
        )
    marker = "numpy.ndarray size changed"
    reproduced = (
        [c["returncode"] for c in cases] == [0, 0, 1]
        and marker not in cases[0]["stderr"]
        and all(marker in c["stderr"] for c in cases[1:])
    )
    sources = [Path(importlib.metadata.distribution("numpy").locate_file("numpy/__init__.py"))]
    dist = importlib.metadata.distribution("netCDF4")
    sources.extend(
        Path(dist.locate_file(p))
        for p in dist.files
        if str(p).startswith("netCDF4/_netCDF4.") and str(p).endswith(".so")
    )
    result = dict(
        repository=git_state(root),
        code=reference(Path(__file__)),
        cases=cases,
        sources=[reference(p) for p in sources],
        expected_behavior_reproduced=reproduced,
        native_abi_certified=False,
        environment_changed=False,
        new_physical_calls=0,
        upstream_issue="https://github.com/Unidata/netcdf4-python/issues/1354",
    )
    write_json_atomic(args.output, result)
    print(json.dumps({"expected_behavior_reproduced": reproduced, "strict_import_pass": False}))
    return 0 if reproduced else 2


if __name__ == "__main__":
    raise SystemExit(main())
