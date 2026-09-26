"""Read-only archived coarse intake, not permission to execute the fine phase.

Rehash the entire inline archived source manifest and validate active numerical
dependencies. Preserve historical repository records verbatim. Prior-qualified
ancestry behind referenced reports remains byte-bound, not generically reopened;
three explicitly versioned registration edges are checked against Git objects.
Per-case contexts freshly verify the acknowledged complete coarse graph and its
already recorded independent reconstruction, without recomputing any physics.
"""

import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import protected_native_inputs as native
import run_protected_coil_fit as launcher

from fusion_baselines import protected_fine_plan as plan
from fusion_baselines.protected_run_snapshots import read_arrays, read_json
from fusion_baselines.protected_search_journal import _encode, _unique_object
from fusion_baselines.provenance import sha256_file

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = "evidence/protected-coil-fit-coarse-v1.json"
EVIDENCE_COMMIT = "3b31695"
EVIDENCE_SHA256 = "f95059058824a206c4a349765bc098a573dca2e13f33258d677c20a2f709a2f6"
EXECUTION_COMMIT = "2015ac5e6f79600497aafc731dbcc444c2a43962"
REGISTRATIONS = (
    "evidence/protected-cell-synthetic-v1.json",
    "evidence/protected-native-plumbing-v1.json",
    "evidence/protected-saved-physics-v1.json",
)
SCOPE = dict(
    fine_execution_authorized=False,
    fine_implementation_qualified=False,
    physical_admission=False,
    fine_grid_acceptance=False,
    step4_pass=False,
    sota_advance=False,
    ms1_reached=False,
)


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _same(actual, expected, message):
    _need(_encode(actual) == _encode(expected), message)


def _git(root, *args, text=True):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True,
        text=text, timeout=30,
    ).stdout


def _repository(root):
    """A failed git status is never interpreted as a clean checkout."""
    return dict(
        path=_git(root, "rev-parse", "--show-toplevel").strip(),
        available=True,
        commit=_git(root, "rev-parse", "HEAD").strip(),
        branch=_git(root, "branch", "--show-current").strip(),
        dirty=bool(_git(root, "status", "--porcelain")),
    )


def _checked(reference):
    _need(
        type(reference) is dict
        and set(reference) in ({"path", "sha256"}, {"path", "sha256", "bytes"})
        and all(type(key) is str for key in reference)
        and type(reference["path"]) is str and Path(reference["path"]).is_absolute()
        and type(reference["sha256"]) is str
        and re.fullmatch(r"[0-9a-f]{64}", reference["sha256"]),
        "exact absolute archived reference required",
    )
    path = Path(reference["path"])
    _need(path.is_file() and not path.is_symlink(), "regular nonsymlink archived file required")
    if "bytes" in reference:
        _need(type(reference["bytes"]) is int and reference["bytes"] >= 0
              and path.stat().st_size == reference["bytes"], "exact archived byte count")
    _need(sha256_file(path) == reference["sha256"], "archived bytes changed: " + str(path))
    return path


def _reference(path):
    path = Path(path)
    return dict(path=str(path), sha256=sha256_file(path), bytes=path.stat().st_size)


def _load(reference):
    path = _checked(reference)
    _need(path.stat().st_size <= 8 * 1024**2, "bounded archived JSON required")
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    _encode(value)  # Reject nonfinite values/types, without demanding old JSON formatting.
    return value


def _walk(value):
    if type(value) is dict:
        yield value
        for child in value.values():
            yield from _walk(child)
    elif type(value) is list:
        for child in value:
            yield from _walk(child)


def _inline_sources(source):
    refs, count = {}, 0
    for row in _walk(source):
        if "path" in row and "sha256" in row:
            count += 1
            path = str(_checked(row))
            if path in refs:
                _need(refs[path]["sha256"] == row["sha256"], "conflicting archived aliases")
            # Retain the caller's verified identity, never substitute a second
            # read's possibly changed digest for this archived reference.
            refs[path] = dict(path=path, sha256=row["sha256"],
                              bytes=row.get("bytes", Path(path).stat().st_size))
    return refs, count


