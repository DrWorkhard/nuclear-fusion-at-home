"""Synthetic fine geometry composition; no project data or native field calls."""

import copy
import json

import numpy as np
import pytest
from test_coil_perturbation_audit import synthetic_seed
from test_protected_cell_contract import bundle_fixture, context_fixture

from fusion_baselines import coil_perturbation_audit as mathematical
from fusion_baselines import protected_cell_contract as contract
from fusion_baselines import protected_fine_geometry as fine
from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_fine_geometry_codec import encode_geometry
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_arrays


def fixture(directory, nbase=6, method="N", target="reference", changed=True):
    store = SnapshotStore(directory)
    original = context_fixture(nbase, method, target)
    seed, report = synthetic_seed(nbase)
    seed, report = json.loads(json.dumps([seed, report]))
    targets = {}
    for name, minor in (("reference", 0.03), ("selected", 0.025)):
        data = dict(
            nfp=2,
            lasym=False,
            mpol=2,
            ntor=0,
            rbs=[],
            zbc=[],
            rbc=[dict(m=0, n=0, value=1.2), dict(m=1, n=0, value=minor)],
            zbs=[dict(m=1, n=0, value=minor)],
        )
        reference = store.json("surface-" + name, data)
        targets[name] = dict(
            input={k: reference[k] for k in ("path", "sha256")},
            wout=original["seed"]["sources"][name]["wout"],
        )
    seed["sources"] = copy.deepcopy(targets)
    original.update(seed=seed, geometry_report=report, target_sources=targets[target])
    anchor = original["historical_seed"]["snapshot"]
    anchor.update(
        seed_geometry=copy.deepcopy(seed),
        sources=copy.deepcopy(targets[target]),
        base_coefficients=copy.deepcopy(seed["base_coefficients"]),
    )
    original["historical_seed"] = bundle_fixture(original)
    x = np.asarray(seed["base_coefficients"]).ravel().copy()
    if changed:
        x[1] += 1e-5
    selected = bundle_fixture(original, x=x)
    result = mathematical.independent_certificate(
        seed, report, x.reshape(np.shape(seed["base_coefficients"]))
    )
    selected["certificate"] = dict(
        case=copy.deepcopy(original["case"]),
        phase="trial",
        operation_id="trial/certificate/003",
        x=x.tolist(),
        state_sha256=contract.coordinate_identity(original, x),
        original_seed=copy.deepcopy(original["seed_reference"]),
        geometry_report=copy.deepcopy(original["geometry_audit_reference"]),
        geometry_report_index=original["geometry_report_index"],
        result=result,
    )
    context = dict(
        case=copy.deepcopy(original["case"]),
        original_context=original,
        selected=selected,
        coarse={},
    )
    archive = dict(
        archived_source=dict(
            physics_sources=dict(
                native_sources=dict(cell_sources=dict(targets=copy.deepcopy(targets)))
            )
        )
    )
    return context, archive


def produce(context, archive, directory):
    producer = fine.FineGeometry(context, archive, lambda: None)
    store = SnapshotStore(directory)
    coefficients = np.asarray(context["selected"]["snapshot"]["base_coefficients"])
    records = []
    for i, level in enumerate(plan.geometry_levels()):
        before = producer.work()["sampling"]
        raw = producer.sample(coefficients, level)
        after = producer.work()["sampling"]
        work = {k: {n: after[k][n] - before[k][n] for n in after[k]} for k in after}
        arrays, codec = encode_geometry(raw, context["case"], level)
        records.append(
            dict(
                level=level,
                arrays=store.arrays(f"grid-{i}", arrays),
                codec=codec,
                sampling_work=work,
            )
        )
    return producer, records


@pytest.fixture(scope="module", params=[6, 8])
def completed(request, tmp_path_factory):
    path = tmp_path_factory.mktemp(f"synthetic-fine-geometry-{request.param}")
    context, archive = fixture(
        path / "sources",
        request.param,
        method="N" if request.param == 6 else "V",
        target="reference" if request.param == 6 else "selected",
    )
    producer, records = produce(context, archive, path / "raw")
    return context, archive, producer, records


