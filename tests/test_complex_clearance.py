import numpy as np
import pytest

from fusion_baselines.complex_clearance import clearance_rows, fourier_positions


def circles():
    c = np.zeros((2, 3, 3))
    c[:, 0, 2], c[:, 1, 1] = [1, 1.4], [1, 1.4]
    c[1, 2, 0] = 0.5
    return c


def test_independent_fourier_circle_translation_rotation_and_scaling():
    c = circles()
    points = fourier_positions(c, 16)
    np.testing.assert_allclose(np.linalg.norm(points[0], axis=1), 1)
    np.testing.assert_allclose(points[:, 0], [[1, 0, 0], [1.4, 0, 0.5]])
    moved = c.copy()
    moved[:, :, 0] += [2, 3, 4]
    np.testing.assert_allclose(fourier_positions(moved, 16), points + [2, 3, 4])
    rotation = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
    transformed = (c.transpose(0, 2, 1) @ rotation).transpose(0, 2, 1)
    np.testing.assert_allclose(fourier_positions(transformed, 16), points @ rotation)
    np.testing.assert_allclose(fourier_positions(2 * c, 16), 2 * points)


def test_constant_distance_offset_and_complex_direction():
    c = np.zeros((2, 3, 3))
    c[1, 0, 0] = 2
    values, anchors = clearance_rows(c, 1.0, resolution=8)
    assert values[0] == pytest.approx((4 - np.log(64) / 512) / 1.1**2 - 1)
    perturbed = c.astype(complex)
    perturbed[1, 0, 0] += 1j * 1e-24
    z, _ = clearance_rows(perturbed, 1.0, resolution=8, anchors=anchors)
    assert z.imag[0] / 1e-24 == pytest.approx(4 / 1.1**2, rel=1e-14)
    c = circles()
    direction = np.random.default_rng(81).normal(size=c.shape)
    _, anchors = clearance_rows(c, 2.0, resolution=20)
    z, _ = clearance_rows(c + 1j * 1e-24 * direction, 2.0, resolution=20, anchors=anchors)
    errors = []
    for step in (1e-5, 1e-6, 1e-7):
        plus = clearance_rows(c + step * direction, 2.0, resolution=20, anchors=anchors)[0]
        minus = clearance_rows(c - step * direction, 2.0, resolution=20, anchors=anchors)[0]
        central = (plus - minus) / (2 * step)
        errors.append(float(np.abs(central - z.imag / 1e-24).max()))
    # Large beta gives appreciable central-difference truncation even at 1e-6.
    # Verify its second-order reduction, not a relaxed discrepancy tolerance.
    assert errors[0] > 50 * errors[1] > 2500 * errors[2]
    np.testing.assert_allclose(z.imag / 1e-24, central, rtol=1e-7, atol=1e-8)


@pytest.mark.parametrize(
    "coefficients", [np.zeros((3, 3)), np.zeros((2, 3, 4)), np.full((2, 3, 3), np.nan)]
)
def test_bad_coefficients(coefficients):
    with pytest.raises(ValueError):
        fourier_positions(coefficients, 20)
