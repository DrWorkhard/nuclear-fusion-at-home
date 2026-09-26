"""Tiny local Git fixtures; no project archive admission or native evaluation."""

import copy
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import protected_fine_execution_inputs as gate  # noqa: E402


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    git(root, "init", "-q")
    git(root, "config", "user.email", "synthetic@example.invalid")
    git(root, "config", "user.name", "Synthetic Gate Test")
    monkeypatch.setattr(gate, "CODE", ("src/new_fine.py", "scripts/new_gate.py"))
    for name in (gate.PROTOCOL, *gate.CODE):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# synthetic qualified source\n", encoding="utf-8")
    junit = root / "artifacts/full.xml"
    junit.parent.mkdir()
    junit.write_text(
        '<testsuites><testsuite tests="3488" failures="0" errors="0" skipped="0">'
        + "".join(f'<testcase classname="synthetic" name="case{i}"/>' for i in range(3488))
        + "</testsuite></testsuites>",
        encoding="utf-8",
    )
    git(root, "add", ".")
    git(root, "commit", "-qm", "synthetic implementation")
    implementation = git(root, "rev-parse", "HEAD")
    monkeypatch.setattr(gate, "REGISTRATION_COMMIT", implementation)
    monkeypatch.setattr(
        gate, "REGISTRATION_SHA256", gate.inputs._reference(root / gate.PROTOCOL)["sha256"]
    )
    ref = dict(path="/synthetic/old.json", sha256="a" * 64, bytes=1)
    coarse = dict(evidence=ref, summary=ref, source_before=ref, source_after=ref, cases=[ref] * 8)
    historical = dict(repository=dict(commit="old-metadata-kept", dirty=False))

    def archive(_root):
        assert _root == root
        return dict(
            copy.deepcopy(coarse),
            archived_source=copy.deepcopy(historical),
            current_provenance=gate.inputs._repository(root),
        )

    monkeypatch.setattr(gate.inputs, "archive", archive)
    execution = dict(
        protocol=gate.inputs._reference(root / gate.PROTOCOL),
        code=[gate.inputs._reference(root / name) for name in gate.CODE],
    )
    names = (gate.PROTOCOL, *gate.CODE)

    def relative(p):
        return dict(gate.inputs._reference(p), path=p.relative_to(root).as_posix())

    artifact = relative(junit)
    qualification = dict(
        schema_version=1,
        kind="protected-fine-implementation-qualification",
        status="completed",
        qualification_pass=True,
        implementation_commit=implementation,
        execution=execution,
        coarse=coarse,
        sources=[relative(root / n) for n in names],
        artifacts=[artifact],
        regression=dict(
            exit_code=0,
            passed=3488,
            failures=0,
            errors=0,
            skipped=0,
            full_committed_suite=True,
            clean_worktree=True,
            execution_commit=implementation,
            junit=artifact,
        ),
        independent_review=dict(internal=True, blocking_findings_remaining=False),
        limits=gate.SCOPE.copy(),
    )
    path = write(root, gate.QUALIFICATION, qualification)
    git(root, "add", ".")
    git(root, "commit", "-qm", "synthetic qualification")
    checkpoint = dict(
        schema_version=1,
        kind="protected-fine-execution-checkpoint",
        status="ready",
        execution_checkpoint_pass=True,
        execution=execution,
        coarse=coarse,
        qualification=gate.inputs._reference(path),
        limits=gate.SCOPE.copy(),
    )
    write(root, gate.CHECKPOINT, checkpoint)
    git(root, "add", ".")
    git(root, "commit", "-qm", "synthetic execution permission")

    def replace(which, mutate):
        name = gate.QUALIFICATION if which == "qualification" else gate.CHECKPOINT
        value = json.loads((root / name).read_text(encoding="utf-8"))
        mutate(value)
        write(root, name, value)
        if which == "qualification":
            current = json.loads((root / gate.CHECKPOINT).read_text(encoding="utf-8"))
            current["qualification"] = gate.inputs._reference(root / gate.QUALIFICATION)
            write(root, gate.CHECKPOINT, current)
        git(root, "add", ".")
        git(root, "commit", "-qm", "synthetic mutated evidence")

    return SimpleNamespace(
        root=root,
        replace=replace,
        archive=archive,
        historical=historical,
        implementation=implementation,
        junit=junit,
    )


