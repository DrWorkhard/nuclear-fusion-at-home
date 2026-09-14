"""One registered cold VMEC++ solve; parent enforces disk/time budget."""

import argparse
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np
import vmecpp
from current_diagnostic_inputs import checked, reference

from fusion_baselines.plasma_design import design_input
from fusion_baselines.provenance import write_json_atomic


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    folder = args.directory
    if (folder / "solver.json").exists() or (folder / "wout.nc").exists():
        raise FileExistsError("new unsolved plasma cell required")
    request = json.loads((folder / "request.json").read_text())
    original = json.loads(checked(request["original"]).read_text())
    effective = json.loads(checked(request["input"]).read_text())
    if effective != design_input(original, request["x"], request["ns"]):
        raise ValueError("registered named input change mismatch")
    record = dict(
        status="running",
        converged=False,
        version=importlib.metadata.version("vmecpp"),
        request=reference(folder / "request.json"),
    )
    started = time.monotonic()
    try:
        parsed = vmecpp.VmecInput.model_validate(effective)
        if parsed.model_dump(mode="json") != effective:
            raise ValueError("input changed in solver conversion")
        result = vmecpp.run(parsed, max_threads=1, verbose=True)
        result.wout.save(folder / "wout.nc")
        residuals = {k: float(getattr(result.wout, k)) for k in ("fsqr", "fsqz", "fsql")}
        valid = (
            all(np.isfinite(v) and 0 <= v <= 1e-12 for v in residuals.values())
            and int(result.wout.ns) == request["ns"]
        )
        record.update(
            status="completed",
            residuals=residuals,
            converged=valid,
            wout=reference(folder / "wout.nc"),
            niter=int(result.wout.niter),
        )
    except Exception as exc:
        record.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        record["elapsed_seconds"] = time.monotonic() - started
        write_json_atomic(folder / "solver.json", record)
    return 0 if record["converged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
