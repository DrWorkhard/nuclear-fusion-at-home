"""Injected synthetic worker guards and real pipe framing; no native work."""

import copy
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from fusion_baselines.protected_fine_control import FineControlReader
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json
from fusion_baselines.protected_search_journal import EventJournal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_protected_fine_worker as worker  # noqa: E402


@pytest.fixture
def setup(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    for key in worker.THREADS:
        monkeypatch.setenv(key, "1")
    source = dict(kind="synthetic-full-fine-source", archive=dict(historical="unchanged"))
    store = SnapshotStore(root / "inputs")
    source_ref = store.json("source", source)
    case = dict(label="synthetic-fine-case")
    config = dict(
        schema_version=1,
        kind="protected-fine-worker-config",
        case=case,
        source=source_ref,
        output=str(root / "worker"),
        parent_pid=os.getppid(),
        started_monotonic=time.monotonic(),
        threads=worker.THREADS.copy(),
    )
    config_ref = store.json("config", config)
    calls = []

    def core(context, source_reference, *, adapter, geometry, store, journal, guard):
        calls.append("core")
        guard()
        return store.json(
            "result",
            dict(
                schema_version=1,
                kind="protected-fine-cell-execution",
                case=context["case"],
                source=source_reference,
                producer_complete=True,
                complete_execution=False,
                **worker.SCOPE,
            ),
        )

    dependencies = SimpleNamespace(
        Store=SnapshotStore,
        read=read_json,
        Journal=EventJournal,
        run=core,
        metadata=lambda _: {},
        keys=set(config),
    )
    monkeypatch.setattr(worker, "_dependencies", lambda: dependencies)
    monkeypatch.setattr(worker, "space_check", lambda *a: dict(free_bytes=5 * 1024**3))
    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)

    def bind(path):
        assert path == root
        calls.append("source")
        return copy.deepcopy(source)

    def context(manifest, descriptor):
        assert manifest == source and descriptor == case
        calls.append("context")
        return dict(case=copy.deepcopy(descriptor))

    def adapter(context, archive):
        assert archive == source["archive"]
        calls.append("adapter")
        return SimpleNamespace(_failed=False)

    def geometry(context, archive, guard):
        assert archive == source["archive"]
        calls.append("geometry")
        guard()
        return SimpleNamespace(_failed=False)

    def run(**changes):
        kwargs = dict(
            bind_sources=bind,
            build_context=context,
            adapter_factory=adapter,
            geometry_factory=geometry,
            root=root,
        )
        kwargs.update(changes)
        return worker.run_worker(config_ref, write_fd, **kwargs)

    def wire():
        try:
            return os.read(read_fd, 4096)
        except BlockingIOError:
            return b""

    yield SimpleNamespace(
        root=root,
        source=source,
        source_ref=source_ref,
        config=config,
        config_ref=config_ref,
        calls=calls,
        run=run,
        wire=wire,
        dependencies=dependencies,
        bind=bind,
        adapter=adapter,
        geometry=geometry,
    )
    os.close(read_fd)
    os.close(write_fd)


def test_worker_uses_explicit_return_and_full_unchanged_source(setup):
    reference = setup.run()
    reader = FineControlReader(setup.config["started_monotonic"])
    reader.feed(setup.wire(), time.monotonic())
    assert reader.finish()[0]["reference"] == reference
    envelope = read_json(reference)
    assert envelope["worker_pid"] == os.getpid()
    assert envelope["parent_pid"] == os.getppid()
    assert envelope["config"] == setup.config_ref
    assert (
        read_json(envelope["source_before"]) == read_json(envelope["source_after"]) == setup.source
    )
    assert read_json(envelope["fine_result"])["source"] == setup.source_ref
    assert all(envelope[k] is False for k in ("complete_execution", *worker.SCOPE))
    assert setup.calls == ["source", "context", "adapter", "geometry", "core", "source"]
    assert worker._RUNNING is False


@pytest.mark.parametrize("key", list(worker.THREADS))
def test_bad_initial_threads_fail_before_scientific_import(setup, monkeypatch, key):
    monkeypatch.setenv(key, "2")
    monkeypatch.setattr(worker, "_dependencies", lambda: pytest.fail("premature imports"))
    with pytest.raises(ValueError, match="single-thread"):
        setup.run()
    assert setup.calls == [] and setup.wire() == b""


@pytest.mark.parametrize(
    "stage", ["source-before", "source-after", "context", "adapter", "geometry", "core"]
)
def test_each_callback_error_prevents_return(setup, stage):
    def fail(*args, **kwargs):
        raise OSError("synthetic hook")

    options = {}
    if stage.startswith("source"):
        count = 0

        def bind(root):
            nonlocal count
            count += 1
            if count == (1 if stage == "source-before" else 2):
                fail()
            return setup.bind(root)

        options["bind_sources"] = bind
    elif stage == "core":
        setup.dependencies.run = fail
    else:
        options[
            {
                "context": "build_context",
                "adapter": "adapter_factory",
                "geometry": "geometry_factory",
            }[stage]
        ] = fail
    with pytest.raises(OSError):
        setup.run(**options)
    assert setup.wire() == b"" and worker._RUNNING is False


