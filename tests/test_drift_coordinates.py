import numpy as np
import pytest

from fusion_baselines.drift_coordinates import phase_drift


@pytest.mark.parametrize("slope", [-10.0, -1.0, 0.0, 1.0, 10.0])
def test_both_covectors_transform_and_contraction_is_invariant(slope):
    a, k = [2.0, 3.0], [5.0, 7.0]
    row = phase_drift(a, k, slope=slope)
    np.testing.assert_array_equal(row["drift"], [3.0, -2.0 - 3.0 * slope])
    np.testing.assert_array_equal(row["phase_gradient"], [5.0 + 7.0 * slope, 7.0])
    assert row["contraction"] == 1.0


def test_omnigenous_drift_is_unaffected():
    a = phase_drift([-2.0, 0.0], [0.0, 1.0], slope=100.0)
    np.testing.assert_array_equal(a["drift"], [0.0, 2.0])
    assert a["contraction"] == 2.0


def test_angular_component_can_flip_without_phase_drift_changing():
    old = phase_drift([0.1, 0.2], [0.0, 1.0])
    new = phase_drift([0.1, 0.2], [0.0, 1.0], slope=-1)
    assert old["drift"][1] < 0 < new["drift"][1]
    assert old["contraction"] == new["contraction"]
    assert np.dot([0.0, 1.0], new["drift"]) != old["contraction"]


@pytest.mark.parametrize(
    "a,k,c",
    [([1], [1, 2], 0), ([1, 2], [1], 0), ([np.nan, 0], [1, 2], 0), ([1, 2], [1, 2], np.inf)],
)
def test_invalid_coordinate_inputs_rejected(a, k, c):
    with pytest.raises(ValueError):
        phase_drift(a, k, slope=c)
