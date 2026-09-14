"""Synthetic orchestration checks: no project-target evaluation."""

import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "coil_pilot_runner", SCRIPTS / "run_coupled_coil_pilot.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def test_collection_preserves_incomplete_and_last_completed(tmp_path):
    (tmp_path / "attempts").mkdir()
    (tmp_path / "bundles" / "0000").mkdir(parents=True)
    for i in range(2):
        runner.write_json_atomic(tmp_path / "attempts" / f"{i:04d}.json",
                                 dict(index=i, status="attempted", x=[float(i)]))
    completed = dict(index=0, status="completed", x=[0.0], J=2.0)
    runner.write_json_atomic(tmp_path / "bundles" / "0000" / "row.json", completed)
    before = (tmp_path / "bundles" / "0000" / "row.json").read_bytes()
    rows = runner.collected_rows(tmp_path)
    assert [{k: v for k, v in row.items() if k != "attempt"} for row in rows] == [
        completed, dict(index=1, status="attempted", x=[1.0])]
    assert all(runner.checked(row["attempt"]).exists() for row in rows)
    assert (tmp_path / "bundles" / "0000" / "row.json").read_bytes() == before


def test_noncontiguous_attempts_rejected(tmp_path):
    (tmp_path / "attempts").mkdir()
    runner.write_json_atomic(tmp_path / "attempts" / "0001.json", dict(index=1))
    with pytest.raises(ValueError, match="contiguous"):
        runner.collected_rows(tmp_path)


def test_singlethread_rejected_before_sources(monkeypatch, tmp_path):
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    with pytest.raises(ValueError, match="single-thread"):
        runner.run_cell("qualification", {}, tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_worker_counts_duplicates_and_enforces128(monkeypatch, tmp_path):
    class Model:
        seed_x = np.array([0.0, 0.0])
        names = ["a", "b"]
        initialization_work = {"seed_A_calls": 1}

    monkeypatch.setattr(runner, "make_model", lambda *_: Model())
    monkeypatch.setattr(runner, "sources", lambda *_: {})
    for name in runner.THREADS:
        monkeypatch.setenv(name, "1")
    (tmp_path / "attempts").mkdir()
    (tmp_path / "bundles").mkdir()
    runner.write_json_atomic(tmp_path / "config.json",
                             dict(source={}, case={"label": "synthetic"}, phase="search",
                                  parent_pid=os.getppid()))
    called = []

    def bundle(model, x, directory, index, deadline=None):
        assert deadline is not None
        called.append(index)
        directory.mkdir()
        row = dict(index=index, status="completed", x=list(x), J=1.0,
                   gradient=[0.0, 0.0], metrics=dict(normal_rms=1.0, vector_rms=1.0))
        runner.write_json_atomic(directory / "row.json", row)
        return row

    def optimizer(fun, seed, **kwargs):
        assert kwargs["method"] == "L-BFGS-B"
        assert kwargs["options"] == dict(maxiter=128, maxls=20, ftol=1e-12, gtol=1e-9)
        for _ in range(129):
            fun(seed)

    monkeypatch.setattr(runner, "save_bundle", bundle)
    monkeypatch.setattr("scipy.optimize.minimize", optimizer)
    runner.worker(tmp_path / "config.json")
    assert called == list(range(128))
    assert len(runner.collected_rows(tmp_path)) == 128
    terminal = json.loads((tmp_path / "worker-terminal.json").read_text())
    assert terminal["reason"] == "evaluation_budget"
    assert (tmp_path / "search-start.json").exists()


def test_late_bundle_preserves_raw_without_creating_selectable_row(monkeypatch, tmp_path):
    class Field:
        def A(self):
            return np.ones((2, 3))

        B = A

    class Model:
        field = inner_field = loop_field = Field()

        def evaluate(self, x):
            return 1.0, np.ones(2), {"scale": 2.0}

        def arrays(self, x):
            return {"raw": np.ones(2)}

        def snapshot(self, x):
            return {"scale": 2.0}

    clocks = iter([0.0, 600.01])
    monkeypatch.setattr(runner.time, "monotonic", lambda: next(clocks))
    directory = tmp_path / "bundle"
    with pytest.raises(TimeoutError, match="late full bundle"):
        runner.save_bundle(Model(), [0.0, 0.0], directory, 0, deadline=600.0)
    assert (directory / "snapshot.json").exists()
    assert (directory / "arrays.npz").exists()
    assert not (directory / "row.json").exists()


def test_unguarded_worker_rejected_before_model(monkeypatch, tmp_path):
    runner.write_json_atomic(tmp_path / "config.json",
                             dict(phase="search", parent_pid=-1, source={}))
    monkeypatch.setattr(runner, "make_model", lambda *_: pytest.fail("must reject before model"))
    with pytest.raises(ValueError, match="live launching parent"):
        runner.worker(tmp_path / "config.json")


@pytest.mark.parametrize("mutation", ["truthy", "phase", "source", "case", "run"])
def test_incorrect_qualification_cannot_launch_search(monkeypatch, tmp_path, mutation):
    for key in runner.THREADS:
        monkeypatch.setenv(key, "1")
    monkeypatch.setattr(runner, "sources", lambda *_: {})
    monkeypatch.setattr(runner, "space_check", lambda *_: {"sufficient": True})
    qpath, apath = tmp_path / "qual.json", tmp_path / "audit.json"
    runner.write_json_atomic(qpath, dict(phase="qualification", source={}, case={}))
    audit = dict(phase="qualification", source={}, case={}, status="completed",
                 qualification_pass=True, arithmetic_and_source_pass=True,
                 run=runner.reference(qpath))
    key, value = {
        "truthy": ("qualification_pass", "true"), "phase": ("phase", "search"),
        "source": ("source", {"changed": 1}), "case": ("case", {"changed": 1}),
        "run": ("run", {}),
    }[mutation]
    audit[key] = value
    runner.write_json_atomic(apath, audit)
    with pytest.raises(ValueError, match="exact cell"):
        runner.run_cell("search", {}, tmp_path / "new", qpath, apath)
    assert not (tmp_path / "new").exists()
