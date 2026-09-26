"""Injected fixed-candidate fine orchestration, without launch authorization.

The independently admitted context, adapter and geometry bridge are supplied by
the qualified worker. Raw publication and exact work completion do not establish
physical truth: all scientific flags remain false for the saved-data auditor.
"""

import copy
from pathlib import Path

from fusion_baselines import protected_cell_contract as original_contract
from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_fine_geometry_codec import encode_geometry
from fusion_baselines.protected_fine_ledger import FineLedger
from fusion_baselines.protected_fine_process import SCOPE
from fusion_baselines.protected_run_ledger import _reference
from fusion_baselines.protected_search_journal import _encode


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, message):
    _need(_encode(actual) == _encode(expected), message)


def context_metadata(context):
    """Validate supplied coarse schemas and serialize identity, without I/O admission."""
    _need(type(context) is dict and set(context) == {
        "case", "original_context", "coarse", "selected",
    }, "exact fine context required")
    plan.validate_case(context["case"])
    original = context["original_context"]
    original_contract.validate_context(original)
    _same(original["case"], context["case"], "same original and fine case required")
    coarse = context["coarse"]
    _need(type(coarse) is dict and set(coarse) == {
        "case_record", "parent_acknowledgement", "cell_result", "independent_reconstruction",
        "selected_bundle", "selected_snapshot", "selected_certificate",
    }, "complete coarse references required")
    for reference in coarse.values():
        _reference(reference)
    selected = context["selected"]
    _need(type(selected) is dict and set(selected) == {
        "state", "snapshot", "arrays", "certificate",
    }, "complete selected coarse state required")
    x = plan._coordinates(context["case"], selected["state"]["x"])
    original_contract.validate_bundle(
        {key: selected[key] for key in ("state", "snapshot", "arrays")}, x, original
    )
    _need(selected["certificate"]["result"]["certified"] is True,
          "selected positive cumulative certificate required")
    result = dict(
        case=copy.deepcopy(context["case"]),
        original_context=original_contract.context_metadata(original),
        coarse=copy.deepcopy(coarse),
        selected={key: copy.deepcopy(selected[key])
                  for key in ("state", "snapshot", "certificate")},
    )
    _encode(result)
    return result


def _difference(after, before):
    _need(type(after) is dict and type(before) is dict and set(after) == set(before),
          "identical fine work-counter keys required")
    result = {}
    for key in after:
        if type(after[key]) is dict:
            result[key] = _difference(after[key], before[key])
        else:
            _need(type(after[key]) is type(before[key]) is int
                  and 0 <= before[key] <= after[key], "forward integer fine work counters")
            result[key] = after[key] - before[key]
    return result


def _geometry_budget(case, level):
    physical, nodes = 4 * case["nbase"], level["ncoil"]
    pairs = physical * (physical - 1) // 2
    return {
        key: dict(attempted=n, completed=n, points_attempted=p, points_completed=p)
        for key, n, p in (("fourier", 3, 3 * physical * nodes),
                          ("cp", 2, 2 * physical * nodes),
                          ("cc", pairs, pairs * nodes))
    }


