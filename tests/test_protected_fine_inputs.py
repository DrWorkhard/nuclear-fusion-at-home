"""Synthetic archive/type/linkage controls; no native model or physics calls."""

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import protected_fine_inputs as inputs  # noqa: E402

from fusion_baselines.protected_run_snapshots import SnapshotStore  # noqa: E402


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    if type(payload) is not bytes:
        payload = json.dumps(payload, allow_nan=False).encode()
    path.write_bytes(payload)
    return inputs._reference(path)


@pytest.fixture
def archive_harness(tmp_path, monkeypatch):
    source = dict(repository=dict(commit=inputs.EXECUTION_COMMIT),
                  historical=dict(repository=dict(commit="a" * 40)),
                  physics_sources=dict(native_sources={"preserved": "original"}))
    ref = dict(path=str(tmp_path / "evidence.json"), sha256="a" * 64, bytes=1)
    evidence = dict(summary=dict(ref, path=str(tmp_path / "summary.json")),
                    source_before=dict(ref, path=str(tmp_path / "source-before.json")),
                    source_after=dict(ref, path=str(tmp_path / "source-after.json")))
    contexts = {
        case["label"]: dict(case=copy.deepcopy(case), original_context=dict(original=True),
                            coarse=dict(reference="source-bound-" + case["label"]),
                            selected=dict(state=dict(x=[-0.0]),
                                          arrays=dict(B=np.array([1.0]))))
        for case in inputs.plan.cases()
    }
    calls = dict(cases=[], git=[], source_checks=0, anchors=0)
    current = dict(path=str(tmp_path), available=True, dirty=True,
                   branch="fine-work", commit="b" * 40)

    def anchor(root):
        assert root == tmp_path
        calls["anchors"] += 1
        return copy.deepcopy((ref, evidence, {}, source))

    def context(e, summary, s, case):
        assert e == evidence and summary == {} and s == source
        calls["cases"].append(case["label"])
        return copy.deepcopy(contexts[case["label"]])

    def inline(observed):
        assert observed == source
        calls["source_checks"] += 1
        return {"one": ref}, 2

    monkeypatch.setattr(inputs, "_anchor", anchor)
    monkeypatch.setattr(inputs, "_context", context)
    monkeypatch.setattr(inputs, "_inline_sources", inline)
    monkeypatch.setattr(inputs, "_repository", lambda root: copy.deepcopy(current))
    monkeypatch.setattr(inputs, "_repositories", lambda root, s: {"preserved": True})
    monkeypatch.setattr(inputs, "_environment", lambda root, s, refs: {"current": True})
    monkeypatch.setattr(inputs, "_registrations", lambda root, refs: ["git-bound"])
    monkeypatch.setattr(inputs, "_git", lambda root, *args, **kw: calls["git"].append(args))
    monkeypatch.setattr(inputs.native, "sources", lambda *args: pytest.fail("no current recapture"))
    monkeypatch.setattr(inputs.launcher, "run", lambda *args: pytest.fail("no native launcher"))
    return SimpleNamespace(root=tmp_path, source=source, ref=ref, evidence=evidence,
                           contexts=contexts, calls=calls, current=current)


def test_archive_preserves_provenance_and_checks_all_eight_without_authorizing(archive_harness):
    h = archive_harness
    result = inputs.archive(h.root)
    assert result["archived_source"] == h.source
    assert result["current_provenance"] == h.current
    assert result["current_provenance"]["dirty"] is True
    assert result["archived_source"]["repository"]["commit"] != h.current["commit"]
    assert h.calls["cases"] == [case["label"] for case in inputs.plan.cases()]
    assert h.calls["source_checks"] == 1
    assert result["checked_inputs"]["inline_reference_occurrences"] == 2
    assert result["checked_inputs"]["unique_inline_files"] == 1
    assert result["checked_inputs"]["complete_coarse_graphs_checked"] == 8
    assert result["checked_inputs"]["independent_physics_recomputed"] is False
    assert result["checked_inputs"]["prior_qualified_ancestry_reexpanded"] is False
    assert all(result[key] is False for key in inputs.SCOPE)
    assert h.calls["git"] == [("merge-base", "--is-ancestor",
                               inputs.EXECUTION_COMMIT, h.current["commit"])]


