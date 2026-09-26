"""Read-only completed-cell linkage and accounting audit, not a physical verifier.

Does not call the cell producer, search controller or ledger. Reuses qualified
storage readers and structural/replay helpers (some import controller primitives);
controller arithmetic is checked
by its separately authored scalar auditor. The caller supplies an admitted
historical context. Matching its labels is not new source authentication.
"""

import copy
import hashlib
import math
import zipfile

from fusion_baselines import protected_cell_contract as contract
from fusion_baselines.protected_coil_search_audit import audit as audit_controller
from fusion_baselines.protected_run_snapshots import read_arrays, read_json
from fusion_baselines.protected_search_journal import _encode, read_events
from fusion_baselines.protected_startup import derivative_screen, exact_bundle_replay, points

SCOPE = dict(
    field_values_verified=False,
    gradients_verified=False,
    geometry_certificates_verified=False,
    source_admission_verified=False,
    physical_admission=False,
    step4_pass=False,
)
CALLS = (
    ("boundary", "B", 4096),
    ("inner", "B", 3072),
    ("loop", "A", 256),
    ("boundary", "B_vjp", 4096),
    ("inner", "B_vjp", 3072),
    ("loop", "A_vjp", 256),
    ("boundary", "A", 4096),
    ("inner", "A", 3072),
    ("loop", "B", 256),
)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, label):
    _need(_encode(actual) == _encode(expected), "cell audit identity: " + label)


def _clock(value):
    _need(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "finite nonnegative native clock",
    )


def _receipt_prefixes(events):
    receipts = [dict(schema_version=1, records=0, head_sha256=None)]
    for index, event in enumerate(events):
        encoded = _encode(
            dict(
                schema_version=1,
                index=index,
                previous_sha256=receipts[-1]["head_sha256"],
                payload=event,
            )
        )
        receipts.append(
            dict(
                schema_version=1, records=index + 1, head_sha256=hashlib.sha256(encoded).hexdigest()
            )
        )
    return receipts


