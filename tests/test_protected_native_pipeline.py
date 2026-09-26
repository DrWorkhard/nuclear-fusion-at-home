"""Real isolated parent/worker pipeline with deliberately nonphysical arrays."""

import copy
import json
import sys
from pathlib import Path

import pytest
from test_protected_cell_contract import context_fixture

from fusion_baselines.protected_cell_audit import audit_cell
from fusion_baselines.protected_process import supervise_cell
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_json

ROOT = Path(__file__).resolve().parents[1]
CHILD = r'''
import json, os, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path[:0] = [str(root / name) for name in ('src', 'scripts', 'tests')]
from fusion_baselines.protected_run_snapshots import read_json
from run_protected_cell_worker import run_worker
from test_protected_cell_contract import context_fixture
from test_protected_run_cell import Adapter
reference, fd, mode = json.loads(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
config = read_json(reference)
calls = 0
def sources(root):
    global calls
    calls += 1
    source = read_json(config['source'])
    if mode == 'source-drift' and calls == 2:
        source['identity'] = 'changed'
    return source
def context(source, case):
    return context_fixture(case['nbase'], case['method'], case['target'])
def adapter(context, source):
    result = Adapter(context)
    if mode == 'thread-drift':
        original = result.bundle
        def drift(*args):
            bundle = original(*args)
            os.environ['OMP_NUM_THREADS'] = '2'
            return bundle
        result.bundle = drift
    return result
run_worker(reference, fd, bind_sources=sources, build_context=context,
           adapter_factory=adapter, root=root)
if mode == 'nonzero-after-return':
    raise SystemExit(7)
'''


def pipeline(tmp_path, nbase=6, method="N", target="reference", mode="normal"):
    context = context_fixture(nbase, method, target)
    source = SnapshotStore(tmp_path / "source").json(
        "manifest", dict(synthetic=True, identity="unchanged")
    )
    output = tmp_path / "parent-cell"
    checked = []

    def config(started, parent_pid, threads):
        return dict(
            schema_version=1, kind="protected-cell-worker-config",
            case=copy.deepcopy(context["case"]), source=source,
            output=str(output / "worker"), parent_pid=parent_pid,
            started_monotonic=started, threads=threads,
        )

    def command(reference, fd):
        return [sys.executable, "-c", CHILD, str(ROOT), json.dumps(reference), str(fd), mode]

    def validate(reference, configuration):
        envelope = read_json(reference)
        assert envelope["case"] == configuration["case"] == context["case"]
        verdict = audit_cell(envelope["cell_result"], context)
        checked.append(verdict)
        return verdict["integration_integrity_pass"] is True

    reference = supervise_cell(
        config, command, output, validate_return=validate,
        source_check=lambda configuration: read_json(configuration["source"])
        == dict(synthetic=True, identity="unchanged"),
    )
    return read_json(reference), checked


@pytest.mark.parametrize("nbase", [6, 8])
@pytest.mark.parametrize("method", ["N", "V"])
@pytest.mark.parametrize("target", ["reference", "selected"])
def test_eight_real_subprocess_paths_acknowledge_only_synthetic_completion(
    tmp_path, nbase, method, target
):
    acknowledgement, checked = pipeline(tmp_path, nbase, method, target)
    assert acknowledgement["parent_acknowledged"] is True
    assert len(checked) == 1 and checked[0]["integration_integrity_pass"] is True
    assert acknowledgement["physical_admission"] is acknowledgement["step4_pass"] is False
    assert acknowledgement["independent_physical_audit_pass"] is False
    envelope = read_json(acknowledgement["returned_result"])
    result = read_json(envelope["cell_result"])
    assert result["producer_complete"] is True
    assert envelope["worker_pid"] == acknowledgement["worker_pid"]
    assert envelope["parent_pid"] == acknowledgement["parent_pid"]
    messages = [read_json(ref)["message"] for ref in acknowledgement["control_observations"]]
    assert [event["kind"] for event in messages] == [
        "search_started", "search_ended", "returned_result"
    ]
    assert messages[-1]["reference"] == acknowledgement["returned_result"]


@pytest.mark.parametrize("mode", ["source-drift", "thread-drift", "nonzero-after-return"])
def test_real_worker_failures_cannot_become_parent_acknowledgements(tmp_path, mode):
    with pytest.raises(ValueError):
        pipeline(tmp_path, mode=mode)
    output = tmp_path / "parent-cell"
    assert not (output / "parent/acknowledgement.json").exists()
    assert (output / "worker-stdout.log").exists()
    if mode != "thread-drift":
        assert (output / "worker/cell-data/result.json").exists()
    if mode == "nonzero-after-return":
        assert (output / "worker/worker-data/returned.json").exists()
