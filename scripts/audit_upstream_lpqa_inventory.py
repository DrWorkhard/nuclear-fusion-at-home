"""Independently recount a source-bound LPQA inventory and its reported-value screen."""

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable audit required")
    root = Path(__file__).resolve().parents[1]
    report = json.loads(args.inventory.read_text())
    external = Path(report["external"]["path"])
    tree = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "-z",
            report["external"]["commit"],
            "--",
            "submissions/LandremanPaul2021_QA/",
        ],
        cwd=external,
    )
    expected_paths = sorted(
        str(external / entry.split(b"\t", 1)[1].decode())
        for entry in tree.split(b"\0")
        if entry.endswith(b"/results.json")
    )
    checks = dict(
        source_tree=hashlib.sha256(tree).hexdigest() == report["source_tree_sha256"],
        complete_path_list=[row["source"]["path"] for row in report["rows"]] == expected_paths,
        all_source_bytes=True,
        all_reported_values=True,
        all_metadata_screens=True,
        all_selected_fields=True,
    )
    exclusions, schema, eligible = Counter(), Counter(), []
    zeros = 0
    for row in report["rows"]:
        path = Path(row["source"]["path"])
        content = path.read_bytes()
        checks["all_source_bytes"] &= (
            hashlib.sha256(content).hexdigest() == row["source"]["sha256"]
            and hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
            == row["git_blob"]
            and len(content) == row["bytes"]
        )
        doc = json.loads(content)
        if "parse_error" in row:
            raise ValueError("parse errors require separate manual review")
        metrics = doc["metrics"] if "metrics" in doc else doc
        schema[row["schema"]] += 1
        zeros += metrics.get("final_squared_flux") == 0
        checks["all_reported_values"] &= all(
            metrics.get(k) == v for k, v in row["reported"].items()
        )
        scale = metrics.get("_cached_thresholds", {}).get("a0")
        checks["all_reported_values"] &= row["a0"] == scale

        def bound(key, limit, *, lower=False, inverse=False, metrics=metrics, scale=scale):
            value = metrics.get(key)
            if not finite(scale) or scale <= 0 or not finite(value) or value < 0:
                return False
            return (
                (value / scale if inverse else value * scale) >= limit
                if lower
                else ((value / scale if inverse else value * scale) <= limit)
            )

        currents = metrics.get("final_current_per_coil")
        mean, error = metrics.get("final_B_field"), metrics.get("avg_BdotN_over_B")
        expected = dict(
            four_coils=isinstance(currents, list) and len(currents) == 4,
            order_eight=metrics.get("final_order", metrics.get("fourier_order")) == 8,
            no_issues=not row["issues"],
            endpoint_field_available=bool(row["endpoint_field"]),
            field_strength=bool(
                finite(metrics.get("target_B_field"))
                and metrics["target_B_field"] == 1
                and finite(mean)
                and 0.9 <= mean <= 1.1
            ),
            length=bound("final_total_length", 220),
            curvature=bound("final_max_curvature", 1, inverse=True),
            coil_clearance=bound("final_min_cc_separation", 1.06, lower=True),
            plasma_clearance=bound("final_min_cs_separation", 1.3, lower=True),
            ranking_value=finite(error) and error >= 0,
        )
        checks["all_metadata_screens"] &= (
            expected == row["checks"] and all(expected.values()) == row["metadata_screen_pass"]
        )
        exclusions.update(k for k, v in expected.items() if not v)
        if all(expected.values()):
            eligible.append((error, str(path)))
        if "selected_field" in row:
            ref = row["selected_field"]
            checks["all_selected_fields"] &= sha256_file(Path(ref["path"])) == ref["sha256"]
    expected_counts = dict(
        reports=len(expected_paths),
        parse_errors=0,
        metadata_screen_pass=len(eligible),
        reported_zero_flux=zeros,
        schema=dict(schema),
        exclusions=dict(exclusions),
    )
    checks["counts"] = expected_counts == report["counts"]
    checks["selection"] = [path for _, path in sorted(eligible)[:5]] == report["shortlist"]
    checks["selected_field_count"] = sum("selected_field" in row for row in report["rows"]) == len(
        report["shortlist"]
    )
    output = dict(
        repository=git_state(root),
        source=dict(path=str(args.inventory.resolve()), sha256=sha256_file(args.inventory)),
        code=dict(path=str(Path(__file__).resolve()), sha256=sha256_file(Path(__file__))),
        checks=checks,
        all_pass=all(checks.values()),
        additional_physics_calls=0,
        scope="source_hashes_reported_values_screen_arithmetic_counts_and_ranking_only",
        physical_feasibility_certified=False,
    )
    write_json_atomic(args.output, output)
    print(json.dumps({"all_pass": output["all_pass"], "counts": expected_counts}))
    return 0 if output["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