class _Audit:
    def __init__(self, result, context):
        self.result, self.context = result, context
        self.native = read_events(**result["journals"]["native"])
        self.controller = read_events(**result["journals"]["controller"])
        _need(
            result["journals"]["native"]["directory"]
            != result["journals"]["controller"]["directory"],
            "separate journal directories",
        )
        self.prefixes = {
            "native": _receipt_prefixes(self.native),
            "controller": _receipt_prefixes(self.controller),
        }
        self.position = 0
        self.indices = dict(main=0, replay=0)
        self.clocks = dict(main=0.0, replay=0.0)
        self.counts = dict(
            initialization={k: dict(attempted=0, completed=0) for k in ("main", "replay")},
            certificate={
                k: dict(attempted=0, completed=0)
                for k in ("startup", "search-seed", "trial", "replay")
            },
            bundle={
                k: dict(attempted=0, completed=0)
                for k in ("startup", "search-seed", "trial", "replay")
            },
            native=dict(attempted=0, completed=0),
        )
        self.refs = dict(models=[], certificates=[], bundles=[])
        self.checkpoint_index = 0
        self.used_paths = set()

    def take(self, expected):
        _need(self.position < len(self.native), "missing native ledger event")
        event = self.native[self.position]
        _same(event, expected, f"ledger event {self.position}")
        self.position += 1

    def next_ref(self, collection):
        index = len(self.refs[collection])
        _need(index < len(self.result[collection]), "missing operation manifest")
        reference = self.result[collection][index]
        path = reference["path"]
        _need(path not in self.used_paths, "operation manifest must not be reused")
        self.used_paths.add(path)
        self.refs[collection].append(reference)
        return reference, read_json(reference)

    def operation(self, operation, reference, *, certified=None, calls=()):
        kind, phase = operation["kind"], operation["phase"]
        self.take(dict(event="operation-attempted", **operation))
        self.counts[kind][phase]["attempted"] += 1
        model = operation.get("model_id")
        for field, quantity, size in calls:
            _need(self.position < len(self.native), "missing native request")
            attempt = self.native[self.position]["native"]
            start = attempt["started_monotonic"]
            _clock(start)
            _need(start >= self.clocks[model], "native clock moved backwards")
            base = dict(
                index=self.indices[model],
                field=field,
                quantity=quantity,
                points=size,
                started_monotonic=start,
            )
            self.take(
                dict(
                    event="native-attempted",
                    **operation,
                    native=dict(
                        **base, status="attempted", native_started=False, native_completed=False
                    ),
                )
            )
            self.counts["native"]["attempted"] += 1
            _need(self.position < len(self.native), "missing native outcome")
            stop = self.native[self.position]["native"]["completed_monotonic"]
            _clock(stop)
            _need(stop >= start, "native outcome precedes request")
            self.take(
                dict(
                    event="native-completed",
                    **operation,
                    native=dict(
                        **base,
                        status="completed",
                        native_started=True,
                        native_completed=True,
                        completed_monotonic=stop,
                    ),
                )
            )
            self.counts["native"]["completed"] += 1
            self.indices[model] += 1
            self.clocks[model] = stop
        extra = {} if kind != "certificate" else dict(certified=certified)
        self.take(dict(event="operation-completed", **operation, raw_reference=reference, **extra))
        self.counts[kind][phase]["completed"] += 1

    def checkpoint(self, phase, controller_count):
        _need(self.checkpoint_index < len(self.result["checkpoints"]), "missing checkpoint")
        reference = self.result["checkpoints"][self.checkpoint_index]
        _need(reference["path"] not in self.used_paths, "checkpoint must not be reused")
        self.used_paths.add(reference["path"])
        actual = read_json(reference)
        journals = {
            key: dict(
                directory=value["directory"],
                receipt=self.prefixes[key][self.position if key == "native" else controller_count],
            )
            for key, value in self.result["journals"].items()
        }
        expected = dict(
            schema_version=1,
            kind="protected-cell-checkpoint",
            phase=phase,
            context=self.result["context"],
            journals=journals,
            counts=self.counts,
            **self.refs,
            physical_admission=False,
            step4_pass=False,
        )
        _same(actual, expected, "checkpoint complete prefix")
        self.checkpoint_index += 1

    def initialize(self, model):
        reference, record = self.next_ref("models")
        context, anchor = self.context, self.context["historical_seed"]["snapshot"]
        metadata = dict(
            seed_x=context["historical_seed"]["state"]["x"],
            names=context["seed"]["names"],
            seed_geometry=context["seed"],
            method=context["case"]["method"],
            **{k: anchor[k] for k in ("B2_scale", "target_flux", "seed_unit_flux")},
            initialization_work=contract.INITIALIZATION,
            construction=contract.CONSTRUCTION,
            sources=context["target_sources"],
        )
        _same(
            record,
            dict(
                schema_version=1,
                kind="protected-model-initialization",
                model_id=model,
                case=context["case"],
                original_seed=context["seed_reference"],
                metadata=metadata,
            ),
            "model initialization manifest",
        )
        self.operation(
            dict(
                kind="initialization",
                phase=model,
                operation_id=f"initialize/{model}",
                model_id=model,
            ),
            reference,
            calls=(("loop", "A", 256),),
        )

    def certificate(self, phase, index, x):
        reference, record = self.next_ref("certificates")
        context = self.context
        certificate = record["result"]
        _need(
            type(certificate) is dict
            and type(certificate["certified"]) is bool
            and type(certificate["calculation_complete"]) is bool,
            "typed full certificate decision",
        )
        positive = certificate["certified"]
        _need(
            certificate["status"] == ("certified" if positive else "uncertified")
            and (not positive or certificate["calculation_complete"]),
            "consistent full certificate decision",
        )
        operation_id = f"{phase}/certificate/{index:03d}"
        digest = contract.coordinate_identity(context, x)
        _same(
            record,
            dict(
                case=context["case"],
                phase=phase,
                operation_id=operation_id,
                x=list(x),
                state_sha256=digest,
                original_seed=context["seed_reference"],
                geometry_report=context["geometry_audit_reference"],
                geometry_report_index=context["geometry_report_index"],
                result=certificate,
            ),
            "certificate provenance",
        )
        self.operation(
            dict(kind="certificate", phase=phase, operation_id=operation_id, state_sha256=digest),
            reference,
            certified=positive,
        )
        return reference, certificate

    def bundle(self, phase, index, x, certificate_ref):
        reference, record = self.next_ref("bundles")
        _same(
            set_as_list(record),
            sorted(("case", "phase", "operation_id", "state", "snapshot", "arrays", "certificate")),
            "bundle keys",
        )
        _same(record["case"], self.context["case"], "bundle case")
        _same(record["phase"], phase, "bundle phase")
        operation_id = f"{phase}/bundle/{index:03d}"
        _same(record["operation_id"], operation_id, "bundle operation")
        _same(record["certificate"], certificate_ref, "bundle certificate reference")
        bundle = dict(
            state=record["state"],
            snapshot=read_json(record["snapshot"]),
            arrays=read_arrays(record["arrays"]),
        )
        contract.validate_bundle(bundle, x, self.context)
        self.operation(
            dict(
                kind="bundle",
                phase=phase,
                operation_id=operation_id,
                state_sha256=contract.coordinate_identity(self.context, x),
                certificate_id=f"{phase}/certificate/{index:03d}",
                model_id="replay" if phase == "replay" else "main",
            ),
            reference,
            calls=CALLS,
        )
        return reference, bundle

    def evaluated(self, phase, index, x):
        reference, certificate = self.certificate(phase, index, x)
        _need(certificate["certified"] is True, "startup/search-seed/replay must be certified")
        return self.bundle(phase, index, x, reference)

    def run(self):
        seed = self.context["historical_seed"]["state"]["x"]
        self.initialize("main")
        self.checkpoint("initialize-main", 0)
        case = self.context["case"]
        startup = []
        for index, x in enumerate(points(seed, case["nbase"], case["order"])):
            reference, bundle = self.evaluated("startup", index, x.tolist())
            startup.append(bundle)
            self.checkpoint("startup", 0)
        exact_bundle_replay(startup[0], self.context["historical_seed"])
        exact_bundle_replay(startup[-1], startup[0])
        screen = derivative_screen(
            seed, case["nbase"], case["order"], [b["state"] for b in startup]
        )
        _need(screen["startup_screen_pass"] is True, "recorded startup derivative screen")
        _same(read_json(self.result["startup_screen"]), screen, "startup screen report")
        selected_ref, initial = self.evaluated("search-seed", 0, seed)
        selected = initial
        self.checkpoint("search-seed", 0)
        exact_bundle_replay(initial, startup[0])
        report = read_json(self.result["search_report"])
        control = audit_controller(seed, initial["state"], report, self.controller)
        _need(
            control["control_flow_pass"] is True,
            "independent controller audit: " + control.get("error", ""),
        )
        trial_event_counts = [
            i + 1 for i, e in enumerate(self.controller) if e["event"] == "trial_result"
        ]
        for index, trial in enumerate(report["trials"]):
            cert_ref, certificate = self.certificate("trial", index, trial["x"])
            view = {k: certificate[k] for k in ("status", "calculation_complete", "certified")}
            view["certificate_reference"] = cert_ref
            _same(trial["certificate"], view, "compact decision/full certificate linkage")
            if certificate["certified"]:
                reference, bundle = self.bundle("trial", index, trial["x"], cert_ref)
                _same(bundle["state"], trial["evaluation"], "trial state linkage")
                if report["selected_index"] == index:
                    selected_ref, selected = reference, bundle
            self.checkpoint("trial", trial_event_counts[index])
        self.checkpoint("search-complete", len(self.controller))
        self.initialize("replay")
        self.checkpoint("initialize-replay", len(self.controller))
        replay_ref, replay = self.evaluated("replay", 0, selected["state"]["x"])
        self.checkpoint("replay", len(self.controller))
        equality = exact_bundle_replay(replay, selected)
        _same(self.result["selected_replay"], equality, "full numerical replay")
        _same(self.result["selected_bundle"], selected_ref, "selected bundle linkage")
        _same(report["selected"], selected["state"], "selected controller state")
        _same(self.result["replay_bundle"], replay_ref, "replay bundle linkage")
        _same(self.result["counts"], self.counts, "final reconstructed ledger counts")
        for key, refs in self.refs.items():
            _same(self.result[key], refs, "complete manifest list " + key)
        _need(self.position == len(self.native), "unexpected native tail")
        _need(self.checkpoint_index == len(self.result["checkpoints"]), "unexpected checkpoints")
        _need(self.counts["native"]["completed"] <= 290, "native request budget")
        return dict(
            control_flow_pass=True,
            counts=copy.deepcopy(self.counts),
            trial_certificates=len(report["trials"]),
            complete_bundles=len(self.refs["bundles"]),
            checkpoint_prefixes=self.checkpoint_index,
            selected_index=report["selected_index"],
            reason=report["reason"],
        )


