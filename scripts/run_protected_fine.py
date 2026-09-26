"""Serial fixed-candidate fine validation; admission stays closed until qualified.

Source/scientific imports occur inside the first parent's 1,800-second clock.
Only explicitly returned parent references count as execution. Independent
saved-data audits have separate guarded timing; threshold failures are results,
whereas execution, source, arithmetic or publication errors stop the study.
"""

import argparse
import copy
import json
import math
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
THREADS = dict.fromkeys(
    ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"), "1"
)
SCOPE = dict.fromkeys(
    (
        "physical_admission",
        "resolved_fine_grid_improvement",
        "pareto_dominance",
        "realized_field_transfer",
        "step4_pass",
        "sota_advance",
        "ms1_reached",
    ),
    False,
)
_RUNNING = False
_POISONED = False


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _threads():
    _need(
        {key: os.environ.get(key) for key in THREADS} == THREADS,
        "set all four registered thread variables to 1 before scientific imports",
    )


def _clock(value):
    _need(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "finite nonnegative fine study clock required",
    )
    return value


def _cases():
    return [
        dict(
            label=f"{target}-n{n}-{method}",
            target=target,
            nbase=n,
            order=order,
            seed_label=f"n{n}-shape-d100mm",
            method=method,
        )
        for target in ("reference", "selected")
        for n, order in ((6, 5), (8, 7))
        for method in ("N", "V")
    ]


def _supervise(*args, **kwargs):
    # This module and its supervisor are import-light; no scientific imports.
    from fusion_baselines.protected_fine_process import supervise_fine_cell

    return supervise_fine_cell(*args, **kwargs)


def _dependencies():
    import audit_protected_fine_fields as fields
    import protected_fine_execution_inputs as inputs

    from fusion_baselines import protected_fine_geometry as geometry
    from fusion_baselines import protected_fine_process as process
    from fusion_baselines.protected_fine_graph import audit_fine_graph
    from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json
    from fusion_baselines.protected_search_journal import _encode
    from fusion_baselines.resource_guard import GIB, space_check

    return SimpleNamespace(
        inputs=inputs,
        fields=fields,
        geometry=geometry,
        process=process,
        graph=audit_fine_graph,
        Store=SnapshotStore,
        read=read_json,
        encode=_encode,
        GIB=GIB,
        space=space_check,
    )


def _same(d, actual, expected, label):
    _need(d.encode(actual) == d.encode(expected), "exact fine study binding: " + label)


def _command(reference, fd, root):
    return [
        sys.executable,
        str(Path(__file__).with_name("run_protected_fine_worker.py")),
        "--config-reference",
        json.dumps(reference, sort_keys=True, allow_nan=False),
        "--control-fd",
        str(fd),
        "--root",
        str(root),
    ]


