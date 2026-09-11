from types import SimpleNamespace

import numpy as np

from fusion_baselines.spatial_backend import ResidualRepresentation
from fusion_baselines.spatial_flux import normal_weights, spatial_flux


class Field:
    def __init__(self, objective):
        self.objective = objective
        self.points = np.array([[1., 0., 0.], [2., 0., 0.], [3., 0., 0.]])

    def set_points(self, points):
        self.points = points.copy()

    def get_points_cart_ref(self):
        return self.points

    def B(self):
        x = self.objective.x
        return np.column_stack((x[0]*self.points[:, 0], np.full(len(self.points), x[1]),
                                np.zeros(len(self.points))))

    def B_vjp(self, weights):
        result = np.array([np.sum(weights[:, 0]*self.points[:, 0]), weights[:, 1].sum()])
        return lambda objective: result


class Backend:
    def __init__(self):
        flux = SimpleNamespace(x=np.array([1., 2.]), target=np.zeros(3), threshold=1e-8,
                               definition="quadratic flux")
        flux.field = Field(flux)
        points = flux.field.points.copy()
        normal = np.tile([1., 1., 0.], (3, 1))
        flux.surface = SimpleNamespace(normal=lambda: normal, gamma=lambda: points)
        self.global_objective, self.objectives, self.scales = flux, [flux], np.array([2.])

    def __call__(self, x):
        f = self.global_objective
        f.x = x.copy()
        f.field.set_points(f.surface.gamma())
        z = spatial_flux(f.field.B(), f.surface.normal())
        weights = normal_weights(f.surface.normal())
        dz = np.column_stack((weights[:, 0]*f.field.points[:, 0], weights[:, 1]))
        phi, dphi = z@z/2, z@dz
        if phi < f.threshold:
            phi, dphi = 0.0, np.zeros(2)
        return np.array([2*phi, x[1]]), np.vstack((2*dphi, [0., 1.]))


def test_representation_identity_and_explicit_work():
    base = Backend()
    x = np.array([1.2, 0.7])
    original, original_jac = base(x)
    spatial = ResidualRepresentation(base, spatial=True)
    lifted, jac = spatial(x)
    np.testing.assert_allclose(lifted@lifted, original@original)
    np.testing.assert_allclose(jac.T@lifted, original_jac.T@original)
    assert spatial.work["common_bundles"] == 1
    assert spatial.work["extra_single_point_VJP_calls"] == 3
    np.testing.assert_array_equal(base.global_objective.field.points,
                                  base.global_objective.surface.gamma())
    scalar = ResidualRepresentation(base)
    np.testing.assert_array_equal(scalar(x)[0], original)
    assert scalar.work["extra_single_point_VJP_calls"] == 0


def test_clipped_flux_skips_spatial_derivatives_and_preserves_other_components():
    spatial = ResidualRepresentation(Backend(), spatial=True)
    values, jac = spatial(np.zeros(2))
    assert not values.any()
    np.testing.assert_array_equal(jac[-1], [0., 1.])
    assert spatial.work["common_bundles"] == 1
    assert spatial.work["extra_single_point_B_calls"] == 0
