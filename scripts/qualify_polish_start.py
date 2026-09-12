"""One native start replay plus fixed independent complex-step clearance qualification."""

import argparse
import json
from pathlib import Path

import numpy as np
from prepare_upstream_start import prepare
from qualify_complex_clearance import checked, errors, physical_coefficients, reference
from run_jac_scaled_study import require_committed
from simsopt import load
from simsopt.geo import SurfaceRZFourier

from fusion_baselines.coil_coefficient_view import base_arrays
from fusion_baselines.complex_clearance import clearance_rows, fourier_positions
from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_dofs import named_serialized_values

CODE = (
    "scripts/qualify_polish_start.py", "scripts/prepare_upstream_start.py",
    "scripts/qualify_complex_clearance.py", "src/fusion_baselines/coil_coefficient_view.py",
    "src/fusion_baselines/complex_clearance.py", "src/fusion_baselines/selected_start.py",
    "src/fusion_baselines/serialized_dofs.py", "src/fusion_baselines/direct_constraints.py",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable qualification required")
    root = Path(__file__).resolve().parents[1]
    failed_path = root / "evidence/slsqp-polish-v1/summary.json"
    arm_path = root / "evidence/slsqp-polish-v1/slsqp-1.json"
    audit_path = root / "evidence/slsqp-polish-v1-failure-audit-v2.json"
    failed, arm, audit = (json.loads(p.read_text()) for p in (failed_path, arm_path, audit_path))
    if (not audit["all_pass"] or audit["construction_qualified"] is not False
            or audit["study"] != reference(failed_path) or audit["arm"] != reference(arm_path)
            or failed["physical_start"]["sha256"] !=
            "65b9b85e942fa3ce54467ad29c319b92f1c2756489df4f668e563aa49d5836eb"):
        raise ValueError("fixed independently audited failed physical start required")
    protocol = root / "docs/optimization/POLISH_START_DERIVATIVE_PROTOCOL.md"
    for p in [failed_path, arm_path, audit_path, protocol, *(root / p for p in CODE)]:
        require_committed(root, p)
    original_qual = json.loads(checked(json.loads(checked(failed["source_study"]).read_text())[
        "qualification"]).read_text())
    for ref in [*failed["code"], *original_qual["code"], *original_qual["installed_sources"]]:
        checked(ref)
    source_path = checked(failed["physical_start"])
    source_doc = json.loads(source_path.read_text())
    names = failed["preparation"]["degrees_of_freedom"]
    x = named_serialized_values(source_doc, names)
    report = dict(repository=git_state(root), status="running", all_pass=False,
                  protocol=reference(protocol), failed_study=reference(failed_path),
                  failed_arm=reference(arm_path), failure_audit=reference(audit_path),
                  source_field=failed["physical_start"], source_names=names,
                  code=[reference(root / p) for p in CODE],
                  qualified_backend_code=original_qual["code"],
                  installed_sources=original_qual["installed_sources"], directions=[],
                  optimization_performed=False, original_all_row_fd_pass=False)
    args.raw.mkdir(parents=True)
    try:
        ctx, prep = prepare(root, args.raw)
        target_doc = json.loads(checked(prep["normalized_start"]).read_text())
        target_x, permutation, owners = mapped_start(
            source_doc, target_doc, names, prep["degrees_of_freedom"], x)
        full = SurfaceRZFourier.from_vmec_input(str(checked(prep["surface"])), range="full torus",
                                               nphi=64, ntheta=64)
        backend = DirectConstraintBackend(ctx, full)
        values, target_jac, _ = backend.evaluate(target_x)
        jacobian = target_jac[:, np.argsort(permutation)]
        source_field = load(str(source_path))
        coefficients = physical_coefficients(source_field, base_arrays(source_doc, names, x))
        native_positions = np.array([c.curve.gamma().copy() for c in source_field.coils])
        real, anchors = clearance_rows(coefficients, prep["thresholds"]["a0"])
        position_error = float(errors(fourier_positions(coefficients, 200), native_positions).max())
        replay_error = float(errors(values, arm["evaluations"][0]["values"]).max())
        real_error = errors(real, values[6:126])
        currents = [i for i, n in enumerate(names) if n.split(":", 1)[0].startswith("Current")]
        nonpair = np.asarray(arm["gradient_checks"][-1]["normalized_errors"])
        nonpair_max = float(np.r_[nonpair[:6], nonpair[126:]].max())
        checks = dict(initial_values=replay_error <= 1e-12, real_values=real_error.max() <= 1e-10,
                      physical_positions=position_error <= 1e-12,
                      current_columns=len(currents) == 3 and np.all(jacobian[6:126, currents] == 0),
                      original_nonpair_fd=nonpair_max <= 1e-6,
                      same_problem=all(prep[k] == failed["preparation"][k] for k in
                                       ("surface", "case", "thresholds", "guarded_search_targets",
                                        "canonical_total")))
        directions, dcoefficients = [], []
        for seed in (46, 47):
            direction = np.random.default_rng(seed).normal(size=207)
            direction /= np.linalg.norm(direction)
            dc = physical_coefficients(source_field,
                                        base_arrays(source_doc, names, direction, direction=True))
            directions.append(direction)
            dcoefficients.append(dc)
            analytic = jacobian @ direction
            if seed == 46:
                derivative_replay = float(errors(analytic, arm["gradient_checks"][0][
                    "analytic"]).max())
                checks["original_analytic_replay"] = derivative_replay <= 1e-12
            steps, first = [], None
            for h in (1e-12, 1e-20, 1e-28):
                complex_rows, _ = clearance_rows(coefficients+1j*h*dc,
                                                  prep["thresholds"]["a0"], anchors=anchors)
                derivative = complex_rows.imag/h
                first = derivative.copy() if first is None else first
                err, stability = errors(derivative, analytic[6:126]), errors(derivative, first)
                steps.append(dict(h=h, derivative=derivative.tolist(), errors=err.tolist(),
                                  stability=stability.tolist(),
                                  passed=bool(err.max() <= 1e-9 and stability.max() <= 1e-10)))
            report["directions"].append(dict(seed=seed, analytic=analytic.tolist(), steps=steps))
            print(seed, max(max(s["errors"]) for s in steps), flush=True)
        checks["complex_directions"] = all(s["passed"] for d in report["directions"]
                                           for s in d["steps"])
        arrays = args.raw / "start_derivatives.npz"
        with arrays.open("xb") as stream:
            np.savez_compressed(stream, x=x, values=values, jacobian=jacobian,
                                directions=directions, coefficients=coefficients,
                                dcoefficients=dcoefficients, anchors=anchors, real=real,
                                native_positions=native_positions, scale=prep["thresholds"]["a0"])
        report.update(status="completed", preparation=prep, source_indices_in_target_order=
                      permutation.tolist(), owner_map=owners, arrays=reference(arrays),
                      checks={k: bool(v) for k, v in checks.items()},
                      all_pass=bool(all(checks.values())),
                      initial_replay_error=replay_error, derivative_replay_error=derivative_replay,
                      position_error=position_error, real_errors=real_error.tolist(),
                      original_nonpair_maximum_error=nonpair_max, work=backend.work,
                      extra_work=dict(native_position_requests=16, pair_value_evaluations=7,
                                      squared_distance_samples=33600000))
    except Exception as error:
        report.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
