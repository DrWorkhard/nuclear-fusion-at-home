"""Source-bound two-state current study and completed finest-mesh predecessor."""

import json
from pathlib import Path

from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import sha256_file

STATES = (
    (
        "al",
        "upstream-start-study-v1",
        "6ee2a013254b2f30195291dfd4d13c6a166d06d5286cb966db92a2646db2fb5f",
    ),
    (
        "slsqp",
        "slsqp-composite-v1",
        "a9a2448a9204478acd2b89675f625bc2122c4665c311d6623c0642800e661dcf",
    ),
)


def reference(path):
    return dict(path=str(Path(path).resolve()), sha256=sha256_file(path))


def checked(ref):
    path = Path(ref["path"])
    if sha256_file(path) != ref["sha256"]:
        raise ValueError("fixed-current study source hash mismatch")
    return path


def sources(root):
    result = []
    for label, name, expected_sha in STATES:
        paths = [
            root / "evidence" / p
            for p in (
                f"{name}/summary.json",
                f"{name}-audit.json",
                f"{name}-validation/summary.json",
            )
        ]
        study, audit, holdout = [json.loads(p.read_text()) for p in paths]
        if (
            study["status"] != "completed"
            or not study["qualification_pass"]
            or not audit["all_pass"]
            or audit["study"] != reference(paths[0])
            or holdout["status"] != "completed"
            or not holdout["all_four_phases_completed"]
            or holdout["study"] != reference(paths[0])
            or holdout["audit"] != reference(paths[1])
            or [step["name"] for step in holdout["steps"]]
            != ["holdout", "curvature", "clearance", "native"]
            or any(step["status"] != "completed" for step in holdout["steps"])
        ):
            raise ValueError("two originally qualified/audited/fine-checked sources required")
        arm = json.loads(checked(study["arms"][0]).read_text())
        if arm["best"]["field"]["sha256"] != expected_sha:
            raise ValueError("predeclared first selected field changed")
        for ref in [arm["best"]["field"], arm["best"]["arrays"], *study["code"]]:
            checked(ref)
        for step in holdout["steps"]:
            checked(step["result"])
        for path in paths:
            require_committed(root, path)
        result.append(
            dict(
                label=label,
                study=reference(paths[0]),
                audit=reference(paths[1]),
                holdouts=reference(paths[2]),
                arm=study["arms"][0],
                field=arm["best"]["field"],
                arrays=arm["best"]["arrays"],
                names=study["preparation"]["degrees_of_freedom"],
                preparation=study["preparation"],
            )
        )
    return result


def predecessor(root):
    path = root / "evidence/mesh-fine-completion-v1-audit.json"
    audit = json.loads(path.read_text())
    study_path = checked(audit["source"])
    study = json.loads(study_path.read_text())
    if audit["status"] != "completed" or not audit["all_pass"] or study["status"] != "completed":
        raise ValueError("completed independent finest-mesh audit required")
    require_committed(root, path)
    require_committed(root, study_path)
    return reference(path)
