"""One real fine subprocess pipeline with explicitly nonphysical field fixtures.

The qualified launcher, parent, pipe control, worker, native-adapter orchestration,
cell, request ledger, canonical storage and complete graph auditor run together.
Only admission, model calculations, direct geometry and physical reconstruction
are substituted. This test cannot authorize or establish any physical result.
"""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_protected_fine as launch  # noqa: E402
from test_protected_fine_launcher import fixture  # noqa: E402
from test_protected_fine_native import inputs  # noqa: E402

from fusion_baselines import protected_fine_process as process  # noqa: E402
from fusion_baselines.protected_fine_geometry import expected_work  # noqa: E402
from fusion_baselines.protected_fine_graph import audit_fine_graph  # noqa: E402
from fusion_baselines.protected_run_snapshots import read_json  # noqa: E402

CHILD = r"""
import copy,json,sys
from pathlib import Path
root=Path(sys.argv[3])
sys.path[:0]=[str(root/name) for name in ('src','scripts','tests')]
import pytest
import test_protected_fine_native as fixtures
from test_protected_fine_cell import Geometry,request
from fusion_baselines import protected_fine_native as native
from fusion_baselines.protected_run_snapshots import read_json
from run_protected_fine_worker import run_worker
reference=json.loads(sys.argv[1]); config=read_json(reference)
patch=pytest.MonkeyPatch()
patch.setattr(fixtures.Model,'request',request)
context,archive,calls=fixtures.setup(patch)
context['selected']['certificate']=dict(result=dict(certified=True),synthetic=True)
bound=copy.deepcopy(context)
patch.setattr(native,'_build_context',lambda a,c:copy.deepcopy(bound))
result=run_worker(reference,int(sys.argv[2]),
    bind_sources=lambda root:read_json(config['source']),
    build_context=lambda source,case:copy.deepcopy(context),
    adapter_factory=lambda context,archive:native.FineNativeAdapter(context,archive),
    geometry_factory=lambda context,archive,guard:Geometry(context['case']),root=root)
assert len(calls['models'])==8 and len(calls['execute'])==24
assert sum(len(m.native_calls) for m in calls['models'])==80
assert result['path'].endswith('/worker-data/returned.json')
"""


def test_one_real_fine_pipeline_then_explicitly_stop_before_second_child(monkeypatch, tmp_path):
    f = fixture(monkeypatch, tmp_path)
    context, archive = inputs()
    context["selected"]["certificate"] = dict(result=dict(certified=True), synthetic=True)
    f.source["archive"] = copy.deepcopy(archive)
    monkeypatch.setattr(f.d.inputs, "sources", lambda root: copy.deepcopy(f.source))
    monkeypatch.setattr(f.d.inputs, "build_context", lambda source, case: copy.deepcopy(context))
    monkeypatch.setattr(f.d, "graph", audit_fine_graph)
    monkeypatch.setattr(launch, "_dependencies", lambda: f.d)
    original_geometry = f.d.geometry.audit_geometry

    def geometry(*args):
        report = original_geometry(*args)
        report["producer_work"] = expected_work(context["case"])
        return report

    monkeypatch.setattr(f.d.geometry, "audit_geometry", geometry)
    monkeypatch.setattr(process, "POLL_SECONDS", 0.005)
    calls = []

    def supervised(*args, **kwargs):
        calls.append(Path(args[2]))
        if len(calls) == 2:
            raise RuntimeError("deliberate synthetic stop before second child")
        return process.supervise_fine_cell(*args, **kwargs)

    monkeypatch.setattr(launch, "_supervise", supervised)
    monkeypatch.setattr(
        launch,
        "_command",
        lambda ref, fd, root: [
            sys.executable,
            "-c",
            CHILD,
            json.dumps(ref),
            str(fd),
            str(launch.ROOT),
        ],
    )
    with pytest.raises(RuntimeError, match="deliberate synthetic stop"):
        launch.run(f.output, root=launch.ROOT)
    assert len(calls) == 2 and not calls[1].exists()
    row = json.loads((f.output / "study/case-00.json").read_text(encoding="utf-8"))
    assert row["complete_execution"] is row["arithmetic_consistency"] is True
    assert all(row[key] is False for key in launch.SCOPE)
    acknowledgement = read_json(row["parent_acknowledgement"])
    assert acknowledgement["returncode"] == 0
    assert len(acknowledgement["control_observations"]) == 1
    report = read_json(row["independent_audit"])
    graph = read_json(report["graph"])
    assert graph["graph_consistency"] is True and graph["complete_execution"] is False
    assert graph["counts"]["native"] == dict(attempted=80, completed=80)
    assert graph["counts"]["points"] == dict(attempted=552960, completed=552960)
    assert len(graph["initialization_rows"]) == 8
    assert len(graph["operation_rows"]) == 24 and len(graph["geometry_rows"]) == 4
    failure = json.loads((f.output / "study/failure-01.json").read_text(encoding="utf-8"))
    assert len(failure["completed_cases"]) == 1
    assert failure["following_cases_unexecuted"] == launch._cases()[2:]
    assert not (f.output / "study/summary.json").exists()
