"""Injected protected-cell orchestration; no native adapter or launch defaults.

Operation completion is not independent physical admission. The two journals
retain different contracts: ledger work versus unchanged controller events.
"""

import copy
from pathlib import Path

import numpy as np

from fusion_baselines import protected_cell_contract as contract
from fusion_baselines import protected_coil_search as controller
from fusion_baselines.protected_run_ledger import ProtectedRunLedger
from fusion_baselines.protected_search_journal import MAX_RECORDS, _encode
from fusion_baselines.protected_startup import derivative_screen, exact_bundle_replay, points


def _need(condition, message):
    if not condition:
        raise ValueError(message)


class _Cell:
    def __init__(self, context, native_journal, controller_journal, store, adapter, guard):
        self.context = copy.deepcopy(context)
        self.native_journal, self.controller_journal = native_journal, controller_journal
        self.store, self.adapter, self.guard = store, adapter, guard
        self.failed = False
        self.ledger = None
        self.context_ref = None
        self.models, self.certificates, self.bundles, self.checkpoints = [], [], [], []
        self.trial_bundles = {}
        self.pending_trial = None
        self.proposal_count = 0
        self.last_trial = -1
        self.seed = None
        self.ledger = ProtectedRunLedger(record=self.native_record, guard=self.check_guard)

    def healthy(self):
        poisoned = self.failed or (self.ledger is not None and self.ledger.failed)
        poisoned = poisoned or any(
            getattr(owner, "_failed", False) is True
            for owner in (self.store, self.native_journal, self.controller_journal)
        )
        if poisoned:
            self.failed = True
            raise RuntimeError("protected cell failed; no further dispatch or publication")

    def call(self, function, *args, **kwargs):
        """Track errors even when an outer adapter swallows a failing callback."""
        self.healthy()
        try:
            result = function(*args, **kwargs)
            self.healthy()
            return result
        except BaseException:
            self.failed = True
            raise

    def check_guard(self):
        return self.call(self.guard)

    def native_record(self, event):
        self.check_guard()
        return self.call(self.native_journal, copy.deepcopy(event))

    def json(self, name, value):
        self.check_guard()
        return self.call(self.store.json, name, copy.deepcopy(value))

    def arrays(self, name, value):
        self.check_guard()
        return self.call(self.store.arrays, name, copy.deepcopy(value))

    def journals(self):
        result = {}
        for name, journal in (
            ("native", self.native_journal),
            ("controller", self.controller_journal),
        ):
            self.healthy()
            receipt = copy.deepcopy(journal.receipt)
            _need(
                type(receipt) is dict
                and set(receipt) == {"schema_version", "records", "head_sha256"},
                "exact journal receipt",
            )
            _need(
                type(receipt["schema_version"]) is int
                and receipt["schema_version"] == 1
                and type(receipt["records"]) is int
                and 0 <= receipt["records"] <= MAX_RECORDS,
                "typed journal receipt counters",
            )
            head = receipt["head_sha256"]
            _need(
                head is None
                if receipt["records"] == 0
                else (
                    type(head) is str
                    and len(head) == 64
                    and all(c in "0123456789abcdef" for c in head)
                ),
                "journal receipt head must match empty/nonempty prefix",
            )
            _encode(receipt)
            result[name] = dict(directory=str(Path(journal._directory).resolve()), receipt=receipt)
        _need(
            result["native"]["directory"] != result["controller"]["directory"],
            "distinct native and controller journals required",
        )
        self.healthy()
        return result

    def checkpoint(self, phase):
        payload = dict(
            schema_version=1,
            kind="protected-cell-checkpoint",
            phase=phase,
            context=self.context_ref,
            journals=self.journals(),
            counts=self.ledger.counts,
            models=self.models,
            certificates=self.certificates,
            bundles=self.bundles,
            physical_admission=False,
            step4_pass=False,
        )
        reference = self.json(f"checkpoint-{len(self.checkpoints):03d}", payload)
        self.checkpoints.append(reference)
        return reference

    def initialize(self, model_id):
        reference = None

        def factory(callback):
            return self.call(
                self.adapter.initialize, lambda event: self.call(callback, copy.deepcopy(event))
            )

        def validate(model):
            return contract.validate_model(model, self.context)

        def publish(model):
            nonlocal reference
            reference = self.json(
                f"initialize-{model_id}",
                dict(
                    schema_version=1,
                    kind="protected-model-initialization",
                    model_id=model_id,
                    case=self.context["case"],
                    original_seed=self.context["seed_reference"],
                    metadata=contract.model_metadata(model, self.context),
                ),
            )
            return reference

        model = self.call(
            self.ledger.initialize, model_id, factory=factory, validate=validate, publish=publish
        )
        self.models.append(reference)
        self.checkpoint(f"initialize-{model_id}")
        return model

    def certificate(self, phase, index, x):
        x = np.array(x, dtype=float, copy=True)
        digest = contract.coordinate_identity(self.context, x)
        operation_id = f"{phase}/certificate/{index:03d}"
        reference = None

        def compute():
            return self.call(self.adapter.certificate, self.seed.copy(), x.copy())

        def validate(result):
            return controller._certificate(result)["certified"]

        def publish(result):
            nonlocal reference
            reference = self.json(
                operation_id.replace("/", "-"),
                dict(
                    case=self.context["case"],
                    phase=phase,
                    operation_id=operation_id,
                    x=x.tolist(),
                    state_sha256=digest,
                    original_seed=self.context["seed_reference"],
                    geometry_report=self.context["geometry_audit_reference"],
                    geometry_report_index=self.context["geometry_report_index"],
                    result=controller._certificate(result),
                ),
            )
            return reference

        result = self.call(
            self.ledger.certificate,
            phase,
            operation_id,
            digest,
            compute=compute,
            validate=validate,
            publish=publish,
        )
        self.certificates.append(reference)
        return controller._certificate(result), operation_id, reference

    def bundle(self, phase, index, x, certificate_id, certificate_ref):
        x = np.array(x, dtype=float, copy=True)
        digest = contract.coordinate_identity(self.context, x)
        operation_id = f"{phase}/bundle/{index:03d}"
        reference = None

        def compute(model):
            value = self.call(self.adapter.bundle, model, x.copy())
            _need(
                contract.coordinate_identity(self.context, model.x) == digest
                and np.asarray(model.x, dtype=float).tobytes() == x.tobytes(),
                "actual model coordinates must match the requested complete state",
            )
            return value

        def invalidate(model):
            self.call(self.adapter.invalidate, model)
            _need(model._cache is None, "model cache must be invalidated before bundle dispatch")

        def validate(value):
            return contract.validate_bundle(value, x, self.context)

        def publish(value):
            nonlocal reference
            stem = operation_id.replace("/", "-")
            snapshot_ref = self.json(stem + "-snapshot", value["snapshot"])
            arrays_ref = self.arrays(stem + "-arrays", value["arrays"])
            reference = self.json(
                stem,
                dict(
                    case=self.context["case"],
                    phase=phase,
                    operation_id=operation_id,
                    state=value["state"],
                    snapshot=snapshot_ref,
                    arrays=arrays_ref,
                    certificate=certificate_ref,
                ),
            )
            return reference

        value = self.call(
            self.ledger.bundle,
            phase,
            operation_id,
            digest,
            certificate_id=certificate_id,
            invalidate=invalidate,
            compute=compute,
            validate=validate,
            publish=publish,
        )
        self.bundles.append(reference)
        return copy.deepcopy(value), reference

    def evaluated(self, phase, index, x):
        certificate, certificate_id, certificate_ref = self.certificate(phase, index, x)
        _need(
            certificate["certified"] is True,
            "startup/search-seed/replay certificate must be positive",
        )
        result = self.bundle(phase, index, x, certificate_id, certificate_ref)
        self.checkpoint(phase)
        return result

    def record_controller(self, event):
        self.check_guard()
        self.call(self.controller_journal, copy.deepcopy(event))
        if event["event"] == "proposal_attempt":
            trial = event["trial"]
            _need(
                type(trial["index"]) is int and trial["index"] == self.proposal_count,
                "ordered controller proposal index",
            )
            _need(self.pending_trial is None, "previous controller proposal unfinished")
            self.pending_trial = dict(
                index=trial["index"],
                x=copy.deepcopy(trial["x"]),
                certificate=None,
                certificate_id=None,
                certificate_ref=None,
                bundle=None,
            )
            self.proposal_count += 1
        elif event["event"] == "trial_result":
            _need(
                self.pending_trial is not None
                and event["trial"]["index"] == self.pending_trial["index"],
                "controller completion must match pending proposal",
            )
            self.last_trial = self.pending_trial["index"]
            self.pending_trial = None
            self.checkpoint("trial")
        elif event["event"] == "search_complete":
            _need(self.pending_trial is None, "controller completed with unfinished proposal")
            self.checkpoint("search-complete")

    def certify_trial(self, original, x):
        _need(
            np.asarray(original).tobytes() == self.seed.tobytes(),
            "controller certificate must retain the original seed",
        )
        trial = self.pending_trial
        _need(
            trial is not None and trial["certificate"] is None,
            "one certificate per reserved controller proposal",
        )
        _need(
            np.asarray(trial["x"]).tobytes() == np.asarray(x).tobytes(),
            "certificate coordinates must match controller proposal",
        )
        certificate, operation_id, reference = self.certificate("trial", trial["index"], x)
        trial.update(
            certificate=certificate, certificate_id=operation_id, certificate_ref=reference
        )
        # Keep the large raw proof once in its immutable manifest. The frozen
        # controller accepts a complete decision view plus an explicit reference;
        # independent integration verification must dereference and compare it.
        return {
            key: certificate[key] for key in ("status", "calculation_complete", "certified")
        } | {"certificate_reference": copy.deepcopy(reference)}

    def evaluate_trial(self, x):
        trial = self.pending_trial
        _need(
            trial is not None
            and trial["certificate"] is not None
            and trial["certificate"]["certified"] is True
            and trial["bundle"] is None,
            "one field bundle after a positive controller certificate",
        )
        _need(
            np.asarray(trial["x"]).tobytes() == np.asarray(x).tobytes(),
            "field coordinates must match controller proposal",
        )
        value, reference = self.bundle(
            "trial", trial["index"], x, trial["certificate_id"], trial["certificate_ref"]
        )
        trial["bundle"] = reference
        self.trial_bundles[trial["index"]] = (value, reference)
        return copy.deepcopy(value["state"])

    def execute(self):
        self.check_guard()
        _need(contract.validate_context(self.context) is True, "valid complete cell context")
        self.journals()
        _need(
            self.native_journal.receipt["records"] == 0
            and self.controller_journal.receipt["records"] == 0,
            "fresh empty cell journals required",
        )
        case = self.context["case"]
        self.seed = (
            np.asarray(self.context["seed"]["base_coefficients"], dtype=float).ravel().copy()
        )
        self.context_ref = self.json("context", contract.context_metadata(self.context))
        self.initialize("main")
        startup = []
        for index, x in enumerate(points(self.seed, case["nbase"], case["order"])):
            value, reference = self.evaluated("startup", index, x)
            startup.append((value, reference))
            if index == 0:
                exact_bundle_replay(value, self.context["historical_seed"])
        exact_bundle_replay(startup[-1][0], startup[0][0])
        screen = derivative_screen(
            self.seed, case["nbase"], case["order"], [value["state"] for value, _ in startup]
        )
        _need(screen["startup_screen_pass"] is True, "recorded startup screen failed")
        screen_ref = self.json("startup-screen", screen)
        initial, initial_ref = self.evaluated("search-seed", 0, self.seed)
        exact_bundle_replay(initial, startup[0][0])
        report = self.call(
            controller.search,
            self.seed.copy(),
            copy.deepcopy(initial["state"]),
            lambda original, x: self.call(self.certify_trial, original, x),
            lambda x: self.call(self.evaluate_trial, x),
            lambda event: self.call(self.record_controller, event),
        )
        report_ref = self.json("search-report", report)
        index = report["selected_index"]
        if index is None:
            selected, selected_ref = initial, initial_ref
        else:
            _need(
                type(index) is int
                and index in report["accepted_indices"]
                and report["trials"][index]["accepted"] is True
                and index in self.trial_bundles,
                "selected index must be an accepted field trial",
            )
            selected, selected_ref = self.trial_bundles[index]
        _need(
            _encode(report["selected"]) == _encode(selected["state"]),
            "controller selection must equal the linked complete bundle state",
        )
        self.initialize("replay")
        replay, replay_ref = self.evaluated("replay", 0, selected["state"]["x"])
        equality = exact_bundle_replay(replay, selected)
        result = dict(
            schema_version=1,
            kind="protected-cell-execution",
            producer_complete=True,
            case=case,
            context=self.context_ref,
            journals=self.journals(),
            counts=self.ledger.counts,
            models=self.models,
            certificates=self.certificates,
            bundles=self.bundles,
            checkpoints=self.checkpoints,
            startup_screen=screen_ref,
            search_report=report_ref,
            selected_bundle=selected_ref,
            replay_bundle=replay_ref,
            selected_replay=equality,
            independent_audit_pass=False,
            physical_admission=False,
            step4_pass=False,
        )
        # Terminal publication is the commit boundary: no fallible resource
        # check follows it. Only the successfully returned reference is an
        # acknowledged result; a discovered file after failed fsync is not one.
        return self.json("result", result)


def run_cell(context, *, native_journal, controller_journal, store, adapter, guard):
    """Execute one injected cell, returning its immutable final manifest reference.

    Every exception terminates the cell; partial files and completed journal
    prefixes remain. No resume, retry, physical admission or native default.
    """
    cell = _Cell(context, native_journal, controller_journal, store, adapter, guard)
    try:
        return cell.execute()
    except BaseException:
        cell.failed = True
        raise
