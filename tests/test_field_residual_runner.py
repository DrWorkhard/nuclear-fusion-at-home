"""Metadata and synthetic-run controls; never read the registered field arrays."""

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from fusion_baselines.protected_run_snapshots import SnapshotStore
from scripts import analyze_field_residuals as runner


def ref(name):
    return dict(path="/synthetic/" + name, bytes=1, sha256="0" * 64)


def graph(monkeypatch):
    documents = {}

    def put(name, value):
        reference = ref(name)
        documents[reference["path"]] = value
        return reference

    states, archived, pairs = [], [], []
    for pair_index in range(2):
        constructed, checked = [], []
        case = dict(label=f"reference-n{6 + 2 * pair_index}-N")
        for role in range(2):
            index = pair_index * 2 + role
            state = dict(state_sha256=str(index) * 64, names=["x"], x=[float(index)], case=case)
            states.append(state)
            models, audits, result_levels = [], [], []
            for level in range(6):
                grid = dict(index=level, nphi=64, ntheta=64)
                snapshot = dict(
                    sources={"target": 1},
                    seed_geometry={"seed": pair_index},
                    B2_scale=1.0,
                    target_flux=-1.0,
                    names=["x"],
                )
                model = dict(
                    **state,
                    state=index,
                    level=grid,
                    snapshot=snapshot,
                    arrays=ref(f"s{index}-l{level}.npz"),
                )
                models.append(put(f"s{index}-l{level}.json", model))
                audits.append(
                    dict(**state, level=grid, snapshot=copy.deepcopy(snapshot), metrics={})
                )
                result_levels.append(dict(level=grid))
            constructed.append(dict(state=index, models=models))
            checked.append(
                put(
                    f"audit-s{index}.json",
                    dict(
                        state_sha256=state["state_sha256"],
                        complete=True,
                        numerical_pass=True,
                        models=audits,
                    ),
                )
            )
            archived.append(dict(state_sha256=state["state_sha256"], levels=result_levels))
        producer = put(f"producer-{pair_index}.json", dict(result=dict(states=constructed)))
        audit = put(f"audit-{pair_index}.json", dict(result=dict(states=checked)))
        pairs.append(
            dict(
                pair_index=pair_index,
                producer=dict(complete=True, result=producer),
                audit=dict(complete=True, result=audit),
            )
        )
    study = put("study.json", dict(pairs=pairs))
    study["sha256"] = runner.STUDY_SHA
    manifest = put("manifest.json", dict(states=states))
    review = put("review.json", dict(all_scoped_checks_pass=True, study=study))
    root = put(
        "root.json",
        dict(
            status="completed",
            sources_unchanged=True,
            states=archived,
            references=dict(study=study, inputs=manifest, independent_saved_review=review),
        ),
    )

    def read(reference, references, guard):
        guard()
        references.append(reference)
        return copy.deepcopy(documents[reference["path"]])

    monkeypatch.setattr(runner, "read", read)
    return root, documents


def test_exact_order_and_coverage(monkeypatch):
    root, _ = graph(monkeypatch)
    rows, refs = runner.inputs(root, lambda: None)
    assert [(r["pair_index"], r["level"]) for r in rows] == [
        (pair, level) for pair in range(2) for level in range(4)
    ]
    assert len({r["control"]["reference"]["path"] for r in rows}) == 8
    assert len({r["proposal"]["reference"]["path"] for r in rows}) == 8
    assert refs


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_pair",
        "incomplete_phase",
        "missing_original_level",
        "wrong_order",
        "wrong_names",
        "wrong_state",
        "wrong_snapshot",
        "mismatched_seed",
        "negative_audit",
        "wrong_review",
        "changed_x",
        "wrong_grid",
    ],
)
def test_metadata_rejects(monkeypatch, mutation):
    root, docs = graph(monkeypatch)
    study = docs["/synthetic/study.json"]
    model = docs["/synthetic/s0-l0.json"]
    if mutation == "missing_pair":
        study["pairs"].pop()
    elif mutation == "incomplete_phase":
        study["pairs"][0]["audit"]["complete"] = False
    elif mutation == "missing_original_level":
        docs["/synthetic/producer-0.json"]["result"]["states"][0]["models"].pop()
    elif mutation == "wrong_order":
        study["pairs"].reverse()
    elif mutation == "wrong_names":
        model["names"] = ["z"]
    elif mutation == "wrong_state":
        model["state"] = 1
    elif mutation == "wrong_snapshot":
        model["snapshot"]["B2_scale"] = 2.0
    elif mutation == "mismatched_seed":
        for name in ("/synthetic/s1-l0.json",):
            docs[name]["snapshot"]["seed_geometry"] = {"seed": 9}
        docs["/synthetic/audit-s1.json"]["models"][0]["snapshot"]["seed_geometry"] = {"seed": 9}
    elif mutation == "negative_audit":
        docs["/synthetic/audit-s0.json"]["numerical_pass"] = False
    elif mutation == "wrong_review":
        docs["/synthetic/review.json"]["all_scoped_checks_pass"] = False
    elif mutation == "changed_x":
        model["x"] = [2.0]
    elif mutation == "wrong_grid":
        model["level"] = dict(index=0, nphi=128, ntheta=128)
    with pytest.raises(ValueError):
        runner.inputs(root, lambda: None)


