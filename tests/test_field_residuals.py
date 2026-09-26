"""Synthetic fields only; no saved project arrays, native calls or file reads."""

import copy
import json
import math

import numpy as np
import pytest

from fusion_baselines import field_residuals as residuals


def fields(control=(0.4, 0.2), proposal=(0.2, 0.1), *, weights=None):
    def magnetic(values):
        values = np.asarray(values, dtype=float)
        return np.column_stack((values, np.sqrt(1 - values**2), np.zeros(len(values))))

    count = len(control)
    return [magnetic(control), magnetic(proposal), np.tile([1.0, 0, 0], (count, 1)),
            np.ones(count) if weights is None else np.asarray(weights, dtype=float), 1.0]


FIT_KEYS = {
    "control_norm", "proposal_norm", "delta_norm", "secant_norm", "projection_resolved",
    "alignment", "aligned_fraction", "alpha", "beta", "fit_norm", "fit_fraction",
    "fit_limit_ratio", "orthogonality", "pythagoras_error",
}
PROJECTED = FIT_KEYS - {
    "control_norm", "proposal_norm", "delta_norm", "secant_norm", "projection_resolved",
}


def test_exact_finite_json_schema():
    result = residuals.analyze_pair(*fields())
    assert set(result) == {"metrics", "residuals", "split"}
    assert set(result["metrics"]) == {"control", "proposal", "deltas"}
    for row in result["metrics"].values():
        assert set(row) == {"normal_rms", "JN", "boundary_B_rms"}
        assert all(type(value) is float for value in row.values())
    assert set(result["residuals"]) == {"normal", "objective"}
    for row in result["residuals"].values():
        assert set(row) == FIT_KEYS
        assert type(row["projection_resolved"]) is bool
        assert all(value is None or type(value) is float
                   for key, value in row.items() if key != "projection_resolved")
    assert set(result["split"]) == {
        "numerator_norm_squared", "denominator_norm_squared", "cross_term",
        "control_numerator_term", "control_denominator_term", "delta_squared_norm",
        "energy_identity_error", "vector_identity_error",
    }
    assert json.loads(json.dumps(result, allow_nan=False)) == result


def test_aligned_known_fit_and_both_origins():
    result = residuals.analyze_pair(*fields())
    row = result["residuals"]["normal"]
    assert row["projection_resolved"] is True
    assert row["alpha"] == pytest.approx(2)
    assert row["beta"] == pytest.approx(1)
    assert row["alignment"] == pytest.approx(1)
    assert row["aligned_fraction"] == pytest.approx(1)
    assert row["fit_norm"] < 1e-15
    assert row["fit_fraction"] < 1e-14
    assert row["fit_limit_ratio"] < 1e-10
    assert result["residuals"]["objective"]["fit_limit_ratio"] is None
    assert row["delta_norm"] == pytest.approx(-math.sqrt(0.1) / 2)
    assert result["metrics"]["deltas"]["JN"] == pytest.approx(-0.0375)


def test_signed_fields_not_absolute_fields():
    result = residuals.analyze_pair(*fields((0.4, -0.4), (-0.4, 0.4)))
    row = result["residuals"]["normal"]
    assert row["alpha"] == pytest.approx(0.5)
    assert row["beta"] == pytest.approx(-0.5)
    assert row["secant_norm"] == pytest.approx(0.8)
    assert row["delta_norm"] == pytest.approx(0)
    assert row["fit_norm"] < 1e-15


def test_orthogonal_response_cannot_remove_control_residual():
    result = residuals.analyze_pair(*fields((0.4, 0), (0.4, 0.3)))
    row = result["residuals"]["normal"]
    assert row["alpha"] == pytest.approx(0)
    assert row["beta"] == pytest.approx(-1)
    assert row["alignment"] == pytest.approx(0, abs=1e-14)
    assert row["fit_fraction"] == pytest.approx(1)
    assert row["fit_limit_ratio"] == pytest.approx(math.sqrt(0.08) / 1e-4)


def test_uniform_positive_scaling_cancels_only_normalized_residual():
    args = fields()
    args[1] = 2 * args[0]
    result = residuals.analyze_pair(*args)
    normal, objective = result["residuals"].values()
    assert normal["projection_resolved"] is False
    assert normal["secant_norm"] < 1e-15
    assert objective["alpha"] == pytest.approx(-1)
    assert objective["beta"] == pytest.approx(-2)
    assert result["metrics"]["deltas"]["normal_rms"] == pytest.approx(0)
    assert result["metrics"]["deltas"]["JN"] == pytest.approx(0.15)
    assert result["metrics"]["deltas"]["boundary_B_rms"] == pytest.approx(1)
    split = result["split"]
    assert split["numerator_norm_squared"] == pytest.approx(0.1)
    assert split["denominator_norm_squared"] == pytest.approx(0.1)
    assert split["cross_term"] == pytest.approx(-0.2)
    assert split["control_numerator_term"] == pytest.approx(0.2)
    assert split["control_denominator_term"] == pytest.approx(-0.2)


