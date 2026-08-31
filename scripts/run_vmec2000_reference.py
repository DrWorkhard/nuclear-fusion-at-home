#!/usr/bin/env python3
"""Run or summarize the pinned native VMEC 8.52 reference calculation."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import time
from pathlib import Path

import netCDF4
import numpy as np

EXPECTED_SOURCE_COMMIT = "e59affaec7713aee8da1f1bccdf05cc0612c12e3"
CASE_LABEL = "w7xbaseline"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def command_output(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def scalar(dataset: netCDF4.Dataset, name: str) -> int | float | str:
    value = np.asarray(dataset[name][:]).item()
    if isinstance(value, bytes):
        return value.decode().strip()
    if isinstance(value, (np.integer, int)):
        return int(value)
    return float(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument(
        "--reuse",
        action="store_true",
        help="summarize an existing completed result instead of running VMEC",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    source_root = project_root / "external/stellopt-v251"
    binary = source_root / "VMEC2000/Release/xvmec2000"
    patch = project_root / "patches/stellopt-v251-macos-vmec-validation.patch"
    input_path = args.input.resolve()
    output_directory = args.output_directory.resolve()
    local_input = output_directory / f"input.{CASE_LABEL}"
    output_wout = output_directory / f"wout_{CASE_LABEL}.nc"
    run_log = output_directory / "run.log"

    for required in (input_path, binary, patch):
        if not required.exists():
            raise FileNotFoundError(required)
    actual_commit = command_output(["git", "-C", str(source_root), "rev-parse", "HEAD"])
    if actual_commit != EXPECTED_SOURCE_COMMIT:
        raise RuntimeError(
            f"STELLOPT source is at {actual_commit}, expected {EXPECTED_SOURCE_COMMIT}"
        )
    patch_check = subprocess.run(
        ["git", "-C", str(source_root), "apply", "--reverse", "--check", str(patch)],
        capture_output=True,
        check=False,
    )
    if patch_check.returncode != 0:
        raise RuntimeError("the tracked validation/build patch does not match the source tree")

    elapsed_seconds: float | None = None
    if args.reuse:
        if not output_wout.is_file() or not run_log.is_file():
            raise FileNotFoundError("--reuse requires the completed wout and run.log")
        if not local_input.exists() or sha256(local_input) != sha256(input_path):
            raise RuntimeError("existing run input does not match the requested input")
    else:
        if output_directory.exists() and any(output_directory.iterdir()):
            raise FileExistsError(
                f"refusing to overwrite nonempty output directory: {output_directory}"
            )
        output_directory.mkdir(parents=True, exist_ok=True)
        local_input.symlink_to(input_path)
        started = time.monotonic()
        with run_log.open("wb") as log_stream:
            result = subprocess.run(
                [str(binary), local_input.name],
                cwd=output_directory,
                stdout=log_stream,
                stderr=subprocess.STDOUT,
                check=False,
            )
        elapsed_seconds = time.monotonic() - started
        if result.returncode != 0:
            raise RuntimeError(f"VMEC exited {result.returncode}; inspect {run_log}")

    log_text = run_log.read_text(errors="replace")
    if "EXECUTION TERMINATED NORMALLY" not in log_text:
        raise RuntimeError("run log does not contain VMEC's normal-termination marker")
    runtime_match = re.search(r"TOTAL COMPUTATIONAL TIME\s+([0-9.]+) SECONDS", log_text)
    reported_runtime = float(runtime_match.group(1)) if runtime_match else None

    with netCDF4.Dataset(output_wout) as dataset:
        metrics = {
            name: scalar(dataset, name)
            for name in (
                "version_",
                "ier_flag",
                "niter",
                "ns",
                "mpol",
                "ntor",
                "nfp",
                "fsqr",
                "fsqz",
                "fsql",
                "aspect",
                "volume_p",
                "betatotal",
            )
        }

    outputs = {}
    for path in sorted(output_directory.iterdir()):
        if path.is_file() or path.is_symlink():
            outputs[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}

    evidence = {
        "schema_version": 1,
        "case": "StellCoilBench W7-X fixed-boundary equilibrium",
        "execution": {
            "mode": "reuse" if args.reuse else "fresh",
            "command": [str(binary), local_input.name],
            "cwd": str(output_directory),
            "wall_seconds_observed": elapsed_seconds,
            "vmec_reported_compute_seconds": reported_runtime,
            "normal_termination_marker": True,
        },
        "source": {
            "repository": "https://github.com/PrincetonUniversity/STELLOPT",
            "commit": actual_commit,
            "vmec_version": "8.52",
            "patch_path": str(patch.relative_to(project_root)),
            "patch_sha256": sha256(patch),
            "patch_matches_source_tree": True,
        },
        "platform": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "gfortran": command_output(["/opt/homebrew/bin/gfortran", "--version"]).splitlines()[0],
        },
        "binary": {
            "path": str(binary),
            "sha256": sha256(binary),
            "dynamic_libraries": command_output(["otool", "-L", str(binary)]).splitlines()[1:],
        },
        "input": {
            "path": str(input_path),
            "bytes": input_path.stat().st_size,
            "sha256": sha256(input_path),
        },
        "outputs": outputs,
        "metrics": metrics,
    }
    evidence_path = project_root / "evidence/w7x-vmec2000-v852-reference.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
