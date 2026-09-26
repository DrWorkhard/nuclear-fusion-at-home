"""Additive launch admission; stays closed until a physics qualification is pinned."""

import re
from pathlib import Path

import protected_native_inputs as native
import qualify_protected_cell_physics as physics

PROTOCOL = "docs/optimization/PROTECTED_PILOT_EXECUTION_PROTOCOL.md"
CODE = (
    "scripts/protected_pilot_inputs.py",
    "scripts/run_protected_coil_fit.py",
    "tests/test_protected_pilot_inputs.py",
    "tests/test_protected_coil_fit_launcher.py",
)
QUALIFICATION = "evidence/protected-saved-physics-v1.json"
# Saved-physics qualification is complete; the separate execution checkpoint
# must still exist, bind independently qualified launcher bytes and be committed.
QUALIFICATION_REVISION = "c2237843bf9d961b2ae24c8d152cafd56927ebf7"
QUALIFICATION_HASH = "0d0d15d6c11cbd505863de08ea9b244b621b09fa474217d9f45bc153f2257843"
EXECUTION_CHECKPOINT = "evidence/protected-pilot-execution-v1.json"
EXECUTION_SCOPE = dict(
    physical_admission=False,
    fine_grid_acceptance=False,
    realized_field_transfer=False,
    step4_pass=False,
    sota_advance=False,
    ms1_reached=False,
    resolved_fine_grid_improvement=False,
    pareto_dominance=False,
    external_peer_review=False,
)


def _pins(root, document):
    """Pin all relative qualification records, including retained failed tests."""
    pins = {}
    for key in ("sources", "artifacts"):
        rows = document[key]
        native.require(type(rows) is list and bool(rows), "nonempty qualification references")
        pins[key], names = [], set()
        for row in rows:
            native.require(
                type(row) is dict and type(row.get("path")) is str, "named qualification reference"
            )
            path = Path(row["path"])
            native.require(
                not path.is_absolute() and ".." not in path.parts and str(path) not in names,
                "unique repository-relative qualification reference",
            )
            names.add(str(path))
            ref = dict(path=str(root / path), sha256=row["sha256"], bytes=row["bytes"])
            native.checked(ref)
            if key == "sources":
                native.require_committed(root, root / path)
            pins[key].append(ref)
    return pins


def _execution_gate(root, execution, physics_ref):
    """Fixed committed checkpoint, without a circular hash of this source file.

    Checkpoint: schema_version=1, kind=protected-pilot-execution-checkpoint,
    status=ready, execution_checkpoint_pass=True, execution, physics_qualification
    and launcher_qualification (a distinct committed repository JSON reference).
    The linked launcher qualification repeats execution/physics identities and
    binds its complete source/artifact evidence, successful regression and review.
    """
    path = root / EXECUTION_CHECKPOINT
    native.require(
        path.is_file() and not path.is_symlink(),
        "fixed execution checkpoint must be a regular nonsymlink file",
    )
    native.require_committed(root, path)
    ref = native.reference(path)
    checkpoint = native.read(ref)
    native.previous._fields(
        checkpoint,
        dict(
            schema_version=1,
            kind="protected-pilot-execution-checkpoint",
            status="ready",
            execution_checkpoint_pass=True,
            execution=execution,
            physics_qualification=physics_ref,
        ),
        "committed exact execution checkpoint",
    )
    native.previous._fields(
        checkpoint["limits"],
        EXECUTION_SCOPE,
        "execution checkpoint preserves diagnostic-only scope",
    )
    qualification_ref = checkpoint["launcher_qualification"]
    qualification_path = Path(qualification_ref["path"])
    native.require(
        qualification_path.is_absolute()
        and qualification_path.suffix == ".json"
        and qualification_path.is_file()
        and not qualification_path.is_symlink()
        and qualification_path.resolve().is_relative_to(root)
        and qualification_path.resolve() != path.resolve(),
        "distinct repository launcher qualification",
    )
    native.checked(qualification_ref)
    native.require_committed(root, qualification_path)
    qualification = native.read(qualification_ref)
    native.previous._fields(
        qualification,
        dict(
            schema_version=1,
            kind="protected-pilot-launcher-qualification",
            status="completed",
            launcher_qualification_pass=True,
            execution=execution,
            physics_qualification=physics_ref,
        ),
        "independently qualified exact launcher sources",
    )
    native.previous._fields(
        qualification["limits"],
        EXECUTION_SCOPE,
        "launcher qualification preserves diagnostic-only scope",
    )
    native.previous._fields(
        qualification["regression"],
        dict(
            exit_code=0,
            failures=0,
            errors=0,
            skipped=0,
        ),
        "complete successful launcher regression",
    )
    native.require(
        type(qualification["regression"]["passed"]) is int
        and qualification["regression"]["passed"] > 3363,
        "launcher tests included in full regression",
    )
    native.previous._fields(
        qualification["independent_review"],
        dict(
            internal=True,
            blocking_findings_remaining=False,
        ),
        "completed independent internal launcher review",
    )
    pins = _pins(root, qualification)
    required = [execution["protocol"], *execution["code"]]
    for expected in required:
        native.require(
            any(
                row["path"] == expected["path"] and row["sha256"] == expected["sha256"]
                for row in pins["sources"]
            ),
            "all exact launcher sources qualified",
        )
    return dict(checkpoint=ref, qualification=qualification_ref, **pins)


