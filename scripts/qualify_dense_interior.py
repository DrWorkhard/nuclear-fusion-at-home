"""Bounded standard-library full-field comparison with frozen native #25 controls."""

import time

START, WALL_START = time.monotonic(), time.time()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def clean_revision(revision):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    if git("rev-parse", "HEAD") != revision or git("status", "--porcelain"):
        raise ValueError("Exact clean producer/evaluator revision required")


def source_bindings(expected_path, target):
    paths = [Path(__file__).resolve(), expected_path.resolve()]
    paths.extend((ROOT / "src/fusion_public").glob("*.py"))
    paths.extend(ROOT / "examples/clear-coil-samples-v1" / name
                 for name in ("manifest.json", "case.json", "candidate.json"))
    paths.extend(ROOT / "examples/clear-coil-interior-v1" / name for name in (
        "manifest.json", "reference401.json", "selected401.json", f"{target}-candidate.json"))
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def run(target, expected_path, expected_sha, output, revision):
    clean_revision(revision)
    bindings = source_bindings(expected_path, target)
    from fusion_public.data import canonical, load, load_case, require, save_new, sha
    from fusion_public.dense_interior import evaluate_dense
    from fusion_public.field import relative_error

    start, wall = START, WALL_START
    require(shutil.disk_usage(output.parent).free >= 3 * 1024**3, "3 GiB reserve required")
    output.mkdir(exist_ok=False)
    receipt = dict(completed=False, target_id=target, producer_evaluator=revision,
                   expected_sha256=expected_sha, physical_admission=False,
                   seconds=600, max_bytes=32*1024**2, clock_tolerance_s=5,
                   source_bindings=bindings)

    def guard():
        elapsed, elapsed_wall = time.monotonic() - start, time.time() - wall
        require(max(elapsed, elapsed_wall) < 600, "600 s qualification budget exhausted")
        require(abs(elapsed - elapsed_wall) <= 5, "Clock discrepancy exceeds 5 s")
        require(shutil.disk_usage(output).free >= 2*1024**3, "2 GiB live reserve required")
        require(sum(p.stat().st_size for p in output.iterdir() if p.is_file()) <= 32*1024**2,
                "32 MiB output cap exceeded")

    try:
        require(sha(expected_path.read_bytes()) == expected_sha, "Frozen native control changed")
        expected = load(expected_path)
        require(expected["target_id"] == target, "Expected target mismatch")
        candidate_path = ROOT / f"examples/clear-coil-interior-v1/{target}-candidate.json"
        require(sha(candidate_path.read_bytes()) == expected["candidate_sha256"],
                "Frozen coil shape changed")
        candidate, (case, _) = load(candidate_path), load_case()
        report, magnetic = evaluate_dense(candidate, case, target, 590, check_resources=guard)
        guard()
        require(report["packet_sha256"] == expected["packet_sha256"], "Target packet changed")
        current_error = abs(report["flux_normalized_max_abs_current_A"]
                            / expected["original_current_A"] - 1)
        field_error = relative_error(magnetic, expected["native_B_T"])
        metric_error = abs(report["dense_inner_vector_rms"]
                           - expected["original_metrics"]["vector_rms"])
        surface_error = max(abs(a-b) for a, b in zip(report["surface_vector_rms"],
                            expected["original_metrics"]["surface_vector_rms"], strict=True))
        require(current_error <= 1e-12, "Archived current was not recovered")
        require(field_error <= 1e-10, "Full-field scalar/native mismatch")
        require(max(metric_error, surface_error) <= 1e-10, "Dense metric mismatch")
        require(report["interior_metric_below_limit"] is False, "Original failure lost")
        with (output / "fields.json").open("xb") as stream:
            stream.write(canonical(magnetic) + b"\n")
        save_new(output / "report.json", report)
        receipt.update(completed=True, current_relative_error=current_error,
                       full_field_relative_error=field_error, rms_absolute_error=metric_error,
                       surface_rms_absolute_error=surface_error,
                       fields_sha256=sha((output / "fields.json").read_bytes()),
                       report_sha256=sha((output / "report.json").read_bytes()),
                       elapsed_s=time.monotonic() - start)
        clean_revision(revision)
        require(source_bindings(expected_path, target) == bindings,
                "Source/input changed during qualification")
        guard()
        save_new(output / "receipt.json", receipt)
        guard()
    except Exception as error:
        if (output / "receipt.json").exists():
            (output / "receipt.json").rename(output / "attempted-receipt.json")
        receipt.update(completed=False, error_type=type(error).__name__, error=str(error),
                       elapsed_s=time.monotonic() - start)
        save_new(output / "receipt.json", receipt)
        raise
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=("reference401", "selected401"))
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    run(args.target, args.expected, args.expected_sha, args.output, args.revision)