def test_new_commit_provenance_is_separate_from_frozen_history(prepared):
    p = prepared
    first = gate.sources(p.root)
    assert first["fine_execution_authorized"] is True
    assert all(first[key] is False for key in gate.SCOPE)
    assert first["archive"]["archived_source"] == p.historical
    assert first["repository"]["commit"] != p.implementation
    assert first["archive"]["current_provenance"] == first["repository"]
    write(p.root, "overview.json", dict(documentation_only=True))
    git(p.root, "add", ".")
    git(p.root, "commit", "-qm", "synthetic new documentation commit")
    second = gate.sources(p.root)
    assert first["repository"] != second["repository"]
    assert first["archive"]["archived_source"] == second["archive"]["archived_source"]
    assert second == gate.sources(p.root)


@pytest.mark.parametrize("name", [gate.QUALIFICATION, gate.CHECKPOINT])
def test_missing_permission_closes_before_archive_work(prepared, monkeypatch, name):
    # Move only this disposable synthetic fixture's evidence, never project evidence.
    path = prepared.root / name
    path.rename(path.with_suffix(".absent"))
    git(prepared.root, "add", ".")
    git(prepared.root, "commit", "-qm", "synthetic committed missing permission")
    monkeypatch.setattr(gate.inputs, "archive", lambda *a: pytest.fail("premature archive work"))
    with pytest.raises(ValueError):
        gate.sources(prepared.root)


@pytest.mark.parametrize(
    "key,value",
    [
        ("qualification_pass", False),
        ("schema_version", True),
        ("status", "pending"),
        ("implementation_commit", "a" * 39),
        ("extra", False),
        ("independent_review", {"internal": True, "blocking_findings_remaining": True}),
        ("limits", {}),
    ],
)
def test_unqualified_or_malformed_record_rejected(prepared, key, value):
    prepared.replace("qualification", lambda d: d.update({key: value}))
    with pytest.raises(ValueError):
        gate.sources(prepared.root)


@pytest.mark.parametrize(
    "key,value",
    [
        ("passed", True),
        ("passed", 3487),
        ("passed", 3489),
        ("errors", 1),
        ("failures", 1),
        ("skipped", 1),
        ("exit_code", 1),
        ("clean_worktree", False),
        ("full_committed_suite", False),
        ("execution_commit", "a" * 40),
        ("junit", {}),
    ],
)
def test_fabricated_or_incomplete_regression_rejected(prepared, key, value):
    prepared.replace("qualification", lambda d: d["regression"].update({key: value}))
    with pytest.raises(ValueError):
        gate.sources(prepared.root)


@pytest.mark.parametrize(
    "mutation",
    [
        "sources-missing",
        "sources-order",
        "artifact-empty",
        "outside",
        "checkpoint-source",
        "checkpoint-coarse",
        "permission",
    ],
)
def test_exact_qualification_source_artifact_and_permission_links(prepared, mutation):
    def change(d):
        if mutation == "sources-missing":
            d["sources"].pop()
        elif mutation == "sources-order":
            d["sources"].reverse()
        elif mutation == "artifact-empty":
            d["artifacts"] = []
        elif mutation == "outside":
            d["artifacts"][0]["path"] = "../outside.xml"
        elif mutation == "checkpoint-source":
            d["execution"]["code"] = []
        elif mutation == "checkpoint-coarse":
            d["coarse"]["cases"] = []
        else:
            d["execution_checkpoint_pass"] = False

    prepared.replace(
        "checkpoint"
        if mutation.startswith("checkpoint") or mutation == "permission"
        else "qualification",
        change,
    )
    with pytest.raises((ValueError, FileNotFoundError)):
        gate.sources(prepared.root)


def test_junit_declared_counts_cannot_hide_missing_actual_cases(prepared):
    p = prepared
    p.junit.write_text(
        '<testsuites><testsuite tests="3488" failures="0" errors="0" skipped="0">'
        '<testcase name="only-one"/></testsuite></testsuites>',
        encoding="utf-8",
    )

    def mutate(d):
        row = dict(gate.inputs._reference(p.junit), path="artifacts/full.xml")
        d["artifacts"] = [row]
        d["regression"]["junit"] = row

    p.replace("qualification", mutate)
    with pytest.raises(ValueError, match="declared/observed"):
        gate.sources(p.root)