def _linked(d, reference, case, source, output):
    """Recheck explicit acknowledgement/control/config/envelope, not file discovery."""
    ack = d.read(reference)
    fixed = dict(
        schema_version=1,
        kind="protected-fine-parent-acknowledgement",
        parent_acknowledged=True,
        complete_execution=True,
        returncode=0,
        threads=THREADS,
        acknowledgement_clock_scope="before-terminal-publication",
        independent_physical_audit_pass=False,
        **d.process.SCOPE,
    )
    _need(
        type(ack) is dict
        and set(ack)
        == set(fixed)
        | {
            "case",
            "config",
            "source",
            "parent_pid",
            "worker_pid",
            "owned_process_group",
            "started_monotonic",
            "spawned_monotonic",
            "exited_monotonic",
            "acknowledged_monotonic",
            "minimum_observed_free_bytes",
            "control_observations",
            "returned_result",
        },
        "exact complete fine parent acknowledgement required",
    )
    _need(
        type(ack["minimum_observed_free_bytes"]) is int
        and ack["minimum_observed_free_bytes"] >= 2 * d.GIB,
        "acknowledged live disk reserve required",
    )
    for key, expected in fixed.items():
        _same(d, ack[key], expected, "acknowledgement " + key)
    _same(d, ack["case"], case, "acknowledged case")
    parent, worker = ack["parent_pid"], ack["worker_pid"]
    _need(
        type(parent) is type(worker) is int and parent > 1 and worker > 1 and parent != worker,
        "distinct exact parent/worker PIDs required",
    )
    _same(d, ack["owned_process_group"], worker, "retired owned process group")
    times = [
        _clock(ack[key])
        for key in (
            "started_monotonic",
            "spawned_monotonic",
            "exited_monotonic",
            "acknowledged_monotonic",
        )
    ]
    _need(times == sorted(times), "forward fine parent clocks required")
    config = d.read(ack["config"])
    d.process._configuration(config, started=times[0], parent_pid=parent, output=output)
    _same(d, config["case"], case, "configured case")
    _same(d, config["source"], ack["source"], "acknowledged source reference")
    _same(d, d.read(config["source"]), source, "complete configured source")
    observations = ack["control_observations"]
    _need(
        type(observations) is list and len(observations) == 1,
        "one explicit fine returned-reference observation required",
    )
    observation = d.read(observations[0])
    _need(
        type(observation) is dict
        and set(observation)
        == {"schema_version", "kind", "observed_monotonic", "worker_pid", "message"},
        "exact fine parent control observation required",
    )
    for key, expected in dict(
        schema_version=1, kind="protected-fine-parent-control-observation", worker_pid=worker
    ).items():
        _same(d, observation[key], expected, "control observation " + key)
    observed = _clock(observation["observed_monotonic"])
    _need(
        times[1] <= observation["message"]["monotonic"] <= observed <= times[2],
        "control return inside actual launched lifetime",
    )
    reader = d.process.FineControlReader(times[0])
    reader.feed(d.encode(observation["message"]), observed)
    reader.check(times[3])
    messages = reader.finish()
    _same(d, reader.returned, ack["returned_result"], "explicit control return")
    envelope = d.process._returned(
        ack["returned_result"],
        config,
        ack["config"],
        worker_pid=worker,
        spawned=times[1],
        message=messages[0],
    )
    core = d.read(envelope["fine_result"])
    _same(d, core["source"], config["source"], "core source reference")
    return ack, envelope["fine_result"], config["source"]


def _audit_reports(d, graph, fields, geometry, case):
    for report, kind in (
        (graph, "protected-fine-graph-audit"),
        (fields, "protected-fine-saved-field-audit"),
        (geometry, "protected-fine-independent-geometry"),
    ):
        _same(d, report["schema_version"], 1, "audit schema")
        _same(d, report["kind"], kind, "audit kind")
        _same(d, report["case"], case, "audit case")
    _need(
        graph["graph_consistency"] is True
        and fields["arithmetic_consistency"] is True
        and geometry["geometry_consistency"] is True,
        "complete graph and independent arithmetic reconstruction required",
    )
    for report, scope in (
        (graph, d.process.SCOPE),
        (fields, d.fields.SCOPE),
        (geometry, d.geometry.SCOPE),
    ):
        for key in scope:
            _need(report[key] is False, "component cannot broaden scope: " + key)
    _need(graph["complete_execution"] is False, "graph cannot acknowledge worker")
    _same(d, fields["status"], "completed", "complete independent field audit")
    _same(d, graph["geometry_work"], geometry["producer_work"], "producer geometry work")
    for report, keys in (
        (fields, ("fine_numerical_qualification", "field_limits_pass")),
        (geometry, ("continuous_geometry_pass", "sampled_geometry_pass")),
    ):
        _need(all(type(report[key]) is bool for key in keys), "exact qualification booleans")
    expected = {
        key: dict(attempted=n, completed=n)
        for key, n in (("initialization", 8), ("operation", 24), ("native", 80), ("points", 552960))
    }
    _same(d, graph["counts"], expected, "complete fixed fine native work")
    _same(
        d,
        fields["independent_work"],
        dict(
            initializer_scalar_checks=8,
            diagnostic_reconstructions=6,
            flux_grid_reconstructions=18,
            sampled_BA_statistics=72,
            sampled_vectors=4608,
            sampled_scalar_components=13824,
            refinement_checks=5,
            flux_checks=63,
            native_requests=0,
            native_model_constructions=0,
            producer_certificates=0,
            equilibrium_solves=0,
            search_calls=0,
        ),
        "complete independent numerical work",
    )
    _same(
        d,
        geometry["independent_work"],
        dict(certificate_recomputations=1, surface_reconstructions=2, direct_grids=4),
        "complete independent geometry work",
    )
    for key in ("field_calls", "gradient_calls", "equilibrium_solves"):
        _same(d, geometry[key], 0, "field-free geometry " + key)
    numerical = fields["fine_numerical_qualification"]
    absolute = (
        numerical
        and fields["field_limits_pass"]
        and geometry["continuous_geometry_pass"]
        and geometry["sampled_geometry_pass"]
    )
    return dict(
        complete_execution=True,
        arithmetic_consistency=True,
        fine_numerical_qualification=numerical,
        absolute_field_geometry_pass=absolute,
    )


