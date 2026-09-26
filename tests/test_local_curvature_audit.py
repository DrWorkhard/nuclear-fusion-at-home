"""Independent analytical controls and adversarial certificate-audit tests."""

import copy
import math

import numpy as np
import pytest

from fusion_baselines import local_curvature_audit as audit


def circle(radius=0.2, order=1):
    coefficients = np.zeros((3, 2 * order + 1))
    coefficients[0, 2], coefficients[1, 1] = radius, radius
    return coefficients


def fixture_report(seed=None, candidate=None, caps=None):
    """Synthetic tree fixture; this is not an independent producer test."""
    seed = circle() if seed is None else seed
    candidate = seed if candidate is None else candidate
    caps = dict(t_depth=14, lambda_depth=10, evaluations=16383) if caps is None else caps
    checker = audit._IndependentCurve(seed, candidate, np.eye(3))
    rows, stack, count = [], [""], 0
    while stack:
        path = stack.pop()
        if count >= caps["evaluations"]:
            rows.append([path, "pending", None, None, None, None])
            continue
        count += 1
        values = checker.values(path)
        depths = audit._interval(path)[2]
        if values[1] is not None and values[1] <= 12:
            action = "pass"
        elif depths == [caps["t_depth"], caps["lambda_depth"]]:
            action = "depth"
        else:
            use_t = depths[0] < caps["t_depth"] and (
                depths[1] == caps["lambda_depth"] or values[2] >= values[3])
            a = "t" if use_t else "l"
            action = "split_" + a
            stack.extend([path + a + "1", path + a + "0"])
        rows.append([path, action, *values])
    has_pending = any(r[1] == "pending" for r in rows)
    return dict(schema_version=1, kind="local-homotopy-curvature", caps=caps, nodes=rows,
                attempted=count,
                curvature_pass=all(r[1] in ("pass", "split_t", "split_l") for r in rows),
                stop_reason="evaluation-budget" if has_pending else "complete",
                interval_arithmetic=False, field_pass=False, step4_pass=False)


def check(report, seed=None, candidate=None, **kwargs):
    seed = circle() if seed is None else seed
    candidate = seed if candidate is None else candidate
    return audit.audit_curve(seed, candidate, np.eye(3), report,
                             deadline=kwargs.pop("deadline", 120.0),
                             clock=kwargs.pop("clock", lambda: 0.0), **kwargs)


def test_period_one_global_derivatives_and_local_circle_bound():
    model = audit._IndependentCurve(circle(), circle(), np.eye(3))
    result = model.values("t0" * 8)
    assert result[0] > 0
    assert 5 < result[1] < 12
    for k in (1, 2, 3):
        actual = model._B(circle(), np.zeros((3, 3)), k)
        expected = math.sqrt(2) * 0.2 * (2 * math.pi)**k
        assert actual >= expected
        assert actual == pytest.approx(expected, rel=2e-10)


def test_nonideal_actual_matrix_and_transpose_used():
    source = circle()
    matrix = np.array([[1.0, 0.2, 0.0], [0.0, 0.9, 0.1], [0.0, 0.0, 1.1]])
    model = audit._IndependentCurve(source, source, matrix)
    model.values("t0" * 8)
    np.testing.assert_array_equal(np.asarray(model.s), matrix.T @ source)
    assert not np.array_equal(model.s, matrix @ source)


def test_translation_scaling_and_input_immutability():
    seed = circle()
    target = circle(0.25)
    target[:, 0] = [12, -5, 1]
    before = target.copy()
    model = audit._IndependentCurve(seed, target, np.eye(3))
    for path in ("t0" * 8 + "l0" * 6, "t1" * 8 + "l1" * 6):
        k = model.values(path)[1]
        assert k is not None and 4 < k < 12
    np.testing.assert_array_equal(target, before)


def test_homotopy_collapse_and_interior_curvature_failure():
    seed = circle()
    collapse = audit._IndependentCurve(seed, -seed, np.eye(3))
    assert collapse.values("t0" * 8)[1] is None  # lambda center is exactly 1/2.
    seed = circle(0.1)
    target = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]) @ seed
    model = audit._IndependentCurve(seed, target, np.eye(3))
    # Endpoint radii .1 give curvature10. Midpoint radius .1/sqrt2 exceeds12.
    assert 1 / (0.1 / math.sqrt(2)) > 12
    near_midpoint = "t0" * 14 + "l0" + "l1" * 9
    bound = model.values(near_midpoint)[1]
    assert bound is None or bound > 12


