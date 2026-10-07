"""Verify identities and recompute saved dense-interior comparisons using stdlib."""

import argparse
import hashlib
import json
import math
import time
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def score(actual, target, b2):
    residual = math.fsum(math.fsum((a-b)**2 for a, b in zip(got, want, strict=True))
                         for got, want in zip(actual, target, strict=True))
    return math.sqrt(residual / len(target) / b2)


def replay(root, output):
    start = time.monotonic()
    base = root / "evidence/issue10-interior-v1"
    manifest = read(base / "manifest.json")
    for name, expected in manifest.items():
        require(digest(base / name) == expected, f"Archive changed: {name}")
    mapping = read(base / "source-map.json")
    for original, entry in mapping.items():
        require(digest(root / entry["relative_path"]) == entry["sha256"],
                f"Producer/input changed: {original}")
    packet_root = root / "examples/clear-coil-interior-v1"
    require(digest(packet_root / "manifest.json") ==
            "9f9b32ffb6176b22e149069896500da0ac1aa0c371b5f17be7fa7603ebfb2ccb",
            "Packet manifest changed")
    packet_manifest = read(packet_root / "manifest.json")
    for name, expected in packet_manifest["files"].items():
        require(digest(packet_root / name) == expected, f"Packet changed: {name}")
    launch = read(base / "raw/launch.json")
    require(launch["completed"] is True, "Outer process did not complete")
    rows = []
    for target_id in ("reference401", "selected401"):
        raw = base / "raw" / target_id
        receipt, report = read(raw / "receipt.json"), read(raw / "report.json")
        require(receipt["completed"] is True and report["completed"] is True,
                "Qualification incomplete")
        require(receipt["producer_evaluator"] == "f40c53851e99f175f06257c17340e9b79237f3cb",
                "Unexpected producer/evaluator")
        for original, expected in receipt["source_bindings"].items():
            require(mapping[original]["sha256"] == expected, "Receipt source binding mismatch")
        expected_path = base / "inputs" / f"{target_id}-native.json"
        require(digest(expected_path) == receipt["expected_sha256"], "Expected fields changed")
        expected = read(expected_path)
        packet = read(packet_root / f"{target_id}.json")
        require(report["target_id"] == packet["target_id"] == expected["target_id"] == target_id,
                "Cross-target comparison")
        require(digest(packet_root / f"{target_id}.json") ==
                report["packet_sha256"] == expected["packet_sha256"], "Target identity mismatch")
        require(digest(raw / "report.json") == receipt["report_sha256"], "Report changed")
        require(digest(raw / "fields.json") == receipt["fields_sha256"], "Fields changed")
        fields = read(raw / "fields.json")
        target = [row[3:] for row in packet["samples_xyz_B"]]
        require(len(fields) == len(expected["native_B_T"]) == len(target) == 12288,
                "Full dense arrays required")
        b2 = packet["B2_scale_T2"]
        rms = score(fields, target, b2)
        surfaces = [score(fields[i:i+4096], target[i:i+4096], b2) for i in (0, 4096, 8192)]
        field_error = max(abs(a-b) for got, want in zip(fields, expected["native_B_T"], strict=True)
                          for a, b in zip(got, want, strict=True)) / max(
                              abs(x) for row in expected["native_B_T"] for x in row)
        current_error = abs(report["flux_normalized_max_abs_current_A"]
                            / expected["original_current_A"] - 1)
        require(current_error <= 1e-12 and field_error <= 1e-10, "Current/field mismatch")
        require(abs(rms - expected["original_metrics"]["vector_rms"]) <= 1e-10,
                "Native RMS mismatch")
        require(abs(rms - report["dense_inner_vector_rms"]) <= 1e-14,
                "Saved RMS not reproduced")
        for value, native, saved in zip(
            surfaces, expected["original_metrics"]["surface_vector_rms"],
            report["surface_vector_rms"], strict=True,
        ):
            require(abs(value-native) <= 1e-10 and abs(value-saved) <= 1e-14,
                    "Surface RMS mismatch")
        require(report["signed_target_flux_Wb"] < 0 and report["measured_unscaled_flux_Wb"] < 0,
                "Flux sign changed")
        require(abs(report["flux_scale"] * report["measured_unscaled_flux_Wb"]
                    / report["signed_target_flux_Wb"] - 1) < 1e-14, "Current scale mismatch")
        require(rms > 0.01 and report["interior_metric_below_limit"] is False,
                "Original failure lost")
        require(report["physical_admission"] is False and report["step4_pass"] is False,
                "Unsupported admission")
        require(abs(current_error-receipt["current_relative_error"]) <= 1e-15 and
                abs(field_error-receipt["full_field_relative_error"]) <= 1e-15,
                "Qualification discrepancy not reproduced")
        rows.append(dict(target_id=target_id, current_relative_error=current_error,
                         full_field_relative_error=field_error, dense_inner_vector_rms=rms))
    cli = read(base / "portable-cli/stdout.json")
    require(read(base / "portable-cli/launch.json")["completed"] is True,
            "Portable command failed")
    selected = read(base / "raw/selected401/report.json")
    for name in ("source_sha256", "packet_sha256", "case_sha256", "candidate_sha256",
                 "dense_inner_vector_rms", "surface_vector_rms",
                 "flux_normalized_max_abs_current_A", "interior_metric_below_limit",
                 "physical_admission", "step4_pass"):
        require(cli[name] == selected[name], f"Portable command changed {name}")
    result = dict(completed=True, manifest_files=len(manifest), source_bindings=len(mapping),
                  arms=rows, elapsed_s=time.monotonic()-start,
                  fields_recomputed=False, native_solver_repeated=False, timing_reattested=False,
                  physical_admission=False)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    replay(args.root, args.output)
