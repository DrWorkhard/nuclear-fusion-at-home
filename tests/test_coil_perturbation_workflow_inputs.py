"""Pure source/qualification controls; no new candidate geometry or fields."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import coil_perturbation_workflow_inputs as binder  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def fixture(root):
    qualification = json.loads((ROOT / binder.QUALIFICATION).read_text())
    records = [
        dict(path=str(root / row["path"]), sha256=row["sha256"]) for row in qualification["sources"]
    ]
    source = dict(
        code=records[:-1],
        protocol=records[-1],
        matrix=binder.matrix(),
        scope=binder.SCOPE.copy(),
        repository=dict(commit="current", dirty=False),
    )
    return qualification, source


def test_complete_primitive_qualification_remains_bounded_and_does_not_mutate(tmp_path):
    documents = fixture(tmp_path)
    before = copy.deepcopy(documents)
    binder.qualification_gate(*documents, tmp_path)
    assert documents == before


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", True),
        ("phase", "invented"),
        ("tests", 200),
        ("failures", 1),
        ("errors", 1),
        ("skipped", 1),
        ("warnings", 0),
        ("producer_to_independent_synthetic_cross_cases", 0),
        ("saved_predecessor_source_replay_pass", 1),
        ("new_tests", dict(producer=55)),
    ],
)
def test_incomplete_or_relabelled_qualification_is_rejected(tmp_path, key, value):
    qualification, source = fixture(tmp_path)
    qualification[key] = value
    with pytest.raises(ValueError):
        binder.qualification_gate(qualification, source, tmp_path)


@pytest.mark.parametrize(
    "key",
    [
        "whole_workflow_qualified",
        "real_52_state_matrix_executed",
        "search_allowed",
        "field_pass",
        "transfer_pass",
        "step4_pass",
    ],
)
def test_primitive_certificate_cannot_be_promoted(tmp_path, key):
    qualification, source = fixture(tmp_path)
    qualification["scope"][key] = True
    with pytest.raises(ValueError):
        binder.qualification_gate(qualification, source, tmp_path)


@pytest.mark.parametrize("mutation", ["hash", "path", "order", "missing", "protocol", "keys"])
def test_current_primitive_graph_must_match_exact_qualification(tmp_path, mutation):
    qualification, source = fixture(tmp_path)
    if mutation == "hash":
        source["code"][0]["sha256"] = "0" * 64
    elif mutation == "path":
        source["code"][0]["path"] = "/elsewhere/producer.py"
    elif mutation == "order":
        source["code"].reverse()
    elif mutation == "missing":
        source["code"].pop()
    elif mutation == "protocol":
        source["protocol"]["sha256"] = "f" * 64
    else:
        qualification["sources"][0]["extra"] = "not original"
    with pytest.raises(ValueError):
        binder.qualification_gate(qualification, source, tmp_path)


@pytest.mark.parametrize("mutation", ["class", "field", "type"])
def test_matrix_and_scope_cannot_change(tmp_path, mutation):
    qualification, source = fixture(tmp_path)
    if mutation == "class":
        source["matrix"].reverse()
    elif mutation == "field":
        source["scope"]["field_calls"] = 1
    else:
        source["scope"]["field_calls"] = False
    with pytest.raises(ValueError):
        binder.qualification_gate(qualification, source, tmp_path)


def test_wrapper_keeps_historical_binding_and_requires_every_new_file(tmp_path, monkeypatch):
    qualification, source = fixture(tmp_path)
    calls = []
    qref = dict(path=str(tmp_path / binder.QUALIFICATION), sha256=binder.QUALIFICATION_HASH)
    monkeypatch.setattr(binder.primitive, "sources", lambda root: copy.deepcopy(source))

    def historical(*args):
        assert args == (
            tmp_path,
            binder.QUALIFICATION,
            binder.QUALIFICATION_REVISION,
            binder.QUALIFICATION_HASH,
        )
        return qref

    monkeypatch.setattr(binder.primitive.previous, "historical", historical)
    monkeypatch.setattr(binder, "read", lambda ref: qualification if ref == qref else None)
    monkeypatch.setattr(binder, "require_committed", lambda root, path: calls.append((root, path)))
    monkeypatch.setattr(binder, "reference", lambda p: dict(path=str(p), sha256="a" * 64))
    checked_refs = []
    monkeypatch.setattr(binder, "checked", lambda ref: checked_refs.append(ref))
    actual = binder.sources(tmp_path)
    assert {k: actual[k] for k in source} == source
    assert actual["primitive_qualification"] == qref
    assert actual["primitive_regression"] == {
        "path": str(tmp_path / binder.REGRESSION),
        "sha256": qualification["junit"]["sha256"],
    }
    assert checked_refs == [actual["primitive_regression"]]
    assert [r["path"] for r in actual["workflow_code"]] == [str(tmp_path / p) for p in binder.CODE]
    assert calls == [(tmp_path, tmp_path / name) for name in binder.CODE]
    assert len(binder.CODE) == len(set(binder.CODE)) == 10


def test_uncommitted_workflow_file_blocks_source_admission(tmp_path, monkeypatch):
    qualification, source = fixture(tmp_path)
    monkeypatch.setattr(binder.primitive, "sources", lambda root: source)
    monkeypatch.setattr(binder.primitive.previous, "historical", lambda *args: {})
    monkeypatch.setattr(binder, "read", lambda ref: qualification)
    monkeypatch.setattr(binder, "checked", lambda ref: None)

    def changed(*args):
        raise ValueError("uncommitted")

    monkeypatch.setattr(binder, "require_committed", changed)
    with pytest.raises(ValueError, match="uncommitted"):
        binder.sources(tmp_path)


@pytest.mark.parametrize("bad", [None, {}, {"path": "/unrelated", "sha256": "0" * 64}])
def test_missing_or_relabelled_regression_reference_rejected(tmp_path, bad):
    qualification, source = fixture(tmp_path)
    qualification["junit"] = bad
    with pytest.raises(ValueError, match="regression"):
        binder.qualification_gate(qualification, source, tmp_path)


def test_missing_or_changed_regression_blocks_workflow(tmp_path, monkeypatch):
    qualification, source = fixture(tmp_path)
    monkeypatch.setattr(binder.primitive, "sources", lambda root: source)
    monkeypatch.setattr(binder.primitive.previous, "historical", lambda *args: {})
    monkeypatch.setattr(binder, "read", lambda ref: qualification)

    def changed(ref):
        assert ref["path"] == str(tmp_path / binder.REGRESSION)
        raise ValueError("changed regression bytes")

    monkeypatch.setattr(binder, "checked", changed)
    with pytest.raises(ValueError, match="changed regression"):
        binder.sources(tmp_path)
