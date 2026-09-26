"""Explicit synthetic wiring/fault controls; native physics is never invoked.

Complete histories use the qualified synthetic cell adapter. Only target/field
and certificate reconstruction primitives are stubbed; source-context rebuilding,
canonical storage, structural/graph audit and protected FD checks remain real.
The separately registered eight saved-native-seed run qualifies real arithmetic.
"""

import copy
import sys
from pathlib import Path

import numpy as np
import pytest
from test_protected_cell_contract import bundle_fixture, context_fixture
from test_protected_native_inputs import saved_context
from test_protected_run_cell import Adapter

from fusion_baselines.protected_run_cell import run_cell
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json
from fusion_baselines.protected_search_journal import EventJournal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_protected_cell_physics as physics  # noqa: E402

REAL_FIELD_ROW = physics.legacy.field_row


def target_fixture(context):
    return dict(
        input=dict(synthetic=True),
        B2_scale=context["B2_scale"],
        target_flux=context["historical_seed"]["snapshot"]["target_flux"],
        targets={
            32: dict(
                B2_scale=context["B2_scale"],
                **{
                    k: context["historical_seed"]["arrays"][k].copy()
                    for k in ("inner_points", "inner_target")
                },
            ),
            64: {},
        },
    )


def fake_field_row(row, snapshot, target, level, evidence, *, method, diagnostic):
    assert level == dict(index=0, nphi=64, ntheta=64, ncoil=256, ninner=32, offset=0)
    assert method == snapshot["method"] and diagnostic is False
    assert row["status"] == "completed"
    assert set(evidence.array(row["arrays"])) == {
        "boundary_points",
        "boundary_normals",
        "boundary_weights",
        "boundary_B",
        "boundary_A",
        "inner_points",
        "inner_target",
        "inner_B",
        "inner_A",
        "loop_points",
        "loop_tangents",
        "loop_A",
        "loop_B",
        "coil_positions",
        "coil_tangents",
        "coil_currents",
    }
    metrics = copy.deepcopy(row["metrics"])
    metrics.pop("frozen_scale")
    metrics["direct_errors"] = dict.fromkeys(
        ("boundary_B", "boundary_A", "inner_B", "inner_A", "loop_B", "loop_A"), 0.0
    )
    return dict(
        status="completed", metrics=metrics, arrays=evidence.array(row["arrays"]), snapshot=snapshot
    )


def history(directory, *, nbase=6, method="N", strategy="null", padding=0):
    inputs_path = directory / "inputs"
    inputs_path.mkdir()
    case = context_fixture(nbase, method)["case"]
    context, manifest = saved_context(inputs_path, case)
    adapter = Adapter(context, strategy=strategy, padding=padding)
    context = copy.deepcopy(adapter.context)
    row = physics.legacy.Evidence().read(context["historical_seed_reference"])
    row["gradient"] = context["historical_seed"]["state"]["gradient"]
    reference = SnapshotStore(inputs_path / "bound").json("operation", row)
    context["historical_seed_reference"] = reference
    manifest["cell_sources"]["startup_seed_bundles"][case["label"]]["operation"] = reference
    adapter.context = copy.deepcopy(context)
    reference = run_cell(
        context,
        native_journal=EventJournal(directory / "native"),
        controller_journal=EventJournal(directory / "controller"),
        store=SnapshotStore(directory / "raw"),
        adapter=adapter,
        guard=lambda: None,
    )
    return dict(
        context=context,
        source=manifest,
        reference=reference,
        result=read_json(reference),
        adapter=adapter,
    )


@pytest.fixture(scope="module")
def histories(tmp_path_factory):
    result = {}
    for nbase, method in ((6, "N"), (6, "V"), (8, "N"), (8, "V")):
        name = f"n{nbase}-{method}"
        result[name] = history(tmp_path_factory.mktemp(name), nbase=nbase, method=method)
    for strategy in (
        "gapped",
        "geometry-budget",
        "geometry-reject",
        "overcurrent",
        "armijo-reject",
    ):
        result[strategy] = history(
            tmp_path_factory.mktemp(strategy),
            strategy=strategy,
            padding=140000 if strategy == "geometry-budget" else 0,
        )
    return result


