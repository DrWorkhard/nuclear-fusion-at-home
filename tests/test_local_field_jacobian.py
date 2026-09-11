import numpy as np
import pytest

from fusion_baselines.local_field_jacobian import local_field_jacobian


class Field:
    def __init__(self, fail=False):
        self.points = np.array([[9., 8., 7.], [6., 5., 4.]])
        self.cache_ready = False
        self.calls = []
        self.x = np.array([2., 3.])
        self.fail = fail

    def get_points_cart_ref(self):
        return self.points

    def set_points(self, points):
        self.points = points.copy()
        self.cache_ready = False

    def B(self):
        self.cache_ready = True
        self.calls.append("B")
        return self.x[0]*self.points + self.x[1]*np.ones_like(self.points)

    def B_vjp(self, weights):
        assert self.cache_ready and self.points.shape == (1, 3)
        self.calls.append("vjp")
        if self.fail:
            raise RuntimeError("forced failure")
        row = np.array([np.sum(weights*self.points), np.sum(weights)])
        return lambda objective: row


def test_analytic_rows_cache_order_and_restoration():
    f = Field()
    original = f.points.copy()
    points = np.array([[1., 2., 3.], [3., 1., 2.]])
    weights = np.array([[2., 3., 4.], [4., 2., 1.]])
    jac = local_field_jacobian(f, f, points, weights)
    np.testing.assert_array_equal(jac, np.column_stack((np.sum(points*weights, axis=1),
                                                       weights.sum(axis=1))))
    np.testing.assert_array_equal(f.points, original)
    assert f.calls == ["B", "vjp", "B", "vjp"]


def test_forced_failure_restores_original_points():
    f = Field(fail=True)
    original = f.points.copy()
    with pytest.raises(RuntimeError, match="forced failure"):
        local_field_jacobian(f, f, np.ones((2, 3)), np.ones((2, 3)))
    np.testing.assert_array_equal(f.points, original)


def test_invalid_input_rejected_without_state_change():
    f = Field()
    original = f.points.copy()
    for points, weights in [(np.ones(3), np.ones(3)), (np.empty((0, 3)), np.empty((0, 3))),
                            (np.full((1, 3), np.nan), np.ones((1, 3)))]:
        with pytest.raises(ValueError):
            local_field_jacobian(f, f, points, weights)
    np.testing.assert_array_equal(f.points, original)
    assert not f.calls
