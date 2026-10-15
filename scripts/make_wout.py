"""Solve a hash-bound VMEC++ input JSON to a 401-surface Wout and record its identity (#115).

Writes `wout.nc` and `manifest.json` (input and Wout SHA-256, vmecpp version, schedule,
scalars, boundary check, wall time). Use `--compare` to report per-variable differences
against another Wout, for example an archived one.
"""

import argparse
import hashlib
import importlib.metadata
import json
import multiprocessing
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))

from fusion_baselines import wout_build as build  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402
from fusion_baselines.reference_wout import validate_reference  # noqa: E402

THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def solve(source, target):
    import vmecpp

    vmecpp.run(vmecpp.VmecInput.from_file(source), max_threads=1).wout.save(str(target))


def compare(first, second):
    import netCDF4

    with netCDF4.Dataset(first) as a, netCDF4.Dataset(second) as b:
        a.set_auto_mask(False)
        b.set_auto_mask(False)
        return dict(first=dict(path=str(first), sha256=digest(first)),
                    second=dict(path=str(second), sha256=digest(second)),
                    **build.compare(a.variables, b.variables))


def run(source, sha256, output, seconds=900, reference=None):
    import netCDF4

    build.need(all(os.environ.get(k) == "1" for k in THREADS), "one-thread execution required")
    build.need(0 < seconds <= 3600, "bounded solve budget required")
    build.need(digest(source) == sha256, f"input identity changed: {source}")
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = dict(kind="vmecpp-wout", completed=False,
                    input=dict(path=str(source), sha256=sha256),
                    schedule=build.schedule(data), max_threads=1, budget_seconds=seconds,
                    vmecpp=importlib.metadata.version("vmecpp"),
                    python=platform.python_version(), machine=platform.machine(),
                    provenance=build_run_record(ROOT),
                    identity_note="regenerated Wout: own identity, never an archived one")
    partial = output/"wout.partial.nc"
    started = time.monotonic()
    worker = multiprocessing.get_context("spawn").Process(target=solve, args=(source, partial))
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        worker.terminate()
        worker.join()
    manifest["wall_seconds"] = time.monotonic() - started
    manifest["exit_code"] = worker.exitcode
    try:
        build.need(worker.exitcode == 0 and partial.exists(), "VMEC++ solve did not complete")
        wout = output/"wout.nc"
        partial.rename(wout)
        with netCDF4.Dataset(wout) as nc:
            manifest["summary"] = build.summary(nc.variables)
            validate_reference(nc.variables, data)
        build.need(manifest["summary"]["ier_flag"] == 0, "VMEC++ reported ier_flag != 0")
        manifest["boundary_check"] = "input boundary to 1e-12, 401 surfaces, edge flux to 1e-14"
        manifest["wout"] = dict(path=str(wout), sha256=digest(wout))
        if reference:
            comparison = compare(reference, wout)
            (output/"comparison.json").write_text(
                json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
            manifest["comparison"] = {k: comparison[k] for k in (
                "identical", "worst_variable", "worst_max_rel", "only_first", "only_second")}
        manifest["completed"] = True
    except ValueError as exc:
        manifest["error"] = str(exc)
    (output/"manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--input-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seconds", type=int, default=900)
    parser.add_argument("--compare", type=Path, help="Wout to compare against (first operand)")
    parser.add_argument("--wout", type=Path, help="with --compare and no --input: compare only")
    args = parser.parse_args()
    if args.input is None:
        build.need(args.compare and args.wout and args.output, "--compare, --wout, --output")
        result = compare(args.compare, args.wout)
        args.output.write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
    else:
        result = run(args.input, args.input_sha256, args.output, args.seconds, args.compare)
        result = {k: result.get(k) for k in ("completed", "error", "wall_seconds", "wout",
                                             "comparison")}
    print(json.dumps({k: v for k, v in result.items() if k != "variables"}, indent=2))
    raise SystemExit(0 if result.get("completed", True) else 1)


if __name__ == "__main__":
    main()
