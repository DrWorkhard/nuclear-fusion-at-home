import numpy as np
import pytest

from fusion_baselines.current_field_probes import central_probes


def test_seven_explicit_current_only_probes_leave_source_unchanged():
    x, columns = np.arange(207) / 1000, np.array([205, 1, 37])
    original, calls = x.copy(), []
    slopes = np.arange(36).reshape(3, 4, 3) / 10

    def field(proposal):
        calls.append(proposal.copy())
        return np.ones((4, 3)) + np.tensordot(proposal[columns], slopes, 1)

    result = central_probes(x, columns, field)
    assert result["affine_pass"] and result["field_requests"] == len(calls) == 7
    assert np.array_equal(x, original) and np.array_equal(calls[0], original)
    for i, column in enumerate(columns):
        for j, sign in enumerate((1, -1)):
            expected = x.copy()
            expected[column] += sign * 0.001
            assert np.array_equal(calls[1 + 2 * i + j], expected)
    np.testing.assert_allclose(result["slopes"], slopes, atol=2e-13)


def test_nonlinear_even_current_response_is_not_affine():
    x, columns = np.zeros(207), np.array([0, 1, 2])
    result = central_probes(x, columns, lambda p: np.ones((4, 3)) + sum(p[:3] ** 2))
    assert not result["affine_pass"]


def test_invalid_columns_and_nonfinite_native_return_rejected():
    with pytest.raises(ValueError):
        central_probes(np.zeros(207), [0, 0, 1], lambda p: np.ones((2, 3)))
    with pytest.raises(ValueError):
        central_probes(np.zeros(207), [0.0, 1.0, 2.0], lambda p: np.ones((2, 3)))
    with pytest.raises(ValueError):
        central_probes(np.zeros(207), [0, 1, 2], lambda p: np.full((2, 3), np.nan))
