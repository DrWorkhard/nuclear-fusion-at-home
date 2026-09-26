"""Synthetic analytical curves only; no saved project candidates or native work."""

import copy
import math

import numpy as np
import pytest

from fusion_baselines import local_curvature as local


def circle(radius=0.2, order=1, phase=0.0):
    coefficients = np.zeros((3, 2 * order + 1))
    coefficients[0, 1:3] = [-radius * math.sin(phase), radius * math.cos(phase)]
    coefficients[1, 1:3] = [radius * math.cos(phase), radius * math.sin(phase)]
    return coefficients


def certify(seed=None, candidate=None, matrix=None, **kwargs):
    seed = circle() if seed is None else seed
    candidate = seed if candidate is None else candidate
    matrix = np.eye(3) if matrix is None else matrix
    return local.certify_curve(
        seed,
        candidate,
        matrix,
        deadline=kwargs.pop("deadline", 100.0),
        clock=kwargs.pop("clock", lambda: 0.0),
        **kwargs,
    )


def scripted(monkeypatch, function):
    monkeypatch.setattr(local.CurveModel, "bound", lambda self, path: function(path))


def check_scope(report):
    assert set(report) == {
        "schema_version",
        "kind",
        "caps",
        "nodes",
        "attempted",
        "curvature_pass",
        "stop_reason",
        "interval_arithmetic",
        "field_pass",
        "step4_pass",
    }
    assert report["schema_version"] == 1
    assert report["kind"] == "local-homotopy-curvature"
    assert report["interval_arithmetic"] is report["field_pass"] is report["step4_pass"] is False
    assert report["attempted"] == sum(row[1] != "pending" for row in report["nodes"])
    assert all(len(row) == 6 and len(local._encode(row)) <= 256 for row in report["nodes"])


@pytest.mark.parametrize("change", ["identical", "translation", "expansion", "contraction"])
def test_analytic_circle_homotopies_pass_with_margin(change):
    seed, target = circle(), circle()
    if change == "translation":
        target[:, 0] = [7.0, -2.5, 4.0]
    elif change == "expansion":
        target = circle(0.3)
    elif change == "contraction":
        seed = circle(0.3)
    report = certify(seed, target)
    check_scope(report)
    assert report["curvature_pass"] is True and report["stop_reason"] == "complete"
    passing = [row for row in report["nodes"] if row[1] == "pass"]
    assert passing and all(0 < row[2] and 1 / 0.3 <= row[3] <= 12 for row in passing)
    assert report["attempted"] <= 16383


@pytest.mark.parametrize(
    "matrix",
    [
        np.eye(3),
        np.diag([-1.0, 1.0, -1.0]),
        np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        np.diag([1.0, -1.0, 1.0]),
        np.diag([2.0, 2.0, 2.0]),
    ],
)
def test_actual_finite_transform_copies(matrix):
    report = certify(matrix=matrix)
    assert report["curvature_pass"] is True
    check_scope(report)


def test_matrix_is_transposed_and_inputs_privately_retained():
    seed = circle()
    seed[:, 0] = [1.0, 2.0, 3.0]
    matrix = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    expected = matrix.T @ seed
    model = local.CurveModel(seed, seed.copy(), matrix)
    seed[:] = 999.0
    matrix[:] = 0.0
    model.bound("")
    np.testing.assert_array_equal(model._s, expected)
    assert not np.array_equal(expected[:, 0], [3.0, 1.0, 2.0])


def test_period_one_differentiation_and_third_derivative_weight():
    model = local.CurveModel(circle(), circle(), np.eye(3))
    model.bound("")
    v, a = model._center(model._s, 0.0)
    assert v == pytest.approx([0.0, 2 * math.pi * 0.2, 0.0])
    assert a == pytest.approx([-((2 * math.pi) ** 2) * 0.2, 0.0, 0.0])
    expected = math.sqrt(2) * 0.2 * (2 * math.pi) ** 3
    actual = model._derivative_bound(model._s, model._zero, 3)
    assert expected < actual < expected * (1 + 1e-9)


def test_shared_lambda_cache_is_bitwise_identical_for_repeated_and_mixed_requests():
    seed, target = circle(order=5), circle(0.3, order=5, phase=0.25)
    paths = ["", "t0" * 5, "t1" * 5, "l0t0l1t1", "l1t0t1", "t0" * 8, "l0" * 7]
    fresh = {p: local._encode(local.CurveModel(seed, target, np.eye(3)).bound(p)) for p in paths}
    for order in (paths + paths, paths[::-1] + paths):
        model = local.CurveModel(seed, target, np.eye(3))
        for path in order:
            assert local._encode(model.bound(path)) == fresh[path]