@pytest.mark.parametrize("radius", [1 / 12, 0.08, 1e-100, 0.0])
def test_threshold_or_singular_circle_cannot_pass(radius):
    model = audit._IndependentCurve(circle(radius), circle(radius), np.eye(3))
    upper = model.values("t0" * 14)[1]
    assert upper is None or upper > 12


@pytest.mark.parametrize("bad", [True, "0.2", complex(0.2, 0), math.inf, math.nan])
def test_bad_scalar_inputs_rejected(bad):
    seed = circle().tolist()
    seed[0][2] = bad
    with pytest.raises(ValueError):
        audit._IndependentCurve(seed, circle(), np.eye(3))


@pytest.mark.parametrize("seed,candidate,matrix", [
    (np.zeros((3, 2)), np.zeros((3, 2)), np.eye(3)),
    (circle(), np.zeros((3, 5)), np.eye(3)),
    (circle(), circle(), np.eye(2)),
])
def test_bad_shapes(seed, candidate, matrix):
    with pytest.raises(ValueError):
        audit._IndependentCurve(seed, candidate, matrix)


@pytest.mark.parametrize("path", ["t", "x0", "t2", "l00", "t0" * 15, "l0" * 11, None])
def test_invalid_paths(path):
    with pytest.raises(ValueError):
        audit._IndependentCurve(circle(), circle(), np.eye(3)).values(path)


def test_complete_synthetic_report_and_negative_budget():
    positive = fixture_report()
    assert check(positive)["curvature_pass"] is True
    budget = fixture_report(caps=dict(t_depth=14, lambda_depth=10, evaluations=3))
    result = check(budget)
    assert result["audit_pass"] is True and result["curvature_pass"] is False
    assert result["pending_leaves"] > 0 and result["attempted"] == 3


def test_unequal_leaf_depths_are_valid_complete_coverage():
    seed = circle()
    seed[0, 2] = 0.3
    report = fixture_report(seed, seed)
    depths = {len(row[0]) for row in report["nodes"] if row[1] == "pass"}
    assert len(depths) > 1
    assert check(report, seed, seed)["curvature_pass"] is True


def test_nonnegative_report_quantities_even_within_absolute_tolerance():
    with pytest.raises(ValueError, match="negative"):
        audit._compare([1.0, -1e-15, 0.0, 0.0], [1.0, 1e-15, 0.0, 0.0])


def test_zero_upper_bound_cannot_pass_via_absolute_comparison_tolerance():
    seed = circle(1e14)
    report = fixture_report(seed, seed)
    assert report["curvature_pass"] is True
    for row in report["nodes"]:
        if row[1] == "pass":
            row[3] = 0.0
    with pytest.raises(ValueError, match="strict curvature gate"):
        check(report, seed, seed)


def test_bound_encloses_interior_samples_of_nonplanar_homotopy():
    seed, target = circle(order=3), circle(order=3)
    target[0, 4], target[1, 3], target[2, 6] = 0.003, -0.004, 0.002
    model = audit._IndependentCurve(seed, target, np.eye(3))
    paths = ["t0t1t0t1t0t1t0t1l0l1l0l1", "t1t1t0t0t1t1t0t0l1l0l1l0"]
    for path in paths:
        (t, lam), (h, r), _ = audit._interval(path)
        low, upper, _, _ = model.values(path)
        assert low > 0 and upper is not None
        for ti in np.linspace(t - h, t + h, 7):
            for li in np.linspace(lam - r, lam + r, 5):
                coefficients = seed + li * (target - seed)
                modes = np.arange(1, 4)
                omega = 2 * np.pi * modes
                phases = omega * ti
                v = (omega * (coefficients[:, 1::2] * np.cos(phases)
                              - coefficients[:, 2::2] * np.sin(phases))).sum(axis=1)
                a = (-omega**2 * (coefficients[:, 1::2] * np.sin(phases)
                                 + coefficients[:, 2::2] * np.cos(phases))).sum(axis=1)
                actual = np.linalg.norm(np.cross(v, a)) / np.linalg.norm(v)**3
                assert np.linalg.norm(v) >= low
                assert actual <= upper


@pytest.mark.parametrize("kind", ["missing", "duplicate", "order", "path", "bound", "axis",
                                  "count", "pass", "scope", "extra", "cap", "bool_count"])
