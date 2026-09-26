"""Explicit native bridge for an already admitted context; no import-time native work.

This adapter has no command-line entry point. The qualified cell and supervisor
own work reservations and resource guards. Tests replace the three lazy bridges.
"""

import copy
from contextlib import contextmanager

import numpy as np
from protected_native_inputs import build_context

from fusion_baselines import protected_cell_contract as contract
from fusion_baselines.protected_coil_search import _certificate, _json
from fusion_baselines.protected_startup import exact_bundle_replay


def _make_model(source, case, spec, geometry, callback):
    from run_clear_coil_field_start import make_model

    return make_model(source, case, spec, geometry, callback)


def _execute(model, operation):
    from run_clear_coil_field_start import execute

    return execute(model, operation, None)


def _certify(seed, report, candidate):
    from fusion_baselines.coil_perturbation import candidate_certificate

    return candidate_certificate(seed, report, candidate)


class NativeAdapter:
    def __init__(self, context, source_manifest):
        expected = build_context(source_manifest, context["case"])
        contract.validate_context(context)
        contract._same(
            contract.context_metadata(context),
            contract.context_metadata(expected),
            "adapter source-bound context",
        )
        exact_bundle_replay(context["historical_seed"], expected["historical_seed"])
        self._context, self._source = copy.deepcopy(expected), copy.deepcopy(source_manifest)
        self._models, self._failed, self._busy = [], False, False

    @contextmanager
    def _operation(self):
        try:
            if self._failed:
                raise RuntimeError("native adapter failed; no retry")
            contract._need(not self._busy, "reentrant native adapter operation")
            self._busy = True
            yield
            if self._failed:
                raise RuntimeError("native adapter callback failed; no retry")
        except BaseException:
            self._failed = True
            raise
        finally:
            self._busy = False

    def _fixed_model(self, model):
        contract._need(any(model is old for old in self._models), "adapter-owned model required")
        context, seed = self._context, self._context["seed"]
        anchor = context["historical_seed"]["snapshot"]
        expected = dict(
            names=seed["names"],
            _seed_geometry=seed,
            method=context["case"]["method"],
            nbase=seed["nbase"],
            order=seed["order"],
            nfp=2,
            initialization_work=contract.INITIALIZATION,
            **{
                key: contract.CONSTRUCTION[key]
                for key in ("ncoil", "nphi", "ntheta", "ninner", "offset")
            },
        )
        for key, value in expected.items():
            contract._same(getattr(model, key), value, "adapter fixed model " + key)
        for key in ("B2_scale", "target_flux", "seed_unit_flux"):
            value = getattr(model, key)
            contract._need(type(value) in (int, float, np.float64), "real fixed model " + key)
            contract._same(float(value), anchor[key], "adapter fixed model " + key)
        contract._same(model.target["sources"], context["target_sources"], "adapter fixed sources")
        actual = contract._coordinates(context, model.seed_x)
        original = np.asarray(seed["base_coefficients"], dtype=float).ravel()
        contract._need(actual.tobytes() == original.tobytes(), "unchanged original model seed")

    def initialize(self, callback):
        with self._operation():
            contract._need(callable(callback), "native event callback required")
            contract._need(len(self._models) < 2, "only original main and replay models")
            context = self._context

            def receive(event):
                try:
                    if self._failed:
                        raise RuntimeError("native adapter callback failed; no further events")
                    callback(copy.deepcopy(event))
                except BaseException:
                    self._failed = True
                    raise

            spec = dict(
                method=context["case"]["method"],
                grid=dict(ncoil=256, nphi=64, ntheta=64, ninner=32, offset=0),
            )
            model = _make_model(
                copy.deepcopy(self._source["cell_sources"]),
                copy.deepcopy(context["case"]),
                spec,
                copy.deepcopy(context["seed"]),
                receive,
            )
            contract._need(all(model is not old for old in self._models), "distinct fresh model")
            contract.validate_model(model, context)
            self._models.append(model)
            return model

    def certificate(self, original_seed, x):
        with self._operation():
            context, seed = self._context, self._context["seed"]
            supplied = contract._coordinates(context, original_seed)
            expected = np.asarray(seed["base_coefficients"], dtype=float).ravel()
            contract._need(
                supplied.tobytes() == expected.tobytes(), "original seed, not prior trial"
            )
            candidate = contract._coordinates(context, x)
            result = _certify(
                copy.deepcopy(seed),
                copy.deepcopy(context["geometry_report"]),
                candidate.reshape(seed["nbase"], 3, 2 * seed["order"] + 1).copy(),
            )
            return _certificate(result)

    def invalidate(self, model):
        with self._operation():
            self._fixed_model(model)
            model._cache = None
            contract._need(model._cache is None, "effective native cache invalidation required")

    def bundle(self, model, x):
        with self._operation():
            self._fixed_model(model)
            contract._need(model._cache is None, "invalidate before every native full bundle")
            candidate = contract._coordinates(self._context, x)
            record, arrays = _execute(model, dict(kind="qualification", x=candidate.copy()))
            contract._need(
                type(record) is dict
                and set(record) == {"J", "gradient", "metrics", "snapshot_data"},
                "exact legacy full bundle result",
            )
            result = dict(
                state=_json(
                    dict(
                        x=candidate,
                        value=record["J"],
                        gradient=record["gradient"],
                        metrics=record["metrics"],
                    )
                ),
                snapshot=_json(record["snapshot_data"]),
                arrays=copy.deepcopy(arrays),
            )
            contract.validate_bundle(result, candidate, self._context)
            actual = contract._coordinates(self._context, model.x)
            contract._need(actual.tobytes() == candidate.tobytes(), "native requested coordinates")
            return result
