"""Registered native source, derivative and single-trial checks for six frozen LPs."""

import argparse
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, reference
from geometric_descent_inputs import closed_sources, source_arrays
from qualify_fixed_currents import native_setup, versions
from run_jac_scaled_study import require_committed

from fusion_baselines.coil_coefficient_view import base_arrays
from fusion_baselines.complex_clearance import clearance_rows, fourier_positions
from fusion_baselines.direct_constraints import DirectConstraintBackend
from fusion_baselines.geometric_box_model import RADII
from fusion_baselines.geometric_direction_checks import (
    COMPLEX_STEPS,
    EPS,
    direction_gate,
    errors,
    trial_metrics,
)
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state

CODE = (
    "scripts/probe_geometric_descent.py",
    "scripts/geometric_descent_inputs.py",
    "scripts/current_diagnostic_inputs.py",
    "scripts/qualify_fixed_currents.py",
    "scripts/prepare_upstream_start.py",
    "scripts/qualify_complex_clearance.py",
    "src/fusion_baselines/direct_constraints.py",
    "src/fusion_baselines/geometric_direction_checks.py",
    "src/fusion_baselines/complex_clearance.py",
    "src/fusion_baselines/coil_coefficient_view.py",
    "src/fusion_baselines/selected_start.py",
    "src/fusion_baselines/serialized_dofs.py",
    "src/fusion_baselines/serialized_field_state.py",
)


def native_coefficients(field, bases):
    from qualify_complex_clearance import physical_coefficients

    return physical_coefficients(field, bases)


