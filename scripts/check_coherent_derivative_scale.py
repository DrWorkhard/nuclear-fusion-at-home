"""Thirty-bundle component derivative diagnostic; never authorizes optimization."""

import argparse
import copy
import hashlib
import json
import shutil
import time
from pathlib import Path

import explore_coherent_coils as paired
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FAILED = "artifacts/coherent-coils-v1/run/result.json"
INPUTS = {
    **paired.INPUTS,
    FAILED: "b371d45a07c5ed197b2c9fd56112d66474448036c29f29b4232a31dafeb813a2",
    "scripts/explore_coherent_coils.py":
        "b5d1b8af0b077e751547d5d6f92fb16477609f0f0e9ebaee20ca31b81289f33c",
    "tests/test_explore_coherent_coils.py":
        "c0ccd28ee5cef78ad26c6faa7d1221cd828581722e4a6154675c125f14b0a1b7",
}
STEPS = (2e-5, 1e-5, 5e-6, 2.5e-6, 1.25e-6, 6.25e-7, 3.125e-7)
BUNDLES, SECONDS, MAX_BYTES = 30, 180, 64*1024**2
COMPONENTS = ("total", "flux", "geometry")


class Recorder(paired.Recorder):
    def save(self, name, value):
        payload = value if isinstance(value, bytes) else (
            json.dumps(value, allow_nan=False, sort_keys=True, indent=2)+"\n").encode("utf-8")
        if self.storage[0]+len(payload) > MAX_BYTES:
            raise OSError("64 MiB diagnostic output ceiling including temporary publication")
        super().save(name, payload)


def component_comparison(seed, plus, minus, direction, h, preceding=None):
    if not np.isfinite(h) or h <= 0:
        raise ValueError("positive finite derivative step required")
    answer = {}
    for component in COMPONENTS:
        analytic = float(np.asarray(seed["gradients"][component])@direction)
        p, m = plus["values"][component], minus["values"][component]
        finite = (p-m)/(2*h)
        error = abs(finite-analytic)
        ratio = (preceding[component]["error"]/error
                 if preceding is not None and error > 0 else None)
        if (not np.isfinite([analytic, p, m, finite, error]).all()
                or ratio is not None and not np.isfinite(ratio)):
            raise ValueError("nonfinite derived component comparison")
        answer[component] = dict(analytic=analytic, plus=p, minus=m, finite_difference=finite,
            error=error, threshold_met=error <= 1e-7 or
            error <= 1e-4*max(abs(analytic), abs(finite)),
            preceding_error_ratio=ratio)
    return answer


