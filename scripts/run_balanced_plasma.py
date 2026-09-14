"""Separate immutable archive, proposal and cold-endpoint phases for two-domain design."""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path

import numpy as np
from balanced_plasma_inputs import sources
from current_diagnostic_inputs import checked, reference
from plasma_inputs import root_path
from plasma_measurement import measure
from run_plasma_search import solve

from fusion_baselines.balanced_plasma import (
    BOX,
    FD_STEP,
    SCALES,
    arrays,
    construction,
    proposal,
    select,
)
from fusion_baselines.plasma_design import HOLD_PITCHES, HOLD_SURFACES
from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check


def read(ref):
    return json.loads(checked(ref).read_text())


def broad(native, folder, baseline=None):
    row = dict(native=native)
    try:
        if native["status"] != "completed":
            raise ValueError("failed native candidate")
        wide = measure(
            checked(native["wout"]), folder, surfaces=HOLD_SURFACES, pitches=HOLD_PITCHES
        )
        row.update(wide=reference(folder / "measurement.json"), wide_score=wide["score"])
        if baseline is not None:
            row["construction"] = construction(
                native["measurement"]["score"],
                wide,
                baseline["native"]["measurement"]["score"],
                read(baseline["wide"]),
                native["metadata"],
                baseline["native"]["metadata"],
            )
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        if (folder / "measurement.json").exists():
            row["wide"] = reference(folder / "measurement.json")
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("archive", "propose", "endpoints"))
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    root, output, raw = root_path(), args.output.resolve(), args.raw.resolve()
    destination = output / f"{args.phase}.json"
    if destination.exists() or (raw / args.phase).exists():
        raise FileExistsError("new immutable balanced phase paths required")
    original, binding, predecessor = sources(root)
    space_check(root, 3 * GIB)
    thread_env = {
        k: os.environ.get(k)
        for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
    }
    if set(thread_env.values()) != {"1"}:
        raise ValueError("one-thread environment required")
    output.mkdir(parents=True, exist_ok=True)
    (raw / args.phase).mkdir(parents=True)
    report = dict(
        phase=args.phase,
        status="running",
        source=binding,
        rows=[],
        new_solves=0,
        repository=git_state(root),
        host=host_state(),
        thread_environment=thread_env,
        step3_pass=False,
        versions={name: importlib.metadata.version(name) for name in ("numpy", "scipy", "netCDF4")},
    )

    def save():
        write_json_atomic(destination, report)

    def cold(label, x, ns, baseline):
        report.update(active=label, new_solves=report["new_solves"] + 1)
        save()
        print(f"Balanced {args.phase}: {label}, x={list(x)}, ns={ns}", flush=True)
        folder = raw / args.phase / label
        native = solve(root, folder / "native", original, binding["legacy"], x, ns)
        result = broad(native, folder / "wide", baseline)
        report["rows"].append(dict(label=label, **result))
        save()
        return report["rows"][-1]

    try:
        if args.phase == "archive":
            for i, native in enumerate(predecessor["cells"]):
                print(f"Balanced archive: preserved state{i}", flush=True)
                space_check(root, 2 * GIB)
                row = broad(
                    native, raw / "archive" / f"state-{i}", report["rows"][0] if i else None
                )
                report["rows"].append(dict(source_index=i, **row))
                save()
                if i == 0 and row.get("error"):
                    raise ValueError("complete broad baseline required")
            report["selected"] = select(report["rows"])
        else:
            archive_path = output / "archive.json"
            archive = json.loads(archive_path.read_text())
            if archive["status"] != "completed" or archive["source"] != binding:
                raise ValueError("completed same-source archive phase required")
            report["archive"] = reference(archive_path)
            baseline = archive["rows"][0]
            if args.phase == "propose":
                if archive["selected"] is not None:
                    raise ValueError(
                        "proposal phase not authorized when archive already has a candidate"
                    )
                for k in range(4):
                    for sign in (1, -1):
                        cold(
                            f"fd-{k}-{'plus' if sign == 1 else 'minus'}",
                            sign * FD_STEP * np.eye(4)[k],
                            201,
                            baseline,
                        )
                if any(r.get("error") for r in report["rows"]):
                    raise ValueError("all eight finite-difference domains required")
                wide = [read(r["wide"]) for r in report["rows"]]
                model = proposal(
                    [r["native"]["measurement"]["score"] for r in report["rows"]],
                    [r["score"] for r in wide],
                    [arrays(r)["mean"] for r in wide],
                    baseline["native"]["measurement"]["score"],
                    baseline["wide_score"],
                    arrays(read(baseline["wide"]))["mean"],
                )
                report["model"] = model
                save()
                if not model["success"] or model["solution"][-1] <= 0:
                    raise ValueError("no positive common model descent")
                for i, scale in enumerate(SCALES):
                    cold(f"probe-{i}", BOX * np.array(model["solution"][:4]) * scale, 201, baseline)
                selected = select(report["rows"][8:])
                report["selected"] = None if selected is None else selected + 8
            else:
                owner, index = archive, archive["selected"]
                owner_path = archive_path
                if index is None:
                    owner_path = output / "propose.json"
                    owner = json.loads(owner_path.read_text())
                    if owner["status"] != "completed" or owner["source"] != binding:
                        raise ValueError("completed same-source proposal phase required")
                    index = owner["selected"]
                if index is None:
                    raise ValueError("no candidate admitted for independent validation")
                selected = owner["rows"][index]
                report.update(
                    selection=reference(owner_path), selected_index=index, selected=selected
                )
                cold("selected-repeat", selected["native"]["x"], 201, baseline)
                cold("selected-fine", selected["native"]["x"], 401, baseline)
                report["total_new_solves"] = owner["new_solves"] + report["new_solves"]
                if report["total_new_solves"] > 13:
                    raise ValueError("registered follow-up cold-solve cap")
        report["status"] = "completed"
        report.pop("active", None)
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
    finally:
        save()
    print(
        json.dumps(
            {k: report[k] for k in ("phase", "status", "new_solves", "selected") if k in report}
        )
    )
    return 0 if report["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
