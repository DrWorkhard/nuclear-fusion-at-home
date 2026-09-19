"""Small synthetic native/Sparse/block controls, never the resource matrix."""

import copy

import jax
import numpy as np
import pytest
from simsopt.field.coil import apply_symmetries_to_curves
from simsopt.geo import CurveSurfaceDistance, CurveXYZFourier, SurfaceRZFourier

from fusion_baselines import block_native_coil_surface as block
from fusion_baselines.sparse_coil_surface import SparseCurveSurfaceDistance


def curve(count=24, phi=0.19):
    result = CurveXYZFourier(count, 3)
    result.set("xc(0)", 0.30 * np.cos(phi))
    result.set("yc(0)", 0.30 * np.sin(phi))
    result.set("xc(1)", 0.28 * np.cos(phi))
    result.set("yc(1)", 0.28 * np.sin(phi))
    result.set("zs(1)", -0.28)
    return result


def surface():
    result = SurfaceRZFourier(
        nfp=2,
        stellsym=True,
        mpol=1,
        ntor=0,
        quadpoints_phi=np.arange(12) / 12,
        quadpoints_theta=np.arange(8) / 8,
    )
    result.set_rc(0, 0, 0.30)
    result.set_rc(1, 0, 0.25)
    result.set_zs(1, 0, 0.25)
    result.fix_all()
    return result


def make(curves=None, block_size=16, progress_callback=None):
    curves = [curve()] if curves is None else curves
    target = surface()
    return block.BlockNativeCurveSurfaceDistance(
        curves,
        target.gamma().reshape(-1, 3),
        target.normal().reshape(-1, 3),
        block_size=block_size,
        progress_callback=progress_callback,
    )


def gradient(term, bases):
    derivative = term.dJ(partials=True)
    return np.concatenate([derivative(base) for base in bases])


def expected_work(**counts):
    return {
        key: dict(attempted=counts.get(key, 0), completed=counts.get(key, 0))
        for key in block.QUANTITIES
    }


@pytest.mark.parametrize("count,block_size", [(24, 16), (32, 32), (24, 96)])
def test_active_full_integral_and_gradient_match_both_backends(count, block_size):
    base, target = curve(count), surface()
    native = CurveSurfaceDistance([base], target, 0.08)
    sparse = SparseCurveSurfaceDistance(
        [base], target.gamma().reshape(-1, 3), target.normal().reshape(-1, 3)
    )
    own = make([base], block_size)
    assert own.J() > 0
    for reference in (native, sparse):
        np.testing.assert_allclose(own.J(), reference.J(), rtol=5e-10, atol=1e-12)
        np.testing.assert_allclose(
            gradient(own, [base]), gradient(reference, [base]), rtol=5e-10, atol=1e-12
        )
        np.testing.assert_allclose(
            own.shortest_distance(), reference.shortest_distance(), rtol=5e-10, atol=1e-12
        )


def test_full_symmetry_copies_unequal_curve_grids_and_repeat_restore():
    bases = [curve(24, 0.13), curve(32, 0.37)]
    physical = apply_symmetries_to_curves(bases, 2, True)
    own, target = make(physical), surface()
    native = CurveSurfaceDistance(physical, target, 0.08)
    original = bases[0].local_full_x.copy()
    first, first_gradient = own.J(), gradient(own, bases)
    assert own.J() == first and np.array_equal(gradient(own, bases), first_gradient)
    changed = original.copy()
    changed[0] += 0.002
    bases[0].local_full_x = changed
    second, second_gradient = own.J(), gradient(own, bases)
    assert second != first
    assert own.J() == second and np.array_equal(gradient(own, bases), second_gradient)
    np.testing.assert_allclose(second, native.J(), rtol=5e-10, atol=1e-12)
    np.testing.assert_allclose(second_gradient, gradient(native, bases), rtol=5e-10, atol=1e-12)
    bases[0].local_full_x = original
    assert own.J() == first and np.array_equal(gradient(own, bases), first_gradient)
    assert own.kernel_work() == expected_work(
        J=5 * 8 * 6,
        position=5 * 8 * 6,
        tangent=5 * 8 * 6,
        position_vjp=5 * 8,
        tangent_vjp=5 * 8,
    )


def test_both_directional_derivatives_and_step_sizes_have_no_hidden_value_gradients():
    base = curve()
    own = make([base])
    original = base.local_full_x.copy()
    analytic = gradient(own, [base])
    before = own.kernel_work()
    for fun in (np.sin, np.cos):
        direction = fun(np.arange(original.size) + 1)
        direction /= np.linalg.norm(direction)
        for step in (1e-5, 5e-6):
            base.local_full_x = original + step * direction
            plus = own.J()
            base.local_full_x = original - step * direction
            minus = own.J()
            finite_difference = (plus - minus) / (2 * step)
            derivative = float(analytic @ direction)
            assert abs(finite_difference - derivative) <= max(
                1e-8, 2e-4 * max(abs(finite_difference), abs(derivative))
            )
    after = own.kernel_work()
    assert after["J"] == dict(attempted=8 * 6, completed=8 * 6)
    assert all(after[key] == before[key] for key in block.QUANTITIES if key != "J")