def test_complete_independent_roundtrip_all_pairs_grids_surfaces_and_work(completed):
    context, archive, producer, records = completed
    result = fine.audit_geometry(context, archive, records, lambda: None)
    n = context["case"]["nbase"]
    assert producer.work() == result["producer_work"] == fine.expected_work(context["case"])
    assert result["geometry_consistency"] is result["continuous_geometry_pass"] is True
    assert result["sampled_geometry_pass"] is True
    assert result["independent_work"] == dict(
        certificate_recomputations=1, surface_reconstructions=2, direct_grids=4
    )
    assert all(result[k] is False for k in fine.SCOPE)
    assert result["field_calls"] == result["gradient_calls"] == result["equilibrium_solves"] == 0
    assert [row["level"] for row in result["grids"]] == plan.geometry_levels()
    for row, level in zip(result["grids"], plan.geometry_levels(), strict=True):
        report = row["independent"]
        assert report["coil_pairs_checked"] == (276 if n == 6 else 496)
        assert report["cp_distances_checked"] == 2 * 4 * n * level["ncoil"]
        assert report["comparison_tolerance"]["bound_enclosure_tolerance"] == 0
    expected = (202752, 135168, 777216) if n == 6 else (270336, 180224, 1396736)
    assert [
        producer.work()["sampling"][k]["points_completed"] for k in ("fourier", "cp", "cc")
    ] == list(expected)
    assert [producer.work()["sampling"][k]["completed"] for k in ("fourier", "cp", "cc")] == [
        12,
        8,
        (1104 if n == 6 else 1984),
    ]


@pytest.mark.parametrize("case", plan.cases(), ids=lambda row: row["label"])
@pytest.mark.parametrize("changed", [True, False])
def test_all_cases_and_changed_or_fallback_coordinates(tmp_path, case, changed):
    context, archive = fixture(
        tmp_path / "sources", case["nbase"], case["method"], case["target"], changed
    )
    producer = fine.FineGeometry(context, archive, lambda: None)
    coefficients = np.asarray(context["selected"]["snapshot"]["base_coefficients"])
    raw = producer.sample(coefficients, plan.geometry_levels()[0])
    assert raw["curvature_available"].dtype == np.dtype(bool)
    assert raw["pairs"].dtype == raw["pair_witnesses"].dtype == np.dtype(np.int64)
    assert raw["cp_reference_indices"].dtype.kind in "iu"
    assert producer.work()["direct_grids"] == dict(attempted=1, completed=1)


@pytest.mark.parametrize(
    "change",
    [
        "case",
        "source",
        "other-target",
        "coordinate",
        "snapshot-current",
        "array-current",
        "certificate-x",
        "certificate-seed",
        "certificate-hash",
        "certificate-report",
        "certificate-case",
        "certificate-positive",
    ],
)
def test_identity_mutations_fail_before_sampling(completed, monkeypatch, change):
    context, archive = copy.deepcopy(completed[:2])
    if change == "case":
        context["case"]["method"] = "wrong"
    elif change == "source":
        archive["archived_source"]["physics_sources"]["native_sources"]["cell_sources"]["targets"][
            "reference"
        ]["input"]["sha256"] = "0" * 64
    elif change == "other-target":
        context["original_context"]["seed"]["sources"]["selected"]["input"]["sha256"] = "0" * 64
    elif change == "coordinate":
        context["selected"]["state"]["x"][0] += 0.01
    elif change == "snapshot-current":
        context["selected"]["snapshot"]["physical"][0]["current"] += 1
    elif change == "array-current":
        context["selected"]["arrays"]["coil_currents"][0] += 1
    else:
        key = {
            "certificate-x": "x",
            "certificate-seed": "original_seed",
            "certificate-hash": "state_sha256",
            "certificate-report": "geometry_report",
            "certificate-case": "case",
        }.get(change)
        if change == "certificate-positive":
            context["selected"]["certificate"]["result"]["certified"] = False
        elif key == "x":
            context["selected"]["certificate"][key][0] += 0.01
        elif key == "state_sha256":
            context["selected"]["certificate"][key] = "0" * 64
        elif key == "case":
            context["selected"]["certificate"][key]["target"] = "wrong"
        else:
            context["selected"]["certificate"][key]["sha256"] = "0" * 64
    monkeypatch.setattr(
        fine.sampling, "surface_points", lambda *a: pytest.fail("premature sampling")
    )
    with pytest.raises(ValueError):
        fine.FineGeometry(context, archive, lambda: None)


