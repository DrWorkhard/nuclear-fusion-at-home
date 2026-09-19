"""Persist the registered geometry-only LP matrix under an owned parent guard."""

import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from clear_coil_initialization_inputs import sources
from current_diagnostic_inputs import checked, reference

from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, guarded_run, space_check

ROOT = Path(__file__).resolve().parents[1]
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
SCOPE = dict(
    field_calls=0,
    gradient_calls=0,
    equilibrium_solves=0,
    field_pass=False,
    transfer_pass=False,
    step4_pass=False,
)
MAX_ATTEMPTS = 168
WALL_SECONDS = 1800.0
LP_SECONDS = 30.0


class LPBudgetExceeded(TimeoutError):
    """An individual LP attempt exceeded its registered wall-time window."""


def successful_process(process):
    return bool(
        isinstance(process, dict)
        and type(process.get("returncode")) is int
        and process["returncode"] == 0
    )


def typed(value):
    if isinstance(value, np.ndarray):
        return typed(value.tolist())
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, dict):
        if any(type(k) is not str for k in value):
            raise TypeError("string JSON keys required")
        return {k: typed(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [typed(v) for v in value]
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float and np.isfinite(value):
        return value
    raise TypeError("finite lossless builtin JSON data required")


def save_json(path, document):
    normalized = typed(document)
    json.dumps(normalized, allow_nan=False)
    write_json_atomic(Path(path), normalized)


def read(path):
    return json.loads(Path(path).read_text())


def save_arrays(path, values):
    arrays = {name: np.asarray(value) for name, value in values.items()}
    if any(
        value.dtype.hasobject or value.dtype.kind not in "biuf" or not np.isfinite(value).all()
        for value in arrays.values()
    ):
        raise ValueError("finite non-object numerical arrays required")
    # Output directory is owned and fresh; no historical file is overwritten.
    with Path(path).open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    return reference(path)


def split_arrays(directory, name, document):
    """Store producer arrays losslessly; all remaining typed metadata separately."""
    array_values = {key: value for key, value in document.items() if isinstance(value, np.ndarray)}
    metadata = {key: value for key, value in document.items() if key not in array_values}
    result = dict(arrays=save_arrays(directory / f"{name}.npz", array_values))
    save_json(directory / f"{name}.json", metadata)
    result["metadata"] = reference(directory / f"{name}.json")
    return result


def surface_levels():
    return [
        dict(
            target=target,
            nphi=n,
            ntheta=n,
            offset=offset,
            label=f"{target}-n{n}-shift{int(2 * offset)}",
        )
        for target in ("reference", "selected")
        for n, offset in ((256, 0), (512, 0), (512, 0.5))
    ]


def attempt_plan(matrix):
    return [
        dict(index=index, case=case["label"], base_index=i, repeat=repeat)
        for index, (case, i, repeat) in enumerate(
            (case, i, repeat)
            for case in matrix
            for i in range(case["nbase"])
            for repeat in (False, True)
        )
    ]


def complete_plan(rows, matrix):
    keys = ("index", "case", "base_index", "repeat")
    return bool(
        [{key: row.get(key) for key in keys} for row in rows] == attempt_plan(matrix)
        and all(
            type(row.get("index")) is int
            and type(row.get("base_index")) is int
            and type(row.get("repeat")) is bool
            for row in rows
        )
    )


def geometry_snapshot(case, coefficients, source):
    coefficients = np.asarray(coefficients, dtype=float)
    nbase, order = case["nbase"], case["order"]
    if coefficients.shape != (nbase, 3, 2 * order + 1) or not np.isfinite(coefficients).all():
        raise ValueError("complete finite named geometric coefficient tensor required")
    names = [
        f"coil[{i}]/{axis}{kind}({m})"
        for i in range(nbase)
        for axis in "xyz"
        for kind, m in [("c", 0)] + [(kind, m) for m in range(1, order + 1) for kind in "sc"]
    ]
    physical = []
    for period in range(2):
        angle = np.pi * period
        c, s = np.cos(angle), np.sin(angle)
        rotation = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
        for flip in (False, True):
            matrix = rotation @ np.diag([1.0, -1.0, -1.0]) if flip else rotation
            for base_index in range(nbase):
                physical.append(
                    dict(base_index=base_index, period=period, flip=flip, matrix=matrix.tolist())
                )
    return dict(
        schema_version=1,
        kind="geometry-only",
        nfp=2,
        nbase=nbase,
        order=order,
        names=names,
        base_coefficients=coefficients.tolist(),
        physical=physical,
        parameter_orientation="alpha=-2*pi*t",
        sources=source["targets"],
        case=case,
    )


def collected_attempts(raw):
    rows = []
    for path in sorted((raw / "attempts").glob("*.json")):
        attempt = read(path)
        outcome_path = raw / "outcomes" / path.name
        row = read(outcome_path) if outcome_path.exists() else dict(attempt)
        row["attempt"] = reference(path)
        if outcome_path.exists():
            row["outcome"] = reference(outcome_path)
        elif all(key in attempt for key in ("case", "base_index", "repeat")):
            solution = (
                raw
                / "sets"
                / attempt["case"]
                / f"coil-{attempt['base_index']:02d}"
                / ("repeat.json" if attempt["repeat"] else "original.json")
            )
            if solution.exists():
                row["retained_uncompleted_solution"] = reference(solution)
            failure = solution.with_name(
                "repeat-failure.json" if attempt["repeat"] else "original-failure.json"
            )
            if failure.exists():
                row["retained_uncompleted_failure"] = reference(failure)
        rows.append(row)
    if [row.get("index") for row in rows] != list(range(len(rows))) or len(rows) > MAX_ATTEMPTS:
        raise ValueError("contiguous bounded LP attempt ledger required")
    return rows


def lp_deadline(started, now=None):
    elapsed = (time.monotonic() if now is None else now) - started
    if not np.isfinite(elapsed) or elapsed < 0:
        raise ValueError("finite forward LP clock required")
    if elapsed >= LP_SECONDS:
        raise LPBudgetExceeded("registered30s individual LP wall budget")
    return float(elapsed)


def live_deadlines(raw, producer_start, now=None):
    """Parent checks the latest persisted in-flight attempt, never another job."""
    now = time.monotonic() if now is None else now
    elapsed = now - producer_start
    if not np.isfinite(elapsed) or elapsed < 0:
        raise ValueError("finite forward producer clock required")
    if elapsed >= WALL_SECONDS:
        raise TimeoutError("registered1800s total producer budget")
    attempts = sorted((raw / "attempts").glob("*.json"))
    if attempts and not (raw / "outcomes" / attempts[-1].name).exists():
        lp_deadline(read(attempts[-1])["started_monotonic"], now)


def worker(config_path):
    from fusion_baselines import clear_coil_geometry as producer

    config_path = Path(config_path)
    config, raw = read(config_path), config_path.parent
    if (
        config.get("parent_pid") != os.getppid()
        or config.get("phase") != "geometry_initialization"
        or config.get("source") != sources(ROOT)
        or any(os.environ.get(key) != "1" for key in THREADS)
    ):
        raise ValueError("live launching parent, committed sources and single threads required")
    if config["source"]["matrix"] != producer.cases():
        raise ValueError("unchanged registered producer case matrix required")
    deadline = config["start_monotonic"] + WALL_SECONDS

    def guard():
        if config["parent_pid"] != os.getppid():
            raise RuntimeError("guarding parent no longer owns this worker")
        if time.monotonic() >= deadline:
            raise TimeoutError("registered1800s total producer budget")
        return space_check(ROOT, 2 * GIB)

    inputs = [
        read(checked(config["source"]["targets"][label]["input"]))
        for label in ("reference", "selected")
    ]
    state = dict(
        schema_version=1,
        phase="geometry_initialization",
        source=config["source"],
        surfaces=[],
        sets=[],
        attempts=[],
        **SCOPE,
    )
    surfaces = {}
    try:
        for level in surface_levels():
            guard()
            folder = raw / "surfaces" / level["label"]
            folder.mkdir()
            started = time.monotonic()
            row = dict(level, status="attempted", started_monotonic=started)
            save_json(folder / "attempt.json", row)
            try:
                values = producer.surface(
                    inputs[("reference", "selected").index(level["target"])],
                    nphi=level["nphi"],
                    ntheta=level["ntheta"],
                    offset=level["offset"],
                )
                refs = split_arrays(folder, "surface", values)
                guard()
                row.update(status="completed", **refs, completed_monotonic=time.monotonic())
                surfaces[level["label"]] = values
            except (TimeoutError, OSError):
                raise
            except Exception as exc:
                row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            save_json(folder / "outcome.json", row)
            state["surfaces"].append(row)
            save_json(raw / "completed-checkpoint.json", state)
        construction_surfaces = [
            surfaces[f"{label}-n256-shift0"] for label in ("reference", "selected")
        ]
        for case in producer.cases():
            guard()
            case_dir = raw / "sets" / case["label"]
            case_dir.mkdir()
            set_row = dict(case=case, status="attempted", coils=[], snapshot=None)
            for base_index in range(case["nbase"]):
                guard()
                folder = case_dir / f"coil-{base_index:02d}"
                folder.mkdir()
                phi = (base_index + 0.5) * np.pi / (2 * case["nbase"])
                center = producer.origin(inputs, phi)
                coil = dict(
                    base_index=base_index,
                    phi=float(phi),
                    center=typed(center),
                    status="attempted",
                    attempts=[],
                    coefficients=None,
                )
                try:
                    disks = producer.envelope(
                        construction_surfaces, phi, case["d"], case["r_floor"], center
                    )
                    coil["disks"] = split_arrays(folder, "disks", disks)
                    model = producer.problem(disks, case["K"], center[0], case["r_floor"])
                    coil["problem"] = split_arrays(folder, "problem", model)
                except (TimeoutError, OSError):
                    raise
                except Exception as exc:
                    coil.update(status="construction_failed", error=f"{type(exc).__name__}: {exc}")
                    # No LP was attempted: keep the unconstructed slot visible.
                    set_row["coils"].append(coil)
                    save_json(folder / "coil.json", coil)
                    continue
                solutions = []
                for repeat in (False, True):
                    guard()
                    index = len(state["attempts"])
                    if index >= MAX_ATTEMPTS:
                        raise RuntimeError("registered168 attempted LP cap")
                    expected = dict(case=case["label"], base_index=base_index, repeat=repeat)
                    attempt = dict(
                        index=index,
                        **expected,
                        status="attempted",
                        problem=coil["problem"],
                        started_monotonic=time.monotonic(),
                    )
                    save_json(raw / "attempts" / f"{index:04d}.json", attempt)
                    state["attempts"].append(attempt)
                    try:
                        # Each solver gets its own exact copy of the stored arrays;
                        # internal solver mutation cannot alter the repeat input.
                        solution = typed(producer.solve(copy.deepcopy(model)))
                        solution_path = folder / ("repeat.json" if repeat else "original.json")
                        save_json(solution_path, solution)
                        guard()
                        completed = time.monotonic()
                        elapsed = lp_deadline(attempt["started_monotonic"], completed)
                        outcome = dict(
                            attempt,
                            status="completed",
                            solution=reference(solution_path),
                            completed_monotonic=completed,
                            elapsed_seconds=elapsed,
                        )
                        solutions.append(solution)
                    except (TimeoutError, OSError):
                        raise
                    except Exception as exc:
                        failure = dict(
                            error=f"{type(exc).__name__}: {exc}", raised_monotonic=time.monotonic()
                        )
                        failure_path = folder / (
                            "repeat-failure.json" if repeat else "original-failure.json"
                        )
                        # Keep the original exception even if the independent
                        # time/resource guard now makes this attempt incomplete.
                        save_json(failure_path, failure)
                        guard()
                        failed_end = time.monotonic()
                        elapsed = lp_deadline(attempt["started_monotonic"], failed_end)
                        outcome = dict(
                            attempt,
                            status="failed",
                            error=failure["error"],
                            failure=reference(failure_path),
                            failed_end_monotonic=failed_end,
                            elapsed_seconds=elapsed,
                        )
                        solutions.append(None)
                    save_json(raw / "outcomes" / f"{index:04d}.json", outcome)
                    state["attempts"][-1] = outcome
                    coil["attempts"].append(
                        dict(index=index, outcome=reference(raw / "outcomes" / f"{index:04d}.json"))
                    )
                    save_json(raw / "completed-checkpoint.json", state)
                original = solutions[0]
                if original is not None and original.get("x") is not None:
                    try:
                        h = np.asarray(original["x"], dtype=float)[: 2 * case["K"] + 1]
                        coil["coefficients"] = typed(
                            producer.export_coefficients(h, center, phi, case["order"])
                        )
                        coil["status"] = "exported"
                    except Exception as exc:
                        coil.update(status="export_failed", error=f"{type(exc).__name__}: {exc}")
                else:
                    coil["status"] = "no_primal_solution"
                save_json(folder / "coil.json", coil)
                set_row["coils"].append(coil)
            if all(c["coefficients"] is not None for c in set_row["coils"]):
                snapshot = geometry_snapshot(
                    case, [c["coefficients"] for c in set_row["coils"]], config["source"]
                )
                save_json(case_dir / "snapshot.json", snapshot)
                set_row["snapshot"] = reference(case_dir / "snapshot.json")
                set_row["status"] = "exported"
            else:
                set_row["status"] = "incomplete_geometry"
            save_json(case_dir / "set.json", set_row)
            state["sets"].append(set_row)
            save_json(raw / "completed-checkpoint.json", state)
            print(
                json.dumps(
                    dict(
                        case=case["label"],
                        status=set_row["status"],
                        attempted_lps=len(state["attempts"]),
                    )
                ),
                flush=True,
            )
        terminal = dict(
            reason="matrix_complete",
            all_registered_attempts=complete_plan(state["attempts"], producer.cases()),
        )
    except Exception as exc:
        terminal = dict(
            reason="lp_wall_budget"
            if isinstance(exc, LPBudgetExceeded)
            else "wall_budget"
            if isinstance(exc, TimeoutError)
            else "worker_failure",
            error=f"{type(exc).__name__}: {exc}",
        )
    save_json(raw / "worker-terminal.json", terminal)


def run(raw):
    raw = Path(raw)
    if not raw.is_absolute() or raw.exists():
        raise ValueError("absolute fresh raw output directory required")
    if any(os.environ.get(key) != "1" for key in THREADS):
        raise ValueError("registered single-thread environment required")
    source = sources(ROOT)
    reserve = space_check(ROOT, 3 * GIB)
    raw.mkdir(parents=True)
    for name in ("surfaces", "sets", "attempts", "outcomes"):
        (raw / name).mkdir()
    config = dict(
        schema_version=1,
        phase="geometry_initialization",
        source=source,
        threads={name: os.environ[name] for name in THREADS},
        parent_pid=os.getpid(),
        start_monotonic=time.monotonic(),
        **SCOPE,
    )
    save_json(raw / "config.json", config)

    def guard(path, required):
        record = space_check(path, required)
        live_deadlines(raw, config["start_monotonic"])
        return record

    try:
        with (raw / "worker.log").open("xb") as log:
            process = guarded_run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    str(raw / "config.json"),
                ],
                cwd=ROOT,
                env=os.environ.copy(),
                stdout=log,
                space_root=ROOT,
                reserve_bytes=2 * GIB,
                check=guard,
                interval=0.5,
            )
        terminal = (
            read(raw / "worker-terminal.json")
            if (raw / "worker-terminal.json").exists()
            else dict(reason="worker_failure")
        )
        terminal["process"] = process
        if not successful_process(process):
            terminal["worker_reason"] = terminal["reason"]
            terminal["reason"] = "worker_exit_failure"
            terminal["error"] = "worker returncode must be an exact integer zero"
    except Exception as exc:
        terminal = dict(
            reason="parent_lp_timeout"
            if isinstance(exc, LPBudgetExceeded)
            else "parent_timeout"
            if isinstance(exc, TimeoutError)
            else "parent_failure",
            error=f"{type(exc).__name__}: {exc}",
        )
    terminal["parent_stop_monotonic"] = time.monotonic()
    save_json(raw / "terminal.json", terminal)
    checkpoint = raw / "completed-checkpoint.json"
    state = read(checkpoint) if checkpoint.exists() else dict(surfaces=[], sets=[])
    rows = collected_attempts(raw)
    complete = complete_plan(rows, source["matrix"])
    result = dict(
        state,
        schema_version=1,
        phase="geometry_initialization",
        source=source,
        threads=config["threads"],
        attempts=rows,
        attempted_lps=len(rows),
        case_matrix=source["matrix"],
        terminal=terminal,
        resource_before=reserve,
        status="completed"
        if (
            terminal["reason"] == "matrix_complete"
            and terminal.get("all_registered_attempts") is True
            and complete
            and successful_process(terminal.get("process"))
        )
        else "incomplete",
        geometry_pass=False,
        selected=None,
        **SCOPE,
    )
    result["clock"] = dict(
        start_monotonic=config["start_monotonic"],
        parent_stop_monotonic=terminal["parent_stop_monotonic"],
        timeout_seconds=WALL_SECONDS,
        lp_timeout_seconds=LP_SECONDS,
        check_interval=0.5,
        termination_grace_seconds=5,
    )
    result["execution_artifacts"] = {
        name: reference(raw / name)
        for name in (
            "config.json",
            "worker.log",
            "worker-terminal.json",
            "terminal.json",
            "completed-checkpoint.json",
        )
        if (raw / name).exists()
    }
    result["repository"] = git_state(ROOT)
    save_json(raw / "run.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--raw", type=Path)
    group.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker.resolve())
        return 0
    report = run(args.raw)
    print(
        json.dumps({key: report[key] for key in ("status", "attempted_lps", "terminal")}),
        flush=True,
    )
    return 0 if report["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
