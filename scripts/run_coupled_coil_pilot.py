"""Run one preregistered coil cell with persistent attempts and parent time cap."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from coupled_coil_inputs import sources
from current_diagnostic_inputs import checked, reference

from fusion_baselines.coupled_coil_workflow import cases, choose_search, qualification_points
from fusion_baselines.provenance import write_json_atomic
from fusion_baselines.resource_guard import GIB, guarded_run, space_check

ROOT = Path(__file__).resolve().parents[1]
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")


class BudgetExhausted(RuntimeError):
    pass


def read(path):
    return json.loads(Path(path).read_text())


def make_model(source, case):
    from fusion_baselines.coupled_coils import CoupledCoils

    target = source["targets"][case["target"]]
    return CoupledCoils(checked(target["wout"]), checked(target["input"]),
                        case["nbase"], case["order"], case["method"])


def save_bundle(model, x, directory, index, deadline=None):
    """Exactly one requested full bundle; serialization does not call evaluate."""
    directory.mkdir(exist_ok=False)
    start = time.monotonic()
    value, gradient, metrics = model.evaluate(x)
    arrays = model.arrays(x)
    snapshot = model.snapshot(x)
    scale = metrics["scale"]
    # Explicit supplementary value work, not hidden gradient bundles.
    arrays["boundary_A"] = scale * model.field.A().copy()
    arrays["inner_A"] = scale * model.inner_field.A().copy()
    arrays["loop_B"] = scale * model.loop_field.B().copy()
    np.savez_compressed(directory / "arrays.npz", **arrays)
    write_json_atomic(directory / "snapshot.json", snapshot)
    result = dict(index=index, status="completed", x=np.asarray(x).tolist(),
                  J=float(value), gradient=np.asarray(gradient).tolist(), metrics=metrics,
                  snapshot=reference(directory / "snapshot.json"),
                  arrays=reference(directory / "arrays.npz"),
                  started_monotonic=start,
                  supplementary_field_work=dict(boundary_A_calls=1, inner_A_calls=1,
                                                loop_B_calls=1))
    completed = time.monotonic()
    if deadline is not None and completed >= deadline:
        raise TimeoutError("late full bundle retained as unselected incomplete attempt")
    result.update(completed_monotonic=completed, elapsed_seconds=completed - start)
    write_json_atomic(directory / "row.json", result)
    return result


def collected_rows(directory):
    """Retain every attempted point, including an interrupted final evaluation."""
    result = []
    for attempt_path in sorted((directory / "attempts").glob("*.json")):
        attempt = read(attempt_path)
        completed = directory / "bundles" / f"{attempt['index']:04d}" / "row.json"
        failure = completed.with_name("failure.json")
        row = (read(completed) if completed.exists()
               else read(failure) if failure.exists() else attempt)
        row["attempt"] = reference(attempt_path)
        result.append(row)
    if [r["index"] for r in result] != list(range(len(result))):
        raise ValueError("attempt ledger must have contiguous indices")
    return result


def worker(config_path):
    """Owned subprocess; parent alone enforces the wall clock across native calls."""
    from scipy.optimize import minimize

    config = read(config_path)
    directory = Path(config_path).parent
    if (config.get("phase") not in ("qualification", "search")
            or config.get("parent_pid") != os.getppid()
            or any(os.environ.get(key) != "1" for key in THREADS)
            or config.get("source") != sources(ROOT)):
        raise ValueError("worker requires registered source, threads and its live launching parent")
    model = make_model(config["source"], config["case"])
    write_json_atomic(directory / "initialization.json", dict(
        seed_x=model.seed_x.tolist(), names=model.names,
        initialization_work=model.initialization_work))
    rows = []
    phase = config["phase"]
    deadline = None

    def objective(x):
        nonlocal deadline
        if phase == "search" and len(rows) >= 128:
            raise BudgetExhausted("registered128 attempted full-bundle cap")
        if config["parent_pid"] != os.getppid():
            raise RuntimeError("guarding parent no longer owns this worker")
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError("registered600s budget before next attempted bundle")
        if not rows and phase == "search":
            begun = time.monotonic()
            deadline = begun + 600
            write_json_atomic(directory / "search-start.json", dict(monotonic=begun))
        index = len(rows)
        attempt = dict(index=index, status="attempted", x=np.asarray(x).tolist(),
                       started_monotonic=time.monotonic())
        write_json_atomic(directory / "attempts" / f"{index:04d}.json", attempt)
        rows.append(attempt)
        try:
            row = save_bundle(model, x, directory / "bundles" / f"{index:04d}", index,
                              deadline=deadline)
        except Exception as exc:
            failure = dict(attempt, status="failed", error=f"{type(exc).__name__}: {exc}")
            write_json_atomic(directory / "bundles" / f"{index:04d}" / "failure.json", failure)
            # Last completed checkpoint remains unchanged on failure/termination.
            raise
        rows[-1] = row
        write_json_atomic(directory / "completed-checkpoint.json", dict(rows=rows))
        print(json.dumps(dict(phase=phase, case=config["case"]["label"], index=index,
                              J=row["J"], normal_rms=row["metrics"]["normal_rms"],
                              vector_rms=row["metrics"]["vector_rms"])), flush=True)
        return row["J"], np.asarray(row["gradient"])

    try:
        if phase == "qualification":
            for x in qualification_points(model.seed_x):
                objective(x)
            terminal = dict(reason="qualification_complete")
        else:
            result = minimize(objective, model.seed_x.copy(), jac=True, method="L-BFGS-B",
                              bounds=list(zip(model.seed_x - 0.12, model.seed_x + 0.12,
                                              strict=True)),
                              options=dict(maxiter=128, maxls=20, ftol=1e-12, gtol=1e-9))
            terminal = dict(reason="solver_return", solver_success=bool(result.success),
                            solver_status=int(result.status), message=str(result.message),
                            nit=int(result.nit), nfev=int(result.nfev), njev=int(result.njev))
    except BudgetExhausted as exc:
        terminal = dict(reason="evaluation_budget", message=str(exc))
    except TimeoutError as exc:
        terminal = dict(reason="wall_budget", message=str(exc))
    except Exception as exc:
        terminal = dict(reason="evaluation_failure", error=f"{type(exc).__name__}: {exc}")
    write_json_atomic(directory / "worker-terminal.json", terminal)


def run_cell(phase, case, directory, qualification=None, qualification_audit=None):
    if any(os.environ.get(key) != "1" for key in THREADS):
        raise ValueError("registered single-thread environment required")
    source = sources(ROOT)
    before = space_check(ROOT, 3 * GIB)
    if directory.exists():
        raise FileExistsError("fresh output directory required; old evidence is immutable")
    config = dict(schema_version=1, phase=phase, source=source, case=case,
                  threads={key: os.environ[key] for key in THREADS}, equilibrium_solves=0,
                  parent_pid=os.getpid())
    if phase == "search":
        if qualification is None or qualification_audit is None:
            raise ValueError("qualified source-bound start and independent audit required")
        q, qa = read(qualification), read(qualification_audit)
        if (q["phase"] != "qualification" or q["source"] != source or q["case"] != case
                or qa.get("status") != "completed"
                or qa.get("qualification_pass") is not True
                or qa.get("arithmetic_and_source_pass") is not True
                or qa.get("phase") != "qualification" or qa.get("source") != source
                or qa.get("case") != case
                or qa.get("run") != reference(qualification)):
            raise ValueError("independent qualification does not bind this exact cell")
        config.update(qualification=reference(qualification),
                      qualification_audit=reference(qualification_audit))
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "attempts").mkdir()
    (directory / "bundles").mkdir()
    write_json_atomic(directory / "config.json", config)

    def check(path, reserve):
        record = space_check(path, reserve)
        marker = directory / "search-start.json"
        if phase == "search" and marker.exists():
            if time.monotonic() - read(marker)["monotonic"] > 600:
                raise TimeoutError("registered600s search wall budget")
        return record

    start = time.monotonic()
    try:
        with (directory / "worker.log").open("xb") as logfile:
            process = guarded_run([sys.executable, str(Path(__file__).resolve()),
                                   "--worker", str(directory / "config.json")],
                                  cwd=ROOT, env=os.environ.copy(), stdout=logfile,
                                  space_root=ROOT, reserve_bytes=2 * GIB,
                                  check=check, interval=0.5)
        terminal_path = directory / "worker-terminal.json"
        terminal = read(terminal_path) if terminal_path.exists() else dict(reason="worker_failure")
        terminal["process"] = process
    except Exception as exc:
        terminal = dict(reason="parent_timeout" if isinstance(exc, TimeoutError)
                        else "parent_failure", error=f"{type(exc).__name__}: {exc}")
    terminal["parent_elapsed_seconds"] = time.monotonic() - start
    terminal["parent_stop_monotonic"] = time.monotonic()
    write_json_atomic(directory / "terminal.json", terminal)
    initialization = directory / "initialization.json"
    run = dict(config, status="completed" if initialization.exists() else "failed",
               rows=collected_rows(directory), terminal=terminal,
               resource_before=before, transfer_pass=False, step4_pass=False)
    run["execution_artifacts"] = {
        name: reference(directory / name) for name in (
            "config.json", "worker.log", "terminal.json", "initialization.json",
            "completed-checkpoint.json", "worker-terminal.json")
        if (directory / name).exists()
    }
    if initialization.exists():
        run.update(read(initialization))
    else:
        write_json_atomic(directory / "run.json", run)
        return run
    run["attempted_bundles"] = len(run["rows"])
    marker = directory / "search-start.json"
    if phase == "search" and marker.exists():
        run["search_clock"] = dict(
            start_monotonic=read(marker)["monotonic"],
            parent_stop_monotonic=terminal["parent_stop_monotonic"],
            check_interval=0.5, timeout_seconds=600, termination_grace_seconds=5,
            marker=reference(marker))
    run["status"] = "running"
    write_json_atomic(directory / "run.json", run)
    if phase == "qualification" and len(run["rows"]) == 10 and all(
        r["status"] == "completed" for r in run["rows"]
    ):
        from validate_coupled_coil_pilot import flux_diagnostics

        first = run["rows"][0]
        try:
            model = make_model(source, case)
            model.x = np.asarray(first["x"])
            run["flux_initialization_work"] = model.initialization_work
            run["flux"] = flux_diagnostics(model, first["x"], read(checked(first["snapshot"])),
                                           directory / "flux", ncoil=128)
        except Exception as exc:
            run["flux"] = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    if phase == "search":
        selected = choose_search(run["rows"])
        run["selected"] = selected
        if selected is not None:
            try:
                model = make_model(source, case)
                run["replay_initialization_work"] = model.initialization_work
                run["replay"] = save_bundle(model, run["rows"][selected]["x"],
                                            directory / "replay", selected)
            except Exception as exc:
                run["replay"] = dict(status="failed", error=f"{type(exc).__name__}: {exc}")
    run["status"] = "completed"
    write_json_atomic(directory / "run.json", run)
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("qualification", "search"))
    parser.add_argument("--case", choices=[row["label"] for row in cases()])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--qualification-audit", type=Path)
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker.resolve())
        return
    if args.phase is None or args.case is None or args.output is None:
        parser.error("phase, case and fresh output are required")
    case = next(row for row in cases() if row["label"] == args.case)
    result = run_cell(args.phase, case, args.output.resolve(), args.qualification,
                      args.qualification_audit)
    print(json.dumps(dict(status=result["status"], phase=result["phase"], case=case,
                          attempted_bundles=result.get("attempted_bundles", 0),
                          terminal=result["terminal"])), flush=True)


if __name__ == "__main__":
    main()