class _FineCell:
    def __init__(self, context, source_reference, *, adapter, geometry, store, journal, guard):
        self.context = copy.deepcopy(context)
        self.metadata = context_metadata(self.context)
        self.source = _reference(source_reference)
        self.case = self.context["case"]
        self.x = plan._coordinates(self.case, self.context["selected"]["state"]["x"])
        self.adapter, self.geometry, self.store, self.journal = adapter, geometry, store, journal
        _need(callable(guard), "fine guard callback required")
        self.guard, self.failed, self.checking = guard, False, False
        self.ledger = None
        self.ledger = FineLedger(self.case, self.x, record=self.record, guard=self.check)
        self.initializations, self.operations, self.grids = [], [], []

    def healthy(self):
        owners = (self.adapter, self.geometry, self.store, self.journal, self.ledger)
        if self.failed or any(getattr(owner, key, False) is True
                              for owner in owners for key in ("_failed", "failed")):
            self.failed = True
            raise RuntimeError("fine cell failed; no further work or acknowledged result")

    def call(self, function, *args, **kwargs):
        self.healthy()
        try:
            result = function(*args, **kwargs)
            self.healthy()
            return result
        except BaseException:
            self.failed = True
            raise

    def check(self):
        entered = False
        try:
            self.healthy()
            _need(not self.checking, "reentrant fine cell guard")
            self.checking = entered = True
            self.call(self.guard)
        except BaseException:
            self.failed = True
            raise
        finally:
            if entered:
                self.checking = False

    def record(self, row):
        self.check()
        self.call(self.journal, copy.deepcopy(row))
        self.check()

    def json(self, name, value):
        self.check()
        ref = self.call(self.store.json, name, copy.deepcopy(value))
        self.check()
        return _reference(ref)

    def arrays(self, name, values):
        self.check()
        ref = self.call(self.store.arrays, name, copy.deepcopy(values))
        self.check()
        return _reference(ref)

    def initialize(self, spec):
        reference = metadata = None

        def factory(callback):
            return self.call(self.adapter.initialize, copy.deepcopy(spec),
                             lambda event: self.call(callback, copy.deepcopy(event)))

        def validate(model):
            nonlocal metadata
            metadata = self.call(self.adapter.metadata, model)
            _same(metadata["case"], self.case, "initialized fine case")
            _same(metadata["spec"], spec, "initialized exact fine model")
            _same(metadata["coarse"], self.context["coarse"], "initialized coarse selection")
            _same(metadata["selected_x"], self.x.tolist(), "initialized selected coordinates")
            for key in ("complete_execution", *SCOPE):
                _need(metadata[key] is False, "initializer cannot assert " + key)
            _encode(metadata)
            return True

        def publish(model):
            nonlocal reference
            reference = self.json(
                "initialize-" + spec["id"],
                dict(schema_version=1, kind="protected-fine-initialization", case=self.case,
                     spec=spec, metadata=metadata),
            )
            return reference

        model = self.call(self.ledger.initialize, copy.deepcopy(spec), factory=factory,
                          validate=validate, publish=publish)
        self.initializations.append(reference)
        return model, copy.deepcopy(metadata)

    def execute(self, model, spec, operation, initialized):
        reference = None

        def validate(result):
            _need(type(result) is dict and set(result) == {"record", "arrays", "metadata"},
                  "complete fine bridge result required")
            _same(result["metadata"], initialized, "immutable initialized model metadata")
            record = result["record"]
            _need(type(record) is dict and set(record) == {
                "snapshot", "scale", "B2_scale", "target_flux",
                "metrics" if spec["kind"] == "diagnostic" else "flux",
            }, "exact fixed-current fine numerical record")
            _same(record["snapshot"], self.context["coarse"]["selected_snapshot"],
                  "unchanged selected coarse snapshot")
            for key in ("scale", "B2_scale", "target_flux"):
                _same(record[key], self.context["selected"]["snapshot"][key],
                      "unchanged fine normalization " + key)
            _encode(record)
            return True

        def publish(result):
            nonlocal reference
            identity = operation["operation_id"]
            raw = self.arrays(identity + "-arrays", result["arrays"])
            descriptor = {key: value for key, value in operation.items() if key != "x"}
            reference = self.json(
                identity,
                dict(schema_version=1, kind="protected-fine-operation", status="completed",
                     case=self.case, spec=spec, operation=descriptor, arrays=raw,
                     record=result["record"], initialization=self.initializations[-1]),
            )
            return reference

        self.call(self.ledger.execute, model, copy.deepcopy(spec), copy.deepcopy(operation),
                  compute=lambda m: self.call(self.adapter.execute, m, copy.deepcopy(operation)),
                  validate=validate, publish=publish)
        self.operations.append(reference)

    def sample_geometry(self):
        coefficients = self.x.reshape(self.case["nbase"], 3, 2 * self.case["order"] + 1)
        for index, level in enumerate(plan.geometry_levels()):
            self.check()
            before = self.call(self.geometry.work)
            raw = self.call(self.geometry.sample, coefficients.copy(), copy.deepcopy(level))
            after = self.call(self.geometry.work)
            work = _difference(after["sampling"], before["sampling"])
            _same(work, _geometry_budget(self.case, level), "exact direct fine geometry work")
            arrays, descriptor = encode_geometry(raw, self.case, level)
            reference = self.arrays(f"geometry-{index}-arrays", arrays)
            row = dict(level=level, arrays=reference, codec=descriptor, sampling_work=work)
            self.grids.append(self.json(
                f"geometry-{index}",
                dict(schema_version=1, kind="protected-fine-geometry", case=self.case, record=row),
            ))

    def run(self):
        context_ref = self.json("context", self.metadata)
        for spec in plan.model_plan(self.case):
            model, metadata = self.initialize(spec)
            for operation in plan.operation_plan(spec, self.x):
                self.execute(model, spec, operation, metadata)
        counts = self.call(self.ledger.finish)
        self.sample_geometry()
        work = self.call(self.geometry.work)
        _same(work["surfaces"], dict(attempted=2, completed=2), "both full-torus target surfaces")
        _same(work["direct_grids"], dict(attempted=4, completed=4), "all four geometry grids")
        receipt = copy.deepcopy(self.journal.receipt)
        _need(receipt["records"] == 225, "complete fine ledger journal required")
        result = dict(
            schema_version=1, kind="protected-fine-cell-execution", case=self.case,
            source=self.source, context=context_ref, initializations=self.initializations,
            operations=self.operations, geometry=self.grids, counts=counts,
            geometry_work=work,
            journal=dict(directory=str(Path(self.journal._directory).resolve()), receipt=receipt),
            producer_complete=True, complete_execution=False, **SCOPE,
        )
        return self.json("result", result)


def run_fine_cell(context, source_reference, *, adapter, geometry, store, journal, guard):
    """Return only the explicitly published core reference; no retries or file discovery."""
    cell = _FineCell(context, source_reference, adapter=adapter, geometry=geometry,
                     store=store, journal=journal, guard=guard)
    return cell.call(cell.run)
