"""Complete synthetic cell histories; all field arrays deliberately nonphysical."""

import copy

import numpy as np
import pytest
from test_protected_cell_contract import bundle_fixture, context_fixture, model_fixture
from test_protected_run_ledger import EXPECTED, Native

from fusion_baselines.clear_coil_field import CountedField
from fusion_baselines.protected_coil_search_audit import audit
from fusion_baselines.protected_run_cell import run_cell
from fusion_baselines.protected_run_snapshots import SnapshotStore, read_arrays, read_json
from fusion_baselines.protected_search_journal import EventJournal, read_events


class Adapter:
    def __init__(self, context, *, strategy="null", padding=0):
        self.context = copy.deepcopy(context)
        self.seed = np.asarray(context["seed"]["base_coefficients"]).ravel().copy()
        self.gradient = np.zeros_like(self.seed)
        if strategy != "null":
            self.gradient[0] = 1.0
        self.context["historical_seed"] = bundle_fixture(self.context, gradient=self.gradient)
        self.strategy, self.padding = strategy, padding
        self.models, self.callbacks, self.native_calls = [], [], []
        self.certificate_calls = self.bundle_calls = self.invalidations = 0
        self.trial_index = -1
        self.latest_phase = None
        self.fault = None

    def initialize(self, callback):
        model = model_fixture(self.context)
        self.callbacks.append(callback)
        events = []
        model.fields = {
            field: CountedField(
                Native(self.native_calls, self.fault == "native"), field, events, callback
            )
            for field in ("boundary", "inner", "loop")
        }
        model.fields["loop"].set_points(np.zeros((256, 3)))
        model.fields["loop"].A()
        self.models.append(model)
        return model

    def certificate(self, original, x):
        self.certificate_calls += 1
        if self.fault == "certificate":
            raise ArithmeticError("injected certificate failure")
        assert original.tobytes() == self.seed.tobytes()
        self.latest_phase = (
            "startup"
            if self.certificate_calls <= 10
            else "search-seed"
            if self.certificate_calls == 11
            else "replay"
            if len(self.models) == 2
            else "trial"
        )
        certified = True
        if self.latest_phase == "trial":
            self.trial_index += 1
            if self.strategy == "geometry-reject":
                certified = False
            elif self.strategy == "gapped":
                certified = self.trial_index != 0
            elif self.strategy == "geometry-budget":
                certified = self.trial_index % 16 == 15
        return dict(
            status="certified" if certified else "uncertified",
            calculation_complete=True,
            certified=certified,
            complete_synthetic_proof="p" * self.padding,
            field_pass=False,
            step4_pass=False,
        )

    def invalidate(self, model):
        self.invalidations += 1
        if self.fault == "invalidate":
            raise ArithmeticError("injected invalidation failure")
        model._cache = None

    def bundle(self, model, x):
        self.bundle_calls += 1
        if self.fault == "bundle":
            raise ArithmeticError("injected bundle failure")
        assert model._cache is None
        for field, quantity, count in EXPECTED:
            model.fields[field].set_points(np.zeros((count, 3)))
            if quantity.endswith("vjp"):
                getattr(model.fields[field], quantity)(np.zeros((count, 3)))
            else:
                getattr(model.fields[field], quantity)()
        model.x, model._cache = x.copy(), {"computed": True}
        value = float(0.1 + self.gradient @ (x - self.seed))
        current = 100000.0
        if self.latest_phase == "trial" and self.strategy == "armijo-reject":
            value = 0.2
        if self.latest_phase == "trial" and self.strategy == "overcurrent":
            current = 600000.0
        return bundle_fixture(self.context, x, value=value, gradient=self.gradient, current=current)


