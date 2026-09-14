"""Registered two-round four-mode plasma search and frozen endpoint cold starts."""

import argparse
import importlib.metadata
import json
import os
import time
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import reference
from plasma_inputs import root_path, sources
from plasma_measurement import geometry_guard, measure, metadata

from fusion_baselines.plasma_design import MODES, choose, design_input, poll_points
from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, guarded_run, space_check


def solve(root, folder, original, binding, x, ns):
    folder.mkdir(parents=True, exist_ok=False)
    effective = design_input(original, x, ns)
    write_json_atomic(folder / "input.json", effective)
    request = dict(
        original=binding["original"],
        input=reference(folder / "input.json"),
        x=list(map(float, x)),
        ns=ns,
        modes=[list(v) for v in MODES],
    )
    write_json_atomic(folder / "request.json", request)
    command = [
        str(root / "environments/vmecpp/.venv/bin/python"),
        "scripts/plasma_equilibrium_worker.py",
        str(folder),
    ]
    started = time.monotonic()
    record = dict(
        status="running",
        eligible=False,
        x=request["x"],
        ns=ns,
        command=command,
        directory=str(folder),
        input=request["input"],
        request=reference(folder / "request.json"),
    )

    def check(path, reserve):
        if time.monotonic() - started > 1800:
            raise TimeoutError("registered1800s cold-start cap reached")
        return space_check(path, reserve)

    log = folder / "solver.log"
    try:
        with log.open("xb") as stream:
            process = guarded_run(
                command,
                cwd=root,
                env=os.environ,
                stdout=stream,
                space_root=root,
                reserve_bytes=2 * GIB,
                check=check,
            )
        record.update(process)
        if (folder / "solver.json").exists():
            record["solver"] = reference(folder / "solver.json")
        if process["returncode"] != 0:
            raise ValueError(f"cold solve failed: exit{process['returncode']}")
        record["wout"] = reference(folder / "wout.nc")
        record["metadata"] = metadata(folder / "wout.nc", folder / "input.json")
        measurement = measure(folder / "wout.nc", folder / "training")
        record.update(
            status="completed",
            measurement=dict(
                report=reference(folder / "training/measurement.json"), score=measurement["score"]
            ),
            eligible=True,
        )
    except Exception as exc:
        record.update(status="error", error=f"{type(exc).__name__}: {exc}", eligible=False)
    finally:
        record["elapsed_seconds"] = time.monotonic() - started
        if log.exists():
            record["log"] = reference(log)
        write_json_atomic(folder / "cell.json", record)
    return record


def search(evaluate):
    """Fixed-budget, stable tie-breaking coordinate polls; mocks can exercise the whole loop."""
    records, events, rounds, cache = [], [], [], {}

    def at(point):
        key = tuple(map(float, point))
        hit = key in cache
        if not hit:
            index = len(records)
            records.append(evaluate(np.asarray(point), index))
            cache[key] = index
        events.append(dict(x=list(key), cache_hit=hit, record=cache[key]))
        return cache[key]

    center = at(np.zeros(4))
    if not records[center]["eligible"]:
        raise ValueError("baseline equilibrium/action gate failed; no search allowed")
    step = 2e-4
    for number in (1, 2):
        indices = [center] + [at(p) for p in poll_points(records[center]["x"], step)]
        selected = indices[choose([records[i] for i in indices])]
        rounds.append(
            dict(round=number, center=center, step=step, candidates=indices, selected=selected)
        )
        step = step if selected != center else step / 2
        center = selected
    return dict(
        records=records,
        events=events,
        rounds=rounds,
        selected=center,
        requests=len(events),
        unique_solves=len(records),
        cache_hits=sum(r["cache_hit"] for r in events),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    output, raw = args.output.resolve(), args.raw.resolve()
    if output.exists() or raw.exists():
        raise FileExistsError("new plasma study/raw directories required")
    root = root_path()
    original, binding = sources(root)
    space_check(root, 3 * GIB)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        if os.environ.get(name) != "1":
            raise ValueError("registered single-thread environment required")
    output.mkdir(parents=True)
    raw.mkdir(parents=True)
    report = dict(
        status="running",
        source=binding,
        repository=git_state(root),
        host=host_state(),
        cells=[],
        endpoints=[],
        step3_pass=False,
        new_equilibrium_attempts=0,
        thread_environment={
            name: os.environ[name]
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        },
        versions={name: importlib.metadata.version(name) for name in ("numpy", "scipy", "netCDF4")},
    )

    def checkpoint():
        write_json_atomic(output / "summary.json", report)

    def evaluate(x, index):
        report.update(
            active=f"search-{index}",
            new_equilibrium_attempts=report["new_equilibrium_attempts"] + 1,
        )
        checkpoint()
        print(f"Plasma search: solve{index} x={x.tolist()}", flush=True)
        row = solve(root, raw / f"search-{index}", original, binding, x, 201)
        if row["eligible"] and report["cells"]:
            row["eligible"] = geometry_guard(row["metadata"], report["cells"][0]["metadata"])
        row["cell_record"] = reference(raw / f"search-{index}/cell.json")
        report["cells"].append(row)
        checkpoint()
        print(
            f"Plasma result{index}: eligible={row['eligible']} score={row.get('measurement')}",
            flush=True,
        )
        return row

    try:
        record = search(evaluate)
        report.update(
            search={k: v for k, v in record.items() if k != "records"}, status="endpoints"
        )
        selected = report["cells"][record["selected"]]
        for label, x, ns in (
            ("selected-repeat", selected["x"], 201),
            ("reference-fine", [0.0] * 4, 401),
            ("selected-fine", selected["x"], 401),
        ):
            report.update(
                active=label, new_equilibrium_attempts=report["new_equilibrium_attempts"] + 1
            )
            checkpoint()
            print(f"Plasma endpoint: {label}", flush=True)
            row = solve(root, raw / label, original, binding, x, ns)
            report["endpoints"].append(dict(label=label, **row))
            checkpoint()
        report["status"] = "completed"
        del report["active"]
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        checkpoint()
    print(
        json.dumps(
            dict(
                status=report["status"],
                solves=report["new_equilibrium_attempts"],
                selected=report["search"]["selected"],
                step3_pass=False,
            )
        )
    )
    return 0 if all(r["eligible"] for r in report["endpoints"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
