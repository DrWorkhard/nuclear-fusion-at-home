"""Retrospective metadata/current audit; no new magnetic-field evaluations."""

import argparse
import json
from pathlib import Path

import numpy as np
from simsopt import load

from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic

HOLDOUTS = (
    "timed-spatial-pilot-v1-holdout.json",
    "direct-slsqp-pilot-v1-holdout.json",
    "gn-trust-native-v1-holdout.json",
    "direct-slsqp-1024-v1-holdout.json",
)


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable metadata audit required")
    root = Path(__file__).resolve().parents[1]
    records, sources = [], []
    for filename in HOLDOUTS:
        path = root / "evidence" / filename
        sources.append(reference(path))
        report = json.loads(path.read_text())
        if report["status"] != "completed" or not report["all_repeats"]:
            raise ValueError("complete all-repeat holdout required")
        for candidate in report["candidates"]:
            field_path = Path(candidate["field"]["path"])
            if sha256_file(field_path) != candidate["field"]["sha256"]:
                raise ValueError("field hash mismatch")
            fine = candidate["flux"][-1]
            if (fine["surface_resolution"], fine["coil_quadrature"]) != (128, 800):
                raise ValueError("identical fine quadrature required")
            phi, bmean = fine["unthresholded_quadratic_flux"], fine["mean_B_magnitude_T"]
            if not np.isfinite([phi, bmean]).all() or min(phi, bmean) <= 0:
                raise ValueError("positive finite saved flux/field required")
            field = load(str(field_path))
            currents = [c.current.get_value() for c in field.coils[:4]]
            records.append(
                dict(
                    source=filename,
                    candidate=candidate["method"],
                    field=reference(field_path),
                    base_currents_A=currents,
                    base_current_sum_A=sum(currents),
                    raw_flux=phi,
                    mean_B_T=bmean,
                    raw_flux_over_mean_B_squared=phi / bmean**2,
                )
            )
    means = np.array([r["mean_B_T"] for r in records])
    totals = np.array([r["base_current_sum_A"] for r in records])
    ratios = []
    for repeat in (1, 2):
        pair = [
            next(
                r
                for r in records
                if r["source"] == HOLDOUTS[0] and r["candidate"] == f"{label}-r{repeat}"
            )
            for label in ("scalar", "batched")
        ]
        ratios.append(
            dict(
                repeat=repeat,
                raw_flux_ratio=pair[0]["raw_flux"] / pair[1]["raw_flux"],
                mean_B_normalized_ratio=pair[0]["raw_flux_over_mean_B_squared"]
                / pair[1]["raw_flux_over_mean_B_squared"],
            )
        )
    result = dict(
        schema_version=1,
        repository=git_state(root),
        retrospective=True,
        source_holdouts=sources,
        candidates=records,
        timed_pair_ratios=ratios,
        mean_B_min_T=float(means.min()),
        mean_B_max_T=float(means.max()),
        mean_B_relative_span=float(np.ptp(means) / means.min()),
        total_current_min_A=float(totals.min()),
        total_current_max_A=float(totals.max()),
        new_B_evaluations=0,
        optimizer_feedback=False,
        new_feasibility_gate=False,
        physical_feasibility_certified=False,
        metric_note=("Phi/<|B|>^2 is a global-scale diagnostic, "
                     "not local normalized flux or a new gate."),
        code=reference(Path(__file__)),
        pinned_current_factory=reference(
            root
            / "external/stellcoilbench/src/stellcoilbench"
            / "coil_optimization/_adaptive_search.py"
        ),
    )
    write_json_atomic(args.output, result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "mean_B_relative_span",
                    "timed_pair_ratios",
                    "total_current_min_A",
                    "total_current_max_A",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
