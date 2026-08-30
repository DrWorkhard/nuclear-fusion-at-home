#!/usr/bin/env python3
"""Run a pinned SIMPLE input in a self-describing output directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def read_last_numeric_row(path: Path) -> list[float]:
    rows = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            rows.append([float(value) for value in stripped.split()])
    if not rows:
        raise ValueError(f"no numeric rows in {path}")
    return rows[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("wout", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--executable", type=Path, default=Path("external/simple/build/simple.x")
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    executable = (project_root / args.executable).resolve()
    input_path = args.input.resolve()
    wout_path = args.wout.resolve()
    output = args.output.resolve()
    for path in (executable, input_path, wout_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    output.mkdir(parents=True, exist_ok=True)
    local_input = output / "simple.in"
    local_wout = output / "wout.nc"
    shutil.copy2(input_path, local_input)
    shutil.copy2(wout_path, local_wout)

    started = time.perf_counter()
    completed = subprocess.run(
        [str(executable)], cwd=output, check=False, text=True, capture_output=True
    )
    elapsed = time.perf_counter() - started
    (output / "stdout.log").write_text(completed.stdout)
    (output / "stderr.log").write_text(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(f"SIMPLE exited with {completed.returncode}; see {output}")

    confined_path = output / "confined_fraction.dat"
    final = read_last_numeric_row(confined_path)
    if len(final) < 4:
        raise ValueError("unexpected confined_fraction.dat format")
    summary = {
        "schema_version": 1,
        "solver": "SIMPLE",
        "simple_commit": subprocess.check_output(
            ["git", "-C", str(project_root / "external/simple"), "rev-parse", "HEAD"],
            text=True,
        ).strip(),
        "elapsed_seconds": elapsed,
        "returncode": completed.returncode,
        "result": {
            "final_time_s": final[0],
            "passing_fraction": final[1],
            "trapped_fraction": final[2],
            "resolved_particles": int(final[3]),
            "loss_fraction": 1.0 - final[1] - final[2],
        },
        "inputs": {
            "simple_input_sha256": sha256(local_input),
            "wout_sha256": sha256(local_wout),
        },
        "outputs": {
            "confined_fraction_sha256": sha256(confined_path),
            "stdout_sha256": sha256(output / "stdout.log"),
            "stderr_sha256": sha256(output / "stderr.log"),
        },
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
