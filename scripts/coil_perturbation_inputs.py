"""Immutable geometry/field-start admission for a field-free perturbation study.

Only prior evidence is read. This binder does not generate perturbed geometry or
evaluate magnetic fields, equilibria, searches, or linear programs.
"""

from pathlib import Path

import clear_coil_field_start_inputs as previous
from current_diagnostic_inputs import reference
from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import git_state

PROTOCOL = "docs/geometry/COIL_PERTURBATION_PROTOCOL.md"
CODE = (
    "src/fusion_baselines/coil_perturbation.py",
    "src/fusion_baselines/coil_perturbation_audit.py",
    "scripts/coil_perturbation_inputs.py",
    "tests/test_coil_perturbation.py",
    "tests/test_coil_perturbation_audit.py",
    "tests/test_coil_perturbation_inputs.py",
)
STARTUP_AUDIT = "evidence/clear-coil-field-start-v1-audit.json"
STARTUP_AUDIT_HASH = "e6fa7cda853cc2576f9660501043fc6f8c0d7121c1ce0a819df47544fd262fd8"
STARTUP_RUN = "evidence/clear-coil-field-start-v1-run.json"
STARTUP_RUN_HASH = "e4949a9be9518c9acaa727c3f6de238703028e9baca16bf89ec15bb145cb9714"
STARTUP_REVISION = "3334f1e"
SCOPE = dict(
    field_calls=0,
    gradient_calls=0,
    equilibrium_solves=0,
    search_calls=0,
    lp_calls=0,
    search_allowed=False,
    field_pass=False,
    transfer_pass=False,
    step4_pass=False,
)
require, same, checked, read = previous.require, previous.same, previous.checked, previous.read


def matrix():
    return [
        dict(label=f"n{n}-shape-d100mm", nbase=n, order=m, geometry_report_index=i)
        for n, m, i in ((6, 5, 3), (8, 7, 9))
    ]


def startup_gate(audit, run, current):
    """Retain individual numerical passes and all four physical rejections."""
    require(
        audit.get("status") == "completed"
        and all(
            audit.get(key) is True
            for key in (
                "all_pass",
                "arithmetic_and_source_pass",
                "independent_audit_pass",
                "startup_pass",
            )
        )
        and all(
            audit.get(key) is False
            for key in ("physical_seed_pass", "search_allowed", "transfer_pass", "step4_pass")
        )
        and same(audit.get("equilibrium_solves"), 0)
        and same(audit.get("search_calls"), 0),
        "completed positive numerical startup, negative physical admission",
    )
    require(
        run.get("status") == "completed"
        and run.get("kind") == "clear-coil-field-start"
        and run.get("producer_complete") is True
        and run.get("source_unchanged") is True
        and run.get("admission_status") == "pending-independent-audit"
        and all(
            run.get(key) is False
            for key in (
                "all_pass",
                "startup_pass",
                "physical_seed_pass",
                "search_allowed",
                "transfer_pass",
                "step4_pass",
                "independent_audit_pass",
            )
        )
        and same(run.get("equilibrium_solves"), 0)
        and same(run.get("search_calls"), 0),
        "original complete producer is not independent admission",
    )
    binding = audit.get("source")
    require(
        isinstance(binding, dict)
        and same(binding, run.get("source_before"))
        and same(binding, run.get("source_after"))
        and same(
            {k: v for k, v in binding.items() if k != "repository"},
            {k: v for k, v in current.items() if k != "repository"},
        ),
        "exact executed/current startup sources; later root metadata only",
    )
    cases = previous.physical_cases()
    cells = audit.get("cells", [])
    require(
        len(cells) == 4
        and same(run.get("matrix"), cases)
        and same(binding.get("matrix"), cases)
        and len(run.get("rows", [])) == 4,
        "complete four-cell numerical predecessor",
    )
    for cell, case in zip(cells, cases, strict=True):
        require(
            same(cell.get("case"), case)
            and cell.get("status") == "completed"
            and cell.get("arithmetic_and_source_pass") is True
            and cell.get("startup_pass") is True
            and all(
                cell.get(key) is False
                for key in ("physical_seed_pass", "search_allowed", "transfer_pass", "step4_pass")
            ),
            "each original cell qualified numerically, rejected physically",
        )
        require(
            same(
                cell.get("checks"),
                dict(
                    startup=True,
                    normal_rms=False,
                    normal_max=False,
                    vector_rms=False,
                    current=True,
                    lengths=True,
                    curvature=True,
                    coil_distance=True,
                    plasma_distance=True,
                ),
            ),
            "all original positive geometry/current and three negative field gates retained",
        )
        work = cell.get("work", {})
        require(
            work.get("passed") is True
            and same(work.get("events"), 524)
            and same(
                work.get("work"),
                dict(
                    native_requests=262,
                    completed_requests=262,
                    values=202,
                    vjps=60,
                    initialization_requests=10,
                    full_bundles=20,
                    equilibrium_solves=0,
                    search_calls=0,
                ),
            ),
            "all original native work retained",
        )
        qualification = cell.get("qualification", {})
        require(set(qualification) == {"N", "V"}, "both independent method qualifications")
        for method in ("N", "V"):
            q = qualification[method]
            derivative = q.get("derivatives", {})
            checks = derivative.get("checks", [])
            require(
                q.get("passed") is True
                and len(q.get("rows", [])) == 10
                and derivative.get("passed") is True
                and derivative.get("exact_repeat") is True
                and len(checks) == 8
                and all(row.get("passed") is True for row in checks),
                "all derivative steps, independent values and exact repetitions",
            )
        refinement = cell.get("refinement", {})
        require(
            cell.get("identity", {}).get("passed") is True
            and len(cell.get("diagnostics", [])) == 6
            and all(row.get("status") == "completed" for row in cell["diagnostics"])
            and refinement.get("passed") is True
            and len(refinement.get("checks", [])) == 5
            and all(row.get("passed") is True for row in refinement["checks"]),
            "all six grids, five refinements and physical N/V identity",
        )
        blocks = cell.get("flux", [])
        require(len(blocks) == 2, "both full flux blocks")
        for block, ncoil in zip(blocks, (256, 512), strict=True):
            require(
                same(block.get("ncoil"), ncoil)
                and block.get("passed") is True
                and len(block.get("grids", [])) == len(block.get("values", [])) == 9
                and len(block.get("checks", [])) == 27
                and all(row.get("passed") is True for row in block["checks"]),
                "all target/Stokes/angular/radial flux checks",
            )
        cross = cell.get("flux_coil_comparison", {})
        require(
            cross.get("passed") is True
            and len(cross.get("checks", [])) == 9
            and all(row.get("passed") is True for row in cross["checks"])
            and same(cell.get("direct_point_reconstructions"), 96)
            and same(cell.get("direct_field_comparisons"), 192),
            "all cross-coil flux and independent direct-field work",
        )