def diagnose(model, record, anchors):
    report = dict(comparisons=[], completed=False, physical_admission=False,
                  search_authorized=False, derivative_policy_changed=False)
    record.counts["component_geometry_dJ"] = dict(attempted=0, completed=0)
    rows = []

    def evaluate(x, role, **metadata):
        record.guard()
        if record.bundles >= BUNDLES:
            raise StopIteration("30 total diagnostic bundles consumed")
        index = record.bundles
        record.bundles += 1
        record.active = dict(bundle=index, role=role, **metadata)
        row = dict(index=index, role=role, x=np.asarray(x).tolist(), status="attempted",
                   native_before=copy.deepcopy(record.counts), **metadata)
        name = f"trial-{index:02}"
        record.save(name+"-attempt.json", row)
        try:
            value, gradient, metrics = model.evaluate(x)
            record.guard()
            partials = record.call("component_geometry_dJ",
                                   lambda: model.geometry.dJ(partials=True))
            geometry = paired.previous.common.canonical_gradient(model.curves, partials)
            flux = gradient-geometry
            if (np.shape(gradient) != (198,) or not np.isfinite([gradient, geometry, flux]).all()
                    or value != metrics["flux_objective"]+metrics["geometry_penalty"]):
                raise ValueError("exact total/component identity required")
            row.update(value=value, gradient=gradient.tolist(), metrics=metrics,
                       values=dict(total=value, flux=metrics["flux_objective"],
                                   geometry=metrics["geometry_penalty"]),
                       gradients=dict(total=gradient.tolist(), flux=flux.tolist(),
                                      geometry=geometry.tolist()), status="completed")
            record.guard()
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            row["native_after"] = copy.deepcopy(record.counts)
            record.save(name+".json", row)
        record.guard()
        rows.append(row)
        return row

    try:
        seed = evaluate(model.x0, "seed")
        report["seed_replay"] = {key: dict(expected=value, actual=seed["metrics"][key],
            passed=bool(np.isclose(value, seed["metrics"][key], rtol=1e-10, atol=1e-12)))
            for key, value in anchors.items()}
        if not all(row["passed"] for row in report["seed_replay"].values()):
            raise ValueError("original shape52 coarse anchors failed")
        for label, function in (("sin", np.sin), ("cos", np.cos)):
            direction = function(np.arange(198)+1)
            direction /= np.linalg.norm(direction)
            preceding = None
            for h in STEPS:
                plus = evaluate(model.x0+h*direction, "probe", direction=label, h=h, sign=1)
                minus = evaluate(model.x0-h*direction, "probe", direction=label, h=h, sign=-1)
                components = component_comparison(seed, plus, minus, direction, h, preceding)
                report["comparisons"].append(dict(direction=label, vector=direction.tolist(), h=h,
                    plus_index=plus["index"], minus_index=minus["index"], components=components))
                preceding = components
        repeat = evaluate(model.x0, "repeat")
        report["exact_repeat"] = all(seed[key] == repeat[key] for key in
                                     ("value", "gradient", "metrics", "values", "gradients"))
        if not report["exact_repeat"]:
            raise ValueError("final same-seed exact component repeat failed")
        report["completed"] = len(rows) == BUNDLES
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report.update(bundles_attempted=record.bundles, bundles_completed=len(rows),
                  counts=record.counts)
    return report


def fingerprints():
    result = paired.fingerprints()
    paths = [Path(__file__).resolve(), *(ROOT/name for name in INPUTS)]
    result.update({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    return result


def run(output):
    from fusion_baselines.provenance import git_state

    started = time.monotonic()
    if output.exists():
        raise FileExistsError("fresh diagnostic output directory required")
    if shutil.disk_usage(ROOT).free < paired.previous.common.START_RESERVE:
        raise OSError("3 GiB starting reserve required")
    for name, digest in INPUTS.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"source identity changed: {name}")
    source = {name: json.loads((ROOT/name).read_text(encoding="utf-8"))
              for name in INPUTS if name.endswith(".json")}
    seed, anchors = paired.seed_inputs(source)
    failed = source[FAILED]
    if (failed["completed"] or not failed["sources_unchanged"] or failed["seed_anchors"] != anchors
            or [r["arm"] for r in failed["arms"]] != list(paired.ARMS)
            or any(r["startup_pass"] or r["bundles_attempted"] != 10 for r in failed["arms"])):
        raise ValueError("exact failed paired-startup evidence required")
    record = Recorder(output, started+SECONDS)
    report = dict(kind="coherent-component-derivative-scale-diagnostic", completed=False,
                  sources_before=fingerprints(), repository=git_state(ROOT),
                  physical_admission=False, model_configuration="control", coefficient_box_m=.02,
                  search_authorized=False, derivative_policy_changed=False, steps=list(STEPS),
                  tolerances=dict(absolute=1e-7, relative=1e-4, combination="OR"),
                  limits=dict(bundles=BUNDLES, seconds=SECONDS, output_bytes=MAX_BYTES))
    record.save("inputs.json", report)
    record.save("seed.json", seed)
    try:
        with paired.configuration("control"):
            record.guard()
            model = paired.previous.Model(seed, source[paired.previous.common.INPUT], record,
                                          paired.previous.active_indices("full"))
            record.guard()
            report["seed_identity_error"] = model.identity_error
            report.update(diagnose(model, record, anchors))
    except Exception as exc:
        report.update(completed=False, error=f"{type(exc).__name__}: {exc}")
    report["sources_after"] = fingerprints()
    report["sources_unchanged"] = report["sources_before"] == report["sources_after"]
    report["elapsed_s"] = time.monotonic()-started
    report["completed"] &= report["sources_unchanged"] and report["elapsed_s"] < SECONDS
    code = paired.publish(record, report, started)
    print(json.dumps(dict(output=str(output), completed=report["completed"])))
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output.resolve()))
