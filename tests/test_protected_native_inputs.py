"""Additive source binding and historical context loading without native work."""

import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from test_protected_cell_contract import context_fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import protected_native_inputs as inputs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def qualification():
    return json.loads((ROOT / inputs.QUALIFICATION).read_text(encoding="utf-8"))


def test_original_synthetic_qualification_metadata_passes_without_mutation():
    value = qualification()
    before = copy.deepcopy(value)
    inputs.qualification_gate(value)
    assert value == before


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", True),
        ("kind", "invented"),
        ("status", "pending"),
        ("synthetic_integration_qualification_pass", 1),
        ("implementation_commit", "other"),
    ],
)
def test_completion_and_schema_required(key, value):
    document = qualification()
    document[key] = value
    with pytest.raises(ValueError):
        inputs.qualification_gate(document)


@pytest.mark.parametrize("key", inputs.QUALIFICATION_LIMITS)
def test_every_original_scope_exclusion_is_preserved(key):
    document = qualification()
    document["limits"][key] = True
    with pytest.raises(ValueError):
        inputs.qualification_gate(document)


@pytest.mark.parametrize(
    "section,key,value",
    [
        ("components", "contract_tests", 178),
        ("components", "cell_tests", 53),
        ("components", "graph_audit_tests", 65),
        ("components", "total_focused_tests", 298),
        ("regression", "exit_code", False),
        ("regression", "passed", 2917),
        ("regression", "failures", 1),
        ("regression", "errors", 1),
        ("regression", "skipped", 1),
        ("regression", "warnings", 0),
        ("historical_compatibility", "historical_contexts_passed", 7),
        ("historical_compatibility", "identity_mutations_rejected", 71),
        ("historical_compatibility", "finite_overcurrent_synthetic_bundles_retained", 7),
        ("historical_compatibility", "individual_input_references_checked", 27),
        ("historical_compatibility", "native_requests", False),
        ("historical_compatibility", "equilibrium_solves", 1),
        ("historical_compatibility", "geometry_certificate_calculations", 1),
        ("historical_compatibility", "full_source_graph_re_admitted", True),
    ],
)
def test_each_qualification_count_and_read_only_limit(section, key, value):
    document = qualification()
    document[section][key] = value
    with pytest.raises(ValueError):
        inputs.qualification_gate(document)


@pytest.mark.parametrize("section", ["sources", "artifacts"])
@pytest.mark.parametrize("mutation", ["missing", "order", "renamed", "extra", "not-record"])
def test_all_source_and_artifact_records_remain_exact(section, mutation):
    document = qualification()
    if mutation == "missing":
        document[section].pop()
    elif mutation == "order":
        document[section].reverse()
    elif mutation == "renamed":
        document[section][0]["path"] = "../../external-file"
    elif mutation == "extra":
        document[section][0]["unbound"] = True
    else:
        document[section][0] = None
    with pytest.raises(ValueError):
        inputs.qualification_gate(document)


def wire_sources(tmp_path, monkeypatch):
    doc, calls = qualification(), dict(committed=[], checked=[], historical=[])
    cell_sources = dict(matrix=inputs.previous.matrix(), marker="qualified cell sources")
    qref = dict(path=str(tmp_path / inputs.QUALIFICATION), sha256=inputs.QUALIFICATION_HASH)
    monkeypatch.setattr(inputs.previous, "sources", lambda root: copy.deepcopy(cell_sources))

    def historical(*args):
        calls["historical"].append(args)
        return qref.copy()

    monkeypatch.setattr(inputs.previous.previous, "historical", historical)
    monkeypatch.setattr(inputs, "read", lambda ref: copy.deepcopy(doc))
    monkeypatch.setattr(inputs, "checked", lambda ref: calls["checked"].append(ref.copy()))
    monkeypatch.setattr(
        inputs, "require_committed", lambda root, path: calls["committed"].append((root, path))
    )
    monkeypatch.setattr(inputs, "reference", lambda path: dict(path=str(path), sha256="b" * 64))
    monkeypatch.setattr(inputs, "git_state", lambda root: dict(commit="new plumbing"))
    return doc, calls, cell_sources


def test_complete_additive_binding_includes_all_qualified_and_new_sources(tmp_path, monkeypatch):
    document, calls, old = wire_sources(tmp_path, monkeypatch)
    source = inputs.sources(tmp_path)
    assert source["cell_sources"] == old
    assert calls["historical"] == [
        (tmp_path, inputs.QUALIFICATION, inputs.QUALIFICATION_REVISION, inputs.QUALIFICATION_HASH)
    ]
    assert len(calls["checked"]) == 41
    assert calls["committed"] == [
        (tmp_path, tmp_path / name)
        for name in (*inputs.QUALIFIED_NAMES, inputs.PROTOCOL, *inputs.CODE)
    ]
    assert [row["path"] for row in source["plumbing"]["code"]] == [
        str(tmp_path / name) for name in inputs.CODE
    ]
    assert len(source["plumbing"]["qualified_sources"]) == 19
    assert len(source["plumbing"]["qualification_artifacts"]) == 22
    assert any(row.get("junit", {}).get("failures", 0) > 0 for row in document["artifacts"])


