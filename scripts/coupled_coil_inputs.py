"""Fixed original/accepted step3 sources for the new paired coil pilot."""

import importlib.metadata
import json
from pathlib import Path

from balanced_plasma_inputs import sources as plasma_sources
from current_diagnostic_inputs import checked, reference
from run_jac_scaled_study import require_committed

from fusion_baselines.coupled_coil_workflow import cases

PROTOCOL = "docs/optimization/COUPLED_COIL_PILOT_PROTOCOL.md"
CODE = (
    "src/fusion_baselines/coupled_coils.py",
    "src/fusion_baselines/coupled_coil_audit.py",
    "src/fusion_baselines/coupled_coil_workflow.py",
    "scripts/coupled_coil_inputs.py",
    "scripts/run_coupled_coil_pilot.py",
    "scripts/audit_coupled_coil_pilot.py",
    "scripts/validate_coupled_coil_pilot.py",
    "tests/test_coupled_coils.py",
    "tests/test_coupled_coil_audit.py",
    "tests/test_coupled_coil_workflow.py",
    "tests/test_coupled_coil_overall_audit.py",
    "tests/test_coupled_coil_validation.py",
    "tests/test_coupled_coil_integration.py",
    "tests/test_coupled_coil_runner.py",
)

STEP3_GATES = (
    "cell_guards", "crosscheck", "geometry", "holdout_gain", "new_design",
    "physics", "refinement", "repeat", "resolved_gain", "training_gain",
)
TARGET_WOUT_HASHES = {
    "reference": "83dc45b911a1e8290c3e97c7e28d4de28fcff6021b93d55df2f91d6dd3751c5e",
    "selected": "8cd6bebfc29963f80645acf25e1a3db194e4db381365b17a89b9844554f51b52",
}
FIELD_CHECKS = ("cartesian", "magnitude", "missing_2pi", "poloidal", "toroidal", "wrong_sign")


def accepted_predecessor(audit, end, validation, plasma, validation_reference):
    """Require the final scientific decision, not merely a completed producer."""
    gates = audit.get("gates", {})
    if not (
        audit.get("status") == "completed"
        and audit.get("phase") == "final"
        and audit.get("step3_pass") is True
        and audit.get("arithmetic_and_source_pass") is True
        and set(gates) == set(STEP3_GATES)
        and all(gates[name] is True for name in STEP3_GATES)
        and audit.get("source") == plasma
        and audit.get("validation") == validation_reference
        and end.get("source") == plasma
        and end.get("status") == "completed"
        and [row.get("label") for row in end.get("rows", [])]
        == ["selected-repeat", "selected-fine"]
        and validation.get("status") == "completed"
        and validation.get("all_phases_completed") is True
        and validation.get("used_for_selection") is False
        and validation.get("source") == plasma["legacy"]
        and [state.get("label") for state in validation.get("states", [])]
        == ["reference-201", "selected-201", "reference-401", "selected-401"]
        and all(state.get("errors") == [] for state in validation["states"])
    ):
        raise ValueError("accepted immutable step3 predecessor and complete validation required")


def target_archives(validation, targets):
    """Bind accepted native-coordinate archives; nested subgrids need no new target solve.

    The independent auditor can reconstruct Cartesian positions from radius,
    height and phi, and compare the vector target with archived ``native``. The
    16/32/64 target grids are nested slices of the archived n64 grids. Both n64
    and n128 files remain hash-bound, preserving the qualified refinement pair.
    """
    result = {}
    for label, state in zip(("reference", "selected"), validation["states"][2:], strict=True):
        fields = state.get("fields", [])
        if not (
            state.get("label") == f"{label}-401"
            and state.get("wout") == targets[label]["wout"]
            and state["wout"]["sha256"] == TARGET_WOUT_HASHES[label]
            and [(f.get("s"), f.get("n")) for f in fields]
            == [(s, n) for s in (0.25, 0.5, 0.75) for n in (64, 128)]
            and all(
                set(f.get("checks", {})) == set(FIELD_CHECKS)
                and all(f["checks"][name] is True for name in FIELD_CHECKS)
                for f in fields
            )
        ):
            raise ValueError("exact accepted/reference401 field archive identities required")
        for field in fields:
            checked(field["arrays"])
        result[label] = dict(
            label=state["label"], wout=state["wout"],
            fields=[{key: f[key] for key in ("s", "n", "arrays")} for f in fields],
        )
    return result


def sources(root):
    root = Path(root).resolve()
    _, plasma, old = plasma_sources(root)
    end_path = root / "evidence/plasma-balanced-v1/endpoints.json"
    audit_path = root / "evidence/plasma-balanced-v1/final-audit.json"
    validation_path = root / "evidence/plasma-balanced-v1/validation.json"
    end, audit, validation = [
        json.loads(p.read_text()) for p in (end_path, audit_path, validation_path)
    ]
    accepted_predecessor(audit, end, validation, plasma, reference(validation_path))
    targets = {}
    for label, native, exported in (
        ("reference", old["endpoints"][1], "plasma-design-v2/reference-input-401.json"),
        ("selected", end["rows"][1]["native"], "plasma-balanced-v1/selected-input-401.json"),
    ):
        input_path = root / "evidence" / exported
        require_committed(root, input_path)
        if not (native["status"] == "completed" and native["eligible"] is True
                and native["ns"] == 401
                and native["wout"]["sha256"] == TARGET_WOUT_HASHES[label]):
            raise ValueError("exact completed target401 endpoint required")
        if input_path.read_bytes() != checked(native["input"]).read_bytes():
            raise ValueError("exported target does not match actual native input")
        checked(native["wout"])
        targets[label] = dict(input=reference(input_path), wout=native["wout"])
    archives = target_archives(validation, targets)
    import simsoptpp

    native_files = [Path(simsoptpp.__file__)]
    native_files += [root / "external/simsopt/src/simsopt" / p for p in (
        "field/biotsavart.py", "field/coil.py", "geo/curve.py",
        "geo/curvexyzfourier.py", "geo/curveobjectives.py", "geo/surfacerzfourier.py",
        "objectives/utilities.py", "_core/derivative.py",
    )]
    for p in [root / PROTOCOL, end_path, audit_path, validation_path,
              *(root / p for p in CODE)]:
        require_committed(root, p)
    return dict(
        plasma=plasma, predecessor=reference(audit_path), endpoints=reference(end_path),
        validation=reference(validation_path), target_archives=archives,
        targets=targets, protocol=reference(root / PROTOCOL),
        code=[reference(root / p) for p in CODE], native=[reference(p) for p in native_files],
        versions={name: importlib.metadata.version(name)
                  for name in ("numpy", "scipy", "netCDF4", "simsopt", "jax", "jaxlib")},
        matrix=cases(),
    )
