import copy

import numpy as np
import pytest

from fusion_baselines.serialized_dofs import (
    base_coil_owners,
    dof_permutation,
    named_serialized_values,
)


def test_decimal_object_name_boundary_and_roundtrip():
    source = ["Curve8:x", "Curve8:y", "Curve9:x", "Curve9:y"]
    target = ["Curve10:x", "Curve10:y", "Curve9:x", "Curve9:y"]
    mapping = {"Curve8": "Curve9", "Curve9": "Curve10"}
    permutation = dof_permutation(source, target, mapping)
    np.testing.assert_array_equal(permutation, [2, 3, 0, 1])
    values = np.array([1., 2., 3., 4.])
    np.testing.assert_array_equal(values[permutation][np.argsort(permutation)], values)
    for bad in ([*target[:-1], target[0]], [*target[:-1], "Curve11:y"], target[:-1]):
        with pytest.raises(ValueError):
            dof_permutation(source, bad, mapping)
    with pytest.raises(ValueError):
        dof_permutation(source, target, {"Curve8": "Curve9", "Curve9": "Curve9"})


def fixture():
    objects = {"B": {"@class": "BiotSavart", "coils": [
        {"value": "coil" + str(i % 4)} for i in range(16)]}}
    for i in range(4):
        objects.update({
            f"coil{i}": {"curve": {"value": f"curve{i}"}, "current": {"value": f"scale{i}"}},
            f"curve{i}": {"@class": "CurveXYZFourier", "dofs": {"value": f"dof{i}"}},
            f"scale{i}": {"@class": "ScaledCurrent", "current_to_scale": {"value": f"I{i}"}},
            f"I{i}": {"@class": "Current"},
            f"dof{i}": {"names": ["x", "y"], "x": {"data": [i, i+1]},
                         "free": {"data": [True, False]}}})
    return {"simsopt_objs": objects, "graph": {"value": "B"}}


def test_archived_values_and_physical_owner_order():
    doc = fixture()
    np.testing.assert_array_equal(named_serialized_values(doc, ["curve3:x", "curve0:x"]), [3, 0])
    assert base_coil_owners(doc) == [(f"curve{i}", [(("current_to_scale",), f"I{i}")])
                                    for i in range(4)]
    with pytest.raises(ValueError, match="fixed"):
        named_serialized_values(doc, ["curve0:y"])
    with pytest.raises(ValueError, match="duplicate"):
        named_serialized_values(doc, ["curve0:x", "curve0:x"])
    bad = copy.deepcopy(doc)
    bad["simsopt_objs"]["dof0"]["x"]["data"][0] = np.nan
    with pytest.raises(ValueError, match="invalid"):
        named_serialized_values(bad, ["curve0:x"])
    bad = copy.deepcopy(doc)
    bad["simsopt_objs"]["scale0"]["current_to_scale"]["value"] = "scale0"
    with pytest.raises(ValueError, match="cyclic"):
        base_coil_owners(bad)


def test_current_sum_keeps_repeated_shared_leaves_and_constant():
    doc = fixture()
    objects = doc["simsopt_objs"]
    objects["sum"] = {"@class": "CurrentSum", "current_a": {"value": "I3"},
                      "current_b": {"value": "scale0"}}
    objects["coil3"]["current"] = {"value": "sum"}
    assert base_coil_owners(doc)[-1] == ("curve3", [
        (("current_a",), "I3"), (("current_b", "current_to_scale"), "I0")])
    objects["sum"]["current_b"]["value"] = "sum"
    with pytest.raises(ValueError, match="cyclic"):
        base_coil_owners(doc)
