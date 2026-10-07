"""Portable controls for record fidelity, identity and failure preservation."""

import json
import time
from pathlib import Path

import pytest

from fusion_baselines.coil_trajectory import export


def save(run, name, value):
    (run/name).write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


@pytest.fixture
def run(tmp_path):
    root = tmp_path/"run"
    root.mkdir()
    names = [f"coil[{i}]/{axis}{kind}({mode})" for i in range(6) for axis in "xyz"
             for kind, mode in [("c", 0)]+[(k, m) for m in range(1, 6) for k in "sc"]]
    save(root, "seed.json", dict(nbase=6, nfp=2, order=5, names=names,
                                base_coefficients=[[[0.]*11 for _ in range(3)] for _ in range(6)],
                                target_id="synthetic", target_flux=-.01, B2_scale=1.))
    save(root, "inputs.json", dict(kind="normalized-coil-fit", provenance=dict(
        repository=dict(commit="a"*40, dirty=False, path="/private/producer"),
        host=dict(python="synthetic", python_executable="/private/python")),
        sources_before={"/private/code.py": "b"*64}, solver_options=dict(ftol=0.)))
    for index, status in enumerate(("completed", "failed", "attempted")):
        row = dict(index=index, role="search", x=[float(index)]*198, status="attempted")
        save(root, f"trial-{index:05}-attempt.json", row)
        if status == "attempted":
            continue
        row["status"] = status
        if status == "completed":
            row.update(value=1., gradient=[0.]*198, metrics=dict(normal_rms=.2, lengths=[3.]*6))
        else:
            row.update(error="ValueError: invalid flux", rejected_value=2.)
        save(root, f"trial-{index:05}.json", row)
    return root


def read(output):
    return [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]


def test_complete_failed_and_incomplete_records_are_not_acceptance(run, tmp_path):
    output = tmp_path/"records.jsonl"
    summary = export(run, output, "https://example.invalid/immutable/run")
    header, complete, failed, incomplete, footer = read(output)
    assert summary["counts"] == dict(completed=1, failed=1, incomplete=1)
    assert complete["metrics"]["normal_rms"] == .2
    assert failed["metrics"] is None and failed["objective"] is None
    assert failed["error"] == "ValueError: invalid flux" and failed["rejection_value"] == 2.
    assert incomplete["evaluation_status"] == "incomplete" and incomplete["gradient"] is None
    assert all(row["solver_step_status"] == "unknown" for row in (complete, failed, incomplete))
    assert header["producer"]["commit"] == "a"*40 and header["coefficient_unit"] == "m"
    assert header["search_resolution"] is None
    assert footer["artifacts"]["seed.json"]["uri"].endswith("/seed.json")
    assert "/private/" not in output.read_text(encoding="utf-8")
    assert footer["type"] == "export_complete" and not footer["physical_admission"]


def test_stable_identity_is_independent_of_output_and_artifact_location(run, tmp_path):
    left, right = tmp_path/"left.jsonl", tmp_path/"right.jsonl"
    export(run, left)
    export(run, right, "https://example.invalid/other")
    assert read(left)[0]["run_id"] == read(right)[0]["run_id"]
    assert read(left)[1]["candidate_id"] == read(right)[1]["candidate_id"]
    assert read(left)[1]["candidate_id"] != read(left)[2]["candidate_id"]
    attempt = json.loads((run/"trial-00002-attempt.json").read_text(encoding="utf-8"))
    attempt["x"][0] = 99.
    save(run, "trial-00002-attempt.json", attempt)
    changed = tmp_path/"changed.jsonl"
    export(run, changed)
    assert read(left)[0]["run_id"] != read(changed)[0]["run_id"]


def test_verification_stays_separate_and_selected_identity_is_checked(run, tmp_path):
    selected = json.loads((run/"trial-00000.json").read_text(encoding="utf-8"))
    search = dict(selected=selected, status=dict(reason="budget"))
    save(run, "search.json", search)
    save(run, "result.json", dict(search=search, completed=True, physical_admission=False,
                                  fine=[dict(n=128, nodes=512, metrics=dict(normal_rms=.3))]))
    output = tmp_path/"records.jsonl"
    export(run, output)
    rows = read(output)
    assert rows[1]["selected"] and rows[1]["metrics"]["normal_rms"] == .2
    assert rows[-2]["type"] == "verification"
    assert rows[-2]["recorded"]["fine"][0]["metrics"]["normal_rms"] == .3
    assert rows[1]["verification_status"] == "not_evaluated"
    selected["x"][0] = 99.
    save(run, "search.json", search)
    save(run, "result.json", dict(search=search))
    with pytest.raises(ValueError, match="selected candidate"):
        export(run, tmp_path/"bad.jsonl")