@pytest.fixture
def stub(monkeypatch):
    calls = dict(target=[], field=[], certificate=[], disk=[])

    def target(binding, case, evidence):
        calls["target"].append((copy.deepcopy(binding), copy.deepcopy(case)))
        context = physics.build_context(
            dict(cell_sources=binding, plumbing={}, repository={}), case
        )
        return target_fixture(context)

    def field(*args, **kwargs):
        calls["field"].append((copy.deepcopy(args[1]), kwargs.copy()))
        return fake_field_row(*args, **kwargs)

    def certificate(seed, report, coefficients, recorded):
        calls["certificate"].append(
            dict(
                seed=copy.deepcopy(seed),
                report=copy.deepcopy(report),
                coefficients=coefficients.copy(),
                recorded=recorded.copy(),
            )
        )
        return copy.deepcopy(recorded)

    def disk(path, reserve):
        calls["disk"].append((Path(path), reserve))
        return dict(sufficient=True)

    monkeypatch.setattr(physics.legacy, "target", target)
    monkeypatch.setattr(physics.legacy, "field_row", field)
    monkeypatch.setattr(physics.certificates, "audit_certificate", certificate)
    monkeypatch.setattr(physics, "space_check", disk)
    return calls


def run(h, tmp_path, **overrides):
    return physics.audit_saved_cell(
        overrides.get("reference", h["reference"]),
        overrides.get("context", h["context"]),
        overrides.get("source", h["source"]),
        output=tmp_path / "audit",
    )


FALSE_FLAGS = (
    "source_admission_verified",
    "external_execution_acknowledgement_verified",
    "field_values_verified",
    "gradients_verified",
    "physical_admission",
    "fine_grid_acceptance",
    "realized_field_transfer",
    "step4_pass",
    "sota_advance",
    "ms1_reached",
)


@pytest.mark.parametrize(
    "name",
    [
        "n6-N",
        "n6-V",
        "n8-N",
        "n8-V",
        "gapped",
        "geometry-budget",
        "geometry-reject",
        "overcurrent",
        "armijo-reject",
    ],
)
def test_all_complete_histories_reconstruct_every_positive_and_negative_record(
    histories, tmp_path, stub, name
):
    h = histories[name]
    native_before = len(h["adapter"].native_calls)
    reference = run(h, tmp_path)
    report = read_json(reference)
    count_cert, count_bundle = len(h["result"]["certificates"]), len(h["result"]["bundles"])
    assert report["reconstruction_component_pass"] is True
    assert report["cell_result"] == h["reference"]
    assert report["case"] == h["context"]["case"]
    assert all(report[k] is False for k in FALSE_FLAGS)
    assert report["changes_are_resolved_fine_grid_improvements"] is False
    assert report["pareto_dominance"] is False
    assert len(stub["certificate"]) == count_cert == len(report["certificates"])
    assert len(stub["field"]) == count_bundle == len(report["bundles"])
    assert len(stub["target"]) == 1
    assert stub["target"][0] == (h["source"]["cell_sources"], h["context"]["case"])
    cert_rows = [read_json(ref) for ref in report["certificates"]]
    bundle_rows = [read_json(ref) for ref in report["bundles"]]
    assert [r["manifest"] for r in cert_rows] == h["result"]["certificates"]
    assert [r["manifest"] for r in bundle_rows] == h["result"]["bundles"]
    for call, ref in zip(stub["certificate"], h["result"]["certificates"], strict=True):
        original = read_json(ref)
        assert call["seed"] == h["context"]["seed"]
        assert call["report"] == h["context"]["geometry_report"]
        assert call["recorded"] == original["result"]
        assert call["coefficients"].shape == (
            h["context"]["case"]["nbase"],
            3,
            2 * h["context"]["case"]["order"] + 1,
        )
        assert call["coefficients"].ravel().tolist() == original["x"]
    work = report["independent_work"]
    negative = sum(r["independent_certificate"]["certified"] is False for r in cert_rows)
    assert work["certificate_recomputations"] == count_cert
    assert work["certified"] == count_cert - negative and work["uncertified"] == negative
    assert work["bundle_reconstructions"] == count_bundle
    assert work["sampled_comparison_statistics"] == 6 * count_bundle
    assert work["sampled_vectors"] == 384 * count_bundle
    assert work["sampled_scalar_components"] == 1152 * count_bundle
    assert work["startup_directional_checks"] == 8
    for key in (
        "native_requests",
        "native_model_constructions",
        "producer_certificate_calls",
        "equilibrium_solves",
        "search_calls",
    ):
        assert work[key] == 0
    screen = read_json(report["startup_reconstruction"])
    assert screen["startup_screen_pass"] is True
    assert screen["independently_supplied_values"] is True
    assert screen["exact_independent_value_repeat"] is True
    assert [r["objective"] for r in screen["checks"]].count("independent") == 4
    assert len(screen["checks"]) == 8 and report["startup_reconstruction_timing"] == "posthoc"
    assert len(h["adapter"].native_calls) == native_before
    assert stub["disk"][0][1] == 3 * 1024**3
    assert all(row[1] == 2 * 1024**3 for row in stub["disk"][1:])
    if name in ("gapped", "geometry-budget", "geometry-reject"):
        assert negative > 0
    if name == "geometry-budget":
        assert count_cert == 128 and count_bundle == 19
        assert reference["bytes"] < 100000
        assert all(ref["bytes"] > 140000 for ref in report["certificates"])
    if name == "gapped":
        assert report["diagnostic_changes"]["J"]["difference"] < 0
        assert report["search_seed_bundle"] != report["selected_bundle"]
    if name == "overcurrent":
        assert any(r["reconstruction"]["metrics"]["current"] == 600000 for r in bundle_rows)


