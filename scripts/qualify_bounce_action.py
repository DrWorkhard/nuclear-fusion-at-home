"""Execute preregistered QI measurement v1; persist failures and raw trace hashes."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import platform
import time
import warnings
from pathlib import Path

import numpy as np
import scipy
from evaluate_published_maximum_j import VmecAdapter, load_published_functions

from fusion_baselines.bounce_action import action_envelope, bounce_wells
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic

SURFACES = [0.25, 0.5, 0.75]
PITCH_FRACTIONS = [0.1, 0.3, 0.5, 0.7, 0.9]
LEVELS = [(401, 16, 2), (801, 16, 2), (1601, 16, 2), (1601, 32, 2), (3201, 32, 4)]


def file_record(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def compare_levels(previous, current, *, action_check=False):
    cells = []
    for before, after in zip(previous["cells"], current["cells"], strict=True):
        a, b = before["summary"]["envelope"], after["summary"]["envelope"]
        difference = abs(b - a) if a is not None and b is not None else None
        tolerance = max(0.002, 0.05 * abs(a)) if a is not None else None
        cell = {
            "s": before["s"],
            "bounce_field": before["bounce_field"],
            "envelope_change": difference,
            "tolerance": tolerance,
            "envelope_pass": difference is not None and difference <= tolerance,
        }
        if action_check:
            errors = []
            topology_matches = True
            for left, right in zip(before["wells_by_alpha"], after["wells_by_alpha"], strict=True):
                left = [w for w in left if w["complete"]]
                right = [w for w in right if w["complete"]]
                if len(left) != len(right) or not left:
                    topology_matches = False
                    continue
                errors.extend(
                    abs(y["action"] / x["action"] - 1) for x, y in zip(left, right, strict=True)
                )
            maximum = max(errors) if errors else None
            cell.update(
                topology_matches=topology_matches,
                max_relative_action_change=maximum,
                action_pass=topology_matches and maximum is not None and maximum <= 1e-3,
            )
        cells.append(cell)
    return {
        "previous_resolution": previous["resolution"],
        "current_resolution": current["resolution"],
        "cells": cells,
        "all_pass": all(c["envelope_pass"] and c.get("action_pass", True) for c in cells),
    }


def run_case(root, case_name, output_root):
    started = time.monotonic()
    source = root / "external/data/qifiles-v1/Files/plots/plot_elephants/PltElephants.py"
    reference = json.loads((root / "references/goodman_qi_transfer_cases.json").read_text())
    wout = (
        root
        / f"external/data/qifiles-v1/Files/configurations/{case_name}/vacuum/wout_QI_{case_name}.nc"
    )
    if sha256_file(wout) != reference["cases"][case_name]["wout_sha256"]:
        raise ValueError("wout hash differs from frozen transfer specification")
    if sha256_file(source) != reference["published_metric_code"]["maximum_j_plot_code_sha256"]:
        raise ValueError("published trace source hash differs from transfer specification")
    output = output_root / f"{case_name}.json"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing experiment: {output}")
    trace, _ = load_published_functions(source)
    vmec = VmecAdapter(wout)
    record = {
        "schema_version": 1,
        "case": case_name,
        "status": "running",
        "protocol": file_record(root / "docs/qi/QI_MEASUREMENT_PROTOCOL.md"),
        "inputs": {"wout": file_record(wout), "published_trace": file_record(source)},
        "code": [
            file_record(Path(__file__)),
            file_record(root / "src/fusion_baselines/bounce_action.py"),
            file_record(root / "scripts/evaluate_published_maximum_j.py"),
        ],
        "repository": git_state(root),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "surfaces": SURFACES,
        "pitch_fractions": PITCH_FRACTIONS,
        "levels": [],
        "scientific_QI_qualification_pass": False,
        "limitations": [
            "shared legacy field-line tracer",
            "no well-family matching",
            "no contour topology",
            "no radial/pitch refinement",
            "vacuum only",
        ],
    }
    write_json_atomic(output, record)
    fields = None
    raw_root = root / "artifacts/qi-measurement-v1" / case_name
    raw_root.mkdir(parents=True, exist_ok=True)
    try:
        for level_index, (nphi, nalpha, periods) in enumerate(LEVELS):
            traces = []
            diagnostics = []
            trace_files = []
            for surface in SURFACES:
                print(
                    f"{case_name}: level={level_index} nphi={nphi} nalpha={nalpha} s={surface}",
                    flush=True,
                )
                messages = io.StringIO()
                with (
                    warnings.catch_warnings(record=True) as caught,
                    contextlib.redirect_stdout(messages),
                ):
                    warnings.simplefilter("always")
                    values = trace(
                        vmec,
                        phi_start=0,
                        nphi=nphi,
                        alpha0=0,
                        nalpha=nalpha,
                        nfpinc=periods,
                        snorm=surface,
                        verbose=False,
                    )
                diagnostic = {
                    "s": surface,
                    "stdout": messages.getvalue(),
                    "warnings": [str(w.message) for w in caught],
                }
                diagnostics.append(diagnostic)
                if "error" in diagnostic["stdout"].lower():
                    raise ValueError(f"published tracing reported an error: {diagnostic}")
                if not np.all(np.isfinite(values.B)) or np.any(values.B <= 0):
                    raise ValueError("invalid traced B")
                length = values.ls - values.ls[0]
                length *= np.sign(length[-1])[None, :]
                if not np.all(np.isfinite(length)) or np.any(np.diff(length, axis=0) <= 0):
                    raise ValueError("nonfinite or nonmonotone traced arc length")
                raw = raw_root / f"level{level_index}-s{surface}.npz"
                if raw.exists():
                    raise FileExistsError(f"refusing to overwrite raw trace: {raw}")
                np.savez_compressed(
                    raw, B=values.B, length=length, alpha=values.alphas, phi=values.phis
                )
                trace_files.append(file_record(raw))
                traces.append((surface, values.B, length))
            if fields is None:
                lower = max(float(np.max(np.min(b, axis=0))) for _, b, _ in traces)
                upper = min(float(np.min(np.max(b, axis=0))) for _, b, _ in traces)
                if lower >= upper:
                    raise ValueError("empty common trapped-field interval")
                fields = [lower + q * (upper - lower) for q in PITCH_FRACTIONS]
                record["frozen_bounce_fields"] = fields
                record["coarse_common_interval"] = [lower, upper]
            level = {
                "resolution": [nphi, nalpha, periods],
                "cells": [],
                "traces": trace_files,
                "trace_diagnostics": diagnostics,
            }
            for surface, b, length in traces:
                for bounce_field in fields:
                    wells = [
                        bounce_wells(length[:, a], b[:, a], bounce_field) for a in range(nalpha)
                    ]
                    level["cells"].append(
                        {
                            "s": surface,
                            "bounce_field": bounce_field,
                            "summary": action_envelope(wells),
                            "wells_by_alpha": [[w.record() for w in line] for line in wells],
                        }
                    )
            record["levels"].append(level)
            record["elapsed_seconds"] = time.monotonic() - started
            write_json_atomic(output, record)
        record["comparisons"] = [
            compare_levels(a, b, action_check=i == 1)
            for i, (a, b) in enumerate(
                zip(record["levels"][:-1], record["levels"][1:], strict=True)
            )
        ]
        record["all_alpha_coverage_pass"] = all(
            cell["summary"]["complete_alpha_coverage"] == 1
            for level in record["levels"]
            for cell in level["cells"]
        )
        record["bounded_measurement_screen_pass"] = record["all_alpha_coverage_pass"] and all(
            c["all_pass"] for c in record["comparisons"]
        )
        record["status"] = "completed"
    except Exception as error:
        record.update(
            status="error",
            error=f"{type(error).__name__}: {error}",
            bounded_measurement_screen_pass=False,
        )
        raise
    finally:
        record["elapsed_seconds"] = time.monotonic() - started
        write_json_atomic(output, record)
    print(f"{case_name}: bounded screen={record['bounded_measurement_screen_pass']}", flush=True)
    return record["bounded_measurement_screen_pass"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=["nfp1", "nfp2", "nfp3", "all"], default="all")
    parser.add_argument("--output-root", type=Path, default=Path("evidence/qi-measurement-v1"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cases = ["nfp1", "nfp2", "nfp3"] if args.case == "all" else [args.case]
    passed = [run_case(root, case, args.output_root) for case in cases]
    return 0 if all(passed) else 2


if __name__ == "__main__":
    raise SystemExit(main())