@pytest.mark.parametrize(
    "mutation", ["aggregate", "failure", "hidden-case", "nested-suite", "doctype"]
)
def test_junit_nested_and_aggregate_misrepresentation_rejected(prepared, mutation):
    p = prepared
    original = p.junit.read_text(encoding="utf-8")
    if mutation == "aggregate":
        changed = original.replace("<testsuites>", '<testsuites tests="1">')
    elif mutation == "failure":
        changed = original.replace('name="case0"/>', 'name="case0"><failure/></testcase>')
    elif mutation == "hidden-case":
        changed = original.replace("</testsuites>", "<extra><testcase/></extra></testsuites>")
    elif mutation == "nested-suite":
        changed = original.replace("</testsuite>", "<testsuite/></testsuite>")
    else:
        changed = "<!DOCTYPE testsuites []>" + original
    p.junit.write_text(changed, encoding="utf-8")

    def mutate(d):
        row = dict(gate.inputs._reference(p.junit), path="artifacts/full.xml")
        d["artifacts"] = [row]
        d["regression"]["junit"] = row

    p.replace("qualification", mutate)
    with pytest.raises(ValueError):
        gate.sources(p.root)


def test_registered_protocol_cannot_change_in_a_new_clean_commit(prepared):
    (prepared.root / gate.PROTOCOL).write_text("# changed registration\n", encoding="utf-8")
    git(prepared.root, "add", ".")
    git(prepared.root, "commit", "-qm", "synthetic changed registration")
    with pytest.raises(ValueError, match="committed bytes"):
        gate.sources(prepared.root)


def test_repository_changed_during_archive_gate_cannot_authorize_execution(prepared, monkeypatch):
    def archive(root):
        result = prepared.archive(root)
        write(root, "drift.json", dict(synthetic=True))
        git(root, "add", ".")
        git(root, "commit", "-qm", "synthetic during-admission drift")
        return result

    monkeypatch.setattr(gate.inputs, "archive", archive)
    with pytest.raises(ValueError, match="during admission"):
        gate.sources(prepared.root)


def test_changed_qualified_source_cannot_be_reauthorized_by_new_hash_only(prepared):
    p = prepared
    (p.root / gate.CODE[0]).write_text("# changed implementation\n", encoding="utf-8")

    def mutate(d):
        reference = gate.inputs._reference(p.root / gate.CODE[0])
        d["sources"][1] = dict(reference, path=gate.CODE[0])
        d["execution"]["code"][0] = reference

    p.replace("qualification", mutate)
    with pytest.raises(ValueError, match="committed bytes"):
        gate.sources(p.root)


@pytest.mark.parametrize("dirty", ["tracked", "untracked"])
def test_any_current_dirty_state_closes_gate(prepared, dirty):
    name = gate.CODE[0] if dirty == "tracked" else "untracked.txt"
    (prepared.root / name).write_text("dirty\n", encoding="utf-8")
    with pytest.raises(ValueError, match="clean"):
        gate.sources(prepared.root)


def test_archive_with_stale_fine_provenance_rejected(prepared, monkeypatch):
    stale = prepared.archive(prepared.root)
    stale["current_provenance"]["commit"] = prepared.implementation
    monkeypatch.setattr(gate.inputs, "archive", lambda root: stale)
    with pytest.raises(ValueError, match="current fine repository"):
        gate.sources(prepared.root)


def test_context_delegates_only_private_archive_and_case(prepared, monkeypatch):
    source = gate.sources(prepared.root)
    before = copy.deepcopy(source)
    case = dict(label="synthetic")

    def build(archive, descriptor):
        archive.clear()
        descriptor.clear()
        return dict(synthetic=True)

    monkeypatch.setattr(gate.inputs, "build_context", build)
    assert gate.build_context(source, case) == dict(synthetic=True)
    assert source == before and case == dict(label="synthetic")
    with pytest.raises(ValueError):
        gate.build_context({}, case)
