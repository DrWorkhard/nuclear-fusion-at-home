import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import current_diagnostic_inputs as inputs


def test_current_diagnostic_predecessor_requires_bound_completed_audit(tmp_path, monkeypatch):
    path = tmp_path / "evidence/mesh-fine-completion-v1-audit.json"
    path.parent.mkdir(parents=True)
    study = tmp_path / "study.json"
    study.write_text(json.dumps(dict(status="completed")))
    data = dict(status="completed", all_pass=True, source=inputs.reference(study))
    path.write_text(json.dumps(data))
    commits = []
    monkeypatch.setattr(inputs, "require_committed", lambda root, p: commits.append(p))
    assert inputs.predecessor(tmp_path) == inputs.reference(path)
    assert commits == [path, study]
    data["all_pass"] = False
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="completed independent"):
        inputs.predecessor(tmp_path)
    data["all_pass"] = True
    data["source"]["sha256"] = "0" * 64
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="hash"):
        inputs.predecessor(tmp_path)
