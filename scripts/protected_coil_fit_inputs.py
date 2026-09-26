"""Read-only admission for the protected eight-cell construction pilot.

The predecessor binders retain their original version boundaries. This module
adds the accepted 52-state geometry qualification and exposes the eight saved
initial field bundles; it performs no new field, geometry, LP or search work.
"""

import copy
from pathlib import Path

import coil_perturbation_workflow_inputs as workflow
import numpy as np
from current_diagnostic_inputs import reference
from run_jac_scaled_study import require_committed

from fusion_baselines import clear_coil_field_audit as fields
from fusion_baselines import coil_perturbation_direct_audit as direct
from fusion_baselines.provenance import git_state

previous = workflow.primitive.previous
require, same, checked, read = previous.require, previous.same, previous.checked, previous.read
PROTOCOL = "docs/optimization/PROTECTED_RUNNER_PROTOCOL.md"
CODE = ("scripts/protected_coil_fit_inputs.py", "tests/test_protected_coil_fit_inputs.py")
PERTURBATION_AUDIT = "evidence/coil-perturbation-v1-audit.json"
PERTURBATION_REVISION = "c60aed7"
PERTURBATION_HASH = "9f8fd9a0c4ca1f93baa3b8896f803e1f1a3a6ae8cd409517abe5a24fda98c7e8"
PERTURBATION_RUN_HASH = "ce895f482e49d36d323c7c08bd2e004356cc2626005bc1cb0f85e44875e6afe6"
SCOPE = workflow.SCOPE.copy()
LIMITS = dict(
    wall_seconds=1800.0,
    parent_poll_seconds=0.5,
    termination_grace_seconds=5,
    start_reserve_bytes=3 * 1024**3,
    live_reserve_bytes=2 * 1024**3,
)
CONSTRUCTION = dict(
    ncoil=256,
    nphi=64,
    ntheta=64,
    ninner=32,
    offset=0,
    nloop=256,
    geometry_nphi=128,
    geometry_ntheta=128,
    geometry_full_torus=True,
    geometry_offset=0,
)


def matrix():
    return [
        dict(
            label=f"{target}-n{n}-{method}",
            target=target,
            nbase=n,
            order=order,
            seed_label=f"n{n}-shape-d100mm",
            method=method,
        )
        for target in ("reference", "selected")
        for n, order in ((6, 5), (8, 7))
        for method in ("N", "V")
    ]


def _identity(actual, expected, message):
    require(same(actual, expected), message)


def _fields(record, expected, message):
    require(type(record) is dict, message)
    for key, value in expected.items():
        _identity(record.get(key), value, f"{message}: {key}")


def _perturbation_gate(audit, run, current):
    _fields(
        audit,
        dict(
            schema_version=1,
            kind="coil-perturbation-audit",
            status="completed",
            all_pass=True,
            arithmetic_and_source_pass=True,
            independent_audit_pass=True,
            qualification_pass=True,
            **SCOPE,
        ),
        "complete accepted field-free perturbation audit",
    )
    _fields(
        run,
        dict(
            schema_version=1,
            kind="coil-perturbation",
            status="completed",
            producer_complete=True,
            source_unchanged=True,
            admission_status="pending-independent-audit",
            all_pass=False,
            independent_audit_pass=False,
            qualification_pass=False,
            **SCOPE,
        ),
        "original producer is not independent admission",
    )
    source = audit.get("source")
    require(type(source) is dict and type(current) is dict, "complete original/current sources")
    _identity(source, run.get("source_before"), "audit and original execution sources")
    _identity(source, run.get("source_after"), "unchanged original execution sources")
    _identity(
        {k: v for k, v in source.items() if k != "repository"},
        {k: v for k, v in current.items() if k != "repository"},
        "all numerical sources unchanged; outer repository metadata only",
    )
    cases = workflow.matrix()
    _identity(source.get("matrix"), cases, "original two-class source matrix")
    _identity(run.get("matrix"), cases, "original two-class run matrix")
    _identity(run.get("limits"), LIMITS, "unchanged predecessor resource limits")
    require(
        type(run.get("rows")) is list and len(run["rows"]) == 2,
        "both complete original raw class results",
    )
    cells = audit.get("cells")
    require(type(cells) is list and len(cells) == 2, "both complete admitted geometry classes")
    for index, (cell, case) in enumerate(zip(cells, cases, strict=True)):
        _fields(
            cell,
            dict(
                case=case,
                status="completed",
                arithmetic_and_source_pass=True,
                qualification_pass=True,
            ),
            "individual geometry class admission",
        )
        work = cell.get("work", {})
        _fields(work, dict(passed=True), "individual completed work audit")
        counts = dict(states=26, certificates=52, direct_grids=104, surfaces=2 if index == 0 else 0)
        _identity(
            work.get("work"),
            {k: dict(attempted=v, completed=v) for k, v in counts.items()},
            "complete per-class attempted/completed work",
        )
        states = cell.get("states")
        require(type(states) is list and len(states) == 26, "all 26 ordered states per class")
        for state, descriptor in zip(states, direct.plan(), strict=True):
            _fields(
                state,
                dict(descriptor, mathematical_pass=True, exact_repeat=True),
                "individual ordered mathematical/repeat qualification",
            )
            require(type(state.get("certified")) is bool, "boolean geometric classification")
            if descriptor["kind"] != "probe" or descriptor["radius"] == 1e-5:
                require(state["certified"] is True, "both seeds and all smallest probes certified")
            grids = state.get("direct")
            require(type(grids) is list and len(grids) == 4, "all four independent direct grids")
            nphysical = 4 * case["nbase"]
            for grid, level in zip(grids, direct.levels(), strict=True):
                _fields(
                    grid,
                    dict(
                        level,
                        passed=True,
                        nphysical=nphysical,
                        coil_pairs_checked=nphysical * (nphysical - 1) // 2,
                        cp_distances_checked=2 * nphysical * level["ncoil"],
                    ),
                    "ordered complete independently passed direct grid",
                )
    _fields(
        audit.get("independent_work"),
        dict(
            certificate_recomputations=52,
            certificate_records_checked=104,
            direct_grids=208,
            surface_reconstructions=2,
        ),
        "complete separately counted independent qualification",
    )


