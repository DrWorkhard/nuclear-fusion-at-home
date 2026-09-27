"""Paired 600-bundle shape52 searches: uniform versus low-mode-expanded boxes."""

import argparse
import copy
import hashlib
import importlib
import json
import shutil
import time
from contextlib import contextmanager
from pathlib import Path

import explore_constrained_coils as previous
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SLACK = "artifacts/constrained-coils-slack-v1/"
ORIGINAL = "artifacts/constrained-coils-v1/run/n6-shape-d100mm-full/"
SNAPSHOT = SLACK+"run/n6-shape-d100mm-full/selected-snapshot.json"
TRIAL, SEED = ORIGINAL+"trial-052.json", ORIGINAL+"seed.json"
ADAPTIVE, SELECTION, GEOMETRY = SLACK+"run/result.json", SLACK+"run/postselection.json", \
    SLACK+"geometry/result.json"
INPUTS = {
    **previous.INPUTS,
    "scripts/explore_constrained_coils.py":
        "675175ef038f3a0c43b51fdeb198febd90707ff53123f8ca514272b165aa87e0",
    SNAPSHOT: "2492d83ad3392069be5bfe8ae35b2e98ca0419916517e96065e017bcf15417e9",
    TRIAL: "954e8b63bbb8fc2fb3b3215c8f70c88b0f576796b43fa7e57d991bd45d66e961",
    SEED: "b3bfc3da94defbe24d58d538e99779da21eae27cddcf6f9daa421890842ff1ff",
    ADAPTIVE: "8f7861053e55944d49b6f97d44d258a4bdb1f524ce3bf87b340e3535e38dca30",
    SELECTION: "59ca0bbefa46856fdbe36fb8e199a2218faac10463d5d660950b3dab23a6fa77",
    GEOMETRY: "644abc5eb248a0e9f9f827f5aaec163157575a2a9edccb1810b6aace287d4bc2",
    "evidence/constrained-coils-slack-v1.json":
        "e7ce35627134152f54cf7882bf2c51cbbde950c80e352e58cc4079c24670d62d",
}
BUNDLES, ARM_SECONDS, SECONDS = 600, 300, 900
ARMS = ("control", "coherent")


def half_widths(arm):
    if arm not in ARMS:
        raise ValueError("fixed control/coherent arm required")
    widths = np.full(198, .02)
    if arm == "coherent":
        widths[previous.active_indices("low2")] = .08
    return widths


@contextmanager
def configuration(arm):
    if np.shape(previous.BOX) != () or previous.BOX != .02 or previous.BUNDLES != 240:
        raise ValueError("pinned runner defaults required; nested/concurrent overrides forbidden")
    old = previous.BOX, previous.BUNDLES
    previous.BOX, previous.BUNDLES = half_widths(arm), BUNDLES
    try:
        yield previous.BOX.copy()
    finally:
        previous.BOX, previous.BUNDLES = old


def solver_adapter(minimize):
    def solve(function, initial, **kwargs):
        if kwargs["method"] != "L-BFGS-B" or kwargs["options"] != dict(
                maxiter=230, maxfun=230, maxls=20, ftol=1e-12, gtol=1e-9):
            raise ValueError("pinned optimizer settings changed")
        kwargs["options"] = dict(kwargs["options"], maxiter=590, maxfun=590)
        return minimize(function, initial, **kwargs)
    return solve


