"""Actual fine component composition with instrumented, nonphysical model fields."""

import copy
import time

import numpy as np
import pytest
import test_protected_fine_native as fixtures

from fusion_baselines import protected_fine_cell as cell
from fusion_baselines import protected_fine_native as native
from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_fine_geometry_codec import decode_geometry
from fusion_baselines.protected_fine_process import SCOPE
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_arrays, read_json
from fusion_baselines.protected_search_journal import EventJournal, read_events

SOURCE = dict(path="/synthetic/fine-source.json", sha256="b" * 64, bytes=12)


def request(self, field, quantity, points):
    event = dict(index=len(self.native_calls), field=field, quantity=quantity, points=points,
                 status="attempted", started_monotonic=time.monotonic(),
                 native_started=False, native_completed=False)
    self.native_calls.append(event)
    self.callback(copy.deepcopy(event))
    event.update(status="completed", native_started=True, native_completed=True,
                 completed_monotonic=time.monotonic())
    self.callback(copy.deepcopy(event))


class Geometry:
    """Only orchestration fixtures; intentionally incomplete nonphysical geometry."""
    def __init__(self, case):
        self.case, self.index, self._failed = case, 0, False
        self.counts = dict(
            surfaces=dict(attempted=2, completed=2),
            direct_grids=dict(attempted=0, completed=0),
            sampling={k: dict(attempted=0, completed=0, points_attempted=0, points_completed=0)
                      for k in ("fourier", "cp", "cc")},
        )

    def work(self):
        return copy.deepcopy(self.counts)

    def sample(self, coefficients, level):
        assert plan._same(level, plan.geometry_levels()[self.index])
        assert coefficients.shape == (self.case["nbase"], 3, 2 * self.case["order"] + 1)
        self.index += 1
        self.counts["direct_grids"] = dict(attempted=self.index, completed=self.index)
        # Independently spell out the work expected from each physical pair.
        n, p = level["ncoil"], self.case["nbase"] * 4
        pairs = p * (p - 1) // 2
        for key, count, points in (("fourier", 3, 3 * p * n), ("cp", 2, 2 * p * n),
                                   ("cc", pairs, pairs * n)):
            for stage in ("attempted", "completed"):
                self.counts["sampling"][key][stage] += count
                self.counts["sampling"][key]["points_" + stage] += points
        return dict(curvature_available=np.ones((p, n), dtype=bool),
                    synthetic_indices=np.arange(p, dtype=np.int64))


def setup(monkeypatch, tmp_path, case=None, changed=True):
    case = case or plan.cases()[0]
    for name in native.THREADS:
        monkeypatch.setenv(name, "1")
    monkeypatch.setattr(fixtures.Model, "request", request)
    context, archive, calls = fixtures.setup(
        monkeypatch, case["nbase"], case["method"], case["target"], changed
    )
    # Source-bound context is supplied to the real adapter through its isolated
    # builder stub, as in its own tests. No archive/native source admission here.
    proof = dict(result=dict(certified=True), synthetic=True)
    context["selected"]["certificate"] = proof
    bound = copy.deepcopy(context)
    monkeypatch.setattr(native, "_build_context", lambda a, c: copy.deepcopy(bound))
    adapter = native.FineNativeAdapter(context, archive)
    geometry = Geometry(case)
    store = SnapshotStore(tmp_path / "data")
    journal = EventJournal(tmp_path / "journal")
    runner = cell._FineCell(context, SOURCE, adapter=adapter, geometry=geometry,
                            store=store, journal=journal, guard=lambda: None)
    return runner, calls


