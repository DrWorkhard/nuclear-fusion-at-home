"""Pure, typed plans for the registered eight-model selected-candidate fine phase.

No field/geometry calculations or physical admission. Model specifications carry
their case so coordinate lengths and the explicit N/V method cannot be inferred
from a mutable external selection. Every returned container/coordinate is private.
"""

import copy

import numpy as np


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected):
    """Exact plain descriptor types, including int versus bool/float/NumPy."""
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return (
            all(type(key) is str for key in actual)
            and set(actual) == set(expected)
            and all(_same(actual[key], value) for key, value in expected.items())
        )
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            _same(a, b) for a, b in zip(actual, expected, strict=True)
        )
    return actual == expected


def cases():
    """Eight original cases in their registered target/class/method order."""
    return [
        dict(
            label=f"{target}-n{nbase}-{method}",
            target=target,
            nbase=nbase,
            order=order,
            seed_label=f"n{nbase}-shape-d100mm",
            method=method,
        )
        for target in ("reference", "selected")
        for nbase, order in ((6, 5), (8, 7))
        for method in ("N", "V")
    ]


def validate_case(case):
    """Require an exact original descriptor; do not silently repair its label."""
    _need(any(_same(case, row) for row in cases()), "exact registered fine case required")
    return True


def diagnostic_levels():
    """Boundary half-offset does not shift coil quadrature or initialization."""
    return [
        dict(index=i, nphi=p, ntheta=t, ncoil=c, ninner=n, offset=offset)
        for i, (p, t, c, n, offset) in enumerate(
            (
                (64, 64, 256, 32, 0),
                (128, 128, 256, 32, 0),
                (128, 128, 512, 32, 0),
                (128, 128, 512, 32, 0.5),
                (64, 64, 256, 64, 0),
                (64, 64, 512, 64, 0),
            )
        )
    ]


def geometry_levels():
    """Four direct-geometry grids; here the half-offset shifts coil samples."""
    return [
        dict(ncoil=ncoil, offset=offset)
        for ncoil, offset in ((256, 0), (512, 0), (1024, 0), (1024, 0.5))
    ]


def validate_geometry_level(level):
    _need(
        any(_same(level, row) for row in geometry_levels()),
        "exact registered fine geometry level required",
    )
    return True


def model_plan(case):
    """Six diagnostic models, then two flux models; all start at the original seed.

    The plan does not construct a model or prove its original-seed/current identity.
    Those checks belong to the separately qualified fine adapter and auditor.
    """
    validate_case(case)
    base = dict(nphi=64, ntheta=64, ncoil=256, ninner=32, offset=0)
    return [
        dict(
            id=f"diagnostic-{level['index']}",
            kind="diagnostic",
            method=case["method"],
            grid={key: value for key, value in level.items() if key != "index"},
            level=level,
            case=copy.deepcopy(case),
        )
        for level in diagnostic_levels()
    ] + [
        dict(
            id=f"flux-{ncoil}",
            kind="flux",
            method=case["method"],
            grid=dict(base, ncoil=ncoil),
            case=copy.deepcopy(case),
        )
        for ncoil in (256, 512)
    ]


def validate_spec(spec):
    _need(type(spec) is dict and "case" in spec, "exact registered fine model required")
    _need(
        any(_same(spec, row) for row in model_plan(spec["case"])),
        "exact registered fine model required",
    )
    return True


def _coordinates(case, value):
    # JSON states use plain float lists; live model coordinates use float64
    # ndarrays. Reject coercions that would mask booleans, object arrays, truncated
    # precision, extra dimensions or an unrelated class's coordinate layout.
    _need(
        type(value) is np.ndarray
        or (type(value) is list and all(type(item) is float for item in value)),
        "plain float list or float64 coordinate array required",
    )
    array = np.asarray(value)
    size = case["nbase"] * 3 * (2 * case["order"] + 1)
    _need(
        array.dtype == np.dtype(np.float64)
        and array.shape == (size,)
        and np.isfinite(array).all(),
        "complete finite float64 selected coordinates required",
    )
    return array.copy(order="C")


def _operation_descriptors(spec):
    if spec["kind"] == "diagnostic":
        return [
            dict(
                operation_id=spec["id"],
                model_id=spec["id"],
                kind="diagnostic",
                index=spec["level"]["index"],
                level=copy.deepcopy(spec["level"]),
            )
        ]
    grids = [dict(form="line", ntheta=n) for n in (256, 512, 1024)] + [
        dict(form="area", nrho=r, ntheta=n)
        for r in (16, 32)
        for n in (256, 512, 1024)
    ]
    return [
        dict(
            operation_id=f"{spec['id']}-{grid['form']}-"
            + (f"{grid['nrho']}-" if grid["form"] == "area" else "")
            + str(grid["ntheta"]),
            model_id=spec["id"],
            kind="flux",
            index=i,
            ncoil=spec["grid"]["ncoil"],
            **grid,
        )
        for i, grid in enumerate(grids)
    ]


def operation_plan(spec, selected_x):
    """One diagnostic or nine flux operations, each owning the full selected x.

    Including x on flux operations does not make legacy execution assign it:
    the adapter must explicitly assign and bit-check model.x before dispatch.
    """
    validate_spec(spec)
    x = _coordinates(spec["case"], selected_x)
    return [dict(row, x=x.copy()) for row in _operation_descriptors(spec)]


def validate_operation(spec, operation, selected_x=None):
    """Validate one registered operation, optionally bind its coordinate bytes."""
    validate_spec(spec)
    _need(
        type(operation) is dict and "x" in operation
        and all(type(key) is str for key in operation),
        "exact fine operation required",
    )
    descriptor = {key: value for key, value in operation.items() if key != "x"}
    _need(
        any(_same(descriptor, row) for row in _operation_descriptors(spec)),
        "exact registered fine operation descriptor required",
    )
    actual = _coordinates(spec["case"], operation["x"])
    if selected_x is not None:
        expected = _coordinates(spec["case"], selected_x)
        _need(actual.tobytes() == expected.tobytes(), "exact selected coordinate bits required")
    return True


def expected_calls(spec, operation=None):
    """Exact (field, quantity, points) sequence; None is model initialization.

    This is a declaration, not a work ledger. The caller reserves and records
    actual dispatches and must enforce whole-cell operation/model ordering.
    """
    validate_spec(spec)
    if operation is None:
        return [("loop", "A", 256)]
    validate_operation(spec, operation)
    if spec["kind"] == "flux":
        points = operation["ntheta"] * operation.get("nrho", 1)
        quantities = ("A", "B") if operation["form"] == "line" else ("B", "A")
        return [("loop", quantity, points) for quantity in quantities]
    grid = spec["grid"]
    boundary, inner = grid["nphi"] * grid["ntheta"], 3 * grid["ninner"] ** 2
    return [
        ("boundary", "B", boundary),
        ("inner", "B", inner),
        ("loop", "A", 256),
        ("boundary", "A", boundary),
        ("inner", "A", inner),
        ("loop", "B", 256),
    ]