def test_nonuniform_weights_and_nonunit_normals():
    args = fields((0.2, 0.8), (0.4, 0.6), weights=[1, 3])
    args[2] *= np.array([[7], [2]])
    result = residuals.analyze_pair(*args)
    assert result["metrics"]["control"]["normal_rms"] == pytest.approx(0.7)
    assert result["metrics"]["proposal"]["normal_rms"] == pytest.approx(math.sqrt(0.31))
    assert result["residuals"]["normal"]["alpha"] == pytest.approx(2.75)
    args[3] *= 100
    assert residuals.analyze_pair(*args) == result


def test_b2_affects_objective_only():
    args = fields()
    first = residuals.analyze_pair(*args)
    args[-1] = 4
    second = residuals.analyze_pair(*args)
    assert second["residuals"]["normal"] == first["residuals"]["normal"]
    assert second["split"] == first["split"]
    for side in ("control", "proposal"):
        assert second["metrics"][side]["JN"] == first["metrics"][side]["JN"] / 4


@pytest.mark.parametrize("difference,resolved", [(0, False), (5e-13, False),
                                                   (1e-12, False), (2e-12, True)])
def test_fixed_nearzero_boundary_and_zero_control(difference, resolved):
    result = residuals.analyze_pair(*fields((0,), (difference,)))
    for row in result["residuals"].values():
        assert row["projection_resolved"] is resolved
        if not resolved:
            assert all(row[key] is None for key in PROJECTED)
        else:
            assert row["alpha"] == 0
            assert row["beta"] == -1
            assert row["fit_norm"] == 0
            assert row["alignment"] is row["aligned_fraction"] is row["fit_fraction"] is None


@pytest.mark.parametrize("direction,resolved", [(0.0, False), (math.inf, True)])
def test_nextafter_nearzero_boundary_is_not_tolerance_classified(direction, resolved):
    step = np.nextafter(1e-12, direction)
    result = residuals.analyze_pair(*fields((0,), (step,)))
    for row in result["residuals"].values():
        assert row["projection_resolved"] is resolved


def test_nearzero_rule_scales_with_large_objective_norm():
    args = fields((0.5,), (0.5 + 2e-13,))
    args[-1] = 1e-8
    result = residuals.analyze_pair(*args)
    assert result["residuals"]["objective"]["secant_norm"] > 1e-12
    assert result["residuals"]["objective"]["projection_resolved"] is False


def test_explicit_fit_remains_positive_for_near_aligned_small_remainder():
    result = residuals.analyze_pair(*fields((0.4, 1e-10), (0.2, 1e-10)))
    row = result["residuals"]["normal"]
    assert row["fit_norm"] == pytest.approx(1e-10 / math.sqrt(2), rel=1e-8, abs=0)
    assert row["fit_norm"] > 0


def test_general_split_energy_and_alpha_identity():
    args = fields((0.2, -0.3, 0.5), (0.4, 0.1, -0.2), weights=[2, 3, 7])
    args[1] *= np.array([[2], [0.5], [3]])
    result = residuals.analyze_pair(*args)
    split = result["split"]
    reconstructed = sum(split[key] for key in (
        "numerator_norm_squared", "denominator_norm_squared", "cross_term",
        "control_numerator_term", "control_denominator_term"))
    assert reconstructed == pytest.approx(split["delta_squared_norm"], abs=1e-14)
    assert split["energy_identity_error"] < 1e-14
    assert split["vector_identity_error"] < 1e-14
    for row in result["residuals"].values():
        assert row["control_norm"] ** 2 == pytest.approx(
            row["fit_norm"] ** 2 + row["alpha"] ** 2 * row["secant_norm"] ** 2)
        assert abs(row["orthogonality"]) < 1e-14


def test_reversing_pair_changes_alpha_origin_and_sign_of_scalar_deltas():
    args = fields((0.2, -0.3, 0.5), (0.4, 0.1, -0.2), weights=[2, 3, 7])
    forward = residuals.analyze_pair(*args)
    args[0], args[1] = args[1], args[0]
    reverse = residuals.analyze_pair(*args)
    for key in ("normal", "objective"):
        left, right = forward["residuals"][key], reverse["residuals"][key]
        assert right["alpha"] == pytest.approx(1 - left["alpha"])
        assert right["fit_norm"] == pytest.approx(left["fit_norm"])
        assert right["delta_norm"] == -left["delta_norm"]
    for key, value in forward["metrics"]["deltas"].items():
        assert reverse["metrics"]["deltas"][key] == -value


