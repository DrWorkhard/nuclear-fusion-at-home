"""Bounded field-free cumulative coil-perturbation producer; admission is separate."""

import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import qualify_sparse_coil_surface as storage

from fusion_baselines.coil_perturbation import candidate_certificate
from fusion_baselines.coil_perturbation_samples import (
    TARGETS,
    Sampler,
    candidate,
    directions,
    empty_work,
    grid_budget,
    levels,
    state_plan,
    surface_points,
)
from fusion_baselines.resource_guard import GIB, guarded_run, space_check

ROOT = Path(__file__).resolve().parents[1]
THREADS = storage.THREADS
WALL_SECONDS = 1800.0
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
    all_pass=False,
    qualification_pass=False,
    independent_audit_pass=False,
)
save, ref, checked, read = storage.save, storage.ref, storage.checked, storage.read


def sources(root):
    from coil_perturbation_workflow_inputs import sources as bound_sources

    return bound_sources(root)


def checked_source(reference):
    from coil_perturbation_inputs import checked as bound_checked

    return bound_checked(reference)


def matrix():
    return [
        dict(label=f"n{n}-shape-d100mm", nbase=n, order=m, geometry_report_index=i)
        for n, m, i in ((6, 5, 3), (8, 7, 9))
    ]


def work_zero():
    return {
        key: dict(attempted=0, completed=0)
        for key in ("states", "certificates", "direct_grids", "surfaces")
    }


