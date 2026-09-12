import numpy as np
import pytest

from fusion_baselines.clebsch_field import compare_fields, sample_coordinates


def torus(lam=False):
    theta = np.linspace(0, 2 * np.pi, 33)
    radius, minor = 3 + 0.4 * np.cos(theta), 0.4
    # At phi=0, right-handed Cartesian coordinates give this negative Jacobian.
    g = -radius * 0.4**2 / 2
    et = np.stack((-minor * np.sin(theta), np.zeros(33), minor * np.cos(theta)), axis=-1)
    ep = np.stack((np.zeros(33), radius, np.zeros(33)), axis=-1)
    lt, lp = (0.1 * np.cos(theta), np.full(33, 0.07)) if lam else (np.zeros(33), np.zeros(33))
    psi, iota = -1.0, 0.7
    bt, bp = psi * (iota - lp) / g, psi * (1 + lt) / g
    mod_b = np.sqrt((bt * minor)**2 + (bp * radius)**2)
    return dict(psi=psi, g=g, bt=bt, bp=bp, lt=lt, lp=lp, iota=iota, et=et, ep=ep, mod_b=mod_b)


@pytest.mark.parametrize("lam", [False, True])
def test_analytic_torus_and_negative_controls(lam):
    native, clebsch, errors, checks = compare_fields(**torus(lam))
    assert all(checks.values())
    np.testing.assert_allclose(native, clebsch, rtol=1e-14, atol=1e-14)
    assert errors["wrong_sign"] == pytest.approx(2)
    assert errors["missing_2pi"] == pytest.approx(2 * np.pi - 1)


@pytest.mark.parametrize("factor", [-1, 2 * np.pi])
def test_wrong_flux_cannot_pass(factor):
    data = torus()
    data["psi"] *= factor
    assert not all(compare_fields(**data)[3].values())


@pytest.mark.parametrize("key", ["g", "psi"])
def test_singular_rejected(key):
    data = torus()
    data[key] = np.zeros_like(data[key])
    with pytest.raises(ValueError):
        compare_fields(**data)


def test_nonfinite_field_rejected():
    data = torus()
    data["bt"][0] = np.nan
    with pytest.raises(ValueError):
        compare_fields(**data)


@pytest.mark.parametrize("s,n", [(0.1, 16), (0.5, 64)])
def test_unregistered_grid_rejected_before_reading(tmp_path, s, n):
    with pytest.raises(ValueError):
        sample_coordinates(tmp_path / "absent.nc", s, n)
