from types import SimpleNamespace

import numpy as np
import pytest

from fusion_baselines.counted_field_views import CountedBatchField, CountedLocalField
from fusion_baselines.local_field_jacobian import local_field_jacobian


class Field:
    def __init__(self, fail=False):
        self.points = np.array([[10.0, 20.0, 30.0]])
        self.fail, self.calls = fail, 0

    def get_points_cart_ref(self):
        return self.points

    def set_points(self, points):
        self.points = np.asarray(points).copy()

    def B(self):
        return self.points.copy()

    def B_vjp(self, _weights):
        self.calls += 1
        if self.fail and self.calls == 2:
            raise RuntimeError("deliberate point VJP failure")
        value = self.points[0, :2].copy()
        return lambda _objective: value


def test_local_counting_preserves_results_and_restores_points():
    field, counts = Field(), {}
    original = field.points.copy()
    view = CountedLocalField(field, counts)
    points = np.arange(9.0).reshape(3, 3)
    jac = local_field_jacobian(view, SimpleNamespace(x=np.zeros(2)), points, np.ones_like(points))
    np.testing.assert_array_equal(jac, points[:, :2])
    np.testing.assert_array_equal(jac, view.rows)
    np.testing.assert_array_equal(field.points, original)
    assert counts == dict(
        local_B_requests=3, local_B_completed=3, local_VJP_requests=3, local_VJP_completed=3
    )


def test_partial_local_failure_keeps_completed_rows_and_attempts():
    field, counts = Field(fail=True), {}
    original = field.points.copy()
    view = CountedLocalField(field, counts)
    points = np.arange(9.0).reshape(3, 3)
    with pytest.raises(RuntimeError, match="deliberate"):
        local_field_jacobian(view, SimpleNamespace(x=np.zeros(2)), points, np.ones_like(points))
    np.testing.assert_array_equal(field.points, original)
    np.testing.assert_array_equal(view.rows, points[:1, :2])
    assert counts == dict(
        local_B_requests=2, local_B_completed=2, local_VJP_requests=2, local_VJP_completed=1
    )


def test_batch_views_only_count_requested_native_operations():
    curve = SimpleNamespace(
        name="curve",
        gamma=lambda: np.ones((2, 3)),
        gammadash=lambda: np.ones((2, 3)),
        dgamma_by_dcoeff=lambda: np.ones((2, 3, 1)),
        dgammadash_by_dcoeff=lambda: np.ones((2, 3, 1)),
    )
    current = SimpleNamespace(get_value=lambda: 2.0, vjp=lambda _w: lambda _o: np.array([3.0]))
    native = SimpleNamespace(coils=[SimpleNamespace(curve=curve, current=current)], psc_array=None)
    counts = {}
    view = CountedBatchField(native, counts)
    assert view.psc_array is None and view.coils[0].curve.name == "curve"
    for name in ("gamma", "gammadash", "dgamma_by_dcoeff", "dgammadash_by_dcoeff"):
        np.testing.assert_array_equal(getattr(view.coils[0].curve, name)(), getattr(curve, name)())
    assert view.coils[0].current.get_value() == 2.0
    np.testing.assert_array_equal(view.coils[0].current.vjp([1])(object()), [3.0])
    assert all(value == 1 for value in counts.values())
    assert len(counts) == 13
