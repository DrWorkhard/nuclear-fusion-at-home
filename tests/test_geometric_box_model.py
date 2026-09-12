import numpy as np
import pytest

from fusion_baselines.box_lp_certificate import certificate
from fusion_baselines.geometric_box_model import OPTIONS, box_model, solve_model


def test_known_active_row_and_lower_bound_certificate():
    result = certificate([1, 2], [[-1, 0]], [0], [0, -1], [-1], [0, 2], [0, 0])
    assert result["all_pass"]
    assert result["primal_objective"] == result["dual_objective"] == -2
    assert all(v == 0 for v in result["residuals"].values())


@pytest.mark.parametrize("change", ["dual_sign", "point", "objective", "nan"])
def test_certificate_rejects_corrupted_witness(change):
    c, s, m = np.array([1.0, 2.0]), np.array([0.0, -1.0]), np.array([-1.0])
    if change == "dual_sign":
        m[0] *= -1
    elif change == "point":
        s[0] = -0.01
    elif change == "objective":
        c[0] = -1
    else:
        m[0] = np.nan
    if change == "nan":
        with pytest.raises(ValueError, match="finite"):
            certificate(c, [[-1, 0]], [0], s, m, [0, 2], [0, 0])
    else:
        assert not certificate(c, [[-1, 0]], [0], s, m, [0, 2], [0, 0])["all_pass"]


def test_model_scaling_keeps_every_true_inequality_and_zero_gradient():
    model = box_model([3.0, 4.0], [-1e-9, 0.1], [[1, 0], [0, 2]], 1e-6)
    np.testing.assert_array_equal(model["A"], [[-1, 0], [0, -2]])
    np.testing.assert_allclose(model["b"], [-0.001, 100000], rtol=1e-15)
    np.testing.assert_array_equal(model["c"], [0.6, 0.8])
    assert model["gradient_norm"] == 5
    zero = box_model([0, 0], [1], [[1, 1]], 1e-6)
    assert zero["status"] == "zero_gradient" and "c" not in zero
    with pytest.raises(ValueError, match="nonzero"):
        solve_model(zero)


def test_highs_control_reconstructs_analytic_solution_and_retains_infeasibility():
    pytest.importorskip("scipy.optimize")
    model = box_model([1, 2], [0], [[1, 0]], 1e-5)
    result = solve_model(model)
    assert result["success"] and result["status"] == 0 and result["options"] == OPTIONS
    np.testing.assert_allclose(result["s"], [0, -1], rtol=0, atol=1e-14)
    verified = certificate(
        model["c"],
        model["A"],
        model["b"],
        result["s"],
        result["inequality_marginals"],
        result["lower_marginals"],
        result["upper_marginals"],
    )
    assert verified["all_pass"]
    result = solve_model(box_model([1], [-2], [[1]], 1.0))
    assert not result["success"] and result["status"] == 2 and result["s"] is None


def test_invalid_geometric_model_inputs():
    for h, g, j, radius in (
        ([np.nan], [1], [[1]], 1),
        ([1], [1], [[1]], 0),
        ([1, 2], [1], [[1]], 1),
        ([1], [1], [[np.inf]], 1),
    ):
        with pytest.raises(ValueError, match="finite"):
            box_model(h, g, j, radius)
