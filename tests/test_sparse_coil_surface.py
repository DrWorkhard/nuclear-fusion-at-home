"""Bounded synthetic primitive tests; the full-size resource study is separate."""

import numpy as np
import pytest

pytest.importorskip("simsopt")
from simsopt.field import Current, coils_via_symmetries
from simsopt.geo import CurveSurfaceDistance, CurveXYZFourier, SurfaceRZFourier

from fusion_baselines.sparse_coil_surface import SparseCurveSurfaceDistance


def circle(radius=0.28, center=0.3, count=48, phi=0):
    curve = CurveXYZFourier(count, 3)
    curve.set("xc(0)", center * np.cos(phi))
    curve.set("yc(0)", center * np.sin(phi))
    curve.set("xc(1)", radius * np.cos(phi))
    curve.set("yc(1)", radius * np.sin(phi))
    curve.set("zs(1)", -radius)
    return curve


def torus(nphi=24, ntheta=20):
    surface = SurfaceRZFourier(nfp=2, stellsym=True, mpol=1, ntor=0,
                              quadpoints_phi=np.arange(nphi) / nphi,
                              quadpoints_theta=np.arange(ntheta) / ntheta)
    surface.set_rc(0, 0, .3)
    surface.set_rc(1, 0, .25)
    surface.set_zs(1, 0, .25)
    surface.fix_all()
    return surface


def sparse(curves, surface, threshold=.08):
    return SparseCurveSurfaceDistance(curves, surface.gamma().reshape(-1, 3),
                                      surface.normal().reshape(-1, 3), threshold)


def named_gradient(term, bases):
    d = term.dJ(partials=True)
    return np.concatenate([d(curve) for curve in bases])


@pytest.mark.parametrize("count", [24, 48])
def test_active_integral_value_and_full_vjp_match_native(count):
    base, surface = circle(count=count, phi=.17), torus()
    native = CurveSurfaceDistance([base], surface, .08)
    own = sparse([base], surface)
    assert own.J() > 0 and own.stats()["active_pairs"] > 0
    np.testing.assert_allclose(own.J(), native.J(), rtol=5e-10, atol=1e-12)
    np.testing.assert_allclose(named_gradient(own, [base]), named_gradient(native, [base]),
                               rtol=5e-10, atol=1e-12)
    np.testing.assert_allclose(own.shortest_distance(), native.shortest_distance(), atol=1e-14)


def test_all_physical_copies_accumulate_on_named_base_dofs():
    bases = [circle(phi=.15), circle(phi=.48)]
    currents = [Current(1) for _ in bases]
    for current in currents:
        current.fix_all()
    curves = [coil.curve for coil in coils_via_symmetries(bases, currents, 2, True)]
    surface = torus()
    native, own = CurveSurfaceDistance(curves, surface, .08), sparse(curves, surface)
    assert own.stats()["physical_curves"] == 8
    np.testing.assert_allclose(own.J(), native.J(), rtol=5e-10, atol=1e-12)
    np.testing.assert_allclose(named_gradient(own, bases), named_gradient(native, bases),
                               rtol=5e-10, atol=1e-12)


def test_each_curve_uses_its_own_quadrature_count():
    bases, surface = [circle(count=24, phi=.12), circle(count=48, phi=.3)], torus()
    own, native = sparse(bases, surface), CurveSurfaceDistance(bases, surface, .08)
    assert own.stats()["curve_points"] == [24, 48]
    np.testing.assert_allclose(own.J(), native.J(), rtol=5e-10, atol=1e-12)
    np.testing.assert_allclose(named_gradient(own, bases), named_gradient(native, bases),
                               rtol=5e-10, atol=1e-12)


def test_exact_cache_repeat_and_changed_base_invalidation_with_symmetry():
    base, surface = circle(phi=.22), torus()
    curves = [c.curve for c in coils_via_symmetries([base], [Current(1)], 2, True)]
    own = sparse(curves, surface)
    first, gradient = own.J(), named_gradient(own, [base]).copy()
    cached = own._geometry_cache
    assert own.J() == first and own._geometry_cache is cached
    assert np.array_equal(named_gradient(own, [base]), gradient)
    base.set("xc(0)", base.get("xc(0)") + .002)
    assert own._geometry_cache is None
    assert own.J() != first
    native = CurveSurfaceDistance(curves, surface, .08)
    np.testing.assert_allclose(own.J(), native.J(), rtol=5e-10, atol=1e-12)
    np.testing.assert_allclose(named_gradient(own, [base]), named_gradient(native, [base]),
                               rtol=5e-10, atol=1e-12)


