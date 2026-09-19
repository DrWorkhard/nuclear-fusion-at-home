"""Committed sources for the geometry-only clear-start follow-up."""

import importlib.metadata
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from coupled_coil_inputs import sources as pilot_sources
from current_diagnostic_inputs import checked, reference
from run_jac_scaled_study import require_committed

PROTOCOL = "docs/geometry/CLEAR_COIL_INITIALIZATION_PROTOCOL.md"
PREDECESSOR_COMMIT = "4f3c2fa"
PREDECESSOR_LABELS = (
    "reference-n6-N",
    "reference-n6-V",
    "selected-n6-N",
    "selected-n6-V",
    "selected-n8-N",
    "selected-n8-V",
)
CODE = (
    "src/fusion_baselines/clear_coil_geometry.py",
    "src/fusion_baselines/clear_coil_geometry_audit.py",
    "scripts/clear_coil_initialization_inputs.py",
    "scripts/run_clear_coil_initialization.py",
    "scripts/audit_clear_coil_initialization.py",
    "tests/test_clear_coil_geometry.py",
    "tests/test_clear_coil_geometry_audit.py",
    "tests/test_clear_coil_initialization_workflow.py",
    "tests/test_clear_coil_initialization_audit.py",
    "src/fusion_baselines/provenance.py",
    "src/fusion_baselines/resource_guard.py",
)


def negative_predecessor(report, source, label):
    """A completed negative decision is retained, never converted into admission."""
    required = dict(
        arithmetic_and_source_pass=True,
        validation_complete=True,
        all_pass=False,
        entry_pass=False,
        transfer_pass=False,
        step4_pass=False,
    )
    recheck = report.get("typed_gate_recheck", {})
    if (
        report.get("status") != "completed"
        or report.get("phase") != "validation"
        or report.get("source") != source
        or report.get("case", {}).get("label") != label
        or any(report.get(key) is not value for key, value in required.items())
        or recheck.get("identical") is not True
        or recheck.get("entry_pass") is not False
        or recheck.get("legacy_gates") != recheck.get("normalized_gates")
        or recheck.get("normalized_gates") != report.get("gates")
        or report.get("run") != report.get("validation")
    ):
        raise ValueError("exact completed and unchanged negative coil-pilot admission required")


def historical_identity(root, path, commit=PREDECESSOR_COMMIT):
    relative = path.resolve().relative_to(root.resolve())
    original = subprocess.check_output(["git", "show", f"{commit}:{relative}"], cwd=root)
    if original != path.read_bytes():
        raise ValueError(f"historical negative evidence changed: {relative}")


def sources(root):
    from fusion_baselines.clear_coil_geometry import OPTIONS, cases

    root = Path(root).resolve()
    pilot = pilot_sources(root)
    negatives = []
    for label in PREDECESSOR_LABELS:
        path = root / f"evidence/coupled-coil-pilot-v1/validation-{label}-audit-serialized.json"
        historical_identity(root, path)
        require_committed(root, path)
        report = json.loads(path.read_text())
        negative_predecessor(report, pilot, label)
        for key in ("run", "failure_manifest", "legacy_auditor", "output_adapter", "adapter_tests"):
            checked(report[key])
        negatives.append(dict(label=label, report=reference(path), run=report["run"]))
    for path in (root / PROTOCOL, *(root / p for p in CODE)):
        require_committed(root, path)
    import scipy.optimize

    optimize = Path(scipy.optimize.__file__).parent
    solver_files = [
        optimize / p
        for p in (
            "_linprog.py",
            "_linprog_util.py",
            "_linprog_highs.py",
            "_optimize.py",
            "_highspy/__init__.py",
            "_highspy/_highs_wrapper.py",
        )
    ]
    for module in ("scipy.optimize._highspy._core", "scipy.optimize._highspy._highs_options"):
        spec = importlib.util.find_spec(module)
        if spec is None or spec.origin is None:
            raise ValueError(f"required pinned native HiGHS component missing: {module}")
        solver_files.append(Path(spec.origin))
    native_geometry = [
        root / "external/simsopt/src/simsopt/geo" / p
        for p in ("surface.py", "surfacerzfourier.py", "curve.py", "curvexyzfourier.py")
    ]
    return dict(
        pilot=pilot,
        targets=pilot["targets"],
        negatives=negatives,
        preserved_revision=PREDECESSOR_COMMIT,
        protocol=reference(root / PROTOCOL),
        code=[reference(root / p) for p in CODE],
        solver_files=[reference(p) for p in solver_files],
        native_geometry=[reference(p) for p in native_geometry],
        versions={name: importlib.metadata.version(name) for name in ("numpy", "scipy", "simsopt")},
        python=dict(executable=str(Path(sys.executable).resolve()), version=sys.version),
        solver_configuration=dict(method="highs-ds", options=OPTIONS.copy()),
        matrix=cases(),
    )
