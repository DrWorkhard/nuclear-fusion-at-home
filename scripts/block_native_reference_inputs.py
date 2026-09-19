"""Immutable prerequisites for the separately registered block-native reference."""

import importlib.util
import json
import subprocess
from pathlib import Path

import qualify_sparse_coil_surface as legacy
from run_jac_scaled_study import require_committed

from fusion_baselines.provenance import git_state

PROTOCOL = "docs/optimization/BLOCK_NATIVE_REFERENCE_PROTOCOL.md"
PREDECESSOR = "evidence/clear-coil-field-start-v1-resource.json"
PREDECESSOR_COMMIT = "97d75b8"
PREDECESSOR_HASH = "5c77723ee9f77de7a4b176de3a69f06ccc6af6d22ad7a4572c2c631ea013acdf"
CODE = (
    "src/fusion_baselines/block_native_coil_surface.py",
    "scripts/block_native_reference_inputs.py",
    "scripts/qualify_block_native_reference.py",
    "scripts/audit_block_native_reference.py",
    "tests/test_block_native_coil_surface.py",
    "tests/test_block_native_reference_inputs.py",
    "tests/test_block_native_reference_workflow.py",
    "tests/test_block_native_reference_audit.py",
)
DENSE_FAILURES = {"n6-q512-native", "n8-q256-native", "n8-q512-native"}


def matrix():
    return [
        dict(label=f"n{n}-q{q}-block-native", nbase=n, order=m, ncoil=q, backend="block-native")
        for n, m in ((6, 5), (8, 7))
        for q in (256, 512)
    ]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(reference):
    return json.loads(legacy.checked(reference).read_text())


def check_references(document, seen=None):
    """Check every nested byte reference; conflicting aliases never get skipped."""
    seen = {} if seen is None else seen
    if isinstance(document, dict):
        if "path" in document and "sha256" in document:
            require(set(document) == {"path", "sha256", "bytes"}, "complete byte reference")
            require(
                type(document["bytes"]) is int and document["bytes"] >= 0,
                "exact nonnegative byte count",
            )
            require(Path(document["path"]).is_absolute(), "absolute immutable reference")
            previous = seen.get(document["path"])
            require(previous is None or previous == document, "conflicting reference aliases")
            if previous is None:
                legacy.checked(document)
                seen[document["path"]] = document
        for value in document.values():
            check_references(value, seen)
    elif isinstance(document, list):
        for value in document:
            check_references(value, seen)
    return seen


def summary_gate(report):
    require(
        type(report.get("schema_version")) is int
        and report["schema_version"] == 1
        and report.get("status") == "completed"
        and report.get("kind") == "synthetic-resource-qualification"
        and report.get("source_unchanged") is True
        and report.get("source_before") == report.get("source_after")
        and isinstance(report.get("source_before"), dict)
        and report.get("all_pass") is False
        and report.get("scope") == legacy.SCOPE
        and report.get("matrix") == legacy.matrix()
        and len(report.get("rows", [])) == 8,
        "complete unchanged negative resource predecessor required",
    )
    require(
        report.get("limits")
        == dict(
            wall_seconds=120.0,
            peak_rss_bytes=1610612736,
            parent_poll_seconds=0.5,
            termination_grace_seconds=5,
        ),
        "original resource limits",
    )
    require(
        [(row.get("nbase"), row.get("ncoil")) for row in report.get("pairs", [])]
        == [(n, q) for n in (6, 8) for q in (256, 512)]
        and all(row.get("all_pass") is True for row in report["pairs"]),
        "all four original mathematical pairs required",
    )


def numerical_environment(current, original):
    """A new local commit is allowed; changed numerical bytes/environment are not."""
    expected = {key: value for key, value in original.items() if key != "repository"}
    actual = {key: value for key, value in current.items() if key != "repository"}
    require(actual == expected, "original numerical bytes or environment changed")
    return actual


