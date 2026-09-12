import numpy as np
import pytest

from fusion_baselines.spectral_projection import explicit_projection, mode_mask, project


def test_exact_stored_mode_projection_and_parseval():
    size = 32
    angles = 2 * np.pi * np.arange(size) / size
    phi, theta = angles[:, None], angles[None, :]
    kept = 2 + 3 * np.cos(2 * theta - 3 * phi) + 0.4 * np.sin(2 * theta - 3 * phi)
    omitted = 0.8 * np.cos(theta + 5 * phi)
    mask = mode_mask(size, [0, 2], [0, 6], 2)
    actual, coefficients, stats = project(kept + omitted, mask)
    np.testing.assert_allclose(actual, kept, atol=2e-14, rtol=1e-14)
    np.testing.assert_allclose(explicit_projection(coefficients, mask), kept, atol=2e-14)
    assert stats["inside"] == pytest.approx(4 + (9 + 0.16) / 2)
    assert stats["outside"] == pytest.approx(0.64 / 2)
    assert stats["parseval_error"] < 1e-14


def test_batch_and_idempotence():
    values = np.random.default_rng(4).normal(size=(2, 16, 16))
    mask = mode_mask(16, [0, 1], [0, -2], 2)
    projected, coeffs, _ = project(values, mask)
    np.testing.assert_allclose(project(projected, mask)[0], projected, atol=1e-15)
    np.testing.assert_allclose(explicit_projection(coeffs, mask), projected, atol=1e-15)


@pytest.mark.parametrize("m,n,nfp", [([16], [0], 1), ([1.2], [0], 1), ([1], [1], 2), ([], [], 1)])
def test_unsupported_modes_rejected(m, n, nfp):
    with pytest.raises(ValueError):
        mode_mask(32, m, n, nfp)


def test_asymmetric_mask_and_nonfinite_field_rejected():
    mask = mode_mask(16, [1], [2], 2)
    mask[1, 15] = False
    with pytest.raises(ValueError):
        project(np.ones((16, 16)), mask)
    with pytest.raises(ValueError):
        project(np.full((16, 16), np.nan), np.ones((16, 16), dtype=bool))