def test_repeated_lambda_skips_only_unchanged_derivative_bounds(monkeypatch):
    model = local.CurveModel(circle(), circle(0.3), np.eye(3))
    calls, original = [], model._derivative_bound

    def count(*args):
        calls.append(args[-1])
        return original(*args)

    monkeypatch.setattr(model, "_derivative_bound", count)
    model.bound("t0" * 5)
    before = len(calls)
    model.bound("t1" * 5)
    assert len(calls) == before
    model.bound("l0t0")
    assert len(calls) > before


def test_transform_dot_products_use_fsum_and_small_changes_are_retained():
    seed = circle()
    seed[:, 0] = [1e16, 1.0, -1e16]
    target = seed.copy()
    target[2, 1] = 1e-320
    model = local.CurveModel(seed, target, np.ones((3, 3)))
    model.bound("")
    assert model._s[0][0] == 1.0
    assert model._es[0][0] >= (1024 * 2.0**-52) * 2e16
    untransformed = local.CurveModel(circle(), target, np.eye(3))
    untransformed.bound("")
    assert untransformed._d[2][1] == 1e-320


def test_positive_speed_with_nonpositive_padded_denominator_stays_unresolved():
    model = local.CurveModel(circle(1e-6), circle(1e-6), np.eye(3))
    vminus, upper, t, h = model.bound("t0" * 14 + "l0" * 10)
    assert vminus > 0 and upper is None and math.isfinite(t) and math.isfinite(h)


def test_homotopy_endpoints_can_be_regular_while_interior_collapses():
    seed = circle(0.1)
    model = local.CurveModel(seed, -seed, np.eye(3))
    assert 1 / 0.1 < 12  # Both endpoint geometries are the same regular circle.
    vminus, upper, _, _ = model.bound("")
    assert vminus < 0 and upper is None  # lambda=.5 has identically zero derivative.
    report = certify(seed, -seed, caps=dict(t_depth=4, lambda_depth=4, evaluations=63))
    check_scope(report)
    assert report["curvature_pass"] is False
    assert any(row[1] in ("depth", "pending") for row in report["nodes"])


def test_regular_rotated_endpoints_hide_excessive_interior_curvature():
    radius, angle = 0.1, 2 * math.pi / 3
    seed, target = circle(radius), circle(radius, phase=angle)
    assert 1 / radius < 12
    assert 1 / (radius * math.cos(angle / 2)) > 12
    path = "t0" * 12 + "l1" + "l0" * 9
    model = local.CurveModel(seed, target, np.eye(3))
    vminus, upper, _, _ = model.bound(path)
    assert vminus > 0 and upper > 12
    report = certify(seed, target, caps=dict(t_depth=4, lambda_depth=4, evaluations=63))
    assert report["curvature_pass"] is False


def test_between_node_high_mode_peak_cannot_be_certified_from_samples():
    radius, amplitude, mode = 0.2, 0.01, 8
    coefficients = circle(radius, mode)
    coefficients[2, 2 * mode - 1] = amplitude
    # On t=j/m, z=0 and z''=0; at t=(j+1/4)/m, z'=0 instead.
    sampled_curvature = radius / (radius**2 + (amplitude * mode) ** 2)
    between_curvature = math.hypot(radius, amplitude * mode**2) / radius**2
    assert sampled_curvature < 12 < between_curvature
    report = certify(coefficients, caps=dict(t_depth=10, lambda_depth=0, evaluations=255))
    check_scope(report)
    assert report["curvature_pass"] is False
    assert any(row[3] is not None and row[3] > 12 for row in report["nodes"])


@pytest.mark.parametrize("radius", [0.0, 1e-20])
def test_zero_or_near_zero_speed_is_unresolved(radius):
    report = certify(circle(radius), caps=dict(t_depth=0, lambda_depth=0, evaluations=1))
    assert report["nodes"][0][1] == "depth"
    assert report["nodes"][0][3] is None
    assert report["curvature_pass"] is False


@pytest.mark.parametrize("mutation", ["seed", "candidate", "matrix"])
@pytest.mark.parametrize("bad", [True, "number", complex(1, 2), np.nan, np.inf])
def test_nonreal_nonfinite_entries_rejected(mutation, bad):
    values = dict(seed=circle().tolist(), candidate=circle().tolist(), matrix=np.eye(3).tolist())
    values[mutation][0][0] = bad
    with pytest.raises(ValueError):
        local.CurveModel(**values)


