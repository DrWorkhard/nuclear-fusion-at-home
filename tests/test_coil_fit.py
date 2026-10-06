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

def test_named_mapping_handles_free_permutation_and_rejects_missing_coordinates():
    names = experiment.names()
    assert names[:3] == ["xc(0)", "xs(1)", "xc(1)"]
    assert names[11] == "yc(0)" and names[22] == "zc(0)" and len(set(names)) == 33
    curves = [SimpleNamespace(local_full_dof_names=names, local_dof_names=names[::-1])
              for _ in range(6)]
    result = experiment.canonical_gradient(curves, lambda _: np.arange(33)[::-1])
    np.testing.assert_array_equal(result, np.tile(np.arange(33), 6))
    curves[0].local_dof_names = names[:-1]
    with pytest.raises(ValueError, match="named"):
        experiment.canonical_gradient(curves, lambda _: np.arange(33))

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
    def __init__(self):
        self.x0 = np.zeros(198)
        self.linear = np.cos(np.arange(198)+1)
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


def test_startup_probes_do_not_win_and_no_inherited_evaluation_cap(tmp_path, clock):
    def many(function, x, **kwargs):
        for _ in range(100):
            function(x)
        return seed_solver(function, x, **kwargs)

    model = SyntheticModel()
    record = experiment.Recorder(tmp_path/'run', 1)
    result = experiment.search(model, record, many)
    assert result['startup_pass'] and result['bundles_completed'] == 111
    assert result['selected']['index'] == 0
    assert all(row['passed'] for row in result['derivative_checks'])
    assert not result['physical_admission']
    np.testing.assert_array_equal(model.x, model.x0)


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
            raise experiment.InvalidTrial('numerical failure at startup')
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


@pytest.mark.parametrize('error', [experiment.InvalidTrial])
@pytest.mark.parametrize('continue_search', [False, True])
def test_failed_search_trial_keeps_eligible_candidates(tmp_path, clock, error, continue_search):
    model = SyntheticModel()
    original = model.evaluate

    def evaluate(x):
        if np.all(x == 1.):
            raise error('invalid trial')
        return original(x)

    def solver(function, x, **kwargs):
        before = function(x)[0]
        rejected, gradient = function(np.ones_like(x))
        assert np.isfinite(rejected) and rejected > before
        np.testing.assert_array_equal(gradient, np.zeros_like(x))
        if continue_search:
            function(x-model.linear*.01)
        return SimpleNamespace(success=continue_search, message='retained failure')

    model.evaluate = evaluate
    record = experiment.Recorder(tmp_path/'run', 1)
    result = experiment.search(model, record, solver)
    assert result['startup_pass'] and result['status']['reason'] == 'solver-return'
    assert result['selected']['index'] == (12 if continue_search else 0)
    assert result['bundles_attempted'] == 12+continue_search
    assert result['bundles_completed'] == 11+continue_search
    row = json.loads((record.output/'trial-00011.json').read_text(encoding='utf-8'))
    assert row['status'] == 'failed' and row['error'] == f'{error.__name__}: invalid trial'
    assert 'metrics' not in row and np.isfinite(row['rejected_value'])
    np.testing.assert_array_equal(model.x, result['selected']['x'])


@pytest.mark.parametrize('error', [TimeoutError, OSError, RuntimeError, TypeError,
                                 ValueError, FloatingPointError])
def test_resource_and_unexpected_search_failures_remain_fatal(tmp_path, clock, error):
    model = SyntheticModel()
    original = model.evaluate

    def evaluate(x):
        if model.calls == 10:
            raise error('fatal trial')
        return original(x)

    model.evaluate = evaluate
    result = experiment.search(model, experiment.Recorder(tmp_path/'run', 1), seed_solver)
    assert result['startup_pass'] and result['selected']['index'] == 0
    assert result['status']['reason'] == ('budget' if error is TimeoutError else 'failure')
    assert result['bundles_completed'] == 10


