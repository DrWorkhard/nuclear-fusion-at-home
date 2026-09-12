"""Independent file/array audit for the two frozen-geometry current minimizers."""

import argparse
import json
from pathlib import Path

import numpy as np
from current_diagnostic_inputs import checked, predecessor, reference, sources
from run_jac_scaled_study import require_committed

from fusion_baselines.coil_coefficient_view import serialized_physical_coefficients
from fusion_baselines.current_diagnostic_audit import audit_arrays, error
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.selected_start import mapped_start
from fusion_baselines.serialized_current_affine import current_map
from fusion_baselines.serialized_dofs import named_serialized_values
from fusion_baselines.serialized_field_state import serialized_state

CODE = (
    "scripts/audit_fixed_currents.py",
    "scripts/current_diagnostic_inputs.py",
    "src/fusion_baselines/current_diagnostic_audit.py",
    "src/fusion_baselines/affine_current_audit.py",
    "src/fusion_baselines/coil_coefficient_view.py",
    "src/fusion_baselines/serialized_current_affine.py",
    "src/fusion_baselines/serialized_dofs.py",
    "src/fusion_baselines/serialized_field_state.py",
    "src/fusion_baselines/selected_start.py",
)


def audit_case(row, original):
    if row["source"] != original:
        raise ValueError("fixed first-arm source metadata changed")
    before_doc = json.loads(checked(original["field"]).read_text())
    template = json.loads(checked(row["preparation"]["normalized_start"]).read_text())
    after_doc = json.loads(checked(row["field"]).read_text())
    with np.load(checked(row["arrays"]), allow_pickle=False) as archive:
        data = {k: archive[k] for k in archive.files}
    with np.load(checked(original["arrays"]), allow_pickle=False) as source:
        x, permutation, owners = mapped_start(
            before_doc, template, original["names"], row["names"], source["x"]
        )
        replay = error(data["before_values"], source["values"])
    result = audit_arrays(data, row)
    checks = result["checks"]
    checks.update(
        source_mapping=np.array_equal(x, data["x"]),
        source_values=replay <= 1e-12,
        permutation=permutation.tolist() == row["source_indices_in_target_order"],
        owner_map=owners == row["owner_map"],
        unchanged_problem=all(
            row["preparation"][key] == original["preparation"][key]
            for key in (
                "surface",
                "case",
                "thresholds",
                "guarded_search_targets",
                "canonical_total",
            )
        ),
        explicit_names=row["names"] == row["preparation"]["degrees_of_freedom"],
        named_after=np.array_equal(
            data["after_x"], named_serialized_values(after_doc, row["names"])
        ),
    )
    before, after = serialized_state(before_doc), serialized_state(after_doc)
    before_physical = serialized_physical_coefficients(
        before_doc, before["coefficients"].reshape(4, 3, 17)
    )
    after_physical = serialized_physical_coefficients(
        after_doc, after["coefficients"].reshape(4, 3, 17)
    )
    checks["all_physical_geometry"] = np.array_equal(before_physical, after_physical)
    checks["base_regularizations"] = np.array_equal(
        before["base_regularizations"], after["base_regularizations"]
    )
    old_map = current_map(before_doc, original["names"])
    new_map = current_map(after_doc, row["names"])
    checks["current_columns"] = np.array_equal(data["columns"], new_map["columns"])
    checks["current_affine_map"] = all(
        np.array_equal(old_map[k], new_map[k]) for k in ("matrix", "constant", "scale", "total")
    )
    for label, state, vector, mapping in (
        ("before", before, named_serialized_values(before_doc, original["names"]), old_map),
        ("after", after, data["after_x"], new_map),
    ):
        checks[f"physical_currents_{label}"] = (
            error(state["currents"], row[f"physical_currents_{label}"]) <= 1e-12
            and error(
                state["currents"],
                mapping["matrix"] @ vector[mapping["columns"]] + mapping["constant"],
            )
            <= 1e-12
        )
    for doc, label in ((before_doc, "before"), (after_doc, "after")):
        objects = doc["simsopt_objs"]
        coils = [objects[v["value"]] for v in objects[doc["graph"]["value"]]["coils"]]
        regs = [v["regularization"] for v in coils]
        if label == "before":
            previous_regs = regs
        else:
            checks["all_regularizations"] = regs == previous_regs
    result.update(
        all_pass=all(checks.values()),
        source_replay_error=replay,
        source=original["field"],
        field=row["field"],
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable current audit path required")
    root = Path(__file__).resolve().parents[1]
    for name in CODE:
        require_committed(root, root / name)
    study = json.loads(args.study.read_text())
    result = dict(
        repository=git_state(root),
        source=reference(args.study),
        status="running",
        all_pass=False,
        cases=[],
        code=[reference(root / p) for p in CODE],
        physical_admission=False,
    )
    try:
        selected = sources(root)
        if (
            study["status"] != "completed"
            or not study["all_pass"]
            or len(study["cases"]) != 2
            or study["predecessor"] != predecessor(root)
            or study["physical_admission"] is not False
        ):
            raise ValueError("completed two-state qualification with exact predecessor required")
        for ref in [study["protocol"], *study["code"]]:
            checked(ref)
        for row, original in zip(study["cases"], selected, strict=True):
            result["cases"].append(audit_case(row, original))
            write_json_atomic(args.output, result)
        result.update(status="completed", all_pass=all(r["all_pass"] for r in result["cases"]))
    except Exception as exc:
        result.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(args.output, result)
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
