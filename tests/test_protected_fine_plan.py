"""Pure plans only: no model creation, native calls or geometry calculations."""

import copy

import numpy as np
import pytest

from fusion_baselines import protected_fine_plan as plan

CASES = [
    dict(
        label=f"{target}-n{n}-{method}",
        target=target,
        nbase=n,
        order=order,
        seed_label=f"n{n}-shape-d100mm",
        method=method,
    )
    for target in ("reference", "selected")
    for n, order in ((6, 5), (8, 7))
    for method in ("N", "V")
]
GRIDS = [
    (64, 64, 256, 32, 0),
    (128, 128, 256, 32, 0),
    (128, 128, 512, 32, 0),
    (128, 128, 512, 32, 0.5),
    (64, 64, 256, 64, 0),
    (64, 64, 512, 64, 0),
]


def selected(case=CASES[0]):
    n = case["nbase"] * 3 * (2 * case["order"] + 1)
    x = np.linspace(-0.125, 0.125, n)
    x[0] = -0.0
    x[-1] = np.nextafter(0.0, 1.0)
    return x


def test_case_matrix_exact_order_and_types():
    assert plan.cases() == CASES
    assert [case["label"] for case in plan.cases()] == [
        "reference-n6-N", "reference-n6-V", "reference-n8-N", "reference-n8-V",
        "selected-n6-N", "selected-n6-V", "selected-n8-N", "selected-n8-V",
    ]
    for case in plan.cases():
        assert plan.validate_case(case) is True
        assert type(case["nbase"]) is type(case["order"]) is int


@pytest.mark.parametrize("case", CASES, ids=lambda row: row["label"])
def test_independent_complete_eighty_request_schedule(case):
    models = plan.model_plan(case)
    assert len(models) == 8
    assert [row["id"] for row in models] == [
        "diagnostic-0", "diagnostic-1", "diagnostic-2", "diagnostic-3",
        "diagnostic-4", "diagnostic-5", "flux-256", "flux-512",
    ]
    calls, model_points, operation_ids = [], [], []
    for index, spec in enumerate(models):
        assert plan.validate_spec(spec) is True
        assert spec["case"] == case and spec["method"] == case["method"]
        assert set(spec) == {"id", "kind", "method", "grid", "case"} | (
            {"level"} if index < 6 else set()
        )
        initialization = plan.expected_calls(spec)
        assert initialization == [("loop", "A", 256)]
        actual = initialization.copy()
        operations = plan.operation_plan(spec, selected(case))
        if index < 6:
            p, t, c, n, offset = GRIDS[index]
            grid = dict(nphi=p, ntheta=t, ncoil=c, ninner=n, offset=offset)
            assert spec["grid"] == grid
            assert spec["level"] == dict(index=index, **grid)
            assert len(operations) == 1
            op = operations[0]
            assert op["operation_id"] == op["model_id"] == f"diagnostic-{index}"
            assert op["kind"] == "diagnostic" and op["index"] == index
            assert op["level"] == dict(index=index, **grid)
            assert plan.expected_calls(spec, op) == [
                ("boundary", "B", p * t), ("inner", "B", 3 * n**2),
                ("loop", "A", 256), ("boundary", "A", p * t),
                ("inner", "A", 3 * n**2), ("loop", "B", 256),
            ]
        else:
            ncoil = 256 if index == 6 else 512
            assert spec["grid"] == dict(nphi=64, ntheta=64, ncoil=ncoil, ninner=32, offset=0)
            assert len(operations) == 9
            grids = [("line", None, n) for n in (256, 512, 1024)] + [
                ("area", r, n) for r in (16, 32) for n in (256, 512, 1024)
            ]
            for i, (op, (form, radial, angular)) in enumerate(zip(operations, grids, strict=True)):
                assert op["index"] == i and op["form"] == form
                assert op["model_id"] == f"flux-{ncoil}" and op["ncoil"] == ncoil
                assert op["ntheta"] == angular
                stem = f"flux-{ncoil}-{form}-" + (f"{radial}-" if radial is not None else "")
                assert op["operation_id"] == stem + str(angular)
                if radial is None:
                    assert "nrho" not in op
                    expected = [("loop", "A", angular), ("loop", "B", angular)]
                else:
                    assert op["nrho"] == radial
                    expected = [
                        ("loop", "B", radial * angular), ("loop", "A", radial * angular)
                    ]
                assert plan.expected_calls(spec, op) == expected
        for op in operations:
            assert plan.validate_operation(spec, op, selected(case)) is True
            assert op["x"].dtype == np.dtype("float64")
            assert op["x"].tobytes() == selected(case).tobytes()
            operation_ids.append(op["operation_id"])
            actual.extend(plan.expected_calls(spec, op))
        assert len(actual) == (7 if index < 6 else 19)
        calls.extend(actual)
        model_points.append(sum(row[2] for row in actual))
    assert len(operation_ids) == len(set(operation_ids)) == 24
    assert len(calls) == 80
    assert all(quantity in ("A", "B") and type(n) is int for _, quantity, n in calls)
    assert model_points == [15104, 39680, 39680, 39680, 33536, 33536, 175872, 175872]
    assert sum(model_points) == 552960