@pytest.mark.parametrize(
    "change", ["missing", "extra", "order", "level-type", "work", "descriptor"]
)
def test_incomplete_or_changed_saved_graph_rejected(completed, change):
    context, archive, _, records = completed
    records = copy.deepcopy(records)
    if change == "missing":
        records.pop()
    elif change == "extra":
        records[0]["extra"] = False
    elif change == "order":
        records[0], records[1] = records[1], records[0]
    elif change == "level-type":
        records[0]["level"]["ncoil"] = 256.0
    elif change == "work":
        records[0]["sampling_work"]["cc"]["completed"] -= 1
    else:
        records[0]["codec"]["shape"][0] = 1
    with pytest.raises(ValueError):
        fine.audit_geometry(context, archive, records, lambda: None)


@pytest.mark.parametrize(
    "key",
    [
        "pairs",
        "pair_witnesses",
        "cp_reference_indices",
        "cp_selected_indices",
        "curvature_available",
        "speed",
        "pair_distances",
        "cp_reference_distances",
        "cp_selected_distances",
        "parameters",
    ],
)
def test_saved_raw_mutations_rejected(completed, tmp_path, key):
    context, archive, _, records = completed
    records = copy.deepcopy(records)
    raw = {key: value.copy() for key, value in read_arrays(records[0]["arrays"]).items()}
    if key == "curvature_available":
        raw[key][0, 0] = 2
    elif key in ("pairs", "pair_witnesses", "cp_reference_indices", "cp_selected_indices"):
        raw[key] = raw[key].astype(float)
    else:
        raw[key].flat[0] += 1e-3
    records[0]["arrays"] = SnapshotStore(tmp_path / "tampered").arrays("grid", raw)
    with pytest.raises(ValueError):
        fine.audit_geometry(context, archive, records, lambda: None)


def test_independent_auditor_never_calls_producer(completed, monkeypatch):
    context, archive, _, records = completed
    monkeypatch.setattr(fine.sampling.Sampler, "sample", lambda *a: pytest.fail("producer reuse"))
    monkeypatch.setattr(
        fine.sampling, "surface_points", lambda *a: pytest.fail("producer surface reuse")
    )
    assert fine.audit_geometry(context, archive, records, lambda: None)["geometry_consistency"]


@pytest.mark.parametrize(
    "attack", ["skip", "coordinates", "signed-zero", "reentrant-swallowed", "guard-error"]
)
def test_sampling_failures_poison_before_later_work(completed, attack):
    context, archive = copy.deepcopy(completed[:2])
    producer = fine.FineGeometry(context, archive, lambda: None)
    coefficients = np.asarray(context["selected"]["snapshot"]["base_coefficients"])
    level = plan.geometry_levels()[0]
    if attack == "skip":
        level = plan.geometry_levels()[1]
    elif attack == "coordinates":
        coefficients.flat[0] += 1e-3
    elif attack == "signed-zero":
        zero = np.flatnonzero(coefficients.ravel() == 0)[0]
        coefficients.flat[zero] = np.copysign(0.0, -np.copysign(1.0, coefficients.flat[zero]))
    elif attack == "guard-error":

        def guard():
            raise TimeoutError("synthetic geometry guard")

        producer._guard = guard
    else:

        def guard():
            try:
                producer.sample(coefficients, level)
            except ValueError:
                pass

        producer._guard = guard
    with pytest.raises((ValueError, RuntimeError, TimeoutError)):
        producer.sample(coefficients, level)
    assert producer.failed
    before = producer.work()
    with pytest.raises(RuntimeError):
        producer.sample(coefficients, plan.geometry_levels()[0])
    assert producer.work() == before


def test_all_four_grids_exhaustion_and_private_work(completed):
    context, _, producer, _ = completed
    # Do not poison the shared producer: independently inspect its copied work.
    work = producer.work()
    work["sampling"]["cc"]["completed"] = 0
    assert producer.work() == fine.expected_work(context["case"])


