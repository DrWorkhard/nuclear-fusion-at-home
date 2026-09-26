"""One explicit fine worker; production dependencies stay behind committed gates.

Import-light until the actual environment/pipe is checked. Finding a saved file
never acknowledges completion; the parent must receive the sole returned frame,
observe exit zero, and validate its independent source/config/process bindings.
"""

import argparse
import copy
import json
import os
import stat
import time
from pathlib import Path

from fusion_baselines.protected_fine_control import THREADS, FineWorkerControl, send_fine_control
from fusion_baselines.protected_fine_process import SCOPE
from fusion_baselines.protected_search_journal import _encode, _unique_object
from fusion_baselines.resource_guard import GIB, space_check

ROOT = Path(__file__).resolve().parents[1]
_RUNNING = False
_POISONED = False


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, message):
    _need(_encode(actual) == _encode(expected), message)


def _threads():
    _same(
        {key: os.environ.get(key) for key in THREADS},
        THREADS,
        "unchanged fine single-thread environment required",
    )


def _dependencies():
    from types import SimpleNamespace

    from fusion_baselines.protected_fine_cell import context_metadata, run_fine_cell
    from fusion_baselines.protected_fine_process import _CONFIG_KEYS
    from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json
    from fusion_baselines.protected_search_journal import EventJournal

    return SimpleNamespace(
        Store=SnapshotStore,
        read=read_json,
        Journal=EventJournal,
        run=run_fine_cell,
        metadata=context_metadata,
        keys=_CONFIG_KEYS,
    )


def _run_worker(
    config_reference,
    control_fd,
    *,
    bind_sources,
    build_context,
    adapter_factory,
    geometry_factory,
    root=ROOT,
):
    """Injected execution for tests; the CLI supplies gated production dependencies."""
    _threads()
    _need(
        type(control_fd) is int and control_fd >= 0 and stat.S_ISFIFO(os.fstat(control_fd).st_mode),
        "inherited fine control pipe required",
    )
    _need(
        all(callable(f) for f in (bind_sources, build_context, adapter_factory, geometry_factory)),
        "explicit fine worker dependencies required",
    )
    d = _dependencies()
    config = d.read(config_reference)
    _need(type(config) is dict and set(config) == d.keys, "exact fine worker configuration")
    for key, value in dict(
        schema_version=1, kind="protected-fine-worker-config", threads=THREADS
    ).items():
        _same(config[key], value, "fine worker config " + key)
    _need(
        type(config["output"]) is str and Path(config["output"]).is_absolute(),
        "absolute fresh fine worker output required",
    )
    output = Path(config["output"])
    _need(
        output.resolve() == output and not output.exists() and not output.is_symlink(),
        "fresh direct fine worker directory required",
    )
    expected = d.read(config["source"])
    owners = []

    def health():
        _threads()
        _need(not _POISONED, "reentrant fine worker execution poisoned")
        _need(
            not any(
                getattr(owner, key, False) is True
                for owner in owners
                for key in ("failed", "_failed")
            ),
            "fine worker dependency poisoned",
        )

    def resources():
        health()
        space_check(output if output.exists() else output.parent, 2 * GIB)
        health()

    control = FineWorkerControl(
        config["started_monotonic"],
        config["parent_pid"],
        lambda event: send_fine_control(control_fd, event),
        resources,
        clock=time.monotonic,
        parent=os.getppid,
    )
    control.check()
    output.mkdir(exist_ok=False)
    store = d.Store(output / "worker-data")
    owners.append(store)
    control.check()
    observed = bind_sources(Path(root).resolve())
    control.check()
    _same(observed, expected, "fine worker exact pre-execution source")
    before = store.json("source-before", observed)
    control.check()
    context = build_context(copy.deepcopy(observed), copy.deepcopy(config["case"]))
    control.check()
    _same(context["case"], config["case"], "fine worker exact configured case")
    d.metadata(context)
    control.check()
    adapter = adapter_factory(copy.deepcopy(context), copy.deepcopy(observed["archive"]))
    owners.append(adapter)
    control.check()
    geometry = geometry_factory(
        copy.deepcopy(context), copy.deepcopy(observed["archive"]), control.check
    )
    owners.append(geometry)
    control.check()
    data = d.Store(output / "cell-data")
    owners.append(data)
    control.check()
    journal = d.Journal(output / "fine-events")
    owners.append(journal)
    control.check()
    result_ref = d.run(
        context,
        config["source"],
        adapter=adapter,
        geometry=geometry,
        store=data,
        journal=journal,
        guard=control.check,
    )
    control.check()
    after = bind_sources(Path(root).resolve())
    control.check()
    _same(after, expected, "fine worker exact post-execution source")
    after_ref = store.json("source-after", after)
    control.check()
    result = d.read(result_ref)
    for key, value in dict(
        schema_version=1,
        kind="protected-fine-cell-execution",
        case=config["case"],
        source=config["source"],
        producer_complete=True,
        complete_execution=False,
        **SCOPE,
    ).items():
        _same(result.get(key), value, "fine worker returned core " + key)
    _same(d.read(config_reference), config, "unchanged fine worker configuration bytes")
    _same(d.read(config["source"]), expected, "unchanged supplied fine source bytes")
    control.check()
    envelope = dict(
        schema_version=1,
        kind="protected-fine-worker-return",
        case=config["case"],
        config=config_reference,
        fine_result=result_ref,
        source_before=before,
        source_after=after_ref,
        threads={key: os.environ.get(key) for key in THREADS},
        parent_pid=config["parent_pid"],
        worker_pid=os.getpid(),
        started_monotonic=config["started_monotonic"],
        returned_monotonic=time.monotonic(),
        complete_execution=False,
        **SCOPE,
    )
    reference = store.json("returned", envelope)
    control.check()
    control.returned(reference)
    return reference


def run_worker(
    config_reference,
    control_fd,
    *,
    bind_sources,
    build_context,
    adapter_factory,
    geometry_factory,
    root=ROOT,
):
    """One fail-stop worker; reentrant attempts cannot be swallowed by a callback."""
    global _RUNNING, _POISONED
    if _RUNNING:
        _POISONED = True
        raise ValueError("fine workers must execute serially")
    _RUNNING, _POISONED = True, False
    try:
        return _run_worker(
            config_reference,
            control_fd,
            bind_sources=bind_sources,
            build_context=build_context,
            adapter_factory=adapter_factory,
            geometry_factory=geometry_factory,
            root=root,
        )
    finally:
        _RUNNING = False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-reference", required=True)
    parser.add_argument("--control-fd", type=int, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)

    def bind(root):
        from protected_fine_execution_inputs import sources

        return sources(root)

    def context(source, case):
        from protected_fine_execution_inputs import build_context

        return build_context(source, case)

    def adapter(context, archive):
        from fusion_baselines.protected_fine_native import FineNativeAdapter

        return FineNativeAdapter(context, archive)

    def geometry(context, archive, guard):
        from fusion_baselines.protected_fine_geometry import FineGeometry

        return FineGeometry(context, archive, guard)

    reference = json.loads(args.config_reference, object_pairs_hook=_unique_object)
    run_worker(
        reference,
        args.control_fd,
        bind_sources=bind,
        build_context=context,
        adapter_factory=adapter,
        geometry_factory=geometry,
        root=args.root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
