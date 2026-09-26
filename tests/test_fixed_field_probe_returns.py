"""Adversarial parent-return controls using fresh synthetic files, never fields."""

import copy
import sys
from pathlib import Path

import numpy as np
import pytest
from test_fixed_field_probe_audit import paired, replace_metric

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fixed_field_probe_inputs as inputs  # noqa: E402
import run_fixed_field_probe as run  # noqa: E402

from fusion_baselines import fixed_field_probe_audit as audit  # noqa: E402
from fusion_baselines.fixed_field_probe_control import requests  # noqa: E402
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json  # noqa: E402
from fusion_baselines.protected_search_journal import _encode  # noqa: E402


@pytest.fixture(scope="module")
def templates():
    # Only synthetic metric adapters are active while these reports are built.
    with pytest.MonkeyPatch.context() as patch:
        return {n: paired(patch, n) for n in (6, 8)}


def saved_return(
    monkeypatch,
    tmp_path,
    templates,
    *,
    phase="producer",
    pair_index=0,
    model_change=None,
    state_change=None,
    pair_change=None,
    envelope_change=None,
    event_change=None,
    negative=False,
):
    control, proposal, pair = copy.deepcopy(templates[6 if pair_index == 0 else 8])
    if negative:
        row = proposal["models"][4]
        replace_metric(row, "flux", row["metrics"]["target_flux"] * (1 + 2e-6))
        proposal = audit.audit_state(proposal["models"])
    comparison = audit.compare_pair(control, proposal, pair)
    contexts = []
    for state in (control, proposal):
        row = state["models"][0]
        contexts.append(
            dict(
                case=row["case"],
                seed=row["snapshot"]["seed_geometry"],
                x=row["x"],
                names=row["names"],
                row=dict(state_sha256=row["state_sha256"]),
            )
        )
    admitted = dict(
        metadata_identity=dict(synthetic="immutable-input-graph"),
        states=copy.deepcopy(contexts + contexts),
        pairs=[dict(original=copy.deepcopy(pair)) for _ in range(2)],
    )
    source = dict(commit="a" * 40, sources=[])
    intake_calls = []

    def intake(root, *, guard, native_admission):
        assert root == tmp_path and native_admission is False
        guard()
        intake_calls.append(root)
        return copy.deepcopy(admitted)

    monkeypatch.setattr(inputs, "intake", intake)
    monkeypatch.setattr(run, "execution_gate", lambda *args, **kwargs: copy.deepcopy(source))
    output = tmp_path / phase
    output.mkdir()
    configuration = dict(
        schema_version=1,
        kind="fixed-field-probe-configuration",
        phase=phase,
        pair_index=pair_index,
        root=str(tmp_path),
        output=str(output),
        checkpoint={},
        producer=None,
        started_monotonic=0.0,
        payload_charged_bytes=0,
        **run.SCOPE,
    )
    config_ref = SnapshotStore(tmp_path / "configuration").json("configuration", configuration)
    budget = run.PayloadBudget()
    writer = run.Writer(output / "records", budget, lambda: None)
    admission = dict(
        metadata_identity=admitted["metadata_identity"],
        current_provenance={},
        checked_inputs={},
        source_before={},
        source_after={},
    )
    before = writer.json("admission-before", admission)
    states = []
    for position, state in enumerate((control, proposal)):
        index = 2 * pair_index + position
        model_refs = []
        for level, audited in zip(run.LEVELS, state["models"], strict=True):
            label = f"s{index}-l{level['index']}"
            if phase == "audit":
                model_refs.append(writer.json(label + "-audit", audited))
                continue
            events = run.Events(output / (label + "-events"), budget, lambda: None, lambda e: None)

            def persist(event, events=events):
                saved_event = copy.deepcopy(event)
                if event_change:
                    event_change(saved_event)
                events(saved_event)

            work = run.Work(level, persist, lambda: None)
            calls = []
            for at, (field, quantity, points) in enumerate(requests(level)):
                event = dict(
                    index=at,
                    field=field,
                    quantity=quantity,
                    points=points,
                    status="attempted",
                    started_monotonic=float(at),
                    native_started=False,
                    native_completed=False,
                )
                work(event)
                event = dict(
                    event,
                    status="completed",
                    native_started=True,
                    native_completed=True,
                    completed_monotonic=event["started_monotonic"] + 0.5,
                )
                work(event)
                saved_event = copy.deepcopy(event)
                if event_change:
                    event_change(saved_event)
                calls.append(saved_event)
            counts = work.finish(work.completed)
            # The parent checks raw byte identity; numerical/schema checks belong
            # to the separate saved-data auditor. No physical arrays are needed.
            arrays = writer.arrays(label + "-arrays", dict(synthetic=np.array([1.0])))
            metrics = {key: value["actual"] for key, value in audited["metric_checks"].items()}
            metrics["frozen_scale"] = level["index"] != 0
            row = dict(
                schema_version=1,
                kind="fixed-field-probe-model",
                state=index,
                case=state["case"],
                level=level,
                state_sha256=state["state_sha256"],
                names=audited["names"],
                x=audited["x"],
                arrays=arrays,
                snapshot=audited["snapshot"],
                metrics=metrics,
                initialization={},
                native_calls=calls,
                work=counts,
                event_directory=events.path,
                event_receipt=events.journal.receipt,
                **run.SCOPE,
            )
            if model_change and position == 0 and level["index"] == 0:
                model_change(row)
            model_refs.append(writer.json(label + "-model", row))
        if phase == "producer":
            states.append(dict(state=index, models=model_refs))
        else:
            if state_change and position == 0:
                state_change(state)
            states.append(writer.json(f"s{index}-audit", state))
    if phase == "producer":
        saved = dict(
            states=states, models=12, native_requests=84, native_points=402432, **run.SCOPE
        )
    else:
        if pair_change:
            pair_change(comparison)
        saved = dict(states=states, comparison=writer.json("comparison", comparison), **run.SCOPE)
    after = writer.json("admission-after", admission)
    envelope = dict(
        schema_version=1,
        kind="fixed-field-probe-phase",
        status="completed",
        phase=phase,
        pair_index=pair_index,
        configuration=config_ref,
        source_before=source,
        source_after=source,
        admission_before=before,
        admission_after=after,
        result=saved,
        references=writer.references.copy(),
        attempted_writes=writer.attempts.copy(),
        payload_charged_bytes_before_return=budget.used,
        **run.SCOPE,
    )
    if envelope_change:
        envelope_change(envelope)
    ref = writer.json("result", envelope)
    return ref, configuration, config_ref, admitted, intake_calls