def test_source_file_tampering_is_checked_before_surface_work(tmp_path, monkeypatch):
    context, archive = fixture(tmp_path / "sources")
    reference = context["original_context"]["seed"]["sources"]["reference"]["input"]
    from pathlib import Path

    Path(reference["path"]).write_bytes(b"{}\n")
    monkeypatch.setattr(
        fine.sampling, "surface_points", lambda *a: pytest.fail("premature sampling")
    )
    with pytest.raises(ValueError, match="bytes changed"):
        fine.FineGeometry(context, archive, lambda: None)


def test_wrong_certificate_scalar_is_recomputed_independently(completed):
    context, archive = copy.deepcopy(completed[:2])
    context["selected"]["certificate"]["result"]["curves"][0]["D1"] += 0.01
    with pytest.raises(ValueError):
        fine.audit_geometry(context, archive, completed[3], lambda: None)


@pytest.mark.parametrize("after_last", [False, True])
def test_live_or_post_sampling_guard_failure_preserves_failed_prefix(completed, after_last):
    context, archive = completed[:2]
    producer = fine.FineGeometry(context, archive, lambda: None)
    coefficients = np.asarray(context["selected"]["snapshot"]["base_coefficients"])
    pairs = 276 if context["case"]["nbase"] == 6 else 496

    def guard():
        work = producer.work()["sampling"]
        if work["cc"]["completed"] == pairs if after_last else work["fourier"]["completed"] > 0:
            raise TimeoutError("synthetic sample-boundary failure")

    producer._guard = guard
    with pytest.raises(TimeoutError):
        producer.sample(coefficients, plan.geometry_levels()[0])
    assert producer.failed
    assert producer.work()["direct_grids"] == dict(attempted=1, completed=0)
    assert producer.work()["sampling"]["fourier"]["completed"] == (3 if after_last else 1)
    with pytest.raises(RuntimeError):
        producer.sample(coefficients, plan.geometry_levels()[0])


def test_four_grid_limit_cannot_be_restarted(completed):
    context, _, original, _ = completed
    producer = copy.deepcopy(original)
    coefficients = np.asarray(context["selected"]["snapshot"]["base_coefficients"])
    with pytest.raises(ValueError, match="already sampled"):
        producer.sample(coefficients, plan.geometry_levels()[0])
    assert producer.failed
    assert producer.work() == fine.expected_work(context["case"])


@pytest.mark.parametrize("at", [1, 2, 4, 12])
def test_independent_resource_failure_never_returns_success(completed, at):
    context, archive, _, records = completed
    calls = 0

    def guard():
        nonlocal calls
        calls += 1
        if calls == at:
            raise TimeoutError("synthetic independent guard")

    with pytest.raises(TimeoutError):
        fine.audit_geometry(context, archive, records, guard)
    assert calls == at


def test_caller_context_mutation_does_not_change_fixed_sampling_inputs(completed):
    context, archive = copy.deepcopy(completed[:2])
    producer = fine.FineGeometry(context, archive, lambda: None)
    coefficients = np.asarray(context["selected"]["snapshot"]["base_coefficients"]).copy()
    context["selected"]["state"]["x"][0] += 100
    context["original_context"]["seed"]["base_coefficients"][0][0][0] += 100
    archive["archived_source"]["physics_sources"]["native_sources"]["cell_sources"][
        "targets"
    ].clear()
    raw = producer.sample(coefficients, plan.geometry_levels()[0])
    assert raw["parameters"].shape == (256,)
    assert producer.work()["direct_grids"]["completed"] == 1


@pytest.mark.parametrize("change", ["missing", "extra"])
def test_full_raw_schema_remains_owned_by_independent_auditor(completed, tmp_path, change):
    context, archive, _, records = completed
    records = copy.deepcopy(records)
    raw = {key: value.copy() for key, value in read_arrays(records[0]["arrays"]).items()}
    if change == "missing":
        del raw["normals"]
    else:
        raw["unregistered"] = np.ones(1)
    records[0]["arrays"] = SnapshotStore(tmp_path / "malformed").arrays("grid", raw)
    with pytest.raises(ValueError, match="complete registered raw"):
        fine.audit_geometry(context, archive, records, lambda: None)
