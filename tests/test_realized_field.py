import netCDF4
import numpy as np
import pytest

from fusion_baselines.realized_field import Target, summarize, winding


def torus(iota=-0.55, radius=1.0, minor=0.1, ns=11):
    """Circular torus with nested circles: R = R0 + r(s) cos theta, Z = r(s) sin theta."""
    rows = np.sqrt(np.linspace(0, 1, ns)) * minor
    rmnc = np.column_stack((np.full(ns, radius), rows))
    return Target([0, 1], [0, 0], rmnc, np.column_stack((np.zeros(ns), rows)), np.full(ns, iota))


def helix(target, s, turns=5.0, n=20001):
    phi = np.linspace(0, 2 * np.pi * turns, n)
    theta = target.iota(s) * phi
    r, z = target.rz(s, theta, phi)
    return np.column_stack((r * np.cos(phi), r * np.sin(phi), z))


@pytest.mark.parametrize("iota", [-0.59, -0.25, 0.3, 1.7])
def test_winding_recovers_transform_and_transits_including_sign(iota):
    target = torus(iota)
    transits, measured = winding(helix(target, 0.5), target)
    assert transits == pytest.approx(5.0, rel=1e-12)
    assert measured == pytest.approx(iota, rel=1e-10)


def test_reversed_line_direction_keeps_transform():
    target = torus(-0.59)
    _, forward = winding(helix(target, 0.7), target)
    _, backward = winding(helix(target, 0.7)[::-1], target)
    assert backward == pytest.approx(forward, rel=1e-12)


def test_target_surfaces_axis_and_wout_round_trip(tmp_path):
    target = torus()
    r, z = target.rz(1.0, np.array([0.0, np.pi / 2]), np.zeros(2))
    np.testing.assert_allclose(r, [1.1, 1.0], atol=1e-15)
    np.testing.assert_allclose(z, [0.0, 0.1], atol=1e-15)
    np.testing.assert_allclose(target.axis(np.array([0.3])), [[1.0], [0.0]], atol=1e-15)
    path = tmp_path / "wout_test.nc"
    with netCDF4.Dataset(path, "w") as data:
        data.createDimension("radius", target.ns)
        data.createDimension("mn_mode", 2)
        data.createVariable("lasym__logical__", "i4")[...] = 0
        for name, dims in (("xm", ("mn_mode",)), ("xn", ("mn_mode",)), ("iotaf", ("radius",)),
                           ("rmnc", ("radius", "mn_mode")), ("zmns", ("radius", "mn_mode"))):
            data.createVariable(name, "f8", dims)[...] = getattr(target, name)
    loaded = Target.from_wout(path)
    assert len(loaded.sha256) == 64
    np.testing.assert_array_equal(loaded.rmnc, target.rmnc)
    assert loaded.iota(0.5) == target.iota(0.5)


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        Target([0], [0], [[1.0]], [[0.0], [0.0]], [0.5, 0.5])
    with pytest.raises(ValueError):
        torus().rz(1.5, 0.0, 0.0)
    with pytest.raises(ValueError):
        winding(np.zeros((1, 3)), torus())


def test_summary_requires_every_line_confined_and_matching():
    good = [dict(left_target=False, iota_traced=-0.59, iota_target=-0.587)] * 3
    assert summarize(good)["nested_and_matching"] is True
    escaped = good[:2] + [dict(left_target=True, iota_traced=-0.59, iota_target=-0.587)]
    assert summarize(escaped)["lines_confined"] == 2
    assert summarize(escaped)["nested_and_matching"] is False
    shifted = [dict(left_target=False, iota_traced=-0.62, iota_target=-0.587)]
    assert summarize(shifted)["nested_and_matching"] is False
    assert summarize(good)["physical_admission"] is False
