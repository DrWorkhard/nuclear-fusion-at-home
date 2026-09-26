"""Serial diagnostic pilot connection; native admission is closed until qualified.

Uses explicit returned parent/audit references, never discovers results. The
original scientific protocol and its separate fine phase are unchanged.
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
THREADS = {
    key: "1"
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    )
}
SCOPE = dict(
    physical_admission=False,
    fine_grid_acceptance=False,
    realized_field_transfer=False,
    step4_pass=False,
    sota_advance=False,
    ms1_reached=False,
    resolved_fine_grid_improvement=False,
    pareto_dominance=False,
)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _threads():
    _need(
        {key: os.environ.get(key) for key in THREADS} == THREADS,
        "set all four registered thread variables to 1 before scientific imports",
    )


def _dependencies():
    import audit_protected_cell_physics as physics
    import protected_native_inputs as native
    import protected_pilot_inputs as inputs
    from protected_native_adapter import NativeAdapter
    from run_protected_cell_worker import run_worker

    from fusion_baselines.protected_cell_audit import audit_cell
    from fusion_baselines.protected_process import _configuration, _returned, supervise_cell
    from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json
    from fusion_baselines.protected_search_journal import _encode
    from fusion_baselines.protected_worker_control import ControlReader
    from fusion_baselines.resource_guard import GIB, space_check

    return SimpleNamespace(
        physics=physics,
        native=native,
        inputs=inputs,
        NativeAdapter=NativeAdapter,
        run_worker=run_worker,
        audit_cell=audit_cell,
        supervise_cell=supervise_cell,
        Store=SnapshotStore,
        read=read_json,
        GIB=GIB,
        space=space_check,
        configuration=_configuration,
        returned=_returned,
        ControlReader=ControlReader,
        encode=_encode,
    )


def _native(source):
    return source["physics_sources"]["native_sources"]


def worker(config_reference, control_fd, *, root=ROOT):
    """Explicit native dependencies; parent supplies the inherited control pipe."""
    _threads()
    d = _dependencies()
    return d.run_worker(
        config_reference,
        control_fd,
        bind_sources=d.inputs.sources,
        build_context=lambda source, case: d.native.build_context(_native(source), case),
        adapter_factory=lambda context, source: d.NativeAdapter(context, _native(source)),
        root=root,
    )


def _clock(value):
    _need(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "finite nonnegative launch/audit clock",
    )
    return value


def _linked(d, acknowledgement_ref, case, source, cell_output):
    acknowledgement = d.read(acknowledgement_ref)
    d.native.previous._fields(
        acknowledgement,
        dict(
            schema_version=1,
            kind="protected-parent-acknowledgement",
            parent_acknowledged=True,
            returncode=0,
            threads=THREADS,
        ),
        "explicit returned successful parent acknowledgement",
    )
    _need(d.native.same(acknowledgement["case"], case), "acknowledged case")
    for key in ("physical_admission", "step4_pass", "independent_physical_audit_pass"):
        _need(acknowledgement[key] is False, "parent cannot claim " + key)
    config = d.read(acknowledgement["config"])
    d.configuration(
        config,
        started=acknowledgement["started_monotonic"],
        parent_pid=acknowledgement["parent_pid"],
        output=cell_output,
    )
    _need(
        d.native.same(config["case"], case)
        and d.native.same(config["source"], acknowledgement["source"])
        and d.native.same(d.read(config["source"]), source),
        "exact acknowledged source/case",
    )
    worker_pid = acknowledgement["worker_pid"]
    _need(
        type(worker_pid) is int
        and worker_pid > 1
        and type(acknowledgement["parent_pid"]) is int
        and acknowledgement["parent_pid"] > 1
        and worker_pid != acknowledgement["parent_pid"]
        and d.native.same(acknowledgement["owned_process_group"], worker_pid),
        "exact owned worker/parent process identity",
    )
    clocks = [
        _clock(acknowledgement[key])
        for key in (
            "started_monotonic",
            "spawned_monotonic",
            "exited_monotonic",
            "acknowledged_monotonic",
        )
    ]
    _need(clocks == sorted(clocks), "forward acknowledged construction clocks")
    reader = d.ControlReader(clocks[0])
    observations = acknowledgement["control_observations"]
    _need(
        type(observations) is list and len(observations) == 3,
        "three explicitly linked parent phase observations",
    )
    for reference in observations:
        observation = d.read(reference)
        d.native.previous._fields(
            observation,
            dict(
                schema_version=1,
                kind="protected-parent-control-observation",
                worker_pid=worker_pid,
            ),
            "parent control observation identity",
        )
        observed = _clock(observation["observed_monotonic"])
        _need(
            clocks[1] <= observation["message"]["monotonic"] <= observed <= clocks[2],
            "control observation inside actual launched lifetime",
        )
        reader.feed(d.encode(observation["message"]), observed)
    reader.check(clocks[3])
    messages = reader.finish()
    _need(
        d.native.same(reader.returned, acknowledgement["returned_result"]),
        "acknowledgement binds explicit control return",
    )
    envelope = d.returned(
        acknowledgement["returned_result"],
        config,
        acknowledgement["config"],
        worker_pid=worker_pid,
        search_ended=reader.search_ended,
        message=messages[-1],
    )
    return acknowledgement, envelope["cell_result"]


def _audit_link(d, reference, cell_reference, case, source, context):
    report = d.read(reference)
    d.native.previous._fields(
        report,
        dict(
            schema_version=1,
            kind="protected-saved-physics-audit",
            status="completed",
            startup_reconstruction_timing="posthoc",
        ),
        "complete returned posthoc saved-physics report",
    )
    _need(
        d.native.same(report["cell_result"], cell_reference)
        and d.native.same(report["case"], case)
        and d.native.same(d.read(report["supplied_source"]), _native(source)),
        "independent report/source/case/cell linkage",
    )
    _need(
        d.native.same(
            d.read(report["supplied_context"]), d.native.contract.context_metadata(context)
        ),
        "independent report binds exact original context",
    )
    for key in ("changes_are_resolved_fine_grid_improvements", "pareto_dominance"):
        _need(report[key] is False, "diagnostic reconstruction cannot claim " + key)
    for key in (
        "reconstruction_component_pass",
        "saved_graph_integrity_pass",
        "saved_metrics_reconstruction_pass",
        "sampled_direct_BA_pass",
        "cumulative_certificates_verified",
        "protected_directional_startup_pass",
    ):
        _need(report[key] is True, "independent coarse verification: " + key)
    for key in d.physics.SCOPE:
        _need(report[key] is False, "preserve reconstruction scope: " + key)
    # Fresh graph check closes the report linkage; source authentication remains
    # the launcher's explicit before/after checks, not a claim by the component.
    graph = d.audit_cell(cell_reference, context)
    _need(graph["integration_integrity_pass"] is True, "final complete cell graph")
    _need(
        d.native.same(d.read(report["graph_audit"]), graph),
        "independent report binds complete graph audit",
    )
    work = report["independent_work"]
    bundles = graph["complete_bundles"]
    certificates = sum(row["completed"] for row in graph["counts"]["certificate"].values())
    d.native.previous._fields(
        work,
        dict(
            certificate_recomputations=certificates,
            bundle_reconstructions=bundles,
            sampled_comparison_statistics=6 * bundles,
            sampled_vectors=384 * bundles,
            sampled_scalar_components=1152 * bundles,
            startup_directional_checks=8,
            native_requests=0,
            native_model_constructions=0,
            producer_certificate_calls=0,
            equilibrium_solves=0,
            search_calls=0,
        ),
        "all recorded construction work independently reconstructed",
    )
    return report, graph


def run(output, *, root=ROOT):
    """Run the exact eight-case construction; stop on any execution/audit failure.

    Conservative failure policy: no subsequent case or automatic retry follows
    a raised error. Already returned references and failed prefixes are preserved.
    This does not run or waive the independently qualified fine phase.
    """
    _threads()
    d = _dependencies()
    output = Path(output).resolve()
    d.space(output.parent, 3 * d.GIB)
    store = d.Store(output)

    def guard():
        _need(store._failed is False, "pilot publication poisoned")
        _threads()
        d.space(output, 2 * d.GIB)
        _need(store._failed is False, "pilot publication poisoned")

    def save(name, payload):
        guard()
        ref = store.json(name, payload)
        _need(store._failed is False, "pilot publication poisoned")
        return ref

    guard()
    source = d.inputs.sources(root)
    initial_source = save("source-before", source)
    matrix = _native(source)["cell_sources"]["matrix"]
    _need(d.native.same(matrix, d.native.previous.matrix()), "exact eight-case pilot order")
    records, confirmed = [], dict(native_requests=0, bundles=0, certificates=0)
    for index, case in enumerate(matrix):
        guard()
        attempt = save(
            f"attempt-{index:02d}",
            dict(
                schema_version=1,
                kind="protected-pilot-case-attempt",
                index=index,
                case=case,
                source=initial_source,
                status="attempted",
                **SCOPE,
            ),
        )
        cell_output = output / f"cell-{index:02d}-{case['label']}"
        acknowledgement_ref = None
        audit_ref = None
        try:

            def config(
                started,
                parent_pid,
                threads,
                *,
                case=case,
                index=index,
                cell_output=cell_output,
            ):
                observed = d.inputs.sources(root)
                _need(d.native.same(observed, source), "unchanged cell-launch source")
                return dict(
                    schema_version=1,
                    kind="protected-cell-worker-config",
                    case=copy.deepcopy(case),
                    source=save(f"cell-source-{index:02d}", observed),
                    output=str(cell_output / "worker"),
                    parent_pid=parent_pid,
                    started_monotonic=started,
                    threads=threads,
                )

            def source_check(configuration):
                observed = d.inputs.sources(root)
                return d.native.same(observed, source) and d.native.same(
                    observed, d.read(configuration["source"])
                )

            def validate_return(reference, configuration):
                envelope = d.read(reference)
                context = d.native.build_context(_native(source), configuration["case"])
                return d.audit_cell(envelope["cell_result"], context)["integration_integrity_pass"]

            def command(reference, fd):
                return [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "worker",
                    "--config",
                    json.dumps(reference),
                    "--fd",
                    str(fd),
                ]

            acknowledgement_ref = d.supervise_cell(
                config,
                command,
                cell_output,
                source_check=source_check,
                validate_return=validate_return,
            )
            guard()
            acknowledgement, cell_ref = _linked(d, acknowledgement_ref, case, source, cell_output)
            context = d.native.build_context(_native(source), case)
            audit_started = _clock(time.monotonic())
            audit_ref = d.physics.audit_saved_cell(
                cell_ref,
                context,
                _native(source),
                output=output / f"audit-{index:02d}-{case['label']}",
            )
            audit_ended = _clock(time.monotonic())
            _need(audit_ended >= audit_started, "forward independent audit clock")
            audit_seconds = audit_ended - audit_started
            guard()
            report, graph = _audit_link(d, audit_ref, cell_ref, case, source, context)
            _need(d.native.same(d.inputs.sources(root), source), "unchanged post-audit source")
            counts = dict(
                native_requests=graph["counts"]["native"]["completed"],
                bundles=graph["complete_bundles"],
                certificates=sum(v["completed"] for v in graph["counts"]["certificate"].values()),
            )
            for key, maximum in dict(native_requests=290, bundles=32, certificates=128).items():
                _need(
                    type(counts[key]) is int and 0 <= counts[key] <= maximum,
                    "registered per-case " + key,
                )
                confirmed[key] += counts[key]
            records.append(
                save(
                    f"case-{index:02d}",
                    dict(
                        schema_version=1,
                        kind="protected-pilot-case",
                        status="completed",
                        index=index,
                        case=case,
                        attempt=attempt,
                        parent_acknowledgement=acknowledgement_ref,
                        independent_reconstruction=audit_ref,
                        cell_result=cell_ref,
                        counts=counts,
                        construction_seconds=acknowledgement["acknowledged_monotonic"]
                        - acknowledgement["started_monotonic"],
                        independent_audit_seconds=audit_seconds,
                        construction_completed=True,
                        independent_coarse_verification_pass=True,
                        diagnostic_changes=report["diagnostic_changes"],
                        **SCOPE,
                    ),
                )
            )
        except BaseException as error:
            try:
                save(
                    f"failure-{index:02d}",
                    dict(
                        schema_version=1,
                        kind="protected-pilot-case-failure",
                        status="failed",
                        case=case,
                        attempt=attempt,
                        parent_acknowledgement=acknowledgement_ref,
                        independent_reconstruction=audit_ref,
                        error=type(error).__name__ + ": " + str(error),
                        error_notes=list(getattr(error, "__notes__", [])),
                        following_cases_unexecuted=matrix[index + 1 :],
                        complete_failed_tail_work_count_known=False,
                        **SCOPE,
                    ),
                )
            except BaseException as recording_error:
                error.add_note("Could not publish failure record: " + repr(recording_error))
            raise
    guard()
    after = d.inputs.sources(root)
    _need(d.native.same(after, source), "unchanged complete study source graph")
    after_ref = save("source-after", after)
    return save(
        "summary",
        dict(
            schema_version=1,
            kind="protected-coil-fit-construction",
            status="completed",
            source_before=initial_source,
            source_after=after_ref,
            matrix=matrix,
            cases=records,
            completed_cases=len(records),
            all_eight_constructions_complete=len(records) == 8,
            all_eight_independent_coarse_verifications_pass=len(records) == 8,
            confirmed_work=confirmed,
            failure_policy="stop-without-retry",
            fine_phase="required-not-run",
            **SCOPE,
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    study = sub.add_parser("run", help="registered construction, only after complete qualification")
    study.add_argument("output", type=Path)
    child = sub.add_parser("worker", help=argparse.SUPPRESS)
    child.add_argument("--config", required=True)
    child.add_argument("--fd", required=True, type=int)
    args = parser.parse_args()
    if args.mode == "worker":
        worker(json.loads(args.config), args.fd)
    else:
        print(run(args.output)["path"])


if __name__ == "__main__":
    main()
