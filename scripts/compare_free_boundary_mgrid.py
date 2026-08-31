#!/usr/bin/env python3
"""Compare two otherwise identical free-boundary MGRID response resolutions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(first: float, second: float) -> float:
    return abs(second - first) / abs(second)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("standard", type=Path)
    parser.add_argument("refined", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    standard = json.loads(args.standard.read_text())
    refined = json.loads(args.refined.read_text())
    if standard["prepared_case_sha256"] != refined["prepared_case_sha256"]:
        raise ValueError("Prepared cases differ")

    relative_changes = {
        metric: _relative(
            standard["free_boundary"][metric], refined["free_boundary"][metric]
        )
        for metric in ("volume_m3", "aspect", "iota_axis", "iota_edge")
    }
    cross_section_absolute_changes = {
        phi: abs(
            refined["comparisons"]["cross_sections"][phi]["normalized_rms_distance"]
            - standard["comparisons"]["cross_sections"][phi]["normalized_rms_distance"]
        )
        for phi in standard["comparisons"]["cross_sections"]
    }
    acceptance = {
        "same_prepared_case": True,
        "both_individually_accepted": standard["accepted"] and refined["accepted"],
        "free_metrics_relative_change_below_0_005": all(
            change < 0.005 for change in relative_changes.values()
        ),
        "cross_section_normalized_rms_absolute_change_below_0_005": all(
            change < 0.005 for change in cross_section_absolute_changes.values()
        ),
    }
    evidence = {
        "schema_version": 1,
        "standard": {
            "path": str(args.standard.resolve()),
            "sha256": _sha256(args.standard),
            "r_z_points": standard["response_grid"]["r_points"],
        },
        "refined": {
            "path": str(args.refined.resolve()),
            "sha256": _sha256(args.refined),
            "r_z_points": refined["response_grid"]["r_points"],
        },
        "free_boundary_relative_changes": relative_changes,
        "cross_section_normalized_rms_absolute_changes": cross_section_absolute_changes,
        "acceptance": acceptance,
        "accepted": all(acceptance.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