def sources(root):
    root = Path(root).resolve()
    native.require(
        type(QUALIFICATION_REVISION) is str
        and re.fullmatch(r"[0-9a-f]{7,40}", QUALIFICATION_REVISION)
        and type(QUALIFICATION_HASH) is str
        and re.fullmatch(r"[0-9a-f]{64}", QUALIFICATION_HASH),
        "native pilot is closed: saved-physics qualification is not pinned",
    )
    repository = native.git_state(root)
    native.require(
        repository.get("available") is True
        and repository.get("dirty") is False
        and type(repository.get("commit")) is str
        and re.fullmatch(r"[0-9a-f]{40}", repository["commit"]),
        "native pilot requires an available clean committed checkout",
    )
    bound = physics.sources(root)
    qualification_ref = native.previous.previous.historical(
        root, QUALIFICATION, QUALIFICATION_REVISION, QUALIFICATION_HASH
    )
    qualification = native.read(qualification_ref)
    native.previous._fields(
        qualification,
        dict(
            schema_version=1,
            kind="protected-saved-physics-qualification",
            status="completed",
            saved_physics_qualification_pass=True,
        ),
        "completed independently reviewed saved-physics qualification",
    )
    native.previous._fields(
        qualification["historical_reconstruction"],
        dict(
            contexts_passed=8,
            certificate_recomputations=2,
            recorded_certificates_checked=4,
            sampled_BA_comparisons=48,
            sampled_vectors=3072,
            sampled_scalar_components=9216,
            native_requests=0,
            native_models_initialized=0,
            producer_certificates=0,
            equilibrium_solves=0,
            search_calls=0,
        ),
        "eight historical physics reconstructions and original proof comparisons",
    )
    native.previous._fields(
        qualification["regression"],
        dict(exit_code=0, failures=0, errors=0, skipped=0),
        "successful saved-physics full regression",
    )
    native.require(
        type(qualification["regression"]["passed"]) is int
        and qualification["regression"]["passed"] >= 3363,
        "complete predecessor plus physical regression",
    )
    native.previous._fields(
        qualification["independent_review"],
        dict(
            internal=True,
            blocking_findings_remaining=False,
            focused_passed=130,
        ),
        "completed independent internal saved-physics review",
    )
    native.previous._fields(
        qualification["limits"],
        dict(
            new_native_search_executed=False,
            physical_admission=False,
            fine_grid_acceptance=False,
            step4_pass=False,
            sota_advance=False,
            ms1_reached=False,
            external_peer_review=False,
        ),
        "qualified reconstruction cannot acquire design-acceptance scope",
    )
    rows = qualification["sources"]
    native.require(
        type(rows) is list and all(type(row) is dict for row in rows),
        "complete physical source references",
    )
    names = [row["path"] for row in rows]
    native.require(
        len(names) == len(set(names)) and set((physics.PROTOCOL, *physics.CODE)).issubset(names),
        "all independently qualified physical sources",
    )
    pins = _pins(root, qualification)
    for name in (PROTOCOL, *CODE):
        native.require_committed(root, root / name)
    execution = dict(
        protocol=native.reference(root / PROTOCOL),
        code=[native.reference(root / name) for name in CODE],
    )
    gate = _execution_gate(root, execution, qualification_ref)
    native.require(
        native.same(native.git_state(root), repository),
        "unchanged clean repository during launch source admission",
    )
    return dict(
        physics_sources=bound,
        qualification=dict(evidence=qualification_ref, **pins),
        execution=execution,
        execution_admission=gate,
        repository=repository,
    )
