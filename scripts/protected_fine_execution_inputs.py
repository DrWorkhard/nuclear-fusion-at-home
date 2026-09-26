"""Committed fine execution admission, separate from immutable coarse history.

Missing qualification/checkpoint means closed. Qualification binds code bytes,
not today's repository HEAD; fresh intake and the new outer provenance must
match the current clean HEAD throughout one execution. Historical metadata is
never rewritten, stripped, or regenerated through the coarse source binder.
"""

import copy
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import protected_fine_inputs as inputs

from fusion_baselines.protected_fine_process import SCOPE

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "docs/optimization/PROTECTED_FINE_PROTOCOL.md"
REGISTRATION_COMMIT = "95ec58598258bd5f72fb5e4896186e44449d663b"
REGISTRATION_SHA256 = "bb8ab426a5bf6549e1d246caccc2e0e50077325609d82fa62805051e280acdca"
QUALIFICATION = "evidence/protected-fine-qualification-v1.json"
CHECKPOINT = "evidence/protected-fine-execution-v1.json"
MODULES = (
    "plan",
    "geometry_codec",
    "control",
    "process",
    "ledger",
    "native",
    "geometry",
    "cell",
    "graph",
)
CODE = (
    *(f"src/fusion_baselines/protected_fine_{name}.py" for name in MODULES),
    "scripts/protected_fine_inputs.py",
    "scripts/audit_protected_fine_fields.py",
    "scripts/protected_fine_execution_inputs.py",
    "scripts/run_protected_fine_worker.py",
    "scripts/run_protected_fine.py",
    *(f"tests/test_protected_fine_{name}.py" for name in MODULES),
    "tests/test_protected_fine_inputs.py",
    "tests/test_protected_fine_fields.py",
    "tests/test_protected_fine_execution_inputs.py",
    "tests/test_protected_fine_worker.py",
    "tests/test_protected_fine_launcher.py",
    "tests/test_protected_fine_pipeline.py",
)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, message):
    inputs._same(actual, expected, message)


def _committed(root, path, revision="HEAD"):
    path = Path(path)
    _need(
        path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),
        "committed regular fine source/evidence required",
    )
    relative = path.relative_to(root)
    old = inputs._git(root, "show", f"{revision}:{relative.as_posix()}", text=False)
    _need(path.read_bytes() == old, "fine source/evidence differs from committed bytes")
    return inputs._reference(path)


def _clean(root):
    record = inputs._repository(root)
    _need(
        type(record) is dict
        and record.get("available") is True
        and record.get("dirty") is False
        and record.get("path") == str(root)
        and type(record.get("commit")) is str
        and re.fullmatch(r"[0-9a-f]{40}", record["commit"]),
        "fine execution requires current clean committed repository",
    )
    return record


def _coarse(archive):
    return {
        key: copy.deepcopy(archive[key])
        for key in ("evidence", "summary", "source_before", "source_after", "cases")
    }


def _pins(root, document, implementation):
    result = {}
    for key in ("sources", "artifacts"):
        rows = document[key]
        _need(type(rows) is list and bool(rows), "nonempty fine qualification " + key)
        names, pins = [], []
        for row in rows:
            _need(
                type(row) is dict
                and set(row) == {"path", "sha256", "bytes"}
                and type(row["path"]) is str,
                "exact relative qualification reference",
            )
            path = Path(row["path"])
            _need(
                not path.is_absolute()
                and ".." not in path.parts
                and path.as_posix() == row["path"]
                and row["path"] not in names,
                "unique normalized repository-relative fine qualification file",
            )
            names.append(row["path"])
            reference = dict(row, path=str(root / path))
            inputs._checked(reference)
            _need((root / path).resolve().is_relative_to(root), "qualification file escapes root")
            if key == "sources":
                _committed(root, root / path)
                _committed(root, root / path, implementation)
            pins.append(reference)
        if key == "sources":
            _same(names, [PROTOCOL, *CODE], "complete ordered qualified fine source graph")
        result[key] = pins
    return result