@pytest.mark.parametrize("nbase,method", [(6, "N"), (6, "V"), (8, "N"), (8, "V")])
def test_data_helper_routes_complete_bundle_exact_grid_and_method(stub, nbase, method):
    context = context_fixture(nbase, method)
    bundle = bundle_fixture(context)
    report = physics.reconstruct_bundle(bundle, context, target_fixture(context))
    assert report["method"] == method
    assert report["level"] == dict(index=0, nphi=64, ntheta=64, ncoil=256, ninner=32, offset=0)
    assert report["metrics"]["J"] == bundle["state"]["value"]
    assert "arrays" not in report and "snapshot" not in report
    assert set(report["direct_errors"]) == {
        "boundary_B",
        "boundary_A",
        "inner_B",
        "inner_A",
        "loop_B",
        "loop_A",
    }
    assert report["comparison_statistics"] == 6
    assert report["sampled_vectors"] == 384 and report["sampled_scalar_components"] == 1152
    assert all(report[k] is False for k in FALSE_FLAGS)


@pytest.mark.parametrize(
    "mutation",
    [
        "seed",
        "geometry-report",
        "historical-gradient",
        "historical-field",
        "historical-signed-zero",
        "target",
        "normalization",
        "original-reference",
    ],
)
def test_supplied_context_cannot_replace_rebuilt_original(histories, tmp_path, stub, mutation):
    h = histories["n6-N"]
    context = copy.deepcopy(h["context"])
    if mutation == "seed":
        context["seed"]["base_coefficients"][0][0][0] += 0.001
    elif mutation == "geometry-report":
        context["geometry_report"]["sum_base_lengths"] += 1
    elif mutation == "historical-gradient":
        context["historical_seed"]["state"]["gradient"][0] = 0.1
    elif mutation == "historical-field":
        context["historical_seed"]["arrays"]["boundary_B"][0, 0] = 0.1
    elif mutation == "historical-signed-zero":
        context["historical_seed"]["arrays"]["boundary_B"][0, 0] = -0.0
    elif mutation == "target":
        context["target_sources"]["input"]["sha256"] = "b" * 64
    elif mutation == "normalization":
        context["B2_scale"] = 3.0
    else:
        context["historical_seed_reference"]["sha256"] = "b" * 64
    with pytest.raises(ValueError):
        run(h, tmp_path, context=context)
    assert not stub["target"] and not stub["field"] and not stub["certificate"]
    assert not (tmp_path / "audit/records/result.json").exists()


