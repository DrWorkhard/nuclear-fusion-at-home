"""Synthetic additive admission gates; real native admission remains closed."""

import copy
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import protected_pilot_inputs as inputs  # noqa: E402


def fixture(tmp_path, monkeypatch):
    calls = dict(committed=[], checked=[], historical=[])

    def ref(path):
        path = str(path)
        return dict(path=path, sha256=hashlib.sha256(path.encode()).hexdigest())

    def row(name):
        return dict(path=name, sha256=ref(tmp_path / name)["sha256"], bytes=12)

    physics_ref = ref(tmp_path / inputs.QUALIFICATION)
    execution = dict(
        protocol=ref(tmp_path / inputs.PROTOCOL),
        code=[ref(tmp_path / name) for name in inputs.CODE],
    )
    launcher_ref = ref(tmp_path / "evidence/synthetic-launcher.json")
    physics = dict(
        schema_version=1,
        kind="protected-saved-physics-qualification",
        status="completed",
        saved_physics_qualification_pass=True,
        historical_reconstruction=dict(
            contexts_passed=8,
            certificate_recomputations=2,
            recorded_certificates_checked=4,
            sampled_BA_comparisons=48,
            sampled_vectors=3072,
            sampled_scalar_components=9216,
            native_requests=0,
            native_models_initialized=0,
            producer_certificates=0,
            equilibrium_solves=0,
            search_calls=0,
        ),
        regression=dict(exit_code=0, failures=0, errors=0, skipped=0, passed=3363),
        independent_review=dict(
            internal=True, blocking_findings_remaining=False, focused_passed=130
        ),
        limits=dict(
            new_native_search_executed=False,
            physical_admission=False,
            fine_grid_acceptance=False,
            step4_pass=False,
            sota_advance=False,
            ms1_reached=False,
            external_peer_review=False,
        ),
        sources=[row(name) for name in (inputs.physics.PROTOCOL, *inputs.physics.CODE)],
        artifacts=[row("artifacts/synthetic-physics.xml")],
    )
    checkpoint = dict(
        schema_version=1,
        kind="protected-pilot-execution-checkpoint",
        status="ready",
        execution_checkpoint_pass=True,
        execution=copy.deepcopy(execution),
        physics_qualification=physics_ref,
        launcher_qualification=launcher_ref,
        limits=inputs.EXECUTION_SCOPE.copy(),
    )
    launcher = dict(
        schema_version=1,
        kind="protected-pilot-launcher-qualification",
        status="completed",
        launcher_qualification_pass=True,
        execution=copy.deepcopy(execution),
        physics_qualification=physics_ref,
        limits=inputs.EXECUTION_SCOPE.copy(),
        regression=dict(exit_code=0, failures=0, errors=0, skipped=0, passed=3400),
        independent_review=dict(internal=True, blocking_findings_remaining=False),
        sources=[row(name) for name in (inputs.PROTOCOL, *inputs.CODE)],
        artifacts=[row("artifacts/synthetic-launcher.xml")],
    )
    checkpoint_path = tmp_path / inputs.EXECUTION_CHECKPOINT
    checkpoint_path.parent.mkdir()
    checkpoint_path.write_text("{}", encoding="utf-8")
    Path(launcher_ref["path"]).write_text("{}", encoding="utf-8")
    documents = {
        physics_ref["path"]: physics,
        str(checkpoint_path): checkpoint,
        launcher_ref["path"]: launcher,
    }

    def historical(*args):
        calls["historical"].append(args)
        return physics_ref

    monkeypatch.setattr(inputs, "QUALIFICATION_REVISION", "a" * 40)
    monkeypatch.setattr(inputs, "QUALIFICATION_HASH", "b" * 64)
    monkeypatch.setattr(inputs.physics, "sources", lambda root: dict(admitted_physics="synthetic"))
    monkeypatch.setattr(inputs.native.previous.previous, "historical", historical)
    monkeypatch.setattr(
        inputs.native, "read", lambda reference: copy.deepcopy(documents[reference["path"]])
    )
    monkeypatch.setattr(
        inputs.native, "checked", lambda reference: calls["checked"].append(reference)
    )
    monkeypatch.setattr(
        inputs.native, "require_committed", lambda root, path: calls["committed"].append(path)
    )
    monkeypatch.setattr(inputs.native, "reference", ref)
    monkeypatch.setattr(
        inputs.native, "git_state", lambda root: dict(available=True, dirty=False, commit="a" * 40)
    )
    return calls, physics, checkpoint, launcher


