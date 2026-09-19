"""Pure admission controls for immutable geometry and resource predecessors."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import clear_coil_field_start_inputs as binder  # noqa: E402


def geometry_documents():
    source = {"synthetic": True}
    zero = dict(
        field_calls=0,
        gradient_calls=0,
        equilibrium_solves=0,
        field_pass=False,
        transfer_pass=False,
        step4_pass=False,
    )
    audit = dict(
        status="completed",
        phase="geometry_initialization",
        source=source,
        all_pass=True,
        all_twelve_sets_checked=True,
        arithmetic_and_source_pass=True,
        both_classes_pass=True,
        geometry_pass=True,
        selected=dict(n6="n6-shape-d100mm", n8="n8-shape-d100mm"),
        surface_checks=[dict(passed=True) for _ in range(6)],
        work=dict(attempted_lps=168, original_lps=84, repeated_lps=84, **zero),
        sets=[],
        **zero,
    )
    run = dict(
        status="completed",
        source=source,
        geometry_pass=False,
        selected=None,
        attempted_lps=168,
        sets=[],
        **zero,
    )
    for case in binder.geometry_cases():
        coils = [
            dict(
                base_index=i,
                available_geometry=True,
                exact_repeat=True,
                lp_certificates=[dict(solved=True, passed=True) for _ in range(2)],
                export_transfer={
                    key: True
                    for key in (
                        "support_pass",
                        "length_pass",
                        "curvature_pass",
                        "plasma_pass",
                        "controlled_projection_self_disjoint",
                    )
                },
            )
            for i in range(case["nbase"])
        ]
        distances = [
            {
                key: True
                for key in (
                    "coil_pass",
                    "plasma_pass",
                    "sampled_length_pass",
                    "sampled_curvature_pass",
                )
            }
            for _ in range(6)
        ]
        audit["sets"].append(
            dict(
                case=case,
                coils=coils,
                distances=distances,
                available_geometry=True,
                geometry_pass=True,
                analytic_coil_lower=0.10,
            )
        )
        run["sets"].append(
            dict(
                case=case,
                snapshot=dict(
                    path="/synthetic/seed", sha256=binder.SEED_HASHES.get(case["label"], "0" * 64)
                ),
            )
        )
    return audit, run, source


def resource_documents():
    source = dict(repository=dict(commit="old"), synthetic=True)
    run = dict(
        source_before=source,
        source_after=source,
        producer_checks_pass=True,
        bounded_reference_pass=False,
    )
    audit = dict(
        status="completed",
        arithmetic_and_source_pass=True,
        bounded_reference_pass=True,
        all_pass=True,
        legacy_all_pass=False,
        legacy_sparse_pass=True,
        source=source,
        compared_quantities=336,
        field_calls=0,
        target_data_reads=0,
        equilibrium_solves=0,
        startup_pass=False,
        physical_seed_pass=False,
        search_allowed=False,
        transfer_pass=False,
        step4_pass=False,
        workers=[],
        legacy_workers=[],
        legacy_pairs=[dict(passed=True)] * 4,
        comparisons=[dict(passed=True, comparisons=[dict(passed=True)] * 42) for _ in range(8)],
    )
    for case in binder.block_inputs.matrix():
        audit["workers"].append(
            dict(
                case=case,
                passed=True,
                mathematical_pass=True,
                resource_pass=True,
                changed_copies_pass=True,
                state_count=13,
                kernels=dict(passed=True),
                repetitions=[True] * 3,
                finite_differences=[dict(passed=True)] * 8,
            )
        )
    for case in binder.block_inputs.legacy.matrix():
        passed = case["label"] not in binder.block_inputs.DENSE_FAILURES
        audit["legacy_workers"].append(
            dict(case=case, mathematical_pass=True, resource_pass=passed, passed=passed)
        )
    current = copy.deepcopy(source)
    current["repository"]["commit"] = "additive-new"
    return audit, run, current


def test_geometry_requires_and_returns_both_exact_selected_snapshots():
    audit, run, source = geometry_documents()
    result = binder.geometry_gate(audit, run, source)
    assert set(result) == set(binder.SEED_HASHES)
    assert [s["geometry_report_index"] for s in result.values()] == [3, 9]
    assert all(
        s["snapshot"] == run["sets"][s["geometry_report_index"]]["snapshot"]
        for s in result.values()
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda a, r, s: a.update(all_pass=1),
        lambda a, r, s: a.update(geometry_pass=False),
        lambda a, r, s: a.update(selected=dict(n6="n6-circle-d100mm", n8="n8-shape-d100mm")),
        lambda a, r, s: a["sets"][0].update(geometry_pass=False),
        lambda a, r, s: a["sets"][3].update(analytic_coil_lower=0.059),
        lambda a, r, s: a["sets"][3]["coils"][0].update(exact_repeat=False),
        lambda a, r, s: a["sets"][3]["coils"][0]["lp_certificates"][1].update(passed=False),
        lambda a, r, s: a["sets"][3]["coils"][0]["export_transfer"].update(plasma_pass=False),
        lambda a, r, s: a["sets"][3]["coils"][0]["export_transfer"].update(
            controlled_projection_self_disjoint=False
        ),
        lambda a, r, s: a["sets"][3]["distances"][5].update(coil_pass=False),
        lambda a, r, s: a["surface_checks"][5].update(passed=False),
        lambda a, r, s: r["sets"][3]["snapshot"].update(sha256="0" * 64),
        lambda a, r, s: r.update(geometry_pass=True),
        lambda a, r, s: r.update(field_calls=True),
        lambda a, r, s: a["work"].update(repeated_lps=83),
        lambda a, r, s: a.update(source={}),
        lambda a, r, s: a["sets"].pop(),
    ],
)
def test_geometry_global_pass_cannot_hide_individual_failures(mutation):
    audit, run, source = geometry_documents()
    mutation(audit, run, source)
    with pytest.raises(ValueError):
        binder.geometry_gate(audit, run, source)


def test_positive_bounded_reference_preserves_negative_dense_history():
    audit, run, current = resource_documents()
    binder.block_gate(audit, run, current)
    assert audit["legacy_all_pass"] is False
    assert run["bounded_reference_pass"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda a, r, c: a.update(bounded_reference_pass=False),
        lambda a, r, c: a.update(legacy_all_pass=True),
        lambda a, r, c: a.update(legacy_sparse_pass=False),
        lambda a, r, c: a.update(field_calls=True),
        lambda a, r, c: a.update(startup_pass=True),
        lambda a, r, c: a["workers"][3].update(resource_pass=False),
        lambda a, r, c: a["workers"][3]["kernels"].update(passed=False),
        lambda a, r, c: a["workers"][0]["finite_differences"][0].update(passed=False),
        lambda a, r, c: a["workers"][0].update(repetitions=[True, False, True]),
        lambda a, r, c: a["comparisons"][0]["comparisons"][0].update(passed=False),
        lambda a, r, c: a["comparisons"].pop(),
        lambda a, r, c: a["legacy_workers"][2].update(resource_pass=True),
        lambda a, r, c: a["legacy_workers"][1].update(passed=False),
        lambda a, r, c: a["legacy_pairs"][0].update(passed=False),
        lambda a, r, c: r.update(bounded_reference_pass=True),
        lambda a, r, c: r.update(source_after={}),
        lambda a, r, c: c.update(synthetic=False),
    ],
)
def test_resource_individual_gates_and_old_failure_identity_required(mutation):
    audit, run, current = resource_documents()
    mutation(audit, run, current)
    with pytest.raises(ValueError):
        binder.block_gate(audit, run, current)


def test_reference_supports_old_hash_and_new_byte_schemas(tmp_path):
    path = tmp_path / "bound"
    path.write_bytes(b"immutable")
    ref = binder.reference(path)
    assert binder.checked(ref) == path
    full = dict(ref, bytes=9)
    assert binder.checked(full) == path
    assert len(binder.bind_tree(dict(old=ref, new=[full]))) == 1
    with pytest.raises(ValueError, match="byte count"):
        binder.checked(dict(ref, bytes=True))
    with pytest.raises(ValueError, match="bytes changed"):
        binder.checked(dict(ref, sha256="0" * 64))
    with pytest.raises(ValueError, match="absolute"):
        binder.checked(dict(ref, path="relative"))


def test_typed_source_identity_rejects_numeric_boolean_aliases():
    assert binder.same(dict(a=[1, True, 1.0]), dict(a=[1, True, 1.0]))
    assert not binder.same(dict(a=[1, True, 1.0]), dict(a=[True, 1, 1]))


def test_transitive_json_to_raw_bytes_are_checked_not_only_top_level_flags(tmp_path):
    raw = tmp_path / "raw.npz"
    raw.write_bytes(b"immutable numerical fixture")
    worker = tmp_path / "worker.json"
    worker.write_text(json.dumps(dict(arrays=binder.reference(raw))))
    result = tmp_path / "result.json"
    result.write_text(json.dumps(dict(worker=binder.reference(worker))))
    outer = dict(rows=[binder.reference(result)], all_pass=True)
    assert len(binder.bind_tree(outer)) == 3
    raw.write_bytes(b"changed numerical fixture")
    with pytest.raises(ValueError, match="source bytes changed"):
        binder.bind_tree(outer)


def test_transitive_repeated_json_reference_expands_once(tmp_path, monkeypatch):
    raw = tmp_path / "raw.bin"
    raw.write_bytes(b"numerical fixture")
    worker = tmp_path / "worker.json"
    worker.write_text(json.dumps(dict(arrays=binder.reference(raw))))
    ref = binder.reference(worker)
    calls = []
    original = binder.checked

    def track(item):
        calls.append(item["path"])
        return original(item)

    monkeypatch.setattr(binder, "checked", track)
    assert len(binder.bind_tree(dict(first=ref, second=[ref]))) == 2
    assert calls.count(str(raw)) == 1


def test_historical_source_metadata_is_hashed_without_global_old_code_replay(tmp_path):
    ancestor = tmp_path / "historical-source.json"
    ancestor.write_text(
        json.dumps(dict(old_code=dict(path="/historical/not-the-current-version", sha256="0" * 64)))
    )
    document = dict(source=dict(accepted_ancestor=binder.reference(ancestor)))
    assert len(binder.bind_tree(document)) == 1
    # This is not permission to hide missing current raw data behind normal rows.
    with pytest.raises(FileNotFoundError):
        binder.bind_tree(dict(rows=[binder.reference(ancestor)]))
    ancestor.write_text("{}")
    with pytest.raises(ValueError, match="source bytes changed"):
        binder.bind_tree(document)


def test_historical_byte_binding_requires_commit_and_original_bytes(tmp_path, monkeypatch):
    path = tmp_path / "fixture.json"
    path.write_bytes(b"{}")
    calls = []
    monkeypatch.setattr(binder, "require_committed", lambda root, name: calls.append(name))
    monkeypatch.setattr(binder.subprocess, "check_output", lambda *a, **k: b"{}")
    ref = binder.historical(tmp_path, path.name, "fixed")
    assert calls == [path] and ref == binder.reference(path)
    monkeypatch.setattr(binder.subprocess, "check_output", lambda *a, **k: b"[]")
    with pytest.raises(ValueError, match="historical evidence bytes"):
        binder.historical(tmp_path, path.name, "fixed")


def test_workflow_sources_require_all_new_code_committed(tmp_path, monkeypatch):
    bound = dict(synthetic="read-only predecessors")
    monkeypatch.setattr(binder, "prerequisites", lambda root: bound)
    calls = []
    monkeypatch.setattr(binder, "require_committed", lambda root, path: calls.append(path))
    monkeypatch.setattr(binder, "reference", lambda path: dict(path=str(path), sha256="0" * 64))
    monkeypatch.setattr(binder, "git_state", lambda root: dict(commit="new", dirty=False))
    source = binder.sources(tmp_path)
    assert calls == [tmp_path / name for name in (binder.PROTOCOL, *binder.CODE)]
    assert source["synthetic"] == bound["synthetic"]
    assert source["repository"] == dict(commit="new", dirty=False)
    assert len(source["code"]) == 6


def test_uncommitted_workflow_is_not_admitted_by_positive_predecessors(tmp_path, monkeypatch):
    monkeypatch.setattr(binder, "prerequisites", lambda root: dict(positive_predecessors=True))

    def reject(root, path):
        raise ValueError("not committed")

    monkeypatch.setattr(binder, "require_committed", reject)
    with pytest.raises(ValueError, match="not committed"):
        binder.sources(tmp_path)