def seed_inputs(source):
    from fusion_baselines.coupled_coil_audit import validate_snapshot

    seed, trial, original = copy.deepcopy(source[SNAPSHOT]), source[TRIAL], source[SEED]
    validate_snapshot(seed)
    validate_snapshot(original)
    if (seed["names"] != original["names"] or len(seed["names"]) != 198
            or not np.array_equal(np.asarray(seed["base_coefficients"]).ravel(), trial["x"])
            or (trial["index"], trial["role"], trial["status"], trial["deadline_met"])
            != (52, "search", "completed", True)
            or any(seed[k] != original[k] for k in ("target_flux", "B2_scale"))
            or any(seed[k] != trial["metrics"][k] for k in ("unit_flux", "scale"))):
        raise ValueError("exact named shape52 geometry, trial and normalization required")
    adaptive, geometry = source[ADAPTIVE], source[GEOMETRY]
    rows = [r for r in geometry["rows"] if r["label"] == "n6-shape-d100mm-full"]
    arms = [r for r in adaptive["arms"] if (r["case"], r["mode"])
            == ("n6-shape-d100mm", "full")]
    if (not all(r["completed"] and r["sources_unchanged"] for r in (adaptive, geometry))
            or len(rows) != 1 or rows[0]["snapshot"]["sha256"] != INPUTS[SNAPSHOT]
            or not rows[0]["levels"][-1]["combined_scoped_pass"] or len(arms) != 1
            or arms[0]["fine_selected"] != trial
            or not all(r["checks_pass"] for r in arms[0]["fine"])
            or source[SELECTION]["frozen"]["n6-shape-d100mm-full"] != 52):
        raise ValueError("source-bound adaptive selection and scoped geometry check required")
    anchors = {key: trial["metrics"][key] for key in (
        "unit_flux", "scale", "normal_rms", "flux_normalized_raw", "flux_objective",
        "geometry_penalty", "min_b", "coil_distance", "surface_distance")}
    return seed, anchors


class Recorder(previous.common.Recorder):
    """Shared byte accounting; failed-prefix writes remain possible after the deadline."""

    def save(self, name, value):
        payload = value if isinstance(value, bytes) else (
            json.dumps(value, allow_nan=False, sort_keys=True, indent=2)+"\n").encode("utf-8")
        path = self.output/name
        temporary = path.with_suffix(path.suffix+".tmp")
        if temporary.exists():
            raise FileExistsError("existing failed temporary output must not be overwritten")
        if self.storage[0]+len(payload) > previous.common.MAX_BYTES:
            raise OSError("256 MiB aggregate output ceiling including temporary publication")
        difference = len(payload)-(path.stat().st_size if path.exists() else 0)
        try:
            with temporary.open("xb") as stream:
                if stream.write(payload) != len(payload):
                    raise OSError("short output write; publication incomplete")
            temporary.replace(path)
        except Exception:
            # Retain failed temporary bytes and charge them against the shared cap.
            if temporary.exists():
                retained = temporary.stat().st_size
                self.storage[0] += retained
                self.bytes += retained
            raise
        self.bytes += difference
        self.storage[0] += difference

    def call(self, name, function, *args):
        self.guard()
        self.counts[name]["attempted"] += 1
        self.save("progress.json",
                  dict(native=self.counts, bundles=self.bundles, active=self.active))
        self.guard()  # A progress write must not start native work after its deadline.
        answer = function(*args)
        self.counts[name]["completed"] += 1
        self.save("progress.json",
                  dict(native=self.counts, bundles=self.bundles, active=self.active))
        self.guard()
        return answer


def publish(record, report, started):
    try:
        record.guard()
        record.save("result.json", report)
        record.guard()
    except (TimeoutError, OSError) as exc:
        report.update(completed=False, publication_error=f"{type(exc).__name__}: {exc}",
                      elapsed_s=time.monotonic()-started)
        path = record.output/"result.json"
        if path.exists():
            path.rename(record.output/"rejected-late-result.json")
        record.save("late-publication.json", dict(completed=False, error=str(exc)))
        # A short final write leaves a .tmp; preserve it under a separate failure name.
        temporary = path.with_suffix(".json.tmp")
        if temporary.exists():
            temporary.rename(record.output/"rejected-partial-result.json")
        record.save("result.json", report)
    return 0 if report["completed"] else 1