@pytest.mark.parametrize("collection", ["certificates", "bundles", "checkpoints"])
@pytest.mark.parametrize("mutation", ["missing", "order", "duplicate"])
def test_bad_graph_rejected_before_physics(histories, tmp_path, stub, collection, mutation):
    h = histories["gapped"]
    changed = copy.deepcopy(h["result"])
    if mutation == "missing":
        changed[collection].pop()
    elif mutation == "order":
        changed[collection].reverse()
    else:
        changed[collection][1] = changed[collection][0]
    ref = SnapshotStore(tmp_path / "changed").json("result", changed)
    with pytest.raises(ValueError, match="saved-graph"):
        run(h, tmp_path, reference=ref)
    assert not stub["target"] and not stub["field"] and not stub["certificate"]


@pytest.mark.parametrize(
    "mutation",
    [
        "coordinates",
        "snapshot-coordinates",
        "current",
        "metric",
        "missing-array",
        "field-shape",
        "fixed-input",
        "array-current",
    ],
)
def test_complete_bundle_contract_blocks_tampering_before_numerics(stub, mutation):
    context = context_fixture()
    bundle = bundle_fixture(context)
    if mutation == "coordinates":
        bundle["state"]["x"][0] += 0.1
    elif mutation == "snapshot-coordinates":
        bundle["snapshot"]["base_coefficients"][0][0][0] += 0.1
    elif mutation == "current":
        bundle["snapshot"]["physical"][0]["current"] += 1
    elif mutation == "metric":
        bundle["state"]["metrics"]["B2_scale"] += 1
    elif mutation == "missing-array":
        bundle["arrays"].pop("loop_B")
    elif mutation == "field-shape":
        bundle["arrays"]["boundary_B"] = np.zeros((1, 3))
    elif mutation == "fixed-input":
        bundle["arrays"]["boundary_points"][0, 0] += 1
    else:
        bundle["arrays"]["coil_currents"][0] += 1
    with pytest.raises(ValueError):
        physics.reconstruct_bundle(bundle, context, target_fixture(context))
    assert not stub["field"]


@pytest.mark.parametrize("key", ["B2_scale", "target_flux", "active-B2"])
def test_target_scale_and_orientation_cannot_be_substituted(stub, key):
    context = context_fixture()
    target = target_fixture(context)
    if key == "active-B2":
        target["targets"][32]["B2_scale"] += 1
    else:
        target[key] *= -1
    with pytest.raises(ValueError):
        physics.reconstruct_bundle(bundle_fixture(context), context, target)
    assert not stub["field"]


@pytest.mark.parametrize("bad", [True, -1.0, float("nan"), float("inf"), 5.00001e-10])
def test_bad_direct_result_never_reports_pass(stub, monkeypatch, bad):
    def field(*args, **kwargs):
        result = fake_field_row(*args, **kwargs)
        result["metrics"]["direct_errors"]["loop_A"] = bad
        return result

    monkeypatch.setattr(physics.legacy, "field_row", field)
    context = context_fixture()
    with pytest.raises(ValueError, match="direct B/A"):
        physics.reconstruct_bundle(bundle_fixture(context), context, target_fixture(context))


def test_all_ten_independent_values_are_supplied_in_original_order(
    histories, tmp_path, stub, monkeypatch
):
    original, observed = physics.derivative_screen, []

    def screen(seed, nbase, order, rows, independent_values=None):
        observed.append((copy.deepcopy(rows), list(independent_values)))
        return original(seed, nbase, order, rows, independent_values)

    monkeypatch.setattr(physics, "derivative_screen", screen)
    report = read_json(run(histories["gapped"], tmp_path))
    assert len(observed) == 1
    rows, values = observed[0]
    bundle_reports = [read_json(ref) for ref in report["bundles"][:10]]
    assert len(values) == len(rows) == 10
    assert values == [r["reconstruction"]["metrics"]["J"] for r in bundle_reports]
    assert rows == [read_json(r["manifest"])["state"] for r in bundle_reports]