def test_full_named_directional_derivatives_both_fixed_steps():
    base, surface = circle(phi=.19), torus(32, 32)
    own = sparse([base], surface)
    x = base.local_full_x.copy()
    gradient = named_gradient(own, [base])
    for func in (np.sin, np.cos):
        direction = func(np.arange(1, len(x) + 1))
        direction /= np.linalg.norm(direction)
        analytic = float(gradient @ direction)
        for step in (1e-5, 5e-6):
            base.local_full_x = x + step * direction
            plus = own.J()
            base.local_full_x = x - step * direction
            minus = own.J()
            fd = (plus - minus) / (2 * step)
            assert abs(fd - analytic) <= max(1e-8, 2e-4 * max(abs(fd), abs(analytic)))
    base.local_full_x = x


def test_zero_hinge_has_zero_full_gradient_and_unclipped_actual_minimum():
    base, surface = circle(radius=.42, center=.6), torus()
    own, native = sparse([base], surface), CurveSurfaceDistance([base], surface, .08)
    # Far translation removes every active pair; curve speed remains nonzero.
    base.set("xc(0)", 4.0)
    assert own.J() == 0 and own.stats()["active_pairs"] == 0
    assert np.array_equal(named_gradient(own, [base]), np.zeros_like(base.local_full_x))
    assert own.shortest_distance() > .08
    np.testing.assert_allclose(own.shortest_distance(), native.shortest_distance(), atol=1e-14)


def test_surface_copies_are_fixed_and_unscaled_area_is_preserved():
    base, surface = circle(phi=.12), torus()
    p, n = surface.gamma().reshape(-1, 3).copy(), surface.normal().reshape(-1, 3).copy()
    own = SparseCurveSurfaceDistance([base], p, n)
    value = own.J()
    doubled = SparseCurveSurfaceDistance([base], p, 2 * n)
    assert doubled.J() == pytest.approx(2 * value, rel=1e-14)
    p[:] = 100
    n[:] = 0
    base.set("xc(0)", base.get("xc(0)"))
    assert own.J() == value
    for frozen in (own.points, own.normals, own.area):
        assert not frozen.flags.writeable


@pytest.mark.parametrize("mutation", ["complex", "nan", "zero_normal", "bad_shape", "cutoff"])
def test_invalid_surface_or_cutoff_fails_closed(mutation):
    base, surface = circle(), torus()
    p = surface.gamma().reshape(-1, 3).copy()
    n, cutoff = surface.normal().reshape(-1, 3).copy(), .08
    if mutation == "complex":
        p = p.astype(complex) + 1j
    elif mutation == "nan":
        p[0, 0] = np.nan
    elif mutation == "zero_normal":
        n[0] = 0
    elif mutation == "bad_shape":
        p = p[:-1]
    else:
        cutoff = 0
    with pytest.raises(ValueError):
        SparseCurveSurfaceDistance([base], p, n, cutoff)


def test_zero_speed_or_exact_surface_intersection_is_not_regularized_away():
    base, surface = circle(), torus()
    points = surface.gamma().reshape(-1, 3).copy()
    normals = surface.normal().reshape(-1, 3)
    points[0] = base.gamma()[0]
    with pytest.raises(ValueError, match="coincident"):
        SparseCurveSurfaceDistance([base], points, normals).J()
    base.local_full_x = np.zeros_like(base.local_full_x)
    with pytest.raises(ValueError, match="speed"):
        sparse([base], surface).J()


def test_near_cutoff_broadphase_padding_does_not_change_hinge():
    class ToyCurve:
        def gamma(self):
            return np.tile([0., 0., 0.], (4, 1))

        def gammadash(self):
            return np.tile([0., 1., 0.], (4, 1))

    # Isolate pure pair arithmetic from native dependency graph wiring.
    own = sparse([circle()], torus())
    own.curves = [ToyCurve()]
    points = np.array([[.08 - 1e-14, 0, 0], [.08, 0, 0], [.08 + 1e-14, 0, 0], [1., 0, 0]])
    from scipy.spatial import cKDTree

    own.points = points
    own.area = np.ones(4)
    own._tree = cKDTree(points)
    result = own._compute()
    expected = max(.08 - points[0, 0], 0)**2 / 4
    assert result["stats"]["maximum_neighbors"] == 3
    assert result["stats"]["active_pairs"] == 4
    assert result["value"] == expected