def test_real_default_native_admission_is_closed_before_any_source_work(tmp_path, monkeypatch):
    monkeypatch.setattr(inputs, "QUALIFICATION_REVISION", None)
    monkeypatch.setattr(inputs, "QUALIFICATION_HASH", None)
    assert inputs.QUALIFICATION_REVISION is inputs.QUALIFICATION_HASH is None
    monkeypatch.setattr(
        inputs.physics, "sources", lambda root: pytest.fail("closed pilot reached source binding")
    )
    with pytest.raises(ValueError, match="pilot is closed"):
        inputs.sources(tmp_path)


def test_actual_physics_pins_alone_cannot_open_native_execution(tmp_path, monkeypatch):
    revision, digest = inputs.QUALIFICATION_REVISION, inputs.QUALIFICATION_HASH
    assert revision == "c2237843bf9d961b2ae24c8d152cafd56927ebf7"
    assert digest == "0d0d15d6c11cbd505863de08ea9b244b621b09fa474217d9f45bc153f2257843"
    calls, _, _, _ = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(inputs, "QUALIFICATION_REVISION", revision)
    monkeypatch.setattr(inputs, "QUALIFICATION_HASH", digest)
    (tmp_path / inputs.EXECUTION_CHECKPOINT).unlink()
    with pytest.raises(ValueError, match="regular nonsymlink"):
        inputs.sources(tmp_path)
    assert calls["historical"][0][-2:] == (revision, digest)


@pytest.mark.parametrize(
    "key,value",
    [
        ("available", 1),
        ("available", False),
        ("dirty", True),
        ("dirty", 0),
        ("commit", "uncommitted"),
        ("commit", "A" * 40),
    ],
)
def test_native_execution_requires_fully_clean_available_repository(
    tmp_path, monkeypatch, key, value
):
    fixture(tmp_path, monkeypatch)
    repository = dict(available=True, dirty=False, commit="a" * 40)
    repository[key] = value
    monkeypatch.setattr(inputs.native, "git_state", lambda root: repository)
    with pytest.raises(ValueError, match="clean committed"):
        inputs.sources(tmp_path)


def test_valid_synthetic_qualification_binds_checkpoint_and_all_sources(tmp_path, monkeypatch):
    calls, _, _, _ = fixture(tmp_path, monkeypatch)
    source = inputs.sources(tmp_path)
    assert source["physics_sources"] == dict(admitted_physics="synthetic")
    assert source["execution_admission"]["checkpoint"]["path"] == str(
        tmp_path / inputs.EXECUTION_CHECKPOINT
    )
    assert len(source["execution_admission"]["sources"]) == 5
    assert len(source["qualification"]["sources"]) == 5
    assert tmp_path / inputs.EXECUTION_CHECKPOINT in calls["committed"]
    assert tmp_path / "evidence/synthetic-launcher.json" in calls["committed"]
    for name in (inputs.PROTOCOL, *inputs.CODE):
        assert tmp_path / name in calls["committed"]


@pytest.mark.parametrize(
    "name,value",
    [
        ("QUALIFICATION_REVISION", ""),
        ("QUALIFICATION_REVISION", "not-hex"),
        ("QUALIFICATION_HASH", "b" * 63),
        ("QUALIFICATION_HASH", None),
    ],
)
def test_malformed_pins_never_open_native_admission(tmp_path, monkeypatch, name, value):
    fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(inputs, name, value)
    with pytest.raises(ValueError, match="pilot is closed"):
        inputs.sources(tmp_path)


@pytest.mark.parametrize(
    "name",
    (
        inputs.PROTOCOL,
        *inputs.CODE,
        inputs.EXECUTION_CHECKPOINT,
        "evidence/synthetic-launcher.json",
    ),
)
def test_uncommitted_execution_source_or_gate_is_rejected(tmp_path, monkeypatch, name):
    fixture(tmp_path, monkeypatch)

    def committed(root, path):
        if path == tmp_path / name:
            raise ValueError("uncommitted")

    monkeypatch.setattr(inputs.native, "require_committed", committed)
    with pytest.raises(ValueError, match="uncommitted"):
        inputs.sources(tmp_path)