@pytest.mark.parametrize("payload", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'])
def test_bad_json_rejected(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_bytes(payload)
    with pytest.raises(ValueError):
        runner.read(runner.reference(path), [], lambda: None)


def test_bound_hash_and_symlink(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('{"x":1}', encoding="utf-8")
    reference = runner.reference(path)
    assert runner.read(reference, [], lambda: None) == {"x": 1}
    bad = dict(reference, sha256="0" * 64)
    with pytest.raises(ValueError, match="changed"):
        runner.read(bad, [], lambda: None)
    bad = dict(reference, bytes=runner.JSON_LIMIT + 1)
    with pytest.raises(ValueError, match="bounded"):
        runner.read(bad, [], lambda: None)
    link = tmp_path / "link.json"
    link.symlink_to(path)
    with pytest.raises(ValueError, match="regular"):
        runner.read(dict(reference, path=str(link)), [], lambda: None)


def synthetic_run(tmp_path, monkeypatch):
    seed = tmp_path / "evidence"
    seed.mkdir()
    path = seed / "fixed-field-probe-results-v1.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(runner, "RESULT_SHA", hashlib.sha256(b"{}").hexdigest())
    monkeypatch.setattr(runner, "source_identity", lambda root: dict(commit="synthetic"))
    monkeypatch.setattr(
        runner.shutil, "disk_usage", lambda _: type("Disk", (), {"free": 9 * 1024**3})()
    )
    store = SnapshotStore(tmp_path / "arrays")
    normals = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0]])
    weights = np.array([1.0, 2.0])
    a = np.array([[1.0, 0.0, 0.2], [1.0, 0.3, 0.0]])
    b = np.array([[1.0, 0.0, 0.1], [1.0, 0.2, 0.0]])
    metrics = runner.field_residuals.analyze_pair(a, b, normals, weights, 1.0)["metrics"]
    rows = []
    for role, field in (("control", a), ("proposal", b)):
        arrays = store.arrays(
            role,
            dict(
                boundary_B=field,
                boundary_normals=normals,
                boundary_weights=weights,
                boundary_points=np.zeros((2, 3)),
            ),
        )
        model = dict(
            arrays=arrays,
            snapshot=dict(B2_scale=1.0),
            metrics=metrics[role],
            state_sha256=role,
            case=dict(label="synthetic"),
            level=dict(index=0, nphi=1, ntheta=2),
        )
        rows.append(
            dict(reference=runner.reference(path), model=model, checked_metrics=metrics[role])
        )
    records = [
        dict(pair_index=i, level=j, control=copy.deepcopy(rows[0]), proposal=copy.deepcopy(rows[1]))
        for i in range(2)
        for j in range(4)
    ]
    for record in records:
        for role in ("control", "proposal"):
            record[role]["model"]["level"]["index"] = record["level"]
    monkeypatch.setattr(runner, "inputs", lambda ref, guard: (records, [runner.reference(path)]))
    return records


def test_complete_synthetic_run_and_exclusive_output(tmp_path, monkeypatch):
    synthetic_run(tmp_path, monkeypatch)
    output = tmp_path / "run"
    reference = runner.run(tmp_path, output)
    result = json.loads(Path(reference["path"]).read_text())
    assert result["complete"] is True
    assert len(result["comparisons"]) == 8
    assert result["counts"]["new_native_requests"] == 0
    assert all(result[key] is False for key in runner.SCOPE)
    with pytest.raises(FileExistsError):
        runner.run(tmp_path, output)


@pytest.mark.parametrize("failure", ["metric", "checker", "geometry", "source", "bytes"])
def test_run_fails_closed_with_prefix(tmp_path, monkeypatch, failure):
    records = synthetic_run(tmp_path, monkeypatch)
    if failure == "metric":
        records[1]["proposal"]["model"]["metrics"]["JN"] = 1e5
    elif failure == "checker":
        monkeypatch.setattr(
            runner.field_residual_audit,
            "compare",
            lambda *args: (_ for _ in ()).throw(ValueError("audit")),
        )
    elif failure == "geometry":
        actual = runner.read_arrays

        def changed(ref):
            value = actual(ref)
            if "proposal" in ref["path"]:
                value["boundary_normals"][0, 0] = 1.0
            return value

        monkeypatch.setattr(runner, "read_arrays", changed)
    elif failure == "source":
        calls = iter([dict(commit="before"), dict(commit="after")])
        monkeypatch.setattr(runner, "source_identity", lambda _: next(calls))
    elif failure == "bytes":
        monkeypatch.setattr(runner, "JSON_LIMIT", 1)
    with pytest.raises(ValueError):
        runner.run(tmp_path, tmp_path / "failed")
    assert not (tmp_path / "failed/result.json").exists()
