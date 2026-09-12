import ast
import copy
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_composite_slsqp_arm as runner
from audit_composite_polish import audit_start

from fusion_baselines.composite_start_gate import composite_gate, reference_checks, startup_replay


def fixture():
    q = dict(x=np.zeros(207), values=np.ones(138), jacobian=np.zeros((138, 207)))
    d = np.random.default_rng(46).normal(size=207)
    d /= np.linalg.norm(d)
    q["directions"] = np.array([d, d])
    p = np.arange(206, -1, -1)
    data = dict(x=q["x"][p], values=q["values"].copy(), jacobian=q["jacobian"][:, p],
                direction=d[p])
    vectors = [q["x"]]
    for h in (1e-5, 1e-6, 1e-7, 1e-8):
        vectors.extend((q["x"]+h*d, q["x"]-h*d))
    old, ledger, screens = [], [], []
    for i, vector in enumerate(vectors):
        values = q["values"].copy()
        if i:
            values[6] += 1e-13 if i % 2 else -1e-13
        old.append(dict(x_sha256=hashlib.sha256(vector.tobytes()).hexdigest(),
                        values=values.tolist()))
        ledger.append(dict(x_sha256=hashlib.sha256(vector[p].tobytes()).hexdigest(),
                           values=values.tolist()))
    for i, h in enumerate((1e-5, 1e-6, 1e-7, 1e-8)):
        fd = (np.asarray(ledger[1+2*i]["values"])-ledger[2+2*i]["values"])/(2*h)
        screens.append(dict(eps=h, analytic=np.zeros(138).tolist(), finite_difference=fd.tolist(),
                            normalized_errors=abs(fd).tolist()))
    qualified = dict(x=data["x"], values=data["values"], jacobian=data["jacobian"],
                     direction=data["direction"])
    ref = reference_checks(data["x"], data["values"], data["jacobian"], qualified)
    replay = startup_replay(data["x"], data["direction"], p, ledger, dict(evaluations=old))
    arm = dict(evaluations=ledger, gradient_checks=screens, initial_reference=ref,
                startup_replay=replay,
                gradient_gate_profile="qualified_pairs_plus_original_nonpair_fd")
    arm.update(composite_gate(screens[-1]["normalized_errors"], ref, replay))
    return arm, data, q, p, dict(evaluations=old), qualified


def test_explicit_failed_all_row_and_passed_composite_with_independent_audit():
    arm, data, q, p, old, _ = fixture()
    assert arm["original_all_row_fd_pass"] is False
    assert arm["gradient_screen_pass"] is True
    assert all(audit_start(arm, data, q, p, old).values())


def test_changed_nonpair_or_full_jacobian_replay_cannot_pass():
    arm, data, q, p, old, qualified = fixture()
    errors = np.asarray(arm["gradient_checks"][-1]["normalized_errors"])
    errors[127] = 1e-5
    assert not composite_gate(errors, arm["initial_reference"], arm["startup_replay"])[
        "gradient_screen_pass"]
    changed = data["jacobian"].copy()
    changed[6, 43] = 1e-6
    ref = reference_checks(data["x"], data["values"], changed, qualified)
    assert not ref["jacobian_pass"]
    bad = copy.deepcopy(arm)
    bad["gradient_checks"][-1]["normalized_errors"][0] += 0.01
    assert not all(audit_start(bad, data, q, p, old).values())


def test_bad_permutation_source_hash_and_nonfinite_rejected():
    arm, data, _, p, old, qualified = fixture()
    with pytest.raises(ValueError):
        startup_replay(data["x"], data["direction"], np.zeros(207, dtype=int),
                       arm["evaluations"], old)
    old["evaluations"][5]["x_sha256"] = "0" * 64
    replay = startup_replay(data["x"], data["direction"], p, arm["evaluations"], old)
    assert not replay[5]["source_hash"]
    with pytest.raises(ValueError):
        reference_checks(data["x"], np.full(138, np.nan), data["jacobian"], qualified)


def test_additive_solver_and_callback_bodies_match_unchanged_original():
    root = Path(__file__).resolve().parents[1]
    def nodes(path):
        function = next(n for n in ast.parse(path.read_text()).body
                        if isinstance(n, ast.FunctionDef) and n.name == "run_arm")
        callbacks = {n.name: ast.dump(n, include_attributes=False) for n in ast.walk(function)
                     if isinstance(n, ast.FunctionDef) and n.name != "run_arm"}
        solver = [ast.dump(n, include_attributes=False) for n in ast.walk(function)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "minimize"]
        return callbacks, solver
    assert nodes(root / "scripts/run_direct_slsqp_pilot.py") == nodes(
        root / "scripts/run_composite_slsqp_arm.py")


def test_arm_calls_solver_only_after_nine_counted_qualified_bundles(tmp_path, monkeypatch):
    arm, data, _, p, old, qualified = fixture()
    class Backend:
        work = {"evaluations": 0}
        def evaluate(self, x):
            i = self.work["evaluations"]
            self.work["evaluations"] += 1
            assert hashlib.sha256(x.tobytes()).hexdigest() == arm["evaluations"][i]["x_sha256"]
            return np.asarray(arm["evaluations"][i]["values"]), data["jacobian"].copy(), {}
    backend = Backend()
    calls = []
    def minimize(*args, **kwargs):
        assert backend.work["evaluations"] == 9
        calls.append(kwargs)
        return SimpleNamespace(x=np.zeros(207), success=True, status=0, message="mock only",
                               nit=0, nfev=0, njev=0)
    monkeypatch.setattr(runner, "minimize", minimize)
    field = SimpleNamespace(save=lambda path: Path(path).write_text("{}\n"))
    ctx = SimpleNamespace(Jf=SimpleNamespace(field=field, x=data["x"]))
    result = runner.run_arm(backend, ctx, data["x"], tmp_path / "raw", tmp_path / "out.json", 1,
                            qualified=qualified, source_permutation=p, failed_arm=old)
    assert len(calls) == 1 and result["counters"]["attempts"] == 9
    assert result["gradient_screen_pass"] and not result["original_all_row_fd_pass"]


def test_bad_start_matrix_stops_before_fd_or_solver(tmp_path, monkeypatch):
    _, data, _, p, old, qualified = fixture()
    calls = []
    class Backend:
        work = {"evaluations": 0}
        def evaluate(self, x):
            self.work["evaluations"] += 1
            return data["values"], data["jacobian"]+0.1, {}
    backend = Backend()
    monkeypatch.setattr(runner, "minimize", lambda *args, **kwargs: calls.append(1))
    field = SimpleNamespace(save=lambda path: Path(path).write_text("{}\n"))
    ctx = SimpleNamespace(Jf=SimpleNamespace(field=field, x=data["x"]))
    with pytest.raises(ValueError, match="full start replay"):
        runner.run_arm(backend, ctx, data["x"], tmp_path / "raw", tmp_path / "out.json", 1,
                       qualified=qualified, source_permutation=p, failed_arm=old)
    assert not calls and backend.work["evaluations"] == 1
