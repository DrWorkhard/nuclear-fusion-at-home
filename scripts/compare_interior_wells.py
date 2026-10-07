"""One frozen comparison of interior error and target-launched shallow-well coverage."""

import time

START, WALL_START = time.monotonic(), time.time()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.metadata  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CANDIDATES = {
    "reference": ("examples/clear-coil-interior-v1/reference401-candidate.json",
                  "2046cb9f0a7bdd4d0b1aabe9779ab954dfd8d6c8ffae8e62d03c5bca64e81d48"),
    "continuation": ("submissions/interior-pass-headroom-continuation/candidate.json",
                     "521ed4e7ac5b3c0a343545287d05bd1872ed87634939b68ba2e84f9be235dfb4"),
}
EXPECTED_FAILURES = {(0.1, 0.03), (0.25, 0.03)}
SCIENTIFIC_ERRORS = {
    "exactly two uncensored wells required on every line",
    "well family crosses its registered field period",
}
MAX_OUTPUT_BYTES, FAILURE_RESERVE = 64*1024**2, 1024**2


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_payload(record, name, value, *, failure=False):
    payload = value if isinstance(value, bytes) else (
        json.dumps(value, sort_keys=True, allow_nan=False, indent=2)+"\n").encode("utf-8")
    ceiling = MAX_OUTPUT_BYTES if failure else MAX_OUTPUT_BYTES-FAILURE_RESERVE
    need(record.storage[0]+len(payload) <= ceiling, "64 MiB output ceiling exceeded")
    record.save(name, payload)


def save_failure(record, error, revision, config_sha):
    output = record.output
    if (output/"result.json").exists():
        (output/"result.json").rename(output/"attempted-result.json")
    receipt = dict(completed=False, error=f"{type(error).__name__}: {error}"[:1024],
                   elapsed_s=time.monotonic()-START, producer_evaluator=revision,
                   config_sha256=config_sha,
                   decision=dict(verdict="inconclusive", reason="execution failed"),
                   retained_files=sorted(p.name for p in output.iterdir() if p.is_file()))
    # A separate name preserves a failed result.json.tmp without retrying its publication.
    save_payload(record, "failure.json", receipt, failure=True)
    return receipt


def clean_head(revision):
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    need(head == revision and not dirty, "Exact clean producer/evaluator revision required")


def verify_environment(path, guard):
    document = json.loads(path.read_bytes())
    need(sys.version == document["python"], "Frozen Python version required")
    need(digest(sys.executable) == document["executable_sha256"], "Python executable changed")
    count = 0
    for name, row in document["packages"].items():
        distribution = importlib.metadata.distribution(name)
        need(distribution.version == row["version"], "Native package version changed")
        for relative, expected in row["files"].items():
            guard()
            need(digest(distribution.locate_file(relative)) == expected,
                 f"Native package file changed: {relative}")
            count += 1
    return count


def validate_trace(trace):
    import numpy as np

    phi, alpha, field, length = (np.asarray(trace[k]) for k in ("phi", "alpha", "B", "length"))
    need(phi.ndim == 1 and alpha.shape == (16,) and field.shape == length.shape == (len(phi), 16),
         "Complete 16-launch trace arrays required")
    need(len(phi) in (801, 1601) and abs(phi[0]) < 1e-14 and abs(phi[-1]-2*np.pi) < 1e-12,
         "Two complete field periods required")
    need(all(np.isfinite(a).all() for a in (phi, alpha, field, length))
         and np.all(np.diff(phi) > 0) and np.all(np.diff(length, axis=0) > 0)
         and np.all(field > 0), "Malformed trace is not a scientific missing-well result")


def cells(trace):
    import numpy as np

    from fusion_baselines import coil_bounce as bounce
    from fusion_baselines.bounce_action import bounce_wells

    validate_trace(trace)
    rows = []
    for q in bounce.HOLD_PITCHES:
        row = dict(q=q, error=None, failed_lines=[])
        try:
            row["result"] = bounce.period_actions(trace, q)
        except ValueError as error:
            if str(error) not in SCIENTIFIC_ERRORS:
                raise
            row["error"] = str(error)
            for j in range(16):
                wells = bounce_wells(trace["length"][:, j], trace["B"][:, j],
                                     bounce.bounce_field(q))
                angles = [np.interp([w.left, w.right], trace["length"][:, j], trace["phi"])
                          for w in wells]
                crossing = len(wells) == 2 and any(lo < p*np.pi-1e-12 or hi > (p+1)*np.pi+1e-12
                           for p, (lo, hi) in enumerate(angles))
                if len(wells) != 2 or any(not w.complete for w in wells) or crossing:
                    row["failed_lines"].append(dict(alpha_index=j, well_count=len(wells),
                        censored=sum(not w.complete for w in wells), period_crossing=crossing,
                        wells=[w.record() for w in wells]))
        middle = (len(trace["phi"])-1)//2
        row["period_min_B_minus_Bbounce_T"] = [
            (np.min(trace["B"][a:b], axis=0)-bounce.bounce_field(q)).tolist()
            for a, b in ((0, middle+1), (middle, len(trace["phi"])))
        ]
        rows.append(row)
    return rows


