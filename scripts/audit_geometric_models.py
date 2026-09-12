"""Reconstruct six LP inputs and verify stored primal-dual witnesses without solving."""

import argparse
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from geometric_descent_inputs import closed_sources, source_arrays
from run_jac_scaled_study import require_committed

from fusion_baselines.box_lp_certificate import certificate
from fusion_baselines.current_diagnostic_audit import error
from fusion_baselines.geometric_box_model import OPTIONS, RADII
from fusion_baselines.provenance import git_state, write_json_atomic

CODE = (
    "scripts/audit_geometric_models.py",
    "scripts/geometric_descent_inputs.py",
    "scripts/current_diagnostic_inputs.py",
    "src/fusion_baselines/box_lp_certificate.py",
    "src/fusion_baselines/current_diagnostic_audit.py",
    "src/fusion_baselines/geometric_box_model.py",
    "src/fusion_baselines/serialized_current_affine.py",
    "src/fusion_baselines/serialized_dofs.py",
)


def audit_case(row, source):
    if (
        row["status"] != "completed"
        or row["source"] != source
        or [m["radius"] for m in row["models"]] != list(RADII)
    ):
        raise ValueError("exact completed two-source/three-radius model matrix required")
    original = source_arrays(source)
    geometry = original["geometry"]
    norm = float(np.linalg.norm(original["jacobian"][0, geometry]))
    records = []
    for model in row["models"]:
        with np.load(checked(model["arrays"]), allow_pickle=False) as archive:
            data = {k: archive[k] for k in archive.files}
        if not all(np.isfinite(v).all() for v in data.values()):
            raise ValueError("finite stored model arrays required")
        checks = {
            f"source_{key}": np.array_equal(data[key], value) for key, value in original.items()
        }
        checks["gradient_norm"] = model["gradient_norm"] == norm
        if norm == 0:
            checks["zero_gradient"] = (
                model["status"] == "zero_gradient"
                and model["all_pass"] is False
                and "solver" not in model
            )
            records.append(
                dict(checks=checks, all_pass=all(checks.values()), model_qualified=False)
            )
            continue
        c = original["jacobian"][0, geometry] / norm
        a = -original["jacobian"][1:, geometry]
        b = original["values"][1:] / model["radius"]
        checks["model_arrays"] = all(
            np.array_equal(data[k], v) for k, v in (("c", c), ("A", a), ("b", b))
        )
        solver = model["solver"]
        checks["solver_options"] = solver["method"] == "highs-ds" and solver["options"] == OPTIONS
        if not solver["success"] or solver["status"] != 0:
            checks["negative_status"] = (
                model["status"] == "solver_returned" and model["all_pass"] is False
            )
            records.append(
                dict(
                    checks=checks,
                    all_pass=all(checks.values()),
                    model_qualified=False,
                    no_infeasibility_proof_claimed=True,
                )
            )
            continue
        proof = certificate(
            c,
            a,
            b,
            solver["s"],
            solver["inequality_marginals"],
            solver["lower_marginals"],
            solver["upper_marginals"],
        )
        checks["reported_certificate"] = proof == model["certificate"]
        checks["solver_objective"] = error(proof["primal_objective"], solver["objective"]) <= 1e-12
        checks["solver_slacks"] = error(b - a @ solver["s"], solver["slack"]) <= 1e-12
        step = np.zeros(207)
        step[geometry] = model["radius"] * np.asarray(solver["s"])
        length = float(np.linalg.norm(step))
        checks["step"] = np.array_equal(step, data["step"])
        checks["step_norm"] = length == model["step_norm"]
        checks["unchanged_currents"] = np.all(data["step"][original["currents"]] == 0)
        checks["predicted_values"] = np.array_equal(
            original["values"] + original["jacobian"] @ step, data["predicted_values"]
        )
        checks["predicted_flux_change"] = (
            error(float(original["jacobian"][0] @ step * 1e-6), model["predicted_flux_change"])
            <= 1e-12
        )
        checks["direction"] = (
            np.array_equal(data["direction"], step / length)
            if length > 0
            else "direction" not in data
        )
        checks["classification"] = (
            model["status"] == "completed" and model["all_pass"] == proof["all_pass"]
        )
        checks = {k: bool(v) for k, v in checks.items()}
        records.append(
            dict(
                checks=checks,
                all_pass=all(checks.values()),
                model_qualified=proof["all_pass"],
                certificate=proof,
            )
        )
    checks = dict(
        models=all(r["all_pass"] for r in records),
        classification=row["all_pass"] == all(r["model_qualified"] for r in records),
    )
    return dict(checks=checks, models=records, all_pass=all(checks.values()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable geometric model audit required")
    root = Path(__file__).resolve().parents[1]
    for name in CODE:
        require_committed(root, root / name)
    study = json.loads(args.study.read_text())
    result = dict(
        repository=git_state(root),
        source=reference(args.study),
        code=[reference(root / p) for p in CODE],
        status="running",
        all_pass=False,
        cases=[],
        new_LP_calls=0,
        new_native_calls=0,
        physical_admission=False,
    )
    try:
        selected, bindings = closed_sources(root)
        if (
            study["status"] != "completed"
            or not study["all_six_models_recorded"]
            or study["prerequisites"] != bindings
            or len(study["cases"]) != 2
        ):
            raise ValueError("complete bound six-model study required")
        for ref in [study["protocol"], *study["code"], *study["environment"]["installed_sources"]]:
            checked(ref)
        for row, source in zip(study["cases"], selected, strict=True):
            result["cases"].append(audit_case(row, source))
        models = [m for r in study["cases"] for m in r["models"]]
        checks = dict(
            cases=all(r["all_pass"] for r in result["cases"]),
            work=study["native_calls"] == 0
            and study["LP_calls"] == sum("solver" in m for m in models)
            and study["independent_certificate_checks"] == sum("certificate" in m for m in models),
            classification=study["all_pass"] == all(r["all_pass"] for r in study["cases"]),
            no_physical_admission=study["physical_admission"] is False,
        )
        result.update(status="completed", checks=checks, all_pass=all(checks.values()))
    except Exception as exc:
        result.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.output, result)
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