def _repositories(root, source):
    projects, externals, ancestors = [], [], set()
    for row in _walk(source):
        if "available" not in row or "commit" not in row or "path" not in row:
            continue
        _need(set(row) == {"path", "available", "commit", "branch", "dirty"}
              and type(row["path"]) is str and row["available"] is True
              and row["dirty"] is False and type(row["branch"]) is str
              and type(row["commit"]) is str
              and re.fullmatch(r"[0-9a-f]{40}", row["commit"]),
              "exact available clean archived repository identity")
        if row["path"] == str(root):
            if row["commit"] not in ancestors:
                _git(root, "merge-base", "--is-ancestor", row["commit"], EXECUTION_COMMIT)
                ancestors.add(row["commit"])
            projects.append(copy.deepcopy(row))
        else:
            _need(row["path"] == str(root / "external/simsopt"),
                  "only the declared active Simsopt checkout in inline manifest")
            _same(_repository(Path(row["path"])), row, "unchanged active Simsopt repository")
            externals.append(copy.deepcopy(row))
    _need(projects and externals, "historical project and active native repositories required")
    return dict(project_records=len(projects), active_native_records=len(externals),
                historical_project_commits=sorted(ancestors),
                historical_project_records_preserved=True,
                current_project_commit_substituted=False)


def _origin(name):
    spec = importlib.util.find_spec(name)
    _need(spec is not None and type(spec.origin) is str, "active import origin required: " + name)
    return Path(spec.origin).resolve()


def _environment(root, source, refs):
    package_root, binary = _origin("simsopt").parent, _origin("simsoptpp")
    scipy_root = _origin("scipy").parent
    full_records, version_records = 0, 0
    versions = {}
    for row in _walk(source):
        for key in ("packages", "versions"):
            if key in row:
                expected = row[key]
                _need(type(expected) is dict and bool(expected), "declared package versions")
                for name, version in expected.items():
                    _need(type(name) is str and type(version) is str, "plain package version")
                    actual = importlib.metadata.version(name)
                    _need(actual == version, "active numerical package changed: " + name)
                    _need(name not in versions or versions[name] == version,
                          "conflicting archived package versions")
                    versions[name] = actual
                version_records += 1
        if "python_version" in row:
            full_records += 1
            _same(row["python_version"], sys.version, "exact active Python version")
            _same(row["platform"], sys.platform, "exact active Python platform")
            _same(row["python"]["path"], str(Path(sys.executable).resolve()),
                  "exact active Python executable")
            _same(row["native_binary"]["path"], str(binary), "exact active native binary origin")
            _need(type(row.get("installed_native_python")) is list
                  and bool(row["installed_native_python"]), "installed native Python pins")
            _same(row["installed_native_python"][0]["path"], str(package_root / "__init__.py"),
                  "exact active Simsopt package origin")
        python = row.get("python")
        if type(python) is dict and "executable" in python:
            _same(python, dict(executable=str(Path(sys.executable).resolve()), version=sys.version),
                  "geometry Python interpreter identity")
    _need(full_records > 0, "complete active numerical environment records required")
    checked_installed = set()
    checkout = root / "external/simsopt/src/simsopt"
    for name, reference in refs.items():
        path = Path(name)
        if path.is_relative_to(checkout):
            installed = package_root / path.relative_to(checkout)
            _need(sha256_file(installed) == reference["sha256"],
                  "active installed source differs from pinned checkout: " + str(installed))
            checked_installed.add(str(installed))
        elif "/site-packages/simsopt/" in name:
            relative = name.split("/site-packages/simsopt/", 1)[1]
            _same(name, str(package_root / relative), "active installed native source path")
            checked_installed.add(name)
        elif "/site-packages/scipy/" in name:
            relative = name.split("/site-packages/scipy/", 1)[1]
            _same(name, str(scipy_root / relative), "active installed SciPy source path")
    return dict(full_environment_records=full_records, version_records=version_records,
                packages=versions, python_executable=str(Path(sys.executable).resolve()),
                python_version=sys.version, platform=sys.platform,
                simsopt_origin=str(package_root / "__init__.py"), native_origin=str(binary),
                installed_native_files=sorted(checked_installed))


