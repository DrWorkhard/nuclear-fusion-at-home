"""Independent deadline-ledger and common-prefix checks, without physics dependencies."""

import numpy as np

from .oracle_audit import audit_ledger


def audit_timed_arm(arm, x, values, seconds=300.0, safety_limit=300000):
    checks = audit_ledger(arm, x, values, safety_limit)
    # The proposal-cap stop rule is inapplicable to a wall-clock stop; replace
    # that check explicitly, not the underlying record/status/counters.
    del checks["budget_stop_is_exact"]
    t = arm["timing"]
    checks["declared_wall_budget"] = t["budget_seconds"] == seconds
    checks["finite_timing"] = all(
        np.isfinite(t[key]) and t[key] >= 0
        for key in ("elapsed_to_stop_seconds", "overrun_seconds")
    )
    if arm["status"] == "budget_exhausted":
        checks["wall_clock_stop"] = (
            t["time_denials"] == arm["counters"]["denied"] == 1
            and t["elapsed_to_stop_seconds"] >= seconds
        )
        checks["overrun_accounted"] = np.isclose(
            t["overrun_seconds"], t["elapsed_to_stop_seconds"] - seconds, rtol=0, atol=1e-7
        )
    else:
        checks["early_solver_return"] = (
            arm["status"] == "solver_returned"
            and t["time_denials"] == arm["counters"]["denied"] == 0
        )
        checks["early_time_is_upper_bound"] = t["early_return_end_to_end_upper_bound"]
    return {key: bool(value) for key, value in checks.items()}


def audit_common_prefix(first, second):
    a, b = first["evaluations"], second["evaluations"]
    n = min(len(a), len(b))
    checks = {
        "nonempty": n > 0,
        "same_terminal_status": first["status"] == second["status"],
        "same_stop_reason": first["timing"]["time_denials"] == second["timing"]["time_denials"],
        "all_common_proposals_match": all(
            x["x_sha256"] == y["x_sha256"] for x, y in zip(a[:n], b[:n], strict=True)
        ),
        "all_common_values_match": all(
            np.allclose(x["values"], y["values"], rtol=1e-12, atol=1e-14)
            for x, y in zip(a[:n], b[:n], strict=True)
        ),
    }
    if first["status"] == second["status"] == "solver_returned":
        checks["same_converged_count"] = len(a) == len(b)
    return {
        "common_prefix_length": n,
        "counts": [len(a), len(b)],
        "checks": checks,
        "pass": all(checks.values()),
    }