@pytest.mark.parametrize('scale', [1., 5e-6])
def test_real_lbfgsb_backtracks_failed_trial_without_discarding_seed(tmp_path, clock, scale):
    from scipy.optimize import minimize

    model = SyntheticModel()
    model.linear /= 2*np.linalg.norm(model.linear)
    original = model.evaluate

    def evaluate(x):
        if np.linalg.norm(x) > .75:
            raise experiment.InvalidTrial('unit flux degenerate or orientation reversed')
        value, gradient, metrics = original(x)
        return scale*value, scale*gradient, metrics

    model.evaluate = evaluate
    record = experiment.Recorder(tmp_path/'run', 1)
    result = experiment.search(model, record, minimize)
    failures = [json.loads(path.read_text(encoding='utf-8'))
                for path in record.output.glob('trial-*.json') if '-attempt' not in path.name]
    assert any(row['status'] == 'failed' for row in failures)
    assert result['startup_pass'] and result['status']['reason'] == 'solver-return'
    assert result['status']['success']
    assert result['selected']['metrics']['normal_rms'] < .88
    np.testing.assert_allclose(model.x, -model.linear, atol=1e-8)
    assert result['solver_options']['ftol'] == 0.
    assert result['solver_options']['gtol'] == 1e-9


def test_failed_search_trial_output_error_cannot_be_recovered(tmp_path, clock):
    model = SyntheticModel()
    original = model.evaluate

    def evaluate(x):
        if model.calls == 10:
            raise experiment.InvalidTrial('invalid trial')
        return original(x)

    model.evaluate = evaluate
    record = experiment.Recorder(tmp_path/'run', 1)
    save = record.save

    def write(name, value):
        if name == 'trial-00010.json':
            raise OSError('output ceiling')
        save(name, value)

    record.save = write
    result = experiment.search(model, record, seed_solver)
    assert result['status']['reason'] == 'failure'
    assert result['selected']['index'] == 0 and result['bundles_completed'] == 10
    assert 'OSError: output ceiling' in result['status']['error']


@pytest.mark.parametrize('q', [-1., 0., 1e-12, 1e-10])
def test_clipped_native_gradient_is_rejected_before_derivatives(q):
    model = object.__new__(experiment.Model)
    model.set_x = lambda _: None
    model.unit_flux = lambda: -1.
    model.objective = SimpleNamespace(J=lambda: q)
    with pytest.raises(ValueError, match='truncation'):
        model.evaluate(np.zeros(198))


@pytest.mark.parametrize("mismatch", [False, True])
def test_fine_saves_full_loop_freezes_current_and_checks_independent_BA(
        tmp_path, clock, monkeypatch, mismatch):
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
    seed = dict(target_flux=-1., physical=[dict(flip=False), dict(flip=True)])
    chosen = dict(index=11, x=np.zeros(198), metrics=dict(scale=2., unit_flux=-.5))
    if mismatch:
        with pytest.raises(ValueError, match="independent fine"):
            experiment.fine(seed, {}, chosen, record, .5)
    else:
        experiment.fine(seed, {}, chosen, record, .5)
    row = json.loads((record.output/"fine-0.5.json").read_text(encoding="utf-8"))
    assert row["checks_pass"] is not mismatch
    assert row["metrics"]["flux_relative_error"] == pytest.approx(.2)
    assert row["metrics"]["current"] == 200000
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


def order5_snapshot():
    from fusion_baselines.coupled_coil_audit import parameter_names, physical_curves  # noqa: F401

    rng = np.random.default_rng(5)
    coefficients = 0.01*rng.standard_normal((6, 3, 11))
    coefficients[:, 0, 2] += 1.0  # nonzero c(1) radius keeps every curve nonstationary
    coefficients[:, 1, 1] += 1.0
    scale = -0.03141592653589793/-0.01
    physical = []
    for period in range(2):
        c, s = np.cos(np.pi*period), np.sin(np.pi*period)
        rotation = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
        for flip in (False, True):
            matrix = rotation.T @ (np.diag([1.0, -1.0, -1.0]) if flip else np.eye(3))
            physical.extend(dict(base_index=i, period=period, flip=flip, matrix=matrix.tolist(),
                                 current=1e5*scale*(-1 if flip else 1)) for i in range(6))
    return dict(schema_version=1, nfp=2, nbase=6, order=5, names=parameter_names(6, 5),
                base_coefficients=coefficients.tolist(), physical=physical, scale=scale,
                B2_scale=1.0, unit_flux=-0.01, target_flux=-0.03141592653589793)


