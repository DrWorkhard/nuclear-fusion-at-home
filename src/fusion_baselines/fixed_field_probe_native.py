"""One owned value-only model; no admission, storage, CLI or scientific acceptance.

The caller supplies admitted inputs, a synchronous native ledger and resource
guard. Importing this module does not import a native model. The two lazy helper
bridges are replaced by instrumented models in qualification tests.
"""

import copy
import os

import numpy as np

from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_fine_control import THREADS
from fusion_baselines.protected_search_journal import _encode

_ACTIVE = None
_INIT = dict(seed_A_calls=1, seed_A_points=256)
_CONSTRUCTION = dict(
    ncoil=256,
    nphi=64,
    ntheta=64,
    ninner=32,
    offset=0,
    nloop=256,
    geometry_nphi=128,
    geometry_ntheta=128,
    geometry_full_torus=True,
    geometry_offset=0,
)
_METRICS = {
    "JN",
    "JV",
    "scale",
    "B2_scale",
    "unit_flux",
    "target_flux",
    "flux",
    "current",
    "normal_rms",
    "normal_max",
    "vector_rms",
    "boundary_B_rms",
    "lengths",
    "kappa_max",
    "coil_distance",
    "surface_distance",
    "geometry_penalty",
    "J",
    "frozen_scale",
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, label):
    _need(
        type(actual) is type(expected) and _encode(actual) == _encode(expected),
        "exact typed identity: " + label,
    )


def _scalar(value, label):
    _need(
        type(value) in (float, int, np.float64) and np.isfinite(value),
        "finite real scalar: " + label,
    )
    return float(value)


def _environment():
    _need(
        os.name == "posix" and all(os.environ.get(k) == v for k, v in THREADS.items()),
        "unchanged POSIX single-thread native environment required",
    )


def _make_model(source, case, spec, seed, callback):
    from run_clear_coil_field_start import make_model

    return make_model(source, case, spec, seed, callback)


def _supplement(model, arrays, scale):
    from run_clear_coil_field_start import supplement

    return supplement(model, arrays, scale)


def _coordinates(case, value, expected, label):
    actual = plan._coordinates(case, value)
    _need(actual.tobytes() == expected.tobytes(), "exact coordinate bits: " + label)


def _snapshot(snapshot, case, seed, x, b2):
    _need(
        type(snapshot) is dict
        and set(snapshot)
        == {
            "schema_version",
            "nfp",
            "nbase",
            "order",
            "names",
            "base_coefficients",
            "physical",
            "scale",
            "B2_scale",
            "unit_flux",
            "target_flux",
            "seed_unit_flux",
            "method",
            "sources",
            "construction",
            "initialization_work",
            "seed_geometry",
        },
        "complete coarse snapshot schema required",
    )
    for key, value in dict(
        schema_version=1,
        nfp=2,
        nbase=case["nbase"],
        order=case["order"],
        method="N",
        names=seed["names"],
        sources=seed["sources"]["reference"],
        seed_geometry=seed,
        B2_scale=b2,
        construction=_CONSTRUCTION,
        initialization_work=_INIT,
    ).items():
        _same(snapshot[key], value, "coarse snapshot " + key)
    coefficients = np.asarray(snapshot["base_coefficients"])
    _need(
        coefficients.dtype == np.dtype(np.float64)
        and coefficients.shape == (case["nbase"], 3, 2 * case["order"] + 1),
        "complete float64 coarse coefficient tensor",
    )
    _coordinates(case, coefficients.ravel(), x, "coarse snapshot")
    for key in ("scale", "unit_flux", "target_flux", "seed_unit_flux"):
        _need(_scalar(snapshot[key], key) != 0, "nonzero coarse " + key)
    _need(
        abs(snapshot["unit_flux"]) > 1e-12
        and snapshot["scale"] == snapshot["target_flux"] / snapshot["unit_flux"],
        "exact nondegenerate original coarse flux normalization",
    )
    _need(
        type(snapshot["physical"]) is list and len(snapshot["physical"]) == len(seed["physical"]),
        "all physical copies",
    )
    for row, original in zip(snapshot["physical"], seed["physical"], strict=True):
        expected = dict(
            original, current=float(1e5 * snapshot["scale"] * (-1 if original["flip"] else 1))
        )
        _same(row, expected, "coarse physical matrix/current")


