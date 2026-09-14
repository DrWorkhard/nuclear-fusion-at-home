"""Immutable step3 sources and committed numeric dependencies."""

import json
from pathlib import Path

from current_diagnostic_inputs import checked, reference
from run_jac_scaled_study import require_committed

PROTOCOL = "docs/qi/PLASMA_OPTIMIZATION_PROTOCOL.md"
CODE = (
    "scripts/plasma_inputs.py",
    "scripts/plasma_equilibrium_worker.py",
    "scripts/plasma_measurement.py",
    "scripts/run_plasma_search.py",
    "scripts/validate_plasma_design.py",
    "scripts/audit_plasma_design.py",
    "src/fusion_baselines/plasma_design.py",
    "src/fusion_baselines/plasma_action_audit.py",
    "src/fusion_baselines/vmec_trace.py",
    "src/fusion_baselines/bounce_action.py",
    "src/fusion_baselines/qi_resolution.py",
    "src/fusion_baselines/qi_field_grid.py",
    "src/fusion_baselines/clebsch_field.py",
    "src/fusion_baselines/contour_topology.py",
    "scripts/evaluate_published_maximum_j.py",
    "src/fusion_baselines/resource_guard.py",
    "scripts/audit_qi_clebsch.py",
    "tests/test_plasma_design.py",
)


def sources(root, *, committed=True):
    paths = [
        root / "evidence" / p
        for p in (
            "qi-fresh-resolution-v1.json",
            "qi-fresh-resolution-v1-evaluation.json",
            "qi-fresh-resolution-v1-evaluation-audit.json",
            "qi-producer-inventory-v1.json",
            "qi-measurement-v1/nfp2.json",
        )
    ]
    study, evaluated, audit, inventory, measured = [json.loads(p.read_text()) for p in paths]
    cell = next(
        r for r in study["cells"] if (r["case"], r["ns"], r["angular"]) == ("nfp2-vacuum", 201, 2)
    )
    qualification = next(
        r
        for r in evaluated["cells"]
        if (r["case"], r["ns"], r["angular"]) == ("nfp2-vacuum", 201, 2)
    )
    if (
        study["status"] != "completed"
        or not cell["numerically_converged"]
        or not qualification["physical_screen_pass"]
        or not qualification["arithmetic_screen_pass"]
        or audit["all_pass"] is not True
        or audit["source"] != reference(paths[1])
        or measured["coarse_common_interval"] != [1.0082953902491054, 1.5870966275564338]
    ):
        raise ValueError("closed nfp2 numeric source and invariant domain required")
    original = json.loads(checked(cell["original"]).read_text())
    checked(cell["input"])
    for ref in inventory["vmecpp"]["sources"]:
        checked(ref)
    if committed:
        for p in [*paths, checked(cell["original"]), root / PROTOCOL, *(root / p for p in CODE)]:
            require_committed(root, p)
    return original, dict(
        reports=[reference(p) for p in paths],
        original=cell["original"],
        author_input=cell["input"],
        solver=inventory["vmecpp"],
        published_tracer=reference(checked(measured["inputs"]["published_trace"])),
        lock=reference(root / "environments/vmecpp/uv.lock"),
        analysis_lock=reference(root / "uv.lock"),
        protocol=reference(root / PROTOCOL),
        code=[reference(root / p) for p in CODE],
    )


def root_path():
    return Path(__file__).resolve().parents[1]