def test_eight_case_work_totals_and_geometry_order():
    call_count = point_count = 0
    for case in CASES:
        for spec in plan.model_plan(case):
            calls = plan.expected_calls(spec)
            for op in plan.operation_plan(spec, selected(case)):
                calls += plan.expected_calls(spec, op)
            call_count += len(calls)
            point_count += sum(n for _, _, n in calls)
    assert call_count == 640
    assert point_count == 4423680
    assert call_count + 8 * 290 == 2960
    assert plan.geometry_levels() == [
        dict(ncoil=256, offset=0), dict(ncoil=512, offset=0),
        dict(ncoil=1024, offset=0), dict(ncoil=1024, offset=0.5),
    ]
    for level in plan.geometry_levels():
        assert plan.validate_geometry_level(level) is True


@pytest.mark.parametrize("key,value", [
    ("nbase", True), ("nbase", 6.0), ("nbase", np.int64(6)), ("nbase", 8),
    ("order", False), ("order", 5.0), ("order", 7), ("label", "reference-n6-V"),
    ("target", "selected"), ("seed_label", "selected"), ("method", "V"),
    ("method", np.str_("N")), ("extra", "value"),
])
def test_case_forged_types_and_identities_rejected(key, value):
    case = dict(CASES[0], **{key: value})
    with pytest.raises(ValueError):
        plan.model_plan(case)


@pytest.mark.parametrize("bad", [None, [], (), "reference-n6-N", 1, True, {}])
def test_case_nonmapping_and_missing_keys_rejected(bad):
    with pytest.raises(ValueError):
        plan.validate_case(bad)


@pytest.mark.parametrize("key", list(CASES[0]))
def test_case_each_missing_key_rejected(key):
    case = dict(CASES[0])
    del case[key]
    with pytest.raises(ValueError):
        plan.validate_case(case)


@pytest.mark.parametrize("index", range(8))
@pytest.mark.parametrize("change", ["extra", "missing", "kind", "method", "id", "case"])
def test_model_forgery_rejected(index, change):
    spec = plan.model_plan(CASES[0])[index]
    if change == "extra":
        spec["extra"] = 1
    elif change == "missing":
        del spec["grid"]
    elif change == "kind":
        spec["kind"] = "qualification"
    elif change == "method":
        spec["method"] = "V"
    elif change == "id":
        spec["id"] += "-copy"
    else:
        spec["case"]["nbase"] = True
    with pytest.raises(ValueError):
        plan.expected_calls(spec)


@pytest.mark.parametrize("key,value", [
    ("nphi", 64.0), ("ntheta", np.int64(64)), ("ncoil", True), ("ninner", 64),
    ("offset", False), ("offset", 0.0), ("offset", -0.0), ("offset", float("nan")),
    ("coil_offset", 0),
])
def test_model_grid_must_match_exact_descriptor(key, value):
    spec = plan.model_plan(CASES[0])[0]
    spec["grid"][key] = value
    with pytest.raises(ValueError):
        plan.validate_spec(spec)


@pytest.mark.parametrize("key,value", [("index", False), ("index", 0.0), ("offset", 0.5)])
def test_level_and_grid_are_separately_bound(key, value):
    spec = plan.model_plan(CASES[0])[0]
    spec["level"][key] = value
    with pytest.raises(ValueError):
        plan.validate_spec(spec)


@pytest.mark.parametrize("index", [0, 3, 6, 7])
@pytest.mark.parametrize("change", ["index", "index-type", "id", "model", "kind", "extra", "x"])
def test_operation_forgery_rejected(index, change):
    spec = plan.model_plan(CASES[0])[index]
    op = plan.operation_plan(spec, selected())[0]
    if change == "index":
        op["index"] += 1
    elif change == "index-type":
        op["index"] = float(op["index"])
    elif change == "id":
        op["operation_id"] += "-copy"
    elif change == "model":
        op["model_id"] = "qualification-N"
    elif change == "kind":
        op["kind"] = "qualification"
    elif change == "extra":
        op["extra"] = 1
    else:
        del op["x"]
    with pytest.raises(ValueError):
        plan.expected_calls(spec, op)


