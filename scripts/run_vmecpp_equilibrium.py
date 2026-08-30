"""Run a VMEC++ fixed/free-boundary input and emit a compact verified summary."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import vmecpp


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(path: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def as_scalar(value):
    if isinstance(value, np.generic):
        return value.item()
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()

    source = args.input.resolve()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    vmec_input = vmecpp.VmecInput.from_file(source)

    start = time.perf_counter()
    output = vmecpp.run(vmec_input, max_threads=args.threads, verbose=False)
    elapsed = time.perf_counter() - start
    wout = output.wout
    wout_path = output_dir / "wout.nc"
    wout.save(wout_path)

    last_ftol = float(vmec_input.ftol_array[-1])
    residuals = {name: float(getattr(wout, name)) for name in ["fsqr", "fsqz", "fsql"]}
    # VMEC maps successful status 11 to legacy wout ier_flag 0. Check the actual
    # residuals against the requested tolerance instead of interpreting 0 alone.
    residual_converged = max(residuals.values()) <= last_ftol * 1.01
    summary = {
        "schema_version": 1,
        "vmecpp_version": version("vmecpp"),
        "vmecpp_source_commit": git_head(Path("external/vmecpp")),
        "input": {
            "path": str(source),
            "sha256": sha256(source),
            "nfp": vmec_input.nfp,
            "mpol": vmec_input.mpol,
            "ntor": vmec_input.ntor,
            "ns_array": vmec_input.ns_array.tolist(),
            "ftol_array": vmec_input.ftol_array.tolist(),
            "niter_array": vmec_input.niter_array.tolist(),
            "free_boundary": vmec_input.lfreeb,
        },
        "host": {
            "machine": platform.machine(),
            "python": platform.python_version(),
            "max_threads": args.threads,
        },
        "elapsed_seconds": elapsed,
        "output": {
            "path": str(wout_path),
            "sha256": sha256(wout_path),
            "ier_flag": int(wout.ier_flag),
            "residual_converged": residual_converged,
            "niter": int(wout.niter),
            "ns": int(wout.ns),
            "mpol": int(wout.mpol),
            "ntor": int(wout.ntor),
            "nfp": int(wout.nfp),
            "force_residuals": residuals,
            "aspect": as_scalar(wout.aspect),
            "volume_m3": as_scalar(wout.volume_p),
            "beta_total": as_scalar(wout.betatotal),
            "beta_poloidal": as_scalar(wout.betapol),
            "beta_toroidal": as_scalar(wout.betator),
            "magnetic_energy": as_scalar(wout.wb),
            "thermal_energy": as_scalar(wout.wp),
            "iota_axis": float(wout.iotaf[0]),
            "iota_edge": float(wout.iotaf[-1]),
            "iota_min": float(np.min(wout.iotaf)),
            "iota_max": float(np.max(wout.iotaf)),
        },
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if residual_converged else 2


if __name__ == "__main__":
    raise SystemExit(main())
