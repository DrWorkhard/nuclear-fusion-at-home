import numpy as np
import pytest

from fusion_baselines.clearance_chain_rule import chain_rule_rows, loop_positions
from fusion_baselines.complex_clearance import clearance_rows, fourier_positions


def test_exact_constant_separation_and_direction():
    c = np.zeros((2, 3, 3))
    c[1, 0, 0] = 2
    d = np.zeros((1, 2, 3, 3))
    d[0, 1, 0, 0] = 1
    values, derivative, anchors = chain_rule_rows(c, d, 3, resolution=8)
    assert anchors[0] == 36
    assert values[0] == pytest.approx((36-np.log(64)/512)/1.1**2 - 1)
    assert derivative[0, 0] == pytest.approx(36/1.1**2)


def test_independent_loop_and_chain_against_complex_fourier_values():
    rng = np.random.default_rng(45)
    c = rng.normal(size=(4, 3, 7)) * 0.02
    c[:, 0, 0] += np.arange(4)
    directions = rng.normal(size=(2, 4, 3, 7)) * 0.01
    v, dv, anchor = chain_rule_rows(c, directions, 1.3, resolution=32)
    cv, _ = clearance_rows(c, 1.3, resolution=32)
    np.testing.assert_allclose(v, cv, rtol=0, atol=1e-12)
    np.testing.assert_allclose(loop_positions(c, 32), fourier_positions(c, 32), atol=1e-14)
    for k, direction in enumerate(directions):
        perturbed, _ = clearance_rows(c+1j*1e-20*direction, 1.3, resolution=32, anchors=anchor)
        np.testing.assert_allclose(dv[k], perturbed.imag/1e-20, rtol=1e-10, atol=1e-12)


def test_translation_direction_is_zero():
    c = np.zeros((3, 3, 5))
    c[:, 0, 0] = [0, 1, 2]
    d = np.zeros((1, 3, 3, 5))
    d[0, :, :, 0] = [1, 2, 3]
    assert np.all(chain_rule_rows(c, d, 1)[1] == 0)


@pytest.mark.parametrize("bad", [np.nan, np.inf, 0, -1])
def test_invalid_scale_rejected(bad):
    with pytest.raises(ValueError):
        chain_rule_rows(np.zeros((2, 3, 3)), np.zeros((1, 2, 3, 3)), bad)
