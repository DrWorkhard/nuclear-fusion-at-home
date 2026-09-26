"""Injected protected worker; no native CLI/default before physical qualification.

Thread environment is checked before loading NumPy or the scientific cell modules.
The parent owns process deadlines and acknowledgement; finding files is not success.
"""

import copy
import os
import stat
import time
from pathlib import Path

from fusion_baselines.protected_search_journal import _encode
from fusion_baselines.protected_worker_control import (
    THREADS,
    PhaseJournal,
    WorkerControl,
    send_control,
)
from fusion_baselines.resource_guard import GIB, space_check

ROOT = Path(__file__).resolve().parents[1]
CONFIG_KEYS = {
    "schema_version",
    "kind",
    "case",
    "source",
    "output",
    "parent_pid",
    "started_monotonic",
    "threads",
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, label):
    _need(_encode(actual) == _encode(expected), "worker identity: " + label)


def run_worker(
    config_reference, control_fd, *, bind_sources, build_context, adapter_factory, root=ROOT
):
    """Execute one injected worker, send its checked returned envelope, return it.

    Callers provide all scientific dependencies explicitly. Qualification uses
    only stubs/synthetic adapters. No automatic native path or resumable outputs.
    The supplied control descriptor is borrowed; its owner closes it at process exit.
    """
    _same(
        {key: os.environ.get(key) for key in THREADS},
        THREADS,
        "single-thread environment before scientific imports",
    )
    _need(
        type(control_fd) is int and control_fd >= 0 and stat.S_ISFIFO(os.fstat(control_fd).st_mode),
        "inherited control pipe required",
    )
    _need(
        all(callable(f) for f in (bind_sources, build_context, adapter_factory)),
        "explicit worker dependencies required",
    )

    # These imports may load scientific libraries: keep them after the env guard.
    from fusion_baselines import protected_cell_contract as contract
    from fusion_baselines.protected_run_cell import run_cell
    from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json
    from fusion_baselines.protected_search_journal import EventJournal

    config = read_json(config_reference)
    _need(type(config) is dict and set(config) == CONFIG_KEYS, "exact worker config required")
    for key, value in dict(
        schema_version=1, kind="protected-cell-worker-config", threads=THREADS
    ).items():
        _same(config[key], value, "config " + key)
    _need(
        type(config["output"]) is str and Path(config["output"]).is_absolute(),
        "absolute fresh worker output required",
    )
    output = Path(config["output"])
    _need(not output.exists() and not output.is_symlink(), "fresh worker output required")
    expected_sources = read_json(config["source"])

    def resource_check():
        _same(
            {key: os.environ.get(key) for key in THREADS},
            THREADS,
            "single-thread environment during execution",
        )
        return space_check(output if output.exists() else output.parent, 2 * GIB)

    control = WorkerControl(
        config["started_monotonic"],
        config["parent_pid"],
        lambda event: send_control(control_fd, event),
        resource_check,
        clock=time.monotonic,
        parent=os.getppid,
    )
    control.check()
    output.mkdir(exist_ok=False)
    store = SnapshotStore(output / "worker-data")
    observed = bind_sources(root)
    control.check()
    _same(observed, expected_sources, "pre-execution source graph")
    source_before = store.json("source-before", observed)
    context = build_context(copy.deepcopy(observed), copy.deepcopy(config["case"]))
    control.check()
    _same(context["case"], config["case"], "exact registered case")
    contract.validate_context(context)
    adapter = adapter_factory(copy.deepcopy(context), copy.deepcopy(observed))
    control.check()
    native = PhaseJournal(EventJournal(output / "native-events"), control, "native")
    controller = PhaseJournal(EventJournal(output / "controller-events"), control, "controller")
    cell_result = run_cell(
        context,
        native_journal=native,
        controller_journal=controller,
        store=SnapshotStore(output / "cell-data"),
        adapter=adapter,
        guard=control.check,
    )
    control.check()
    after = bind_sources(root)
    control.check()
    _same(after, expected_sources, "post-execution source graph")
    source_after = store.json("source-after", after)
    result = read_json(cell_result)
    _same(result["case"], config["case"], "returned cell case")
    for key, value in dict(
        producer_complete=True, physical_admission=False, step4_pass=False
    ).items():
        _same(result[key], value, "returned cell " + key)
    control.check()
    returned = time.monotonic()
    envelope = dict(
        schema_version=1,
        kind="protected-cell-worker-return",
        case=config["case"],
        config=config_reference,
        cell_result=cell_result,
        source_before=source_before,
        source_after=source_after,
        threads={key: os.environ.get(key) for key in THREADS},
        parent_pid=config["parent_pid"],
        worker_pid=os.getpid(),
        started_monotonic=config["started_monotonic"],
        returned_monotonic=returned,
        physical_admission=False,
        step4_pass=False,
    )
    reference = store.json("returned", envelope)
    control.signal("returned_result", reference)
    return reference


if __name__ == "__main__":
    raise SystemExit(
        "Injected qualification worker only; native launch awaits physical qualification."
    )
