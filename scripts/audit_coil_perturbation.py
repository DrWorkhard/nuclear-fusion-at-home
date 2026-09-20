"""Independent saved-data admission of the registered field-free52-state matrix."""

import argparse
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
from audit_clear_coil_field_start import Evidence as HistoricalEvidence
from audit_clear_coil_field_start import typed_equal

from fusion_baselines import clear_coil_geometry_audit as geometry
from fusion_baselines import coil_perturbation_audit as mathematical
from fusion_baselines import coil_perturbation_direct_audit as direct
from fusion_baselines.provenance import sha256_file, write_json_atomic

ROOT = Path(__file__).resolve().parents[1]
GIB = 1024**3
THREADS = {k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")}
SCOPE = dict(
    field_calls=0,
    gradient_calls=0,
    equilibrium_solves=0,
    search_calls=0,
    lp_calls=0,
    search_allowed=False,
    field_pass=False,
    transfer_pass=False,
    step4_pass=False,
)
PENDING = dict(all_pass=False, qualification_pass=False, independent_audit_pass=False)
LIMITS = dict(
    wall_seconds=1800.0,
    parent_poll_seconds=0.5,
    termination_grace_seconds=5,
    start_reserve_bytes=3 * GIB,
    live_reserve_bytes=2 * GIB,
)
WORK_KEYS = ("states", "certificates", "direct_grids", "surfaces")
require = mathematical.require


def sources(root):
    from coil_perturbation_workflow_inputs import sources as bound_sources

    return bound_sources(root)


def matrix():
    return [
        dict(label=f"n{n}-shape-d100mm", nbase=n, order=m, geometry_report_index=i)
        for n, m, i in ((6, 5, 3), (8, 7, 9))
    ]


def identity(actual, expected, label):
    require(typed_equal(actual, expected), label)


def number(value, label):
    require(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        f"{label}: finite nonnegative clock/quantity",
    )
    return float(value)


class Evidence(HistoricalEvidence):
    def array(self, ref):
        # Preserve integer witnesses and boolean masks. Do not cache the full
        # matrix in RAM; only one grid is needed for independent reconstruction.
        with np.load(self.check(ref), allow_pickle=False) as archive:
            result = {key: archive[key].copy() for key in archive.files}
        require(
            all(v.dtype.kind in "biuf" and np.isfinite(v).all() for v in result.values()),
            "finite real/integer/boolean raw arrays without coercion",
        )
        return result


def zero_work():
    return {k: dict(attempted=0, completed=0) for k in WORK_KEYS}


def zero_sampling():
    return {
        k: dict(attempted=0, completed=0, points_attempted=0, points_completed=0)
        for k in ("fourier", "cp", "cc")
    }


def add_work(first, extra):
    return {k: {name: first[k][name] + extra[k][name] for name in first[k]} for k in first}


def source_identity(record, binding):
    identity(record.get("source_before"), record.get("source_after"), "unchanged execution sources")
    source = record["source_before"]
    require(type(source) is dict, "full original source binding")
    identity(
        {k: v for k, v in source.items() if k != "repository"},
        {k: v for k, v in binding.items() if k != "repository"},
        "all numerical sources exact; only outer repository metadata may change",
    )
    return source


def required_certification(states):
    require(
        len(states) == 26 and all(type(row.get("certified")) is bool for row in states),
        "complete typed candidate classifications",
    )
    selected = [row for row in states if row["kind"] != "probe" or row["radius"] == 1e-5]
    require(len(selected) == 8, "two seed states and six signed smallest probes per class")
    return bool(all(row["certified"] for row in selected))


def process_audit(evidence, result, case, source, previous_end=None):
    require(result.get("status") == "completed", "complete class producer required")
    identity(result.get("case"), case, "parent class identity")
    config, launch, process = (evidence.read(result[k]) for k in ("config", "launch", "process"))
    worker = evidence.read(result["worker"])
    directory = Path(result["config"]["path"]).parent
    identity(config.get("case"), case, "configured class")
    identity(config.get("source"), source, "configured immutable source")
    require(
        config.get("output") == str(directory) and directory.is_absolute(), "worker output path"
    )
    require(type(config.get("parent_pid")) is int and config["parent_pid"] > 0, "owned parent pid")
    started = number(config.get("started_monotonic"), "worker start")
    if previous_end is not None:
        require(started >= previous_end, "fresh class workers run serially")
    require(
        type(process.get("returncode")) is int
        and process["returncode"] == 0
        and process.get("timed_out") is False
        and not process.get("error_type"),
        "successful owned child process, not bool returncode",
    )
    elapsed = number(process.get("elapsed_seconds"), "parent elapsed")
    require(elapsed < 1800, "parent1800s wall budget")
    require(
        number(process.get("minimum_observed_free_bytes"), "parent free space") >= 2 * GIB,
        "parent live disk reserve",
    )
    start_space = config.get("start_space")
    require(
        type(start_space) is dict
        and type(start_space.get("required_bytes")) is int
        and start_space["required_bytes"] == 3 * GIB
        and number(start_space.get("free_bytes"), "launch free space") >= 3 * GIB,
        "recorded starting disk reserve",
    )
    identity(launch.get("case"), case, "launched class")
    identity(launch.get("started_monotonic"), config["started_monotonic"], "launch clock")
    command = launch.get("command")
    require(
        type(command) is list
        and len(command) == 4
        and Path(command[0]).is_absolute()
        and Path(command[0]).resolve() == Path(sys.executable).resolve(),
        "qualified interpreter",
    )
    identity(
        command[1:],
        [str(ROOT / "scripts/run_coil_perturbation.py"), "--worker", result["config"]["path"]],
        "exact recorded worker command",
    )
    require(
        worker.get("status") == "completed"
        and type(worker.get("schema_version")) is int
        and worker.get("schema_version") == 1
        and worker.get("kind") == "coil-perturbation-cell",
        "complete raw class schema",
    )
    identity(worker.get("case"), case, "raw class identity")
    identity(worker.get("source_before"), source, "worker original source")
    identity(worker.get("source_after"), source, "worker terminal source")
    identity(worker.get("threads"), THREADS, "one-thread environment")
    identity(worker.get("scope"), dict(SCOPE, **PENDING), "field-free pending producer scope")
    identity(worker.get("started_monotonic"), config["started_monotonic"], "worker initial clock")
    ended = number(worker.get("ended_monotonic"), "worker end")
    duration = number(worker.get("elapsed_seconds"), "worker elapsed")
    require(
        0 <= ended - started < 1800
        and abs(duration - (ended - started)) <= 1e-9
        and ended <= started + elapsed + 1e-9,
        "consistent complete worker wall time",
    )
    require(
        number(worker.get("minimum_observed_free_bytes"), "worker free space") >= 2 * GIB,
        "worker live disk reserve",
    )
    identity(config.get("build_surfaces"), case == matrix()[0], "only first class builds surfaces")
    require(
        config.get("surface_directory") == str(directory.parent / "surfaces"),
        "shared surface directory",
    )
    require(type(result.get("retained")) is list and result["retained"], "retained execution files")
    for ref in result["retained"]:
        require(Path(ref["path"]).is_relative_to(directory), "retained child execution artifact")
        evidence.check(ref)
    retained = {
        Path(ref["path"]).name: ref
        for ref in result["retained"]
        if Path(ref["path"]).parent == directory
    }
    require(
        "plan.json" in retained and "checkpoint.json" in retained,
        "retained complete plan and final worker checkpoint",
    )
    identity(
        evidence.read(retained["plan.json"]),
        dict(states=direct.plan(), levels=direct.levels(), case=case),
        "registered saved plan",
    )
    checkpoint_keys = (
        "states",
        "operations",
        "operation_attempts",
        "state_attempts",
        "work",
        "sampling_work",
    )
    checkpoint = evidence.read(retained["checkpoint.json"])
    require(
        type(checkpoint) is dict and "inflight" in checkpoint and "inflight" in worker,
        "both immutable checkpoint and separate live marker references required",
    )
    identity(
        {k: v for k, v in checkpoint.items() if k != "inflight"},
        {k: worker[k] for k in checkpoint_keys},
        "final worker checkpoint is the complete retained execution prefix",
    )
    require(
        type(worker.get("states")) is list
        and len(worker["states"]) == 26
        and type(worker.get("operation_attempts")) is list
        and worker["operation_attempts"],
        "complete ordered state and operation prefixes before marker binding",
    )
    final_directory = directory / direct.plan()[-1]["state_id"]
    require(
        Path(worker["states"][-1]["path"]).parent == final_directory,
        "final state resides in its registered immutable state directory",
    )
    require(
        evidence.check(checkpoint["inflight"]) == final_directory / "checkpoint-inflight.json",
        "checkpoint binds its own immutable per-state marker, never the mutable live marker",
    )
    require(
        evidence.check(worker["inflight"]) == directory / "inflight.json",
        "separate current live attempt marker",
    )
    expected_marker = dict(attempt=worker["operation_attempts"][-1])
    identity(
        evidence.read(checkpoint["inflight"]),
        expected_marker,
        "immutable checkpoint marker names the final ordered completed attempt",
    )
    identity(
        evidence.read(worker["inflight"]),
        expected_marker,
        "completed live marker agrees semantically without sharing mutable reference",
    )
    return worker, config, started, ended, started + elapsed


class LedgerAudit:
    def __init__(self, evidence, worker, started, ended):
        self.evidence, self.worker = evidence, worker
        self.work, self.sampling = zero_work(), zero_sampling()
        self.position, self.previous_end, self.ended = 0, started, ended
        self.states = 0

    def times(self, record):
        start = number(record.get("started_monotonic"), "operation start")
        end = number(record.get("ended_monotonic"), "operation end")
        require(
            self.previous_end <= start <= end <= self.ended,
            "sequential contained completed operation clocks",
        )
        self.previous_end = end

    def attempt(self, ref, descriptor, kind, *, state=False):
        document = self.evidence.read(ref)
        expected = dict(
            descriptor,
            status="attempted",
            kind=kind,
            started_monotonic=document.get("started_monotonic"),
            work_before=copy.deepcopy(self.work),
            reservation={key: int(key == kind) for key in WORK_KEYS},
        )
        identity(document, expected, "complete persisted one-call reservation and prefix")
        require(
            number(document["started_monotonic"], "attempt clock") >= self.previous_end,
            "attempt precedes only its own forward work",
        )
        self.previous_end = float(document["started_monotonic"])
        if state:
            identity(ref, self.worker["state_attempts"][self.states], "ordered state attempt")
            self.states += 1
        self.work[kind]["attempted"] += 1
        return document

    def operation(self, ref, kind, descriptor):
        identity(ref, self.worker["operations"][self.position], "complete ordered operation ledger")
        record = self.evidence.read(ref)
        descriptor = dict(descriptor, operation_index=self.position)
        if kind == "direct_grids":
            reservation = direct.bounded_work(descriptor["nphysical"], descriptor["level"]["ncoil"])
            descriptor.update(
                sampling_work_before=copy.deepcopy(self.sampling), sampling_reservation=reservation
            )
        attempt = self.attempt(record["attempt"], descriptor, kind)
        identity(
            record["attempt"],
            self.worker["operation_attempts"][self.position],
            "ordered operation attempted references",
        )
        self.position += 1
        require(
            record.get("status") == "completed" and not record.get("error_type"),
            "no missing/error raw operation",
        )
        for key, value in attempt.items():
            if key != "status":
                identity(record.get(key), value, "operation preserves its attempted identity")
        self.work[kind]["completed"] += 1
        identity(record.get("work_after"), self.work, "exact completed outer work prefix")
        if kind == "direct_grids":
            self.sampling = add_work(self.sampling, reservation)
            identity(
                record.get("sampling_work_after"),
                self.sampling,
                "full Fourier/CP/CC sampling counts and point prefixes",
            )
        self.times(record)
        return record

    def finish(self, first):
        identity(
            self.work,
            {
                k: dict(attempted=n, completed=n)
                for k, n in dict(
                    states=26, certificates=52, direct_grids=104, surfaces=2 if first else 0
                ).items()
            },
            "complete class work caps",
        )
        identity(self.worker.get("work"), self.work, "worker reported work")
        identity(self.worker.get("sampling_work"), self.sampling, "worker reported direct work")
        require(
            len(self.worker["operations"])
            == len(self.worker["operation_attempts"])
            == self.position
            and len(self.worker["state_attempts"]) == self.states == 26,
            "no omitted or extra attempted operations",
        )
        identity(
            self.evidence.read(self.worker["inflight"]),
            dict(attempt=self.worker["operation_attempts"][-1]),
            "final in-flight marker",
        )
        return dict(
            passed=True, work=copy.deepcopy(self.work), sampling_work=copy.deepcopy(self.sampling)
        )


def surface_audit(evidence, run, source):
    registry = evidence.read(run["surface_registry"])
    identity(
        registry,
        dict(schema_version=1, status="completed", fixed_surfaces=run["fixed_surfaces"]),
        "complete shared surface registry",
    )
    require(set(run["fixed_surfaces"]) == set(direct.TARGETS), "both shared surfaces")
    surfaces, records = {}, {}
    for target in direct.TARGETS:
        row = evidence.read(run["fixed_surfaces"][target])
        expected = dict(
            target=target,
            nphi=256,
            ntheta=256,
            offset=0,
            full_torus=True,
            source_input=source["targets"][target],
        )
        for key, value in expected.items():
            identity(row.get(key), value, "shared surface identity")
        raw = evidence.array(row["arrays"])
        require(
            set(raw) == {"points"} and raw["points"].shape == (256**2, 3),
            "complete fixed full-torus surface arrays",
        )
        independent = geometry.surface(evidence.read(source["targets"][target]), 256, 256, 0)
        mathematical.close(
            raw["points"],
            independent["points"].reshape(-1, 3),
            "independent full-torus source geometry",
        )
        operation = evidence.read(row["operation"])
        identity(
            {k: v for k, v in row.items() if k != "operation"},
            operation,
            "surface file is the persisted original operation",
        )
        # Downstream strict enclosures use the independently reconstructed
        # source, not producer points merely within the raw comparison tolerance.
        surfaces[target], records[target] = independent["points"].reshape(-1, 3), row
    return surfaces, records


def cell_audit(evidence, result, case, source, run, surfaces, surface_records, previous_end=None):
    worker, config, start, end, process_end = process_audit(
        evidence, result, case, source, previous_end
    )
    first = case == matrix()[0]
    identity(worker.get("fixed_surfaces"), run["fixed_surfaces"], "same two source surface files")
    identity(worker.get("surface_registry"), run["surface_registry"], "same source registry")
    identity(
        config.get("surface_registry"),
        None if first else run["surface_registry"],
        "no second-class rebuild",
    )
    seed_ref = source["seeds"][case["label"]]["snapshot"]
    identity(worker.get("seed_snapshot"), seed_ref, "fixed accepted seed reference")
    snapshot = evidence.read(seed_ref)
    report = evidence.read(source["geometry"]["audit"])["sets"][case["geometry_report_index"]]
    prescribed = direct.directions(snapshot)
    vectors = evidence.array(worker["directions"])
    require(set(vectors) == {"directions"}, "only the three predeclared directions")
    mathematical.close(vectors["directions"], prescribed, "independent deterministic directions")
    require(len(worker.get("states", [])) == 26, "all26 registered states including seed-repeat")
    ledger = LedgerAudit(evidence, worker, start, end)
    if first:
        for target in direct.TARGETS:
            row = surface_records[target]
            ledger.operation(
                row["operation"],
                "surfaces",
                dict(
                    target=target,
                    nphi=256,
                    ntheta=256,
                    offset=0,
                    full_torus=True,
                    source_input=source["targets"][target],
                ),
            )
    summaries, seed_state = [], None
    for descriptor, state_ref in zip(direct.plan(), worker["states"], strict=True):
        state = evidence.read(state_ref)
        for key, value in descriptor.items():
            identity(state.get(key), value, "ordered complete state descriptor")
        require(
            state.get("status") == "completed" and state.get("repeat_exact") is True,
            "state complete and both certificates byte-identical",
        )
        attempt = ledger.attempt(state["attempt"], descriptor, "states", state=True)
        identity(
            state.get("started_monotonic"), attempt["started_monotonic"], "state initial clock"
        )
        identity(state.get("work_before"), attempt["work_before"], "state starting work prefix")
        identity(state.get("seed_snapshot"), seed_ref, "state cumulative original reference")
        raw = evidence.array(state["candidate"])
        require(set(raw) == {"coefficients"}, "complete only named candidate coefficients")
        coefficients = direct.candidate(snapshot, descriptor, prescribed)
        mathematical.close(raw["coefficients"], coefficients, "prescribed cumulative candidate")
        if descriptor["kind"] != "probe":
            require(
                np.array_equal(raw["coefficients"], snapshot["base_coefficients"]),
                "bit-identical original seed/repeat coefficients",
            )
        certificate = mathematical.independent_certificate(snapshot, report, raw["coefficients"])
        require(
            certificate["calculation_complete"] is True, "all finite registered bound calculations"
        )
        require(
            len(state["certificates"]) == len(state["certificate_operations"]) == 2,
            "two complete certificate calls per state",
        )
        for repeat in range(2):
            operation = ledger.operation(
                state["certificate_operations"][repeat],
                "certificates",
                dict(
                    state_id=descriptor["state_id"],
                    state_index=descriptor["index"],
                    repeat=repeat,
                    candidate=state["candidate"],
                ),
            )
            identity(
                operation["certificate"], state["certificates"][repeat], "bound raw certificate"
            )
            mathematical.compare_certificate(evidence.read(operation["certificate"]), certificate)
        require(
            state["certificates"][0]["sha256"] == state["certificates"][1]["sha256"],
            "exact repeated certificate bytes",
        )
        require(len(state["direct"]) == 4, "every registered direct grid")
        checks = []
        for index, level in enumerate(direct.levels()):
            operation = ledger.operation(
                state["direct"][index],
                "direct_grids",
                dict(
                    state_id=descriptor["state_id"],
                    state_index=descriptor["index"],
                    level_index=index,
                    level=level,
                    candidate=state["candidate"],
                    nphysical=4 * case["nbase"],
                ),
            )
            checks.append(
                direct.audit_samples(
                    snapshot,
                    raw["coefficients"],
                    certificate,
                    level,
                    evidence.array(operation["arrays"]),
                    surfaces,
                )
            )
        ledger.work["states"]["completed"] += 1
        identity(state.get("work_after"), ledger.work, "state complete work prefix")
        state_end = number(state.get("ended_monotonic"), "state end")
        require(
            ledger.previous_end <= state_end <= end, "state terminal persisted after all operations"
        )
        ledger.previous_end = state_end
        if descriptor["kind"] == "seed":
            seed_state = state
        if descriptor["kind"] == "seed-repeat":
            require(
                state["certificates"][0]["sha256"] == seed_state["certificates"][0]["sha256"],
                "original seed certificate exact terminal replay",
            )
            for a, b in zip(seed_state["direct"], state["direct"], strict=True):
                before = evidence.array(evidence.read(a)["arrays"])
                after = evidence.array(evidence.read(b)["arrays"])
                require(
                    set(before) == set(after)
                    and all(np.array_equal(before[k], after[k]) for k in before),
                    "bit-identical direct seed-repeat arrays",
                )
        summaries.append(
            dict(
                descriptor,
                certified=certificate["certified"],
                direct=checks,
                mathematical_pass=True,
                exact_repeat=True,
            )
        )
    return dict(
        case=case,
        status="completed",
        arithmetic_and_source_pass=True,
        states=summaries,
        work=ledger.finish(first),
        qualification_pass=required_certification(summaries),
    ), process_end


def audit(run_path, root=ROOT):
    run_path = Path(run_path)
    require(run_path.is_absolute(), "absolute run path required")
    binding = sources(root)
    evidence = Evidence(opaque_json=[binding["primitive_qualification"]])
    ref = dict(path=str(run_path), sha256=sha256_file(run_path))
    run = evidence.read(ref)
    evidence.bind(run)
    evidence.bind(binding, expand_json=False)
    source = source_identity(run, binding)
    require(
        run.get("schema_version") == 1
        and type(run.get("schema_version")) is int
        and run.get("kind") == "coil-perturbation"
        and run.get("status") == "completed"
        and run.get("source_unchanged") is True
        and run.get("producer_complete") is True
        and run.get("admission_status") == "pending-independent-audit",
        "complete pending matrix",
    )
    for key, value in dict(SCOPE, **PENDING).items():
        identity(run.get(key), value, "field-free pending producer flags")
    identity(run.get("limits"), LIMITS, "unaltered registered resource limits")
    identity(run.get("matrix"), matrix(), "complete registered class matrix")
    identity(source.get("matrix"), matrix(), "source matrix")
    require(len(run.get("rows", [])) == 2, "both fresh class workers required")
    identity(
        evidence.read(run["checkpoint"]),
        dict(rows=run["rows"]),
        "final parent checkpoint contains both completed classes",
    )
    surfaces, records = surface_audit(evidence, run, source)
    cells, previous = [], None
    for index, (case, row) in enumerate(zip(matrix(), run["rows"], strict=True)):
        result = evidence.read(row)
        identity(result.get("index"), index, "ordered parent class index")
        cell, previous = cell_audit(
            evidence, result, case, source, run, surfaces, records, previous
        )
        cells.append(cell)
    passed = all(c["qualification_pass"] for c in cells)
    return dict(
        schema_version=1,
        kind="coil-perturbation-audit",
        status="completed",
        run=ref,
        source=source,
        auditor_repository=binding.get("repository"),
        arithmetic_and_source_pass=True,
        independent_audit_pass=True,
        qualification_pass=bool(passed),
        all_pass=bool(passed),
        cells=cells,
        checked_references=len(evidence.references),
        independent_work=dict(
            surface_reconstructions=2,
            certificate_recomputations=52,
            certificate_records_checked=104,
            direct_grids=208,
            sampling_work={
                k: {
                    name: sum(c["work"]["sampling_work"][k][name] for c in cells)
                    for name in zero_sampling()[k]
                }
                for k in zero_sampling()
            },
        ),
        **SCOPE,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        args.run.is_absolute()
        and args.run.is_file()
        and args.output.is_absolute()
        and not args.output.exists()
        and not args.output.is_symlink()
        and not args.output.with_suffix(args.output.suffix + ".tmp").exists(),
        "absolute input and fresh output/temp required",
    )
    require(
        not args.output.with_suffix(args.output.suffix + ".tmp").is_symlink(),
        "fresh temporary output cannot be a broken symlink",
    )
    try:
        result = audit(args.run)
    except Exception as error:
        result = dict(
            schema_version=1,
            kind="coil-perturbation-audit",
            status="error",
            arithmetic_and_source_pass=False,
            independent_audit_pass=False,
            qualification_pass=False,
            all_pass=False,
            error_type=type(error).__name__,
            error=str(error),
            run=dict(path=str(args.run), sha256=sha256_file(args.run)),
            **SCOPE,
        )
    write_json_atomic(args.output, result)
    print(json.dumps(dict(status=result["status"], all_pass=result["all_pass"])))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