@pytest.mark.parametrize("stage", ["source", "adapter", "geometry", "core"])
def test_swallowed_worker_reentry_poisoning(setup, stage):
    def swallow():
        with pytest.raises(ValueError, match="serially"):
            setup.run()

    def bind(root):
        swallow()
        return setup.bind(root)

    def adapter(*args):
        swallow()
        return setup.adapter(*args)

    def geometry(*args):
        swallow()
        return setup.geometry(*args)

    original = setup.dependencies.run

    def core(*args, **kwargs):
        swallow()
        return original(*args, **kwargs)

    options = {}
    if stage == "core":
        setup.dependencies.run = core
    else:
        options[
            {
                "source": "bind_sources",
                "adapter": "adapter_factory",
                "geometry": "geometry_factory",
            }[stage]
        ] = locals()[stage if stage != "source" else "bind"]
    with pytest.raises((ValueError, RuntimeError), match="poison"):
        setup.run(**options)
    assert setup.wire() == b""


@pytest.mark.parametrize("poison", ["reentry", "store"])
def test_final_post_send_resource_hook_poison_cannot_return_success(setup, monkeypatch, poison):
    sent = False
    owners = []
    original_send = worker.send_fine_control
    original_store = setup.dependencies.Store

    def capture_store(*args, **kwargs):
        owner = original_store(*args, **kwargs)
        owners.append(owner)
        return owner

    def send(*args):
        nonlocal sent
        original_send(*args)
        sent = True

    def disk(*args):
        if sent:
            if poison == "reentry":
                with pytest.raises(ValueError, match="serially"):
                    setup.run()
            else:
                owners[0]._failed = True
        return dict(free_bytes=5 * 1024**3)

    setup.dependencies.Store = capture_store
    monkeypatch.setattr(worker, "send_fine_control", send)
    monkeypatch.setattr(worker, "space_check", disk)
    with pytest.raises((ValueError, RuntimeError), match="poison"):
        setup.run()
    # A sent frame is insufficient: propagating failure makes the actual CLI
    # exit nonzero, which its independent supervisor must reject.
    assert setup.wire() and worker._RUNNING is False


@pytest.mark.parametrize("name", ["source-before", "source-after", "returned", "result"])
@pytest.mark.parametrize("swallowed", [False, True])
def test_failed_persistence_file_is_never_a_returned_result(setup, monkeypatch, name, swallowed):
    original = SnapshotStore.json

    def write(self, stem, value):
        reference = original(self, stem, value)
        if stem == name:
            self._failed = True
            if not swallowed:
                raise OSError("synthetic final fsync failure")
        return reference

    monkeypatch.setattr(SnapshotStore, "json", write)
    with pytest.raises((ValueError, RuntimeError, OSError)):
        setup.run()
    assert setup.wire() == b""
    assert list((setup.root / "worker").rglob(name + ".json"))


@pytest.mark.parametrize("stage", ["source", "adapter", "geometry", "core"])
def test_observed_thread_drift_is_rejected(setup, monkeypatch, stage):
    def drift():
        monkeypatch.setenv("MKL_NUM_THREADS", "2")

    def bind(root):
        result = setup.bind(root)
        drift()
        return result

    def adapter(*args):
        result = setup.adapter(*args)
        drift()
        return result

    def geometry(*args):
        result = setup.geometry(*args)
        drift()
        return result

    original = setup.dependencies.run

    def core(*args, **kwargs):
        result = original(*args, **kwargs)
        drift()
        return result

    options = {}
    if stage == "core":
        setup.dependencies.run = core
    else:
        options[
            {
                "source": "bind_sources",
                "adapter": "adapter_factory",
                "geometry": "geometry_factory",
            }[stage]
        ] = locals()[stage if stage != "source" else "bind"]
    with pytest.raises(ValueError, match="single-thread"):
        setup.run(**options)
    assert setup.wire() == b""


@pytest.mark.parametrize("stage", [1, 2])
def test_source_drift_before_or_after_execution_is_rejected(setup, stage):
    count = 0

    def bind(root):
        nonlocal count
        count += 1
        result = setup.bind(root)
        if count == stage:
            result["archive"]["historical"] = "changed"
        return result

    with pytest.raises(ValueError, match="source"):
        setup.run(bind_sources=bind)
    assert setup.wire() == b""
    assert ("core" in setup.calls) is (stage == 2)


def test_context_case_mismatch_before_adapter_construction(setup):
    with pytest.raises(ValueError, match="configured case"):
        setup.run(build_context=lambda *a: dict(case={}))
    assert "adapter" not in setup.calls and setup.wire() == b""


def test_parent_identity_checked_before_sources(setup, monkeypatch):
    monkeypatch.setattr(worker.os, "getppid", lambda: 1)
    with pytest.raises(ValueError, match="parent identity"):
        setup.run()
    assert setup.calls == [] and setup.wire() == b""


def test_initial_import_is_scientifically_inert():
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(Path(worker.__file__).parent)!r}); "
        "import run_protected_fine_worker; "
        "assert not ({'numpy','scipy','simsopt','jax','protected_fine_execution_inputs'}"
        " & set(sys.modules))"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_cli_requires_explicit_config_and_control_pipe():
    result = subprocess.run(
        [sys.executable, worker.__file__, "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--config-reference" in result.stdout and "--control-fd" in result.stdout
    assert "--root" in result.stdout
