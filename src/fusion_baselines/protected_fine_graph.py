"""Independent saved fine graph/accounting checks, without physical acceptance.

Require an explicit core reference plus separately admitted source and context.
Read every new raw archive and the complete journal. Old source admission and
independent field/geometry maths remain separate; paired events cannot prove
that the reported native routine actually computed correct physics.
"""

import copy
import hashlib
from pathlib import Path

from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_fine_cell import context_metadata
from fusion_baselines.protected_fine_process import SCOPE
from fusion_baselines.protected_run_ledger import _clock, _reference
from fusion_baselines.protected_run_snapshots import read_arrays, read_json
from fusion_baselines.protected_search_journal import _encode, read_events


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, message):
    _need(_encode(actual) == _encode(expected), message)


def _keys(value, keys, message):
    _need(type(value) is dict and set(value) == set(keys), message)


def _calls(spec, operation):
    # Separate spelling of the registered sequence, not replay of the producer's
    # ledger. Both this schedule and the planner remain source-qualified code.
    if operation is None:
        return [("loop", "A", 256)]
    if spec["kind"] == "diagnostic":
        g = spec["grid"]
        b, i = g["nphi"] * g["ntheta"], 3 * g["ninner"] ** 2
        return [("boundary", "B", b), ("inner", "B", i), ("loop", "A", 256),
                ("boundary", "A", b), ("inner", "A", i), ("loop", "B", 256)]
    n = operation["ntheta"] * operation.get("nrho", 1)
    return [("loop", q, n) for q in (("A", "B") if operation["form"] == "line" else ("B", "A"))]


def _geometry_work(case, nodes):
    p = case["nbase"] * 4
    pairs = p * (p - 1) // 2
    return {
        key: dict(attempted=n, completed=n, points_attempted=count, points_completed=count)
        for key, n, count in (("fourier", 3, 3 * p * nodes), ("cp", 2, 2 * p * nodes),
                              ("cc", pairs, pairs * nodes))
    }


def _native_pair(attempt, outcome, identity, expected, index, last_clock):
    for row, event in ((attempt, "native-attempted"), (outcome, "native-completed")):
        _keys(row, {*identity, "event", "native"}, "exact fine native journal row")
        _same({k: row[k] for k in identity}, identity, "native operation identity")
        _same(row["event"], event, "paired fine native event order")
    before, after = attempt["native"], outcome["native"]
    keys = {"index", "field", "quantity", "points", "status", "started_monotonic",
            "native_started", "native_completed"}
    _keys(before, keys, "exact fine attempted native schema")
    _keys(after, keys | {"completed_monotonic"}, "exact fine completed native schema")
    field, quantity, points = expected
    fixed = dict(index=index, field=field, quantity=quantity, points=points)
    for key, value in fixed.items():
        _same(before[key], value, "native expected " + key)
        _same(after[key], value, "completed native expected " + key)
    _same(before["status"], "attempted", "native attempt status")
    _same(after["status"], "completed", "native completed status")
    _need(before["native_started"] is False and before["native_completed"] is False,
          "reservation before native work")
    _need(after["native_started"] is True and after["native_completed"] is True,
          "successful paired native outcome")
    _clock(before["started_monotonic"])
    _clock(after["completed_monotonic"])
    _same(before["started_monotonic"], after["started_monotonic"], "exact native start identity")
    _need(last_clock <= before["started_monotonic"] <= after["completed_monotonic"],
          "forward native observation clocks")
    return after["completed_monotonic"]