def test_zero_hinge_and_complete_unclipped_minimum():
    base = curve()
    base.set("xc(0)", 4.0)
    own = make([base])
    assert own.J() == 0
    assert np.array_equal(gradient(own, [base]), np.zeros_like(base.local_full_x))
    assert own.shortest_distance() > 0.08
    assert own.kernel_work() == expected_work(
        J=6,
        position=6,
        tangent=6,
        minimum=6,
        position_vjp=1,
        tangent_vjp=1,
    )


def test_partition_visits_every_point_in_order_and_correctly_weights_every_block():
    own = make()
    original_points = own.points.copy()
    seen = []

    def sentinel(position, tangent, points, normals, threshold):
        seen.append(points.copy())
        return np.array(len(seen), dtype=np.float64)

    own._kernels["J"] = sentinel
    assert own.J() == pytest.approx(np.mean(np.arange(1, 7)))
    assert len(seen) == 6
    assert np.array_equal(np.concatenate(seen), original_points)
    assert own.kernel_work() == expected_work(J=6)


def test_fixed_surface_copies_and_original_area_weight_scaling():
    base, target = curve(), surface()
    p, n = target.gamma().reshape(-1, 3).copy(), target.normal().reshape(-1, 3).copy()
    own = block.BlockNativeCurveSurfaceDistance([base], p, n, block_size=16)
    doubled = block.BlockNativeCurveSurfaceDistance([base], p, 2 * n, block_size=16)
    value, derivative = own.J(), gradient(own, [base])
    np.testing.assert_allclose(doubled.J(), 2 * value, rtol=5e-10, atol=1e-12)
    np.testing.assert_allclose(gradient(doubled, [base]), 2 * derivative, rtol=5e-10, atol=1e-12)
    p[:] = 10
    n[:] = 0
    assert own.J() == value
    assert not own.points.flags.writeable and not own.normals.flags.writeable


def test_kernel_ledger_reservations_match_every_uncached_call_and_are_isolated():
    events = []
    own = make(progress_callback=events.append)
    for _ in range(2):
        own.J()
        own.dJ()
        own.shortest_distance()
    assert [e["phase"] for e in events] == [p for p in ("J", "dJ", "minimum") * 2 for _ in range(2)]
    for index, (before, after) in enumerate(zip(events[::2], events[1::2], strict=True)):
        assert before["index"] == after["index"] == index
        assert before["status"] == "reserved" and after["status"] == "completed"
        assert before["work"] == before["work_before"]
        assert after["work"] == before["upper_work"]
        assert before["curve_index"] == 0
        assert set(before["reservation"]) == set(block.QUANTITIES)
    expected = expected_work(
        J=12, position=12, tangent=12, minimum=12, position_vjp=2, tangent_vjp=2
    )
    assert own.kernel_work() == expected
    returned = own.kernel_work()
    returned["J"]["attempted"] = 0
    events[-1]["work"]["J"]["completed"] = 0
    assert own.kernel_work() == expected