@pytest.mark.parametrize(
    "mutation,value",
    [
        ("seed", np.zeros((3, 0))),
        ("seed", np.zeros((3, 1))),
        ("seed", np.zeros((3, 4))),
        ("seed", np.zeros((2, 3))),
        ("candidate", np.zeros((3, 5))),
        ("matrix", np.zeros((3, 4))),
        ("matrix", np.zeros((2, 3))),
        ("seed", [[1.0], [2.0, 3.0], [4.0]]),
        ("candidate", None),
        ("matrix", 1),
    ],
)
def test_shape_and_order_validation(mutation, value):
    values = dict(seed=circle(), candidate=circle(), matrix=np.eye(3))
    values[mutation] = value
    with pytest.raises(ValueError):
        local.CurveModel(**values)


def test_real_integer_inputs_and_float32_inputs_are_copied_to_binary64():
    integer = np.array([[0, 0, 1], [0, 1, 0], [0, 0, 0]])
    for value in (integer, integer.astype(np.float32), integer.tolist()):
        model = local.CurveModel(value, value, np.eye(3))
        assert all(type(v) is float for row in model._seed for v in row)
        assert certify(value)["curvature_pass"] is True


@pytest.mark.parametrize(
    "path", [None, 1, [], "t", "x0", "t2", "l-", "t0" * 15, "l0" * 11, "t0" * 25, "t０", " t0"]
)
def test_invalid_dyadic_paths(path):
    model = local.CurveModel(circle(), circle(), np.eye(3))
    with pytest.raises(ValueError):
        model.bound(path)


def test_exact_dyadic_rectangle_endpoint_convention():
    assert local._rectangle("") == (0.5, 0.5, 0.5, 0.5, 0.0, 1.0, dict(t=0, l=0))
    assert local._rectangle("t1l0t0") == (0.625, 0.25, 0.125, 0.25, 0.0, 0.5, dict(t=2, l=1))
    tc, lc, h, r, lo, hi, depths = local._rectangle("t1" * 14 + "l1" * 10)
    assert tc + h == lc + r == hi == 1.0
    assert lo == 1 - 2**-10 and depths == dict(t=14, l=10)


@pytest.mark.parametrize(
    "curvature,passed",
    [
        (12.0, True),
        (math.nextafter(12.0, math.inf), False),
        (0.0, False),
        (-1.0, False),
    ],
)
def test_exact_threshold_with_no_tolerance(monkeypatch, curvature, passed):
    scripted(monkeypatch, lambda p: [1.0, curvature, 0.0, 0.0])
    report = certify(caps=dict(t_depth=0, lambda_depth=0, evaluations=1))
    assert report["curvature_pass"] is passed
    assert report["nodes"][0][1] == ("pass" if passed else "depth")


def test_nonpositive_speed_cannot_pass_even_if_synthetic_curvature_is_small(monkeypatch):
    scripted(monkeypatch, lambda p: [-1.0, 1.0, 0.0, 0.0])
    assert certify(caps=dict(t_depth=0, lambda_depth=0, evaluations=1))["curvature_pass"] is False


def test_dfs_child_zero_first_tie_t_and_unequal_leaf_depths(monkeypatch):
    scripted(monkeypatch, lambda p: [1.0, 20.0 if p in ("", "t0") else 2.0, 1.0, 1.0])
    report = certify()
    assert [(n[0], n[1]) for n in report["nodes"]] == [
        ("", "split_t"),
        ("t0", "split_t"),
        ("t0t0", "pass"),
        ("t0t1", "pass"),
        ("t1", "pass"),
    ]
    assert report["curvature_pass"] is True and report["attempted"] == 5


@pytest.mark.parametrize(
    "weights,limits,expected",
    [
        ((2.0, 1.0), (1, 1), "split_t"),
        ((1.0, 2.0), (1, 1), "split_l"),
        ((2.0, 1.0), (0, 1), "split_l"),
        ((1.0, 2.0), (1, 0), "split_t"),
        ((1.0, 1.0), (0, 0), "depth"),
    ],
)
def test_split_heuristic_and_exhausted_axis_fallback(monkeypatch, weights, limits, expected):
    scripted(monkeypatch, lambda p: [1.0, 20.0, *weights])
    report = certify(caps=dict(t_depth=limits[0], lambda_depth=limits[1], evaluations=1))
    assert report["nodes"][0][1] == expected