class Harness:
    def __init__(
        self,
        path,
        *,
        nbase=6,
        method="N",
        target="reference",
        strategy="null",
        padding=0,
        native_type=EventJournal,
        controller_type=EventJournal,
        store_type=SnapshotStore,
    ):
        self.adapter = Adapter(
            context_fixture(nbase, method, target), strategy=strategy, padding=padding
        )
        self.context = copy.deepcopy(self.adapter.context)
        self.native = native_type(path / "native-events")
        self.controller = controller_type(path / "controller-events")
        self.store = store_type(path / "raw")
        self.guard = lambda: None

    def run(self):
        return run_cell(
            self.context,
            native_journal=self.native,
            controller_journal=self.controller,
            store=self.store,
            adapter=self.adapter,
            guard=self.guard,
        )

    def verify(self, reference):
        result = read_json(reference)
        events = read_events(
            self.controller._directory, result["journals"]["controller"]["receipt"]
        )
        native = read_events(self.native._directory, result["journals"]["native"]["receipt"])
        report = read_json(result["search_report"])
        verdict = audit(self.adapter.seed.tolist(), report["initial"], report, events)
        assert verdict["control_flow_pass"]
        assert not verdict["field_values_verified"] and not verdict["physical_admission"]
        assert result["producer_complete"] is True
        assert not result["physical_admission"] and not result["step4_pass"]
        assert not result["independent_audit_pass"]
        assert self.adapter.invalidations == self.adapter.bundle_calls
        certificate_refs = {r["path"]: r for r in result["certificates"]}
        for trial in report["trials"]:
            view = trial["certificate"]
            assert set(view) == {
                "status",
                "calculation_complete",
                "certified",
                "certificate_reference",
            }
            ref = view["certificate_reference"]
            assert certificate_refs[ref["path"]] == ref
            manifest = read_json(ref)
            assert manifest["case"] == self.context["case"]
            assert manifest["phase"] == "trial"
            assert manifest["operation_id"] == f"trial/certificate/{trial['index']:03d}"
            assert manifest["x"] == trial["x"]
            for key in ("status", "calculation_complete", "certified"):
                assert type(view[key]) is type(manifest["result"][key])
                assert view[key] == manifest["result"][key]
        for ref in result["bundles"]:
            bundle = read_json(ref)
            assert set(bundle) == {
                "case",
                "phase",
                "operation_id",
                "state",
                "snapshot",
                "arrays",
                "certificate",
            }
            read_arrays(bundle["arrays"])
            snapshot = read_json(bundle["snapshot"])
            assert (
                np.asarray(snapshot["base_coefficients"]).ravel().tolist() == bundle["state"]["x"]
            )
            certificate = read_json(bundle["certificate"])
            assert certificate["result"]["certified"] is True
            assert certificate["x"] == bundle["state"]["x"]
            assert certificate["phase"] == bundle["phase"]
        completed = [e for e in native if e["event"] == "operation-completed"]
        assert [e["raw_reference"] for e in completed if e["kind"] == "bundle"] == result["bundles"]
        assert [e["raw_reference"] for e in completed if e["kind"] == "certificate"] == result[
            "certificates"
        ]
        return result, report, events


@pytest.mark.parametrize("nbase,method", [(6, "N"), (6, "V"), (8, "N"), (8, "V")])
def test_complete_null_paths_for_both_classes_and_methods(tmp_path, nbase, method):
    h = Harness(tmp_path, nbase=nbase, method=method, target="selected")
    result, report, events = h.verify(h.run())
    assert report["reason"] == "null-direction" and report["selected_index"] is None
    assert result["counts"]["native"] == {"attempted": 110, "completed": 110}
    assert len(result["bundles"]) == len(result["certificates"]) == 12
    assert len(h.adapter.models) == 2
    assert h.adapter.models[0] is not h.adapter.models[1]
    assert all(model.seed_x.tobytes() == h.adapter.seed.tobytes() for model in h.adapter.models)
    assert read_json(result["selected_bundle"])["phase"] == "search-seed"
    assert read_json(result["replay_bundle"])["phase"] == "replay"
    screen = read_json(result["startup_screen"])
    assert screen["startup_screen_pass"] and len(screen["checks"]) == 4
    assert not screen["independently_supplied_values"]
    assert events[0]["event"] == "search_started" and events[-1]["event"] == "search_complete"


