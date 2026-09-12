"""Independent arithmetic replay of fixed natural-AL stage records."""

import numpy as np


def audit_stages(arm):
    ledger, stages = arm["evaluations"], arm["stages"]
    checks = dict(
        stage_count=1 <= len(stages) <= 8,
        nine_qualification_bundles=len(ledger) >= 9,
        stage_partition=True,
        merit_identity=True,
        selected_minimum=True,
        multiplier_sequence=True,
        target_semantics=True,
    )
    if len(ledger) < 9 or not stages:
        return {**checks, "all_stage_records": False}
    lam, rho = np.zeros(137), 10.0
    previous = max(1.0, max(0.0, -float(np.min(ledger[0]["values"][1:]))))
    start, compositions = 9, 0
    for number, stage in enumerate(stages, 1):
        end, requests = stage["end_attempts"], stage["requests"]
        checks["stage_partition"] &= bool(
            stage["stage"] == number
            and stage["start_attempts"] == start
            and start <= end <= start + 128
            and end <= len(ledger)
            and requests
        )
        checks["multiplier_sequence"] &= bool(
            np.array_equal(stage["multipliers"], lam)
            and stage["rho"] == rho
            and stage["previous_violation"] == previous
        )
        visited = set()
        for request in requests:
            attempt = request["attempt"]
            if not max(1, start) <= attempt <= end or attempt > len(ledger):
                checks["stage_partition"] = False
                continue
            row = ledger[attempt - 1]
            values = np.asarray(row["values"], dtype=float)
            merit = values[0] + 0.5 * rho * np.sum(np.minimum(0, values[1:] - lam / rho) ** 2)
            checks["merit_identity"] &= bool(
                row["x_sha256"] == request["x_sha256"]
                and np.isfinite(request["merit"])
                and abs(merit - request["merit"]) <= 1e-10 * max(1.0, abs(merit))
            )
            if attempt > start:
                visited.add(attempt)
        checks["stage_partition"] &= visited == set(range(start + 1, end + 1))
        if not requests:
            checks["selected_minimum"] = False
            continue
        expected = min(requests, key=lambda r: r["merit"])
        chosen = stage["selected"]
        checks["selected_minimum"] &= chosen == expected
        if not 1 <= chosen["attempt"] <= len(ledger):
            checks["selected_minimum"] = False
            continue
        values = np.asarray(ledger[chosen["attempt"] - 1]["values"])
        checks["selected_minimum"] &= np.array_equal(values, stage["selected_values"])
        v = max(0.0, -float(np.min(values[1:])))
        new_lam = np.maximum(0, lam - rho * values[1:])
        next_rho = rho * 10 if v > 0.25 * previous else rho
        checks["multiplier_sequence"] &= bool(
            stage["violation"] == v
            and np.array_equal(stage["updated_multipliers"], new_lam)
            and stage["next_rho"] == next_rho
        )
        is_target = stage["status"] == "construction_target"
        target_rows = [ledger[r["attempt"] - 1]["values"] for r in requests]
        targets = [v[0] <= 0.008 and min(v[1:]) >= 0 for v in target_rows]
        if is_target:
            checks["target_semantics"] &= bool(
                number == len(stages)
                and targets[-1]
                and not any(targets[:-1])
                and stage["denied"] == 0
            )
        else:
            checks["target_semantics"] &= not any(targets)
            checks["stage_partition"] &= bool(
                (
                    stage["status"] == "stage_budget_exhausted"
                    and end - start == 128
                    and stage["denied"] == 1
                )
                or (
                    stage["status"] == "solver_returned"
                    and stage["denied"] == 0
                    and "solver" in stage
                )
            )
        start, lam, rho, previous = end, new_lam, next_rho, max(v, 1e-12)
        compositions += len(requests)
    checks["stage_partition"] &= start == len(ledger)
    checks["request_accounting"] = (
        arm["residual_compositions"] == compositions
        and arm["counters"]["requests"] == 9 + compositions
    )
    target = stages[-1]["status"] == "construction_target"
    checks["termination"] = bool(
        (target and arm["stop_reason"] == "construction_target")
        or (not target and len(stages) == 8 and arm["stop_reason"] == "eight_stages_completed")
    )
    return {k: bool(v) for k, v in checks.items()}
