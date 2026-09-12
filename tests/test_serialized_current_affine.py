import copy

import numpy as np
import pytest
from test_serialized_field_state import document

from fusion_baselines.current_normalization import CANONICAL_TOTAL
from fusion_baselines.serialized_current_affine import current_map
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state


def fixture():
    doc = document()
    objects, names = doc["simsopt_objs"], [f"current{i}:x0" for i in range(3)]
    for i in range(4):
        objects[f"q{i}"].update(names=["x0"], free=dict(data=[i < 3]),
                               x=dict(data=[.01*(i+1) if i < 3 else CANONICAL_TOTAL]))
        labels = [f"x{j}" for j in range(51)]
        objects[f"d{i}"].update(names=labels, free=dict(data=[True]*51))
        names.extend(f"curve{i}:{label}" for label in labels)
    for i in range(3):
        objects[f"scaled{i}"] = dict(**{"@class": "ScaledCurrent"}, scale=1e7,
                                    current_to_scale=dict(value=f"current{i}"))
    objects["sum01"] = {"@class": "CurrentSum", "current_a": {"value": "scaled0"},
                        "current_b": {"value": "scaled1"}}
    objects["sum012"] = {"@class": "CurrentSum", "current_a": {"value": "sum01"},
                         "current_b": {"value": "scaled2"}}
    objects["minus_sum"] = {"@class": "ScaledCurrent", "scale": -1,
                            "current_to_scale": {"value": "sum012"}}
    objects["fourth"] = {"@class": "CurrentSum", "current_a": {"value": "current3"},
                         "current_b": {"value": "minus_sum"}}
    currents = ["scaled0", "scaled1", "scaled2", "fourth"]
    for i, owner in enumerate(currents):
        objects[f"neg{i}"] = {"@class": "ScaledCurrent", "scale": -1,
                               "current_to_scale": {"value": owner}}
    for i in range(16):
        objects[f"physical{i}"] = dict(curve=dict(value=f"curve{i%4}"), regularization=.1,
            current=dict(value=currents[i%4] if (i//4)%2 == 0 else f"neg{i%4}"))
    objects["field"]["coils"] = [dict(value=f"physical{i}") for i in range(16)]
    return doc, names


def test_canonical_affine_current_graph_and_named_column_permutation():
    doc, names = fixture()
    result = current_map(doc, names)
    x = named_serialized_values(doc, names)
    np.testing.assert_allclose(result["matrix"] @ x[result["columns"]] + result["constant"],
                               serialized_state(doc)["currents"], rtol=1e-14, atol=1e-9)
    reversed_names = list(reversed(names))
    permuted = current_map(doc, reversed_names)
    assert np.array_equal(permuted["columns"], len(names)-1-result["columns"])
    assert np.array_equal(permuted["matrix"], result["matrix"])


def test_current_scale_and_symmetry_mutations_rejected():
    document, names = fixture()
    objects = document["simsopt_objs"]
    coil_ref = objects[document["graph"]["value"]]["coils"][0]["value"]
    owner = objects[coil_ref]["current"]["value"]
    changed = copy.deepcopy(document)
    changed["simsopt_objs"][owner]["scale"] = 1e6
    with pytest.raises(ValueError, match="scaling"):
        current_map(changed, names)
    changed = copy.deepcopy(document)
    coils = changed["simsopt_objs"][changed["graph"]["value"]]["coils"]
    first = changed["simsopt_objs"][coils[0]["value"]]["current"]
    changed["simsopt_objs"][coils[4]["value"]]["current"] = first
    with pytest.raises(ValueError, match="symmetry"):
        current_map(changed, names)