class ParentLost(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


def deadline(started, now=None):
    elapsed = (time.monotonic() if now is None else now) - started
    if type(started) not in (int, float) or not np.isfinite(elapsed) or elapsed < 0:
        raise ValueError("finite forward worker clock required")
    if elapsed >= WALL_SECONDS:
        raise TimeoutError("registered 1800 s geometry-class budget exceeded")
    return float(elapsed)


class Guard:
    def __init__(self, output, parent_pid, started):
        self.output, self.parent_pid, self.started = output, parent_pid, started
        self.minimum_free_bytes = None

    def __call__(self):
        if type(self.parent_pid) is not int or os.getppid() != self.parent_pid:
            raise ParentLost("owned parent changed; no additional geometric work allowed")
        deadline(self.started)
        free = space_check(self.output, 2 * GIB)["free_bytes"]
        self.minimum_free_bytes = (
            free if self.minimum_free_bytes is None else min(self.minimum_free_bytes, free)
        )


class Ledger:
    """Persist reservations before dispatch, completed prefixes after raw output."""

    def __init__(self, output, guard, build_surfaces):
        self.output, self.guard = output, guard
        self.work = work_zero()
        self.caps = dict(
            states=26, certificates=52, direct_grids=104, surfaces=2 if build_surfaces else 0
        )
        self.operations, self.attempts, self.state_attempts = [], [], []
        self.sampling_work = empty_work()
        (output / "operations").mkdir()

    def reserve(self, kind, descriptor, path):
        self.guard()
        if kind not in self.caps or self.work[kind]["attempted"] >= self.caps[kind]:
            raise BudgetExceeded("registered work cap reached before dispatch")
        attempt = dict(
            descriptor,
            status="attempted",
            kind=kind,
            started_monotonic=time.monotonic(),
            work_before=copy.deepcopy(self.work),
            reservation={key: int(key == kind) for key in self.caps},
        )
        save(path, attempt)
        reference = ref(path)
        save(self.output / "inflight.json", dict(attempt=reference))
        self.work[kind]["attempted"] += 1
        return attempt, reference

    def perform(self, kind, descriptor, callback, sampling=None):
        index = len(self.attempts)
        path = self.output / "operations" / f"operation-{index:03d}"
        descriptor = dict(descriptor, operation_index=index)
        if sampling is not None:
            descriptor.update(
                sampling_work_before=sampling.work(),
                sampling_reservation=grid_budget(
                    descriptor["nphysical"], descriptor["level"]["ncoil"]
                ),
            )
        attempt, attempt_ref = self.reserve(kind, descriptor, path.with_suffix(".attempt.json"))
        self.attempts.append(attempt_ref)
        record = dict(attempt, attempt=attempt_ref)
        error = None
        try:
            record.update(callback(path))
            self.guard()
            self.work[kind]["completed"] += 1
            record["status"] = "completed"
        except Exception as caught:
            error = caught
            record.update(status="error", error_type=type(caught).__name__, error=str(caught))
        if sampling is not None:
            self.sampling_work = sampling.work()
            record["sampling_work_after"] = sampling.work()
        record.update(ended_monotonic=time.monotonic(), work_after=copy.deepcopy(self.work))
        save(path.with_suffix(".json"), record)
        result = ref(path.with_suffix(".json"))
        self.operations.append(result)
        if isinstance(error, (OSError, TimeoutError, ParentLost, BudgetExceeded)):
            raise error
        return record, result

    def references(self):
        result = dict(
            operations=self.operations,
            operation_attempts=self.attempts,
            state_attempts=self.state_attempts,
            work=copy.deepcopy(self.work),
            sampling_work=copy.deepcopy(self.sampling_work),
        )
        if (self.output / "inflight.json").exists():
            result["inflight"] = ref(self.output / "inflight.json")
        return copy.deepcopy(result)


def load_arrays(reference):
    with np.load(checked(reference), allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def build_surface_registry(source, output, ledger):
    """Called only by first class, under that worker's unchanged time budget."""
    output.mkdir(exist_ok=False)
    fixed = {}
    for target in TARGETS:
        source_input = source["targets"][target]

        def build(path, target=target, source_input=source_input):
            points = surface_points(read(checked_source(source_input)))
            if points.shape != (256**2, 3):
                raise ValueError("complete fixed256 full-torus surface required")
            reference = storage.arrays(output / f"{target}.npz", dict(points=points))
            return dict(arrays=reference)

        document, operation_ref = ledger.perform(
            "surfaces",
            dict(
                target=target,
                nphi=256,
                ntheta=256,
                offset=0,
                full_torus=True,
                source_input=source_input,
            ),
            build,
        )
        if document["status"] != "completed":
            raise ValueError("both fixed surfaces must complete before any state")
        save(output / f"{target}.json", dict(document, operation=operation_ref))
        fixed[target] = ref(output / f"{target}.json")
    save(output / "registry.json", dict(schema_version=1, status="completed", fixed_surfaces=fixed))
    return ref(output / "registry.json")


def surface_registry(reference, source):
    registry = read(checked(reference))
    if (
        registry.get("schema_version") != 1
        or registry.get("status") != "completed"
        or set(registry.get("fixed_surfaces", {})) != set(TARGETS)
    ):
        raise ValueError("complete shared surface registry required; no silent rebuild")
    targets = {}
    for target, item in registry["fixed_surfaces"].items():
        row = read(checked(item))
        required = dict(
            target=target,
            nphi=256,
            ntheta=256,
            offset=0,
            full_torus=True,
            source_input=source["targets"][target],
            status="completed",
        )
        if any(
            type(row.get(key)) is not type(value) or row[key] != value
            for key, value in required.items()
        ):
            raise ValueError("exact shared surface source and full grid required")
        raw = load_arrays(row["arrays"])
        if (
            set(raw) != {"points"}
            or raw["points"].shape != (256**2, 3)
            or raw["points"].dtype.kind not in "iuf"
            or not np.isfinite(raw["points"]).all()
        ):
            raise ValueError("complete finite shared surface point arrays required")
        targets[target] = raw["points"]
    return registry["fixed_surfaces"], targets


def execute_state(output, state, seed, seed_ref, report, vectors, sampler, ledger):
    directory = output / state["state_id"]
    directory.mkdir()
    attempt, attempt_ref = ledger.reserve("states", state, directory / "attempt.json")
    ledger.state_attempts.append(attempt_ref)
    record = dict(
        state,
        attempt=attempt_ref,
        seed_snapshot=seed_ref,
        started_monotonic=attempt["started_monotonic"],
        work_before=attempt["work_before"],
        certificates=[],
        certificate_operations=[],
        direct=[],
        status="error",
        repeat_exact=False,
    )
    try:
        coefficients = candidate(seed, vectors, state)
        record["candidate"] = storage.arrays(
            directory / "candidate.npz", dict(coefficients=coefficients)
        )
        for repeat in range(2):

            def certify(path, repeat=repeat):
                certificate = candidate_certificate(seed, report, coefficients)
                destination = directory / f"certificate-{repeat}.json"
                save(destination, certificate)
                return dict(certificate=ref(destination))

            result, operation = ledger.perform(
                "certificates",
                dict(
                    state_id=state["state_id"],
                    state_index=state["index"],
                    repeat=repeat,
                    candidate=record["candidate"],
                ),
                certify,
            )
            record["certificate_operations"].append(operation)
            if result["status"] == "completed":
                record["certificates"].append(result["certificate"])
        for index, level in enumerate(levels()):

            def sample(path, level=level):
                raw = sampler.sample(coefficients, level)
                return dict(arrays=storage.arrays(path.with_suffix(".npz"), raw))

            _, operation = ledger.perform(
                "direct_grids",
                dict(
                    state_id=state["state_id"],
                    state_index=state["index"],
                    level_index=index,
                    level=level,
                    candidate=record["candidate"],
                    nphysical=4 * seed["nbase"],
                ),
                sample,
                sampling=sampler,
            )
            record["direct"].append(operation)
        record["repeat_exact"] = (
            len(record["certificates"]) == 2
            and record["certificates"][0]["sha256"] == record["certificates"][1]["sha256"]
        )
        complete = record["repeat_exact"] and all(
            read(checked(item))["status"] == "completed" for item in record["direct"]
        )
        if complete:
            ledger.work["states"]["completed"] += 1
            record["status"] = "completed"
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
        if isinstance(error, (OSError, TimeoutError, ParentLost, BudgetExceeded)):
            raise
    record.update(ended_monotonic=time.monotonic(), work_after=copy.deepcopy(ledger.work))
    save(directory / "state.json", record)
    return ref(directory / "state.json")


def worker(config_path):
    config_path = Path(config_path)
    config = read(config_path)
    source, case, output = config["source"], config["case"], Path(config["output"])
    first = case == matrix()[0]
    if (
        case not in matrix()
        or source["matrix"] != matrix()
        or not output.is_absolute()
        or config_path.resolve() != output / "config.json"
        or config.get("build_surfaces") is not first
        or Path(config["surface_directory"]) != output.parent / "surfaces"
        or (first and config.get("surface_registry") is not None)
        or (not first and not isinstance(config.get("surface_registry"), dict))
        or any(os.environ.get(key) != "1" for key in THREADS)
    ):
        raise ValueError("exact registered single-thread geometry worker required")
    guard = Guard(output, config["parent_pid"], config["started_monotonic"])
    ledger, rows, fixed, registry = None, [], {}, config.get("surface_registry")
    try:
        guard()
        if sources(ROOT) != source:
            raise ValueError("worker sources changed before geometric work")
        seed_ref = source["seeds"][case["label"]]["snapshot"]
        seed = read(checked_source(seed_ref))
        report = read(checked_source(source["geometry"]["audit"]))["sets"][
            case["geometry_report_index"]
        ]
        vectors = directions(seed)
        save(output / "plan.json", dict(states=state_plan(), levels=levels(), case=case))
        vector_ref = storage.arrays(output / "directions.npz", dict(directions=vectors))
        ledger = Ledger(output, guard, first)
        if first:
            registry = build_surface_registry(source, Path(config["surface_directory"]), ledger)
        fixed, targets = surface_registry(registry, source)
        sampler = Sampler(seed, targets, check=guard)
        for state in state_plan():
            guard()
            row = execute_state(output, state, seed, seed_ref, report, vectors, sampler, ledger)
            rows.append(row)
            guard()
            if read(checked(row))["status"] == "completed":
                # The live marker changes at the next reservation. A successful
                # checkpoint must instead bind its own immutable prefix marker.
                marker = output / state["state_id"] / "checkpoint-inflight.json"
                guard()
                save(marker, dict(attempt=ledger.attempts[-1]))
                checkpoint = dict(states=rows, **ledger.references())
                checkpoint["inflight"] = ref(marker)
                guard()
                save(output / "checkpoint.json", checkpoint)
        after = sources(ROOT)
        expected = {key: dict(attempted=n, completed=n) for key, n in ledger.caps.items()}
        complete = source == after and ledger.work == expected
        ended = time.monotonic()
        elapsed = deadline(config["started_monotonic"], ended)
        record = dict(
            schema_version=1,
            kind="coil-perturbation-cell",
            status="completed" if complete else "error",
            case=case,
            source_before=source,
            source_after=after,
            seed_snapshot=seed_ref,
            directions=vector_ref,
            states=rows,
            fixed_surfaces=fixed,
            surface_registry=registry,
            **ledger.references(),
            threads={key: os.environ[key] for key in THREADS},
            started_monotonic=config["started_monotonic"],
            elapsed_seconds=elapsed,
            ended_monotonic=ended,
            minimum_observed_free_bytes=guard.minimum_free_bytes,
            scope=SCOPE,
        )
        save(output / "worker.json", record)
        return 0 if complete else 1
    except Exception as error:
        ended = time.monotonic()
        record = dict(
            status="error",
            error_type=type(error).__name__,
            error=str(error),
            case=case,
            source_before=source,
            states=rows,
            fixed_surfaces=fixed,
            surface_registry=registry,
            scope=SCOPE,
            started_monotonic=config["started_monotonic"],
            elapsed_seconds=ended - config["started_monotonic"],
            ended_monotonic=ended,
        )
        if ledger is not None:
            record.update(ledger.references())
        save(output / "worker-error.json", record)
        return 1


def run_process(command, output, env, started):
    def check(path, reserve):
        deadline(started)
        return space_check(path, reserve)

    try:
        with (output / "stdout.txt").open("x") as stdout:
            process = guarded_run(
                command,
                cwd=ROOT,
                env=env,
                stdout=stdout,
                space_root=output,
                reserve_bytes=2 * GIB,
                check=check,
                interval=0.5,
            )
        return dict(process, timed_out=False, elapsed_seconds=time.monotonic() - started)
    except Exception as error:
        return dict(
            returncode=None,
            timed_out=isinstance(error, TimeoutError),
            error_type=type(error).__name__,
            error=str(error),
            elapsed_seconds=time.monotonic() - started,
        )


def process_complete(process, document, case, source, started):
    values = (
        started,
        process.get("elapsed_seconds"),
        document.get("elapsed_seconds"),
        document.get("ended_monotonic"),
    )
    if any(type(v) not in (int, float) or not np.isfinite(v) or v < 0 for v in values):
        raise ValueError("finite forward process clocks required")
    if (
        type(process.get("returncode")) is not int
        or process["returncode"] != 0
        or process.get("timed_out") is not False
        or process.get("error_type")
        or process["elapsed_seconds"] >= WALL_SECONDS
        or document["elapsed_seconds"] >= WALL_SECONDS
        or not 0 <= document["ended_monotonic"] - started < WALL_SECONDS
        or document["elapsed_seconds"] != document["ended_monotonic"] - started
        or document["elapsed_seconds"] > process["elapsed_seconds"]
        or document.get("started_monotonic") != started
        or document.get("status") != "completed"
        or document.get("case") != case
        or document.get("source_before") != source
        or document.get("source_after") != source
        or document.get("threads") != {key: "1" for key in THREADS}
        or document.get("scope") != SCOPE
    ):
        raise ValueError("timely complete source-bound geometry worker required")


def _run(output):
    before = sources(ROOT)
    if before["matrix"] != matrix():
        raise ValueError("exact registered two-class matrix required")
    save(output / "source-before.json", before)
    env = dict(os.environ, **{key: "1" for key in THREADS})
    env["PYTHONPATH"] = str(ROOT / "src")
    rows, registry, fixed = [], None, {}
    for index, case in enumerate(matrix()):
        directory = output / case["label"]
        directory.mkdir()
        if index == 1 and registry is None:
            row = dict(
                index=index,
                case=case,
                status="not-executed",
                error="first worker did not persist both shared surfaces",
                retained=[],
            )
        else:
            start_space = space_check(output, 3 * GIB)
            started = time.monotonic()
            config = dict(
                case=case,
                output=str(directory),
                source=before,
                parent_pid=os.getpid(),
                started_monotonic=started,
                build_surfaces=index == 0,
                surface_directory=str(output / "surfaces"),
                surface_registry=registry,
                start_space=start_space,
            )
            save(directory / "config.json", config)
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                str(directory / "config.json"),
            ]
            save(
                directory / "launch.json",
                dict(command=command, started_monotonic=started, case=case),
            )
            process = run_process(command, directory, env, started)
            save(directory / "process.json", process)
            row = dict(
                index=index,
                case=case,
                status="error",
                config=ref(directory / "config.json"),
                launch=ref(directory / "launch.json"),
                process=ref(directory / "process.json"),
            )
            try:
                document = read(directory / "worker.json")
                process_complete(process, document, case, before, started)
                row.update(status="completed", worker=ref(directory / "worker.json"))
            except Exception as error:
                row.update(error_type=type(error).__name__, error=str(error))
            if index == 0 and (output / "surfaces" / "registry.json").is_file():
                registry = ref(output / "surfaces" / "registry.json")
                try:
                    fixed, _ = surface_registry(registry, before)
                except Exception as error:
                    row["surface_registry_error"] = str(error)
                    registry = None
            row["retained"] = [ref(path) for path in sorted(directory.rglob("*")) if path.is_file()]
        save(directory / "result.json", row)
        rows.append(ref(directory / "result.json"))
        if row["status"] == "completed":
            save(output / "checkpoint.json", dict(rows=rows))
    after = sources(ROOT)
    save(output / "source-after.json", after)
    complete = before == after and all(
        read(checked(item))["status"] == "completed" for item in rows
    )
    result = dict(
        schema_version=1,
        kind="coil-perturbation",
        status="completed",
        source_before=before,
        source_after=after,
        source_unchanged=before == after,
        matrix=matrix(),
        rows=rows,
        surface_registry=registry,
        fixed_surfaces=fixed,
        retained_surfaces=[
            ref(path) for path in sorted((output / "surfaces").rglob("*")) if path.is_file()
        ],
        producer_complete=bool(complete),
        admission_status="pending-independent-audit",
        **SCOPE,
        limits=dict(
            wall_seconds=WALL_SECONDS,
            parent_poll_seconds=0.5,
            termination_grace_seconds=5,
            start_reserve_bytes=3 * GIB,
            live_reserve_bytes=2 * GIB,
        ),
    )
    if (output / "checkpoint.json").exists():
        result["checkpoint"] = ref(output / "checkpoint.json")
    save(output / "run.json", result)
    return result


def run(output):
    output = Path(output)
    if not output.is_absolute():
        raise ValueError("absolute fresh output required")
    output.mkdir(parents=True, exist_ok=False)
    try:
        return _run(output)
    except Exception as error:
        save(
            output / "terminal-error.json",
            dict(status="error", error_type=type(error).__name__, error=str(error), scope=SCOPE),
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--raw", type=Path)
    group.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker is not None:
        return worker(args.worker)
    result = run(args.raw)
    print(
        json.dumps(
            dict(
                status=result["status"],
                producer_complete=result["producer_complete"],
                run=ref(args.raw / "run.json"),
            ),
            allow_nan=False,
        )
    )
    return 0 if result["producer_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