def test_gapped_proposals_select_actual_accepted_bundle_and_hit_field_budget(tmp_path):
    h = Harness(tmp_path, strategy="gapped")
    result, report, events = h.verify(h.run())
    assert report["reason"] == "field-budget"
    assert report["selected_index"] == 20
    assert report["trials"][0]["reason"] == "geometry-rejected"
    assert read_json(result["selected_bundle"])["operation_id"] == "trial/bundle/020"
    trial_ids = [
        read_json(r)["operation_id"] for r in result["bundles"] if read_json(r)["phase"] == "trial"
    ]
    assert trial_ids == [f"trial/bundle/{i:03d}" for i in range(1, 21)]
    assert result["counts"]["native"] == {"attempted": 290, "completed": 290}
    assert np.array_equal(h.adapter.models[1].seed_x, h.adapter.seed)
    assert not np.array_equal(h.adapter.models[1].x, h.adapter.seed)
    changed = copy.deepcopy(events)
    changed[-1]["result"]["selected_index"] = 0
    assert not audit(h.adapter.seed.tolist(), report["initial"], report, changed)[
        "control_flow_pass"
    ]


def test_full_116_proposal_cap_with_large_raw_certificates_has_bounded_decision_views(tmp_path):
    h = Harness(tmp_path, nbase=8, strategy="geometry-budget", padding=140000)
    result, report, events = h.verify(h.run())
    assert report["reason"] == "geometry-budget" and len(report["trials"]) == 116
    assert result["counts"]["certificate"]["trial"] == {"attempted": 116, "completed": 116}
    assert result["counts"]["bundle"]["trial"] == {"attempted": 7, "completed": 7}
    assert result["counts"]["native"] == {"attempted": 173, "completed": 173}
    assert result["search_report"]["bytes"] < 2 * 1024**2
    assert all("complete_synthetic_proof" not in t["certificate"] for t in report["trials"])
    raw = read_json(result["certificates"][11])
    assert len(raw["result"]["complete_synthetic_proof"]) == 140000
    assert events[-1]["event"] == "search_complete"


@pytest.mark.parametrize(
    "strategy,reason,trial_reason,fields",
    [
        ("geometry-reject", "certificate-limited", "geometry-rejected", 0),
        ("armijo-reject", "line-search-failed", "armijo-rejected", 16),
        ("overcurrent", "line-search-failed", "current-rejected", 16),
    ],
)
def test_negative_search_outcomes_remain_completed_negative_results(
    tmp_path, strategy, reason, trial_reason, fields
):
    h = Harness(tmp_path, strategy=strategy)
    result, report, _ = h.verify(h.run())
    assert report["reason"] == reason and report["selected_index"] is None
    assert len(report["trials"]) == 16
    assert all(t["reason"] == trial_reason for t in report["trials"])
    assert result["counts"]["bundle"]["trial"]["completed"] == fields


@pytest.mark.parametrize("fault", ["native", "certificate", "invalidate", "bundle"])
def test_adapter_failures_stop_cell_and_all_later_callbacks(tmp_path, fault):
    h = Harness(tmp_path)
    h.adapter.fault = fault
    with pytest.raises(ArithmeticError):
        h.run()
    before = len(h.adapter.native_calls)
    if h.adapter.callbacks:
        with pytest.raises(RuntimeError, match="cell failed"):
            h.adapter.callbacks[0]({})
    assert len(h.adapter.native_calls) == before
    assert not (h.store.directory / "result.json").exists()