def test_tampered_reports_rejected(kind):
    r = fixture_report()
    if kind == "missing":
        r["nodes"].pop()
    elif kind == "duplicate":
        r["nodes"].append(copy.deepcopy(r["nodes"][-1]))
    elif kind == "order":
        r["nodes"][1], r["nodes"][2] = r["nodes"][2], r["nodes"][1]
    elif kind == "path":
        r["nodes"][-1][0] += "t0"
    elif kind == "bound":
        r["nodes"][-1][3] = 0.0
    elif kind == "axis":
        r["nodes"][0][1] = "split_l"
    elif kind == "count":
        r["attempted"] -= 1
    elif kind == "pass":
        r["curvature_pass"] = False
    elif kind == "scope":
        r["interval_arithmetic"] = True
    elif kind == "extra":
        r["relaxed_limit"] = 13
    elif kind == "cap":
        r["caps"]["evaluations"] = 16384
    else:
        r["attempted"] = True
    with pytest.raises(ValueError):
        check(r)


def test_deadline_before_during_and_after_last_bound():
    r = fixture_report()
    r["curvature_pass"] = False
    r["stop_reason"] = "deadline"
    assert check(r)["curvature_pass"] is False  # Even if all mathematical leaves passed.
    root = audit._IndependentCurve(circle(), circle(), np.eye(3)).values("")
    r["nodes"] = [["", "deadline", *root]]
    r["attempted"] = 1
    assert check(r)["unresolved_leaves"] == 1
    r["nodes"] = [["", "pending", None, None, None, None]]
    r["attempted"] = 0
    assert check(r)["pending_leaves"] == 1
    r["stop_reason"] = "evaluation-budget"
    with pytest.raises(ValueError, match="cap stop"):
        check(r)


def test_audit_own_deadlines_and_no_pass_after_last_check():
    r = fixture_report()
    with pytest.raises(TimeoutError):
        check(r, clock=lambda: 120.0)
    count = 0

    def clock():
        nonlocal count
        count += 1
        return 0.0

    check(r, clock=clock)
    total = count
    count = 0

    def expiring():
        nonlocal count
        count += 1
        return 120.0 if count == total else 0.0

    with pytest.raises(TimeoutError):
        check(r, clock=expiring)


@pytest.mark.parametrize("bad", [-1, math.nan, math.inf, True, "1"])
def test_invalid_clock_or_deadline(bad):
    r = fixture_report()
    with pytest.raises(ValueError):
        check(r, deadline=bad)
    with pytest.raises(ValueError):
        check(r, clock=lambda: bad)


def test_backward_clock_is_not_accepted():
    r = fixture_report()
    values = iter([2.0, 1.0])
    with pytest.raises(ValueError, match="backward"):
        check(r, clock=lambda: next(values))


def test_independent_finite_overflow_is_negative_arithmetic_leaf():
    seed = np.full((3, 3), 1e308)
    matrix = np.full((3, 3), 1e308)
    r = dict(schema_version=1, kind="local-homotopy-curvature", caps=dict(audit._MAXIMA),
             nodes=[["", "arithmetic", None, None, None, None]], attempted=1,
             curvature_pass=False, stop_reason="complete", interval_arithmetic=False,
             field_pass=False, step4_pass=False)
    result = audit.audit_curve(seed, seed, matrix, r, deadline=120, clock=lambda: 0)
    assert result["audit_pass"] and not result["curvature_pass"]
    with pytest.raises(ValueError, match="not independently reproduced"):
        check(r)


@pytest.mark.parametrize("case", ["same", "translated", "scaled", "collapse", "interior",
                                  "threshold", "zero", "nonideal", "budget"])
def test_independently_authored_producer_reports(case):
    # Producer first imported after the independent scalar arithmetic and its
    # analytical/adversarial controls were implemented. Sharing is at the report
    # interface only, never inside the checking implementation.
    from fusion_baselines.local_curvature import certify_curve

    seed, candidate, matrix = circle(), circle(), np.eye(3)
    caps = dict(t_depth=10, lambda_depth=8, evaluations=1023)
    expect_pass = case in ("same", "translated", "scaled", "nonideal")
    if case == "translated":
        candidate[:, 0] = [10, -1, 2]
    elif case == "scaled":
        candidate = circle(0.22)
    elif case == "collapse":
        candidate = -seed
    elif case == "interior":
        seed = circle(0.1)
        candidate = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]) @ seed
    elif case == "threshold":
        seed = candidate = circle(1 / 12)
    elif case == "zero":
        seed = candidate = circle(0)
    elif case == "nonideal":
        matrix = np.array([[1, 0.03, 0], [0, 1.1, 0], [0.01, 0, 1]])
    elif case == "budget":
        caps["evaluations"] = 2
    report = certify_curve(seed, candidate, matrix, caps=caps, deadline=120, clock=lambda: 0)
    result = audit.audit_curve(seed, candidate, matrix, report, deadline=120, clock=lambda: 0)
    assert result["audit_pass"] is True
    assert result["curvature_pass"] is expect_pass
    assert result["attempted"] == report["attempted"]