@pytest.mark.parametrize(
    "record,key,value",
    [
        ("physics", "saved_physics_qualification_pass", 1),
        ("checkpoint", "execution_checkpoint_pass", 1),
        ("checkpoint", "status", "pending"),
        ("launcher", "launcher_qualification_pass", 1),
        ("launcher", "status", "pending"),
    ],
)
def test_typed_qualification_completion_is_mandatory(tmp_path, monkeypatch, record, key, value):
    _, physics, checkpoint, launcher = fixture(tmp_path, monkeypatch)
    dict(physics=physics, checkpoint=checkpoint, launcher=launcher)[record][key] = value
    with pytest.raises(ValueError):
        inputs.sources(tmp_path)


@pytest.mark.parametrize("record", ["checkpoint", "launcher"])
@pytest.mark.parametrize("key", inputs.EXECUTION_SCOPE)
def test_no_checkpoint_or_launcher_record_can_broaden_scope(tmp_path, monkeypatch, record, key):
    _, _, checkpoint, launcher = fixture(tmp_path, monkeypatch)
    dict(checkpoint=checkpoint, launcher=launcher)[record]["limits"][key] = True
    with pytest.raises(ValueError):
        inputs.sources(tmp_path)


@pytest.mark.parametrize(
    "record,section,key,value",
    [
        ("physics", "regression", "passed", 3233),
        ("physics", "regression", "exit_code", False),
        ("physics", "independent_review", "focused_passed", 129),
        ("physics", "independent_review", "blocking_findings_remaining", True),
        ("physics", "historical_reconstruction", "contexts_passed", 7),
        ("physics", "historical_reconstruction", "recorded_certificates_checked", 2),
        ("physics", "historical_reconstruction", "sampled_scalar_components", 3072),
        ("physics", "historical_reconstruction", "native_requests", False),
        ("launcher", "regression", "passed", 3363),
        ("launcher", "regression", "errors", 1),
        ("launcher", "regression", "failures", 1),
        ("launcher", "regression", "skipped", 1),
        ("launcher", "independent_review", "internal", 1),
        ("launcher", "independent_review", "blocking_findings_remaining", True),
    ],
)
def test_evidence_counts_regression_and_review_gates(
    tmp_path, monkeypatch, record, section, key, value
):
    _, physics, _, launcher = fixture(tmp_path, monkeypatch)
    dict(physics=physics, launcher=launcher)[record][section][key] = value
    with pytest.raises(ValueError):
        inputs.sources(tmp_path)


@pytest.mark.parametrize("record", ["checkpoint", "launcher"])
@pytest.mark.parametrize("identity", ["protocol", "code", "physics"])
def test_checkpoint_and_qualification_bind_exact_code_protocol_physics(
    tmp_path, monkeypatch, record, identity
):
    _, _, checkpoint, launcher = fixture(tmp_path, monkeypatch)
    target = dict(checkpoint=checkpoint, launcher=launcher)[record]
    if identity == "physics":
        target["physics_qualification"] = dict(path="wrong", sha256="f" * 64)
    elif identity == "protocol":
        target["execution"]["protocol"]["sha256"] = "f" * 64
    else:
        target["execution"]["code"].reverse()
    with pytest.raises(ValueError):
        inputs.sources(tmp_path)


@pytest.mark.parametrize("mutation", ["missing", "symlink", "directory"])
def test_checkpoint_cannot_be_missing_or_an_uncommitted_alias(tmp_path, monkeypatch, mutation):
    fixture(tmp_path, monkeypatch)
    path = tmp_path / inputs.EXECUTION_CHECKPOINT
    path.unlink()
    if mutation == "symlink":
        path.symlink_to(tmp_path / "evidence/synthetic-launcher.json")
    elif mutation == "directory":
        path.mkdir()
    with pytest.raises(ValueError, match="regular nonsymlink"):
        inputs.sources(tmp_path)


@pytest.mark.parametrize("record", ["physics", "launcher"])
@pytest.mark.parametrize(
    "mutation", ["missing-source", "wrong-source", "duplicate-artifact", "escaped-artifact"]
)
def test_all_qualification_reference_graphs_are_retained(tmp_path, monkeypatch, record, mutation):
    _, physics, _, launcher = fixture(tmp_path, monkeypatch)
    target = dict(physics=physics, launcher=launcher)[record]
    if mutation == "missing-source":
        target["sources"].pop()
    elif mutation == "wrong-source":
        target["sources"][0]["path"] = "unqualified.py"
    elif mutation == "duplicate-artifact":
        target["artifacts"].append(target["artifacts"][0].copy())
    else:
        target["artifacts"][0]["path"] = "../external.json"
    with pytest.raises(ValueError):
        inputs.sources(tmp_path)