@pytest.mark.parametrize("change", ["names", "length", "gradient", "attempt", "status"])
def test_malformed_identity_and_missing_completed_values_fail_closed(run, tmp_path, change):
    name = "seed.json" if change == "names" else "trial-00000.json"
    row = json.loads((run/name).read_text(encoding="utf-8"))
    if change == "names":
        row["names"].reverse()
    elif change == "length":
        row["x"].pop()
    elif change == "gradient":
        row.pop("gradient")
    elif change == "attempt":
        row["x"][0] = .1
    else:
        row["status"] = "accepted"
    save(run, name, row)
    with pytest.raises(ValueError):
        export(run, tmp_path/"bad.jsonl")


def test_output_ceiling_retains_partial_and_never_publishes_complete(run, tmp_path):
    output = tmp_path/"records.jsonl"
    with pytest.raises(ValueError, match="ceiling"):
        export(run, output, max_bytes=1)
    assert not output.exists() and Path(str(output)+".partial").exists()
    with pytest.raises(FileExistsError):
        export(run, output)


def test_existing_output_and_symlink_inputs_are_not_overwritten_or_followed(run, tmp_path):
    output = tmp_path/"records.jsonl"
    output.write_text("preserved", encoding="utf-8")
    with pytest.raises(ValueError, match="fresh"):
        export(run, output)
    assert output.read_text(encoding="utf-8") == "preserved"
    original = run/"trial-00000.json"
    original.rename(run/"hidden.json")
    original.symlink_to(run/"hidden.json")
    with pytest.raises(ValueError, match="regular"):
        export(run, tmp_path/"symlink.jsonl")


def test_order_eight_names_and_gradients_are_preserved(run, tmp_path):
    seed = json.loads((run/"seed.json").read_text(encoding="utf-8"))
    seed.update(order=8, names=[f"coil[{i}]/{axis}{kind}({mode})"
        for i in range(6) for axis in "xyz"
        for kind, mode in [("c", 0)]+[(k, m) for m in range(1, 9) for k in "sc"]],
        base_coefficients=[[[0.]*17 for _ in range(3)] for _ in range(6)])
    save(run, "seed.json", seed)
    for path in run.glob("trial-*.json"):
        row = json.loads(path.read_text(encoding="utf-8"))
        row["x"] = [float(row["index"])]*306
        if "gradient" in row:
            row["gradient"] = [0.]*306
        save(run, path.name, row)
    output = tmp_path/"order8.jsonl"
    export(run, output)
    assert len(read(output)[0]["coefficient_names"]) == 306
    assert len(read(output)[1]["gradient"]) == 306


def test_tiny_new_search_uses_existing_recorder_without_native_calls(run, tmp_path):
    np = pytest.importorskip("numpy")
    from fusion_baselines.coil_fit import Recorder, search

    class Model:
        x0 = np.zeros(198)

        def set_x(self, x):
            self.x = x.copy()

        def evaluate(self, x):
            self.set_x(x)
            if x[0] > .5:
                raise ValueError("synthetic invalid trial")
            return float(1+x.sum()+.5*x@x), 1+x, dict(
                normal_rms=float(1+x.sum()), lengths=[3.]*6,
                sampled_geometry_limits_met=True, current_limit_met=True)

    def minimize(function, x, **kwargs):
        from types import SimpleNamespace

        function(np.ones_like(x))
        function(x-.001)
        return SimpleNamespace(success=True, message="synthetic control")

    recorded = tmp_path/"recorded"
    report = search(Model(), Recorder(recorded, time.monotonic()+5), minimize)
    for name in ("seed.json", "inputs.json"):
        (recorded/name).write_bytes((run/name).read_bytes())
    save(recorded, "search.json", report)
    # A deliberately retained interrupted attempt, separate from the finished search.
    save(recorded, "trial-00012-attempt.json", dict(
        index=12, role="search", status="attempted", x=[0.]*198))
    output = tmp_path/"control.jsonl"
    result = export(recorded, output)
    assert result["counts"] == dict(completed=11, failed=1, incomplete=1)
    rows = read(output)
    assert rows[11]["error"] == "ValueError: synthetic invalid trial"
    assert rows[12]["selected"] and rows[13]["evaluation_status"] == "incomplete"
