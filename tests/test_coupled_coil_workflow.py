import copy

import numpy as np
import pytest

from fusion_baselines.coupled_coil_workflow import (
    cases,
    choose_search,
    derivative_checks,
    qualification_points,
    refinement,
)


def toy_rows():
    seed = np.array([0.2, -0.1, 0.7])
    rows = [dict(x=x.tolist(), J=float(x @ x), gradient=(2 * x).tolist(), status="completed")
            for x in qualification_points(seed)]
    return seed, rows


def test_exact_eight_case_matrix():
    rows = cases()
    assert len(rows) == len({r["label"] for r in rows}) == 8
    assert {(r["nbase"], r["order"]) for r in rows} == {(6, 5), (8, 7)}


def test_registered_differences_and_exact_repeat():
    seed, rows = toy_rows()
    report = derivative_checks(rows, seed)
    assert report["all_pass"] and len(report["checks"]) == 4


@pytest.mark.parametrize("mutation", [
    "missing", "coordinate", "gradient", "repeat", "nan", "status"])
def test_false_qualification_cannot_pass(mutation):
    seed, rows = toy_rows()
    rows = copy.deepcopy(rows)
    if mutation == "missing":
        rows.pop()
    elif mutation == "coordinate":
        rows[1]["x"][0] += 1e-4
    elif mutation == "gradient":
        rows[0]["gradient"][0] += 1
    elif mutation == "repeat":
        rows[-1]["J"] += 1e-9
    elif mutation == "nan":
        rows[0]["gradient"][0] = float("nan")
    else:
        rows[1]["status"] = "error"
    try:
        result = derivative_checks(rows, seed)
    except ValueError:
        return
    assert not result["all_pass"]


def test_selection_is_stable_actual_search_only():
    rows = [dict(status="completed", J=1.0, x=[1.0]),
            dict(status="error", J=-1e30, x=[2.0]),
            dict(status="completed", J=1.0, x=[3.0])]
    assert choose_search(rows) == 0
    assert choose_search([]) is None
    rows[0]["J"] = float("nan")
    with pytest.raises(ValueError):
        choose_search(rows)


def test_refinement_keeps_fixed_thresholds_and_finite_domain():
    assert refinement(1e-4, 1.005e-4)["passed"]
    assert not refinement(1e-4, 1.03e-4)["passed"]
    assert refinement(0.0, 1e-8)["passed"]
    with pytest.raises(ValueError):
        refinement(1.0, float("nan"))
