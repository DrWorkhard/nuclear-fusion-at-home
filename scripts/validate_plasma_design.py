"""Frozen no-feedback fine-domain, topology, field and second-tracer evaluation."""

import argparse
import contextlib
import io
import json
import warnings
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from evaluate_published_maximum_j import VmecAdapter, load_published_functions
from plasma_inputs import root_path, sources
from plasma_measurement import measure

from fusion_baselines.clebsch_field import compare_fields
from fusion_baselines.contour_topology import surface_field, two_root_winding
from fusion_baselines.plasma_design import (
    HOLD_PITCHES,
    HOLD_SURFACES,
    LEVELS,
    PITCHES,
    SURFACES,
    bounce_field,
    period_actions,
)
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.qi_field_grid import sample
from fusion_baselines.resource_guard import GIB, space_check
from fusion_baselines.vmec_trace import trace_geometry


def field_checks(wout, folder):
    rows = []
    for s in SURFACES:
        previous = None
        for n in (64, 128):
            arrays = sample(wout, s, n)
            args = {
                k: arrays[k]
                for k in ("psi", "g", "bt", "bp", "lt", "lp", "iota", "et", "ep", "mod_b")
            }
            native, clebsch, errors, checks = compare_fields(**args)
            path = folder / f"field-s{s}-n{n}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, **arrays, native=native, clebsch=clebsch)
            row = dict(s=s, n=n, arrays=reference(path), errors=errors, checks=checks)
            if previous:
                row["refinement"] = {
                    k: abs(errors[k] - previous[k])
                    for k in ("poloidal", "toroidal", "cartesian", "magnitude")
                }
            previous = errors
            rows.append(row)
    return rows


def published_crosscheck(wout, source, folder):
    trace, _ = load_published_functions(source)
    rows = []
    for s in SURFACES:
        messages = io.StringIO()
        with warnings.catch_warnings(record=True) as caught, contextlib.redirect_stdout(messages):
            warnings.simplefilter("always")
            actual = trace(
                VmecAdapter(wout),
                phi_start=0,
                nphi=801,
                alpha0=0,
                nalpha=16,
                nfpinc=2,
                snorm=s,
                verbose=False,
            )
        independent = trace_geometry(wout, s, 801, 16, 2)
        length = actual.ls - actual.ls[0]
        length *= np.sign(length[-1])[None, :]
        berror = float(np.max(abs(independent["B"] / actual.B - 1)))
        lerror = float(np.max(abs(length - independent["length"])) / np.max(length))
        path = folder / f"published-s{s}.npz"
        with path.open("xb") as stream:
            np.savez_compressed(
                stream,
                B=actual.B,
                length=length,
                phi=independent["phi"],
                alpha=independent["alpha"],
            )
        errors = []
        alternate = dict(
            B=actual.B, length=length, phi=independent["phi"], alpha=independent["alpha"]
        )
        for q in PITCHES:
            a, b = [np.array(period_actions(t, q)["actions"]) for t in (alternate, independent)]
            errors.append(float(np.max(abs(a / b - 1))))
        rows.append(
            dict(
                s=s,
                arrays=reference(path),
                field_relative_error=berror,
                length_normalized_error=lerror,
                action_relative_errors=errors,
                warnings=[str(w.message) for w in caught],
                stdout=messages.getvalue(),
                all_pass=berror <= 1e-8
                and lerror <= 1e-3
                and max(errors) <= 1e-3
                and "error" not in messages.getvalue().lower(),
            )
        )
    return dict(source=reference(source), rows=rows, all_pass=all(r["all_pass"] for r in rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new holdout report/raw path required")
    root = root_path()
    _, binding = sources(root)
    study_path = args.study / "summary.json"
    study = json.loads(study_path.read_text())
    if study["status"] != "completed" or study["source"] != binding:
        raise ValueError("complete fixed-source search required")
    selected = study["cells"][study["search"]["selected"]]
    states = [
        ("reference-201", study["cells"][0]),
        ("selected-201", selected),
        ("reference-401", study["endpoints"][1]),
        ("selected-401", study["endpoints"][2]),
    ]
    report = dict(
        status="running",
        study=reference(study_path),
        source=binding,
        repository=git_state(root),
        states=[],
        used_for_selection=False,
        step3_pass=False,
    )
    args.raw.mkdir(parents=True)
    try:
        for label, state in states:
            space_check(root, 2 * GIB)
            folder = args.raw / label
            folder.mkdir()
            row = dict(
                label=label,
                wout=state.get("wout"),
                measurements=[],
                fields=[],
                contours=[],
                errors=[],
            )
            report["states"].append(row)
            for i, (nphi, nalpha, offset) in enumerate(LEVELS):
                print(f"Plasma holdout: {label} trace level{i}", flush=True)
                try:
                    measure(
                        checked(state["wout"]),
                        folder / f"level-{i}",
                        surfaces=HOLD_SURFACES,
                        pitches=HOLD_PITCHES,
                        nphi=nphi,
                        nalpha=nalpha,
                        offset=offset,
                    )
                except Exception as exc:
                    row["errors"].append(f"trace{i}: {type(exc).__name__}: {exc}")
                path = folder / f"level-{i}/measurement.json"
                row["measurements"].append(reference(path) if path.exists() else None)
                write_json_atomic(args.output, report)
            try:
                row["fields"] = field_checks(checked(state["wout"]), folder)
            except Exception as exc:
                row["errors"].append(f"field: {type(exc).__name__}: {exc}")
            for nt, nz in ((256, 512), (512, 1024)):
                for s in HOLD_SURFACES:
                    print(f"Plasma holdout: {label} contour{nt} s{s}", flush=True)
                    try:
                        field = surface_field(checked(state["wout"]), s, nt, nz)
                        path = folder / f"contour-s{s}-n{nt}.npz"
                        with path.open("xb") as stream:
                            np.savez_compressed(stream, B=field)
                        row["contours"].append(
                            dict(
                                s=s,
                                resolution=[nt, nz],
                                arrays=reference(path),
                                cells=[
                                    dict(q=q, **two_root_winding(field, bounce_field(q)))
                                    for q in HOLD_PITCHES
                                ],
                            )
                        )
                    except Exception as exc:
                        row["errors"].append(f"contour{nt}-{s}: {type(exc).__name__}: {exc}")
                    write_json_atomic(args.output, report)
            if label.endswith("401"):
                try:
                    row["crosscheck"] = published_crosscheck(
                        checked(state["wout"]),
                        root
                        / "external/data/qifiles-v1/Files/plots/plot_elephants/PltElephants.py",
                        folder,
                    )
                except Exception as exc:
                    row["errors"].append(f"published: {type(exc).__name__}: {exc}")
            write_json_atomic(args.output, report)
        report.update(
            status="completed", all_phases_completed=all(not r["errors"] for r in report["states"])
        )
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_phases_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
