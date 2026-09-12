"""Six fixed-radius LPs from frozen arrays; no new native coil evaluation."""

import argparse
import importlib
import importlib.metadata
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import reference
from geometric_descent_inputs import closed_sources, source_arrays
from run_jac_scaled_study import require_committed

from fusion_baselines.box_lp_certificate import certificate
from fusion_baselines.geometric_box_model import RADII, box_model, solve_model
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check

CODE = (
    "scripts/solve_geometric_models.py",
    "scripts/geometric_descent_inputs.py",
    "scripts/current_diagnostic_inputs.py",
    "src/fusion_baselines/geometric_box_model.py",
    "src/fusion_baselines/box_lp_certificate.py",
    "src/fusion_baselines/serialized_current_affine.py",
    "src/fusion_baselines/serialized_dofs.py",
)


def environment():
    return dict(
        versions={p: importlib.metadata.version(p) for p in ("numpy", "scipy")},
        installed_sources=[
            reference(Path(importlib.import_module(p).__file__))
            for p in ("scipy.optimize._linprog", "scipy.optimize._linprog_highs")
        ],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable geometric model paths required")
    root = Path(__file__).resolve().parents[1]
    selected, bindings = closed_sources(root)
    protocol = root / "docs/optimization/GEOMETRIC_DESCENT_PROTOCOL.md"
    for path in [protocol, *(root / p for p in CODE)]:
        require_committed(root, path)
    report = dict(
        repository=git_state(root),
        protocol=reference(protocol),
        code=[reference(root / p) for p in CODE],
        prerequisites=bindings,
        environment=environment(),
        status="running",
        all_pass=False,
        cases=[],
        native_calls=0,
        LP_calls=0,
        independent_certificate_checks=0,
        physical_admission=False,
        disk_preflight=space_check(root, 3 * GIB),
    )
    args.raw.mkdir(parents=True)
    active, active_arrays = None, None
    try:
        for source in selected:
            arrays = source_arrays(source)
            geom = arrays["geometry"]
            row = dict(source=source, status="running", models=[], all_pass=False)
            report["cases"].append(row)
            for i, radius in enumerate(RADII):
                space_check(root, 2 * GIB)
                active = dict(radius=radius, status="preparing", all_pass=False)
                row["models"].append(active)
                path = args.raw / f"{source['label']}-radius-{i}.npz"
                active_arrays = (path, dict(arrays))
                write_json_atomic(args.output, report)
                model = box_model(
                    arrays["jacobian"][0, geom],
                    arrays["values"][1:],
                    arrays["jacobian"][1:, geom],
                    radius,
                )
                active["gradient_norm"] = model["gradient_norm"]
                if model["status"] == "zero_gradient":
                    active.update(status="zero_gradient", all_pass=False)
                else:
                    active_arrays[1].update(c=model["c"], A=model["A"], b=model["b"])
                    report["LP_calls"] += 1
                    solution = solve_model(model)
                    active["solver"] = {
                        k: v.tolist() if isinstance(v, np.ndarray) else v
                        for k, v in solution.items()
                    }
                    active["status"] = "solver_returned"
                    if solution["success"] and solution["status"] == 0:
                        report["independent_certificate_checks"] += 1
                        proof = certificate(
                            model["c"],
                            model["A"],
                            model["b"],
                            solution["s"],
                            solution["inequality_marginals"],
                            solution["lower_marginals"],
                            solution["upper_marginals"],
                        )
                        d = np.zeros(207)
                        d[geom] = radius * solution["s"]
                        length = float(np.linalg.norm(d))
                        active_arrays[1].update(
                            step=d, predicted_values=arrays["values"] + arrays["jacobian"] @ d
                        )
                        if length > 0:
                            active_arrays[1]["direction"] = d / length
                        active.update(
                            certificate=proof,
                            all_pass=proof["all_pass"],
                            step_norm=length,
                            status="completed",
                            predicted_flux_change=float(arrays["jacobian"][0] @ d * 1e-6),
                        )
                with path.open("xb") as stream:
                    np.savez_compressed(stream, **active_arrays[1])
                active["arrays"] = reference(path)
                write_json_atomic(args.output, report)
                print(source["label"], radius, active["status"], active["all_pass"], flush=True)
            row.update(status="completed", all_pass=all(m["all_pass"] for m in row["models"]))
        report.update(
            status="completed",
            all_six_models_recorded=True,
            all_pass=all(r["all_pass"] for r in report["cases"]),
        )
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        if active is not None:
            active.update(status="error", error=report["error"], all_pass=False)
        if active_arrays is not None:
            path, arrays = active_arrays
            if not path.exists():
                with path.open("xb") as stream:
                    np.savez_compressed(stream, **arrays)
                active["arrays"] = reference(path)
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
