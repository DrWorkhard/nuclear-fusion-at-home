"""Independent complex-step check of all pair rows at two frozen direct states."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from simsopt import load

from fusion_baselines.complex_clearance import clearance_rows
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.serialized_dofs import base_coil_owners


def reference(path):
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError(f"hash mismatch: {path}")
    return path


def errors(actual, expected):
    return np.abs(np.asarray(actual) - expected) / np.maximum(1.0, np.abs(expected))


def physical_coefficients(field, base_coefficients):
    bases = [c.curve for c in field.coils[:4]]
    result = []
    for coil in field.coils:
        curve, rotations = coil.curve, []
        while hasattr(curve, "rotmat"):
            rotation = np.asarray(curve.rotmat)
            if not np.allclose(rotation.T @ rotation, np.eye(3), rtol=0, atol=1e-12):
                raise ValueError("nonorthogonal copy transform")
            rotations.append(rotation)
            curve = curve.curve
        indices = [i for i, base in enumerate(bases) if base is curve]
        if len(indices) != 1:
            raise ValueError("ambiguous physical base curve")
        coefficients = base_coefficients[indices[0]].copy()
        for rotation in reversed(rotations):
            coefficients = (coefficients.T @ rotation).T
        result.append(coefficients)
    if len(result) != 16:
        raise ValueError("sixteen physical curves required")
    return np.asarray(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new complex qualification paths required")
    root = Path(__file__).resolve().parents[1]
    source_path = root / "evidence/direct-descent-diagnostic-v1.json"
    diagnostic = json.loads(source_path.read_text())
    if diagnostic["status"] != "completed" or not diagnostic["checks"]["both_replays"]:
        raise ValueError("complete replay-verified diagnostic required")
    study = json.loads(checked(diagnostic["study"]).read_text())
    arm = json.loads(checked(diagnostic["arm"]).read_text())
    field_path = checked(arm["best"]["field"])
    doc = json.loads(field_path.read_text())
    field = load(str(field_path))  # Only coefficients and copy transforms, no geometry derivatives.
    names = study["preparation"]["degrees_of_freedom"]
    indices = {name: i for i, name in enumerate(names)}
    if len(indices) != len(names):
        raise ValueError("duplicate parameter labels")
    scale = float(study["preparation"]["thresholds"]["a0"])
    inverse = np.argsort(diagnostic["source_indices_in_target_order"])
    templates = []
    for owner, _ in base_coil_owners(doc):
        data = doc["simsopt_objs"][doc["simsopt_objs"][owner]["dofs"]["value"]]
        full_names = [owner + ":" + name for name in data["names"]]
        templates.append(
            (full_names, np.asarray(data["x"]["data"], dtype=float), data["free"]["data"])
        )

    def base_arrays(vector, *, direction=False):
        result = []
        for labels, template, free in templates:
            values = np.zeros_like(template) if direction else template.copy()
            for i, label in enumerate(labels):
                if free[i]:
                    values[i] = vector[indices[label]]
            result.append(values.reshape(3, -1))
        return np.asarray(result)

    result = {
        "schema_version": 1,
        "repository": git_state(root),
        "protocol": reference(root / "docs/optimization/COMPLEX_CLEARANCE_PROTOCOL.md"),
        "diagnostic": reference(source_path),
        "source_field": reference(field_path),
        "code": [
            reference(root / p)
            for p in (
                "scripts/qualify_complex_clearance.py",
                "src/fusion_baselines/complex_clearance.py",
                "src/fusion_baselines/serialized_dofs.py",
            )
        ],
        "states": [],
        "status": "running",
        "all_pass": False,
        "original_all_row_finite_difference_pass": diagnostic["checks"]["selected_gradient"],
        "nonlinear_design_search_performed": False,
        "native_geometry_derivative_calls": 0,
    }
    args.raw.mkdir(parents=True)
    try:
        for state in diagnostic["states"]:
            with np.load(checked(state["arrays"]), allow_pickle=False) as saved:
                x, jacobian = saved["x"][inverse], saved["jacobian"][:, inverse]
                expected = saved["values"][6:126].copy()
            expected_hash = (
                arm["evaluations"][0]["x_sha256"]
                if state["name"] == "original"
                else arm["best"]["x_sha256"]
            )
            if hashlib.sha256(x.tobytes()).hexdigest() != expected_hash:
                raise ValueError("source-order physical parameter identity failed")
            coefficients = physical_coefficients(field, base_arrays(x))
            values, anchors = clearance_rows(coefficients, scale)
            real_error = errors(values, expected)
            current_indices = [i for i, n in enumerate(names) if n.startswith("Current")]
            record = {
                "name": state["name"],
                "source_arrays": state["arrays"],
                "real_value_errors": real_error.tolist(),
                "directions": [],
                "checks": {
                    "real_value_agreement": bool(real_error.max() <= 1e-10),
                    "zero_current_columns": bool(np.all(jacobian[6:126, current_indices] == 0)),
                },
            }
            saved_directions = []
            for seed in (47, 48):
                direction = np.random.default_rng(seed).normal(size=len(x))
                direction /= np.linalg.norm(direction)
                dcoeff = physical_coefficients(field, base_arrays(direction, direction=True))
                saved_directions.append(dcoeff)
                analytic = jacobian[6:126] @ direction
                steps, first = [], None
                for h in (1e-12, 1e-20, 1e-28):
                    complex_values, _ = clearance_rows(
                        coefficients + 1j * h * dcoeff, scale, anchors=anchors
                    )
                    measured = np.imag(complex_values) / h
                    first = measured.copy() if first is None else first
                    error, stability = errors(measured, analytic), errors(measured, first)
                    steps.append(
                        {
                            "h": h,
                            "directional_derivative": measured.tolist(),
                            "normalized_errors": error.tolist(),
                            "maximum_error": float(error.max()),
                            "maximum_step_disagreement": float(stability.max()),
                        }
                    )
                    print(state["name"], seed, h, float(error.max()), flush=True)
                passed = all(
                    s["maximum_error"] <= 1e-9 and s["maximum_step_disagreement"] <= 1e-10
                    for s in steps
                )
                record["directions"].append(
                    {"seed": seed, "steps": steps, "pass": passed, "analytic": analytic.tolist()}
                )
            record["checks"]["all_complex_steps"] = all(d["pass"] for d in record["directions"])
            path = args.raw / f"{state['name']}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(
                    stream,
                    coefficients=coefficients,
                    directions=saved_directions,
                    values=values,
                    anchors=anchors,
                    scale=scale,
                )
            record.update(arrays=reference(path), all_pass=all(record["checks"].values()))
            result["states"].append(record)
            write_json_atomic(args.output, result)
        fd = np.asarray(diagnostic["selected_directional_checks"][-1]["normalized_errors"])
        nonpair = np.r_[fd[:6], fd[126:]]
        result["selected_nonpair_original_fd_maximum_error"] = float(nonpair.max())
        result["selected_nonpair_original_fd_pass"] = bool(nonpair.max() <= 1e-6)
        result.update(
            status="completed",
            all_pass=len(result["states"]) == 2
            and all(s["all_pass"] for s in result["states"])
            and result["selected_nonpair_original_fd_pass"],
            work={
                "pair_value_evaluations": 14,
                "pair_sample_sets": 14 * 120,
                "squared_distance_samples": 14 * 120 * 200 * 200,
            },
        )
    except Exception as error:
        result.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, result)
    print(json.dumps({"all_pass": result["all_pass"]}))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