def predecessor(root):
    root = Path(root).resolve()
    path = root / PREDECESSOR
    require_committed(root, path)
    reference = legacy.ref(path)
    require(reference["sha256"] == PREDECESSOR_HASH, "fixed negative predecessor hash")
    historical = subprocess.check_output(
        ["git", "show", f"{PREDECESSOR_COMMIT}:{PREDECESSOR}"], cwd=root
    )
    require(historical == path.read_bytes(), "historical negative predecessor bytes")
    report = read(reference)
    summary_gate(report)
    checked = check_references(report)
    documents, references, reports = {}, {}, []
    failures = set()
    for index, (reference_row, case) in enumerate(
        zip(report["rows"], legacy.matrix(), strict=True)
    ):
        row = read(reference_row)
        require(
            row.get("index") == index
            and row.get("case") == case
            and row.get("status") == "completed",
            "complete ordered original worker",
        )
        checked = check_references(row, checked)
        document, process = read(row["worker"]), read(row["process"])
        checked = check_references(document, checked)
        config_refs = [ref for ref in row["retained"] if Path(ref["path"]).name == "config.json"]
        require(len(config_refs) == 1, "single retained original worker configuration")
        config = read(config_refs[0])
        require(
            config["case"] == case and config["source"] == report["source_before"],
            "original worker configuration source",
        )
        legacy.completed_worker(
            process, document, case, report["source_before"], config["started_monotonic"]
        )
        own = legacy.worker_checks(document)
        require(
            own == row["checks"] and own["all_pass"] is True,
            "all original numerical gates independently recomputed",
        )
        rss = document["peak_rss_bytes"]
        passed = rss <= legacy.MAX_RSS_BYTES
        require(
            row["peak_rss_bytes"] == rss and row.get("resource_pass") is passed,
            "exact original resource classification",
        )
        if not passed:
            failures.add(case["label"])
        if case["backend"] == "sparse":
            require(passed, "each unchanged sparse worker must pass its resource cap")
        documents[case["label"]], references[case["label"]] = document, row["worker"]
        reports.append(dict(case=case, numerical_checks=own, resource_pass=passed))
    require(failures == DENSE_FAILURES, "preserve exactly three dense memory failures")
    pairs = []
    for n in (6, 8):
        for q in (256, 512):
            stem = f"n{n}-q{q}"
            own = legacy.compare_pair(documents[stem + "-native"], documents[stem + "-sparse"])
            require(own["all_pass"] is True, "all original paired numerical checks")
            pairs.append(dict(nbase=n, ncoil=q, **own))
    require(pairs == report["pairs"], "original pair reports independently reproduced")
    return dict(
        old_reference=reference,
        old_workers=references,
        legacy_source=report["source_before"],
        old_checks=dict(
            workers=reports,
            pairs=pairs,
            references=len(checked),
            dense_failures=sorted(failures),
            old_all_pass=False,
        ),
    )


def sources(root):
    root = Path(root).resolve()
    old = predecessor(root)
    environment = numerical_environment(legacy.sources(), old["legacy_source"])
    for path in (root / PROTOCOL, *(root / name for name in CODE)):
        require_committed(root, path)
    # The original resource report binds the geometry module itself. Bind its
    # JIT wrapper too and prove installed bytes equal the preserved native commit.
    spec = importlib.util.find_spec("simsopt")
    require(spec is not None and spec.origin is not None, "installed native Python package")
    installed = Path(spec.origin).parent / "geo/jit.py"
    checkout = root / "external/simsopt/src/simsopt/geo/jit.py"
    native_commit = old["legacy_source"]["external_repository"]["commit"]
    historical_jit = subprocess.check_output(
        ["git", "show", f"{native_commit}:src/simsopt/geo/jit.py"], cwd=root / "external/simsopt"
    )
    require(
        installed.read_bytes() == checkout.read_bytes() == historical_jit,
        "unchanged installed native JIT wrapper",
    )
    return dict(
        **old,
        native_environment=environment,
        repository=git_state(root),
        protocol=legacy.ref(root / PROTOCOL),
        code=[legacy.ref(root / name) for name in CODE],
        native_jit=[legacy.ref(installed), legacy.ref(checkout)],
        matrix=matrix(),
    )
