"""Named gradients, independent fine fields, budgets and candidate selection."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from fusion_baselines import coil_fit as experiment


@pytest.fixture
def clock(monkeypatch):
    now = [0.]
    monkeypatch.setattr(experiment.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(experiment.shutil, "disk_usage", lambda _: SimpleNamespace(free=8*1024**3))
    return now

@pytest.mark.parametrize('order', [5, 8])
def test_named_mapping_handles_free_permutation_and_rejects_missing_coordinates(order):
    names = experiment.names(order)
    width = 2*order+1
    assert names[:3] == ["xc(0)", "xs(1)", "xc(1)"]
    assert names[width] == "yc(0)" and names[2*width] == "zc(0)"
    assert len(set(names)) == 3*width
    curves = [SimpleNamespace(local_full_dof_names=names, local_dof_names=names[::-1])
              for _ in range(6)]
    result = experiment.canonical_gradient(curves, lambda _: np.arange(3*width)[::-1], order)
    np.testing.assert_array_equal(result, np.tile(np.arange(3*width), 6))
    curves[0].local_dof_names = names[:-1]
    with pytest.raises(ValueError, match="named"):
        experiment.canonical_gradient(curves, lambda _: np.arange(3*width), order)

def test_native_counts_failure_prefix_and_late_completion(tmp_path, clock):
    record = experiment.Recorder(tmp_path/"run", 1)

    def fail():
        raise ValueError("native error")

    with pytest.raises(ValueError):
        record.call("B", fail)
    assert record.counts["B"] == dict(attempted=1, completed=0)

    def late():
        clock[0] = 2
        return 42

    with pytest.raises(TimeoutError):
        record.call("A", late)
    assert record.counts["A"] == dict(attempted=1, completed=1)
    saved = json.loads((record.output/"progress.json").read_text())
    assert saved["native"] == record.counts

def test_shared_cap_counts_atomic_temporary_and_fresh_paths(tmp_path, clock, monkeypatch):
    shared = [0]
    left = experiment.Recorder(tmp_path/"left", 1, shared)
    right = experiment.Recorder(tmp_path/"right", 1, shared)
    monkeypatch.setattr(experiment, "MAX_BYTES", 10)
    left.save("a", b"1234")
    right.save("b", b"5678")
    assert shared == [8]
    with pytest.raises(OSError, match="output ceiling"):
        left.save("a", b"123")  # Existing 4 + other 4 + temporary 3 exceeds 10.
    assert (left.output/"a").read_bytes() == b"1234"
    with pytest.raises(FileExistsError):
        experiment.Recorder(left.output, 1)

def test_module_load_has_no_native_field_symbols():
    assert "BiotSavart" not in experiment.__dict__
    assert "SquaredFlux" not in experiment.__dict__

def test_two_native_circle_fields_have_distinct_names_and_invalidate(tmp_path, clock):
    pytest.importorskip("simsopt")
    from simsopt.field import BiotSavart, Coil, Current
    from simsopt.geo import CurveXYZFourier

    curve = CurveXYZFourier(64, 1)
    curve.set("xc(1)", 1.)
    curve.set("ys(1)", 1.)
    coils = [Coil(curve, Current(1e5))]
    records = [experiment.Recorder(tmp_path/f"field-{i}", 1) for i in range(2)]
    fields = [experiment.tracked_field(BiotSavart, coils, record) for record in records]
    points = np.array([[.2, .1, .3], [-.3, .2, .4], [.1, -.2, -.5]])
    for field in fields:
        field.set_points(points)
    before = [[field.B().copy(), field.A().copy()] for field in fields]
    curve.set("xc(0)", .05)
    reference = BiotSavart(coils)
    reference.set_points(points)
    for i, field in enumerate(fields):
        for j, name in enumerate(("B", "A")):
            after, expected = getattr(field, name)(), getattr(reference, name)()
            assert not np.array_equal(after, before[i][j]), f"stale {name} for field {i}"
            np.testing.assert_allclose(after, expected, rtol=1e-12, atol=1e-14)
    assert fields[0].name != fields[1].name and fields[0] != fields[1]
    assert type(fields[0]) is type(fields[1])
    assert len({*fields, reference}) == 3
    curve.set("xc(0)", 0.)
    for i, field in enumerate(fields):
        np.testing.assert_allclose(field.B(), before[i][0], rtol=1e-12, atol=1e-14)
        np.testing.assert_allclose(field.A(), before[i][1], rtol=1e-12, atol=1e-14)
    assert all(record.counts["B"] == dict(attempted=3, completed=3) for record in records)
    assert all(record.counts["A"] == dict(attempted=3, completed=3) for record in records)


def test_progress_write_crossing_deadline_cannot_start_native_call(tmp_path, clock):
    record = experiment.Recorder(tmp_path/"run", 300)
    original, native = record.save, Mock()

    def save(name, value):
        original(name, value)
        clock[0] = 301.

    record.save = save
    with pytest.raises(TimeoutError):
        record.call("B", native)
    assert not native.called and record.counts["B"] == dict(attempted=1, completed=0)


class SyntheticModel:
    def __init__(self, size=198):
        self.x0 = np.zeros(size)
        self.linear = np.cos(np.arange(size)+1)
        self.calls, self.x = 0, self.x0.copy()

    def set_x(self, x):
        self.x = np.asarray(x).copy()

    def evaluate(self, x):
        self.calls += 1
        self.set_x(x)
        value = float(1+self.linear@x+.5*(x@x))
        return value, self.linear+x, dict(normal_rms=value, lengths=[3.44]*6,
            sampled_geometry_limits_met=True, current_limit_met=True)


def seed_solver(function, x, **kwargs):
    assert 'bounds' not in kwargs
    function(x)
    return SimpleNamespace(success=True, message='synthetic')


@pytest.mark.parametrize('size', [198, 306])
def test_startup_probes_do_not_win_and_no_inherited_evaluation_cap(tmp_path, clock, size):
    def many(function, x, **kwargs):
        for _ in range(100):
            function(x)
        return seed_solver(function, x, **kwargs)

    model = SyntheticModel(size)
    record = experiment.Recorder(tmp_path/'run', 1)
    result = experiment.search(model, record, many)
    assert result['startup_pass'] and result['bundles_completed'] == 111
    assert result['selected']['index'] == 0
    assert all(row['passed'] for row in result['derivative_checks'])
    assert not result['physical_admission']
    np.testing.assert_array_equal(model.x, model.x0)


def test_order_eight_model_preserves_seed_objective_and_differentiates_added_modes(tmp_path, clock):
    from pathlib import Path

    pytest.importorskip('simsopt')
    from fusion_baselines import coil_check

    root = Path(__file__).resolve().parents[1]
    data = coil_check.read_json(root/coil_check.TARGET)
    candidate = coil_check.read_json(root/'submissions/length-headroom-six-coil/candidate.json')
    seed = coil_check.candidate_snapshot(candidate, data)
    models, values = [], []
    for order in (5, 8):
        model = experiment.Model(experiment.promote_order(seed, order), data,
                                 experiment.Recorder(tmp_path/f'order-{order}', 60),
                                 n=16, ncoil=128)
        models.append(model)
        values.append(model.evaluate(model.x0))
    assert values[0][0] == pytest.approx(values[1][0], rel=1e-10, abs=1e-12)
    old_gradient = values[0][1].reshape(6, 3, 11)
    np.testing.assert_allclose(values[1][1].reshape(6, 3, 17)[:, :, :11], old_gradient,
                               atol=1e-10, rtol=1e-8)
    model = models[1]
    direction = np.zeros((6, 3, 17))
    direction[:, :, 11:] = np.sin(np.arange(108).reshape(6, 3, 6)+1)
    direction = direction.ravel()/np.linalg.norm(direction)
    point = model.x0+2e-4*direction
    _, gradient, _ = model.evaluate(point)
    h = 1.25e-6
    derivative = (model.evaluate(point+h*direction)[0]
                  - model.evaluate(point-h*direction)[0])/(2*h)
    assert derivative == pytest.approx(float(gradient@direction), rel=1e-4, abs=1e-7)


@pytest.mark.parametrize('failure', ['gradient', 'repeat', 'exception', 'trial', 'late'])
def test_failed_startup_never_searches_and_retains_failure(tmp_path, clock, failure):
    model = SyntheticModel()
    original = model.evaluate

    def evaluate(x):
        value, gradient, metrics = original(x)
        if failure == 'gradient':
            gradient = -gradient
        if failure == 'repeat' and model.calls == 10:
            value += 1e-6
        if failure == 'exception':
            raise ValueError('synthetic failure')
        if failure == 'trial':
            raise experiment.InvalidTrial('unit flux degenerate or orientation reversed')
        if failure == 'late':
            clock[0] = 2
        return value, gradient, metrics

    model.evaluate = evaluate
    record = experiment.Recorder(tmp_path/'run', 1)
    result = experiment.search(model, record, lambda *_a, **_kw: pytest.fail('search'))
    assert not result['startup_pass']
    assert result['status']['reason'] == ('budget' if failure == 'late' else 'failure')
    assert (record.output/'trial-00000-attempt.json').is_file()
    if failure in ('late', 'exception', 'trial'):
        assert result['selected'] is None
        assert json.loads((record.output/'trial-00000.json').read_text())['status'] == 'failed'


def test_failed_search_trial_preserves_candidate_and_can_backtrack(tmp_path, clock):
    model = SyntheticModel()
    original = model.evaluate

    def evaluate(x):
        if x[0] == 1.:
            raise experiment.InvalidTrial('unit flux degenerate or orientation reversed')
        return original(x)

    def backtrack(function, x, **kwargs):
        good = x - .001*model.linear
        valid, _ = function(good)
        bad = x.copy()
        bad[0] = 1.
        rejected, gradient = function(bad)
        assert np.isfinite(rejected) and rejected > valid
        assert np.isfinite(gradient).all()
        function(good)  # Recovery must not depend on the rejected model state.
        return SimpleNamespace(success=False, message='synthetic line-search stop')

    model.evaluate = evaluate
    record = experiment.Recorder(tmp_path/'run', 1)
    result = experiment.search(model, record, backtrack)
    assert result['startup_pass'] and result['status']['reason'] == 'solver-return'
    assert result['selected']['index'] == 10
    assert result['bundles_attempted'] == 13 and result['bundles_completed'] == 12
    failed = json.loads((record.output/'trial-00011.json').read_text(encoding='utf-8'))
    assert failed['status'] == 'failed' and 'InvalidTrial' in failed['error']
    assert 'solver_rejection_value' in failed and 'metrics' not in failed
    np.testing.assert_array_equal(model.x, result['selected']['x'])


@pytest.mark.parametrize('error', [TimeoutError, OSError, RuntimeError])
def test_search_does_not_recover_resource_or_unexpected_errors(tmp_path, clock, error):
    model = SyntheticModel()
    original = model.evaluate

    def evaluate(x):
        if model.calls >= 10:
            raise error('stop')
        return original(x)

    model.evaluate = evaluate
    result = experiment.search(model, experiment.Recorder(tmp_path/'run', 1), seed_solver)
    assert result['startup_pass']
    assert result['status']['reason'] == ('budget' if error is TimeoutError else 'failure')
    assert result['selected']['index'] == 0 and result['bundles_completed'] == 10


def test_scipy_backtracks_from_invalid_trial_and_reaches_valid_minimum(tmp_path, clock):
    from scipy.optimize import minimize

    model = SyntheticModel()

    def evaluate(x):
        model.set_x(x)
        if abs(x[0]) > .2:
            raise experiment.InvalidTrial('outside synthetic objective domain')
        value = float((x[0]-.1)**2 + 1e-6)
        gradient = np.zeros_like(x)
        gradient[0] = 2*(x[0]-.1)
        return value, gradient, dict(normal_rms=value, lengths=[3.44]*6,
            sampled_geometry_limits_met=True, current_limit_met=True)

    model.evaluate = evaluate
    record = experiment.Recorder(tmp_path/'run', 1)
    result = experiment.search(model, record, minimize)
    assert result['startup_pass'] and result['status']['success']
    assert result['selected']['x'][0] == pytest.approx(.1, abs=1e-8)
    trials = [json.loads(p.read_text(encoding='utf-8'))
              for p in record.output.glob('trial-*.json') if '-attempt' not in p.name]
    assert any(t['status'] == 'failed' for t in trials)
    assert result['solver_options']['ftol'] == 0.


def test_unaccepted_lower_trial_cannot_make_invalid_point_look_converged(tmp_path, clock):
    from scipy.optimize import minimize

    model = SyntheticModel()
    solved = []

    def evaluate(x):
        model.set_x(x)
        if .01 < x[0] < .99:
            raise experiment.InvalidTrial('outside synthetic objective domain')
        term = 100*np.exp(-10000*x[0])
        value = float(term + 5 + 5*x[0]**2)
        gradient = np.zeros_like(x)
        gradient[0] = -10000*term + 10*x[0]
        return value, gradient, dict(normal_rms=value, lengths=[3.44]*6,
            sampled_geometry_limits_met=True, current_limit_met=True)

    def capture(*args, **kwargs):
        result = minimize(*args, **kwargs)
        solved.append(result)
        return result

    model.evaluate = evaluate
    record = experiment.Recorder(tmp_path/'run', 1)
    result = experiment.search(model, record, capture)
    assert result['startup_pass'] and result['status']['success']
    assert not .01 < solved[0].x[0] < .99
    assert result['selected']['x'][0] < .01
    failures = [json.loads(p.read_text(encoding='utf-8'))
                for p in record.output.glob('trial-*.json') if '-attempt' not in p.name]
    failures = [row for row in failures if row['status'] == 'failed']
    assert failures and all(row['solver_rejection_value'] > 105 for row in failures)


@pytest.mark.parametrize('component', ['objective', 'geometry'])
@pytest.mark.parametrize('value', [np.nan, np.inf])
def test_model_classifies_nonfinite_native_derivatives_as_invalid_trials(component, value):
    model = object.__new__(experiment.Model)
    model.order = 5
    model.set_x = lambda _: None
    model.unit_flux = lambda: -1.
    model.area = 1.
    labels = experiment.names()
    model.curves = [SimpleNamespace(local_full_dof_names=labels, local_dof_names=labels)]*6
    for name in ('objective', 'geometry'):
        values = np.full(33, value if name == component else 0.)

        def derivative(_curve, values=values):
            return values

        setattr(model, name, SimpleNamespace(J=lambda: 1.,
                dJ=lambda derivative=derivative, **_: derivative))
    with pytest.raises(experiment.InvalidTrial, match='nonfinite native gradient'):
        model.evaluate(np.zeros(198))


def test_native_derivative_shape_mismatch_is_fatal():
    labels = experiment.names()
    curves = [SimpleNamespace(local_full_dof_names=labels, local_dof_names=labels)]*6
    with pytest.raises(ValueError, match='shape') as error:
        experiment.canonical_gradient(curves, lambda _: np.zeros(32))
    assert not isinstance(error.value, experiment.InvalidTrial)


@pytest.mark.parametrize('failure', ['length', 'current', 'geometry', 'late-write'])
def test_ineligible_better_candidate_cannot_win(tmp_path, clock, failure):
    model = SyntheticModel()
    original = model.evaluate

    def evaluate(x):
        value, gradient, metrics = original(x)
        if model.calls > 10:
            metrics['normal_rms'] = 0.
            if failure == 'length':
                metrics['lengths'][0] = 3.46
            if failure == 'current':
                metrics['current_limit_met'] = False
            if failure == 'geometry':
                metrics['sampled_geometry_limits_met'] = False
        return value, gradient, metrics

    model.evaluate = evaluate
    record = experiment.Recorder(tmp_path/'run', 1)
    save = record.save

    def write(name, value):
        save(name, value)
        if failure == 'late-write' and name == 'trial-00010.json':
            clock[0] = 2

    record.save = write
    result = experiment.search(model, record, seed_solver)
    assert result['startup_pass'] and result['selected']['index'] == 0
    if failure == 'late-write':
        assert result['bundles_completed'] == 10 and result['status']['reason'] == 'budget'


def test_no_eligible_candidate_has_no_fallback(tmp_path, clock):
    model = SyntheticModel()
    original = model.evaluate

    def evaluate(x):
        value, gradient, metrics = original(x)
        metrics['lengths'][0] = 3.46
        return value, gradient, metrics

    model.evaluate = evaluate
    result = experiment.search(model, experiment.Recorder(tmp_path/'run', 1), seed_solver)
    assert result['startup_pass'] and result['selected'] is None


@pytest.mark.parametrize('q', [-1., 0., 1e-12, 1e-10])
def test_clipped_native_gradient_is_rejected_before_derivatives(q):
    model = object.__new__(experiment.Model)
    model.set_x = lambda _: None
    model.unit_flux = lambda: -1.
    model.objective = SimpleNamespace(J=lambda: q)
    with pytest.raises(ValueError, match='truncation'):
        model.evaluate(np.zeros(198))


@pytest.mark.parametrize("mismatch", [False, True])
@pytest.mark.parametrize('order', [5, 8])
def test_fine_saves_full_loop_freezes_current_and_checks_independent_BA(
        tmp_path, clock, monkeypatch, mismatch, order):
    from fusion_baselines import coupled_coil_audit

    record = experiment.Recorder(tmp_path/"run", 1)
    record.counts["independent_BA"] = dict(attempted=0, completed=0)
    vectors, block_sizes = dict(B=np.array([3., 4., .5]), A=np.array([-.6, 0., 0.])), []

    class Field:
        def set_points(self, points):
            self.points = points

        def get(self, name):
            block_sizes.append(len(self.points))
            return record.call(name, lambda: np.tile(vectors[name], (len(self.points), 1)))

        def B(self):
            return self.get("B")

        def A(self):
            return self.get("A")

    class Model:
        def __init__(self, *args, **kwargs):
            assert kwargs == dict(n=128, ncoil=512, offset=.5)
            self.points = np.ones((16, 16, 3))
            self.normals = np.broadcast_to([0., 0., 1.], self.points.shape)
            self.field, self.loop_field = Field(), Field()
            self.loop_points = np.ones((512, 3))
            self.loop_tangent = np.tile([1., 0., 0.], (512, 1))

        def set_x(self, x):
            pass

        def geometry_metrics(self):
            return dict(sampled_geometry_limits_met=False, geometry_certified=False)

    monkeypatch.setattr(experiment, "Model", Model)
    monkeypatch.setattr(coupled_coil_audit, "physical_curves", lambda seed, nodes: dict(
        positions=np.ones((2, nodes, 3)), tangents=np.ones((2, nodes, 3)),
        currents=np.array([row["current"] for row in seed["physical"]])))
    monkeypatch.setattr(coupled_coil_audit, "filament_field_and_potential", lambda p, *_: (
        np.tile(2*vectors["B"]+(1 if mismatch else 0), (len(p), 1)),
        np.tile(2*vectors["A"], (len(p), 1))))
    seed = dict(order=order, target_flux=-1., physical=[dict(flip=False), dict(flip=True)])
    chosen = dict(index=11, x=np.arange(18*(2*order+1))*1e-6,
                  metrics=dict(scale=2., unit_flux=-.5))
    if mismatch:
        with pytest.raises(ValueError, match="independent fine"):
            experiment.fine(seed, {}, chosen, record, .5)
    else:
        experiment.fine(seed, {}, chosen, record, .5)
    row = json.loads((record.output/"fine-0.5.json").read_text(encoding="utf-8"))
    assert row["checks_pass"] is not mismatch
    assert row["metrics"]["flux_relative_error"] == pytest.approx(.2)
    assert row["metrics"]["current"] == 200000
    snapshot = json.loads((record.output/'selected-snapshot.json').read_text(encoding='utf-8'))
    assert np.shape(snapshot['base_coefficients']) == (6, 3, 2*order+1)
    np.testing.assert_array_equal(np.ravel(snapshot['base_coefficients']), chosen['x'])
    assert max(block_sizes) == 128
    with np.load(record.output/"fine-0.5.npz", allow_pickle=False) as saved:
        assert saved["A"].shape == saved["loop_tangent"].shape == (512, 3)
        np.testing.assert_array_equal(saved["currents"], [200000, -200000])
        assert saved["independent_B"].shape == saved["independent_A"].shape == (64, 3)


@pytest.mark.parametrize('when', ['already-late', 'late-write', 'on-time'])
def test_late_publication_never_claims_completion(tmp_path, clock, when):
    record = experiment.Recorder(tmp_path/'run', 1)
    original = record.save

    def write(name, value):
        original(name, value)
        if when == 'late-write':
            clock[0] = 2

    record.save = write
    if when == 'already-late':
        clock[0] = 2
    report = dict(completed=True)
    assert record.finish(report, 0) is (when == 'on-time')
    assert json.loads((record.output/'result.json').read_text())['completed'] is (when == 'on-time')