def prerequisites(root):
    root = Path(root).resolve()
    current = previous.sources(root)
    audit_ref = previous.historical(root, STARTUP_AUDIT, STARTUP_REVISION, STARTUP_AUDIT_HASH)
    run_ref = previous.historical(root, STARTUP_RUN, STARTUP_REVISION, STARTUP_RUN_HASH)
    audit, run = read(audit_ref), read(run_ref)
    startup_gate(audit, run, current)
    require(audit["run"]["sha256"] == STARTUP_RUN_HASH, "original raw startup digest")
    previous.bind_tree(run)
    previous.bind_tree(audit["run"])
    # This reuses the fully pinned predecessor admission, not candidate arithmetic.
    geometry = current["geometry"]
    geometry_audit, geometry_run = read(geometry["audit"]), read(geometry["run"])
    seeds = {}
    for case in matrix():
        index, label = case["geometry_report_index"], case["label"]
        report, row = geometry_audit["sets"][index], geometry_run["sets"][index]
        require(
            report["case"]["label"] == label
            and row["case"]["label"] == label
            and report["geometry_pass"] is True
            and row["snapshot"]["sha256"] == previous.SEED_HASHES[label]
            and same(row["snapshot"], current["seeds"][label]["snapshot"]),
            "exact selected actual seed and associated geometry report",
        )
        checked(row["snapshot"])
        seeds[label] = dict(snapshot=row["snapshot"], geometry_report_index=index)
    return dict(
        startup=dict(audit=audit_ref, run=run_ref, source=run["source_before"]),
        geometry=geometry,
        seeds=seeds,
        targets={label: current["targets"][label]["input"] for label in ("reference", "selected")},
        matrix=matrix(),
        scope=SCOPE.copy(),
    )


def sources(root):
    root = Path(root).resolve()
    bound = prerequisites(root)
    for name in (PROTOCOL, *CODE):
        require_committed(root, root / name)
    return dict(
        **bound,
        protocol=reference(root / PROTOCOL),
        code=[reference(root / name) for name in CODE],
        repository=git_state(root),
    )