@pytest.mark.parametrize("phase", ["producer", "audit"])
@pytest.mark.parametrize("pair_index", [0, 1])
def test_complete_return_requires_fresh_metadata_intake(
    monkeypatch, tmp_path, templates, phase, pair_index
):
    args = saved_return(monkeypatch, tmp_path, templates, phase=phase, pair_index=pair_index)
    result = run.validate_return(*args[:3])
    assert args[4] == [tmp_path]
    assert result["status"] == "completed" and result["physical_admission"] is False


@pytest.mark.parametrize(
    "fault",
    [
        "empty_states",
        "extra_state",
        "state_order",
        "missing_model",
        "level_order",
        "duplicate_model",
        "native_count",
        "bool_count",
        "missing_reference",
        "duplicate_reference",
        "source",
        "scope",
        "status",
        "pair_index",
        "schema",
        "configuration",
    ],
)
def test_producer_envelope_coverage_and_identity_fail_closed(
    monkeypatch, tmp_path, templates, fault
):
    def change(row):
        saved = row["result"]
        if fault == "empty_states":
            saved["states"] = []
        elif fault == "extra_state":
            saved["states"].append(copy.deepcopy(saved["states"][0]))
        elif fault == "state_order":
            saved["states"].reverse()
        elif fault == "missing_model":
            saved["states"][0]["models"].pop()
        elif fault == "level_order":
            saved["states"][0]["models"].reverse()
        elif fault == "duplicate_model":
            saved["states"][0]["models"][1] = saved["states"][0]["models"][0]
        elif fault == "native_count":
            saved["native_points"] -= 1
        elif fault == "bool_count":
            saved["models"] = True
        elif fault == "missing_reference":
            row["references"].remove(saved["states"][0]["models"][0])
        elif fault == "duplicate_reference":
            row["references"].append(copy.deepcopy(row["references"][0]))
        elif fault == "source":
            row["source_after"] = dict(commit="b" * 40, sources=[])
        elif fault == "scope":
            row["physical_admission"] = 0
        elif fault == "status":
            row["status"] = "failed"
        elif fault == "pair_index":
            row["pair_index"] = True
        elif fault == "schema":
            row["schema_version"] = True
        else:
            row["configuration"] = {}

    args = saved_return(monkeypatch, tmp_path, templates, envelope_change=change)
    with pytest.raises((ValueError, KeyError)):
        run.validate_return(*args[:3])