@pytest.mark.parametrize(
    "point",
    [
        "context",
        "initialize-main",
        "startup-certificate-000",
        "startup-bundle-000-snapshot",
        "startup-bundle-000-arrays",
        "startup-bundle-000",
        "checkpoint-001",
        "result",
    ],
)
def test_every_raw_publication_boundary_stops_on_failure(tmp_path, point):
    class FaultStore(SnapshotStore):
        def _write(self, name, *args):
            if name == point:
                raise OSError("injected " + point)
            return super()._write(name, *args)

    h = Harness(tmp_path, store_type=FaultStore)
    with pytest.raises(OSError, match="injected"):
        h.run()
    before = len(h.adapter.native_calls)
    if h.adapter.callbacks:
        with pytest.raises(RuntimeError, match="cell failed"):
            h.adapter.callbacks[0]({})
    assert len(h.adapter.native_calls) == before
    events = read_events(h.native._directory, h.native.receipt)
    if point == "checkpoint-001":
        assert events[-1]["event"] == "operation-completed"
        assert events[-1]["kind"] == "bundle"
        assert (h.store.directory / "startup-bundle-000.json").exists()
    assert not (h.store.directory / "result.json").exists()


@pytest.mark.parametrize("journal_kind", ["native", "controller"])
def test_journal_failures_stop_entire_cell(tmp_path, journal_kind):
    class FailingJournal(EventJournal):
        def __call__(self, event):
            if self.receipt["records"] == 1:
                raise OSError("injected journal failure")
            return super().__call__(event)

    h = Harness(tmp_path, strategy="linear", **{journal_kind + "_type": FailingJournal})
    with pytest.raises(OSError, match="journal"):
        h.run()
    before = len(h.adapter.native_calls)
    with pytest.raises(RuntimeError, match="cell failed"):
        h.adapter.callbacks[0]({})
    assert len(h.adapter.native_calls) == before
    if journal_kind == "controller":
        assert len(h.adapter.native_calls) == 100
        assert len(read_events(h.controller._directory, h.controller.receipt)) == 1


def test_guard_failure_after_completed_prefix_stops_before_next_bundle_native_work(tmp_path):
    h = Harness(tmp_path)

    def guard():
        if h.adapter.bundle_calls >= 2:
            raise TimeoutError("injected guard failure")

    h.guard = guard
    with pytest.raises(TimeoutError, match="guard"):
        h.run()
    assert len(h.adapter.native_calls) == 10
    first = h.store.directory / "startup-bundle-000.json"
    assert first.exists()
    before = first.read_bytes()
    with pytest.raises(RuntimeError, match="cell failed"):
        h.adapter.callbacks[0]({})
    assert first.read_bytes() == before


@pytest.mark.parametrize("hook", ["initialize", "certificate", "invalidate", "bundle"])
def test_swallowed_native_callback_errors_poison_the_whole_cell(tmp_path, hook):
    h = Harness(tmp_path)
    original = getattr(h.adapter, hook)

    def swallowed(*args):
        value = original(*args)
        with pytest.raises(ValueError):
            h.adapter.callbacks[0]({})
        return value

    setattr(h.adapter, hook, swallowed)
    with pytest.raises(RuntimeError, match="cell failed"):
        h.run()
    before = len(h.adapter.native_calls)
    with pytest.raises(RuntimeError, match="cell failed"):
        h.adapter.callbacks[0]({})
    assert len(h.adapter.native_calls) == before


def test_swallowed_snapshot_poison_cannot_return_a_successful_manifest(tmp_path):
    class SwallowingStore(SnapshotStore):
        def json(self, name, value):
            reference = super().json(name, value)
            if name == "initialize-main":
                try:
                    super().json("invalid/name", {})
                except ValueError:
                    pass
            return reference

    h = Harness(tmp_path, store_type=SwallowingStore)
    with pytest.raises(RuntimeError, match="cell failed"):
        h.run()
    assert len(h.adapter.native_calls) == 1
    events = read_events(h.native._directory, h.native.receipt)
    assert not any(e["event"] == "operation-completed" for e in events)


