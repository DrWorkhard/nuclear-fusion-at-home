from copy import deepcopy

import numpy as np
import pytest

from fusion_baselines.gauge_action import gauge_chain_rule
from fusion_baselines.gauge_audit import audit_cell_binding, audit_family
from fusion_baselines.radial_action import radial_sign_screen


def fixture():
    a0, gauges = 2.0, {}
    for slope in (-1, 0, 1):
        d = -1 + slope * 0.1
        actions = np.array([[[a0 - h * d, a0 + h * d] for h in (0.04, 0.02, 0.01)]] * 3)
        gauges[str(slope)] = dict(
            action_stencil=actions.tolist(), **radial_sign_screen(actions, a0)
        )
    aa = np.array([[a0 - h * 0.1, a0 + h * 0.1] for h in (0.01, 0.005)])
    original = dict(**gauges["0"], finest_anchor_action=a0)
    family = dict(
        gauges=gauges,
        finest_anchor_action=a0,
        alpha_action_stencil=aa.tolist(),
        old_zero_sign_equal=True,
        old_zero_stencil_exact=True,
        gauge_signs_equal=True,
        chain={
            str(c): gauge_chain_rule(
                gauges["0"]["derivatives"][-1][-1], gauges[str(c)]["derivatives"][-1][-1], aa, a0, c
            )
            for c in (-1, 1)
        },
    )
    return family, original


@pytest.mark.parametrize(
    "mutation", [None, "sign", "derivative", "chain", "alpha", "anchor", "old_flag"]
)
def test_arithmetic_audit_rejects_mutated_derived_values(mutation):
    family, original = deepcopy(fixture())
    if mutation == "sign":
        family["gauges"]["1"]["sign"] = "positive"
    elif mutation == "derivative":
        family["gauges"]["0"]["derivatives"][-1][-1] = 10.0
    elif mutation == "chain":
        family["chain"]["-1"]["chain_pass"] = False
    elif mutation == "alpha":
        family["alpha_action_stencil"][0][0] += 0.1
    elif mutation == "anchor":
        family["finest_anchor_action"] *= 2
    elif mutation == "old_flag":
        family["old_zero_stencil_exact"] = False
    assert all(audit_family(family, original).values()) is (mutation is None)


@pytest.mark.parametrize("mutation", [None, "interval", "action", "duplicate", "index"])
def test_well_interval_and_stencil_binding(mutation):
    family, original = fixture()
    anchor = dict(phi_interval=[4.0, 5.0], action=2.0, complete=True)
    family["anchor"] = original["anchor"] = anchor
    cell = dict(matching_pass=True, families=[family], wells=[])
    for c in (-1, 0, 1):
        for level in range(3):
            for s in (0.46, 0.48, 0.49, 0.5, 0.51, 0.52, 0.54):
                action = 2.0
                if s != 0.5:
                    index = [0.04, 0.02, 0.01].index(round(abs(s - 0.5), 2))
                    action = family["gauges"][str(c)]["action_stencil"][level][index][int(s > 0.5)]
                cell["wells"].append(
                    dict(
                        kind="radial",
                        slope=c,
                        level=level,
                        s=s,
                        wells=[{**anchor, "action": action}],
                        matches=[0],
                    )
                )
    for i, h in enumerate((0.01, 0.005)):
        for sign in (-1, 1):
            action = family["alpha_action_stencil"][i][int(sign > 0)]
            cell["wells"].append(
                dict(
                    kind="alpha",
                    alpha_offset=sign * h,
                    wells=[{**anchor, "action": action}],
                    matches=[0],
                )
            )
    if mutation == "interval":
        cell["wells"][0]["wells"][0]["phi_interval"] = [4.5, 5.5]
    elif mutation == "action":
        cell["wells"][0]["wells"][0]["action"] += 0.1
    elif mutation == "duplicate":
        cell["wells"][0] = deepcopy(cell["wells"][1])
    elif mutation == "index":
        cell["wells"][0]["matches"] = [1]
    assert all(audit_cell_binding(cell, dict(families=[original]), 2).values()) is (
        mutation is None
    )