@pytest.mark.parametrize(
    "fault",
    [
        "case",
        "state",
        "names",
        "x",
        "digest",
        "matrix",
        "scale",
        "construction",
        "flag",
        "metric_scale",
        "work",
        "calls",
        "event_path",
        "event_receipt",
        "raw_reference",
    ],
)
def test_producer_model_identity_and_receipts_fail_closed(monkeypatch, tmp_path, templates, fault):
    def change(row):
        if fault == "case":
            row["case"] = dict(row["case"], method="V")
        elif fault == "state":
            row["state"] = 1
        elif fault == "names":
            row["names"] = list(reversed(row["names"]))
        elif fault == "x":
            row["x"] = list(row["x"])
            row["x"][0] += 0.01
        elif fault == "digest":
            row["state_sha256"] = "b" * 64
        elif fault == "matrix":
            row["snapshot"]["physical"][0]["matrix"][0][0] += 1e-13
        elif fault == "scale":
            row["snapshot"]["scale"] *= 1.1
        elif fault == "construction":
            row["snapshot"]["construction"]["ncoil"] = 512
        elif fault == "flag":
            row["metrics"]["frozen_scale"] = 0
        elif fault == "metric_scale":
            row["metrics"]["scale"] *= 1.1
        elif fault == "work":
            row["work"]["points"] -= 1
        elif fault == "calls":
            row["native_calls"].pop()
        elif fault == "event_path":
            row["event_directory"] += "-unowned"
        elif fault == "event_receipt":
            row["event_receipt"]["head_sha256"] = "b" * 64
        else:
            row["arrays"] = dict(row["arrays"], sha256="b" * 64)

    args = saved_return(monkeypatch, tmp_path, templates, model_change=change)
    with pytest.raises((ValueError, KeyError)):
        run.validate_return(*args[:3])


@pytest.mark.parametrize(
    "fault",
    [
        "empty",
        "model_count",
        "numerical_bool",
        "work",
        "scope",
        "direct",
        "initializer",
        "level_order",
        "fixed_x",
    ],
)
def test_audit_state_must_reconstruct_exactly(monkeypatch, tmp_path, templates, fault):
    def change(state):
        if fault == "empty":
            state.clear()
        elif fault == "model_count":
            state["models"].pop()
        elif fault == "numerical_bool":
            state["numerical_pass"] = 1
        elif fault == "work":
            state["work"]["direct_statistics"] -= 1
        elif fault == "scope":
            state["field_pass"] = True
        elif fault == "direct":
            state["models"][0]["direct_errors"]["boundary_B"] = 1.0
        elif fault == "initializer":
            state["models"][0]["initializer_check"]["passed"] = 1
        elif fault == "level_order":
            state["models"].reverse()
        else:
            state["models"][0]["x"][0] += 0.1

    # Comparison is generated before mutating the retained state in the fixture.
    args = saved_return(monkeypatch, tmp_path, templates, phase="audit", state_change=change)
    with pytest.raises((ValueError, KeyError)):
        run.validate_return(*args[:3])


@pytest.mark.parametrize(
    "fault",
    [
        "empty",
        "normal_gain",
        "margin",
        "vector_gain",
        "armijo",
        "rhs",
        "physical",
        "counterfactual_history",
    ],
)
def test_audit_pair_labels_are_independently_reconstructed(monkeypatch, tmp_path, templates, fault):
    def change(row):
        if fault == "empty":
            row.clear()
        elif fault == "normal_gain":
            row["normal_rms"]["resolved_diagnostic_gain"] = False
        elif fault == "margin":
            row["normal_rms"]["margin"] = 0.0
        elif fault == "vector_gain":
            row["vector_rms"]["resolved_diagnostic_gain"] = 1
        elif fault == "armijo":
            row["armijo"]["counterfactual_armijo_pass"] = False
        elif fault == "rhs":
            row["armijo"]["saved_rhs"] += 1e-15
        elif fault == "physical":
            row["physical_admission"] = True
        else:
            row["armijo"]["historical_step_accepted"] = True

    args = saved_return(monkeypatch, tmp_path, templates, phase="audit", pair_change=change)
    with pytest.raises((ValueError, KeyError)):
        run.validate_return(*args[:3])


def test_complete_finite_negative_is_retained_not_promoted(monkeypatch, tmp_path, templates):
    args = saved_return(monkeypatch, tmp_path, templates, phase="audit", negative=True)
    result = run.validate_return(*args[:3])
    compared = read_json(result["result"]["comparison"])
    assert compared["normal_rms"]["resolved_diagnostic_gain"] is False
    assert compared["vector_rms"]["resolved_diagnostic_gain"] is False
    assert compared["physical_admission"] is False


def test_changed_fresh_metadata_identity_rejects_saved_return(monkeypatch, tmp_path, templates):
    args = saved_return(monkeypatch, tmp_path, templates)
    args[3]["metadata_identity"] = dict(synthetic="different-input-graph")
    with pytest.raises(ValueError, match="metadata"):
        run.validate_return(*args[:3])