def test_swallowed_controller_journal_poison_stops_before_certificate_dispatch(tmp_path):
    class SwallowingJournal(EventJournal):
        def __call__(self, value):
            receipt = super().__call__(value)
            try:
                super().__call__({"bad": np.nan})
            except ValueError:
                pass
            return receipt

    h = Harness(tmp_path, strategy="linear", controller_type=SwallowingJournal)
    with pytest.raises(RuntimeError, match="cell failed"):
        h.run()
    assert len(h.adapter.native_calls) == 100
    assert h.adapter.certificate_calls == 11


@pytest.mark.parametrize("stage", ["historical", "startup-repeat", "search-seed", "replay"])
def test_each_exact_bundle_replay_is_required(tmp_path, stage):
    h = Harness(tmp_path)
    original = h.adapter.bundle

    def mutated(model, x):
        value = original(model, x)
        matched = {
            "historical": h.adapter.bundle_calls == 1,
            "startup-repeat": h.adapter.bundle_calls == 10,
            "search-seed": h.adapter.bundle_calls == 11,
            "replay": len(h.adapter.models) == 2,
        }[stage]
        if matched:
            value["arrays"]["boundary_B"][0, 0] = 1e-20
        return value

    h.adapter.bundle = mutated
    with pytest.raises(ValueError, match="replay array"):
        h.run()
    assert (
        h.adapter.bundle_calls
        == {"historical": 1, "startup-repeat": 10, "search-seed": 11, "replay": 12}[stage]
    )
    assert not (h.store.directory / "result.json").exists()


def test_incomplete_bundle_cannot_reach_equality_or_operation_completion(tmp_path):
    h = Harness(tmp_path)
    original = h.adapter.bundle

    def incomplete(model, x):
        value = original(model, x)
        value["arrays"].pop("inner_A")
        return value

    h.adapter.bundle = incomplete
    with pytest.raises(ValueError, match="sixteen"):
        h.run()
    events = read_events(h.native._directory, h.native.receipt)
    assert not any(e["event"] == "operation-completed" and e["kind"] == "bundle" for e in events)


def test_changed_context_is_rejected_before_model_construction(tmp_path):
    h = Harness(tmp_path)
    h.context["seed"]["names"].reverse()
    with pytest.raises(ValueError):
        h.run()
    assert not h.adapter.models and not h.adapter.native_calls


def test_nonempty_or_shared_journals_are_not_a_new_cell(tmp_path):
    h = Harness(tmp_path)
    h.native({"previous": "work"})
    with pytest.raises(ValueError, match="fresh empty"):
        h.run()
    assert not h.adapter.native_calls
    h.controller = h.native
    with pytest.raises(ValueError, match="distinct"):
        h.run()


def test_public_api_has_no_native_default():
    with pytest.raises(TypeError):
        run_cell(context_fixture())


def test_guard_cannot_swallow_a_nested_callback_failure(tmp_path):
    h = Harness(tmp_path)

    def guard():
        if h.adapter.bundle_calls == 1:
            try:
                h.adapter.callbacks[0]({})
            except ValueError:
                pass

    h.guard = guard
    with pytest.raises(RuntimeError, match="cell failed"):
        h.run()
    assert len(h.adapter.native_calls) == 1
    assert not (h.store.directory / "startup-bundle-000.json").exists()


def test_native_journal_cannot_swallow_its_own_poison(tmp_path):
    class SwallowingJournal(EventJournal):
        def __call__(self, event):
            receipt = super().__call__(event)
            try:
                super().__call__({"bad": float("nan")})
            except ValueError:
                pass
            return receipt

    h = Harness(tmp_path, native_type=SwallowingJournal)
    with pytest.raises(RuntimeError, match="cell failed"):
        h.run()
    assert not h.adapter.models and not h.adapter.native_calls


