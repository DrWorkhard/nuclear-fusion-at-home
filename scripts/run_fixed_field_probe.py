"""Registered two-pair value-only study, gated by committed qualification.

No resume, candidate choice, optimizer or native retry. Workers explicitly return
hash-bound prefixes through a bounded pipe; saved files alone acknowledge nothing.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from fusion_baselines.fixed_field_probe_control import (
    LEVELS,
    PAIR_BYTES,
    PHASE_SECONDS,
    SCOPE,
    START_FREE,
    THREADS,
    Guard,
    PayloadBudget,
    Work,
    need,
    reference,
    same,
    send,
    supervise,
)
from fusion_baselines.protected_search_journal import _encode

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = "evidence/fixed-field-probe-registration-v1.json"
_ACTIVE = False


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.DEVNULL, timeout=30
    )


def source_snapshot(root=ROOT, *, guard=lambda: None):
    guard()
    paths = git(root, "ls-files", "--", "*.py", "pyproject.toml", "uv.lock").decode().splitlines()
    need(paths and len(paths) == len(set(paths)), "nonempty complete tracked Python source list")
    paths += [
        REGISTRATION,
        "evidence/fixed-field-probe-inputs-v1.json",
        "docs/optimization/FIXED_FIELD_PROBE_PROTOCOL.md",
    ]
    refs = []
    for path in sorted(paths):
        guard()
        refs.append(reference(Path(root) / path))
    guard()
    return dict(commit=git(root, "rev-parse", "HEAD").decode().strip(), sources=refs)


def execution_gate(checkpoint, root=ROOT, *, guard=lambda: None):
    from fusion_baselines.protected_run_snapshots import read_json

    guard()
    need(
        not git(root, "status", "--porcelain", "--untracked-files=all").strip(),
        "clean tracked/untracked worktree required for real probe",
    )
    checkpoint_data = read_json(checkpoint)
    need(
        checkpoint_data.get("kind") == "fixed-field-probe-execution-checkpoint"
        and checkpoint_data.get("execution_allowed") is True
        and type(checkpoint_data.get("schema_version")) is int
        and checkpoint_data.get("schema_version") == 1,
        "separate execution checkpoint",
    )
    qualification = read_json(checkpoint_data["qualification"])
    need(
        qualification.get("kind") == "fixed-field-probe-implementation-qualification"
        and qualification.get("status") == "completed"
        and type(qualification.get("schema_version")) is int
        and qualification.get("schema_version") == 1,
        "completed implementation qualification",
    )
    same(
        qualification.get("checks"),
        dict.fromkeys(("focused", "public", "docs", "full_regression", "independent_review"), True),
        "all required actual qualification checks",
    )
    for document in (checkpoint_data, qualification):
        same({key: document.get(key) for key in SCOPE}, SCOPE, "diagnostic-only scope")
    for key in ("sources", "implementation_commit", "registration"):
        same(checkpoint_data[key], qualification[key], "qualified " + key)
    current = source_snapshot(root, guard=guard)
    same(current["sources"], checkpoint_data["sources"], "unchanged complete source closure")
    same(checkpoint_data["registration"], reference(Path(root) / REGISTRATION), "registration")
    implementation = checkpoint_data["implementation_commit"]
    need(type(implementation) is str and len(implementation) == 40, "full implementation commit")
    git(root, "merge-base", "--is-ancestor", implementation, "HEAD")
    for ref in (checkpoint, checkpoint_data["qualification"]):
        path = Path(ref["path"]).relative_to(Path(root).resolve()).as_posix()
        need(
            hashlib.sha256(git(root, "show", "HEAD:" + path)).hexdigest() == ref["sha256"],
            "checkpoint and qualification committed",
        )
    for ref in current["sources"]:
        guard()
        path = Path(ref["path"]).relative_to(Path(root).resolve()).as_posix()
        need(
            hashlib.sha256(git(root, "show", implementation + ":" + path)).hexdigest()
            == ref["sha256"],
            "source content at qualified implementation commit",
        )
    need(
        type(qualification.get("artifacts")) is list and len(qualification["artifacts"]) >= 5,
        "retained qualification evidence",
    )
    roles = qualification.get("evidence")
    need(
        type(roles) is dict and set(roles) == set(qualification["checks"]),
        "five named qualification evidence roles",
    )
    need(
        len({ref["path"] for ref in qualification["artifacts"]}) == len(qualification["artifacts"]),
        "distinct qualification references",
    )
    need(
        len({ref["path"] for ref in roles.values()}) == 5
        and all(ref in qualification["artifacts"] for ref in roles.values()),
        "distinct retained required qualification artifacts",
    )
    for ref in qualification["artifacts"]:
        guard()
        same(reference(ref["path"]), ref, "qualification artifact")
    guard()
    return current


class Writer:
    """Precharged writes through the existing exclusive canonical store."""

    def __init__(self, path, budget, guard):
        from fusion_baselines.protected_run_snapshots import SnapshotStore

        self.store, self.budget, self.guard = SnapshotStore(path), budget, guard
        self.references = []
        self.attempts = []

    def json(self, name, value, *, terminal=False):
        if not terminal:
            self.guard()
        raw = _encode(value)
        self.budget.charge(len(raw), terminal=terminal)
        attempt = dict(
            path=str(self.store.directory / (name + ".json")),
            bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
            acknowledged=False,
        )
        self.attempts.append(attempt)
        ref = self.store.json(name, value)
        self.references.append(ref)
        attempt["acknowledged"] = True
        if not terminal:
            self.guard()
        return ref

    def arrays(self, name, value):
        from fusion_baselines.protected_run_snapshots import _array_bytes

        self.guard()
        raw = _array_bytes(value)
        self.budget.charge(len(raw))
        attempt = dict(
            path=str(self.store.directory / (name + ".npz")),
            bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
            acknowledged=False,
        )
        self.attempts.append(attempt)
        ref = self.store.arrays(name, value)
        self.references.append(ref)
        attempt["acknowledged"] = True
        self.guard()
        return ref


class Events:
    def __init__(self, path, budget, guard, progress):
        from fusion_baselines.protected_search_journal import EventJournal

        self.journal, self.budget, self.guard = EventJournal(path), budget, guard
        self.progress = progress
        self.path = str(path)

    def __call__(self, value):
        self.guard()
        receipt = self.journal.receipt
        self.budget.charge(
            len(
                _encode(
                    dict(
                        schema_version=1,
                        index=receipt["records"],
                        previous_sha256=receipt["head_sha256"],
                        payload=value,
                    )
                )
            )
        )
        receipt = self.journal(value)
        self.progress(
            dict(
                event_directory=self.path,
                event_receipt=receipt,
                payload_charged_bytes=self.budget.used,
            )
        )
        self.guard()


def admission_identity(admitted):
    current = admitted["current_admission"]
    need(current is not None, "fresh active native admission required")
    return dict(
        metadata_identity=admitted["metadata_identity"],
        current_provenance=current["current_provenance"],
        checked_inputs=current["checked_inputs"],
        source_before=current["source_before"],
        source_after=current["source_after"],
    )


def produce(admitted, pair_index, directory, writer, budget, guard, progress):
    from fusion_baselines.fixed_field_probe_native import evaluate_model

    results = []
    for state_index in (2 * pair_index, 2 * pair_index + 1):
        context = admitted["states"][state_index]
        snapshot = None
        state_rows = []
        for level in LEVELS:
            guard()
            budget.reserve_model()
            label = f"s{state_index}-l{level['index']}"
            progress(dict(operation="model-attempted", state=state_index, level=level))
            events = Events(directory / (label + "-events"), budget, guard, progress)
            work = Work(level, events, guard)
            result = evaluate_model(
                admitted["cell_sources"],
                context["case"],
                context["seed"],
                context["x"],
                level,
                frozen_snapshot=snapshot,
                callback=work,
                guard=guard,
            )
            counts = work.finish(result["native_calls"])
            if snapshot is None:
                snapshot = result["snapshot"]
            else:
                same(result["snapshot"], snapshot, "frozen state snapshot")
            arrays = writer.arrays(label + "-arrays", result["arrays"])
            payload = dict(
                schema_version=1,
                kind="fixed-field-probe-model",
                state=state_index,
                case=context["case"],
                level=level,
                state_sha256=context["row"]["state_sha256"],
                names=context["names"],
                x=context["x"],
                arrays=arrays,
                **{k: result[k] for k in ("snapshot", "metrics", "initialization", "native_calls")},
                work=counts,
                event_directory=events.path,
                event_receipt=events.journal.receipt,
                **SCOPE,
            )
            ref = writer.json(label + "-model", payload)
            state_rows.append(ref)
            progress(
                dict(
                    operation="model-returned",
                    state=state_index,
                    level=level,
                    reference=ref,
                    payload_charged_bytes=budget.used,
                )
            )
        results.append(dict(state=state_index, models=state_rows))
    return dict(states=results, models=12, native_requests=84, native_points=402432, **SCOPE)


def targets(admitted, context):
    import audit_clear_coil_field_start as legacy

    # The original archives predate canonical SnapshotStore NPZ. Preserve their
    # qualified hash-checked reader; newly generated arrays use read_arrays above.
    result = legacy.target(admitted["cell_sources"], context["case"], legacy.Evidence())
    same(result["input"], context["input_data"], "independent target input")
    return {
        n: dict(value, target_flux=result["target_flux"]) for n, value in result["targets"].items()
    }


def audit(admitted, pair_index, producer_reference, writer, budget, guard, progress):
    from fusion_baselines.fixed_field_probe_audit import audit_model, audit_state, compare_pair
    from fusion_baselines.protected_run_snapshots import read_arrays, read_json
    from fusion_baselines.protected_search_journal import read_events

    producer = read_json(producer_reference)
    need(
        producer.get("status") == "completed"
        and producer.get("phase") == "producer"
        and producer.get("pair_index") == pair_index,
        "complete exact producer result",
    )
    saved = producer["result"]
    same(
        [row["state"] for row in saved["states"]],
        [2 * pair_index, 2 * pair_index + 1],
        "ordered pair states",
    )
    states, state_refs = [], []
    for state_result in saved["states"]:
        state_index = state_result["state"]
        context = admitted["states"][state_index]
        target = targets(admitted, context)
        need(len(state_result["models"]) == 6, "six raw model records")
        model_results = []
        for level, model_ref in zip(LEVELS, state_result["models"], strict=True):
            guard()
            budget.reserve_model()
            progress(
                dict(
                    operation="audit-attempted",
                    state=state_index,
                    level=level,
                    input_reference=model_ref,
                )
            )
            model = read_json(model_ref)
            for key, value in dict(
                kind="fixed-field-probe-model",
                state=state_index,
                case=context["case"],
                level=level,
                state_sha256=context["row"]["state_sha256"],
                names=context["names"],
                x=context["x"],
                **SCOPE,
            ).items():
                same(model[key], value, "raw model " + key)
            work = Work(level, lambda event: None, guard)
            for event in read_events(model["event_directory"], model["event_receipt"]):
                work(event)
            same(work.finish(model["native_calls"]), model["work"], "saved callback work")
            arrays = read_arrays(model["arrays"])
            control = state_index % 2 == 0 and level["index"] == 0
            checked = audit_model(
                context["seed"],
                context["x"],
                context["case"],
                level,
                model["snapshot"],
                model["initialization"],
                model["metrics"],
                arrays,
                input_data=context["input_data"],
                target=target[level["ninner"]],
                control_bundle=context["control_bundle"] if control else None,
                control_snapshot=context["control_snapshot"] if control else None,
                guard=guard,
            )
            guard()
            ref = writer.json(f"s{state_index}-l{level['index']}-audit", checked)
            progress(
                dict(
                    operation="model-audited",
                    state=state_index,
                    level=level,
                    reference=ref,
                    payload_charged_bytes=budget.used,
                )
            )
            model_results.append(checked)
        checked = audit_state(model_results)
        ref = writer.json(f"s{state_index}-audit", checked)
        state_refs.append(ref)
        states.append(checked)
        progress(dict(operation="state-audited", state=state_index, reference=ref))
    comparison = compare_pair(*states, admitted["pairs"][pair_index]["original"])
    ref = writer.json("comparison", comparison)
    return dict(states=state_refs, comparison=ref, **SCOPE)


def worker(config_ref, control_fd):
    global _ACTIVE
    need(not _ACTIVE, "non-reentrant worker")
    _ACTIVE = True
    from fixed_field_probe_inputs import intake

    from fusion_baselines.protected_run_snapshots import read_json

    config = read_json(config_ref)
    same({key: os.environ.get(key) for key in THREADS}, THREADS, "single-thread worker")
    need(
        os.name == "posix"
        and config["phase"] in ("producer", "audit")
        and type(config["pair_index"]) is int
        and config["pair_index"] in (0, 1),
        "registered POSIX phase/pair",
    )
    directory = Path(config["output"])
    directory.mkdir(exist_ok=False)
    guard = Guard(directory, config["started_monotonic"])
    budget = PayloadBudget(config["payload_charged_bytes"])
    writer = Writer(directory / "records", budget, guard)
    sequence = 0

    def emit(kind, payload):
        nonlocal sequence
        payload = dict(payload, payload_charged_bytes=budget.used)
        for _ in range(8):
            size = len(_encode(dict(sequence=sequence, kind=kind, payload=payload)))
            if payload["payload_charged_bytes"] == budget.used + size:
                break
            payload["payload_charged_bytes"] = budget.used + size
        same(payload["payload_charged_bytes"], budget.used + size, "frame byte fixed point")
        budget.charge(size, terminal=kind in ("returned", "failed"))
        send(control_fd, sequence, kind, payload)
        sequence += 1

    def progress(payload):
        guard()
        emit("progress", payload)
        guard()

    try:
        before = execution_gate(config["checkpoint"], Path(config["root"]), guard=guard)
        admitted = intake(Path(config["root"]), guard=guard, native_admission=True)
        identity = admission_identity(admitted)
        identity_ref = writer.json("admission-before", identity)
        progress(dict(operation="admitted", reference=identity_ref))
        if config["phase"] == "producer":
            result = produce(
                admitted, config["pair_index"], directory, writer, budget, guard, progress
            )
        else:
            result = audit(
                admitted, config["pair_index"], config["producer"], writer, budget, guard, progress
            )
        after = execution_gate(config["checkpoint"], Path(config["root"]), guard=guard)
        same(after, before, "source closure before/after")
        rechecked = intake(Path(config["root"]), guard=guard, native_admission=True)
        same(admission_identity(rechecked), identity, "native admission before/after")
        after_ref = writer.json("admission-after", admission_identity(rechecked))
        payload = dict(
            schema_version=1,
            kind="fixed-field-probe-phase",
            status="completed",
            phase=config["phase"],
            pair_index=config["pair_index"],
            configuration=config_ref,
            source_before=before,
            source_after=after,
            admission_before=identity_ref,
            admission_after=after_ref,
            result=result,
            references=writer.references.copy(),
            attempted_writes=writer.attempts.copy(),
            payload_charged_bytes_before_return=budget.used,
            **SCOPE,
        )
        ref = writer.json("result", payload)
        guard()
        emit("returned", dict(reference=ref, payload_charged_bytes=budget.used))
        guard()
        return 0
    except BaseException as exc:
        # Existing raw/event files survive; this explicit prefix cannot be positive.
        failure = dict(
            schema_version=1,
            kind="fixed-field-probe-phase",
            status="failed",
            phase=config["phase"],
            pair_index=config["pair_index"],
            configuration=config_ref,
            error=f"{type(exc).__name__}: {exc}",
            references=writer.references.copy(),
            attempted_writes=writer.attempts.copy(),
            payload_charged_bytes_before_return=budget.used,
            **SCOPE,
        )
        try:
            need(
                time.monotonic() - config["started_monotonic"] < PHASE_SECONDS + 5,
                "failure publication grace exhausted",
            )
            # Fresh store if the scientific writer was poisoned; retain its partial tail.
            failure_writer = Writer(directory / "failure", budget, lambda: None)
            ref = failure_writer.json("result", failure, terminal=True)
            emit("failed", dict(reference=ref, payload_charged_bytes=budget.used))
        except BaseException as publication_error:
            print(
                f"Failure prefix publication: {type(publication_error).__name__}: "
                f"{publication_error}",
                file=sys.stderr,
            )
        return 1


def validate_return(
    result_ref, configuration, config_ref, *, guard=lambda: None, control_frames=None
):
    """Parent-side exact coverage and byte graph; no new field arithmetic."""
    from fixed_field_probe_inputs import intake

    from fusion_baselines.fixed_field_probe_audit import _identity, audit_state, compare_pair
    from fusion_baselines.protected_run_snapshots import checked_bytes, read_json
    from fusion_baselines.protected_search_journal import read_events

    root = Path(configuration["root"])
    result = read_json(result_ref)
    phase, pair_index = configuration["phase"], configuration["pair_index"]
    for key, value in dict(
        schema_version=1,
        kind="fixed-field-probe-phase",
        status="completed",
        phase=phase,
        pair_index=pair_index,
        configuration=config_ref,
        **SCOPE,
    ).items():
        same(result.get(key), value, "complete phase " + key)
    expected = Path(configuration["output"]) / "records"
    need(Path(result_ref["path"]) == expected / "result.json", "owned returned result path")
    references = result["references"]
    need(
        type(references) is list
        and references
        and len({r["path"] for r in references}) == len(references),
        "distinct explicit references",
    )
    same(
        result["attempted_writes"],
        [dict(ref, acknowledged=True) for ref in references],
        "all explicit payload writes acknowledged",
    )
    charged = result.get("payload_charged_bytes_before_return")
    need(type(charged) is int and 0 <= charged <= PAIR_BYTES, "bounded plain phase byte account")
    initial_charge = configuration["payload_charged_bytes"]
    need(
        type(initial_charge) is int and 0 <= initial_charge <= PAIR_BYTES,
        "bounded plain phase starting account",
    )
    known_bytes = initial_charge + sum(ref["bytes"] for ref in references)
    for ref in references:
        guard()
        path = Path(ref["path"])
        need(
            path.parent == expected and path.suffix in (".json", ".npz"),
            "owned explicitly returned payload",
        )
        checked_bytes(ref, path.suffix)
    same(result["source_before"], result["source_after"], "unchanged worker source closure")
    same(
        result["source_after"],
        execution_gate(configuration["checkpoint"], root, guard=guard),
        "independent parent source check",
    )
    need(
        result["admission_before"] in references and result["admission_after"] in references,
        "retained native admissions",
    )
    same(
        read_json(result["admission_before"]),
        read_json(result["admission_after"]),
        "unchanged native admissions",
    )
    saved = result["result"]
    same({key: saved.get(key) for key in SCOPE}, SCOPE, "result scope")
    admitted = intake(root, guard=guard, native_admission=False)
    same(
        read_json(result["admission_before"])["metadata_identity"],
        admitted["metadata_identity"],
        "parent independently checked metadata",
    )
    contexts = admitted["states"][2 * pair_index : 2 * pair_index + 2]
    if phase == "producer":
        same(
            {key: saved.get(key) for key in ("models", "native_requests", "native_points")},
            dict(models=12, native_requests=84, native_points=402432),
            "complete pair work",
        )
        same(
            [row["state"] for row in saved["states"]],
            [2 * pair_index, 2 * pair_index + 1],
            "complete fixed pair state order",
        )
        for state, context in zip(saved["states"], contexts, strict=True):
            need(len(state["models"]) == 6, "complete six model return")
            snapshot = None
            for ref, level in zip(state["models"], LEVELS, strict=True):
                guard()
                need(ref in references, "explicitly retained model reference")
                row = read_json(ref)
                same(row["level"], level, "returned level order")
                same(row["state"], state["state"], "returned state order")
                need(row["arrays"] in references, "explicitly retained raw arrays")
                for key, value in dict(
                    kind="fixed-field-probe-model",
                    schema_version=1,
                    case=context["case"],
                    names=context["names"],
                    x=context["x"],
                    state_sha256=context["row"]["state_sha256"],
                    **SCOPE,
                ).items():
                    same(row.get(key), value, "returned fixed model " + key)
                _identity(context["seed"], context["x"], context["case"], row["snapshot"])
                if snapshot is None:
                    snapshot = row["snapshot"]
                same(row["snapshot"], snapshot, "unchanged refined currents/snapshot")
                same(row["metrics"]["frozen_scale"], level["index"] != 0, "normalization flag")
                for key in ("scale", "B2_scale", "target_flux"):
                    same(row["metrics"][key], snapshot[key], "frozen metric " + key)
                event_path = (
                    Path(configuration["output"]) / f"s{state['state']}-l{level['index']}-events"
                )
                same(row["event_directory"], str(event_path), "owned model callback journal")
                work = Work(level, lambda e: None, guard)
                for event in read_events(event_path, row["event_receipt"]):
                    work(event)
                known_bytes += sum(
                    (event_path / f"{i:06d}.json").stat().st_size
                    for i in range(row["event_receipt"]["records"])
                )
                same(work.finish(row["native_calls"]), row["work"], "completed raw work")
    else:
        need(
            len(saved["states"]) == 2
            and all(ref in references for ref in saved["states"])
            and saved["comparison"] in references,
            "two states and comparison retained",
        )
        states = []
        for reference, context in zip(saved["states"], contexts, strict=True):
            state = read_json(reference)
            same(state, audit_state(state["models"]), "complete reconstructed state audit")
            same(state["case"], context["case"], "audited fixed case")
            same(state["state_sha256"], context["row"]["state_sha256"], "audited fixed state")
            for row in state["models"]:
                same(row["names"], context["names"], "audited fixed names")
                same(row["x"], context["x"], "audited fixed coordinate bits")
                _identity(context["seed"], context["x"], context["case"], row["snapshot"])
            states.append(state)
        same(
            read_json(saved["comparison"]),
            compare_pair(*states, admitted["pairs"][pair_index]["original"]),
            "independently reconstructed complete paired report",
        )
    need(charged >= known_bytes, "phase byte account covers all explicit payload/journal bytes")
    if control_frames is not None:
        need(
            type(control_frames) is list
            and control_frames
            and control_frames[-1]["kind"] == "returned",
            "explicit complete phase control",
        )
        same(control_frames[-1]["payload"]["reference"], result_ref, "returned control reference")
        same(
            charged,
            known_bytes + sum(len(_encode(frame)) for frame in control_frames[:-1]),
            "exact pre-result payload and control account",
        )
        same(
            control_frames[-1]["payload"]["payload_charged_bytes"],
            charged + result_ref["bytes"] + len(_encode(control_frames[-1])),
            "exact final return byte account",
        )
    guard()
    return result


def run_phase(pair_dir, phase, pair_index, checkpoint, budget, *, producer=None, root=ROOT):
    started = time.monotonic()
    guard = Guard(pair_dir, started)
    parent = Writer(pair_dir / (phase + "-parent"), budget, guard)
    configuration = dict(
        schema_version=1,
        kind="fixed-field-probe-configuration",
        phase=phase,
        pair_index=pair_index,
        checkpoint=checkpoint,
        root=str(root),
        started_monotonic=started,
        output=str(pair_dir / phase),
        producer=producer,
        payload_charged_bytes=budget.used,
        **SCOPE,
    )
    # Include the configuration's own exact encoded length in the child's account.
    for _ in range(8):
        total = budget.used + len(_encode(configuration))
        if configuration["payload_charged_bytes"] == total:
            break
        configuration["payload_charged_bytes"] = total
    config_ref = parent.json("configuration", configuration)
    same(configuration["payload_charged_bytes"], budget.used, "configuration byte fixed point")
    acknowledgement = supervise(
        lambda fd: [
            sys.executable,
            str(Path(root) / "scripts/run_fixed_field_probe.py"),
            "worker",
            "--configuration",
            json.dumps(config_ref),
            "--control-fd",
            str(fd),
        ],
        pair_dir / (phase + "-process"),
        started,
    )
    result_ref = None
    try:
        # The child account is monotonically precharged, even on explicit failure.
        for frame in acknowledgement["frames"]:
            charge = frame["payload"].get("payload_charged_bytes")
            if charge is not None:
                need(type(charge) is int and charge >= budget.used, "monotonic child byte account")
                if charge != budget.used:
                    budget.charge(charge - budget.used, terminal=True)
        for stream in ("stdout.log", "stderr.log"):
            size = (pair_dir / (phase + "-process") / stream).stat().st_size
            if size:
                budget.charge(size, terminal=True)
        need(acknowledgement["complete"] is True, "on-time explicitly returned worker required")
        final = acknowledgement["frames"][-1]
        result_ref = final["payload"]["reference"]
        validate_return(
            result_ref,
            configuration,
            config_ref,
            guard=guard,
            control_frames=acknowledgement["frames"],
        )
        guard()
    except BaseException as exc:
        acknowledgement.update(complete=False, parent_error=f"{type(exc).__name__}: {exc}")
    acknowledgement["result_reference"] = result_ref
    ack_ref = parent.json("acknowledgement", acknowledgement, terminal=True)
    if time.monotonic() - started >= PHASE_SECONDS and acknowledgement["complete"] is True:
        acknowledgement.update(
            complete=False, parent_error="final parent publication missed deadline"
        )
        ack_ref = parent.json("late-negative-acknowledgement", acknowledgement, terminal=True)
    return dict(
        complete=acknowledgement["complete"],
        acknowledgement=ack_ref,
        result=result_ref,
        payload_charged_bytes=budget.used,
        **SCOPE,
    )


def safe_phase(pair_dir, phase, pair_index, checkpoint, budget, *, producer=None, root=ROOT):
    """Parent I/O errors end this phase, not implicitly the other registered pair."""
    try:
        return run_phase(
            pair_dir, phase, pair_index, checkpoint, budget, producer=producer, root=root
        )
    except Exception as exc:
        # No directory scan or guessed return. Files from failed publications stay.
        return dict(
            complete=False,
            acknowledgement=None,
            result=None,
            parent_error=f"{type(exc).__name__}: {exc}",
            output_prefix=str(pair_dir / phase),
            parent_prefix=str(pair_dir / (phase + "-parent")),
            payload_charged_bytes=budget.used,
            **SCOPE,
        )


def run_study(output, checkpoint, root=ROOT):
    from fusion_baselines.protected_run_snapshots import SnapshotStore

    before = execution_gate(checkpoint, root)
    output = Path(output).resolve()
    output.mkdir(exist_ok=False)
    outcomes = []
    budgets = {}
    for pair_index in (0, 1):
        try:
            need(shutil.disk_usage(output).free >= START_FREE, "3 GiB starting disk reserve")
            same(execution_gate(checkpoint, root), before, "source checkpoint before pair")
        except Exception as exc:
            for unchecked in range(pair_index, 2):
                outcomes.append(
                    dict(
                        pair_index=unchecked,
                        producer=None,
                        audit=None,
                        unchecked=True,
                        admission_error=f"{type(exc).__name__}: {exc}",
                        **SCOPE,
                    )
                )
            break
        directory = output / f"pair-{pair_index}"
        directory.mkdir(exist_ok=False)
        budget = PayloadBudget()
        budgets[pair_index] = budget
        producer = safe_phase(directory, "producer", pair_index, checkpoint, budget, root=root)
        auditor = None
        if producer["complete"]:
            auditor = safe_phase(
                directory,
                "audit",
                pair_index,
                checkpoint,
                budget,
                producer=producer["result"],
                root=root,
            )
        outcomes.append(
            dict(
                pair_index=pair_index,
                producer=producer,
                audit=auditor,
                payload_charged_bytes=budget.used,
            )
        )
        try:
            row = outcomes[-1]
            for _ in range(8):
                charged = budget.used + len(_encode(row))
                if row["payload_charged_bytes"] == charged:
                    break
                row["payload_charged_bytes"] = charged
            Writer(output / f"pair-{pair_index}-index", budget, lambda: None).json(
                "outcome", row, terminal=True
            )
            same(row["payload_charged_bytes"], budget.used, "pair index byte fixed point")
        except Exception as exc:
            outcomes[-1]["index_publication_error"] = f"{type(exc).__name__}: {exc}"
            outcomes[-1]["publication_pass"] = False
    after, final_source_error = None, None
    try:
        after = execution_gate(checkpoint, root)
        same(after, before, "unchanged full study source closure")
    except Exception as exc:
        final_source_error = f"{type(exc).__name__}: {exc}"
    payload = dict(
        schema_version=1,
        kind="fixed-field-probe-study",
        source_before=before,
        source_after=after,
        checkpoint=checkpoint,
        pairs=outcomes,
        final_source_error=final_source_error,
        **SCOPE,
    )
    # Conservatively charge the entire shared index to EACH started pair, rather
    # than inventing a favorable division of shared terminal metadata.
    for _ in range(8):
        size = len(_encode(payload))
        wanted = {str(index): budget.used + size for index, budget in budgets.items()}
        if payload.get("final_payload_charged_bytes") == wanted:
            break
        payload["final_payload_charged_bytes"] = wanted
    size = len(_encode(payload))
    for index, budget in budgets.items():
        budget.charge(size, terminal=True)
        same(
            payload["final_payload_charged_bytes"][str(index)],
            budget.used,
            "shared study index byte fixed point",
        )
    return SnapshotStore(output / "index").json("study", payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("sources", "worker", "run"))
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--configuration")
    parser.add_argument("--control-fd", type=int)
    args = parser.parse_args(argv)
    if args.operation == "sources":
        print(json.dumps(source_snapshot(), sort_keys=True))
        return 0
    if args.operation == "worker":
        return worker(json.loads(args.configuration), args.control_fd)
    need(args.checkpoint is not None and args.output is not None, "output and checkpoint required")
    print(json.dumps(run_study(args.output, reference(args.checkpoint)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
