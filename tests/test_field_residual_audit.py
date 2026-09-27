"""Analytical controls for the separately authored scalar field diagnosis."""

import ast
import copy
import math
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines import field_residual_audit as audit


def fields(residuals, magnitudes=None):
    magnitudes = [1.0] * len(residuals) if magnitudes is None else magnitudes
    return [[m * r, m * math.sqrt(1 - r * r), 0.0]
            for r, m in zip(residuals, magnitudes, strict=True)]


def case(control=(0.2, 0.4), proposal=(0.1, 0.2), *, weights=None, b2=1.0):
    return (fields(control), fields(proposal), [[1.0, 0.0, 0.0]] * len(control),
            [1.0] * len(control) if weights is None else weights, b2)


def test_parallel_improvement_control_origin_and_both_spaces():
    result = audit.analyze_pair(*case())
    for row in result["residuals"].values():
        assert row["projection_resolved"] is True
        assert row["alignment"] == pytest.approx(1.0)
        assert row["aligned_fraction"] == pytest.approx(1.0)
        assert row["alpha"] == pytest.approx(2.0)
        assert row["beta"] == pytest.approx(1.0)
        assert row["fit_norm"] == pytest.approx(0.0, abs=1e-15)
        assert row["fit_fraction"] == pytest.approx(0.0, abs=1e-15)
        assert row["delta_norm"] < 0
        assert abs(row["orthogonality"]) < 1e-15
        assert row["pythagoras_error"] < 1e-15
    assert result["residuals"]["objective"]["fit_limit_ratio"] is None
    assert result["residuals"]["normal"]["fit_limit_ratio"] == pytest.approx(0, abs=1e-11)
    assert result["metrics"]["control"]["normal_rms"] == pytest.approx(math.sqrt(0.1))
    assert result["metrics"]["control"]["JN"] == pytest.approx(0.05)
    assert result["metrics"]["deltas"]["JN"] == pytest.approx(-0.0375)


@pytest.mark.parametrize(("control", "proposal", "alpha", "alignment"), [
    ([0.2], [0.3], -2.0, -1.0),
    ([0.2], [-0.1], 2 / 3, 1.0),
    ([-0.2], [0.1], 2 / 3, 1.0),
    ([0.2], [0.0], 1.0, 1.0),
])
def test_signed_parallel_cases(control, proposal, alpha, alignment):
    result = audit.analyze_pair(*case(control, proposal))
    for row in result["residuals"].values():
        assert row["alpha"] == pytest.approx(alpha)
        assert row["beta"] == pytest.approx(alpha - 1)
        assert row["alignment"] == pytest.approx(alignment)
        assert row["fit_norm"] == pytest.approx(0.0, abs=1e-15)


def test_orthogonal_and_partially_aligned_responses():
    orthogonal = audit.analyze_pair(*case([0.2, 0], [0.2, 0.1]))
    row = orthogonal["residuals"]["normal"]
    assert row["alpha"] == 0.0
    assert row["aligned_fraction"] == 0.0
    assert row["fit_fraction"] == pytest.approx(1.0)
    assert row["fit_limit_ratio"] == pytest.approx(math.sqrt(0.02) / 1e-4)
    partial = audit.analyze_pair(*case([0.2, 0.2], [0.1, 0.2]))
    row = partial["residuals"]["normal"]
    assert row["aligned_fraction"] == pytest.approx(0.5)
    assert row["alpha"] == pytest.approx(2.0)
    assert row["fit_norm"] == pytest.approx(math.sqrt(0.02))


def test_nonuniform_weights_and_nonunit_normals_are_normalized():
    args = list(case([0.1, 0.2], [0.05, 0.1], weights=[1, 3], b2=4))
    args[2] = [[7, 0, 0], [0.3, 0, 0]]
    report = audit.analyze_pair(*args)
    assert report["metrics"]["control"]["normal_rms"] == pytest.approx(math.sqrt(0.0325))
    assert report["metrics"]["control"]["JN"] == pytest.approx(0.0325 / 8)
    args[3] = [100, 300]
    assert audit.compare(audit.analyze_pair(*args), report) is True


