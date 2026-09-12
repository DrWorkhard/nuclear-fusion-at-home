import numpy as np
import pytest

from fusion_baselines.product_interpolation import decompose


@pytest.mark.parametrize("weight", [0.0, 0.2, 0.5, 0.9, 1.0])
def test_random_product_identity(weight):
    rng = np.random.default_rng(31)
    g, b, h = [rng.normal(size=(2, 11)) for _ in range(3)]
    nodes, average, correction, result = decompose(g, b, h, weight, -0.005)
    direct = ((1 - weight) * g[0] + weight * g[1]) * (
        (1 - weight) * b[0] + weight * b[1]
    ) + 0.005 * ((1 - weight) * h[0] + weight * h[1])
    np.testing.assert_allclose(result, direct, atol=1e-15, rtol=1e-14)
    np.testing.assert_array_equal(result, average + correction)
    np.testing.assert_array_equal(nodes, g * b + 0.005 * h)


def test_constant_factor_has_no_product_error():
    g = np.ones((2, 3))
    b = np.arange(6).reshape(2, 3)
    _, _, correction, _ = decompose(g, b, g, 0.5, 1)
    assert np.array_equal(correction, np.zeros(3))


@pytest.mark.parametrize("weight", [-1, 2, np.nan])
def test_invalid_weights_rejected(weight):
    with pytest.raises(ValueError):
        decompose(np.ones((2, 3)), np.ones((2, 3)), np.ones((2, 3)), weight, 1)


def test_missing_endpoint_and_nonfinite_rejected():
    with pytest.raises(ValueError):
        decompose(np.ones((1, 3)), np.ones((2, 3)), np.ones((2, 3)), 0.5, 1)
    with pytest.raises(ValueError):
        decompose(np.full((2, 3), np.nan), np.ones((2, 3)), np.ones((2, 3)), 0.5, 1)