def test_evaluation_budget_preserves_complete_dfs_frontier(monkeypatch):
    scripted(monkeypatch, lambda p: [1.0, 20.0, 2.0, 1.0])
    report = certify(caps=dict(t_depth=14, lambda_depth=10, evaluations=2))
    assert [(r[0], r[1]) for r in report["nodes"]] == [
        ("", "split_t"),
        ("t0", "split_t"),
        ("t0t0", "pending"),
        ("t0t1", "pending"),
        ("t1", "pending"),
    ]
    assert all(r[2:] == [None] * 4 for r in report["nodes"][2:])
    assert report["stop_reason"] == "evaluation-budget" and report["attempted"] == 2
    check_scope(report)


def test_maximum_registered_path_and_frontier_are_bounded(monkeypatch):
    scripted(monkeypatch, lambda p: [1.0, 20.0, 2.0, 1.0])
    report = certify(caps=dict(t_depth=14, lambda_depth=10, evaluations=24))
    pending = [r for r in report["nodes"] if r[1] == "pending"]
    assert len(pending) == 25 and max(len(r[0]) for r in report["nodes"]) == 48
    assert report["attempted"] == 24


def test_full_registered_evaluation_cap_is_exact(monkeypatch):
    scripted(monkeypatch, lambda p: [1.0, 20.0, 2.0, 1.0])
    report = certify()
    assert report["caps"] == dict(t_depth=14, lambda_depth=10, evaluations=16383)
    assert report["attempted"] == 16383
    assert report["stop_reason"] == "evaluation-budget"
    assert 1 <= sum(r[1] == "pending" for r in report["nodes"]) <= 25
    check_scope(report)


def test_arithmetic_leaf_does_not_drop_other_pending_branches(monkeypatch):
    def bound(path):
        if path == "t0":
            raise ArithmeticError("synthetic one-branch arithmetic failure")
        return [1.0, 20.0 if path == "" else 2.0, 1.0, 0.0]

    scripted(monkeypatch, bound)
    report = certify()
    assert [(r[0], r[1]) for r in report["nodes"]] == [
        ("", "split_t"),
        ("t0", "arithmetic"),
        ("t1", "pass"),
    ]
    assert report["stop_reason"] == "complete" and report["curvature_pass"] is False
    assert report["attempted"] == 3


@pytest.mark.parametrize(
    "caps",
    [
        {},
        dict(t_depth=14, lambda_depth=10, evaluations=16384),
        dict(t_depth=15, lambda_depth=10, evaluations=1),
        dict(t_depth=14, lambda_depth=11, evaluations=1),
        dict(t_depth=-1, lambda_depth=0, evaluations=1),
        dict(t_depth=0, lambda_depth=0, evaluations=0),
        dict(t_depth=True, lambda_depth=0, evaluations=1),
        dict(t_depth=0, lambda_depth=0, evaluations=1.0),
        dict(t_depth=0, lambda_depth=0, evaluations=1, extra=True),
        [],
    ],
)
def test_caps_cannot_exceed_registration_or_change_types(caps):
    with pytest.raises(ValueError):
        certify(caps=caps)


def test_cap_copy_is_private_even_if_clock_changes_caller_mapping(monkeypatch):
    scripted(monkeypatch, lambda p: [1.0, 20.0, 1.0, 0.0])
    caps = dict(t_depth=0, lambda_depth=0, evaluations=1)

    def clock():
        caps["evaluations"] = 999999
        return 0.0

    result = certify(caps=caps, clock=clock)
    assert result["caps"] == dict(t_depth=0, lambda_depth=0, evaluations=1)


@pytest.mark.parametrize(
    "during,expected_actions",
    [
        ("before", [("", "pending")]),
        ("inside", [("", "deadline")]),
        ("after", [("", "pass")]),
    ],
)
def test_deadline_before_during_after_last_bound(monkeypatch, during, expected_actions):
    scripted(monkeypatch, lambda p: [1.0, 2.0, 0.0, 0.0])
    readings = iter(
        {"before": [1.0, 1.0], "inside": [0.0, 1.0, 1.0], "after": [0.0, 0.0, 1.0]}[during]
    )
    result = certify(deadline=1.0, clock=lambda: next(readings))
    assert [(r[0], r[1]) for r in result["nodes"]] == expected_actions
    assert result["stop_reason"] == "deadline" and result["curvature_pass"] is False
    assert result["attempted"] == (0 if during == "before" else 1)


def test_deadline_inside_node_retains_remaining_frontier(monkeypatch):
    scripted(monkeypatch, lambda p: [1.0, 20.0, 2.0, 1.0])
    readings = iter([0.0, 0.0, 0.0, 1.0, 1.0])
    report = certify(deadline=1.0, clock=lambda: next(readings))
    assert [(r[0], r[1]) for r in report["nodes"]] == [
        ("", "split_t"),
        ("t0", "deadline"),
        ("t1", "pending"),
    ]
    assert report["nodes"][1][2:] == [1.0, 20.0, 2.0, 1.0]
    assert report["attempted"] == 2 and report["curvature_pass"] is False


