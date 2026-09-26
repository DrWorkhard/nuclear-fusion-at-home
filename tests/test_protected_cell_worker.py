"""Injected worker controls with the synthetic complete cell, not native fields."""

import builtins
import copy
import os
import sys
import time
from pathlib import Path

import pytest
from test_protected_cell_contract import context_fixture
from test_protected_run_cell import Adapter

from fusion_baselines.protected_cell_audit import audit_cell
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json
from fusion_baselines.protected_worker_control import THREADS, ControlReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_protected_cell_worker as worker  # noqa: E402


class Harness:
    def __init__(self, tmp_path, monkeypatch):
        for key, value in THREADS.items():
            monkeypatch.setenv(key, value)
        self.store = SnapshotStore(tmp_path / "config-data")
        self.source = dict(synthetic=True, case_source="unchanged")
        self.context = context_fixture()
        self.calls, self.adapters = [], []
        self.config = dict(
            schema_version=1,
            kind="protected-cell-worker-config",
            case=copy.deepcopy(self.context["case"]),
            source=self.store.json("source", self.source),
            output=str(tmp_path / "worker"),
            parent_pid=os.getppid(),
            started_monotonic=time.monotonic(),
            threads=THREADS.copy(),
        )
        self.read_fd, self.write_fd = os.pipe()

    def bind(self, root):
        self.calls.append("bind")
        return copy.deepcopy(self.source)

    def build(self, sources, case):
        self.calls.append("context")
        assert sources == self.source and case == self.context["case"]
        return copy.deepcopy(self.context)

    def adapter(self, context, sources):
        self.calls.append("adapter")
        assert sources == self.source
        adapter = Adapter(context)
        self.adapters.append(adapter)
        return adapter

    def run(self):
        return worker.run_worker(
            self.store.json("config", self.config),
            self.write_fd,
            bind_sources=self.bind,
            build_context=self.build,
            adapter_factory=self.adapter,
        )

    def read(self):
        os.close(self.write_fd)
        self.write_fd = None
        chunks = []
        while chunk := os.read(self.read_fd, 4096):
            chunks.append(chunk)
        return b"".join(chunks)

    def close(self):
        for fd in (self.read_fd, self.write_fd):
            if fd is not None:
                os.close(fd)


@pytest.fixture
def h(tmp_path, monkeypatch):
    harness = Harness(tmp_path, monkeypatch)
    try:
        yield harness
    finally:
        harness.close()


def test_complete_worker_returns_envelope_with_both_sources_and_control_receipt(h):
    reference = h.run()
    envelope = read_json(reference)
    assert envelope["kind"] == "protected-cell-worker-return"
    assert envelope["case"] == h.context["case"]
    assert envelope["parent_pid"] == os.getppid() and envelope["worker_pid"] == os.getpid()
    assert envelope["threads"] == THREADS
    assert envelope["physical_admission"] is envelope["step4_pass"] is False
    assert read_json(envelope["source_before"]) == read_json(envelope["source_after"]) == h.source
    assert envelope["source_before"] != envelope["source_after"]
    assert h.calls == ["bind", "context", "adapter", "bind"]
    reader = ControlReader(h.config["started_monotonic"])
    reader.feed(h.read(), time.monotonic())
    assert reader.finish()[-1]["reference"] == reference
    assert reader.search_started <= reader.search_ended <= envelope["returned_monotonic"]
    assert audit_cell(envelope["cell_result"], h.context)["integration_integrity_pass"]
    assert len(h.adapters[0].native_calls) == 110  # Synthetic CountedField only.