def set_as_list(value):
    _need(type(value) is dict, "JSON dictionary required")
    return sorted(value)


def audit_cell(result_reference, context):
    """Verify a supplied completed graph; no guessed journal heads or native work."""
    try:
        contract.validate_context(context)
        result = read_json(result_reference)
        _same(
            set_as_list(result),
            sorted(
                (
                    "schema_version",
                    "kind",
                    "producer_complete",
                    "case",
                    "context",
                    "journals",
                    "counts",
                    "models",
                    "certificates",
                    "bundles",
                    "checkpoints",
                    "startup_screen",
                    "search_report",
                    "selected_bundle",
                    "replay_bundle",
                    "selected_replay",
                    "independent_audit_pass",
                    "physical_admission",
                    "step4_pass",
                )
            ),
            "result keys",
        )
        for key, value in dict(
            schema_version=1,
            kind="protected-cell-execution",
            producer_complete=True,
            independent_audit_pass=False,
            physical_admission=False,
            step4_pass=False,
            case=context["case"],
        ).items():
            _same(result[key], value, "result " + key)
        _same(set_as_list(result["journals"]), ["controller", "native"], "journal keys")
        _same(
            read_json(result["context"]),
            contract.context_metadata(context),
            "supplied historical context binding",
        )
        details = _Audit(result, context).run()
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        OverflowError,
        RecursionError,
        OSError,
        AttributeError,
        zipfile.BadZipFile,
    ) as error:
        return dict(integration_integrity_pass=False, error=str(error), **SCOPE)
    return dict(integration_integrity_pass=True, **details, **SCOPE)