@pytest.mark.parametrize("mutation", ["seed", "actual-x", "cache", "normalization"])
def test_initialized_model_contract_cannot_be_bypassed(tmp_path, mutation):
    h = Harness(tmp_path)
    initialize = h.adapter.initialize

    def changed(callback):
        model = initialize(callback)
        if mutation == "seed":
            model.seed_x[0] += 1e-3
        elif mutation == "actual-x":
            model.x[0] += 1e-3
        elif mutation == "cache":
            model._cache = {"precomputed": True}
        else:
            model.B2_scale += 1.0
        return model

    h.adapter.initialize = changed
    with pytest.raises(ValueError):
        h.run()
    assert len(h.adapter.native_calls) == 1 and h.adapter.certificate_calls == 0


def test_startup_derivative_failure_stops_before_search_seed(tmp_path):
    h = Harness(tmp_path, strategy="linear")
    original = h.adapter.bundle

    def incorrect_gradient(model, x):
        value = original(model, x)
        # Preserve exact startup seed/repeat, but corrupt one finite difference.
        if h.adapter.bundle_calls == 2:
            for key in ("J", "JN"):
                value["state"]["metrics"][key] += 1e-3
            value["state"]["value"] += 1e-3
        return value

    h.adapter.bundle = incorrect_gradient
    with pytest.raises(ValueError, match="startup screen"):
        h.run()
    assert h.adapter.certificate_calls == h.adapter.bundle_calls == 10
    assert h.controller.receipt["records"] == 0


@pytest.mark.parametrize("phase", ["startup", "search-seed", "replay"])
def test_nontrial_negative_certificate_stops_without_field_work(tmp_path, phase):
    h = Harness(tmp_path)
    original = h.adapter.certificate

    def reject(original_seed, x):
        result = original(original_seed, x)
        if h.adapter.latest_phase == phase:
            result.update(status="uncertified", certified=False)
        return result

    h.adapter.certificate = reject
    with pytest.raises(ValueError, match="must be positive"):
        h.run()
    assert h.adapter.bundle_calls == {"startup": 0, "search-seed": 10, "replay": 11}[phase]


@pytest.mark.parametrize("mutation", ["head", "counter-bool", "counter-too-large"])
def test_malformed_receipt_cannot_enter_a_checkpoint(tmp_path, mutation):
    class BadReceipt(EventJournal):
        @property
        def receipt(self):
            result = super().receipt
            if mutation == "head":
                result["head_sha256"] = "wrong"
            elif mutation == "counter-bool":
                result["records"] = False
            else:
                result["records"] = 2049
            return result

    h = Harness(tmp_path, native_type=BadReceipt)
    with pytest.raises(ValueError, match="receipt"):
        h.run()
    assert not h.adapter.native_calls


def test_invalidation_must_be_effective_before_any_bundle_callback(tmp_path):
    h = Harness(tmp_path)
    original = h.adapter.bundle
    h.adapter.invalidate = lambda model: None

    def late_repair(model, x):
        model._cache = None
        return original(model, x)

    h.adapter.bundle = late_repair
    with pytest.raises(ValueError, match="cache"):
        h.run()
    assert h.adapter.bundle_calls == 1
    assert len(h.adapter.native_calls) == 10


def test_final_publication_is_terminal_with_no_later_fallible_guard(tmp_path):
    h = Harness(tmp_path)

    def guard():
        if (h.store.directory / "result.json").exists():
            raise TimeoutError("forbidden guard after terminal publication")

    h.guard = guard
    reference = h.run()
    assert read_json(reference)["producer_complete"] is True


def test_actual_model_coordinates_must_match_returned_bundle_after_compute(tmp_path):
    h = Harness(tmp_path)
    original = h.adapter.bundle

    def relabelled(model, x):
        value = original(model, x)
        model.x[0] += 1e-4
        return value

    h.adapter.bundle = relabelled
    with pytest.raises(ValueError, match="actual model coordinates"):
        h.run()
    assert len(h.adapter.native_calls) == 10
    assert not (h.store.directory / "startup-bundle-000.json").exists()