def fingerprints():
    result = previous.fingerprints()
    paths = [Path(__file__).resolve(), *(ROOT/p for p in INPUTS),
             Path(importlib.import_module("scipy.optimize._minimize").__file__).resolve()]
    result.update({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    return result


def run(output):
    from scipy.optimize import minimize

    from fusion_baselines.provenance import git_state

    started = time.monotonic()
    if output.exists():
        raise FileExistsError("fresh output directory required")
    if shutil.disk_usage(ROOT).free < previous.common.START_RESERVE:
        raise OSError("3 GiB starting reserve required")
    for name, digest in INPUTS.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"source identity changed: {name}")
    source = {name: json.loads((ROOT/name).read_text(encoding="utf-8"))
              for name in INPUTS if name.endswith(".json")}
    seed, anchors = seed_inputs(source)
    overall = Recorder(output, started+SECONDS, [0])
    report = dict(kind="paired-coherent-coil-box-exploration", sources_before=fingerprints(),
                  repository=git_state(ROOT), arms=[], completed=False, physical_admission=False,
                  seed_sha256=INPUTS[SNAPSHOT], seed_anchors=anchors,
                  limits=dict(bundles_per_arm=BUNDLES, startup_bundles=10,
                              search_seconds=ARM_SECONDS,
                              overall_seconds=SECONDS, output_bytes=previous.common.MAX_BYTES),
                  solver_options=dict(maxiter=590, maxfun=590, maxls=20, ftol=1e-12, gtol=1e-9))
    overall.save("inputs.json", report)
    try:
        for arm in ARMS:
            overall.guard()
            record = Recorder(output/arm, min(started+SECONDS, time.monotonic()+ARM_SECONDS),
                              overall.storage)
            record.counts["independent_BA"] = dict(attempted=0, completed=0)
            result = dict(arm=arm, fine=[], active_names=seed["names"], active_count=198)
            report["arms"].append(result)
            record.save("seed.json", seed)
            try:
                with configuration(arm) as widths:
                    center = np.asarray(seed["base_coefficients"]).ravel()
                    result.update(half_widths_m=widths.tolist(),
                                  lower_bounds=(center-widths).tolist(),
                                  upper_bounds=(center+widths).tolist())
                    record.save("bounds.json", result)
                    indices = previous.active_indices("full")
                    record.guard()
                    model = previous.Model(seed, source[previous.common.INPUT], record, indices)
                    record.guard()
                    result["seed_identity_error"] = model.identity_error
                    result.update(previous.search(model, record, anchors, solver_adapter(minimize)))
                    if result["status"].get("error") == "240 total coarse bundles consumed":
                        result["status"]["error"] = "600 total coarse bundles consumed"
                    record.save("search.json", result)
                    record.deadline = started+SECONDS
                    if result["startup_pass"] and result["status"]["reason"] != "failure":
                        for shift in (0., .5):
                            record.active = dict(fine_shift=shift)
                            result["fine"].append(previous.fine(seed, source[previous.common.INPUT],
                                indices, result["fine_selected"], record, shift))
            except Exception as exc:
                result["execution_error"] = f"{type(exc).__name__}: {exc}"
            finally:
                result["counts"] = record.counts
                record.save("result.json", result)
                overall.save("progress.json", report)
        report["completed"] = len(report["arms"]) == 2 and all(
            not r.get("execution_error") and r.get("startup_pass") and len(r["fine"]) == 2
            for r in report["arms"])
    except Exception as exc:
        report.update(completed=False, error=f"{type(exc).__name__}: {exc}")
    report["sources_after"] = fingerprints()
    report["sources_unchanged"] = report["sources_before"] == report["sources_after"]
    report["elapsed_s"] = time.monotonic()-started
    report["completed"] &= report["sources_unchanged"] and report["elapsed_s"] < SECONDS
    code = publish(overall, report, started)
    print(json.dumps(dict(output=str(output), completed=report["completed"])))
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output.resolve()))
