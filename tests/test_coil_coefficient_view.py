import copy

import numpy as np
import pytest
from test_serialized_dofs import fixture

from fusion_baselines.coil_coefficient_view import base_arrays, serialized_physical_coefficients
from fusion_baselines.serialized_dofs import named_serialized_values


def full_fixture():
    doc = fixture()
    for i in range(4):
        doc["simsopt_objs"][f"dof{i}"] = dict(
            names=[f"v{k}" for k in range(51)], x={"data": list(np.arange(51)+100*i)},
            free={"data": [True]*50+[False]})
    names = [f"curve{i}:v{k}" for i in range(4) for k in range(50)]
    return doc, names


def test_named_order_fixed_coefficients_and_zero_fixed_directions():
    doc, names = full_fixture()
    values = named_serialized_values(doc, names)
    a = base_arrays(doc, names, values)
    b = base_arrays(doc, names[::-1], values[::-1])
    assert np.array_equal(a, b) and a[3, -1, -1] == 350
    d = base_arrays(doc, names, np.ones(200), direction=True)
    assert np.all(d[:, -1, -1] == 0) and np.all(d.reshape(4, -1)[:, :50] == 1)


def test_scalar_serialized_rotation_then_reflection_and_nested_graph():
    doc, _ = full_fixture()
    obj = doc["simsopt_objs"]
    obj["R"] = dict(**{"@class": "RotatedCurve"}, curve={"value": "curve0"},
                     phi=np.pi/2, flip=True)
    obj["RR"] = dict(**{"@class": "RotatedCurve"}, curve={"value": "R"}, phi=0., flip=True)
    obj["extra"] = dict(curve={"value": "RR"})
    obj["B"]["coils"][4] = {"value": "extra"}
    c = np.zeros((4, 3, 17))
    c[0, :, 0] = [1, 2, 3]
    actual = serialized_physical_coefficients(doc, c)
    np.testing.assert_allclose(actual[4, :, 0], [-2, 1, 3], atol=1e-15)
    assert np.array_equal(actual[0], c[0])
    obj["R"]["curve"] = {"value": "RR"}
    with pytest.raises(ValueError, match="cyclic"):
        serialized_physical_coefficients(doc, c)


def test_nonfinite_vector_and_missing_free_label_rejected():
    doc, names = full_fixture()
    with pytest.raises(ValueError, match="finite named"):
        base_arrays(doc, names, np.full(200, np.nan))
    with pytest.raises(KeyError):
        base_arrays(doc, names[:-1], np.zeros(199))
    bad = copy.deepcopy(doc)
    bad["simsopt_objs"]["dof0"]["names"][1] = "v0"
    with pytest.raises(ValueError, match="malformed"):
        base_arrays(bad, names, np.zeros(200))
