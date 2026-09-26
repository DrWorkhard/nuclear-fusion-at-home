"""Fine-only bridge for admitted fixed candidates, with no import-time science.

The caller owns work reservations, synchronous native-event persistence, source
admission, disk/time guards and independent acceptance. No CLI or native launch
authorization is supplied here. Tests replace the three lazy bridge functions.
"""

import copy
import os
from contextlib import contextmanager

from fusion_baselines.protected_fine_control import THREADS
from fusion_baselines.protected_search_journal import _encode


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _environment():
    _need(os.name == "posix", "fine native bridge requires POSIX")
    _need(
        all(os.environ.get(key) == value for key, value in THREADS.items()),
        "fine native bridge requires unchanged single-thread environment",
    )


def _build_context(archive, case):
    _environment()
    from protected_fine_inputs import build_context

    return build_context(archive, case)


def _make_model(source, case, spec, seed, callback):
    _environment()
    from run_clear_coil_field_start import make_model

    return make_model(source, case, spec, seed, callback)


def _execute(model, operation, frozen):
    _environment()
    from run_clear_coil_field_start import execute

    return execute(model, operation, frozen)


class FineNativeAdapter:
    """Eight owned seed models; every operation reinstalls the same selection.

    ``initialize(spec, native_callback)`` returns a live model, and
    ``metadata(model)`` returns its separately recorded original-seed identity.
    ``execute(model, operation)`` returns private ``record/arrays/metadata``.
    No method persists raw results or acknowledges scientific acceptance.
    """

    def __init__(self, context, archive):
        _environment()
        import numpy as np

        from fusion_baselines import protected_fine_plan as plan

        self._np, self._plan = np, plan
        plan.validate_case(context["case"])
        expected = _build_context(copy.deepcopy(archive), copy.deepcopy(context["case"]))
        self._same(context, expected, "source-bound fine context")
        self._context, self._archive = copy.deepcopy(expected), copy.deepcopy(archive)
        self._original = self._context["original_context"]
        self._seed = self._original["seed"]
        self._source = self._archive["archived_source"]["physics_sources"]["native_sources"][
            "cell_sources"
        ]
        self._case = self._context["case"]
        self._selected = plan._coordinates(self._case, self._context["selected"]["state"]["x"])
        self._seed_x = np.asarray(self._seed["base_coefficients"], dtype=np.float64).ravel()
        self._snapshot = self._context["selected"]["snapshot"]
        self._snapshot_ref = self._context["coarse"]["selected_snapshot"]
        self._models, self._failed, self._busy, self._dispatch = [], False, False, None
        self._fixed_context()
        _environment()

    def _same(self, actual, expected, label):
        np = self._np
        if type(expected) is np.ndarray:
            _need(
                type(actual) is np.ndarray
                and actual.dtype == expected.dtype
                and actual.shape == expected.shape
                and actual.tobytes(order="C") == expected.tobytes(order="C"),
                "exact array identity: " + label,
            )
        elif type(expected) is dict:
            _need(type(actual) is dict and set(actual) == set(expected), "exact mapping: " + label)
            for key, value in expected.items():
                self._same(actual[key], value, label + "/" + key)
        elif type(expected) is list:
            _need(type(actual) is list and len(actual) == len(expected), "exact list: " + label)
            for index, (a, b) in enumerate(zip(actual, expected, strict=True)):
                self._same(a, b, label + "/" + str(index))
        else:
            _need(
                type(actual) is type(expected) and _encode(actual) == _encode(expected),
                "exact typed identity: " + label,
            )

    def _scalar(self, value, label):
        _need(type(value) in (int, float, self._np.float64), "real scalar: " + label)
        result = float(value)
        _need(self._np.isfinite(result), "finite scalar: " + label)
        return result

    def _fixed_context(self):
        case, original, seed, snapshot = self._case, self._original, self._seed, self._snapshot
        self._same(original["case"], case, "original case")
        self._same(seed["nbase"], case["nbase"], "seed class")
        self._same(seed["order"], case["order"], "seed order")
        self._same(snapshot["seed_geometry"], seed, "original geometry, not selected seed")
        self._same(snapshot["names"], seed["names"], "selected named mapping")
        for key in ("nbase", "order", "method"):
            self._same(snapshot[key], case[key], "selected " + key)
        self._same(snapshot["sources"], original["target_sources"], "selected target sources")
        self._same(
            self._source["targets"][case["target"]],
            original["target_sources"],
            "native target sources",
        )
        self._same(seed["sources"], self._source["targets"], "both original target sources")
        self._same(snapshot["B2_scale"], original["B2_scale"], "frozen B2")
        self._same(
            self._source["normalization"][case["target"]]["B2_scale"],
            original["B2_scale"],
            "native B2",
        )
        for key in ("scale", "target_flux", "unit_flux", "seed_unit_flux", "B2_scale"):
            value = self._scalar(snapshot[key], key)
            _need(value != 0 and (key != "B2_scale" or value > 0), "nondegenerate frozen " + key)
        selected = self._np.asarray(snapshot["base_coefficients"], dtype=self._np.float64).ravel()
        _need(selected.tobytes() == self._selected.tobytes(), "selected snapshot coordinate bits")
        physical = snapshot["physical"]
        _need(
            type(physical) is list and len(physical) == 4 * case["nbase"],
            "every selected physical current required",
        )
        for actual, geometry in zip(physical, seed["physical"], strict=True):
            self._same(
                {k: v for k, v in actual.items() if k != "current"},
                geometry,
                "original physical symmetry",
            )
            expected = float(1e5 * snapshot["scale"] * (-1 if geometry["flip"] else 1))
            self._same(actual["current"], expected, "frozen selected physical current")

    def _healthy(self):
        if self._failed:
            raise RuntimeError("fine native adapter failed; no retry or further native events")

    @contextmanager
    def _operation(self):
        entered = False
        try:
            self._healthy()
            _need(not self._busy, "reentrant fine native adapter operation")
            self._busy = entered = True
            _environment()
            yield
            self._healthy()
            _environment()
        except BaseException:
            self._failed = True
            raise
        finally:
            if entered:
                self._busy, self._dispatch = False, None

    def _entry(self, model):
        found = [row for row in self._models if row["model"] is model]
        _need(len(found) == 1, "fine adapter-owned distinct model required")
        return found[0]

    def _currents(self, model):
        _need(len(model.base_currents) == self._case["nbase"], "original base current count")
        for current in model.base_currents:
            self._same(
                self._scalar(current.get_value(), "base current"),
                100000.0,
                "original 100000A base current",
            )
        _need(len(model.coils) == 4 * self._case["nbase"], "all physical current copies")
        currents = [
            self._scalar(coil.current.get_value(), "physical current") for coil in model.coils
        ]
        expected = [float(-1e5 if row["flip"] else 1e5) for row in self._seed["physical"]]
        self._same(currents, expected, "original signed 100000A physical currents")
        return currents

    def _fixed_model(self, model, spec, *, initialized_flux=None):
        expected = dict(
            nbase=self._case["nbase"],
            order=self._case["order"],
            nfp=2,
            method=self._case["method"],
            names=self._seed["names"],
            local_names=[
                name.split("/", 1)[1]
                for name in self._seed["names"][: 3 * (2 * self._case["order"] + 1)]
            ],
            _seed_geometry=self._seed,
            initialization_work=dict(seed_A_calls=1, seed_A_points=256),
            **spec["grid"],
        )
        for key, value in expected.items():
            self._same(getattr(model, key), value, "fixed native model " + key)
        seed_x = self._plan._coordinates(self._case, model.seed_x)
        _need(seed_x.tobytes() == self._seed_x.tobytes(), "actual original model seed bits")
        self._same(
            model.target["sources"], self._original["target_sources"], "model target sources"
        )
        for key in ("B2_scale", "target_flux"):
            self._same(
                self._scalar(getattr(model, key), key),
                self._snapshot[key],
                "fixed native model " + key,
            )
        flux = self._scalar(model.seed_unit_flux, "original seed initializer flux")
        _need(abs(flux) > 1e-12, "nondegenerate original seed initializer flux")
        if initialized_flux is not None:
            self._same(flux, initialized_flux, "unchanged initializer scalar")
        self._currents(model)
        return flux

    def _calls(self, model, start, spec, operation=None):
        expected = self._plan.expected_calls(spec, operation)
        calls = model.native_calls[start:]
        _need(
            type(model.native_calls) is list and len(calls) == len(expected),
            "complete exact native callback request count",
        )
        for index, (actual, (field, quantity, points)) in enumerate(
            zip(calls, expected, strict=True)
        ):
            for key, value in dict(
                index=start + index,
                field=field,
                quantity=quantity,
                points=points,
                status="completed",
                native_started=True,
                native_completed=True,
            ).items():
                self._same(actual.get(key), value, "native request " + key)
        return copy.deepcopy(calls)

    def initialize(self, spec, native_callback):
        with self._operation():
            self._plan.validate_spec(spec)
            self._same(spec["case"], self._case, "native model case")
            _need(callable(native_callback), "caller native ledger callback required")
            _need(
                len(self._models) < 8
                and all(row["spec"]["id"] != spec["id"] for row in self._models),
                "eight distinct fine model specifications only",
            )
            spec = copy.deepcopy(spec)
            self._dispatch = spec["id"]

            def receive(event):
                try:
                    self._healthy()
                    _environment()
                    _need(
                        self._busy and self._dispatch == spec["id"],
                        "native work outside an owned fine operation",
                    )
                    native_callback(copy.deepcopy(event))
                    self._healthy()
                    _environment()
                except BaseException:
                    self._failed = True
                    raise

            model = _make_model(
                copy.deepcopy(self._source),
                copy.deepcopy(self._case),
                copy.deepcopy(spec),
                copy.deepcopy(self._seed),
                receive,
            )
            self._healthy()
            _need(
                all(row["model"] is not model for row in self._models),
                "distinct fresh native model",
            )
            flux = self._fixed_model(model, spec)
            actual = self._plan._coordinates(self._case, model.x)
            _need(
                actual.tobytes() == self._seed_x.tobytes(),
                "initialize at ORIGINAL seed coordinates",
            )
            _need(model._cache is None, "fresh fine model has no cached field bundle")
            calls = self._calls(model, 0, spec)
            self._models.append(dict(model=model, spec=spec, flux=flux, calls=calls, operations=0))
            return model

    def _metadata(self, entry):
        model, spec = entry["model"], entry["spec"]
        flux = self._fixed_model(model, spec, initialized_flux=entry["flux"])
        self._same(model.native_calls[:1], entry["calls"], "immutable initializer native record")
        result = dict(
            spec=copy.deepcopy(spec),
            case=copy.deepcopy(self._case),
            original_seed=copy.deepcopy(self._original["seed_reference"]),
            geometry_audit=copy.deepcopy(self._original["geometry_audit_reference"]),
            target_sources=copy.deepcopy(self._original["target_sources"]),
            coarse=copy.deepcopy(self._context["coarse"]),
            names=copy.deepcopy(self._seed["names"]),
            seed_x=self._seed_x.tolist(),
            selected_x=self._selected.tolist(),
            original_seed_unit_flux=flux,
            initializer_physical_currents=self._currents(model),
            initialization_work=dict(seed_A_calls=1, seed_A_points=256),
            initialization_native_calls=copy.deepcopy(entry["calls"]),
            scale=self._snapshot["scale"],
            B2_scale=self._snapshot["B2_scale"],
            target_flux=self._snapshot["target_flux"],
            complete_execution=False,
            arithmetic_consistency=False,
            fine_numerical_qualification=False,
            absolute_field_geometry_pass=False,
            physical_admission=False,
            step4_pass=False,
            sota_advance=False,
            ms1_reached=False,
            resolved_fine_grid_improvement=False,
            pareto_dominance=False,
            realized_field_transfer=False,
        )
        _encode(result)
        return result

    def metadata(self, model):
        with self._operation():
            return self._metadata(self._entry(model))

    def _arrays(self, raw, spec, operation):
        np = self._np
        if spec["kind"] == "diagnostic":
            grid = spec["grid"]
            boundary, inner = grid["nphi"] * grid["ntheta"], 3 * grid["ninner"] ** 2
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
                coil_positions=(4 * self._case["nbase"], grid["ncoil"], 3),
                coil_tangents=(4 * self._case["nbase"], grid["ncoil"], 3),
                coil_currents=(4 * self._case["nbase"],),
            )
        else:
            shape = (operation["ntheta"] * operation.get("nrho", 1), 3)
            shapes = dict(points=shape, A=shape, B=shape)
            shapes["tangents" if operation["form"] == "line" else "weighted_normals"] = shape
        _need(type(raw) is dict and set(raw) == set(shapes), "complete exact fine raw array names")
        arrays = {}
        for name, shape in shapes.items():
            value = raw[name]
            _need(
                type(value) is np.ndarray
                and value.dtype.kind in "iuf"
                and value.shape == shape
                and np.isfinite(value).all(),
                "complete finite fine raw array: " + name,
            )
            arrays[name] = value.copy(order="C")
        if "coil_currents" in arrays:
            expected = np.array([row["current"] for row in self._snapshot["physical"]])
            self._same(arrays["coil_currents"], expected, "frozen physical raw currents")
        return arrays

    def execute(self, model, operation):
        with self._operation():
            entry = self._entry(model)
            spec = entry["spec"]
            self._plan.validate_operation(spec, operation, self._selected)
            _need(
                operation["index"]
                == (
                    spec["level"]["index"] if spec["kind"] == "diagnostic" else entry["operations"]
                ),
                "ordered unrepeated fine operations",
            )
            _need(
                entry["operations"] < (1 if spec["kind"] == "diagnostic" else 9),
                "registered fine operation count exhausted",
            )
            self._metadata(entry)
            model.x = self._selected.copy()
            actual = self._plan._coordinates(self._case, model.x)
            _need(
                actual.tobytes() == self._selected.tobytes(),
                "selected coordinates installed before work",
            )
            model._cache = None
            _need(model._cache is None, "effective fine cache invalidation required")
            start = len(model.native_calls)
            self._dispatch = spec["id"]
            record, raw = _execute(
                model,
                copy.deepcopy(operation),
                (copy.deepcopy(self._snapshot), copy.deepcopy(self._snapshot_ref)),
            )
            self._healthy()
            self._calls(model, start, spec, operation)
            actual = self._plan._coordinates(self._case, model.x)
            _need(
                actual.tobytes() == self._selected.tobytes(),
                "selected coordinates unchanged after work",
            )
            keys = {
                "snapshot",
                "scale",
                "B2_scale",
                "target_flux",
                "metrics" if spec["kind"] == "diagnostic" else "flux",
            }
            _need(
                type(record) is dict and set(record) == keys, "exact frozen fine operation record"
            )
            self._same(
                record["snapshot"], self._snapshot_ref, "original selected snapshot reference"
            )
            for key in ("scale", "B2_scale", "target_flux"):
                self._same(record[key], self._snapshot[key], "frozen operation " + key)
            if spec["kind"] == "diagnostic":
                metrics = record["metrics"]
                metric_names = {
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
                _need(
                    type(metrics) is dict
                    and set(metrics) == metric_names
                    and metrics.get("frozen_scale") is True,
                    "diagnostic uses explicit frozen current scale",
                )
                for key in metric_names - {"frozen_scale", "lengths", "kappa_max"}:
                    self._scalar(metrics[key], "complete fine metric " + key)
                for key in ("lengths", "kappa_max"):
                    _need(
                        type(metrics[key]) is list and len(metrics[key]) == self._case["nbase"],
                        "complete fine geometry metric " + key,
                    )
                    for value in metrics[key]:
                        self._scalar(value, "fine geometry metric " + key)
                for key in ("scale", "B2_scale", "target_flux"):
                    self._same(metrics[key], self._snapshot[key], "frozen metric " + key)
                self._same(
                    metrics["current"],
                    float(1e5 * self._snapshot["scale"]),
                    "no finer current recalibration",
                )
            else:
                self._scalar(record["flux"], "fine flux")
            _encode(record)
            arrays = self._arrays(raw, spec, operation)
            metadata = self._metadata(entry)
            entry["operations"] += 1
            return dict(record=copy.deepcopy(record), arrays=arrays, metadata=metadata)