def test_pointwise_magnitude_distinguishes_objective_and_acceptance():
    control = fields([0.2, 0.4], [1, 2])
    proposal = fields([0.1, 0.2], [2, 4])
    report = audit.analyze_pair(control, proposal, [[1, 0, 0]] * 2, [1, 1], 1)
    assert report["metrics"]["deltas"]["normal_rms"] < 0
    assert report["metrics"]["deltas"]["JN"] == pytest.approx(0)
    assert report["residuals"]["normal"]["projection_resolved"] is True
    assert report["residuals"]["objective"]["projection_resolved"] is False
    assert report["split"]["numerator_norm_squared"] == pytest.approx(0)
    assert report["split"]["denominator_norm_squared"] > 0


def test_uniform_scaling_cancels_only_normal_residual_and_keeps_cross_term():
    control = fields([0.2, -0.4])
    proposal = [[2 * x for x in row] for row in control]
    report = audit.analyze_pair(control, proposal, [[1, 0, 0]] * 2, [1, 1], 1)
    assert report["residuals"]["normal"]["projection_resolved"] is False
    assert report["metrics"]["proposal"]["JN"] == pytest.approx(
        4 * report["metrics"]["control"]["JN"])
    split = report["split"]
    assert split["numerator_norm_squared"] == pytest.approx(0.1)
    assert split["denominator_norm_squared"] == pytest.approx(0.1)
    assert split["cross_term"] == pytest.approx(-0.2)
    assert split["control_numerator_term"] == pytest.approx(0.2)
    assert split["control_denominator_term"] == pytest.approx(-0.2)
    assert split["delta_squared_norm"] == 0.0
    assert split["energy_identity_error"] < 1e-15
    assert split["vector_identity_error"] < 1e-15


def test_reported_delta_squared_norm_is_signed_endpoint_change_not_secant_energy():
    report = audit.analyze_pair(*case([0.2], [0.1]))
    split = report["split"]
    assert split["delta_squared_norm"] == pytest.approx(-0.03)
    assert report["residuals"]["normal"]["secant_norm"] ** 2 == pytest.approx(0.01)


def test_independent_producer_agrees_for_nonuniform_fields_weights_and_normals():
    # Import here only after separately authored implementations were frozen.
    from fusion_baselines.field_residuals import analyze_pair as produce

    args = (fields([0.2, -0.4, 0.3], [1.3, 2.7, 0.9]),
            fields([0.17, -0.3, 0.27], [1.7, 2.1, 1.1]),
            [[7, 0, 0], [3, 0, 0], [0.3, 0, 0]], [1, 3, 7], 2.7)
    assert audit.compare(produce(*args), audit.analyze_pair(*args)) is True


@pytest.mark.parametrize("value", [0.0, 1e-13, 1e-12, math.nextafter(1e-12, 0)])
def test_zero_and_unresolved_secant_have_no_projection_quantities(value):
    report = audit.analyze_pair(*case([0.0], [value]))
    for row in report["residuals"].values():
        assert row["projection_resolved"] is False
        assert row["secant_norm"] == pytest.approx(value, abs=1e-30)
        for key in audit._PROJECTION:
            assert row[key] is None


def test_resolved_zero_control_has_fit_but_no_alignment_or_relative_fraction():
    report = audit.analyze_pair(*case([0.0], [math.nextafter(1e-12, math.inf)]))
    for row in report["residuals"].values():
        assert row["projection_resolved"] is True
        assert row["alpha"] == 0.0
        assert row["beta"] == -1.0
        assert row["fit_norm"] == 0.0
        assert row["alignment"] is None
        assert row["aligned_fraction"] is None
        assert row["fit_fraction"] is None


