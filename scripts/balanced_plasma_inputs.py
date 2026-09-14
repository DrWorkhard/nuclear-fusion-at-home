"""Source-bound follow-up; the previous numerical implementation remains immutable."""

import json

from current_diagnostic_inputs import checked, reference
from plasma_inputs import sources as legacy_sources
from run_jac_scaled_study import require_committed

CODE = (
    "src/fusion_baselines/balanced_plasma.py",
    "scripts/balanced_plasma_inputs.py",
    "scripts/run_balanced_plasma.py",
    "scripts/validate_balanced_plasma.py",
    "scripts/audit_balanced_plasma.py",
    "tests/test_balanced_plasma.py",
)
PROTOCOL = "docs/qi/PLASMA_BALANCED_PROTOCOL.md"


def sources(root, *, committed=True):
    original, legacy = legacy_sources(root, committed=committed)
    paths = [
        root / "evidence" / name
        for name in (
            "plasma-design-v2/summary.json",
            "plasma-design-v2-holdout.json",
            "plasma-design-v2-audit.json",
        )
    ]
    study, holdout, audit = [json.loads(p.read_text()) for p in paths]
    if (
        study["status"] != "completed"
        or study["source"] != legacy
        or len(study["cells"]) != 16
        or audit["status"] != "completed"
        or audit["arithmetic_and_source_pass"] is not True
        or audit["step3_pass"] is not False
        or audit["study"] != reference(paths[0])
        or audit["holdout"] != reference(paths[1])
        or not holdout["all_phases_completed"]
    ):
        raise ValueError("fully audited negative predecessor required")
    for r in study["cells"] + study["endpoints"]:
        for key in ("input", "request", "wout", "solver"):
            checked(r[key])
    if committed:
        for p in [*paths, root / PROTOCOL, *(root / p for p in CODE)]:
            require_committed(root, p)
    return (
        original,
        dict(
            legacy=legacy,
            study=reference(paths[0]),
            holdout=reference(paths[1]),
            audit=reference(paths[2]),
            protocol=reference(root / PROTOCOL),
            code=[reference(root / p) for p in CODE],
        ),
        study,
    )
