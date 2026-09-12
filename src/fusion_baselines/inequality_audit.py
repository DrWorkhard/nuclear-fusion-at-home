"""Independent arithmetic audit of stored direct-inequality optimization ledgers."""

import hashlib

import numpy as np


def audit_inequality_arm(arm, x, values, *, expected_limit=256, stop_profile="single_solver"):
    if type(expected_limit) is not int or expected_limit < 1:
        raise ValueError("positive predeclared expected budget required")
    if stop_profile not in {"single_solver", "staged_al"}:
        raise ValueError("unknown predeclared termination profile")
    records, counters = arm["evaluations"], arm["counters"]
    completed = [r for r in records if r["status"] == "completed"]
    failed = [r for r in records if r["status"] == "error"]
    tolerance = arm["selection_tolerance"]
    checks = {
        "nonempty": bool(completed),
        "consecutive_attempts": [r["attempt"] for r in records] == list(range(1, len(records) + 1)),
        "ledger_counts": len(records) == counters["attempts"] <= counters["limit"],
        "status_partition": len(completed) + len(failed) == len(records),
        "failure_count": len(failed) == counters["failed_attempts"],
        "request_partition": counters["requests"]
        == len(records) + counters["cache_hits"] + counters["denied"],
        "fixed_limit": counters["limit"] == expected_limit,
        "fixed_selection_tolerance": tolerance == 1e-8,
        "gradient_screen": arm["gradient_screen_pass"] is True,
        "correct_stop": (
            arm["status"] == "budget_exhausted"
            and arm["stop_reason"] == "proposal_cap"
            and len(records) == counters["limit"]
            and counters["denied"] == 1
        )
        or (arm["status"] == "solver_returned" and counters["denied"] == 0),
    }
    if stop_profile == "staged_al":
        # Detailed stage accounting/target checks belong to the additional AL audit.
        checks["correct_stop"] = (
            counters["denied"] == 0
            and arm.get("converged") is False
            and (
                (
                    arm["status"] == "stages_completed"
                    and arm["stop_reason"] == "eight_stages_completed"
                )
                or (
                    arm["status"] == "construction_stopped"
                    and arm["stop_reason"] == "construction_target"
                )
            )
        )
    keys, metrics_pass = [], True
    for record in completed:
        vector = np.asarray(record["values"], dtype=float)
        if vector.shape != (138,) or not np.all(np.isfinite(vector)):
            metrics_pass = False
            continue
        violation = max(0.0, -float(vector[1:].min()))
        passed = violation <= tolerance
        # Deliberately do not import the search's selection-key implementation.
        key = (0 if passed else 1, 0.0 if passed else violation, float(vector[0]))
        keys.append((key, record))
        metrics_pass &= (
            record["selection_key"] == list(key)
            and record["objective"] == vector[0]
            and record["maximum_violation"] == violation
            and record["construction_screen_pass"] == passed
        )
    checks["all_stored_metrics"] = bool(metrics_pass)
    if keys:
        key, expected = min(keys, key=lambda pair: pair[0])
        best = arm["best"]
        checks["selected_best"] = best["attempt"] == expected["attempt"]
        checks["selected_key"] = best["selection_key"] == list(key)
        checks["best_values"] = np.array_equal(values, expected["values"])
        checks["best_physical_hash"] = (
            hashlib.sha256(np.asarray(x, dtype=np.float64).tobytes()).hexdigest()
            == best["x_sha256"]
            == expected["x_sha256"]
        )
    else:
        checks["selected_best"] = False
    return {name: bool(value) for name, value in checks.items()}
