"""Registered non-axisymmetric vacuum matrix, retaining all cells and failures."""

import argparse
import importlib.metadata
import itertools
import warnings
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import reference
from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check
from fusion_baselines.vacuum_bounce import normalized_error, vacuum_cell

LINES = list(itertools.product((0.01, 0.03, 0.06), (1.2, 1.6, 2.0), (0.2, 0.6, 1.1)))
CODE = (
    "scripts/run_vacuum_drift_control.py",
    "src/fusion_baselines/vacuum_bounce.py",
    "src/fusion_baselines/vacuum_mirror.py",
    "src/fusion_baselines/analytic_mirror.py",
)
PROTOCOL = "docs/qi/VACUUM_DRIFT_CONTROL_PROTOCOL.md"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("immutable new vacuum study required")
    root = Path(__file__).resolve().parents[1]
    for name in (*CODE, PROTOCOL):
        require_committed(root, root / name)
    reserve = space_check(root, 2 * GIB)
    args.raw.mkdir(parents=True)
    report = dict(
        repository=git_state(root),
        host=host_state(),
        code=[reference(root / p) for p in CODE],
        protocol=reference(root / PROTOCOL),
        versions={p: importlib.metadata.version(p) for p in ("numpy", "scipy")},
        disk_preflight=reserve,
        status="running",
        cells=[],
        refinements=[],
        native_calls=0,
        full_qi_admission=False,
    )
    try:
        for psi, bstar, alpha in LINES:
            line = []
            for nodes in (64, 128, 256):
                row = dict(
                    psi=psi, bstar=bstar, alpha=alpha, nodes=nodes, status="running", work={}
                )
                report["cells"].append(row)
                messages = []
                try:
                    with warnings.catch_warnings(record=True) as messages:
                        warnings.simplefilter("always")
                        computed, arrays = vacuum_cell(psi, bstar, alpha, nodes, work=row["work"])
                    row.update(computed)
                    path = args.raw / f"cell-{len(report['cells']) - 1:03d}.npz"
                    np.savez_compressed(path, **arrays)
                    row.update(status="completed", arrays=reference(path))
                except (ValueError, RuntimeError) as error:
                    row.update(
                        status="error", error=f"{type(error).__name__}: {error}", all_pass=False
                    )
                finally:
                    row["warnings"] = [str(w.message) for w in messages]
                    line.append(row)
                    write_json_atomic(args.output, report)
            if all(r["status"] == "completed" for r in line):
                errors = [
                    {
                        k: normalized_error(lower["values"][k], upper["values"][k])
                        for k in ("action", "transit_length", "dpsi", "dalpha")
                    }
                    for lower, upper in zip(line[:-1], line[1:], strict=True)
                ]
                report["refinements"].append(
                    dict(errors=errors, all_pass=all(e <= 1e-7 for r in errors for e in r.values()))
                )
            else:
                report["refinements"].append(dict(all_pass=False, error="incomplete line"))
        complete = all(r["status"] == "completed" for r in report["cells"])
        report.update(
            status="completed",
            all_cells_completed=complete,
            all_pass=complete
            and all(r["all_pass"] and not r["warnings"] for r in report["cells"])
            and all(r["all_pass"] for r in report["refinements"]),
        )
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}", all_pass=False)
        raise
    finally:
        write_json_atomic(args.output, report)
    print(dict(cells=len(report["cells"]), all_pass=report["all_pass"]))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
