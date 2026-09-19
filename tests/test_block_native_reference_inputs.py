"""Pure source-admission controls; no new field or geometry computation."""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import block_native_reference_inputs as binder  # noqa: E402


def report():
    return dict(
        schema_version=1,
        status="completed",
        kind="synthetic-resource-qualification",
        source_unchanged=True,
        source_before=dict(example="synthetic"),
        source_after=dict(example="synthetic"),
        all_pass=False,
        scope=binder.legacy.SCOPE,
        matrix=binder.legacy.matrix(),
        rows=list(range(8)),
        limits=dict(
            wall_seconds=120.0,
            peak_rss_bytes=1610612736,
            parent_poll_seconds=0.5,
            termination_grace_seconds=5,
        ),
        pairs=[dict(nbase=n, ncoil=q, all_pass=True) for n in (6, 8) for q in (256, 512)],
    )


def test_complete_negative_summary_remains_negative():
    original = report()
    binder.summary_gate(original)
    assert original["all_pass"] is False
    assert binder.matrix() == [
        dict(label=f"n{n}-q{q}-block-native", nbase=n, ncoil=q, order=m, backend="block-native")
        for n, m in ((6, 5), (8, 7))
        for q in (256, 512)
    ]


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", True),
        ("source_unchanged", 1),
        ("all_pass", True),
        ("source_after", {}),
        ("status", "partial"),
        ("rows", [0]),
        ("matrix", []),
        ("pairs", []),
        ("limits", {}),
    ],
)
def test_changed_or_incomplete_predecessor_summary_rejected(key, value):
    candidate = copy.deepcopy(report())
    candidate[key] = value
    with pytest.raises(ValueError):
        binder.summary_gate(candidate)


def test_each_pair_must_pass_not_just_overall_arithmetic():
    candidate = copy.deepcopy(report())
    candidate["pairs"][2]["all_pass"] = False
    with pytest.raises(ValueError, match="mathematical pairs"):
        binder.summary_gate(candidate)


def test_new_root_revision_is_not_a_numerical_source_change():
    old = dict(repository=dict(commit="old"), code=[dict(sha256="same")], packages=dict(numpy="x"))
    current = copy.deepcopy(old)
    current["repository"] = dict(commit="additive-new")
    assert binder.numerical_environment(current, old) == dict(
        code=[dict(sha256="same")], packages=dict(numpy="x")
    )
    current["packages"]["numpy"] = "changed"
    with pytest.raises(ValueError, match="numerical bytes"):
        binder.numerical_environment(current, old)


def test_recursive_reference_alias_hash_and_exact_byte_count(tmp_path):
    path = tmp_path / "bound.json"
    binder.legacy.save(path, dict(synthetic=True))
    ref = binder.legacy.ref(path)
    assert len(binder.check_references(dict(a=ref, b=[ref]))) == 1
    bad = dict(ref, bytes=True)
    with pytest.raises(ValueError, match="byte count"):
        binder.check_references(bad)
    with pytest.raises(ValueError, match="conflicting"):
        binder.check_references([ref, dict(ref, sha256="0" * 64)])
    binder.legacy.save(path, dict(synthetic=False))
    with pytest.raises(ValueError, match="bytes changed"):
        binder.check_references(ref)


def test_nonabsolute_or_incomplete_reference_rejected(tmp_path):
    ref = dict(path="relative", sha256="0" * 64, bytes=0)
    with pytest.raises(ValueError, match="absolute"):
        binder.check_references(ref)
    ref["path"] = str(tmp_path / "missing")
    del ref["bytes"]
    with pytest.raises(ValueError, match="complete byte"):
        binder.check_references(ref)
