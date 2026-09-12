"""Independent serialized Fourier/real-chain-rule audit of native geometric probes."""

import argparse
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from geometric_descent_inputs import closed_sources, source_arrays
from run_jac_scaled_study import require_committed

from fusion_baselines.clearance_chain_rule import chain_rule_rows, loop_positions
from fusion_baselines.coil_coefficient_view import base_arrays, serialized_physical_coefficients
from fusion_baselines.current_diagnostic_audit import error
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state

CODE = (
    "scripts/audit_geometric_probes.py",
    "scripts/geometric_descent_inputs.py",
    "scripts/current_diagnostic_inputs.py",
    "src/fusion_baselines/clearance_chain_rule.py",
    "src/fusion_baselines/coil_coefficient_view.py",
    "src/fusion_baselines/current_diagnostic_audit.py",
    "src/fusion_baselines/selected_start.py",
    "src/fusion_baselines/serialized_dofs.py",
    "src/fusion_baselines/serialized_field_state.py",
)


def arrays(ref):
    with np.load(checked(ref), allow_pickle=False) as archive:
        data = {k: archive[k] for k in archive.files}
    if not all(np.isfinite(v).all() for v in data.values()):
        raise ValueError("finite geometric probe arrays required")
    return data


def expected_work(n):
    single = dict(
        evaluations=1,
        jacobian_evaluations=1,
        B_grid_requests=1,
        B_vjp_requests=1,
        position_requests=16,
        position_derivative_requests=16,
        curvature_requests=4,
        curvature_derivative_requests=4,
        native_metric_requests=12,
        native_gradient_requests=12,
        coil_pair_samples=4800000,
        plasma_pair_samples=3276800,
    )
    return {k: n * v for k, v in single.items()}


