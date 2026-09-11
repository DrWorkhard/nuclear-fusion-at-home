from copy import deepcopy

import numpy as np
import pytest

from fusion_baselines.composite_gradient_gate import composite_gradient_gate


def qualification():
    return {
        "status": "completed",
        "all_pass": True,
        "diagnostic": {"sha256": "a" * 64},
        "states": [
            {
                "name": name,
                "real_value_errors": [0.0] * 120,
                "checks": {"zero_current_columns": True},
                "directions": [
                    {
                        "seed": seed,
                        "analytic": [1.0] * 120,
                        "steps": [
                            {"h": h, "directional_derivative": [1.0] * 120}
                            for h in (1e-12, 1e-20, 1e-28)
                        ],
                    }
                    for seed in (47, 48)
                ],
            }
            for name in ("original", "selected119")
        ],
    }


def test_composite_acceptance_preserves_failed_original_flag():
    errors = np.zeros(138)
    errors[6] = 1.2e-6
    gate = composite_gradient_gate(errors, qualification(), "a" * 64)
    assert gate["accepted"] and not gate["original_all_row_forward_difference_pass"]
    errors[130] = 1.2e-6
    assert not composite_gradient_gate(errors, qualification(), "a" * 64)["accepted"]


@pytest.mark.parametrize("corruption", ["hash", "state", "step", "values", "current"])
def test_do_not_trust_a_green_top_level_flag(corruption):
    q = deepcopy(qualification())
    if corruption == "hash":
        q["diagnostic"]["sha256"] = "b" * 64
    elif corruption == "state":
        q["states"].pop()
    elif corruption == "step":
        q["states"][0]["directions"][0]["steps"].pop()
    elif corruption == "values":
        q["states"][0]["directions"][0]["steps"][0]["directional_derivative"][0] = 1.1
    elif corruption == "current":
        q["states"][0]["checks"]["zero_current_columns"] = False
    assert not composite_gradient_gate(np.zeros(138), q, "a" * 64)["accepted"]
