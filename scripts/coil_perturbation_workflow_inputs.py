"""Additive binding of qualified primitives and the complete field-free workflow."""

from pathlib import Path

import coil_perturbation_inputs as primitive
from current_diagnostic_inputs import reference
from run_jac_scaled_study import require_committed

QUALIFICATION = "evidence/coil-perturbation-v1-primitives.json"
QUALIFICATION_REVISION = "20e9b10"
QUALIFICATION_HASH = "1e241de6874bbd6124586c39415ebdbe7180bc18b6490af0fcee9f85b5436957"
REGRESSION = "artifacts/coil-perturbation-v1-primitives-qualification/regression.xml"
CODE = (
    "scripts/coil_perturbation_workflow_inputs.py",
    "scripts/run_coil_perturbation.py",
    "scripts/audit_coil_perturbation.py",
    "src/fusion_baselines/coil_perturbation_samples.py",
    "src/fusion_baselines/coil_perturbation_direct_audit.py",
    "tests/test_coil_perturbation_workflow_inputs.py",
    "tests/test_coil_perturbation_workflow.py",
    "tests/test_coil_perturbation_samples.py",
    "tests/test_coil_perturbation_overall_audit.py",
    "tests/test_coil_perturbation_direct_audit.py",
)
SCOPE = primitive.SCOPE.copy()
matrix, require, same, checked, read = (
    primitive.matrix,
    primitive.require,
    primitive.same,
    primitive.checked,
    primitive.read,
)


def qualification_gate(document, source, root):
    """Pure contract check in addition to immutable historical byte binding."""
    require(
        same(document.get("schema_version"), 1)
        and document.get("phase") == "coil_perturbation_primitives_qualification",
        "registered primitive qualification schema",
    )
    require(
        same(document.get("tests"), 1840)
        and all(same(document.get(k), 0) for k in ("failures", "errors", "skipped"))
        and same(document.get("warnings"), 334)
        and same(
            document.get("new_tests"),
            dict(producer=55, independent_mathematical_auditor=108, source_binder=37),
        )
        and same(document.get("producer_to_independent_synthetic_cross_cases"), 12)
        and document.get("saved_predecessor_source_replay_pass") is True,
        "complete original pure qualification, not a physical pass",
    )
    require(
        same(
            document.get("scope"),
            dict(
                pure_primitives_qualified=True,
                whole_workflow_qualified=False,
                real_52_state_matrix_executed=False,
                new_project_candidate_geometry_evaluations=0,
                new_project_field_calls=0,
                new_equilibrium_solves=0,
                search_allowed=False,
                field_pass=False,
                transfer_pass=False,
                step4_pass=False,
            ),
        ),
        "preserve the bounded primitive-only qualification scope",
    )
    expected = [*primitive.CODE, primitive.PROTOCOL]
    records = document.get("sources")
    require(
        isinstance(records, list)
        and len(records) == len(expected)
        and all(isinstance(row, dict) and set(row) == {"path", "sha256"} for row in records)
        and [row["path"] for row in records] == expected,
        "ordered complete qualified code and fixed protocol",
    )
    current = [*source["code"], source["protocol"]]
    require(len(current) == len(expected), "complete current primitive code graph")
    root = Path(root).resolve()
    for name, old, new in zip(expected, records, current, strict=True):
        require(
            isinstance(new, dict)
            and set(new) == {"path", "sha256"}
            and new["path"] == str(root / name)
            and same(new["sha256"], old["sha256"]),
            "current primitive/protocol exactly matches its qualified bytes",
        )
    require(
        same(source.get("matrix"), matrix()) and same(source.get("scope"), SCOPE),
        "unchanged two-class field-free protocol",
    )
    junit = document.get("junit")
    require(
        isinstance(junit, dict)
        and set(junit) == {"path", "sha256"}
        and junit["path"] == REGRESSION
        and type(junit["sha256"]) is str
        and len(junit["sha256"]) == 64
        and all(c in "0123456789abcdef" for c in junit["sha256"]),
        "complete original regression reference",
    )


def sources(root):
    root = Path(root).resolve()
    source = primitive.sources(root)
    qualification = primitive.previous.historical(
        root, QUALIFICATION, QUALIFICATION_REVISION, QUALIFICATION_HASH
    )
    document = read(qualification)
    qualification_gate(document, source, root)
    regression = dict(path=str(root / REGRESSION), sha256=document["junit"]["sha256"])
    checked(regression)
    for name in CODE:
        require_committed(root, root / name)
    return dict(
        **source,
        primitive_qualification=qualification,
        primitive_regression=regression,
        workflow_code=[reference(root / name) for name in CODE],
    )
