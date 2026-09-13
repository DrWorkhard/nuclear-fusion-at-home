"""Run every registered analytic mirror cell; no native field/equilibrium calls."""

import argparse
import importlib.metadata
import itertools
import warnings
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import reference
from run_jac_scaled_study import require_committed

from fusion_baselines.mirror_bounce import bounce_cell, refinement_checks
from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check

CODE = (
    "scripts/run_absolute_drift_control.py",
    "src/fusion_baselines/analytic_mirror.py",
    "src/fusion_baselines/mirror_bounce.py",
)
PROTOCOL = "docs/qi/ABSOLUTE_DRIFT_CONTROL_PROTOCOL.md"
LINES = list(itertools.product((0.01, 0.03, 0.06), (1.2, 1.6, 2.0), (0.0, 0.37, 1.2)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable analytic study and raw directory required")
    root = Path(__file__).resolve().parents[1]
    for name in (*CODE, PROTOCOL):
        require_committed(root, root / name)
    reserve = space_check(root, 2 * GIB)
    args.raw.mkdir(parents=True)
    result = dict(
        repository=git_state(root),
        host=host_state(),
        code=[reference(root / p) for p in CODE],
        protocol=reference(root / PROTOCOL),
        versions={name: importlib.metadata.version(name) for name in ("numpy", "scipy")},
        disk_preflight=reserve,
        status="running",
        cells=[],
        refinements=[],
        work=dict(cell_attempts=0, cell_completed=0, cartesian_points_completed=0, root_calls=0),
        full_qi_admission=False,
        native_field_calls=0,
    )
    try:
        for psi, bstar, alpha in LINES:
            line = []
            for nodes in (64, 128, 256):
                cell = dict(psi=psi, bstar=bstar, alpha=alpha, nodes=nodes, status="running")
                result["cells"].append(cell)
                result["work"]["cell_attempts"] += 1
                progress = dict(
                    root_calls=0, cartesian_points_requested=0, cartesian_points_completed=0
                )
                cell["work"] = progress
                messages = []
                try:
                    with warnings.catch_warnings(record=True) as messages:
                        warnings.simplefilter("always")
                        computed, arrays = bounce_cell(psi, bstar, alpha, nodes, work=progress)
                    cell.update(computed)
                    path = args.raw / f"cell-{len(result['cells']) - 1:03d}.npz"
                    np.savez_compressed(path, **arrays)
                    cell.update(status="completed", arrays=reference(path))
                    result["work"]["cell_completed"] += 1
                except (ValueError, RuntimeError) as error:
                    cell.update(
                        status="error", error=f"{type(error).__name__}: {error}", all_pass=False
                    )
                finally:
                    result["work"]["cartesian_points_completed"] += progress[
                        "cartesian_points_completed"
                    ]
                    result["work"]["root_calls"] += progress["root_calls"]
                    cell["warnings"] = [str(w.message) for w in messages]
                    line.append(cell)
                    write_json_atomic(args.output, result)
            result["refinements"].append(
                refinement_checks(line)
                if all(r["status"] == "completed" for r in line)
                else dict(all_pass=False, error="incomplete line; no refinement invented")
            )
        complete = result["work"]["cell_completed"] == 3 * len(LINES)
        result.update(
            status="completed",
            all_cells_completed=complete,
            all_pass=complete
            and all(r["all_pass"] and not r["warnings"] for r in result["cells"])
            and all(r["all_pass"] for r in result["refinements"]),
        )
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}", all_pass=False)
        raise
    finally:
        write_json_atomic(args.output, result)
    print({"cells": len(result["cells"]), "all_pass": result["all_pass"]})
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