def test_exact_nonzero_repeated_state_remains_unresolved_not_perfect_fit():
    result = audit.analyze_pair(*case([0.2], [0.2]))
    for row in result["residuals"].values():
        assert row["control_norm"] > 0
        assert row["secant_norm"] == 0
        assert row["fit_norm"] is None


def test_nearly_perfect_alignment_keeps_explicit_nonnegative_fitted_norm():
    report = audit.analyze_pair(*case([0.2, 0.2], [0.1, 0.1 + 1e-10]))
    row = report["residuals"]["normal"]
    assert 0 < row["fit_norm"] < 1e-9
    assert row["fit_fraction"] > 0
    assert abs(row["orthogonality"]) < 1e-12


def test_large_finite_coefficient_is_descriptor_not_clipped():
    report = audit.analyze_pair(*case([0.2], [0.2 - 2e-12]))
    row = report["residuals"]["normal"]
    assert row["projection_resolved"] is True
    assert row["alpha"] > 1e10
    assert row["beta"] > 1e10
    assert "physical_admission" not in report


@pytest.mark.parametrize(("index", "bad"), [
    (0, []), (0, [[1, 2]]), (0, [[1, 2, 3, 4]]), (0, [[1, 2, "3"]]),
    (0, [[1, 2, True]]), (0, [[1, 2, np.bool_(True)]]), (0, [[1, 2, 1j]]),
    (0, [[1, 2, math.nan]]), (0, [[1, 2, math.inf]]), (0, [[1, 2, 10**400]]),
    (0, [[0, 0, 0], [0, 1, 0]]), (0, [[1, 2, 3]] * 16385),
    (1, [[1, 2, 3]]), (2, [[0, 0, 0], [1, 0, 0]]),
    (2, [[1, 0, 0], [False, 1, 0]]), (2, "normal"),
    (3, [0, 1]), (3, [-1, 2]), (3, [1]), (3, [[1], [1]]),
    (3, [True, 1]), (3, [math.nan, 1]), (3, "11"),
    (4, 0), (4, -1), (4, True), (4, "1"), (4, 1j), (4, math.inf),
    (4, np.array(1.0)),
])
def test_malformed_inputs_rejected(index, bad):
    args = list(case())
    args[index] = bad
    with pytest.raises((ValueError, ArithmeticError)):
        audit.analyze_pair(*args)


@pytest.mark.parametrize("args", [
    ([[1e308, 1e308, 1e308]], [[1, 0, 0]], [[1, 0, 0]], [1], 1),
    ([[1e200, 1, 0]], [[1, 0, 0]], [[1, 0, 0]], [1], 1),
    ([[1, 0, 0]], [[1, 0, 0]], [[1.7e308, 1.7e308, 1.7e308]], [1], 1),
    (*case()[:3], [1e308, 1e308], 1),
    ([[1e-320, 0, 0]], [[2e-320, 0, 0]], [[1, 0, 0]], [1], 1),
])
def test_nonfinite_arithmetic_cannot_produce_success(args):
    with pytest.raises((ValueError, ArithmeticError)):
        audit.analyze_pair(*args)


def test_large_but_finite_normal_is_normalized_with_scaled_hypot():
    report = audit.analyze_pair([[1, 0, 0]], [[1, 0, 0]],
                               [[1e308, 1e308, 1e308]], [1], 1)
    assert report["metrics"]["control"]["normal_rms"] == pytest.approx(1 / math.sqrt(3))