@pytest.mark.parametrize(
    "section,index",
    [("sources", 0), ("sources", 18), ("artifacts", 0), ("artifacts", 17), ("artifacts", 21)],
)
def test_missing_or_changed_qualification_files_block_source_admission(
    tmp_path, monkeypatch, section, index
):
    document, _, _ = wire_sources(tmp_path, monkeypatch)
    bad = str(tmp_path / document[section][index]["path"])

    def check(ref):
        if ref["path"] == bad:
            raise ValueError("missing or changed qualified bytes")

    monkeypatch.setattr(inputs, "checked", check)
    with pytest.raises(ValueError, match="qualified bytes"):
        inputs.sources(tmp_path)


@pytest.mark.parametrize("name", inputs.CODE)
def test_every_new_component_must_be_committed(tmp_path, monkeypatch, name):
    wire_sources(tmp_path, monkeypatch)

    def committed(root, path):
        if path == tmp_path / name:
            raise ValueError("uncommitted component")

    monkeypatch.setattr(inputs, "require_committed", committed)
    with pytest.raises(ValueError, match="uncommitted"):
        inputs.sources(tmp_path)


def saved_context(tmp_path, case):
    context = context_fixture(case["nbase"], case["method"], case["target"])

    def ref(path):
        data = path.read_bytes()
        return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))

    def save(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
        return ref(path)

    seedref = save("seed.json", context["seed"])
    snapshotref = save("snapshot.json", context["historical_seed"]["snapshot"])
    path = tmp_path / "original-compressed-arrays.npz"
    np.savez_compressed(path, **context["historical_seed"]["arrays"])
    arraysref = ref(path)
    state = context["historical_seed"]["state"]
    row = dict(
        status="completed",
        kind="qualification",
        index=0,
        label="seed",
        method=case["method"],
        model_id=f"qualification-{case['method']}",
        operation_id=f"qualification-{case['method']}-00",
        x=state["x"],
        J=state["value"],
        gradient=state["gradient"],
        metrics=state["metrics"],
        snapshot=snapshotref,
        arrays=arraysref,
    )
    rowref = save("operation.json", row)
    reports = [{} for _ in range(12)]
    reports[context["geometry_report_index"]] = context["geometry_report"]
    auditref = save("geometry-audit.json", dict(sets=reports))
    source = dict(
        matrix=inputs.previous.matrix(),
        geometry=dict(audit=auditref),
        seeds={
            case["seed_label"]: dict(
                snapshot=seedref, geometry_report_index=context["geometry_report_index"]
            )
        },
        targets=context["seed"]["sources"],
        normalization={key: dict(B2_scale=2.0, archives=[]) for key in ("reference", "selected")},
        target_archives={key: {} for key in ("reference", "selected")},
        startup_seed_bundles={
            case["label"]: dict(operation=rowref, snapshot=snapshotref, arrays=arraysref)
        },
    )
    source["startup"] = dict(
        source={
            key: copy.deepcopy(source[key])
            for key in ("targets", "normalization", "target_archives")
        }
    )
    manifest = dict(cell_sources=source, plumbing={}, repository=dict(commit="synthetic"))
    context.update(
        seed_reference=seedref, historical_seed_reference=rowref, geometry_audit_reference=auditref
    )
    return context, manifest


@pytest.mark.parametrize("case", inputs.previous.matrix(), ids=lambda row: row["label"])
def test_all_eight_contexts_load_original_compressed_arrays_without_native_calls(tmp_path, case):
    expected, manifest = saved_context(tmp_path, case)
    actual = inputs.build_context(manifest, case)
    assert inputs.contract.context_metadata(actual) == inputs.contract.context_metadata(expected)
    for key, array in actual["historical_seed"]["arrays"].items():
        np.testing.assert_array_equal(array, expected["historical_seed"]["arrays"][key])
    actual["seed"]["base_coefficients"][0][0][0] += 1
    assert expected["seed"]["base_coefficients"][0][0][0] == 1.0


@pytest.mark.parametrize(
    "mutation",
    [
        "case-bool",
        "matrix",
        "targets",
        "normalization",
        "archives",
        "index",
        "operation-ref",
        "snapshot-ref",
        "array-ref",
        "arrays-changed",
        "snapshot-changed",
    ],
)
def test_context_source_changes_fail_closed_before_any_native_work(tmp_path, mutation):
    case = inputs.previous.matrix()[0]
    _, manifest = saved_context(tmp_path, case)
    source = manifest["cell_sources"]
    if mutation == "case-bool":
        case["nbase"] = 6.0
    elif mutation == "matrix":
        source["matrix"].reverse()
    elif mutation == "targets":
        source["targets"]["reference"]["input"]["sha256"] = "f" * 64
    elif mutation == "normalization":
        source["normalization"]["reference"]["B2_scale"] = 3.0
    elif mutation == "archives":
        source["target_archives"]["reference"]["changed"] = True
    elif mutation == "index":
        source["seeds"][case["seed_label"]]["geometry_report_index"] = 3.0
    elif mutation in ("operation-ref", "snapshot-ref", "array-ref"):
        key = {"operation-ref": "operation", "snapshot-ref": "snapshot", "array-ref": "arrays"}[
            mutation
        ]
        source["startup_seed_bundles"][case["label"]][key]["sha256"] = "f" * 64
    else:
        path = tmp_path / (
            "original-compressed-arrays.npz" if mutation == "arrays-changed" else "snapshot.json"
        )
        path.write_bytes(b"changed historical bytes")
    with pytest.raises(ValueError):
        inputs.build_context(manifest, case)
