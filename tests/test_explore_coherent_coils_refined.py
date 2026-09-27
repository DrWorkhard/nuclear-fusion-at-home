"""Exact search equivalence and synthetic checks for the source-bound retry."""

import ast
import copy
import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
with pytest.MonkeyPatch.context() as patch:
    patch.syspath_prepend(str(ROOT/"scripts"))
    spec = importlib.util.spec_from_file_location(
        "coherent_retry_test_module", ROOT/"scripts/explore_coherent_coils_refined.py")
    retry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(retry)


def test_search_ast_changes_only_step_tuple_and_explicit_metadata():
    class Normalize(ast.NodeTransformer):
        metadata = 0

        def visit_Attribute(self, node):
            if isinstance(node.value, ast.Name) and node.value.id == "previous":
                assert node.attr in ("BOX", "BUNDLES", "expand")
                return ast.Name(id=node.attr, ctx=node.ctx)
            return self.generic_visit(node)

        def visit_Name(self, node):
            if node.id == "PROBE_STEPS":
                return ast.parse("(1e-5, 5e-6)", mode="eval").body
            return node

        def visit_Call(self, node):
            # Discard only this documented return metadata; no runtime rewriting.
            for keyword in node.keywords[:]:
                if keyword.arg == "startup_steps":
                    assert isinstance(node.func, ast.Name) and node.func.id == "dict"
                    assert ast.unparse(keyword.value) == "list(PROBE_STEPS)"
                    node.keywords.remove(keyword)
                    self.metadata += 1
            return self.generic_visit(node)

    transform = Normalize()
    actual = transform.visit(ast.parse(inspect.getsource(retry.search)))
    original = ast.parse(inspect.getsource(retry.ORIGINAL_SEARCH))
    assert transform.metadata == 1
    assert ast.dump(actual) == ast.dump(original)
    assert retry.PROBE_STEPS == (1.25e-6, 6.25e-7)


def diagnostic():
    anchors = {"scale": .2, "normal_rms": .15}
    report = dict(completed=True, sources_unchanged=True, exact_repeat=True,
                  bundles_attempted=30, bundles_completed=30,
                  model_configuration="control", coefficient_box_m=.02,
                  tolerances=dict(absolute=1e-7, relative=1e-4, combination="OR"),
                  seed_replay={k: dict(expected=v, actual=v, passed=True)
                               for k, v in anchors.items()}, comparisons=[])
    for label, function in (("sin", np.sin), ("cos", np.cos)):
        direction = function(np.arange(198)+1)
        direction /= np.linalg.norm(direction)
        for h in retry.PROBE_STEPS:
            report["comparisons"].append(dict(direction=label, h=h, vector=direction.tolist(),
                components={name: dict(plus=0., minus=0., finite_difference=0., analytic=0.,
                                       error=0., threshold_met=True)
                            for name in ("total", "flux", "geometry")}))
    return report, anchors


def test_complete_diagnostic_preflight_is_read_only():
    report, anchors = diagnostic()
    before = copy.deepcopy(report)
    retry.validate_diagnostic(report, anchors)
    assert report == before


@pytest.mark.parametrize("fault", ["repeat", "count", "tolerance", "anchor", "direction",
                                   "missing", "duplicate", "failed", "overflow", "value"])
def test_incomplete_changed_or_nonfinite_diagnostic_is_rejected(fault):
    report, anchors = diagnostic()
    component = report["comparisons"][0]["components"]["total"]
    if fault == "repeat":
        report["exact_repeat"] = False
    if fault == "count":
        report["bundles_completed"] = 29
    if fault == "tolerance":
        report["tolerances"]["absolute"] = 1e-6
    if fault == "anchor":
        report["seed_replay"]["scale"]["expected"] = .3
    if fault == "direction":
        report["comparisons"][0]["vector"][0] += .001
    if fault == "missing":
        del report["comparisons"][0]["components"]["geometry"]
    if fault == "duplicate":
        report["comparisons"].append(copy.deepcopy(report["comparisons"][0]))
    if fault == "failed":
        component["threshold_met"] = False
    if fault == "overflow":
        component.update(plus=1e308, minus=-1e308)
    if fault == "value":
        component["finite_difference"] = 1e-4
    with pytest.raises(ValueError):
        retry.validate_diagnostic(report, anchors)


