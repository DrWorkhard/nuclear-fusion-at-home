import numpy as np
import pytest

from fusion_baselines.field_conditioning import conditioning, spectrum


def example():
    matrix = np.zeros((10, 7))
    columns = np.array([4, 0, 6])
    matrix[:3, columns] = np.eye(3)
    matrix[[0, 3], 1] = 1
    matrix[[1, 4], 2] = [2, 1]
    matrix[[2, 5], 3] = [3, 1]
    matrix[[3, 4, 5], 5] = [1, -1, 1]
    z = np.zeros(10)
    z[3:6] = [1, -2, 3]
    steps = np.zeros((3, 7))
    steps[0, 1], steps[1, 2] = 1, 1
    return z, matrix, columns, steps


def test_known_current_subspace_fractions_spectra_and_zero_tangent():
    result = conditioning(*example())
    assert result["current_projection_qualified"] and result["status"] == "completed"
    assert result["work"] == dict(svd_calls=4, qr_calls=1, step_projections=3)
    assert result["spectra"]["full"]["rank"] == 6
    assert result["spectra"]["geometry"]["rank"] == 4
    assert result["spectra"]["projected_geometry"]["rank"] == 3
    assert result["spectra"]["current"]["rank"] == 3
    first, second, zero = result["projections"]
    assert first["current_tangent_energy_fraction"] == pytest.approx(0.5)
    assert second["current_tangent_energy_fraction"] == pytest.approx(0.8)
    assert zero["current_tangent_energy_fraction"] is None
    expected = example()[0].copy()
    expected[3] += 1
    np.testing.assert_allclose(first["projected_residual"], expected, atol=1e-14, rtol=0)
    assert first["projected_linear_raw_flux"] == pytest.approx(8.5)


def test_explicit_column_permutation_preserves_physical_projection():
    z, matrix, columns, steps = example()
    original = conditioning(z, matrix, columns, steps)
    permutation = np.array([6, 1, 4, 3, 2, 5, 0])
    inverse = np.argsort(permutation)
    changed = conditioning(z, matrix[:, permutation], inverse[columns], steps[:, permutation])
    for a, b in zip(original["projections"], changed["projections"], strict=True):
        np.testing.assert_allclose(
            a["projected_residual"], b["projected_residual"], rtol=0, atol=1e-14
        )
    for name in original["spectra"]:
        np.testing.assert_allclose(
            original["spectra"][name]["singular_values"],
            changed["spectra"][name]["singular_values"],
            rtol=1e-13,
            atol=1e-12,
        )


def test_rank_loss_keeps_other_spectra_without_inventing_current_projection():
    z, matrix, columns, steps = example()
    matrix[:, columns[2]] = matrix[:, columns[1]]
    result = conditioning(z, matrix, columns, steps)
    assert not result["current_projection_qualified"]
    assert result["work"] == dict(svd_calls=3, qr_calls=0, step_projections=0)
    assert "Q" not in result and "projected_geometry" not in result["spectra"]
    assert result["projections"] == []


def test_zero_spectrum_and_invalid_inputs():
    zero = spectrum(np.zeros((5, 3)))
    assert zero["rank"] == 0 and zero["condition"] is None
    z, matrix, columns, steps = example()
    steps[0, columns[0]] = 1
    with pytest.raises(ValueError, match="geometric"):
        conditioning(z, matrix, columns, steps)
    steps[0, columns[0]] = 0
    matrix[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        conditioning(z, matrix, columns, steps)
    with pytest.raises(ValueError, match="tall"):
        spectrum(np.ones((2, 3)))


def test_overflow_in_scalar_projection_statistics_is_not_qualified():
    z, matrix, columns, steps = example()
    steps[0, 1] = 1e200
    with np.errstate(over="ignore", invalid="ignore"):
        with pytest.raises(ValueError, match="nonfinite"):
            conditioning(z, matrix, columns, steps)