def perturbation_gate(audit, run, current):
    """Pure named acceptance gates; historical byte/graph binding is separate."""
    try:
        _perturbation_gate(audit, run, current)
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError("malformed perturbation admission record") from error


def seed_bundle_gate(row, snapshot, case, geometry, field_source):
    """Original seed identity only: new protected FD probes are not old probes."""
    try:
        require(
            any(same(case, expected) for expected in matrix()), "registered exact physical cell"
        )
        _fields(
            row,
            dict(
                status="completed",
                kind="qualification",
                index=0,
                label="seed",
                method=case["method"],
                model_id=f"qualification-{case['method']}",
                operation_id=f"qualification-{case['method']}-00",
            ),
            "original first startup seed bundle",
        )
        fields.seed_identity(snapshot, geometry, field_source["targets"][case["target"]])
        _fields(
            snapshot,
            dict(
                nbase=case["nbase"],
                order=case["order"],
                method=case["method"],
                construction=CONSTRUCTION,
                initialization_work=dict(seed_A_calls=1, seed_A_points=256),
                B2_scale=field_source["normalization"][case["target"]]["B2_scale"],
            ),
            "exact original seed construction and normalization",
        )
        x, expected = (
            np.asarray(row["x"]),
            np.asarray(geometry["base_coefficients"], dtype=float).ravel(),
        )
        gradient = np.asarray(row["gradient"])
        require(
            x.shape == expected.shape
            and x.dtype.kind in "iuf"
            and np.isfinite(x).all()
            and np.asarray(x, dtype=float).tobytes() == expected.tobytes(),
            "bit-identical full canonical original seed vector",
        )
        require(
            gradient.shape == expected.shape
            and gradient.dtype.kind in "iuf"
            and np.isfinite(gradient).all(),
            "complete finite real canonical seed gradient",
        )
        require(type(row["J"]) is float and np.isfinite(row["J"]), "finite scalar seed objective")
        _fields(
            row["metrics"],
            dict(
                J=row["J"],
                frozen_scale=False,
                B2_scale=snapshot["B2_scale"],
                scale=snapshot["scale"],
                target_flux=snapshot["target_flux"],
                unit_flux=snapshot["unit_flux"],
                current=1e5 * snapshot["scale"],
            ),
            "unmodified physical seed metrics",
        )
        require(
            same(snapshot["unit_flux"], snapshot["seed_unit_flux"])
            and abs(snapshot["unit_flux"]) > 1e-12
            and abs(row["metrics"]["current"]) <= 500000,
            "qualified seed current and flux",
        )
    except (KeyError, TypeError, IndexError, AttributeError) as error:
        raise ValueError("malformed original seed field bundle") from error


def prerequisites(root):
    """Admit historical data without requiring the new component to be committed."""
    root = Path(root).resolve()
    current = workflow.sources(root)
    audit_ref = previous.historical(
        root, PERTURBATION_AUDIT, PERTURBATION_REVISION, PERTURBATION_HASH
    )
    audit = read(audit_ref)
    run_ref = audit["run"]
    require(run_ref.get("sha256") == PERTURBATION_RUN_HASH, "exact original 52-state run digest")
    run = read(run_ref)
    perturbation_gate(audit, run, current)
    # Hash every raw checkpoint/result reference; retain predecessor source-version
    # boundaries instead of opening old reports against arbitrary current code.
    previous.bind_tree(run)
    previous.bind_tree(audit)
    field_source = current["startup"]["source"]
    startup_run = read(current["startup"]["run"])
    bundles = {}
    for physical_case, result_ref in zip(fields.physical_cases(), startup_run["rows"], strict=True):
        result = read(result_ref)
        worker = read(result["worker"])
        _fields(
            result, dict(case=physical_case, status="completed"), "original startup result cell"
        )
        _fields(
            worker, dict(case=physical_case, status="completed"), "original startup worker cell"
        )
        geometry = read(current["seeds"][physical_case["seed_label"]]["snapshot"])
        for method in ("N", "V"):
            case = next(
                c
                for c in matrix()
                if c["target"] == physical_case["target"]
                and c["nbase"] == physical_case["nbase"]
                and c["method"] == method
            )
            rows = worker["qualification"][method]
            require(
                type(rows) is list and len(rows) == 10, "ten original method qualification rows"
            )
            row_ref = rows[0]
            row = read(row_ref)
            snapshot = read(row["snapshot"])
            checked(row["arrays"])
            seed_bundle_gate(row, snapshot, case, geometry, field_source)
            bundles[case["label"]] = dict(
                operation=row_ref, snapshot=row["snapshot"], arrays=row["arrays"]
            )
    require(list(bundles) == [case["label"] for case in matrix()], "all eight ordered seed bundles")
    return copy.deepcopy(
        dict(
            perturbation=dict(audit=audit_ref, run=run_ref, source=current),
            startup=current["startup"],
            geometry=current["geometry"],
            seeds=current["seeds"],
            targets=field_source["targets"],
            target_archives=field_source["target_archives"],
            normalization=field_source["normalization"],
            startup_seed_bundles=bundles,
            matrix=matrix(),
        )
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
