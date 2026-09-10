"""Read-only consistency checks on a completed common-oracle ledger."""

import hashlib

import numpy as np


def audit_ledger(arm, x, values, limit):
    evaluations, counter = arm["evaluations"], arm["counters"]
    x, values = np.asarray(x), np.asarray(values)
    if not evaluations:
        raise ValueError("cannot qualify an empty ledger")
    completed = [e for e in evaluations if e["status"] == "completed"]
    if not completed:
        raise ValueError("no completed evaluation")
    best = min(completed, key=lambda e: e["merit"])
    return {
        "terminal_status": arm["status"] in ("budget_exhausted", "solver_returned"),
        "gradient_screen": arm["gradient_screen_pass"],
        "exact_proposal_count": counter["attempts"] == len(evaluations),
        "contiguous_attempts": [e["attempt"] for e in evaluations]
            == list(range(1, len(evaluations) + 1)),
        "request_partition": counter["requests"] == counter["attempts"]
            + counter["cache_hits"] + counter["denied"],
        "within_cap": counter["attempts"] <= counter["limit"] == limit,
        "no_failed_evaluation": counter["failed_attempts"] == 0
            and len(completed) == len(evaluations),
        "fixed_coordinate_scale": arm["coordinate_map"]["scale"] == 0.01,
        "physical_coordinates_recorded": arm["coordinate_map"][
            "oracle_records_physical_coordinates"],
        "budget_stop_is_exact": (counter["attempts"] == limit and counter["denied"] == 1)
            if arm["status"] == "budget_exhausted" else counter["denied"] == 0,
        "all_merits_match": all(
            np.all(np.isfinite(e["values"])) and np.isfinite(e["merit"])
            and float(np.asarray(e["values"]) @ np.asarray(e["values"]) / 2) == e["merit"]
            for e in completed),
        "best_selection": all(arm["best"][k] == best[k]
            for k in ("attempt", "merit", "x_sha256")),
        "best_physical_array_hash": np.all(np.isfinite(x))
            and hashlib.sha256(x.tobytes()).hexdigest() == best["x_sha256"],
        "best_values": np.array_equal(values, best["values"]),
        "best_merit": float(values @ values / 2) == best["merit"],
    }
