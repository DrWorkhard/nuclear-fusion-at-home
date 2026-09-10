import numpy as np
import pytest

from fusion_baselines.flux_metrics import quadratic_flux


def test_constant_normal_field_area_and_scaling():
    field = np.tile([2.0, 0.0, 0.0], (5, 7, 1))
    normal = np.tile([3.0, 0.0, 0.0], (5, 7, 1))
    assert quadratic_flux(field, normal) == pytest.approx(6)
    assert quadratic_flux(2 * field, normal) == pytest.approx(24)
    assert quadratic_flux(field, 2 * normal) == pytest.approx(12)
    assert quadratic_flux(np.roll(field, 1, axis=-1), normal) == 0


def test_nonuniform_area_and_no_small_value_clipping():
    field = np.array([[1e-6, 0, 0], [0, 1e-6, 0]])
    normal = np.array([[1, 0, 0], [0, 3, 0]])
    assert quadratic_flux(field, normal) == pytest.approx(1e-12, rel=1e-14, abs=0)


def test_invalid_flux_arrays():
    for field, normal in [
        ([[1, 2, 3]], [[0, 0, 0]]),
        ([[np.nan, 0, 0]], [[1, 0, 0]]),
        ([1, 2, 3], [1, 2, 3]),
        ([[1, 2, 3]], [[1, 2]]),
    ]:
        with pytest.raises(ValueError):
            quadratic_flux(field, normal)