def compare(arms, ideal, interior_rms):
    import numpy as np

    masks, maximum = {}, 0.0
    for label, surfaces in {"ideal": ideal, **arms}.items():
        failed = {}
        for n in (801, 1601):
            failed[n] = {(r["s"], c["q"]) for r in surfaces for c in r[str(n)] if c["error"]}
        if failed[801] != failed[1601]:
            return dict(verdict="inconclusive", reason=f"unstable failed-cell mask: {label}")
        masks[label] = sorted(failed[1601])
        for surface in surfaces:
            for coarse, fine in zip(surface["801"], surface["1601"], strict=True):
                if coarse["error"] or fine["error"]:
                    continue
                error = float(np.max(np.abs(np.asarray(fine["result"]["actions"])
                                             / coarse["result"]["actions"]-1)))
                maximum = max(maximum, error)
    result = dict(failed_cells=masks, max_individual_action_refinement=maximum,
                  core_restored=not (EXPECTED_FAILURES & set(map(tuple, masks["continuation"]))))
    if masks["ideal"] or set(map(tuple, masks["reference"])) != EXPECTED_FAILURES:
        return dict(**result, verdict="inconclusive", reason="ideal/reference control mismatch")
    if maximum > 1e-3:
        return dict(**result, verdict="inconclusive", reason="individual action refinement")
    if not (interior_rms <= 0.0021 and interior_rms < 0.01071651709510873/4):
        return dict(**result, verdict="inconclusive", reason="interior contrast not reproduced")
    verdict = ("lower-interior-error-insufficient" if masks["continuation"]
               else "promising-association")
    return dict(**result, verdict=verdict, reason="target-launch well coverage only")