def _fixed_model(model, case, seed, seed_x, grid, b2, flux=None):
    for key, value in dict(
        nbase=case["nbase"],
        order=case["order"],
        nfp=2,
        method="N",
        names=seed["names"],
        local_names=[n.split("/", 1)[1] for n in seed["names"][: 3 * (2 * case["order"] + 1)]],
        _seed_geometry=seed,
        initialization_work=_INIT,
        **grid,
    ).items():
        _same(getattr(model, key), value, "original model " + key)
    _coordinates(case, model.seed_x, seed_x, "original model seed")
    _same(model.target["sources"], seed["sources"]["reference"], "model sources")
    _same(_scalar(model.B2_scale, "B2"), b2, "model B2")
    _need(_scalar(model.target_flux, "target flux") != 0, "nonzero signed target flux")
    actual_flux = _scalar(model.seed_unit_flux, "initializer flux")
    _need(abs(actual_flux) > 1e-12, "nondegenerate original-seed initializer")
    if flux is not None:
        _same(actual_flux, flux, "unchanged initializer flux")
    _need(
        len(model.base_currents) == case["nbase"] and len(model.coils) == len(seed["physical"]),
        "all original current copies",
    )
    for current in model.base_currents:
        _same(_scalar(current.get_value(), "base current"), 100000.0, "base current")
    for coil, row in zip(model.coils, seed["physical"], strict=True):
        _same(
            _scalar(coil.current.get_value(), "physical current"),
            -100000.0 if row["flip"] else 100000.0,
            "original signed physical current",
        )
    return actual_flux


def _arrays(raw, case, level, snapshot):
    boundary, inner, coils = (
        level["nphi"] * level["ntheta"],
        3 * level["ninner"] ** 2,
        4 * case["nbase"],
    )
    shapes = dict(
        boundary_points=(boundary, 3),
        boundary_normals=(boundary, 3),
        boundary_weights=(boundary,),
        boundary_B=(boundary, 3),
        boundary_A=(boundary, 3),
        inner_points=(inner, 3),
        inner_target=(inner, 3),
        inner_B=(inner, 3),
        inner_A=(inner, 3),
        loop_points=(256, 3),
        loop_tangents=(256, 3),
        loop_A=(256, 3),
        loop_B=(256, 3),
        coil_positions=(coils, level["ncoil"], 3),
        coil_tangents=(coils, level["ncoil"], 3),
        coil_currents=(coils,),
    )
    _need(type(raw) is dict and set(raw) == set(shapes), "complete exact raw array schema")
    result = {}
    for key, shape in shapes.items():
        value = raw[key]
        _need(
            type(value) is np.ndarray
            and value.dtype.kind in "iuf"
            and value.shape == shape
            and np.isfinite(value).all(),
            "finite complete array " + key,
        )
        result[key] = value.copy(order="C")
    currents = np.array([row["current"] for row in snapshot["physical"]], dtype=np.float64)
    _need(
        result["coil_currents"].dtype == currents.dtype
        and result["coil_currents"].tobytes() == currents.tobytes(),
        "exact raw physical currents",
    )
    return result