@pytest.mark.parametrize("key,value", [
    ("ncoil", 512), ("ncoil", 256.0), ("ntheta", 512), ("ntheta", 256.0),
    ("nrho", 1), ("form", "area"), ("index", False),
])
def test_line_flux_descriptor_is_not_interchangeable(key, value):
    spec = plan.model_plan(CASES[0])[6]
    op = plan.operation_plan(spec, selected())[0]
    op[key] = value
    with pytest.raises(ValueError):
        plan.expected_calls(spec, op)


@pytest.mark.parametrize("key,value", [
    ("nrho", 32), ("nrho", 16.0), ("nrho", True), ("ntheta", 512), ("form", "line"),
])
def test_area_flux_descriptor_is_not_interchangeable(key, value):
    spec = plan.model_plan(CASES[0])[6]
    op = plan.operation_plan(spec, selected())[3]
    op[key] = value
    with pytest.raises(ValueError):
        plan.expected_calls(spec, op)


@pytest.mark.parametrize("value", [
    None, True, 1.0, [], [0.0] * 197, [0.0] * 199, [0] * 198, [True] * 198,
    [False] + [0.0] * 197, np.zeros(198, dtype=np.int64), np.zeros(198, dtype=np.float32),
    np.zeros(198, dtype=complex), np.zeros(198, dtype=object), np.zeros((6, 3, 11)),
    np.zeros((1, 198)), np.zeros(360), np.full(198, np.nan), np.full(198, np.inf),
    tuple([0.0] * 198), np.zeros(198, dtype=bool), np.zeros(198, dtype=">f8"),
])
def test_selected_coordinates_cannot_be_coerced_or_truncated(value):
    spec = plan.model_plan(CASES[0])[0]
    with pytest.raises(ValueError):
        plan.operation_plan(spec, value)


def test_array_subclasses_cannot_override_validation():
    class Forged(np.ndarray):
        pass

    with pytest.raises(ValueError):
        plan.operation_plan(plan.model_plan(CASES[0])[0], selected().view(Forged))


def test_coordinate_key_must_be_plain_string_even_when_descriptor_matches():
    spec = plan.model_plan(CASES[0])[0]
    original = plan.operation_plan(spec, selected())[0]
    op = {np.str_(key) if key == "x" else key: value for key, value in original.items()}
    with pytest.raises(ValueError, match="operation"):
        plan.validate_operation(spec, op)


def test_coordinate_private_copies_json_roundtrip_and_signed_zero_binding():
    spec = plan.model_plan(CASES[0])[6]
    x = selected()
    ops = plan.operation_plan(spec, x)
    from_json = plan.operation_plan(spec, x.tolist())
    assert all(row["x"].tobytes() == x.tobytes() for row in from_json)
    for op in ops:
        assert not np.shares_memory(op["x"], x)
        assert plan.validate_operation(spec, op, x.tolist()) is True
    ops[0]["x"][1] = 123.0
    assert all(row["x"][1] == x[1] for row in ops[1:])
    x[2] = 456.0
    assert all(row["x"][2] != 456.0 for row in ops)
    op = plan.operation_plan(spec, selected())[0]
    op["x"][0] = 0.0
    with pytest.raises(ValueError, match="bits"):
        plan.validate_operation(spec, op, selected())


def test_returned_plans_and_sequences_do_not_share_mutable_state():
    case = copy.deepcopy(CASES[0])
    models = plan.model_plan(case)
    before = copy.deepcopy(models)
    case["method"] = "V"
    assert models == before
    models[0]["case"]["nbase"] = 99
    models[0]["level"]["nphi"] = 99
    models[0]["grid"]["offset"] = 99
    assert models[1:] == before[1:]
    assert plan.model_plan(CASES[0]) == before
    levels = plan.diagnostic_levels()
    levels[0]["ncoil"] = 1
    assert plan.diagnostic_levels()[0]["ncoil"] == 256
    geometry = plan.geometry_levels()
    geometry[0]["offset"] = 0.5
    assert plan.geometry_levels()[0]["offset"] == 0
    spec = before[0]
    op = plan.operation_plan(spec, selected())[0]
    op["level"]["offset"] = 0.5
    assert spec["level"]["offset"] == 0
    calls = plan.expected_calls(spec)
    calls.clear()
    assert plan.expected_calls(spec) == [("loop", "A", 256)]


@pytest.mark.parametrize("level", [
    None, {}, {"ncoil": 256}, {"ncoil": 256.0, "offset": 0},
    {"ncoil": 256, "offset": False}, {"ncoil": 256, "offset": 0.0},
    {"ncoil": 256, "offset": 0.5}, {"ncoil": 512, "offset": 0.5},
    {"ncoil": 1024, "offset": np.float64(0.5)},
    {"ncoil": 1024, "offset": 0.5, "index": 3},
])
def test_geometry_requires_exact_one_of_four_grids(level):
    with pytest.raises(ValueError):
        plan.validate_geometry_level(level)