def test_build_context_rebinds_selected_case_and_returns_private_data(archive_harness):
    h = archive_harness
    archived = inputs.archive(h.root)
    case = inputs.plan.cases()[3]
    context = inputs.build_context(archived, case)
    assert h.calls["cases"][-1] == case["label"]
    assert h.calls["anchors"] == 2
    context["selected"]["arrays"]["B"][0] = 999
    context["case"]["nbase"] = 777
    again = inputs.build_context(archived, case)
    assert again["selected"]["arrays"]["B"][0] == 1
    assert again["case"]["nbase"] == 8
    archived["archived_source"]["historical"]["repository"]["commit"] = "c" * 40
    assert h.source["historical"]["repository"]["commit"] == "a" * 40


@pytest.mark.parametrize("field", ["evidence", "summary", "source_before", "source_after",
                                  "archived_source", "cases"])
def test_rehashed_or_substituted_archive_identity_rejected(archive_harness, field):
    h = archive_harness
    archived = inputs.archive(h.root)
    if field == "cases":
        archived[field][0]["reference"] = "another-selected-candidate"
    elif field == "archived_source":
        archived[field]["repository"]["commit"] = h.current["commit"]
    else:
        archived[field]["sha256"] = "b" * 64
    with pytest.raises(ValueError):
        inputs.build_context(archived, inputs.plan.cases()[0])


@pytest.mark.parametrize("key", list(inputs.SCOPE))
@pytest.mark.parametrize("value", [True, 0, None, "false"])
def test_no_authorization_or_physical_flags_can_be_forged(archive_harness, key, value):
    h = archive_harness
    archived = inputs.archive(h.root)
    archived[key] = value
    with pytest.raises(ValueError):
        inputs.build_context(archived, inputs.plan.cases()[0])


@pytest.mark.parametrize("change", ["extra", "missing", "wrong-kind", "version-bool",
                                    "relative-root", "case-count", "wrong-case"])
def test_archive_envelope_strict(archive_harness, change):
    h = archive_harness
    archived, case = inputs.archive(h.root), inputs.plan.cases()[0]
    if change == "extra":
        archived["authorized"] = True
    elif change == "missing":
        del archived["checked_inputs"]
    elif change == "wrong-kind":
        archived["kind"] = "fine-execution-gate"
    elif change == "version-bool":
        archived["schema_version"] = True
    elif change == "relative-root":
        archived["root"] = "relative"
    elif change == "case-count":
        archived["cases"].pop()
    else:
        case["nbase"] = 6.0
    with pytest.raises(ValueError):
        inputs.build_context(archived, case)


def test_any_case_failure_prevents_complete_archive(archive_harness, monkeypatch):
    h = archive_harness
    original = inputs._context

    def fail(e, summary, source, case):
        if case["label"] == "reference-n8-N":
            raise ValueError("missing original case")
        return original(e, summary, source, case)

    monkeypatch.setattr(inputs, "_context", fail)
    with pytest.raises(ValueError, match="missing original"):
        inputs.archive(h.root)
    assert h.calls["cases"] == ["reference-n6-N", "reference-n6-V"]


def test_changed_current_provenance_rejected(archive_harness, monkeypatch):
    h = archive_harness
    values = iter([h.current, dict(h.current, dirty=False)])
    monkeypatch.setattr(inputs, "_repository", lambda root: copy.deepcopy(next(values)))
    with pytest.raises(ValueError, match="stable"):
        inputs.archive(h.root)


@pytest.mark.parametrize("mutate", ["hash", "size", "bool-size", "negative-size", "relative",
                                    "extra", "missing-hash", "uppercase", "symlink"])
def test_strict_byte_references(tmp_path, mutate):
    ref = write(tmp_path / "one.json", {"safe": True})
    if mutate == "hash":
        ref["sha256"] = "a" * 64
    elif mutate == "size":
        ref["bytes"] += 1
    elif mutate == "bool-size":
        ref["bytes"] = True
    elif mutate == "negative-size":
        ref["bytes"] = -1
    elif mutate == "relative":
        ref["path"] = "one.json"
    elif mutate == "extra":
        ref["current_commit"] = "ignored"
    elif mutate == "missing-hash":
        del ref["sha256"]
    elif mutate == "uppercase":
        ref["sha256"] = ref["sha256"].upper()
    else:
        link = tmp_path / "alias.json"
        link.symlink_to(ref["path"])
        ref["path"] = str(link)
    with pytest.raises(ValueError):
        inputs._checked(ref)