def run(config_path, config_sha, output, revision):
    clean_head(revision)
    need(digest(config_path) == config_sha, "Frozen configuration changed")
    config = json.loads(config_path.read_bytes())
    need(all(os.environ.get(key) == "1" for key in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS")),
         "One native thread required")
    need(shutil.disk_usage(output.parent).free >= 3*1024**3, "3 GiB initial reserve required")
    paths = [Path(__file__).resolve(), config_path.resolve()]
    paths += sorted((ROOT / "src/fusion_baselines").glob("*.py"))
    paths += sorted((ROOT / "src/fusion_public").glob("*.py"))
    paths += sorted((ROOT / "examples/clear-coil-samples-v1").glob("*.json"))
    paths += sorted((ROOT / "examples/clear-coil-interior-v1").glob("*.json"))
    paths += [ROOT / "evidence/plasma-design-v2/reference-input-401.json"]
    for relative, expected in CANDIDATES.values():
        need(digest(ROOT/relative) == expected, "Frozen geometry changed")
        paths.append(ROOT/relative)
    for name in ("wout", "environment"):
        path = Path(config[name]["path"])
        need(digest(path) == config[name]["sha256"], f"Frozen {name} changed")
        paths.append(path)
    sources = {str(path): digest(path) for path in paths}
    last_disk = [0.0]

    def guard():
        elapsed, wall_elapsed = time.monotonic()-START, time.time()-WALL_START
        need(max(elapsed, wall_elapsed) < 900, "900 s total budget exhausted")
        need(abs(elapsed-wall_elapsed) <= 5, "Clock discrepancy exceeds 5 s")
        if elapsed-last_disk[0] >= 1:
            need(shutil.disk_usage(output.parent).free >= 2*1024**3, "Live disk reserve exhausted")
            last_disk[0] = elapsed

    environment_files = verify_environment(Path(config["environment"]["path"]), guard)
    import numpy as np
    from simsopt.field import BiotSavart

    from fusion_baselines import coil_bounce as bounce
    from fusion_baselines import coil_check as check
    from fusion_baselines import coil_fit as fit
    from fusion_baselines import coupled_coil_audit as independent
    from fusion_baselines.realized_field import Target
    from fusion_baselines.vmec_trace import trace_geometry
    from fusion_public.data import load, load_case
    from fusion_public.dense_interior import evaluate_dense

    record = fit.Recorder(output, START+900)
    report = dict(completed=False, producer_evaluator=revision, sources_before=sources,
                  environment_files=environment_files, arms={}, ideal=[], physical_admission=False,
                  benefit_transfer_confirmed=False, realized_flux_labels_qualified=False)

    def save(name, value):
        save_payload(record, name, value)

    def arrays(name, values):
        stream = io.BytesIO()
        np.savez_compressed(stream, **values)
        save(name, stream.getvalue())

    def levels(s, trace):
        coarse = {key: trace[key][::2] for key in ("B", "length", "phi")}
        coarse["alpha"] = trace["alpha"]
        return dict(s=s, **{"801": cells(coarse), "1601": cells(trace)})

    try:
        save("inputs.json", report)
        case, _ = load_case()
        continuation = load(ROOT / CANDIDATES["continuation"][0])
        dense, magnetic = evaluate_dense(continuation, case, "reference401", 590,
                                        check_resources=guard)
        save("continuation-dense.json", dense)
        arrays("continuation-inner-B.npz", dict(B=np.asarray(magnetic)))
        data = check.read_json(ROOT / check.TARGET)
        wout = Path(config["wout"]["path"])
        need(digest(wout) == check.FIXED[check.WOUT], "Original Wout identity required")
        need(digest(ROOT/check.TARGET) == check.FIXED[check.TARGET], "Original input required")
        target = Target.from_wout(wout, data)
        ideals = {}
        for s in bounce.SURFACES:
            guard()
            ideals[s] = trace_geometry(wout, s, 1601, 16, 2)
            report["ideal"].append(levels(s, ideals[s]))
            arrays(f"ideal-s{s}.npz", ideals[s])
        for label, (relative, _) in CANDIDATES.items():
            guard()
            snapshot = check.candidate_snapshot(load(ROOT/relative), data, 256)
            if label == "reference":
                need(abs(1e5*snapshot["scale"]/307977.14904565935-1) <= 1e-12,
                     "Reference current not recovered")
            else:
                need(abs(1e5*snapshot["scale"] / dense["flux_normalized_max_abs_current_A"] - 1)
                     <= 1e-12, "Native/scalar continuation normalization disagrees")
            save(f"{label}-snapshot.json", snapshot)
            coils, own, mapping = check.native_coils(snapshot, 512)
            field, rows = BiotSavart(coils), []
            report["arms"][label] = dict(mapping=mapping, surfaces=rows,
                                         current_A=1e5*snapshot["scale"])
            for s in bounce.SURFACES:
                guard()
                actual = bounce.trace_coils(field, target, s, ideals[s], guard)
                indices = np.linspace(0, actual["B"].size-1, 64, dtype=int)
                points = actual["xyz"].reshape(-1, 3)[indices]
                direct, _ = independent.filament_field_and_potential(
                    points, own["positions"], own["tangents"], own["currents"])
                field.set_points(np.ascontiguousarray(points))
                native = field.B().copy()
                error = check.error(native, direct)
                need(error <= 1e-12, "Independent field control failed")
                need(np.max(np.abs(np.linalg.norm(direct, axis=1)
                                   - actual["B"].ravel()[indices])) <= 1e-12,
                     "Saved trace magnitude differs from independent field")
                actual.update(B_indices=indices, independent_B=direct, native_B_control=native)
                arrays(f"{label}-s{s}.npz", actual)
                rows.append(dict(**levels(s, actual), independent_field_error=error))
                save("progress.json", report)
        report["decision"] = compare(
            {name: arm["surfaces"] for name, arm in report["arms"].items()},
            report["ideal"], dense["dense_inner_vector_rms"],
        )
        report["sources_after"] = {path: digest(path) for path in sources}
        need(report["sources_after"] == sources, "Source/input changed during comparison")
        need(verify_environment(Path(config["environment"]["path"]), guard) == environment_files,
             "Native environment changed")
        clean_head(revision)
        guard()
        report.update(completed=True, elapsed_s=time.monotonic()-START)
        save("result.json", report)
        guard()
    except Exception as error:
        report = save_failure(record, error, revision, config_sha)
    print(json.dumps({key: report[key] for key in ("completed", "elapsed_s", "decision", "error")
                      if key in report}, indent=2))
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--config-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.config, args.config_sha, args.output, args.revision))