def test_kernel_failure_retains_exact_partial_counts_and_reserved_upper_bound():
    events = []
    own = make(progress_callback=events.append)
    calls = 0

    def fail_second(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ArithmeticError("synthetic kernel failure")
        return np.array(1.0, dtype=np.float64)

    own._kernels["J"] = fail_second
    with pytest.raises(ArithmeticError, match="synthetic kernel failure"):
        own.J()
    assert own.kernel_work()["J"] == dict(attempted=2, completed=1)
    assert [e["status"] for e in events] == ["reserved", "error"]
    assert events[-1]["work"]["J"] == dict(attempted=2, completed=1)
    assert events[-1]["upper_work"]["J"] == dict(attempted=6, completed=6)
    assert events[0]["work"]["J"] == dict(attempted=0, completed=0)


def test_synchronization_failure_is_not_counted_complete(monkeypatch):
    events = []
    own = make(progress_callback=events.append)
    own._kernels["J"] = lambda *args: np.array(1.0)

    def fail_sync(_):
        raise ArithmeticError("synthetic synchronization failure")

    monkeypatch.setattr(block.jax, "block_until_ready", fail_sync)
    with pytest.raises(ArithmeticError, match="synchronization"):
        own.J()
    assert own.kernel_work()["J"] == dict(attempted=1, completed=0)
    assert events[-1]["status"] == "error"


def test_bad_covector_is_rejected_before_vjp_and_counted_as_incomplete():
    events = []
    own = make(progress_callback=events.append)
    own._kernels["tangent"] = lambda position, *args: np.full_like(position, np.nan)
    with pytest.raises(ValueError, match="native output"):
        own.dJ()
    work = own.kernel_work()
    assert work["position"] == dict(attempted=1, completed=1)
    assert work["tangent"] == dict(attempted=1, completed=0)
    assert work["position_vjp"] == dict(attempted=0, completed=0)
    assert events[-1]["status"] == "error"


def test_native_vjp_exception_retains_completed_covectors(monkeypatch):
    base, events = curve(), []
    own = make([base], progress_callback=events.append)

    def fail(_):
        raise ArithmeticError("synthetic native VJP failure")

    monkeypatch.setattr(base, "dgamma_by_dcoeff_vjp", fail)
    with pytest.raises(ArithmeticError, match="VJP failure"):
        own.dJ()
    work = own.kernel_work()
    assert work["position"] == work["tangent"] == dict(attempted=6, completed=6)
    assert work["position_vjp"] == dict(attempted=1, completed=0)
    assert work["tangent_vjp"] == dict(attempted=0, completed=0)


def test_reservation_persistence_failure_prevents_native_work():
    def fail(_):
        raise OSError("synthetic ledger IO failure")

    own = make(progress_callback=fail)
    with pytest.raises(OSError, match="IO failure"):
        own.J()
    assert own.kernel_work() == expected_work()


def test_completion_persistence_failure_preserves_performed_kernel_counts():
    emitted = []

    def fail(event):
        emitted.append(copy.deepcopy(event))
        if event["status"] == "completed":
            raise OSError("synthetic completed-ledger failure")

    own = make(progress_callback=fail)
    with pytest.raises(OSError, match="completed-ledger"):
        own.J()
    assert own.kernel_work() == expected_work(J=6)
    assert [e["status"] for e in emitted] == ["reserved", "completed", "error"]


@pytest.mark.parametrize("block_size", [0, -1, True, 3.0, 5, 97])
def test_invalid_or_incomplete_partition_rejected(block_size):
    with pytest.raises(ValueError, match="partition"):
        make(block_size=block_size)


@pytest.mark.parametrize("mutation", ["complex", "nan", "normal", "shape", "threshold"])
def test_invalid_surface_data_rejected(mutation):
    target = surface()
    p, n, threshold = target.gamma().reshape(-1, 3), target.normal().reshape(-1, 3).copy(), 0.08
    if mutation == "complex":
        p = p.astype(complex)
    elif mutation == "nan":
        n[0, 0] = np.nan
    elif mutation == "normal":
        n[0] = 0
    elif mutation == "shape":
        n = n[:-1]
    else:
        threshold = 0
    with pytest.raises(ValueError):
        block.BlockNativeCurveSurfaceDistance([curve()], p, n, threshold, 16)


@pytest.mark.parametrize("method", ["J", "dJ", "shortest_distance"])
def test_zero_speed_and_exact_coincidence_fail_before_native_kernels(method):
    base, target = curve(), surface()
    points, normals = target.gamma().reshape(-1, 3).copy(), target.normal().reshape(-1, 3)
    points[-1] = base.gamma()[0]
    own = block.BlockNativeCurveSurfaceDistance([base], points, normals, block_size=16)
    with pytest.raises(ValueError, match="coincident"):
        getattr(own, method)()
    assert own.kernel_work() == expected_work()
    own = make([base])
    base.local_full_x = np.zeros_like(base.local_full_x)
    with pytest.raises(ValueError, match="speed"):
        getattr(own, method)()
    assert own.kernel_work() == expected_work()


def test_float64_must_already_be_enabled():
    with jax.enable_x64(False):
        with pytest.raises(ValueError, match="float64"):
            make()


def test_invalid_callback_is_rejected_before_native_work():
    with pytest.raises(ValueError, match="callback"):
        make(progress_callback="not callable")


def test_empty_curve_iterator_is_not_a_zero_objective():
    with pytest.raises(ValueError, match="nonempty curves"):
        make(iter(()))


def test_full_minimum_failure_keeps_partial_distance_work(monkeypatch):
    events = []
    own = make(progress_callback=events.append)
    original, calls = block.cdist, 0

    def fail_second(left, right):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ArithmeticError("synthetic blocked minimum failure")
        return original(left, right)

    monkeypatch.setattr(block, "cdist", fail_second)
    with pytest.raises(ArithmeticError, match="minimum failure"):
        own.shortest_distance()
    assert own.kernel_work()["minimum"] == dict(attempted=2, completed=1)
    assert events[-1]["status"] == "error"
    assert events[-1]["upper_work"]["minimum"] == dict(attempted=6, completed=6)
