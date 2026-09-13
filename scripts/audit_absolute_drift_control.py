"""Scalar adaptive and both fixed FD checks of all stored analytic drift cells."""

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from run_jac_scaled_study import require_committed

from fusion_baselines.mirror_scalar_audit import audit_values, relative, scalar_action
from fusion_baselines.provenance import git_state, write_json_atomic

CODE = (
    "scripts/audit_absolute_drift_control.py",
    "src/fusion_baselines/mirror_scalar_audit.py",
)
PAIRS = list(itertools.product((0.01, 0.03, 0.06), (1.2, 1.6, 2.0)))
ANGLES = (0.0, 0.37, 1.2)


def array_checks(cell, data):
    n = cell["nodes"]
    if any(not np.isfinite(data[key]).all() for key in data):
        raise ValueError("nonfinite saved analytic arrays")
    if data["points"].shape != (n, 3) or data["weights"].shape != (n,):
        raise ValueError("complete registered Cartesian quadrature required")
    checks = {}
    checks["cell_work"] = cell["work"] == dict(
        root_calls=cell["root_calls"], cartesian_points_requested=n, cartesian_points_completed=n
    )
    for key, value in cell["values"].items():
        checks[f"sum_{key}"] = abs(
            math.fsum(float(w) * float(f) for w, f in zip(data["weights"], data[key], strict=True))
            - value
        ) <= 1e-12 * max(1.0, abs(value))
    x, y, z = data["points"].T
    s = 1 + 0.7 * z * z
    expected_b = np.column_stack((-0.7 * z * x, -0.7 * z * y, s))
    expected_psi = s * (x * x + y * y) / 2
    expected_z = cell["turning_point_z"] * np.sin(data["u"])
    magnitude = np.sqrt(sum(expected_b[:, i] ** 2 for i in range(3)))
    checks["cartesian_field"] = bool(np.max(abs(data["field_B"] - expected_b)) <= 1e-12)
    checks["flux_label"] = bool(np.max(abs(expected_psi - cell["psi"])) <= 1e-12)
    checks["angle_label"] = bool(np.max(abs(np.arctan2(y, x) - cell["alpha"])) <= 1e-12)
    checks["sin_transform"] = bool(np.max(abs(z - expected_z)) <= 1e-12)
    checks["quadrature_weight"] = abs(math.fsum(map(float, data["weights"])) - math.pi) <= 1e-12
    checks["open_interval"] = bool(np.all(magnitude < cell["bstar"]))
    checks["components_add"] = (
        relative(
            cell["values"]["alpha_gradient"] + cell["values"]["alpha_curvature"],
            cell["values"]["delta_alpha_reduced"],
        )
        <= 1e-12
    )
    clebsch = np.cross(data["field_grad_psi"], data["field_grad_alpha"])
    errors = dict(
        clebsch=float(np.max(abs(clebsch - expected_b))) / max(1.0, float(np.max(abs(expected_b)))),
        divergence=float(np.max(abs(data["field_divergence"]))),
        force_balance=float(np.max(abs(data["field_force_balance_residual"])))
        / max(1.0, float(np.max(abs(0.7 * data["field_grad_psi"])))),
        flux_label=float(np.max(abs(data["field_psi"] - cell["psi"]))) / max(1.0, abs(cell["psi"])),
    )
    checks["field_identities"] = max(errors.values()) <= 1e-12
    checks["reported_identities"] = all(
        abs(v - cell["identity_errors"][k]) <= 1e-14 for k, v in errors.items()
    )
    expected_flags = dict(
        field_identities=checks["field_identities"],
        action_drift=relative(cell["values"]["delta_alpha_reduced"], -cell["values"]["action_psi"])
        <= 1e-8,
        radial_zero=abs(cell["values"]["delta_psi_reduced"]) <= 1e-10,
    )
    checks["reported_flags"] = expected_flags == cell["checks"] and cell["all_pass"] == all(
        expected_flags.values()
    )
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable scalar audit required")
    root = Path(__file__).resolve().parents[1]
    for name in CODE:
        require_committed(root, root / name)
    study = json.loads(args.study.read_text())
    result = dict(
        repository=git_state(root),
        code=[reference(root / p) for p in CODE],
        source=reference(args.study),
        status="running",
        scalar_runs=[],
        differences=[],
        cells=[],
        refinement_errors=[],
        native_calls=0,
        full_qi_admission=False,
    )
    try:
        for ref in [study["protocol"], *study["code"]]:
            checked(ref)
        if study["protocol"] != reference(root / "docs/qi/ABSOLUTE_DRIFT_CONTROL_PROTOCOL.md"):
            raise ValueError("registered analytic mirror protocol required")
        expected = [(p, b, a, n) for p, b in PAIRS for a in ANGLES for n in (64, 128, 256)]
        if (
            study["status"] != "completed"
            or not study["all_cells_completed"]
            or [(c["psi"], c["bstar"], c["alpha"], c["nodes"]) for c in study["cells"]] != expected
        ):
            raise ValueError("all ordered registered cells required")
        scalar_pairs = {}

        def scalar_run(psi, bstar):
            row = {}
            result["scalar_runs"].append(row)
            try:
                return scalar_action(psi, bstar, record=row)
            finally:
                write_json_atomic(args.output, result)

        for psi, bstar in PAIRS:
            scalar = scalar_run(psi, bstar)
            differences = []
            for step in (1e-4, 1e-5):
                plus, minus = (
                    scalar_run(psi * (1 + step), bstar),
                    scalar_run(psi * (1 - step), bstar),
                )
                differences.append(
                    dict(
                        psi=psi,
                        bstar=bstar,
                        relative_step=step,
                        derivative=(
                            plus["integrals"]["action"]["value"]
                            - minus["integrals"]["action"]["value"]
                        )
                        / (2 * psi * step),
                    )
                )
                write_json_atomic(args.output, result)
            result["differences"].extend(differences)
            scalar_pairs[(psi, bstar)] = scalar, differences
        for cell in study["cells"]:
            scalar, differences = scalar_pairs[(cell["psi"], cell["bstar"])]
            row = audit_values(cell, scalar, differences)
            with np.load(checked(cell["arrays"]), allow_pickle=False) as data:
                row["array_checks"] = array_checks(cell, data)
            row["all_pass"] = row["all_pass"] and all(row["array_checks"].values())
            result["cells"].append(row)
        for start in range(0, len(study["cells"]), 3):
            line = study["cells"][start : start + 3]
            errors = []
            for lower, upper in zip(line[:-1], line[1:], strict=True):
                errors.append(
                    {
                        k: relative(lower["values"][k], upper["values"][k])
                        for k in ("action", "transit_length", "delta_alpha_reduced")
                    }
                )
            passed = all(e <= 1e-7 for r in errors for e in r.values())
            reported = study["refinements"][start // 3]
            result["refinement_errors"].append(
                dict(
                    errors=errors,
                    all_pass=passed and reported == dict(errors=errors, all_pass=passed),
                )
            )
        work = study["work"]
        checks = dict(
            all_cells=all(r["all_pass"] for r in result["cells"]),
            all_refinements=all(r["all_pass"] for r in result["refinement_errors"]),
            no_warnings=not any(r["warnings"] for r in result["scalar_runs"])
            and not any(r["warnings"] for r in study["cells"]),
            producer_pass=study["all_pass"] is True,
            no_qi_admission=study["full_qi_admission"] is False,
            producer_work=work
            == dict(
                cell_attempts=len(expected),
                cell_completed=len(expected),
                cartesian_points_completed=sum(e[3] for e in expected),
                root_calls=sum(c["root_calls"] for c in study["cells"]),
            ),
        )
        result.update(status="completed", checks=checks, all_pass=all(checks.values()))
    except Exception as error:
        result.update(status="error", error=f"{type(error).__name__}: {error}", all_pass=False)
        raise
    finally:
        write_json_atomic(args.output, result)
    print({"all_pass": result["all_pass"], "scalar_runs": len(result["scalar_runs"])})
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