@pytest.mark.parametrize("key", list(THREADS))
def test_wrong_thread_environment_rejected_before_scientific_imports(h, monkeypatch, key):
    monkeypatch.setenv(key, "2")
    original = builtins.__import__

    def prohibit(name, *args, **kwargs):
        if any(part in name for part in ("numpy", "protected_run_cell", "protected_cell_contract")):
            pytest.fail("scientific import before thread environment guard")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", prohibit)
    with pytest.raises(ValueError, match="thread environment"):
        h.run()
    assert not h.calls and not Path(h.config["output"]).exists()


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", True),
        ("kind", "another-worker"),
        ("threads", {}),
        ("parent_pid", True),
        ("parent_pid", 2),
        ("started_monotonic", True),
        ("started_monotonic", 0.0),
        ("output", "relative"),
    ],
)
def test_invalid_config_prevents_model_or_field_work(h, key, value):
    h.config[key] = value
    with pytest.raises((ValueError, TimeoutError)):
        h.run()
    assert not h.calls


def test_extra_config_field_and_reused_output_fail_before_sources(h):
    h.config["extra"] = True
    with pytest.raises(ValueError, match="exact"):
        h.run()
    assert not h.calls


def test_reused_output_is_not_overwritten(h):
    Path(h.config["output"]).mkdir()
    with pytest.raises(ValueError, match="fresh"):
        h.run()
    assert not h.calls


def test_nonpipe_control_fd_rejected_before_sources(h):
    with pytest.raises((ValueError, OSError)):
        worker.run_worker(
            {}, -1, bind_sources=h.bind, build_context=h.build, adapter_factory=h.adapter
        )
    assert not h.calls


def test_initial_live_disk_failure_prevents_sources_and_models(h, monkeypatch):
    def fail(*args):
        raise OSError("disk reserve")

    monkeypatch.setattr(worker, "space_check", fail)
    with pytest.raises(OSError, match="disk"):
        h.run()
    assert not h.calls and h.read() == b""


@pytest.mark.parametrize("stage", ["before", "after"])
def test_source_drift_never_sends_returned_result(h, stage):
    original = h.bind

    def changed(root):
        source = original(root)
        if len([c for c in h.calls if c == "bind"]) == (1 if stage == "before" else 2):
            source["case_source"] = "changed"
        return source

    h.bind = changed
    with pytest.raises(ValueError, match="source graph"):
        h.run()
    wire = h.read()
    assert b"returned_result" not in wire
    if stage == "before":
        assert not h.adapters and wire == b""
    else:
        assert len(h.adapters[0].native_calls) == 110
        assert (Path(h.config["output"]) / "cell-data/result.json").exists()


def test_wrong_case_rejected_before_adapter(h):
    original = h.build

    def changed(*args):
        context = original(*args)
        context["case"]["method"] = "V"
        return context

    h.build = changed
    with pytest.raises(ValueError, match="case"):
        h.run()
    assert not h.adapters


def test_broken_control_pipe_stops_at_search_start_without_trials(h):
    os.close(h.read_fd)
    h.read_fd = None
    with pytest.raises(BrokenPipeError):
        h.run()
    assert len(h.adapters[0].native_calls) == 100
    assert h.adapters[0].certificate_calls == 11
    assert not (Path(h.config["output"]) / "cell-data/result.json").exists()


def test_failed_envelope_publication_leaves_cell_but_sends_no_return(h, monkeypatch):
    original = SnapshotStore.json

    def fail(self, name, value):
        if name == "returned":
            raise OSError("envelope storage failure")
        return original(self, name, value)

    monkeypatch.setattr(SnapshotStore, "json", fail)
    with pytest.raises(OSError, match="envelope"):
        h.run()
    assert b"returned_result" not in h.read()
    assert (Path(h.config["output"]) / "cell-data/result.json").exists()


@pytest.mark.parametrize("key", list(THREADS))
def test_thread_environment_drift_during_bundle_prevents_return(h, monkeypatch, key):
    original = h.adapter

    def changed(*args):
        adapter = original(*args)
        bundle = adapter.bundle

        def drift(*params):
            result = bundle(*params)
            monkeypatch.setenv(key, "2")
            return result

        adapter.bundle = drift
        return adapter

    h.adapter = changed
    with pytest.raises(ValueError, match="thread environment"):
        h.run()
    assert b"returned_result" not in h.read()
