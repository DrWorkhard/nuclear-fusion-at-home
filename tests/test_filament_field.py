import numpy as np
import pytest

from fusion_baselines.filament_field import filament_field


def circle(radius=2.0, n=128):
    angle = np.arange(n) * 2 * np.pi / n
    position = radius * np.column_stack((np.cos(angle), np.sin(angle), np.zeros(n)))
    tangent = 2 * np.pi * radius * np.column_stack((-np.sin(angle), np.cos(angle), np.zeros(n)))
    return position[None], tangent[None]


def test_circle_axis_field_matches_closed_form_including_sign():
    pos, vel = circle()
    z = np.array([-3.0, -1.0, 0.0, 1.0, 3.0])
    points = np.column_stack((np.zeros_like(z), np.zeros_like(z), z))
    field = filament_field(points, pos, vel, [7.0])
    expected = 4 * np.pi * 1e-7 * 7 * 2**2 / (2 * (2**2 + z * z) ** 1.5)
    np.testing.assert_allclose(field[:, 2], expected, rtol=1e-14, atol=0)
    np.testing.assert_allclose(field[:, :2], 0, rtol=0, atol=1e-21)


def test_current_linearity_and_orientation():
    pos, vel = circle()
    points = [[0.1, 0.2, 1.0]]
    answer = filament_field(points, pos, vel, [1.0])
    np.testing.assert_allclose(filament_field(points, pos, vel, [-2.0]), -2 * answer)
    np.testing.assert_allclose(
        filament_field(points, pos[:, ::-1], -vel[:, ::-1], [1]), -answer, rtol=1e-14, atol=1e-22
    )


def test_superposition_and_rigid_translation():
    pos, vel = circle()
    points, shift = np.array([[0.1, 0.2, 1.0]]), np.array([2.0, 3.0, 4.0])
    answer = filament_field(points, pos, vel, [2.0])
    np.testing.assert_allclose(filament_field(points + shift, pos + shift, vel, [2.0]), answer)
    np.testing.assert_allclose(
        filament_field(points, np.tile(pos, (2, 1, 1)), np.tile(vel, (2, 1, 1)), [1.0, 1.0]), answer
    )


def test_singular_source_point_rejected():
    pos, vel = circle()
    with pytest.raises(ValueError, match="singular"):
        filament_field(pos[0, :1], pos, vel, [1.0])


@pytest.mark.parametrize("kind", ["shape", "empty", "nan", "currents"])
def test_invalid_quadrature_rejected(kind):
    pos, vel = circle()
    points, currents = [[0, 0, 0]], [1.0]
    if kind == "shape":
        vel = vel[..., :2]
    elif kind == "empty":
        points = []
    elif kind == "nan":
        vel[0, 0, 0] = np.nan
    else:
        currents = [1.0, 2.0]
    with pytest.raises(ValueError):
        filament_field(points, pos, vel, currents)