def test_inline_closure_checks_every_occurrence_without_opening_ancestor(tmp_path):
    missing = dict(path=str(tmp_path / "older-code.py"), sha256="a" * 64)
    ancestor = write(tmp_path / "ancestor.json", {"historical_source": missing})
    first = dict(ancestor)
    del first["bytes"]
    source = dict(a=first, nested=[dict(b=ancestor)])
    refs, count = inputs._inline_sources(source)
    assert count == 2 and len(refs) == 1
    assert refs[ancestor["path"]] == ancestor
    Path(ancestor["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError):
        inputs._inline_sources(source)


@pytest.mark.parametrize("payload", [b'{"duplicate":1,"duplicate":2}',
                                     b'{"bad":NaN}', b'{"bad":Infinity}'])
def test_historical_json_is_strict_without_reformatting(tmp_path, payload):
    ref = write(tmp_path / "old.json", payload)
    with pytest.raises(ValueError):
        inputs._load(ref)


def test_git_failure_is_never_a_clean_status(tmp_path, monkeypatch):
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        assert kwargs["check"] is True and kwargs["timeout"] == 30
        if "status" in argv:
            raise subprocess.CalledProcessError(128, argv)
        if "--show-toplevel" in argv:
            return SimpleNamespace(stdout=str(tmp_path) + "\n")
        if "HEAD" in argv:
            return SimpleNamespace(stdout="a" * 40 + "\n")
        return SimpleNamespace(stdout="main\n")

    monkeypatch.setattr(inputs.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        inputs._repository(tmp_path)
    assert len(calls) == 4


def repository_fixture(root):
    project = dict(path=str(root), available=True, branch="historical",
                   dirty=False, commit="a" * 40)
    external = dict(project, path=str(root / "external/simsopt"), branch="native", commit="b" * 40)
    return project, external


def test_historical_repository_is_preserved_and_external_is_fresh(tmp_path, monkeypatch):
    project, external = repository_fixture(tmp_path)
    calls = []
    monkeypatch.setattr(inputs, "_git", lambda root, *args: calls.append((root, args)))
    monkeypatch.setattr(inputs, "_repository", lambda root: copy.deepcopy(external))
    source = dict(repository=project, duplicate=project, native=dict(repository=external))
    result = inputs._repositories(tmp_path, source)
    assert result["project_records"] == 2 and result["active_native_records"] == 1
    assert len(calls) == 1
    assert source["repository"] == project
    assert result["historical_project_commits"] == ["a" * 40]


@pytest.mark.parametrize("change", ["available", "dirty", "bool-commit", "unknown-path",
                                    "extra", "external-dirty", "external-commit"])
def test_repository_mutations_fail(tmp_path, monkeypatch, change):
    project, external = repository_fixture(tmp_path)
    current = copy.deepcopy(external)
    monkeypatch.setattr(inputs, "_git", lambda *args: None)
    monkeypatch.setattr(inputs, "_repository", lambda root: current)
    if change == "available":
        project["available"] = 1
    elif change == "dirty":
        project["dirty"] = 0
    elif change == "bool-commit":
        project["commit"] = True
    elif change == "unknown-path":
        external["path"] = str(tmp_path / "other")
    elif change == "extra":
        project["rewritten"] = False
    elif change == "external-dirty":
        current["dirty"] = True
    else:
        current["commit"] = "c" * 40
    with pytest.raises(ValueError):
        inputs._repositories(tmp_path, [project, external])


@pytest.fixture
def environment(tmp_path, monkeypatch):
    installed = tmp_path / "environment/site-packages/simsopt"
    scipy = tmp_path / "environment/site-packages/scipy"
    binary = tmp_path / "environment/site-packages/simsoptpp.so"
    init = write(installed / "__init__.py", b"original")
    code = write(installed / "geo/curve.py", b"curve-original")
    check = write(tmp_path / "external/simsopt/src/simsopt/geo/curve.py", b"curve-original")
    binary_ref = write(binary, b"native-binary")
    scipy_ref = write(scipy / "optimize/helper.py", b"scipy")
    origins = {"simsopt": installed / "__init__.py", "simsoptpp": binary,
               "scipy": scipy / "__init__.py"}
    monkeypatch.setattr(inputs, "_origin", lambda name: origins[name])
    versions = {"numpy": "1", "simsopt": "2", "scipy": "3", "netCDF4": "4"}
    monkeypatch.setattr(inputs.importlib.metadata, "version", lambda name: versions[name])
    full = dict(python_version=sys.version, platform=sys.platform,
                python=dict(path=str(Path(sys.executable).resolve())),
                native_binary=binary_ref, installed_native_python=[init, code],
                packages={"numpy": "1", "scipy": "3", "simsopt": "2"})
    source = dict(environment=full, geometry=dict(versions={"netCDF4": "4"},
                  python=dict(executable=str(Path(sys.executable).resolve()), version=sys.version)))
    refs = {row["path"]: row for row in [init, code, check, binary_ref, scipy_ref]}
    return SimpleNamespace(root=tmp_path, source=source, refs=refs, origins=origins,
                           versions=versions, installed=installed, full=full)


def test_environment_versions_origins_binary_and_extra_python_pins(environment):
    h = environment
    result = inputs._environment(h.root, h.source, h.refs)
    assert result["full_environment_records"] == 1 and result["version_records"] == 2
    assert result["packages"] == h.versions
    assert result["installed_native_files"] == sorted(
        str(h.installed / name) for name in ["__init__.py", "geo/curve.py"])


@pytest.mark.parametrize("change", ["python", "executable", "platform", "binary-origin",
                                    "package-origin", "package-version", "extra-version",
                                    "installed-bytes", "extra-installed-path", "scipy-origin"])
def test_active_environment_changes_rejected(environment, change):
    h = environment
    if change == "python":
        h.full["python_version"] = "other"
    elif change == "executable":
        h.full["python"]["path"] += "-other"
    elif change == "platform":
        h.full["platform"] = "unknown"
    elif change == "binary-origin":
        h.origins["simsoptpp"] = h.root / "other.so"
    elif change == "package-origin":
        h.origins["simsopt"] = h.root / "other/__init__.py"
    elif change == "package-version":
        h.versions["numpy"] = "changed"
    elif change == "extra-version":
        h.versions["netCDF4"] = "changed"
    elif change == "installed-bytes":
        (h.installed / "geo/curve.py").write_bytes(b"different")
    elif change == "extra-installed-path":
        path = h.root / "other/site-packages/simsopt/geo/extra.py"
        h.refs[str(path)] = dict(path=str(path), sha256="a" * 64)
    else:
        h.origins["scipy"] = h.root / "other-scipy/__init__.py"
    with pytest.raises(ValueError):
        inputs._environment(h.root, h.source, h.refs)


def test_registration_commit_bytes_not_current_worktree(tmp_path, monkeypatch):
    original = b"old registered protocol"
    refs = {}
    for index, name in enumerate(inputs.REGISTRATIONS):
        registration = dict(path=f"docs/optimization/OLD_{index}.md", commit="a" * 40,
                            sha256=hashlib.sha256(original).hexdigest(), bytes=len(original))
        refs[str(tmp_path / name)] = write(tmp_path / name, dict(registration=registration))
        write(tmp_path / registration["path"], b"new clarified protocol")
    calls = []

    def git(root, *args, text=True):
        calls.append((args, text))
        return original if args[0] == "show" else ""

    monkeypatch.setattr(inputs, "_git", git)
    result = inputs._registrations(tmp_path, refs)
    assert len(result) == 3
    assert sum(args[0] == "show" and text is False for args, text in calls) == 3


@pytest.mark.parametrize("change", ["hash", "bytes", "bool-bytes", "commit", "path", "extra",
                                    "missing", "initial"])
def test_historical_registration_forgery_rejected(tmp_path, monkeypatch, change):
    original = b"historical"
    registration = dict(path="docs/optimization/old.md", commit="a" * 40,
                        sha256=hashlib.sha256(original).hexdigest(), bytes=len(original))
    if change == "hash":
        registration["sha256"] = "b" * 64
    elif change == "bytes":
        registration["bytes"] += 1
    elif change == "bool-bytes":
        registration["bytes"] = True
    elif change == "commit":
        registration["commit"] = "HEAD"
    elif change == "path":
        registration["path"] = "../escape"
    elif change == "extra":
        registration["ignore_current"] = True
    elif change == "missing":
        del registration["sha256"]
    else:
        registration["initial_commit"] = 1
    refs = {str(tmp_path / name): write(tmp_path / name, dict(registration=registration))
            for name in inputs.REGISTRATIONS}
    monkeypatch.setattr(inputs, "_git", lambda root, *a, **kw: original)
    with pytest.raises(ValueError):
        inputs._registrations(tmp_path, refs)


@pytest.fixture
def anchor(tmp_path, monkeypatch):
    store = SnapshotStore(tmp_path / "canonical")
    source = dict(repository=dict(commit=inputs.EXECUTION_COMMIT))
    before = store.json("before", source)
    after = store.json("after", source)
    case_refs = [store.json(f"case-{i}", {"index": i}) for i in range(8)]
    counts = dict(native_requests=100, bundles=10, certificates=20)
    summary = dict(schema_version=1, kind="protected-coil-fit-construction", status="completed",
                   source_before=before, source_after=after, matrix=inputs.plan.cases(),
                   completed_cases=8, all_eight_constructions_complete=True,
                   all_eight_independent_coarse_verifications_pass=True,
                   failure_policy="stop-without-retry", fine_phase="required-not-run",
                   confirmed_work=counts, cases=case_refs, **inputs.launcher.SCOPE)
    evidence = dict(schema_version=1, kind="protected-coil-fit-coarse-evidence", status="completed",
                    construction_and_coarse_verification_pass=True,
                    execution_source_commit=inputs.EXECUTION_COMMIT, command_exit_code=0,
                    clean_source_before_after=True, fine_phase="required-not-run",
                    limits=dict(inputs.launcher.SCOPE, external_peer_review=False),
                    summary=store.json("summary", summary), source_before=before,
                    source_after=after,
                    confirmed_work=counts, cases=[dict(case=case, case_record=ref) for case, ref in
                                                 zip(inputs.plan.cases(), case_refs, strict=True)])
    path = tmp_path / inputs.EVIDENCE

    def pin():
        ref = write(path, evidence)
        monkeypatch.setattr(inputs, "EVIDENCE_SHA256", ref["sha256"])
        monkeypatch.setattr(inputs, "_git", lambda *a, **kw: path.read_bytes())
        return ref

    pin()
    return SimpleNamespace(root=tmp_path, store=store, source=source, evidence=evidence,
                           summary=summary, path=path, pin=pin)


def test_anchor_binds_fixed_evidence_returned_summary_and_old_source(anchor):
    h = anchor
    ref, evidence, summary, source = inputs._anchor(h.root)
    assert ref["sha256"] == inputs.EVIDENCE_SHA256
    assert evidence == h.evidence and summary == h.summary and source == h.source


@pytest.mark.parametrize("key,value", [
    ("schema_version", True), ("command_exit_code", False), ("command_exit_code", 1),
    ("construction_and_coarse_verification_pass", 1), ("status", "failed"),
    ("execution_source_commit", "a" * 40), ("fine_phase", "complete"),
    ("clean_source_before_after", False),
])
def test_rehashed_coarse_evidence_gate_mutations_rejected(anchor, key, value):
    h = anchor
    h.evidence[key] = value
    h.pin()
    with pytest.raises(ValueError):
        inputs._anchor(h.root)


@pytest.mark.parametrize("change", ["summary-flag", "summary-count", "summary-order", "work",
                                    "source-after", "case-ref", "case-count", "scope"])
def test_coarse_summary_source_or_case_substitution_rejected(anchor, change):
    h = anchor
    if change == "summary-flag":
        h.summary["all_eight_constructions_complete"] = 1
    elif change == "summary-count":
        h.summary["completed_cases"] = 7
    elif change == "summary-order":
        h.summary["matrix"].reverse()
    elif change == "work":
        h.summary["confirmed_work"] = dict(native_requests=999)
    elif change == "source-after":
        h.evidence["source_after"] = h.store.json("changed-source", {"different": True})
        h.summary["source_after"] = h.evidence["source_after"]
    elif change == "case-ref":
        h.evidence["cases"][0]["case_record"] = h.evidence["cases"][1]["case_record"]
    elif change == "case-count":
        h.evidence["cases"].pop()
    else:
        h.evidence["limits"]["physical_admission"] = True
    h.evidence["summary"] = h.store.json("new-summary", h.summary)
    h.pin()
    with pytest.raises(ValueError):
        inputs._anchor(h.root)


def test_evidence_cannot_disagree_with_fixed_commit(anchor, monkeypatch):
    monkeypatch.setattr(inputs, "_git", lambda *a, **kw: b"different committed bytes")
    with pytest.raises(ValueError, match="committed"):
        inputs._anchor(anchor.root)


def test_coarse_evidence_inline_report_bytes_must_still_exist_and_match(anchor):
    h = anchor
    old = write(h.root / "review.json", {"status": "reviewed"})
    h.evidence["independent_internal_graph_review"] = old
    h.pin()
    Path(old["path"]).write_bytes(b"changed review")
    with pytest.raises(ValueError, match="archived"):
        inputs._anchor(h.root)


def test_inline_binding_does_not_replace_expected_hash_with_a_second_read(tmp_path, monkeypatch):
    ref = write(tmp_path / "original", b"original")
    original_checked = inputs._checked

    def checked_then_changed(reference):
        path = original_checked(reference)
        path.write_bytes(b"changed!")
        return path

    monkeypatch.setattr(inputs, "_checked", checked_then_changed)
    refs, count = inputs._inline_sources(dict(pinned=ref))
    assert count == 1
    assert refs[ref["path"]]["sha256"] == ref["sha256"]


@pytest.fixture
def context_harness(tmp_path, monkeypatch):
    store = SnapshotStore(tmp_path / "data")
    case = inputs.plan.cases()[0]
    source = dict(physics_sources=dict(native_sources={"original_manifest": True}))
    selected = dict(state=dict(x=[-0.0, 0.5]), snapshot=dict(scale=2.0),
                    arrays=dict(B=np.arange(6, dtype=float).reshape(2, 3)))
    certificate = dict(result=dict(certified=True), original_seed="original, not candidate")
    bundle = dict(case=case, state=selected["state"],
                  snapshot=store.json("snapshot", selected["snapshot"]),
                  arrays=store.arrays("arrays", selected["arrays"]),
                  certificate=store.json("certificate", certificate))
    bundle_ref = store.json("bundle", bundle)
    search_ref = store.json("search", {"selected": selected["state"]})
    cell = dict(selected_bundle=bundle_ref, search_report=search_ref)
    cell_ref = store.json("cell", cell)
    acknowledgement_ref = store.json("acknowledgement", {"explicit": "returned"})
    audit_ref = store.json("physics", {"saved": "already calculated"})
    counts = dict(native_requests=110, bundles=12, certificates=12)
    changes = {"normal_rms": {"difference": -0.1}}
    record = dict(schema_version=1, kind="protected-pilot-case", status="completed", index=0,
                  case=case, construction_completed=True, independent_coarse_verification_pass=True,
                  parent_acknowledgement=acknowledgement_ref, independent_reconstruction=audit_ref,
                  cell_result=cell_ref, counts=counts, diagnostic_changes=changes,
                  **inputs.launcher.SCOPE)
    case_ref = store.json("case", record)
    row = dict(case=case, case_record=case_ref, core_result=cell_ref,
               parent_acknowledgement=acknowledgement_ref, independent_reconstruction=audit_ref,
               counts=counts, selected_bundle=bundle_ref, search_report=search_ref,
               selected_snapshot=bundle["snapshot"])
    evidence = dict(cases=[row], summary=dict(path=str(tmp_path / "summary.json")))
    summary = dict(cases=[case_ref])
    original = dict(case=case, seed=dict(original=True))
    report = dict(diagnostic_changes=changes)
    graph = dict(complete_bundles=12, counts=dict(native=dict(completed=110),
                 certificate={"startup": dict(completed=10), "other": dict(completed=2)}))
    calls = []
    d = object()

    def linked(dependencies, ack, actual_case, actual_source, output):
        assert dependencies is d and ack == acknowledgement_ref
        assert actual_case == case and actual_source == source
        assert output == tmp_path / "cell-00-reference-n6-N"
        calls.append("acknowledgement")
        return {}, row["core_result"]

    def audit_link(dependencies, ref, cell_reference, actual_case, actual_source, context):
        assert dependencies is d and ref == audit_ref
        assert cell_reference == row["core_result"] and actual_case == case
        assert actual_source == source and context == original
        calls.append("independent-report-and-full-graph")
        return report, graph

    def old_context(manifest, actual_case):
        assert manifest == {"original_manifest": True} and actual_case == case
        calls.append("original-context")
        return copy.deepcopy(original)

    def validate(actual, x, context):
        assert set(actual) == {"state", "snapshot", "arrays"}
        assert actual["state"] == selected["state"] and x == selected["state"]["x"]
        assert context == original
        calls.append("complete-selected-bundle-schema")
        return True

    monkeypatch.setattr(inputs.launcher, "_dependencies", lambda: d)
    monkeypatch.setattr(inputs.launcher, "_linked", linked)
    monkeypatch.setattr(inputs.launcher, "_audit_link", audit_link)
    monkeypatch.setattr(inputs.native, "build_context", old_context)
    monkeypatch.setattr(inputs.native.contract, "validate_bundle", validate)
    return SimpleNamespace(store=store, case=case, source=source, evidence=evidence,
                           summary=summary,
                           row=row, record=record, report=report, graph=graph, calls=calls,
                           bundle=bundle, cell=cell, selected=selected, certificate=certificate)


def test_selected_context_uses_ack_and_independent_complete_graph_links(context_harness):
    h = context_harness
    result = inputs._context(h.evidence, h.summary, h.source, h.case)
    assert set(result) == {"case", "original_context", "coarse", "selected"}
    assert set(result["coarse"]) == {
        "case_record", "parent_acknowledgement", "cell_result", "independent_reconstruction",
        "selected_bundle", "selected_snapshot", "selected_certificate",
    }
    assert set(result["selected"]) == {"state", "snapshot", "arrays", "certificate"}
    assert result["coarse"]["selected_certificate"] == h.bundle["certificate"]
    assert result["selected"]["certificate"] == h.certificate
    assert result["selected"]["arrays"]["B"].tobytes() == h.selected["arrays"]["B"].tobytes()
    assert h.calls == ["acknowledgement", "original-context",
                       "independent-report-and-full-graph", "complete-selected-bundle-schema"]
    result["selected"]["state"]["x"][1] = 42
    assert h.selected["state"]["x"][1] == 0.5


@pytest.mark.parametrize("key,value", [
    ("schema_version", True), ("status", "failed"), ("index", False), ("index", 1),
    ("construction_completed", 1), ("independent_coarse_verification_pass", 1),
    ("physical_admission", True), ("step4_pass", True), ("case", {"label": "wrong"}),
])
def test_incomplete_or_wrong_typed_case_record_is_not_admitted(context_harness, key, value):
    h = context_harness
    h.record[key] = value
    ref = h.store.json("changed-case", h.record)
    h.summary["cases"][0] = h.row["case_record"] = ref
    with pytest.raises(ValueError):
        inputs._context(h.evidence, h.summary, h.source, h.case)
    assert not h.calls


@pytest.mark.parametrize("key", ["parent_acknowledgement", "independent_reconstruction",
                                 "core_result", "selected_bundle", "selected_snapshot",
                                 "search_report", "counts"])
def test_selected_and_returned_references_cannot_be_substituted(context_harness, key):
    h = context_harness
    h.row[key] = {} if key == "counts" else dict(h.row[key], sha256="f" * 64)
    with pytest.raises(ValueError):
        inputs._context(h.evidence, h.summary, h.source, h.case)


def test_saved_physics_report_must_agree_with_record_changes(context_harness):
    h = context_harness
    h.report["diagnostic_changes"] = {"normal_rms": {"difference": -999}}
    with pytest.raises(ValueError, match="diagnostic"):
        inputs._context(h.evidence, h.summary, h.source, h.case)


def test_graph_counts_must_match_completed_record(context_harness):
    h = context_harness
    h.graph["complete_bundles"] = 13
    with pytest.raises(ValueError, match="work"):
        inputs._context(h.evidence, h.summary, h.source, h.case)


@pytest.mark.parametrize("hook", ["_linked", "_audit_link"])
def test_frozen_ack_or_graph_failure_propagates(context_harness, monkeypatch, hook):
    h = context_harness

    def fail(*args):
        raise ValueError("independent linkage rejected")

    monkeypatch.setattr(inputs.launcher, hook, fail)
    with pytest.raises(ValueError, match="independent linkage"):
        inputs._context(h.evidence, h.summary, h.source, h.case)


def test_full_selected_schema_failure_is_not_replaced_with_seed(context_harness, monkeypatch):
    h = context_harness

    def fail(*args):
        raise ValueError("changed candidate snapshot")

    monkeypatch.setattr(inputs.native.contract, "validate_bundle", fail)
    with pytest.raises(ValueError, match="changed candidate"):
        inputs._context(h.evidence, h.summary, h.source, h.case)


def test_selected_array_identity_is_rechecked_by_canonical_reader(context_harness):
    h = context_harness
    Path(h.bundle["arrays"]["path"]).write_bytes(b"corrupted archive")
    with pytest.raises(ValueError):
        inputs._context(h.evidence, h.summary, h.source, h.case)