def run(output, *, root=ROOT):
    """Run exactly eight admitted fixed cases; never retry, resume or change candidates."""
    global _RUNNING, _POISONED
    if _RUNNING:
        _POISONED = True
        raise ValueError("fine studies must run serially")
    _RUNNING, _POISONED = True, False
    try:
        return _run(Path(output).resolve(), Path(root).resolve())
    finally:
        _RUNNING = False


def _run(output, root):
    _threads()
    _need(os.name == "posix", "fine study requires POSIX")
    output.mkdir(exist_ok=False)
    d = store = source = initial_source = None
    records, outcomes, matrix = [], [], _cases()
    checking = False
    last_clock = _clock(time.monotonic())

    def healthy():
        _threads()
        _need(
            not _POISONED and (store is None or store._failed is False),
            "fine study/publication poisoned",
        )

    def guard():
        nonlocal checking, last_clock
        entered = False
        try:
            healthy()
            _need(not checking, "reentrant fine study guard")
            checking = entered = True
            now = _clock(time.monotonic())
            _need(now >= last_clock, "forward study/audit clock required")
            last_clock = now
            d.space(output, 2 * d.GIB)
            healthy()
            now = _clock(time.monotonic())
            _need(now >= last_clock, "forward clock after resource callback required")
            last_clock = now
        except BaseException:
            global _POISONED
            _POISONED = True
            raise
        finally:
            if entered:
                checking = False

    def save(name, payload):
        guard()
        reference = store.json(name, copy.deepcopy(payload))
        healthy()
        guard()
        return reference

    def unchanged():
        guard()
        _same(d, d.inputs.sources(root), source, "unchanged admitted fine source")
        guard()

    for index, case in enumerate(matrix):
        attempt = acknowledgement_ref = audit_ref = None
        cell_output = output / f"cell-{index:02d}-{case['label']}"
        try:

            def config(
                started, parent_pid, threads, *, index=index, case=case, cell_output=cell_output
            ):
                nonlocal d, store, source, initial_source, attempt
                healthy()
                if d is None:
                    d = _dependencies()
                    healthy()
                    store = d.Store(output / "study")
                observed = d.inputs.sources(root)
                healthy()
                if source is None:
                    source = copy.deepcopy(observed)
                    initial_source = save("source-before", source)
                else:
                    _same(d, observed, source, "unchanged next-cell source")
                attempt = save(
                    f"attempt-{index:02d}",
                    dict(
                        schema_version=1,
                        kind="protected-fine-case-attempt",
                        status="attempted",
                        index=index,
                        case=case,
                        source=initial_source,
                        **SCOPE,
                    ),
                )
                return dict(
                    schema_version=1,
                    kind="protected-fine-worker-config",
                    case=case,
                    source=save(f"cell-source-{index:02d}", observed),
                    output=str(cell_output / "worker"),
                    parent_pid=parent_pid,
                    started_monotonic=started,
                    threads=threads,
                )

            def source_check(configuration):
                unchanged()
                _same(d, d.read(configuration["source"]), source, "parent source reference")
                return True

            def validate_return(reference, configuration):
                guard()
                envelope = d.read(reference)
                core = d.read(envelope["fine_result"])
                _same(d, core["source"], configuration["source"], "returned core source")
                guard()
                return True

            acknowledgement_ref = _supervise(
                config,
                lambda ref, fd: _command(ref, fd, root),
                cell_output,
                source_check=source_check,
                validate_return=validate_return,
            )
            guard()
            ack, core_ref, source_ref = _linked(d, acknowledgement_ref, case, source, cell_output)
            audit_started = _clock(time.monotonic())
            unchanged()
            context = d.inputs.build_context(source, case)
            guard()
            graph = d.graph(core_ref, context, source_ref, guard)
            graph_ref = save(f"graph-{index:02d}", graph)
            fields = d.fields.audit_fields(
                context,
                source["archive"],
                graph["initialization_rows"],
                graph["operation_rows"],
                guard,
            )
            fields_ref = save(f"fields-{index:02d}", fields)
            geometry = d.geometry.audit_geometry(
                context, source["archive"], graph["geometry_rows"], guard
            )
            geometry_ref = save(f"geometry-{index:02d}", geometry)
            outcome = _audit_reports(d, graph, fields, geometry, case)
            _same(d, graph["reference"], core_ref, "graph core reference")
            _same(d, graph["source"], source_ref, "graph admitted source reference")
            _same(d, fields["coarse"], context["coarse"], "field audit fixed coarse selection")
            unchanged()
            for ref, expected in (
                (graph_ref, graph),
                (fields_ref, fields),
                (geometry_ref, geometry),
            ):
                _same(d, d.read(ref), expected, "unchanged published independent audit")
            d.read(core_ref)
            audit_ended = _clock(time.monotonic())
            _need(audit_ended >= audit_started, "forward independent audit clock")
            audit_ref = save(
                f"audit-{index:02d}",
                dict(
                    schema_version=1,
                    kind="protected-fine-independent-audit",
                    status="completed",
                    case=case,
                    source=source_ref,
                    cell_result=core_ref,
                    parent_acknowledgement=acknowledgement_ref,
                    graph=graph_ref,
                    fields=fields_ref,
                    geometry=geometry_ref,
                    audit_started_monotonic=audit_started,
                    audit_ended_monotonic=audit_ended,
                    audit_clock_scope="posthoc-source-context-graph-field-geometry-checks",
                    independent_audit_seconds=audit_ended - audit_started,
                    **outcome,
                    **SCOPE,
                ),
            )
            record = save(
                f"case-{index:02d}",
                dict(
                    schema_version=1,
                    kind="protected-fine-case",
                    status="completed",
                    index=index,
                    case=case,
                    attempt=attempt,
                    parent_acknowledgement=acknowledgement_ref,
                    cell_result=core_ref,
                    independent_audit=audit_ref,
                    fine_execution_seconds_before_acknowledgement_publication=ack[
                        "acknowledged_monotonic"
                    ]
                    - ack["started_monotonic"],
                    counts=graph["counts"],
                    **outcome,
                    **SCOPE,
                ),
            )
            records.append(record)
            outcomes.append(outcome)
        except BaseException as error:
            if store is not None:
                try:
                    save(
                        f"failure-{index:02d}",
                        dict(
                            schema_version=1,
                            kind="protected-fine-case-failure",
                            status="failed",
                            case=case,
                            attempt=attempt,
                            parent_acknowledgement=acknowledgement_ref,
                            independent_audit=audit_ref,
                            completed_cases=records,
                            following_cases_unexecuted=matrix[index + 1 :],
                            complete_failed_tail_work_count_known=False,
                            error=type(error).__name__ + ": " + str(error),
                            error_notes=list(getattr(error, "__notes__", [])),
                            **SCOPE,
                        ),
                    )
                except BaseException as recording_error:
                    error.add_note("Could not publish failure record: " + repr(recording_error))
            raise
    unchanged()
    after_ref = save("source-after", source)
    totals = {key: all(row[key] for row in outcomes) for key in outcomes[0]}
    return save(
        "summary",
        dict(
            schema_version=1,
            kind="protected-fixed-candidate-fine-study",
            status="completed",
            source_before=initial_source,
            source_after=after_ref,
            matrix=matrix,
            cases=records,
            completed_cases=len(records),
            all_eight_executions_acknowledged=len(records) == 8,
            confirmed_work=dict(
                native_requests=640,
                native_points=4423680,
                initializer_scalar_checks=64,
                sampled_BA_statistics=576,
                sampled_vectors=36864,
                sampled_scalar_components=110592,
            ),
            numerical_qualified_cases=sum(row["fine_numerical_qualification"] for row in outcomes),
            absolute_qualified_cases=sum(row["absolute_field_geometry_pass"] for row in outcomes),
            failure_policy="stop-without-retry",
            selection_policy="fixed-coarse-selected-states",
            **totals,
            **SCOPE,
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(run(args.output, root=args.root)["path"])


if __name__ == "__main__":
    main()