def test_numpy_inputs_are_copied_but_numpy_is_not_an_implementation_dependency():
    args = [np.array(value) if index < 4 else np.float64(value)
            for index, value in enumerate(case())]
    before = [value.copy() for value in args[:4]]
    report = audit.analyze_pair(*args)
    assert audit.compare(report, audit.analyze_pair(*case())) is True
    for old, value in zip(before, args[:4], strict=True):
        assert old.tobytes() == value.tobytes()
    syntax = ast.parse(Path(audit.__file__).read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    assert set(imports) == {"math", "numbers"}


def test_compare_exact_structure_and_scalar_tolerance():
    expected = audit.analyze_pair(*case())
    actual = copy.deepcopy(expected)
    assert audit.compare(actual, expected) is True
    actual["metrics"]["control"]["normal_rms"] += 1e-13
    assert audit.compare(actual, expected) is True
    actual["metrics"]["control"]["normal_rms"] += 1e-8
    with pytest.raises(ValueError, match="independent scalar mismatch"):
        audit.compare(actual, expected)


@pytest.mark.parametrize(("where", "key", "replacement"), [
    (("metrics", "control"), "normal_rms", True),
    (("metrics", "control"), "JN", math.nan),
    (("metrics", "control"), "JN", 10**400),
    (("metrics", "control"), "JN", "0.05"),
    (("metrics", "control"), "JN", None),
    (("residuals", "normal"), "projection_resolved", 1),
    (("residuals", "normal"), "alpha", None),
    (("residuals", "objective"), "fit_limit_ratio", 0.0),
    (("split",), "cross_term", False),
])
def test_compare_rejects_scalar_aliases_and_null_tampering(where, key, replacement):
    expected = audit.analyze_pair(*case())
    actual = copy.deepcopy(expected)
    row = actual
    for segment in where:
        row = row[segment]
    row[key] = replacement
    with pytest.raises(ValueError):
        audit.compare(actual, expected)


@pytest.mark.parametrize("level", [(), ("metrics",), ("metrics", "control"),
                                      ("residuals",), ("residuals", "normal"), ("split",)])
@pytest.mark.parametrize("extra", [True, False])
def test_compare_rejects_extra_or_missing_keys_at_every_level(level, extra):
    expected = audit.analyze_pair(*case())
    actual = copy.deepcopy(expected)
    row = actual
    for segment in level:
        row = row[segment]
    if extra:
        row["unexpected"] = 0.0
    else:
        row.pop(next(iter(row)))
    with pytest.raises(ValueError, match="exact schema"):
        audit.compare(actual, expected)


def test_compare_does_not_make_unresolved_response_resolved_by_tolerance():
    expected = audit.analyze_pair(*case([0], [1e-12]))
    actual = audit.analyze_pair(*case([0], [math.nextafter(1e-12, math.inf)]))
    with pytest.raises(ValueError):
        audit.compare(actual, expected)


def test_tolerance_is_or_not_sum():
    expected = audit.analyze_pair(*case())
    # At 0.002 the relative and absolute allowances are both 1e-12.
    expected["metrics"]["deltas"]["JN"] = 0.002
    actual = copy.deepcopy(expected)
    actual["metrics"]["deltas"]["JN"] += 1.5e-12
    with pytest.raises(ValueError, match="independent scalar mismatch"):
        audit.compare(actual, expected)


def test_failed_identity_raises_instead_of_clipping():
    with pytest.raises(ArithmeticError, match="registered arithmetic identity failed"):
        audit._identity(1e-3, 1.0, "control")


def test_single_point_perfect_fit_rounding_limitation_fails_closed():
    from fusion_baselines.field_residuals import analyze_pair

    arguments = (
        [[-0.5800752403121104, 0.8667301319453795, -0.6555770510030897]],
        [[-0.5837537032934108, 0.8710425770175112, -0.6590608476101262]],
        [[1.2711308092178142, -1.602604689323625, -0.40372284577657025]],
        [0.2732628111463021],
        0.5029549355840589,
    )
    # Dividing a last-bit nearzero fit by1e-4 can cross the fixed absolute
    # comparison limit. Record this conservative limitation, do not relax it.
    with pytest.raises(ValueError, match="fit_limit_ratio: independent scalar mismatch"):
        audit.compare(analyze_pair(*arguments), audit.analyze_pair(*arguments))