@pytest.mark.parametrize(
    "fault",
    [
        "unacknowledged",
        "missing_attempt",
        "extra_attempt",
        "wrong_digest",
        "negative_charge",
        "bool_charge",
        "over_cap",
        "underreported",
    ],
)
def test_completed_return_cannot_lose_write_failure_or_byte_account(
    monkeypatch, tmp_path, templates, fault
):
    def change(row):
        attempts = row["attempted_writes"]
        if fault == "unacknowledged":
            attempts[0]["acknowledged"] = False
        elif fault == "missing_attempt":
            attempts.pop()
        elif fault == "extra_attempt":
            attempts.append(copy.deepcopy(attempts[0]))
        elif fault == "wrong_digest":
            attempts[0]["sha256"] = "b" * 64
        elif fault == "negative_charge":
            row["payload_charged_bytes_before_return"] = -1
        elif fault == "bool_charge":
            row["payload_charged_bytes_before_return"] = True
        elif fault == "over_cap":
            row["payload_charged_bytes_before_return"] = run.PAIR_BYTES + 1
        else:
            row["payload_charged_bytes_before_return"] -= 1

    args = saved_return(monkeypatch, tmp_path, templates, envelope_change=change)
    with pytest.raises(ValueError):
        run.validate_return(*args[:3])


def frames_for(result_ref, *, prior=()):
    saved = read_json(result_ref)
    used = saved["payload_charged_bytes_before_return"] + result_ref["bytes"]
    returned = dict(
        sequence=len(prior),
        kind="returned",
        payload=dict(reference=result_ref, payload_charged_bytes=used),
    )
    for _ in range(10):
        size = len(_encode(returned))
        if returned["payload"]["payload_charged_bytes"] == used + size:
            return [*prior, returned]
        returned["payload"]["payload_charged_bytes"] = used + size
    raise AssertionError("synthetic final-frame size did not stabilize")


@pytest.mark.parametrize("phase", ["producer", "audit"])
def test_explicit_final_control_closes_exact_byte_account(monkeypatch, tmp_path, templates, phase):
    args = saved_return(monkeypatch, tmp_path, templates, phase=phase)
    returned = run.validate_return(*args[:3], control_frames=frames_for(args[0]))
    assert returned["status"] == "completed"


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "failed",
        "reference",
        "short_charge",
        "extra_charge",
        "bool_charge",
        "unaccounted_progress",
    ],
)
def test_final_control_cannot_lose_or_forge_account(monkeypatch, tmp_path, templates, fault):
    args = saved_return(monkeypatch, tmp_path, templates, phase="audit")
    frames = frames_for(args[0])
    if fault == "missing":
        frames.clear()
    elif fault == "failed":
        frames[-1]["kind"] = "failed"
    elif fault == "reference":
        frames[-1]["payload"]["reference"] = args[2]
    elif fault == "short_charge":
        frames[-1]["payload"]["payload_charged_bytes"] -= 1
    elif fault == "extra_charge":
        frames[-1]["payload"]["payload_charged_bytes"] += 1
    elif fault == "bool_charge":
        frames[-1]["payload"]["payload_charged_bytes"] = True
    else:
        frames.insert(0, dict(sequence=0, kind="progress", payload=dict(synthetic=True)))
    with pytest.raises(ValueError):
        run.validate_return(*args[:3], control_frames=frames)


@pytest.mark.parametrize("phase", ["producer", "audit"])
def test_prior_progress_frame_bytes_are_counted_once(monkeypatch, tmp_path, templates, phase):
    prior = []

    def change(envelope):
        base = envelope["payload_charged_bytes_before_return"]
        progress = dict(
            sequence=0,
            kind="progress",
            payload=dict(operation="synthetic-progress", payload_charged_bytes=base),
        )
        for _ in range(10):
            total = base + len(_encode(progress))
            if progress["payload"]["payload_charged_bytes"] == total:
                break
            progress["payload"]["payload_charged_bytes"] = total
        assert progress["payload"]["payload_charged_bytes"] == base + len(_encode(progress))
        envelope["payload_charged_bytes_before_return"] = total
        prior.append(progress)

    args = saved_return(monkeypatch, tmp_path, templates, phase=phase, envelope_change=change)
    frames = frames_for(args[0], prior=prior)
    result = run.validate_return(*args[:3], control_frames=frames)
    assert result["status"] == "completed"


@pytest.mark.parametrize("fault", ["negative_clock", "repeated_clock", "extra_keys"])
def test_parent_receipt_replay_rejects_bridge_invalid_envelopes(
    monkeypatch, tmp_path, templates, fault
):
    def change(event):
        if fault == "negative_clock" and event["index"] == 0:
            event["started_monotonic"] = -1.0
        elif fault == "repeated_clock":
            event["started_monotonic"] = 0.0
        elif fault == "extra_keys":
            event["ignored_error"] = "cannot be ignored"

    # The stored journal is canonical and hashes are genuine: these are schema
    # and chronology failures, not an accidental byte mismatch.
    args = saved_return(monkeypatch, tmp_path, templates, event_change=change)
    with pytest.raises(ValueError):
        run.validate_return(*args[:3])