@pytest.mark.parametrize("position", [1, 9])
def test_independent_startup_disagreement_and_repeat_fail_closed(
    histories, tmp_path, stub, monkeypatch, position
):
    count = 0

    def field(*args, **kwargs):
        nonlocal count
        result = fake_field_row(*args, **kwargs)
        if count == position:
            result["metrics"]["J"] += 2e-11
        count += 1
        return result

    monkeypatch.setattr(physics.legacy, "field_row", field)
    with pytest.raises(ValueError, match="startup screen"):
        run(histories["n6-N"], tmp_path)
    assert not (tmp_path / "audit/records/result.json").exists()


@pytest.mark.parametrize("stage", ["negative-certificate", "rejected-field", "target"])
def test_failures_in_rejected_evidence_are_not_skipped(
    histories, tmp_path, stub, monkeypatch, stage
):
    h = histories["gapped" if stage == "negative-certificate" else "overcurrent"]

    def certificate(seed, report, coefficients, recorded):
        if recorded["certified"] is False:
            raise ValueError("negative proof mismatch")
        return copy.deepcopy(recorded)

    def field(*args, **kwargs):
        if args[0]["metrics"]["current"] == 600000:
            raise ValueError("rejected current row mismatch")
        return fake_field_row(*args, **kwargs)

    def target(*args):
        raise ValueError("target mismatch")

    if stage == "negative-certificate":
        monkeypatch.setattr(physics.certificates, "audit_certificate", certificate)
    elif stage == "rejected-field":
        monkeypatch.setattr(physics.legacy, "field_row", field)
    else:
        monkeypatch.setattr(physics.legacy, "target", target)
    with pytest.raises(ValueError, match="mismatch"):
        run(h, tmp_path)
    assert not (tmp_path / "audit/records/result.json").exists()


@pytest.mark.parametrize(
    "name",
    [
        "supplied-source",
        "graph-audit",
        "target",
        "certificate-001",
        "bundle-001",
        "startup-reconstruction",
        "result",
    ],
)
def test_storage_fault_keeps_prefix_without_returning_complete_report(
    histories, tmp_path, stub, monkeypatch, name
):
    original = SnapshotStore.json

    def fail(self, stem, payload):
        if stem == name:
            self._failed = True
            raise OSError("injected publication")
        return original(self, stem, payload)

    monkeypatch.setattr(SnapshotStore, "json", fail)
    with pytest.raises(OSError, match="publication"):
        run(histories["n6-N"], tmp_path)
    assert not (tmp_path / "audit/records/result.json").exists()


def test_swallowed_terminal_publication_failure_cannot_return_pass(
    histories, tmp_path, stub, monkeypatch
):
    original = SnapshotStore.json

    def fail(self, stem, payload):
        reference = original(self, stem, payload)
        if stem == "result":
            self._failed = True
        return reference

    monkeypatch.setattr(SnapshotStore, "json", fail)
    with pytest.raises(ValueError, match="poisoned"):
        run(histories["n6-N"], tmp_path)
    assert (tmp_path / "audit/records/result.json").exists()  # Not acknowledged.


@pytest.mark.parametrize("reserve", [3 * 1024**3, 2 * 1024**3])
def test_disk_guard_blocks_before_physics(histories, tmp_path, stub, monkeypatch, reserve):
    def disk(path, required):
        if required == reserve:
            raise OSError("disk reserve")

    monkeypatch.setattr(physics, "space_check", disk)
    with pytest.raises(OSError, match="disk reserve"):
        run(histories["n6-N"], tmp_path)
    assert not stub["field"] and not stub["certificate"]


def test_existing_output_cannot_be_resumed(histories, tmp_path, stub):
    output = tmp_path / "audit"
    output.mkdir()
    with pytest.raises(FileExistsError):
        run(histories["n6-N"], tmp_path)
    assert not stub["field"] and not stub["certificate"]