def evaluate_model(
    source, case, seed, x, level, *, frozen_snapshot=None, callback, guard=lambda: None
):
    """Return a private seven-call result, or fail without any retry/acceptance.

    ``level`` is the exact registered six-key grid mapping. Only level zero may
    create a snapshot; other levels return the supplied new coarse snapshot
    unchanged. The caller, not this bridge, admits hashes and persists failures.
    """
    global _ACTIVE
    if _ACTIVE is not None:
        _ACTIVE["failed"] = True
        raise RuntimeError("reentrant/concurrent fixed probe model is prohibited")
    owner = dict(failed=False, active=True, receiving=False, phase="initialization")
    _ACTIVE = owner
    calls, pending = [], None

    def check():
        _need(owner["active"] and not owner["failed"], "owned probe operation is poisoned/closed")
        _environment()
        guard()
        _need(not owner["failed"], "probe guard swallowed an ownership failure")
        _environment()

    try:
        _need(callable(callback) and callable(guard), "synchronous callback and guard required")
        check()
        plan.validate_case(case)
        _need(case["target"] == "reference" and case["method"] == "N", "reference N pairs only")
        _need(any(plan._same(level, row) for row in plan.diagnostic_levels()), "exact probe level")
        from fusion_baselines.clear_coil_field import geometry_seed

        source, case, level = copy.deepcopy(source), copy.deepcopy(case), copy.deepcopy(level)
        original = geometry_seed(seed)
        _same(seed, original, "original seed document")
        seed = original
        _same(seed["nbase"], case["nbase"], "seed class")
        _same(seed["order"], case["order"], "seed order")
        _same(source["targets"], seed["sources"], "both original target sources")
        b2 = _scalar(source["normalization"]["reference"]["B2_scale"], "source B2")
        _need(b2 > 0, "positive source B2")
        x = plan._coordinates(case, x)
        seed_x = plan._coordinates(case, np.asarray(seed["base_coefficients"]).ravel())
        snapshot = copy.deepcopy(frozen_snapshot)
        _need((snapshot is None) == (level["index"] == 0), "coarse-only new normalization")
        if snapshot is not None:
            _snapshot(snapshot, case, seed, x, b2)
        grid = {k: v for k, v in level.items() if k != "index"}
        spec = dict(
            id=f"diagnostic-{level['index']}",
            kind="diagnostic",
            method="N",
            grid=grid,
            level=level,
            case=case,
        )
        boundary, inner = grid["nphi"] * grid["ntheta"], 3 * grid["ninner"] ** 2
        schedule = [
            ("loop", "A", 256),
            ("boundary", "B", boundary),
            ("inner", "B", inner),
            ("loop", "A", 256),
            ("boundary", "A", boundary),
            ("inner", "A", inner),
            ("loop", "B", 256),
        ]

        def receive(event):
            nonlocal pending
            try:
                check()
                _need(not owner["receiving"], "reentrant native callback")
                owner["receiving"] = True
                _need(type(event) is dict, "native event mapping required")
                index = len(calls)
                _need(
                    index < 7 and (owner["phase"] != "initialization" or index == 0),
                    "no native work beyond the exact phase schedule",
                )
                field, quantity, points = schedule[index]
                for key, value in dict(
                    index=index, field=field, quantity=quantity, points=points
                ).items():
                    _same(event.get(key), value, "native dispatch " + key)
                started = _scalar(event.get("started_monotonic"), "native start")
                _need(started >= 0, "nonnegative native start")
                status = event.get("status")
                keys = {
                    "index",
                    "field",
                    "quantity",
                    "points",
                    "status",
                    "started_monotonic",
                    "native_started",
                    "native_completed",
                }
                if status == "attempted":
                    _need(pending is None and set(event) == keys, "one exact outstanding attempt")
                    _need(
                        not calls or started >= calls[-1]["completed_monotonic"],
                        "monotonic clock across native calls",
                    )
                    _need(
                        event["native_started"] is False and event["native_completed"] is False,
                        "pre-dispatch attempt flags",
                    )
                    pending = copy.deepcopy(event)
                else:
                    _need(pending is not None, "native outcome without attempt")
                    _same(event["started_monotonic"], pending["started_monotonic"], "native start")
                    if status == "error":
                        callback(copy.deepcopy(event))
                        raise ValueError("native request reported an error")
                    _need(
                        status == "completed" and set(event) == keys | {"completed_monotonic"},
                        "exact native completion event",
                    )
                    _need(
                        event["native_started"] is True
                        and event["native_completed"] is True
                        and _scalar(event["completed_monotonic"], "native finish") >= started,
                        "native completion flags/time",
                    )
                callback(copy.deepcopy(event))
                check()
                if status == "completed":
                    calls.append(copy.deepcopy(event))
                    pending = None
            except BaseException:
                owner["failed"] = True
                raise
            finally:
                owner["receiving"] = False

        check()
        model = _make_model(
            copy.deepcopy(source),
            copy.deepcopy(case),
            copy.deepcopy(spec),
            copy.deepcopy(seed),
            receive,
        )
        check()
        _need(not hasattr(model, "_fixed_probe_owner"), "fresh unowned model required")
        model._fixed_probe_owner = owner
        flux = _fixed_model(model, case, seed, seed_x, grid, b2)
        _coordinates(case, model.x, seed_x, "initializer starts at original seed")
        _need(
            model._cache is None and len(calls) == 1 and pending is None,
            "one fresh initializer and empty cache required",
        )
        _same(model.native_calls, calls, "initializer callback receipts")
        initialization = dict(
            seed_unit_flux=flux,
            names=copy.deepcopy(seed["names"]),
            seed_x=seed_x.tolist(),
            ncoil=grid["ncoil"],
            initialization_work=copy.deepcopy(_INIT),
        )
        owner["phase"] = "candidate"
        check()
        model.x = x.copy()
        model._cache = None
        _coordinates(case, model.x, x, "candidate assignment")
        if snapshot is None:
            snapshot = model.snapshot(x.copy())
            check()
            _snapshot(snapshot, case, seed, x, b2)
            _same(snapshot["seed_unit_flux"], flux, "coarse initializer snapshot")
            metrics = copy.deepcopy(model._state(x.copy(), B2_scale=b2)["metrics"])
            check()
            raw = model.arrays(x.copy(), B2_scale=b2)
        else:
            _same(
                _scalar(model.target_flux, "target flux"), snapshot["target_flux"], "frozen target"
            )
            metrics = model.diagnostics(x.copy(), snapshot["scale"], b2)
            check()
            raw = model.arrays(x.copy(), scale=snapshot["scale"], B2_scale=b2)
        check()
        raw = _supplement(model, raw, snapshot["scale"])
        check()
        _need(model._fixed_probe_owner is owner, "unchanged model ownership")
        _fixed_model(model, case, seed, seed_x, grid, b2, flux)
        _coordinates(case, model.x, x, "unchanged candidate after work")
        _need(len(calls) == 7 and pending is None, "exact seven complete native calls")
        _same(model.native_calls, calls, "all native callback receipts")
        _snapshot(snapshot, case, seed, x, b2)
        _same(_scalar(model.target_flux, "target flux"), snapshot["target_flux"], "model target")
        _need(type(metrics) is dict and set(metrics) == _METRICS, "exact metric schema")
        _need(metrics["frozen_scale"] is (level["index"] != 0), "correct normalization mode")
        for key in _METRICS - {"frozen_scale", "lengths", "kappa_max"}:
            _scalar(metrics[key], "metric " + key)
        for key in ("lengths", "kappa_max"):
            _need(
                type(metrics[key]) is list and len(metrics[key]) == case["nbase"], "per-coil " + key
            )
            for value in metrics[key]:
                _scalar(value, key)
        for key in ("scale", "B2_scale", "target_flux"):
            _same(metrics[key], snapshot[key], "fixed metric " + key)
        _same(metrics["current"], float(1e5 * snapshot["scale"]), "actual common current")
        result = dict(
            snapshot=copy.deepcopy(snapshot),
            metrics=copy.deepcopy(metrics),
            arrays=_arrays(raw, case, level, snapshot),
            initialization=initialization,
            native_calls=copy.deepcopy(calls),
        )
        check()
        return result
    except BaseException:
        owner["failed"] = True
        raise
    finally:
        owner["active"] = False
        _ACTIVE = None
