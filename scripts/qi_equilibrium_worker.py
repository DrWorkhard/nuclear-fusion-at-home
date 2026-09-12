"""Prepare or execute one immutable QI cell in the existing VMEC++ environment."""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import vmecpp

from fusion_baselines.provenance import sha256_file, write_json_atomic
from fusion_baselines.qi_resolution import check_effective, effective_input


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "solve"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--ns", type=int)
    parser.add_argument("--angular", type=int)
    args = parser.parse_args()
    folder = args.directory
    if args.mode == "prepare":
        folder.mkdir(parents=True, exist_ok=False)
        original = vmecpp.VmecInput.from_file(args.input).model_dump(mode="json")
        effective = effective_input(original, args.ns, args.angular)
        parsed = vmecpp.VmecInput.model_validate(effective)
        if parsed.model_dump(mode="json") != effective:
            raise ValueError("effective input changed during solver conversion")
        write_json_atomic(folder / "original_input.json", original)
        write_json_atomic(folder / "effective_input.json", effective)
        write_json_atomic(folder / "preparation.json", dict(
            input_path=str(args.input.resolve()), input_sha256=sha256_file(args.input),
            ns=args.ns, angular=args.angular,
            effective_sha256=sha256_file(folder / "effective_input.json"),
            original_sha256=sha256_file(folder / "original_input.json")))
        return 0
    preparation = json.loads((folder / "preparation.json").read_text())
    for name in ("original", "effective"):
        if sha256_file(folder / f"{name}_input.json") != preparation[f"{name}_sha256"]:
            raise ValueError("prepared input changed")
    original = json.loads((folder / "original_input.json").read_text())
    effective = json.loads((folder / "effective_input.json").read_text())
    if not check_effective(original, effective, preparation["ns"], preparation["angular"]):
        raise ValueError("nonregistered effective controls or physical mutation")
    path = folder / "solver.json"
    if path.exists() or (folder / "wout.nc").exists():
        raise FileExistsError("fresh unsolved cell required")
    report = dict(status="running", numerically_converged=False)
    started = time.monotonic()
    try:
        result = vmecpp.run(vmecpp.VmecInput.model_validate(effective),
                            max_threads=1, verbose=True)
        wout = result.wout
        wout.save(folder / "wout.nc")
        residuals = {k: float(getattr(wout, k)) for k in ("fsqr", "fsqz", "fsql")}
        converged = all(np.isfinite(v) and 0 <= v <= 1e-12 for v in residuals.values())
        converged &= int(wout.ns) == preparation["ns"]
        converged &= all(int(getattr(wout, k)) == effective[k] for k in ("nfp", "mpol", "ntor"))
        report.update(status="completed", residuals=residuals, niter=int(wout.niter),
                      numerically_converged=bool(converged), wout_sha256=sha256_file(
                          folder / "wout.nc"))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        report["elapsed_seconds"] = time.monotonic() - started
        write_json_atomic(path, report)
    return 0 if report["numerically_converged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
