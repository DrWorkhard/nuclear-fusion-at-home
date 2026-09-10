import numpy as np
import pytest

from fusion_baselines.action_quadrature import quadrature_action


def test_exact_constant_and_linear_well():
    assert quadrature_action([0, 1, 3], [1, 1, 1], 0.25, 2.75, 2) == pytest.approx(
        2.5 / np.sqrt(2), abs=1e-14)
    # Symmetric triangular radicand, including both turning points.
    assert quadrature_action([0, 1, 2], [2, 1, 2], 0, 2, 2) == pytest.approx(
        4 / (3 * np.sqrt(2)), rel=1e-7)


def test_quadrature_rejects_forbidden_and_nonfinite_inputs():
    with pytest.raises(ValueError, match="forbidden"):
        quadrature_action([0, 1, 2], [1, 3, 1], 0, 2, 2)
    for left, right, bstar in [(-1, 2, 2), (0, 3, 2), (0, 2, np.nan), (1, 1, 2)]:
        with pytest.raises(ValueError):
            quadrature_action([0, 1, 2], [1, 1, 1], left, right, bstar)
