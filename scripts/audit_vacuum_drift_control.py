"""Independent243-state scalar vacuum action/FD audit; no Cartesian producer imports."""

import argparse
import importlib.metadata
import itertools
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.vacuum_drift_audit import audit_vacuum_cell, error
from fusion_baselines.vacuum_scalar import scalar_vacuum

LINES = list(itertools.product((0.01, 0.03, 0.06), (1.2, 1.6, 2.0), (0.2, 0.6, 1.1)))
CODE = (
    "scripts/audit_vacuum_drift_control.py",
    "src/fusion_baselines/vacuum_scalar.py",
    "src/fusion_baselines/vacuum_drift_audit.py",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable vacuum audit required")
    root = Path(__file__).resolve().parents[1]
    for name in CODE:
        require_committed(root, root / name)
    study = json.loads(args.study.read_text())
    report = dict(
        repository=git_state(root),
        source=reference(args.study),
        code=[reference(root / p) for p in CODE],
        status="running",
        versions={p: importlib.metadata.version(p) for p in ("numpy", "scipy")},
        scalar_runs=[],
        differences=[],
        cells=[],
        refinements=[],
        native_calls=0,
        full_qi_admission=False,
    )
    try:
        for ref in [study["protocol"], *study["code"]]:
            checked(ref)
        expected = [(*line, n) for line in LINES for n in (64, 128, 256)]
        if (
            study["protocol"] != reference(root / "docs/qi/VACUUM_DRIFT_CONTROL_PROTOCOL.md")
            or study["status"] != "completed"
            or not study["all_cells_completed"]
            or [(r["psi"], r["bstar"], r["alpha"], r["nodes"]) for r in study["cells"]] != expected
        ):
            raise ValueError("complete ordered registered vacuum cells required")

        def scalar_run(psi, bstar, alpha):
            row = {}
            report["scalar_runs"].append(row)
            try:
                return scalar_vacuum(psi, bstar, alpha, record=row)
            finally:
                write_json_atomic(args.output, report)

        for line_index, (psi, bstar, alpha) in enumerate(LINES):
            scalar = scalar_run(psi, bstar, alpha)
            differences = []
            for coordinate in ("psi", "alpha"):
                for step in (1e-4, 1e-5):
                    h = psi * step if coordinate == "psi" else step
                    plus = scalar_run(
                        psi + h if coordinate == "psi" else psi,
                        bstar,
                        alpha + h if coordinate == "alpha" else alpha,
                    )
                    minus = scalar_run(
                        psi - h if coordinate == "psi" else psi,
                        bstar,
                        alpha - h if coordinate == "alpha" else alpha,
                    )
                    differences.append(
                        dict(
                            coordinate=coordinate,
                            step=step,
                            derivative=(
                                plus["integrals"]["action"]["value"]
                                - minus["integrals"]["action"]["value"]
                            )
                            / (2 * h),
                        )
                    )
            report["differences"].append(
                dict(psi=psi, bstar=bstar, alpha=alpha, values=differences)
            )
            cells = study["cells"][3 * line_index : 3 * line_index + 3]
            for cell in cells:
                with np.load(checked(cell["arrays"]), allow_pickle=False) as arrays:
                    row = audit_vacuum_cell(cell, arrays, scalar, differences)
                report["cells"].append(row)
            errors = [
                {
                    k: error(lower["values"][k], upper["values"][k])
                    for k in ("action", "transit_length", "dpsi", "dalpha")
                }
                for lower, upper in zip(cells[:-1], cells[1:], strict=True)
            ]
            passed = all(e <= 1e-7 for r in errors for e in r.values())
            report["refinements"].append(
                dict(
                    errors=errors,
                    all_pass=passed
                    and study["refinements"][line_index] == dict(errors=errors, all_pass=passed),
                )
            )
            write_json_atomic(args.output, report)
        checks = dict(
            cells=all(r["all_pass"] for r in report["cells"]),
            refinements=all(r["all_pass"] for r in report["refinements"]),
            no_warnings=not any(r["warnings"] for r in report["scalar_runs"])
            and not any(r["warnings"] for r in study["cells"]),
            producer_pass=study["all_pass"] is True,
            no_qi_admission=study["full_qi_admission"] is False,
            scalar_count=len(report["scalar_runs"]) == 9 * len(LINES),
        )
        report.update(status="completed", checks=checks, all_pass=all(checks.values()))
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}", all_pass=False)
        raise
    finally:
        write_json_atomic(args.output, report)
    print(dict(all_pass=report["all_pass"], scalar_runs=len(report["scalar_runs"])))
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