def save(path, arrays):
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    return reference(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", type=Path)
    parser.add_argument("audit", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable native geometric diagnosis paths required")
    root = Path(__file__).resolve().parents[1]
    models, audit = json.loads(args.models.read_text()), json.loads(args.audit.read_text())
    selected, bindings = closed_sources(root)
    if (
        models["status"] != "completed"
        or not models["all_pass"]
        or len(models["cases"]) != 2
        or audit["status"] != "completed"
        or not audit["all_pass"]
        or audit["source"] != reference(args.models)
        or models["prerequisites"] != bindings
        or [r["source"] for r in models["cases"]] != selected
    ):
        raise ValueError("completed independently audited six-model source required")
    for ref in [
        models["protocol"],
        *models["code"],
        *audit["code"],
        *models["environment"]["installed_sources"],
    ]:
        checked(ref)
    for path in [args.models, args.audit, *(root / p for p in CODE)]:
        require_committed(root, path)
    report = dict(
        repository=git_state(root),
        models=reference(args.models),
        model_audit=reference(args.audit),
        protocol=models["protocol"],
        code=[reference(root / p) for p in CODE],
        versions=versions(),
        status="running",
        all_pass=False,
        cases=[],
        physical_admission=False,
        disk_preflight=space_check(root, 3 * GIB),
    )
    args.raw.mkdir(parents=True)
    active_row = active_event = backend = None
    try:
        for model_case, source in zip(models["cases"], selected, strict=True):
            space_check(root, 2 * GIB)
            raw = args.raw / source["label"]
            raw.mkdir()
            row = dict(
                source=source,
                status="preparing",
                all_pass=False,
                directions=[],
                evaluations=[],
                extra_work=dict(
                    native_position_requests=0, real_pair_calls=0, complex_pair_calls=0
                ),
            )
            active_row, backend = row, None
            report["cases"].append(row)
            write_json_atomic(args.output, report)
            original = source_arrays(source)
            doc = json.loads(checked(source["field"]).read_text())
            ctx, prep, full = native_setup(root, raw)
            template = json.loads(checked(prep["normalized_start"]).read_text())
            if any(
                prep[k] != source["preparation"][k]
                for k in (
                    "surface",
                    "case",
                    "thresholds",
                    "guarded_search_targets",
                    "canonical_total",
                )
            ):
                raise ValueError("canonical geometry diagnostic problem changed")
            x, permutation, owners = mapped_start(
                doc, template, source["names"], prep["degrees_of_freedom"], original["x"]
            )
            backend = DirectConstraintBackend(ctx, full)
            row.update(
                preparation=prep,
                names=backend.names,
                source_indices_in_target_order=permutation.tolist(),
                owner_map=owners,
            )

            def evaluate(point, kind, backend=backend, row=row, raw=raw):
                nonlocal active_event
                event = dict(
                    index=len(row["evaluations"]), kind=kind, status="running", x=point.tolist()
                )
                active_event = event
                row["evaluations"].append(event)
                write_json_atomic(args.output, report)
                values, jac, _ = backend.evaluate(point)
                event.update(
                    status="completed",
                    arrays=save(
                        raw / f"bundle-{event['index']}.npz",
                        dict(x=point, values=values, jacobian=jac),
                    ),
                )
                row["work"] = backend.work.copy()
                write_json_atomic(args.output, report)
                return values, jac, event["arrays"]

            values, jac, initial = evaluate(x, "source")
            checks = dict(
                values_replay=float(errors(values, original["values"]).max()) <= 1e-12,
                jacobian_replay=float(errors(jac, original["jacobian"][:, permutation]).max())
                <= 1e-12,
            )
            coefficients = native_coefficients(
                backend.field, base_arrays(template, backend.names, x)
            )
            row["partial_native_positions"] = []
            for coil in backend.field.coils:
                row["extra_work"]["native_position_requests"] += 1
                write_json_atomic(args.output, report)
                row["partial_native_positions"].append(coil.curve.gamma().copy().tolist())
                write_json_atomic(args.output, report)
            positions = np.asarray(row["partial_native_positions"])
            row["position_arrays"] = save(
                raw / "positions.npz", dict(coefficients=coefficients, native_positions=positions)
            )
            del row["partial_native_positions"]
            write_json_atomic(args.output, report)
            row["extra_work"]["real_pair_calls"] += 1
            real, anchors = clearance_rows(coefficients, prep["thresholds"]["a0"])
            checks.update(
                positions=float(errors(fourier_positions(coefficients, 200), positions).max())
                <= 1e-12,
                real_pair_values=float(errors(real, values[6:126]).max()) <= 1e-10,
            )
            row.update(
                initial=initial,
                checks=checks,
                geometry=save(
                    raw / "geometry.npz",
                    dict(
                        coefficients=coefficients,
                        native_positions=positions,
                        real=real,
                        anchors=anchors,
                    ),
                ),
            )
            if not all(checks.values()):
                raise ValueError("native source replay or independent pair geometry gate failed")
            if [m["radius"] for m in model_case["models"]] != list(RADII):
                raise ValueError("all three unchanged ordered radii required")
            for i, model in enumerate(model_case["models"]):
                direction_row = dict(
                    radius=model["radius"],
                    model_arrays=model["arrays"],
                    status="preparing",
                    all_pass=False,
                    trial_evaluated=False,
                )
                row["directions"].append(direction_row)
                with np.load(checked(model["arrays"]), allow_pickle=False) as data:
                    step = data["step"][permutation].copy()
                    if model["step_norm"] == 0:
                        direction_row.update(status="zero_step", all_pass=False)
                        continue
                    direction = data["direction"][permutation].copy()
                dcoefficients = native_coefficients(
                    backend.field, base_arrays(template, backend.names, direction, direction=True)
                )
                direction_row["input_arrays"] = save(
                    raw / f"direction-{i}-input.npz",
                    dict(step=step, direction=direction, dcoefficients=dcoefficients),
                )
                direction_row["complex_evaluations"] = []
                write_json_atomic(args.output, report)
                fd, refs = [], []
                for eps in EPS:
                    pair, pair_refs = [], []
                    for sign in (1, -1):
                        value, _jac, ref = evaluate(
                            x + sign * eps * direction, f"direction-{i}-eps-{eps}-sign-{sign}"
                        )
                        pair.append(value)
                        pair_refs.append(ref)
                    fd.append(pair)
                    refs.append(pair_refs)
                complex_derivatives = []
                for h in COMPLEX_STEPS:
                    row["extra_work"]["complex_pair_calls"] += 1
                    complex_row = dict(h=h, status="running")
                    direction_row["complex_evaluations"].append(complex_row)
                    write_json_atomic(args.output, report)
                    value, _ = clearance_rows(
                        coefficients + 1j * h * dcoefficients,
                        prep["thresholds"]["a0"],
                        anchors=anchors,
                    )
                    complex_derivatives.append(value.imag / h)
                    complex_row.update(
                        status="completed",
                        arrays=save(raw / f"direction-{i}-complex-{h}.npz", dict(value=value)),
                    )
                    write_json_atomic(args.output, report)
                gate = direction_gate(jac, direction, fd, complex_derivatives)
                direction_row.update(
                    gate=gate,
                    finite_difference_bundles=refs,
                    arrays=save(
                        raw / f"direction-{i}.npz",
                        dict(
                            step=step,
                            direction=direction,
                            dcoefficients=dcoefficients,
                            fd_values=fd,
                            complex_derivatives=complex_derivatives,
                        ),
                    ),
                )
                if gate["all_pass"]:
                    after_x = x + step
                    after_values, _after_jac, trial_ref = evaluate(after_x, f"direction-{i}-trial")
                    field = raw / f"trial-{i}.json"
                    ctx.Jf.field.save(str(field))
                    after_doc = json.loads(field.read_text())
                    current_error = float(
                        errors(
                            serialized_state(after_doc)["currents"],
                            serialized_state(doc)["currents"],
                        ).max()
                    )
                    serialization = dict(
                        named_point=np.array_equal(
                            named_serialized_values(after_doc, backend.names), after_x
                        ),
                        unchanged_currents=current_error <= 1e-12,
                    )
                    direction_row.update(
                        trial_evaluated=True,
                        trial_bundle=trial_ref,
                        field=reference(field),
                        serialization=serialization,
                        trial=trial_metrics(values, jac, step, after_values),
                    )
                direction_row.update(
                    status="completed",
                    all_pass=gate["all_pass"]
                    and (
                        not direction_row["trial_evaluated"]
                        or all(direction_row["serialization"].values())
                    ),
                )
                print(
                    source["label"],
                    model["radius"],
                    "gate",
                    gate["all_pass"],
                    direction_row.get("trial", {}).get("actual_flux_change"),
                    flush=True,
                )
                write_json_atomic(args.output, report)
            row.update(
                status="completed",
                work=backend.work.copy(),
                all_pass=all(checks.values()) and all(d["all_pass"] for d in row["directions"]),
            )
        report.update(status="completed", all_pass=all(r["all_pass"] for r in report["cases"]))
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}")
        if active_row is not None:
            active_row.update(
                status="error",
                all_pass=False,
                error=report["error"],
                work=backend.work.copy() if backend is not None else {},
            )
        if active_event is not None and active_event["status"] == "running":
            active_event.update(status="error", error=report["error"])
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