@pytest.mark.parametrize("case", plan.cases(), ids=lambda case: case["label"])
@pytest.mark.parametrize("changed", [False, True])
def test_all_cases_real_components_complete_without_physical_claim(
    monkeypatch, tmp_path, case, changed
):
    runner, calls = setup(monkeypatch, tmp_path, case, changed)
    reference = runner.call(runner.run)
    result = read_json(reference)
    assert result["kind"] == "protected-fine-cell-execution"
    assert result["producer_complete"] is True
    assert all(result[key] is False for key in ("complete_execution", *SCOPE))
    assert result["source"] == SOURCE
    assert len(result["initializations"]) == 8
    assert len(result["operations"]) == 24
    assert len(result["geometry"]) == 4
    assert result["counts"] == {
        key: dict(attempted=n, completed=n)
        for key, n in (("initialization", 8), ("operation", 24), ("native", 80), ("points", 552960))
    }
    assert len(calls["models"]) == 8 and len(calls["execute"]) == 24
    events = read_events(result["journal"]["directory"], result["journal"]["receipt"])
    assert len(events) == 225
    completed = [e for e in events if e["event"] == "operation-completed"]
    assert [read_json(row["raw_reference"])["kind"] for row in completed].count(
        "protected-fine-initialization") == 8
    for row in completed:
        saved = read_json(row["raw_reference"])
        assert saved["case"] == case
        if "arrays" in saved:
            read_arrays(saved["arrays"])
    for index, ref in enumerate(result["geometry"]):
        record = read_json(ref)["record"]
        raw = decode_geometry(read_arrays(record["arrays"]), record["codec"], case,
                              plan.geometry_levels()[index])
        assert raw["curvature_available"].dtype == np.dtype(bool)
        assert raw["synthetic_indices"].dtype == np.dtype(np.int64)
    assert result["geometry_work"]["surfaces"] == dict(attempted=2, completed=2)
    assert result["geometry_work"]["direct_grids"] == dict(attempted=4, completed=4)
    saved_context = read_json(result["context"])
    assert "historical_seed" not in saved_context["original_context"]
    assert "arrays" not in saved_context["selected"]
    assert saved_context["selected"]["state"] == runner.context["selected"]["state"]
    assert saved_context["coarse"] == runner.context["coarse"]


@pytest.mark.parametrize("mutation", ["extra-context", "wrong-case", "wrong-selected-x",
                                     "missing-array", "bad-coarse-reference",
                                     "negative-certificate"])
def test_bad_context_fails_before_initialization(monkeypatch, tmp_path, mutation):
    runner, calls = setup(monkeypatch, tmp_path)
    context = copy.deepcopy(runner.context)
    if mutation == "extra-context":
        context["extra"] = 1
    elif mutation == "wrong-case":
        context["case"] = plan.cases()[1]
    elif mutation == "wrong-selected-x":
        context["selected"]["state"]["x"][0] += 1.0
    elif mutation == "missing-array":
        context["selected"]["arrays"].pop("loop_A")
    elif mutation == "bad-coarse-reference":
        context["coarse"]["selected_bundle"]["bytes"] = True
    else:
        context["selected"]["certificate"]["result"]["certified"] = False
    with pytest.raises(ValueError):
        cell.run_fine_cell(context, SOURCE, adapter=runner.adapter, geometry=runner.geometry,
                           store=runner.store, journal=runner.journal, guard=lambda: None)
    assert calls["initialize"] == []


@pytest.mark.parametrize("stage", ["context", "initialize", "arrays", "operation",
                                  "geometry", "result"])
def test_publication_failure_never_returns_core(monkeypatch, tmp_path, stage):
    runner, calls = setup(monkeypatch, tmp_path)
    original_json, original_arrays = runner.store.json, runner.store.arrays

    def json(name, value):
        if ((stage == "context" and name == "context")
                or (stage == "initialize" and name.startswith("initialize-"))
                or (stage == "operation" and name == "diagnostic-0")
                or (stage == "geometry" and name == "geometry-0")
                or (stage == "result" and name == "result")):
            raise OSError("synthetic final/raw publication failure")
        return original_json(name, value)

    def arrays(name, values):
        if stage == "arrays":
            raise OSError("synthetic arrays publication failure")
        return original_arrays(name, values)

    monkeypatch.setattr(runner.store, "json", json)
    monkeypatch.setattr(runner.store, "arrays", arrays)
    with pytest.raises(OSError):
        runner.call(runner.run)
    assert runner.failed
    assert not (runner.store.directory / "result.json").exists()
    if stage == "context":
        assert calls["initialize"] == []
    before = len(calls["execute"])
    with pytest.raises(RuntimeError):
        runner.call(runner.run)
    assert len(calls["execute"]) == before