def test_rigid_orthogonal_change_of_cartesian_basis_keeps_scalar_analysis():
    args = fields((0.2, -0.3, 0.5), (0.4, 0.1, -0.2), weights=[2, 3, 7])
    original = residuals.analyze_pair(*args)
    matrix = np.array([[0., 0., 1.], [-1., 0., 0.], [0., 1., 0.]])
    for index in range(3):
        args[index] = args[index] @ matrix
    assert residuals.analyze_pair(*args) == original


def test_no_input_mutation_or_result_aliases():
    args = fields()
    before = copy.deepcopy(args)
    for value in args[:-1]:
        value.flags.writeable = False
    result = residuals.analyze_pair(*args)
    for actual, expected in zip(args[:-1], before[:-1], strict=True):
        assert actual.tobytes() == expected.tobytes()
    args[0] = before[0] * 7
    assert result == residuals.analyze_pair(*before)


@pytest.mark.parametrize("count,valid", [(0, False), (1, True), (16384, True), (16385, False)])
def test_point_limit(count, valid):
    args = [np.tile([0.2, 1., 0], (count, 1)), np.tile([0.1, 1., 0], (count, 1)),
            np.tile([1., 0, 0], (count, 1)), np.ones(count), 1.0]
    if valid:
        residuals.analyze_pair(*args)
    else:
        with pytest.raises(ValueError):
            residuals.analyze_pair(*args)


@pytest.mark.parametrize("index", range(5))
@pytest.mark.parametrize("bad", [True, "1", complex(1, 0), None, float("nan"), float("inf")])
def test_bad_types_and_nonfinite_in_every_input(index, bad):
    args = fields()
    if index < 3:
        args[index] = args[index].tolist()
        args[index][0][0] = bad
    elif index == 3:
        args[index] = [bad, 1.0]
    else:
        args[index] = bad
    with pytest.raises(ValueError):
        residuals.analyze_pair(*args)


@pytest.mark.parametrize("index,bad", [(0, [1, 2, 3]), (1, [[1, 2, 3]]),
                                      (2, np.ones((2, 2))), (3, np.ones((2, 1))),
                                      (4, [1]), (4, 0), (4, -1),
                                      (0, np.zeros((2, 3))), (1, np.zeros((2, 3))),
                                      (2, np.zeros((2, 3))), (3, [0, 1]), (3, [-1, 1])])
def test_shapes_positive_weights_scale_and_nonzero_vectors(index, bad):
    args = fields()
    args[index] = bad
    with pytest.raises(ValueError):
        residuals.analyze_pair(*args)


@pytest.mark.parametrize("index", range(4))
def test_overflow_rejected(index):
    args = fields()
    args[index] = np.full_like(args[index], 1e308)
    with pytest.raises(ValueError):
        residuals.analyze_pair(*args)


def test_array_boolean_and_object_dtypes_rejected():
    for dtype in (bool, object, str, complex):
        args = fields()
        args[0] = args[0].astype(dtype)
        with pytest.raises(ValueError):
            residuals.analyze_pair(*args)


def test_plain_nested_numeric_lists_and_numpy_scalar_scale():
    args = fields()
    actual = residuals.analyze_pair(*[x.tolist() for x in args[:-1]], np.float64(1))
    assert actual == residuals.analyze_pair(*args)


def test_identity_guard_rejects_failed_or_nonfinite_identities():
    for error, scale in [(0.01, 1), (float("inf"), 1), (0, float("inf")), (0, -1)]:
        with pytest.raises(ValueError):
            residuals._identity(error, scale, "synthetic")


def test_public_analysis_rejects_corrupted_pythagorean_identity(monkeypatch):
    original, calls = residuals._dot, 0

    def corrupt(*args):
        nonlocal calls
        calls += 1
        return original(*args) + (0.01 if calls == 1 else 0)

    monkeypatch.setattr(residuals, "_dot", corrupt)
    with pytest.raises(ValueError, match="Pythagoras identity failed"):
        residuals.analyze_pair(*fields())


def test_all_projection_and_energy_identity_guards_are_used(monkeypatch):
    original, labels = residuals._identity, []

    def record(error, scale, label):
        labels.append(label)
        return original(error, scale, label)

    monkeypatch.setattr(residuals, "_identity", record)
    residuals.analyze_pair(*fields())
    assert labels == ["orthogonality", "Pythagoras", "orthogonality", "Pythagoras",
                      "squared-error decomposition"]


def test_no_clipping_of_projection_coefficient():
    result = residuals.analyze_pair(*fields((0.4,), (0.400001,)))
    row = result["residuals"]["normal"]
    assert row["alpha"] < -100000
    assert row["beta"] == row["alpha"] - 1