def test_no_old_full_space_or_seed_only_reconstruction_helpers(
    histories, tmp_path, stub, monkeypatch
):
    def forbidden(*args, **kwargs):
        pytest.fail("older stencil/seed-only identity must not be called")

    monkeypatch.setattr(physics.legacy, "snapshot_identity", forbidden)
    monkeypatch.setattr(physics.legacy.numerical, "derivative_checks", forbidden)
    monkeypatch.setattr(physics.legacy.numerical, "qualification_points", forbidden)
    assert read_json(run(histories["gapped"], tmp_path))["reconstruction_component_pass"]


def test_diagnostic_changes_use_reconstructed_not_recorded_values(
    histories, tmp_path, stub, monkeypatch
):
    h = histories["gapped"]
    seed = np.asarray(h["context"]["seed"]["base_coefficients"])

    def field(*args, **kwargs):
        result = fake_field_row(*args, **kwargs)
        original = np.array_equal(args[1]["base_coefficients"], seed)
        result["metrics"]["J"] += 2e-12 if original else -2e-12
        for key in ("normal_rms", "normal_max"):
            result["metrics"][key] += 1e-11 if original else -1e-11
        return result

    monkeypatch.setattr(physics.legacy, "field_row", field)
    report = read_json(run(h, tmp_path))
    rows = [read_json(ref) for ref in report["bundles"]]
    initial = next(r for r in rows if r["manifest"] == report["search_seed_bundle"])
    selected = next(r for r in rows if r["manifest"] == report["selected_bundle"])
    for key in ("J", "normal_rms", "normal_max", "vector_rms"):
        start, end = [r["reconstruction"]["metrics"][key] for r in (initial, selected)]
        assert report["diagnostic_changes"][key] == dict(
            search_seed=start,
            selected=end,
            difference=end - start,
            relative_change=None if start == 0 else (end - start) / abs(start),
        )
    old = read_json(report["selected_bundle"])["state"]["value"] - 0.1
    assert report["diagnostic_changes"]["J"]["difference"] != old


def test_new_raw_arrays_always_use_canonical_reader(histories, tmp_path, stub, monkeypatch):
    h, seen = histories["n6-N"], []
    original = physics.read_arrays

    def read(reference):
        seen.append(reference)
        return original(reference)

    monkeypatch.setattr(physics, "read_arrays", read)
    run(h, tmp_path)
    assert seen == [read_json(ref)["arrays"] for ref in h["result"]["bundles"]]


def test_actual_field_row_propagates_independent_metric_disagreement(stub, monkeypatch):
    context = context_fixture()
    bundle = bundle_fixture(context)
    metrics = copy.deepcopy(bundle["state"]["metrics"])
    metrics.pop("frozen_scale")
    metrics["normal_rms"] += 1e-3
    monkeypatch.setattr(physics.legacy, "field_row", REAL_FIELD_ROW)
    monkeypatch.setattr(physics.legacy.numerical, "composed_metrics", lambda *args: metrics)
    with pytest.raises(ValueError, match="independent normal_rms"):
        physics.reconstruct_bundle(bundle, context, target_fixture(context))


def test_no_resource_guard_after_terminal_publication(histories, tmp_path, stub, monkeypatch):
    def disk(path, reserve):
        if (tmp_path / "audit/records/result.json").exists():
            raise OSError("fallible postpublication guard")

    monkeypatch.setattr(physics, "space_check", disk)
    assert read_json(run(histories["n6-N"], tmp_path))["reconstruction_component_pass"]


def test_live_disk_failure_preserves_audited_certificate_prefix(
    histories, tmp_path, stub, monkeypatch
):
    def disk(path, reserve):
        if (tmp_path / "audit/records/certificate-000.json").exists():
            raise OSError("disk failure after first proof")

    monkeypatch.setattr(physics, "space_check", disk)
    with pytest.raises(OSError, match="first proof"):
        run(histories["n6-N"], tmp_path)
    assert len(stub["certificate"]) == 1 and not stub["field"]
    assert (tmp_path / "audit/records/certificate-000.json").exists()
    assert not (tmp_path / "audit/records/result.json").exists()