def test_lift_order_preserves_geometry_and_pads_zero_modes():
    from fusion_baselines.coupled_coil_audit import physical_curves, validate_snapshot

    snapshot = order5_snapshot()
    lifted = experiment.lift_order(snapshot, 8)
    validate_snapshot(lifted)
    coefficients = np.asarray(lifted["base_coefficients"])
    assert coefficients.shape == (6, 3, 17) and lifted["lifted_from_order"] == 5
    assert not coefficients[:, :, 11:].any()
    np.testing.assert_array_equal(coefficients[:, :, :11], snapshot["base_coefficients"])
    assert lifted["names"][:3] == ["coil[0]/xc(0)", "coil[0]/xs(1)", "coil[0]/xc(1)"]
    assert len(lifted["names"]) == 6*3*17 == len(experiment.names(8))*6
    before, after = physical_curves(snapshot, 128), physical_curves(lifted, 128)
    for key in ("positions", "tangents"):
        np.testing.assert_allclose(after[key], before[key], rtol=1e-14, atol=1e-15)
    for order in (7, 4):
        with pytest.raises(ValueError):
            experiment.lift_order(lifted if order == 4 else snapshot, order)


def test_order_eight_canonical_gradient_uses_named_coordinates():
    simsopt = pytest.importorskip("simsopt.geo")
    curves = [simsopt.CurveXYZFourier(64, 8) for _ in range(6)]
    gradient = experiment.canonical_gradient(
        curves, lambda curve: np.arange(len(curve.local_full_dof_names), dtype=float), 8)
    assert gradient.shape == (306,)
    np.testing.assert_array_equal(gradient[:51], np.arange(51))
    with pytest.raises(ValueError, match="registered order"):
        experiment.canonical_gradient(curves, lambda curve: np.zeros(51), 5)


@pytest.mark.parametrize('failure', ['shape', 'names'])
def test_structural_gradient_failure_stops_search(tmp_path, clock, failure):
    model = SyntheticModel()
    original = model.evaluate
    labels = experiment.names()
    curves = [SimpleNamespace(local_full_dof_names=labels, local_dof_names=labels)]*6

    def evaluate(x):
        if model.calls == 10:
            if failure == 'names':
                curves[0].local_dof_names = labels[:-1] + ['unknown']
            size = 32 if failure == 'shape' else 33
            experiment.canonical_gradient(curves, lambda _: np.zeros(size))
        return original(x)

    model.evaluate = evaluate
    result = experiment.search(model, experiment.Recorder(tmp_path/'run', 1), seed_solver)
    assert result['startup_pass'] and result['status']['reason'] == 'failure'
    assert result['bundles_completed'] == 10 and result['selected']['index'] == 0
    failed = json.loads((tmp_path/'run/trial-00010.json').read_text(encoding='utf-8'))
    assert failed['status'] == 'failed' and 'rejected_value' not in failed
    assert failed['error'].startswith('ValueError:')


@pytest.mark.parametrize('component', ['objective', 'geometry'])
@pytest.mark.parametrize('value', [np.nan, np.inf])
def test_model_nonfinite_native_derivatives_are_invalid_trials(component, value):
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


def test_nonfinite_rejection_feedback_stops_search(tmp_path, clock):
    model = SyntheticModel()
    original = model.evaluate

    def evaluate(x):
        if model.calls == 10:
            raise experiment.InvalidTrial('outside objective domain')
        _, gradient, metrics = original(x)
        return 1e308, np.zeros_like(gradient), metrics

    model.evaluate = evaluate
    result = experiment.search(model, experiment.Recorder(tmp_path/'run', 1), seed_solver)
    assert result['startup_pass'] and result['status']['reason'] == 'failure'
    assert 'finite rejection value unavailable' in result['status']['error']
    row = json.loads((tmp_path/'run/trial-00010.json').read_text(encoding='utf-8'))
    assert row['status'] == 'failed' and 'rejected_value' not in row