def audit_case(row, source, model_case):
    if (
        row["status"] != "completed"
        or row["source"] != source
        or [d["radius"] for d in row["directions"]] != [1e-6, 1e-5, 1e-4]
    ):
        raise ValueError("complete ordered three-direction source case required")
    original = source_arrays(source)
    doc = json.loads(checked(source["field"]).read_text())
    template = json.loads(checked(row["preparation"]["normalized_start"]).read_text())
    x, permutation, owners = mapped_start(
        doc, template, source["names"], row["names"], original["x"]
    )
    initial = arrays(row["initial"])
    v, jac = initial["values"], initial["jacobian"]
    geom = arrays(row["geometry"])
    pos = arrays(row["position_arrays"])
    coefficients = serialized_physical_coefficients(
        doc, base_arrays(doc, source["names"], original["x"])
    )
    checks = dict(
        named_source=np.array_equal(x, initial["x"]),
        source_values=error(v, original["values"]) <= 1e-12,
        source_jacobian=error(jac, original["jacobian"][:, permutation]) <= 1e-12,
        permutation=row["source_indices_in_target_order"] == permutation.tolist(),
        owner_map=row["owner_map"] == owners,
        explicit_names=row["names"] == row["preparation"]["degrees_of_freedom"],
        unchanged_problem=all(
            row["preparation"][k] == source["preparation"][k]
            for k in ("surface", "case", "thresholds", "guarded_search_targets", "canonical_total")
        ),
        physical_coefficients=error(coefficients, geom["coefficients"]) <= 1e-14,
        positions=error(loop_positions(coefficients), geom["native_positions"]) <= 1e-12,
        position_checkpoint=all(np.array_equal(pos[k], geom[k]) for k in pos),
    )
    records, directions, dcoefficients = [], [], []
    for direction, model in zip(row["directions"], model_case["models"], strict=True):
        data, lp = arrays(direction["arrays"]), arrays(checked_ref := direction["model_arrays"])
        if checked_ref != model["arrays"]:
            raise ValueError("exact frozen LP witness required")
        source_direction = lp["direction"]
        dc = serialized_physical_coefficients(
            doc, base_arrays(doc, source["names"], source_direction, direction=True)
        )
        directions.append((direction, data, lp))
        dcoefficients.append(dc)
    own_values, real_derivatives, anchors = chain_rule_rows(
        coefficients, dcoefficients, source["preparation"]["thresholds"]["a0"]
    )
    checks["real_pair_values"] = (
        error(own_values, v[6:126]) <= 1e-10 and error(own_values, geom["real"]) <= 1e-10
    )
    checks["anchors"] = error(anchors, geom["anchors"]) <= 1e-12
    expected_events = [("source", x, row["initial"])]
    for i, (direction, data, lp) in enumerate(directions):
        p, step = lp["direction"][permutation], lp["step"][permutation]
        stored_input = arrays(direction["input_arrays"])
        tests = dict(
            step=np.array_equal(step, data["step"]),
            direction=np.array_equal(p, data["direction"]),
            frozen_currents=np.all(lp["step"][original["currents"]] == 0),
            coefficient_direction=error(dcoefficients[i], data["dcoefficients"]) <= 1e-14,
            input_checkpoint=all(np.array_equal(stored_input[k], data[k]) for k in stored_input),
        )
        exact = jac @ p
        tests["analytic"] = np.array_equal(exact, direction["gate"]["analytic"])
        fd_passes = []
        for j, eps in enumerate((1e-7, 1e-8)):
            refs = direction["finite_difference_bundles"][j]
            pair = []
            for k, sign in enumerate((1, -1)):
                bundle = arrays(refs[k])
                tests[f"fd_{j}_{k}_point"] = np.array_equal(bundle["x"], x + sign * eps * p)
                tests[f"fd_{j}_{k}_values"] = np.array_equal(
                    bundle["values"], data["fd_values"][j, k]
                )
                pair.append(bundle["values"])
                expected_events.append(
                    (f"direction-{i}-eps-{eps}-sign-{sign}", x + sign * eps * p, refs[k])
                )
            estimate = (pair[0] - pair[1]) / (2 * eps)
            err = abs(estimate - exact) / np.maximum(1, abs(exact))
            maximum = float(np.r_[err[:6], err[126:]].max())
            passed = maximum <= 1e-6
            saved = direction["gate"]["finite_differences"][j]
            tests[f"fd_{j}_arithmetic"] = (
                saved["eps"] == eps
                and np.array_equal(estimate, saved["finite_difference"])
                and np.array_equal(err, saved["errors"])
                and saved["maximum_nonpair_error"] == maximum
                and saved["passed"] == passed
            )
            fd_passes.append(passed)
        pair_passes = []
        for j, h in enumerate((1e-12, 1e-20)):
            complex_row = direction["complex_evaluations"][j]
            saved_complex = arrays(complex_row["arrays"])["value"]
            computed = data["complex_derivatives"][j]
            tests[f"complex_{j}_checkpoint"] = (
                complex_row["h"] == h
                and complex_row["status"] == "completed"
                and np.array_equal(saved_complex.imag / h, computed)
            )
            err = abs(computed - exact[6:126]) / np.maximum(1, abs(exact[6:126]))
            stability = abs(computed - data["complex_derivatives"][0]) / np.maximum(
                1, abs(data["complex_derivatives"][0])
            )
            passed = bool(err.max() <= 1e-9 and stability.max() <= 1e-10)
            saved = direction["gate"]["complex_pairs"][j]
            tests[f"complex_{j}_arithmetic"] = (
                saved["h"] == h
                and np.array_equal(computed, saved["derivative"])
                and np.array_equal(err, saved["errors"])
                and np.array_equal(stability, saved["stability"])
                and saved["passed"] == passed
            )
            tests[f"independent_complex_{j}"] = error(real_derivatives[i], computed) <= 1e-9
            pair_passes.append(passed)
        tests["independent_native_pairs"] = error(real_derivatives[i], exact[6:126]) <= 1e-9
        gate = all(fd_passes + pair_passes)
        tests["gate"] = (
            direction["gate"]["all_pass"] == gate and direction["trial_evaluated"] == gate
        )
        if gate:
            trial = arrays(direction["trial_bundle"])
            after = trial["values"]
            expected_events.append((f"direction-{i}-trial", x + step, direction["trial_bundle"]))
            tests["trial_point"] = np.array_equal(trial["x"], x + step)
            after_doc = json.loads(checked(direction["field"]).read_text())
            named = np.array_equal(named_serialized_values(after_doc, row["names"]), x + step)
            currents = (
                error(serialized_state(after_doc)["currents"], serialized_state(doc)["currents"])
                <= 1e-12
            )
            tests["serialized_trial"] = named and currents
            source_after = original["x"] + lp["step"]
            expected_physical = serialized_physical_coefficients(
                doc, base_arrays(doc, source["names"], source_after)
            )
            saved_physical = serialized_physical_coefficients(
                after_doc, base_arrays(after_doc, row["names"], x + step)
            )
            tests["all_physical_trial_copies"] = error(expected_physical, saved_physical) <= 1e-14
            before_objects, after_objects = doc["simsopt_objs"], after_doc["simsopt_objs"]
            old_coils = before_objects[doc["graph"]["value"]]["coils"]
            new_coils = after_objects[after_doc["graph"]["value"]]["coils"]
            tests["all_trial_regularizations"] = [
                before_objects[c["value"]]["regularization"] for c in old_coils
            ] == [after_objects[c["value"]]["regularization"] for c in new_coils]
            tests["serialized_flags"] = direction["serialization"] == dict(
                named_point=named, unchanged_currents=currents
            )
            pred = v + jac @ step
            pred_change, change = float(jac[0] @ step * 1e-6), float((after[0] - v[0]) * 1e-6)
            violation = max(0.0, -float(after[1:].min()))
            metrics = dict(
                predicted_flux_change=pred_change,
                actual_flux_change=change,
                actual_to_predicted_change=change / pred_change if pred_change != 0 else None,
                raw_flux=float(after[0] * 1e-6),
                flux_improves=change < 0,
                maximum_geometric_violation=violation,
                construction_screen_pass=violation <= 1e-8,
                geometric_linearization_errors=(
                    abs(after[1:] - pred[1:]) / np.maximum(1, abs(pred[1:]))
                ).tolist(),
                physical_admission=False,
            )
            tests["trial_arithmetic"] = metrics == direction["trial"]
        tests["classification"] = (
            direction["status"] == "completed" and direction["all_pass"] == gate
        )
        tests = {k: bool(v) for k, v in tests.items()}
        records.append(
            dict(
                checks=tests,
                all_pass=all(tests.values()),
                derivative_qualified=gate,
                independent_pair_error=error(real_derivatives[i], exact[6:126]),
            )
        )
    if len(expected_events) != len(row["evaluations"]):
        raise ValueError("complete source/FD/trial event sequence required")
    for i, ((kind, point, ref), event) in enumerate(
        zip(expected_events, row["evaluations"], strict=True)
    ):
        data = arrays(event["arrays"])
        checks[f"event_{i}"] = (
            event["index"] == i
            and event["kind"] == kind
            and event["status"] == "completed"
            and event["arrays"] == ref
            and np.array_equal(event["x"], point)
            and np.array_equal(data["x"], point)
            and data["values"].shape == (138,)
            and data["jacobian"].shape == (138, 207)
        )
    checks["work"] = row["work"] == expected_work(len(expected_events)) and row[
        "extra_work"
    ] == dict(native_position_requests=16, real_pair_calls=1, complex_pair_calls=6)
    checks["reported_source"] = row["checks"] == dict(
        values_replay=checks["source_values"],
        jacobian_replay=checks["source_jacobian"],
        positions=checks["positions"],
        real_pair_values=checks["real_pair_values"],
    )
    checks["directions"] = all(r["all_pass"] for r in records)
    checks["classification"] = row["all_pass"] == (
        all(row["checks"].values()) and all(r["derivative_qualified"] for r in records)
    )
    checks = {k: bool(v) for k, v in checks.items()}
    return dict(
        checks=checks,
        directions=records,
        all_pass=all(checks.values()),
        native_bundles=len(expected_events),
        independent_pair_value_error=error(own_values, v[6:126]),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable geometric probe audit required")
    root = Path(__file__).resolve().parents[1]
    for name in CODE:
        require_committed(root, root / name)
    study = json.loads(args.study.read_text())
    report = dict(
        repository=git_state(root),
        source=reference(args.study),
        code=[reference(root / p) for p in CODE],
        status="running",
        all_pass=False,
        cases=[],
        new_native_calls=0,
        new_LP_calls=0,
        new_complex_calls=0,
        independent_real_pair_calls=0,
        physical_admission=False,
    )
    try:
        models, audit = (
            json.loads(checked(study[key]).read_text()) for key in ("models", "model_audit")
        )
        selected, bindings = closed_sources(root)
        if (
            study["status"] != "completed"
            or len(study["cases"]) != 2
            or models["status"] != "completed"
            or audit["status"] != "completed"
            or study["physical_admission"] is not False
            or not models["all_pass"]
            or not audit["all_pass"]
            or audit["source"] != study["models"]
            or models["prerequisites"] != bindings
        ):
            raise ValueError("completed bound native probe/model matrix required")
        for ref in [study["protocol"], *study["code"], *models["code"], *audit["code"]]:
            checked(ref)
        for row, source, model in zip(study["cases"], selected, models["cases"], strict=True):
            report["independent_real_pair_calls"] += 1
            report["cases"].append(audit_case(row, source, model))
            write_json_atomic(args.output, report)
        report.update(
            status="completed",
            all_pass=all(r["all_pass"] for r in report["cases"]),
            original_qualification=study["all_pass"],
        )
        if study["all_pass"] != all(r["all_pass"] for r in study["cases"]):
            report["all_pass"] = False
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