def test_deadline_during_serialization_cannot_return_success(monkeypatch):
    scripted(monkeypatch, lambda p: [1.0, 2.0, 0.0, 0.0])
    expired, original = False, local._encode

    def encode(value):
        nonlocal expired
        result = original(value)
        if type(value) is dict:
            expired = True
        return result

    monkeypatch.setattr(local, "_encode", encode)
    report = certify(deadline=1.0, clock=lambda: 1.0 if expired else 0.0)
    assert report["stop_reason"] == "deadline" and report["curvature_pass"] is False


@pytest.mark.parametrize("mode", ["transform", "difference", "derivative"])
def test_finite_overflow_is_attempted_arithmetic_not_schema_failure(mode):
    seed, target, matrix = circle(), circle(), np.eye(3)
    if mode == "transform":
        seed[0, 0], matrix[0, 0] = 1e308, 2.0
    elif mode == "difference":
        seed[0, 0], target[0, 0] = -1e308, 1e308
    else:
        seed[0, 1] = 1e307
    model = local.CurveModel(seed, target, matrix)  # No transformed arithmetic here.
    with pytest.raises(ArithmeticError):
        model.bound("")
    report = certify(seed, target, matrix)
    assert report["attempted"] == 1
    assert report["nodes"] == [["", "arithmetic", None, None, None, None]]
    assert report["stop_reason"] == "complete" and report["curvature_pass"] is False


def test_arithmetic_failure_during_deadline_is_still_counted(monkeypatch):
    def bound(path):
        raise ArithmeticError("synthetic overflow")

    scripted(monkeypatch, bound)
    readings = iter([0.0, 1.0, 1.0])
    report = certify(deadline=1.0, clock=lambda: next(readings))
    assert report["nodes"] == [["", "arithmetic", None, None, None, None]]
    assert report["attempted"] == 1 and report["stop_reason"] == "deadline"


@pytest.mark.parametrize("deadline", [True, None, "1", np.nan, np.inf, -1.0])
def test_invalid_absolute_deadlines(deadline):
    with pytest.raises(ValueError):
        certify(deadline=deadline)


@pytest.mark.parametrize("readings", [[True], [-1.0], [np.nan], [np.inf], [2.0, 1.0]])
def test_clock_corruption_is_execution_failure(monkeypatch, readings):
    scripted(monkeypatch, lambda p: [1.0, 2.0, 0.0, 0.0])
    values = iter(readings)
    with pytest.raises(ValueError):
        certify(clock=lambda: next(values))


def test_clock_hook_failure_propagates(monkeypatch):
    scripted(monkeypatch, lambda p: [1.0, 2.0, 0.0, 0.0])

    def bad_clock():
        raise OSError("synthetic clock unavailable")

    with pytest.raises(OSError):
        certify(clock=bad_clock)


def test_node_and_curve_byte_limits_are_execution_errors(monkeypatch):
    scripted(monkeypatch, lambda p: [1.0, 2.0, 0.0, 0.0])
    with monkeypatch.context() as patch:
        patch.setattr(local, "MAX_NODE_BYTES", 1)
        with pytest.raises(ValueError, match="node exceeds"):
            certify()
    monkeypatch.setattr(local, "MAX_REPORT_BYTES", 1)
    with pytest.raises(ValueError, match="report exceeds"):
        certify()


def test_preregistered_node_count_envelope_fits_existing_json_store():
    node = local._node(
        "t1" * 14 + "l1" * 10,
        "arithmetic",
        [
            -1.234567890123456e308,
            1.234567890123456e308,
            1.234567890123456e308,
            1.234567890123456e308,
        ],
    )
    assert len(local._encode(node)) <= 256
    # Byte-envelope test only: these repeated paths are deliberately NOT a
    # valid tree, and are never presented as a mathematical certificate.
    pseudo_report = dict(
        schema_version=1,
        kind="local-homotopy-curvature",
        caps=dict(t_depth=14, lambda_depth=10, evaluations=16383),
        nodes=[copy.deepcopy(node) for _ in range(16383 + 25)],
        attempted=16383,
        curvature_pass=False,
        stop_reason="evaluation-budget",
        interval_arithmetic=False,
        field_pass=False,
        step4_pass=False,
    )
    assert len(local._encode(pseudo_report)) < 8 * 1024**2
