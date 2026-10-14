"""Certified selection (#109) on real v3 recordings from the fitter's own search."""

import json
import time

import pytest

np = pytest.importorskip("numpy")

from fusion_baselines import certified_selection as cs  # noqa: E402
from fusion_baselines.coil_fit import Recorder, recording_settings, search  # noqa: E402

COUNT = 6*3*11
INELIGIBLE = {7: dict(lengths=[3.49]*6), 8: dict(lengths=[3.49]*6),
              12: dict(sampled_geometry_limits_met=False), 15: dict(current_limit_met=False)}


def recorded_run(tmp_path, steps=24, selection_value=True):
    """A completed v3 recording: every step improves, some steps are ineligible."""

    class Model:
        x0 = np.zeros(COUNT)

        def set_x(self, x):
            pass

        def evaluate(self, x):
            step = round(-x[0]/.001)
            metrics = dict(normal_rms=float(1+x.sum()), lengths=[3.]*6,
                           sampled_geometry_limits_met=True, current_limit_met=True,
                           scale=2.+step, unit_flux=-.01*(1+step))
            if selection_value:
                metrics["selection_value"] = metrics["normal_rms"]
            metrics.update(INELIGIBLE.get(step, {}))
            return float(1+x.sum()+.5*x@x), 1+x, metrics

    def minimize(function, x, callback, **kwargs):
        from types import SimpleNamespace
        for step in range(1, steps+1):
            function(x-.001*step)
            callback(x-.001*step)
        return SimpleNamespace(success=True, message="synthetic")

    recorder = Recorder(tmp_path/"run", time.monotonic()+30)
    physical = [dict(base_index=i % 6, flip=i >= 12, current=0.) for i in range(24)]
    recorder.save("seed.json", dict(nbase=6, nfp=2, order=5, physical=physical,
                                    base_coefficients=[[[0.]*11]*3]*6, target_id="synthetic"))
    recorder.save("inputs.json", dict(kind="normalized-coil-fit",
                                      recording=recording_settings("certified-control")))
    report = search(Model(), recorder, minimize)
    recorder.save("search.json", report)
    return recorder.output, report


def trials(run):
    return [json.loads(p.read_text()) for p in sorted(run.glob("trial-*.json"))
            if "attempt" not in p.name]


@pytest.mark.parametrize("selection_value", [True, False])
def test_checkpoints_follow_the_fitters_own_selection(tmp_path, selection_value):
    run, report = recorded_run(tmp_path, selection_value=selection_value)
    points = cs.checkpoints(run, 5)
    rows = trials(run)
    last = len(rows)-1
    assert [c for c, _ in points] == list(range(5, last+1, 5))+([last] if last % 5 else [])
    assert points[-1][1]["index"] == report["selected"]["index"]
    length_max = recording_settings("x")["constraints"]["selection"]["length_max_m"]
    for checkpoint, best in points:
        candidates = [r for r in rows[:checkpoint+1] if cs.eligible(r, length_max)]
        assert best["index"] == min(candidates, key=cs.selection_value)["index"]
    values = [cs.selection_value(best) for _, best in points]
    assert values == sorted(values, reverse=True)
    steps = {round(-cs.vector(run, r["x_ref"])[0]/.001) for r in rows
             if r["role"] == "search" and cs.eligible(r, length_max)}
    assert steps.isdisjoint(INELIGIBLE)


def test_vector_and_snapshot_match_the_recorded_trial(tmp_path):
    run, _ = recorded_run(tmp_path)
    seed = json.loads((run/"seed.json").read_text())
    best = cs.checkpoints(run, 5)[-1][1]
    x = cs.vector(run, best["x_ref"])
    snapshot = cs.snapshot(seed, best, x)
    assert np.array_equal(np.asarray(snapshot["base_coefficients"]).ravel(), x)
    assert snapshot["scale"] == best["metrics"]["scale"]
    assert snapshot["unit_flux"] == best["metrics"]["unit_flux"]
    assert [c["current"] for c in snapshot["physical"]] == [
        1e5*best["metrics"]["scale"]*(-1 if i >= 12 else 1) for i in range(24)]
    assert seed["physical"][0]["current"] == 0.
    tampered = dict(best["x_ref"], sha256="0"*64)
    with pytest.raises(ValueError, match="SHA-256"):
        cs.vector(run, tampered)


def test_select_certifies_backward_and_stops_at_the_first_pass(tmp_path):
    run, _ = recorded_run(tmp_path)
    points = cs.checkpoints(run, 2)
    distinct = list(dict.fromkeys(best["index"] for _, best in reversed(points)))
    passing = set(distinct[3:])
    certificates, calls = [], []

    def certify(row):
        calls.append(row["index"])
        return dict(status="pass" if row["index"] in passing else "unresolved")

    chosen = cs.select(points, certify, certificates)
    assert chosen["index"] == distinct[3] and calls == distinct[:4]
    assert [c["status"] for c in certificates] == ["unresolved"]*3+["pass"]
    assert certificates[0]["checkpoint"] == points[-1][0]
    certificates.clear()
    assert cs.select(points, lambda row: dict(status="unresolved"), certificates) is None
    assert len(certificates) == len(distinct)


def test_interrupted_certification_keeps_its_certificates(tmp_path):
    run, _ = recorded_run(tmp_path)
    certificates, calls = [], []

    def certify(row):
        calls.append(row["index"])
        if len(calls) == 3:
            raise TimeoutError("declared elapsed-time limit reached")
        return dict(status="unresolved")

    with pytest.raises(TimeoutError):
        cs.select(cs.checkpoints(run, 2), certify, certificates)
    assert len(certificates) == 2


@pytest.mark.parametrize("every", [0, -1, 1.5, True])
def test_checkpoint_spacing_must_be_a_positive_integer(tmp_path, every):
    run, _ = recorded_run(tmp_path, steps=3)
    with pytest.raises(ValueError, match="spacing"):
        cs.checkpoints(run, every)


def test_older_recordings_are_refused(tmp_path):
    run, _ = recorded_run(tmp_path, steps=3)
    inputs = json.loads((run/"inputs.json").read_text())
    inputs["recording"]["format"] = "fusion-coil-recording-v2"
    (run/"inputs.json").write_text(json.dumps(inputs))
    with pytest.raises(ValueError, match="v3"):
        cs.checkpoints(run, 2)