def _registrations(root, refs):
    result = []
    for name in REGISTRATIONS:
        _need(str(root / name) in refs, "pinned qualification report required: " + name)
        edge = _load(refs[str(root / name)])["registration"]
        _need(type(edge) is dict and set(edge) in (
            {"path", "sha256", "bytes", "commit"},
            {"path", "sha256", "bytes", "commit", "initial_commit"}),
            "exact recorded registration edge")
        path, commit = edge["path"], edge["commit"]
        _need(type(path) is str and not Path(path).is_absolute() and ".." not in Path(path).parts
              and path.startswith("docs/") and type(commit) is str
              and re.fullmatch(r"[0-9a-f]{7,40}", commit)
              and type(edge["bytes"]) is int and edge["bytes"] > 0
              and type(edge["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", edge["sha256"]),
              "typed repository-relative historical registration")
        _git(root, "merge-base", "--is-ancestor", commit, EXECUTION_COMMIT)
        original = _git(root, "show", f"{commit}:{path}", text=False)
        _need(len(original) == edge["bytes"]
              and hashlib.sha256(original).hexdigest() == edge["sha256"],
              "exact commit-pinned registration bytes")
        if "initial_commit" in edge:
            initial = edge["initial_commit"]
            _need(type(initial) is str and re.fullmatch(r"[0-9a-f]{40}", initial),
                  "exact initial registration commit")
            _git(root, "merge-base", "--is-ancestor", initial, commit)
        result.append(dict(report=refs[str(root / name)], registration=copy.deepcopy(edge)))
    return result


def _anchor(root):
    reference = _reference(root / EVIDENCE)
    _need(reference["sha256"] == EVIDENCE_SHA256, "fixed coarse evidence SHA256")
    _need(_git(root, "show", f"{EVIDENCE_COMMIT}:{EVIDENCE}", text=False)
          == _checked(reference).read_bytes(), "fixed committed coarse evidence bytes")
    evidence = _load(reference)
    _inline_sources(evidence)
    native.previous._fields(
        evidence, dict(schema_version=1, kind="protected-coil-fit-coarse-evidence",
                       status="completed", construction_and_coarse_verification_pass=True,
                       execution_source_commit=EXECUTION_COMMIT, command_exit_code=0,
                       clean_source_before_after=True, fine_phase="required-not-run"),
        "complete pinned coarse study evidence",
    )
    _same(evidence["limits"], dict(launcher.SCOPE, external_peer_review=False),
          "coarse evidence preserves all scientific limits")
    summary = read_json(evidence["summary"])
    native.previous._fields(
        summary, dict(schema_version=1, kind="protected-coil-fit-construction",
                      status="completed", matrix=plan.cases(), completed_cases=8,
                      all_eight_constructions_complete=True,
                      all_eight_independent_coarse_verifications_pass=True,
                      failure_policy="stop-without-retry", fine_phase="required-not-run",
                      **launcher.SCOPE), "explicitly returned complete eight-case summary",
    )
    _same(summary["source_before"], evidence["source_before"], "initial coarse source reference")
    _same(summary["source_after"], evidence["source_after"], "final coarse source reference")
    source = read_json(evidence["source_before"])
    _same(source, read_json(evidence["source_after"]), "identical archived before/after source")
    _same(source["repository"]["commit"], EXECUTION_COMMIT, "original construction commit")
    _same(summary["confirmed_work"], evidence["confirmed_work"], "complete coarse work identity")
    _need(type(evidence["cases"]) is list and len(evidence["cases"]) == 8
          and type(summary["cases"]) is list and len(summary["cases"]) == 8,
          "all eight explicit case references required")
    for case, row, case_ref in zip(plan.cases(), evidence["cases"], summary["cases"], strict=True):
        _same(row["case"], case, "original ordered coarse case")
        _same(row["case_record"], case_ref, "explicit returned case reference")
    return reference, evidence, summary, source


def _context(evidence, summary, source, case):
    index = plan.cases().index(case)
    row = evidence["cases"][index]
    record = read_json(summary["cases"][index])
    native.previous._fields(
        record, dict(schema_version=1, kind="protected-pilot-case", status="completed",
                     index=index, case=case, construction_completed=True,
                     independent_coarse_verification_pass=True, **launcher.SCOPE),
        "completed exact coarse case record",
    )
    for key in ("parent_acknowledgement", "independent_reconstruction", "counts"):
        _same(record[key], row[key], "coarse evidence/case linkage: " + key)
    _same(record["cell_result"], row["core_result"], "coarse selected cell reference")
    d = launcher._dependencies()
    cell_output = Path(evidence["summary"]["path"]).parent / f"cell-{index:02d}-{case['label']}"
    _, cell_ref = launcher._linked(d, record["parent_acknowledgement"], case, source, cell_output)
    _same(cell_ref, record["cell_result"], "acknowledged exact cell result")
    original = native.build_context(launcher._native(source), case)
    report, graph = launcher._audit_link(
        d, record["independent_reconstruction"], cell_ref, case, source, original)
    _same(record["diagnostic_changes"], report["diagnostic_changes"], "recorded diagnostic changes")
    counts = dict(native_requests=graph["counts"]["native"]["completed"],
                  bundles=graph["complete_bundles"],
                  certificates=sum(r["completed"] for r in graph["counts"]["certificate"].values()))
    _same(record["counts"], counts, "graph-verified coarse work counts")
    cell = read_json(cell_ref)
    _same(cell["selected_bundle"], row["selected_bundle"], "fixed selected bundle reference")
    _same(cell["search_report"], row["search_report"], "fixed selected search report")
    bundle = read_json(cell["selected_bundle"])
    _same(bundle["snapshot"], row["selected_snapshot"], "fixed selected coarse snapshot")
    selected = dict(state=bundle["state"], snapshot=read_json(bundle["snapshot"]),
                    arrays=read_arrays(bundle["arrays"]))
    native.contract.validate_bundle(selected, selected["state"]["x"], original)
    selected["certificate"] = read_json(bundle["certificate"])
    _need(selected["certificate"]["result"]["certified"] is True,
          "selected cumulative original-seed certificate required")
    coarse = dict(case_record=summary["cases"][index],
                  parent_acknowledgement=record["parent_acknowledgement"],
                  cell_result=cell_ref,
                  independent_reconstruction=record["independent_reconstruction"],
                  selected_bundle=cell["selected_bundle"], selected_snapshot=bundle["snapshot"],
                  selected_certificate=bundle["certificate"])
    return copy.deepcopy(
        dict(case=case, original_context=original, coarse=coarse, selected=selected))


def archive(root=ROOT):
    """Recheck pinned archive/current dependencies, preserving all old source data.

    A dirty current checkout is recorded, not authorized for execution. This API
    is deliberately usable for implementation qualification before a fine gate
    exists. Complete per-case saved graphs are independently reopened here.
    """
    root = Path(root).resolve()
    current = _repository(root)
    reference, evidence, summary, source = _anchor(root)
    _git(root, "merge-base", "--is-ancestor", EXECUTION_COMMIT, current["commit"])
    refs, count = _inline_sources(source)
    repositories = _repositories(root, source)
    environment = _environment(root, source, refs)
    registrations = _registrations(root, refs)
    contexts = [_context(evidence, summary, source, case) for case in plan.cases()]
    _same(_repository(root), current, "stable current intake provenance")
    return dict(
        schema_version=1, kind="protected-fine-archived-coarse-inputs", root=str(root),
        evidence=reference, summary=evidence["summary"], source_before=evidence["source_before"],
        source_after=evidence["source_after"], archived_source=copy.deepcopy(source),
        cases=[context["coarse"] for context in contexts],
        checked_inputs=dict(inline_reference_occurrences=count, unique_inline_files=len(refs),
                            repositories=repositories, active_environment=environment,
                            historical_registration_edges=registrations,
                            complete_coarse_graphs_checked=8,
                            independent_physics_recomputed=False,
                            prior_qualified_ancestry_reexpanded=False),
        current_provenance=current, **SCOPE,
    )


def build_context(archived, case):
    """Fresh private selected-candidate context; no source recapture or new physics."""
    plan.validate_case(case)
    _need(type(archived) is dict and set(archived) == {
        "schema_version", "kind", "root", "evidence", "summary", "source_before", "source_after",
        "archived_source", "cases", "checked_inputs", "current_provenance", *SCOPE,
    }, "exact archived-input envelope required")
    native.previous._fields(archived, dict(schema_version=1,
        kind="protected-fine-archived-coarse-inputs", **SCOPE), "closed fine intake scope")
    _need(type(archived["root"]) is str and Path(archived["root"]).is_absolute(),
          "absolute original archive root")
    root = Path(archived["root"]).resolve()
    reference, evidence, summary, source = _anchor(root)
    for key, value in dict(evidence=reference, summary=evidence["summary"],
                           source_before=evidence["source_before"],
                           source_after=evidence["source_after"], archived_source=source).items():
        _same(archived[key], value, "immutable archived identity: " + key)
    _need(type(archived["cases"]) is list and len(archived["cases"]) == 8,
          "eight archived case bindings")
    result = _context(evidence, summary, source, case)
    _same(archived["cases"][plan.cases().index(case)], result["coarse"],
          "archived selected-case binding")
    return result
