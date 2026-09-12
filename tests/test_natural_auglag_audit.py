from copy import deepcopy

import pytest

from fusion_baselines.natural_auglag_audit import audit_stages


def fixture():
    values = [1.0] + [1.0] * 137
    ledger = [dict(attempt=i, x_sha256=str(i), values=values) for i in range(1, 10)]
    stages = []
    for i in range(1, 9):
        point = dict(attempt=9, x_sha256="9", merit=1.0)
        stages.append(
            dict(
                stage=i,
                start_attempts=9,
                end_attempts=9,
                requests=[point],
                selected=point.copy(),
                selected_values=values,
                rho=10.0,
                multipliers=[0.0] * 137,
                updated_multipliers=[0.0] * 137,
                next_rho=10.0,
                previous_violation=1.0 if i == 1 else 1e-12,
                violation=0.0,
                status="solver_returned",
                solver={},
                denied=0,
            )
        )
    return dict(
        evaluations=ledger,
        stages=stages,
        residual_compositions=8,
        counters=dict(requests=17),
        stop_reason="eight_stages_completed",
    )


@pytest.mark.parametrize(
    "change", [None, "merit", "rho", "multiplier", "selection", "budget", "target", "work"]
)
def test_staged_audit_recomputes_instead_of_trusting_flags(change):
    arm = deepcopy(fixture())
    row = arm["stages"][2]
    if change == "merit":
        row["requests"][0]["merit"] += 0.1
    elif change == "rho":
        row["rho"] = 100.0
    elif change == "multiplier":
        row["updated_multipliers"][0] = 1.0
    elif change == "selection":
        row["selected"]["attempt"] = 1
    elif change == "budget":
        row["end_attempts"] += 1
    elif change == "target":
        row["status"] = "construction_target"
    elif change == "work":
        arm["residual_compositions"] += 1
    assert all(audit_stages(arm).values()) is (change is None)
