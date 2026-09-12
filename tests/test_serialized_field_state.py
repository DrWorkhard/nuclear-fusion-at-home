import numpy as np
import pytest

from fusion_baselines.serialized_field_state import serialized_state


def document():
    objects = {}
    for i in range(4):
        objects[f"d{i}"] = {"x": {"data": [float(i)] * 51}}
        objects[f"q{i}"] = {"x": {"data": [float(i + 1)]}}
        objects[f"curve{i}"] = {"@class": "CurveXYZFourier", "dofs": {"value": f"d{i}"}}
        objects[f"current{i}"] = {"@class": "Current", "dofs": {"value": f"q{i}"}}
        objects[f"coil{i}"] = dict(
            curve={"value": f"curve{i}"},
            current={"value": f"current{i}"},
            regularization={"data": 0.1},
        )
    objects["field"] = {
        "@class": "BiotSavart",
        "coils": [{"value": f"coil{i}"} for i in range(4)] * 4,
    }
    return dict(simsopt_objs=objects, graph={"value": "field"})


def test_reads_dofs_not_stale_constructor_or_process_names():
    doc = document()
    doc["simsopt_objs"]["current0"]["current"] = 999.0
    state = serialized_state(doc)
    np.testing.assert_array_equal(state["coefficients"], [[i] * 51 for i in range(4)])
    np.testing.assert_array_equal(state["currents"], [1.0, 2.0, 3.0, 4.0] * 4)


def test_shared_sum_scale_and_sign():
    doc = document()
    obj = doc["simsopt_objs"]
    obj["sum"] = {
        "@class": "CurrentSum",
        "current_a": {"value": "current0"},
        "current_b": {"value": "current1"},
    }
    obj["scale"] = {"@class": "ScaledCurrent", "current_to_scale": {"value": "sum"}, "scale": -10.0}
    obj["coil3"]["current"] = {"value": "scale"}
    assert serialized_state(doc)["currents"][3] == -30.0


@pytest.mark.parametrize(
    "kind",
    [
        "cycle",
        "unsupported",
        "nonfinite",
        "not_scalar",
        "wrong_order",
        "alias",
        "rotated_base",
        "regularization",
    ],
)
def test_malformed_or_unsupported_sources_fail_closed(kind):
    doc = document()
    obj = doc["simsopt_objs"]
    if kind == "cycle":
        obj["current0"] = {
            "@class": "ScaledCurrent",
            "scale": 1,
            "current_to_scale": {"value": "current0"},
        }
    elif kind == "unsupported":
        obj["current0"]["@class"] = "CallableCurrent"
    elif kind == "nonfinite":
        obj["q0"]["x"]["data"] = [float("nan")]
    elif kind == "not_scalar":
        obj["q0"]["x"]["data"] = [1, 2]
    elif kind == "wrong_order":
        obj["d0"]["x"]["data"] = [0] * 99
    elif kind == "alias":
        obj["coil1"]["curve"]["value"] = "curve0"
    elif kind == "rotated_base":
        obj["curve0"]["@class"] = "RotatedCurve"
    else:
        obj["coil0"]["regularization"]["data"] = -1.0
    with pytest.raises(ValueError):
        serialized_state(doc)