def _regression(root, document, pins, implementation):
    record = document["regression"]
    _need(type(record) is dict, "full fine regression required")
    for key, value in dict(
        exit_code=0,
        failures=0,
        errors=0,
        skipped=0,
        full_committed_suite=True,
        clean_worktree=True,
        execution_commit=implementation,
    ).items():
        _same(record.get(key), value, "fine regression " + key)
    _need(
        type(record.get("passed")) is int and record["passed"] > 3487,
        "fine additions included in complete research regression",
    )
    row = record.get("junit")
    _need(
        type(row) is dict and any(row == value for value in document["artifacts"]),
        "regression JUnit must be an explicitly retained qualification artifact",
    )
    reference = dict(row, path=str(root / row["path"]))
    _need(any(reference == value for value in pins["artifacts"]), "exact checked JUnit reference")
    path = inputs._checked(reference)
    _need(
        path.suffix == ".xml" and 0 < path.stat().st_size <= 8 * 1024**2, "bounded retained JUnit"
    )
    raw = path.read_bytes()
    _need(
        b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(),
        "plain bounded JUnit XML",
    )
    tree = ET.fromstring(raw)
    _need(tree.tag in ("testsuites", "testsuite"), "explicit JUnit root required")
    suites = list(tree.iter("testsuite"))
    _need(
        bool(suites) and all(not list(s.iter("testsuite"))[1:] for s in suites),
        "flat explicit JUnit test suites required",
    )
    totals = dict(tests=0, failures=0, errors=0, skipped=0)
    for suite in suites:
        cases = list(suite.findall("testcase"))
        observed = dict(
            tests=len(cases),
            failures=sum(len(c.findall("failure")) for c in cases),
            errors=sum(len(c.findall("error")) for c in cases),
            skipped=sum(len(c.findall("skipped")) for c in cases),
        )
        for key, value in observed.items():
            _need(suite.get(key) == str(value), "JUnit declared/observed count mismatch: " + key)
            totals[key] += value
    _need(len(list(tree.iter("testcase"))) == totals["tests"], "no hidden nested JUnit cases")
    if tree.tag == "testsuites":
        for key, value in totals.items():
            if key in tree.attrib:
                _need(tree.get(key) == str(value), "JUnit aggregate count mismatch: " + key)
    _same(
        totals,
        dict(tests=record["passed"], failures=0, errors=0, skipped=0),
        "complete passing fine JUnit matches recorded regression",
    )


def sources(root=ROOT):
    """Fresh full execution manifest; no model, field, certificate or search work."""
    root = Path(root).resolve()
    current = _clean(root)
    protocol = _committed(root, root / PROTOCOL, REGISTRATION_COMMIT)
    _same(protocol["sha256"], REGISTRATION_SHA256, "unchanged registered fine scientific protocol")
    inputs._git(root, "merge-base", "--is-ancestor", REGISTRATION_COMMIT, current["commit"])
    # Refuse missing permission before expensive archived graph reconstruction.
    qualification_ref = _committed(root, root / QUALIFICATION)
    checkpoint_ref = _committed(root, root / CHECKPOINT)
    qualification, checkpoint = inputs._load(qualification_ref), inputs._load(checkpoint_ref)
    expected_q = {
        "schema_version",
        "kind",
        "status",
        "qualification_pass",
        "implementation_commit",
        "execution",
        "coarse",
        "sources",
        "artifacts",
        "regression",
        "independent_review",
        "limits",
    }
    _need(
        type(qualification) is dict and set(qualification) == expected_q,
        "exact committed fine implementation qualification required",
    )
    _need(
        type(checkpoint) is dict
        and set(checkpoint)
        == {
            "schema_version",
            "kind",
            "status",
            "execution_checkpoint_pass",
            "execution",
            "coarse",
            "qualification",
            "limits",
        },
        "exact committed fine execution checkpoint required",
    )
    for key, value in dict(
        schema_version=1,
        kind="protected-fine-implementation-qualification",
        status="completed",
        qualification_pass=True,
        limits=SCOPE,
    ).items():
        _same(qualification[key], value, "fine qualification " + key)
    for key, value in dict(
        schema_version=1,
        kind="protected-fine-execution-checkpoint",
        status="ready",
        execution_checkpoint_pass=True,
        limits=SCOPE,
        qualification=qualification_ref,
    ).items():
        _same(checkpoint[key], value, "fine execution checkpoint " + key)
    implementation = qualification["implementation_commit"]
    _need(
        type(implementation) is str and re.fullmatch(r"[0-9a-f]{40}", implementation),
        "full fine implementation commit required",
    )
    inputs._git(root, "merge-base", "--is-ancestor", implementation, current["commit"])
    _same(
        qualification["independent_review"],
        dict(internal=True, blocking_findings_remaining=False),
        "completed independent internal fine review required",
    )
    pins = _pins(root, qualification, implementation)
    _regression(root, qualification, pins, implementation)
    execution = dict(
        protocol=_committed(root, root / PROTOCOL),
        code=[_committed(root, root / name) for name in CODE],
    )
    for document in (qualification, checkpoint):
        _same(document["execution"], execution, "exact qualified fine execution sources")
    archived = inputs.archive(root)
    _same(
        archived["current_provenance"], current, "fresh archive belongs to current fine repository"
    )
    for document in (qualification, checkpoint):
        _same(document["coarse"], _coarse(archived), "unchanged completed coarse anchors")
    _same(_clean(root), current, "unchanged current fine repository during admission")
    return dict(
        schema_version=1,
        kind="protected-fine-execution-sources",
        archive=copy.deepcopy(archived),
        execution=execution,
        qualification=dict(evidence=qualification_ref, **pins),
        execution_admission=dict(checkpoint=checkpoint_ref, qualification=qualification_ref),
        repository=current,
        fine_execution_authorized=True,
        **SCOPE,
    )


def build_context(source, case):
    """Build private context only from an explicit admitted full-source envelope.

    The caller must compare this envelope to fresh sources(); its own boolean
    permission field is not a substitute for the committed execution gate.
    """
    _need(
        type(source) is dict
        and source.get("kind") == "protected-fine-execution-sources"
        and source.get("fine_execution_authorized") is True,
        "admitted fine source envelope required",
    )
    return inputs.build_context(copy.deepcopy(source["archive"]), copy.deepcopy(case))