@pytest.mark.parametrize("fault", ["guard", "adapter", "store", "journal", "geometry"])
def test_poisoned_owner_or_guard_cannot_be_hidden(monkeypatch, tmp_path, fault):
    runner, calls = setup(monkeypatch, tmp_path)
    if fault == "guard":
        def guard():
            try:
                runner.check()
            except ValueError:
                pass
        runner.guard = guard
    else:
        owner = getattr(runner, fault)
        owner._failed = True
    with pytest.raises(RuntimeError):
        runner.call(runner.run)
    assert calls["initialize"] == [] and runner.failed


@pytest.mark.parametrize("key", ["spec", "case", "coarse", "selected_x", "step4_pass"])
def test_initializer_metadata_cannot_change_identity(monkeypatch, tmp_path, key):
    runner, _ = setup(monkeypatch, tmp_path)
    original = runner.adapter.metadata

    def changed(model):
        metadata = original(model)
        metadata[key] = True if key == "step4_pass" else None
        return metadata

    monkeypatch.setattr(runner.adapter, "metadata", changed)
    with pytest.raises(ValueError):
        runner.call(runner.run)
    assert runner.failed
    assert runner.ledger.counts["initialization"]["completed"] == 0


@pytest.mark.parametrize("fault", ["extra", "metadata", "snapshot", "scale", "missing-arrays"])
def test_operation_identity_and_data_faults_fail_before_completion(monkeypatch, tmp_path, fault):
    runner, _ = setup(monkeypatch, tmp_path)
    execute = runner.adapter.execute

    def changed(model, operation):
        result = execute(model, operation)
        if fault == "extra":
            result["extra"] = 1
        elif fault == "metadata":
            result["metadata"]["original_seed_unit_flux"] += 1.0
        elif fault == "snapshot":
            result["record"]["snapshot"]["sha256"] = "c" * 64
        elif fault == "scale":
            result["record"]["scale"] *= 1.01
        else:
            result["arrays"] = {}
        return result

    monkeypatch.setattr(runner.adapter, "execute", changed)
    with pytest.raises(ValueError):
        runner.call(runner.run)
    assert runner.failed
    assert runner.ledger.counts["operation"]["completed"] == 0


@pytest.mark.parametrize("fault", ["work", "mask", "surfaces", "direct-grids"])
def test_geometry_faults_do_not_emit_complete_result(monkeypatch, tmp_path, fault):
    runner, _ = setup(monkeypatch, tmp_path)
    sample = runner.geometry.sample

    def changed(coefficients, level):
        raw = sample(coefficients, level)
        if fault == "work":
            runner.geometry.counts["sampling"]["cc"]["completed"] -= 1
        elif fault == "mask":
            raw["curvature_available"] = raw["curvature_available"].astype(float)
        elif fault == "surfaces":
            runner.geometry.counts["surfaces"]["completed"] = 1
        else:
            runner.geometry.counts["direct_grids"]["completed"] = 1
        return raw

    monkeypatch.setattr(runner.geometry, "sample", changed)
    with pytest.raises(ValueError):
        runner.call(runner.run)
    assert runner.failed and not (runner.store.directory / "result.json").exists()


def test_final_slow_write_leaves_unacknowledged_file(monkeypatch, tmp_path):
    runner, _ = setup(monkeypatch, tmp_path)
    expired = False
    write = runner.store.json

    def slow(name, value):
        nonlocal expired
        ref = write(name, value)
        if name == "result":
            expired = True
        return ref

    def guard():
        if expired:
            raise TimeoutError("synthetic deadline during final write")

    runner.guard = guard
    monkeypatch.setattr(runner.store, "json", slow)
    with pytest.raises(TimeoutError):
        runner.call(runner.run)
    assert runner.failed
    assert (runner.store.directory / "result.json").exists()