def test_all_scoped_overrides_restore_on_exception_and_reject_nesting():
    paired, previous = retry.paired, retry.previous
    original = (previous.search, paired.INPUTS, paired.fingerprints, paired.seed_inputs)
    with pytest.raises(RuntimeError), retry.refined_startup():
        assert previous.search is retry.search and paired.INPUTS is retry.INPUTS
        assert paired.fingerprints is retry.fingerprints and paired.seed_inputs is retry.seed_inputs
        with pytest.raises(ValueError, match="nested"):
            with retry.refined_startup():
                pass
        raise RuntimeError("synthetic interruption")
    assert (previous.search, paired.INPUTS, paired.fingerprints, paired.seed_inputs) == original


class Model:
    x0, indices = np.zeros(198), np.arange(198)

    def evaluate(self, x):
        gradient = x.copy()
        gradient[0] += 1
        return float(1+x[0]+.5*x@x), gradient, dict(normal_rms=.4+x[0], scale=.2,
            sampled_geometry_limits_met=bool(x[0] >= -.05), current_limit_met=True)

    def set_x(self, x):
        self.x = np.asarray(x).copy()


@pytest.mark.parametrize("consume_budget", [False, True])
def test_probe_steps_accounting_and_unchanged_feasible_selection(tmp_path, monkeypatch,
                                                               consume_budget):
    monkeypatch.setattr(retry.time, "monotonic", lambda: 0.)
    monkeypatch.setattr(retry.paired.shutil, "disk_usage",
                        lambda _: SimpleNamespace(free=8*1024**3))
    model, record = Model(), retry.paired.Recorder(tmp_path/"run", 900)

    def solver(function, initial, **kwargs):
        assert kwargs["options"]["maxfun"] == kwargs["options"]["maxiter"] == 590
        assert kwargs["bounds"][0] == (-.08, .08) and kwargs["bounds"][5] == (-.02, .02)
        for displacement in (-.07, -.03):
            point = initial.copy()
            point[0] = displacement
            function(point)
        if consume_budget:
            for _ in range(601):
                function(initial)
        return SimpleNamespace(success=True, message="synthetic result")

    with retry.refined_startup(), retry.paired.configuration("coherent"):
        result = retry.previous.search(model, record, dict(scale=.2, normal_rms=.4),
                                       retry.paired.solver_adapter(solver))
    assert result["startup_pass"] and result["startup_steps"] == list(retry.PROBE_STEPS)
    assert [r["h"] for r in result["derivative_checks"]] == list(retry.PROBE_STEPS)*2
    assert result["bundles_attempted"] == result["bundles_completed"] == (
        600 if consume_budget else 12)
    assert result["lowest_objective"]["index"] == 10
    assert result["fine_selected"]["index"] == 11 and model.x[0] == -.03
    assert not (record.output/"trial-600-attempt.json").exists()
    assert retry.previous.BOX == .02 and retry.previous.BUNDLES == 240
    assert retry.previous.search is retry.ORIGINAL_SEARCH


def test_orchestration_dispatch_is_unchanged_and_restored_on_failure(monkeypatch, tmp_path):
    fake = Mock(side_effect=RuntimeError("synthetic run failure"))
    monkeypatch.setattr(retry.paired, "run", fake)
    with pytest.raises(RuntimeError):
        retry.run(tmp_path)
    fake.assert_called_once_with(tmp_path)
    assert retry.previous.search is retry.ORIGINAL_SEARCH
    assert retry.paired.INPUTS is retry.ORIGINAL_INPUTS
