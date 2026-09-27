import json
import math

import numpy as np
import pytest

from fusion_baselines.boundary_control_metrics import boundary_metrics

FIELD = np.array([[3., 4., 0.], [0., 0., -2.], [1., 2., 2.]])
NORMALS = np.array([[2., 0., 0.], [0., 0., -1.], [0., 3., 0.]])


def scalar_reference(field, normals):
    norm = lambda v: math.sqrt(math.fsum(x*x for x in v))  # noqa: E731
    area, magnitude = list(map(norm, normals)), list(map(norm, field))
    bn = [math.fsum(x*y for x, y in zip(b, n, strict=True))/a
          for b, n, a in zip(field, normals, area, strict=True)]
    ratio = [abs(b)/m for b, m in zip(bn, magnitude, strict=True)]
    mean = lambda v: math.fsum(v)/len(v)  # noqa: E731
    weighted = lambda v: math.fsum(a*x for a, x in zip(area, v, strict=True))/math.fsum(area)  # noqa: E731
    return dict(
        raw_quadratic_flux=0.5*mean([a*b*b for a, b in zip(area, bn, strict=True)]),
        parameter_abs_bn_over_mean_b=mean(list(map(abs, bn)))/mean(magnitude),
        area_mean_abs_ratio=weighted(ratio), normal_rms=math.sqrt(weighted([x*x for x in ratio])),
        normal_max=max(ratio), mean_area_jacobian=mean(area), area_mean_b=weighted(magnitude),
        parameter_mean_b=mean(magnitude), min_b=min(magnitude),
        area_bn_rms=math.sqrt(weighted([x*x for x in bn])),
        normalized_global_flux=0.5*weighted([x*x for x in bn])/weighted([x*x for x in magnitude]),
        local_flux=0.5*mean([a*r*r for a, r in zip(area, ratio, strict=True)]),
    )


def test_scalar_crosscheck_and_json_scalars():
    result = boundary_metrics(FIELD, NORMALS)
    assert result == pytest.approx(scalar_reference(FIELD.tolist(), NORMALS.tolist()))
    assert result["parameter_abs_bn_over_mean_b"] == pytest.approx(0.7)
    assert result["area_mean_abs_ratio"] == pytest.approx(0.7)
    assert result["normal_rms"] > result["area_mean_abs_ratio"]
    assert result["normalized_global_flux"] != pytest.approx(0.5*result["normal_rms"]**2)
    assert all(type(v) is float for v in result.values())
    json.dumps(result, allow_nan=False)


def test_distinct_parameter_and_area_statistics():
    result = boundary_metrics([[1, 0, 0], [0, 0, 2]], [[1, 0, 0], [0, 4, 0]])
    assert result["parameter_abs_bn_over_mean_b"] == pytest.approx(1/3)
    assert result["area_mean_abs_ratio"] == pytest.approx(1/5)
    assert result["normal_rms"] == pytest.approx(math.sqrt(1/5))


def test_constant_field_and_zero_normal_error_are_valid():
    result = boundary_metrics([[3, 4, 0]]*2, [[2, 0, 0], [-5, 0, 0]])
    assert result["normal_rms"] == pytest.approx(0.6)
    assert result["raw_quadratic_flux"] == pytest.approx(15.75)
    assert result["normalized_global_flux"] == pytest.approx(0.18)
    assert result["local_flux"] == pytest.approx(0.63)
    assert boundary_metrics([[0, 1, 0]], [[-2, 0, 0]])["normal_rms"] == 0


@pytest.mark.parametrize("scale", [0.125, -3.0])
def test_current_scaling(scale):
    original, scaled = boundary_metrics(FIELD, NORMALS), boundary_metrics(scale*FIELD, NORMALS)
    linear = {"area_mean_b", "parameter_mean_b", "min_b", "area_bn_rms"}
    for key, value in original.items():
        factor = scale**2 if key == "raw_quadratic_flux" else abs(scale) if key in linear else 1
        assert scaled[key] == pytest.approx(factor*value)


def test_normal_scaling_orientation_shape_and_no_mutation():
    field, normals = FIELD.copy(), NORMALS.copy()
    original = boundary_metrics(field, normals)
    assert boundary_metrics(field.reshape(1, 3, 3), normals.reshape(1, 3, 3)) == original
    scaled = boundary_metrics(field, -7*normals)
    for key, value in original.items():
        factor = 7 if key in {"raw_quadratic_flux", "local_flux", "mean_area_jacobian"} else 1
        assert scaled[key] == pytest.approx(factor*value)
    np.testing.assert_array_equal(field, FIELD)
    np.testing.assert_array_equal(normals, NORMALS)


@pytest.mark.parametrize("bad", [
    [], [1, 2, 3], [[1, 2]], [[0, 0, 0]], [[math.nan, 0, 1]], [[math.inf, 0, 1]],
    [[True, 0, 1]], [["1", "0", "1"]], [[1j, 0, 1]], [[None, 0, 1]],
    np.ones((1, 3), dtype=bool), np.array([[1, 0, 1]], dtype=object),
    np.ma.array([[1, 0, 1]], mask=[[True, False, False]]), [[1e308, 0, 1]],
])
@pytest.mark.parametrize("slot", [0, 1])
def test_invalid_inputs_rejected(bad, slot):
    arguments = [[[1, 1, 0]], [[1, 0, 0]]]
    arguments[slot] = bad
    with pytest.raises(ValueError):
        boundary_metrics(*arguments)


def test_mismatched_shapes_rejected():
    with pytest.raises(ValueError, match="matched"):
        boundary_metrics(FIELD, NORMALS[:1])


def test_finite_inputs_with_unrepresentable_flux_rejected():
    with pytest.raises(ValueError, match="derived"):
        boundary_metrics([[1e150, 0, 0]], [[1e100, 0, 0]])