def audit_fine_graph(reference, context, source_reference, guard):
    """Return checked raw rows for the separately guarded numerical auditor.

    No file discovery, no writes, no native imports/calls and no inference from
    filename alone. This does not acknowledge a worker or replace source intake.
    """
    _need(callable(guard), "explicit fine audit resource guard required")
    _reference(reference)
    _reference(source_reference)
    guard()
    core = read_json(reference)
    data_dir = Path(reference["path"]).parent
    _need(data_dir.resolve() == data_dir and not data_dir.is_symlink(),
          "direct owned data directory")
    _need(Path(reference["path"]).name == "result.json", "explicit fine terminal record")
    expected_counts = {
        key: dict(attempted=n, completed=n)
        for key, n in (("initialization", 8), ("operation", 24), ("native", 80), ("points", 552960))
    }
    _keys(core, {
        "schema_version", "kind", "case", "source", "context", "initializations", "operations",
        "geometry", "counts", "geometry_work", "journal", "producer_complete",
        "complete_execution", *SCOPE,
    }, "exact complete fine core schema")
    _same(core["schema_version"], 1, "fine core schema version")
    _same(core["kind"], "protected-fine-cell-execution", "fine core kind")
    case = context["case"]
    plan.validate_case(case)
    _same(core["case"], case, "source-admitted fine case")
    _same(core["source"], source_reference, "exact externally admitted fine source")
    read_json(source_reference)
    _need(core["producer_complete"] is True, "complete fine producer required")
    _need(all(core[k] is False for k in ("complete_execution", *SCOPE)),
          "core cannot assert acknowledgment or physical success")
    _same(core["counts"], expected_counts, "exact registered complete fine counts")
    for key, count in (("initializations", 8), ("operations", 24), ("geometry", 4)):
        _need(type(core[key]) is list and len(core[key]) == count, "all fixed fine " + key)

    def owned(ref, name, *, arrays=False):
        guard()
        _reference(ref)
        _same(ref["path"], str(data_dir / name), "exact owned fine raw path")
        result = read_arrays(ref) if arrays else read_json(ref)
        guard()
        return result

    _same(owned(core["context"], "context.json"), context_metadata(context),
          "complete unchanged fine context metadata")
    _keys(core["journal"], {"directory", "receipt"}, "exact fine journal locator")
    journal_dir = core["journal"]["directory"]
    _need(type(journal_dir) is str and Path(journal_dir).is_absolute(), "absolute fine journal")
    journal_path = Path(journal_dir)
    _need(journal_path.resolve() == journal_path and journal_path.parent == data_dir.parent
          and journal_path != data_dir and not journal_path.is_symlink(),
          "separate journal in owned worker directory")
    guard()
    events = read_events(journal_path, core["journal"]["receipt"])
    guard()
    _need(len(events) == 225, "all 225 fine dispatch journal records required")
    x = plan._coordinates(case, context["selected"]["state"]["x"])
    digest = hashlib.sha256(x.tobytes()).hexdigest()
    initializations, operations = [], []
    cursor = sequence = native_count = point_count = op_index = 0
    last_clock = 0
    for model_index, spec in enumerate(plan.model_plan(case)):
        native_index = 0
        initialization_ref = core["initializations"][model_index]
        for operation in [None, *plan.operation_plan(spec, x)]:
            guard()
            kind = "initialization" if operation is None else "operation"
            op_id = "initialize/" + spec["id"] if operation is None else operation["operation_id"]
            identity = dict(kind=kind, model_id=spec["id"], operation_id=op_id,
                            case=case["label"], selected_coordinate_sha256=digest,
                            sequence=sequence)
            _same(events[cursor], dict(event="operation-attempted", **identity),
                  "exact ordered fine operation reservation")
            cursor += 1
            first_outcome = None
            for request in _calls(spec, operation):
                if first_outcome is None:
                    first_outcome = events[cursor + 1]["native"]
                last_clock = _native_pair(events[cursor], events[cursor + 1], identity,
                                          request, native_index, last_clock)
                cursor += 2
                native_count += 1
                native_index += 1
                point_count += request[2]
            completed = events[cursor]
            _keys(completed, {*identity, "event", "raw_reference"}, "fine completion raw linkage")
            expected_ref = initialization_ref if operation is None else core["operations"][op_index]
            _same(completed, dict(event="operation-completed", **identity,
                                 raw_reference=expected_ref),
                  "persisted raw reference before completion")
            if operation is None:
                row = owned(expected_ref, "initialize-" + spec["id"] + ".json")
                _keys(row, {"schema_version", "kind", "case", "spec", "metadata"},
                      "exact fine initialization record")
                _same(row["kind"], "protected-fine-initialization", "initialization kind")
                _same(row["metadata"]["initialization_native_calls"], [first_outcome],
                      "recorded actual original-seed initialization request")
                initializations.append(row)
            else:
                row = owned(expected_ref, op_id + ".json")
                _keys(row, {"schema_version", "kind", "status", "case", "spec", "operation",
                            "arrays", "record", "initialization"}, "exact fine operation record")
                _same(row["kind"], "protected-fine-operation", "operation kind")
                _same(row["status"], "completed", "complete fine raw operation")
                _same(row["initialization"], initialization_ref,
                      "own original-seed model reference")
                descriptor = {k: v for k, v in operation.items() if k != "x"}
                _same(row["operation"], descriptor, "fixed fine operation descriptor")
                owned(row["arrays"], op_id + "-arrays.npz", arrays=True)
                operations.append(row)
                op_index += 1
            _same(row["schema_version"], 1, "fine raw schema version")
            _same(row["case"], case, "fine raw case")
            _same(row["spec"], spec, "fine raw exact model")
            cursor += 1
            sequence += 1
    _need((cursor, sequence, native_count, point_count, op_index) == (224, 32, 80, 552960, 24),
          "independently counted full fine native schedule")
    _same(events[-1], dict(event="fine-dispatch-completed", case=case["label"],
                           selected_coordinate_sha256=digest, counts=expected_counts),
          "complete final fine dispatch record")
    grids = []
    total = {key: dict(attempted=0, completed=0, points_attempted=0, points_completed=0)
             for key in ("fourier", "cp", "cc")}
    levels = zip(plan.geometry_levels(), core["geometry"], strict=True)
    for index, (level, ref) in enumerate(levels):
        row = owned(ref, f"geometry-{index}.json")
        _keys(row, {"schema_version", "kind", "case", "record"}, "exact fine geometry wrapper")
        _same(row["schema_version"], 1, "geometry schema version")
        _same(row["kind"], "protected-fine-geometry", "geometry record kind")
        _same(row["case"], case, "geometry case")
        record = row["record"]
        _keys(record, {"level", "arrays", "codec", "sampling_work"}, "exact fine geometry row")
        _same(record["level"], level, "all fine geometry grids in order")
        budget = _geometry_work(case, level["ncoil"])
        _same(record["sampling_work"], budget, "all physical-pair geometry work")
        owned(record["arrays"], f"geometry-{index}-arrays.npz", arrays=True)
        for key, counters in budget.items():
            for counter, value in counters.items():
                total[key][counter] += value
        grids.append(record)
    _same(core["geometry_work"], dict(surfaces=dict(attempted=2, completed=2),
                                      direct_grids=dict(attempted=4, completed=4), sampling=total),
          "complete producer geometry work")
    guard()
    return dict(
        schema_version=1, kind="protected-fine-graph-audit", graph_consistency=True,
        reference=copy.deepcopy(reference), source=copy.deepcopy(source_reference), case=case,
        counts=expected_counts, initialization_rows=initializations, operation_rows=operations,
        geometry_rows=grids, geometry_work=copy.deepcopy(core["geometry_work"]),
        complete_execution=False, **SCOPE,
    )
