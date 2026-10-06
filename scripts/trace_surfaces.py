"""Trace a public candidate's coil field against a VMEC target; a diagnostic, not acceptance."""

import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import realized_field as rf  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402
from fusion_public.data import load, load_case, validate_candidate  # noqa: E402
from fusion_public.dense import flux_scale, load_input  # noqa: E402
from fusion_public.field import field as public_field  # noqa: E402
from fusion_public.field import physical_curves  # noqa: E402


def interpolated(field, surface, target, rng, tolerance=1e-6):
    """Smallest checked interpolant within tolerance of the direct field, else None."""
    from simsopt.field import InterpolatedField

    gamma = surface.gamma()
    radius = np.hypot(gamma[..., 0], gamma[..., 1])
    rrange = (float(radius.min()) - 0.05, float(radius.max()) + 0.05)
    ztop = float(abs(gamma[..., 2]).max()) + 0.05
    points = []
    for s, theta, phi in zip(rng.uniform(0, 0.95, 500), rng.uniform(0, 2*math.pi, 500),
                             rng.uniform(0, 2*math.pi, 500), strict=True):
        r, z = target.rz(s, theta, phi)
        points.append([float(r)*math.cos(phi), float(r)*math.sin(phi), float(z)])
    field.set_points(np.asarray(points))
    exact = field.B().copy()
    errors = {}
    for n in (48, 64, 80):
        # Stellarator symmetry: one full field period in phi, upper half in Z.
        model = InterpolatedField(field, 4, (*rrange, n), (0, math.pi, n), (0, ztop, n//2),
                                  True, nfp=2, stellsym=True)
        model.set_points(np.asarray(points))
        errors[n] = float(np.max(np.linalg.norm(model.B()-exact, axis=1)
                                 / np.linalg.norm(exact, axis=1)))
        if errors[n] <= tolerance:
            return model, errors
    return None, errors


def run(candidate_path, wout, output, transits=200, direct=False,
        snapshot_path=None, target_id="reference401"):
    from simsopt.field import BiotSavart
    from simsopt.geo import SurfaceRZFourier

    rf.need(all(os.environ.get(k) == "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")),
            "one-thread execution required")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    rf.need((candidate_path is None) != (snapshot_path is None),
            "exactly one public candidate or frozen snapshot required")
    spec = check.target_spec(target_id)
    target_input = check.read_json(check.bind(ROOT/spec["input"], spec["input_sha256"], {}))
    if target_id == "selected401":
        check.bind(wout, spec["wout_sha256"], {})
    target = rf.Target.from_wout(wout, target_input)
    report = dict(kind="realized-field-surfaces", completed=False,
                  provenance=build_run_record(ROOT), target_id=target_id,
                  target_input_sha256=spec["input_sha256"],
                  target_check="boundary/flux consistency; not dense identity",
                  wout_sha256=target.sha256, transits=transits,
                  physical_admission=False, step4_pass=False)
    if snapshot_path is not None:
        snapshot = check.read_json(snapshot_path)
        coils, own, control = check.native_coils(snapshot, 512, target_id)
        field = BiotSavart(coils)
        points = rf.sample_points(target, np.random.default_rng(20261005), 64)
        field.set_points(points)
        expected, _ = check.independent.filament_field_and_potential(
            points, own["positions"], own["tangents"], own["currents"])
        control["independent_volume"] = check.error(field.B(), expected)
        report.update(snapshot=str(snapshot_path), snapshot_sha256=check.digest(snapshot_path),
                      current_A=1e5*snapshot["scale"], frozen_current=True)
        label = Path(snapshot_path).parent.name
    else:
        rf.need(target_id == "reference401", "public candidate tracing requires reference401")
        candidate = validate_candidate(load(candidate_path))
        case, _ = load_case()
        public_current = abs(case["physical"][0]["current"])
        scale = flux_scale(candidate, case, load_input(case))
        report.update(candidate=str(candidate_path),
                      candidate_sha256=hashlib.sha256(Path(candidate_path).read_bytes()).hexdigest(),
                      flux_scale=scale, current_A=scale*public_current)
        reference = rf.coils(candidate, public_current)
        control = {}
        points_by_group = {key: case["groups"][key]["points_m"] for key in ("boundary", "inner")}
        points_by_group["independent_volume"] = rf.sample_points(
            target, np.random.default_rng(20261005), 64).tolist()
        for group, points in points_by_group.items():
            native = BiotSavart(reference)
            native.set_points(np.asarray(points, dtype=float))
            expected = np.asarray(public_field(
                points, physical_curves(candidate, case, 512))["B_T"])
            control[group] = float(np.max(abs(native.B()-expected)) / np.max(abs(expected)))
        field = BiotSavart(rf.coils(candidate, scale*public_current))
        label = Path(candidate_path).parent.name
    report["kernel_control"] = control
    rf.need(max(control.values()) <= 1e-12, "native coils differ from the independent kernel")
    surface = SurfaceRZFourier.from_wout(str(wout), range="full torus", nphi=128, ntheta=64)
    model, errors = (None, {}) if direct else interpolated(
        field, surface, target, np.random.default_rng(20261004))
    report["interpolation_errors"] = errors
    if model is None and not direct:
        (output/"result.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
        raise SystemExit("interpolant above 1e-6; rerun with --direct")
    report["field"] = "direct BiotSavart" if direct else "InterpolatedField degree 4"
    (output/"result.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    lines, hits = rf.trace(field if direct else model, target, surface, transits)
    report.update(completed=True, lines=lines, summary=rf.summarize(lines, transits),
                  seconds=round(time.monotonic()-started, 1))
    (output/"result.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    np.savez_compressed(output/"poincare.npz", **{f"line_{i}": hit
                                               for i, hit in enumerate(hits)})
    plot(lines, hits, target, output/"poincare.png", label)
    return report


def plot(lines, hits, target, path, label):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(11, 5))
    for index, (axis, phi) in enumerate(zip(axes, (0.0, math.pi/2), strict=True)):
        for s in (0.25, 0.5, 0.75, 1.0):
            r, z = target.rz(s, np.linspace(0, 2*math.pi, 200), np.full(200, phi))
            axis.plot(r, z, "k-" if s == 1.0 else "k:", lw=0.8)
        for line, hit in zip(lines, hits, strict=True):
            crossing = hit[hit[:, 1] == index]
            axis.scatter(np.hypot(crossing[:, 2], crossing[:, 3]), crossing[:, 4], s=0.6,
                         color=plt.cm.viridis(line["s"]))
        axis.set(title=f"{label}: phi = {phi:.3f}", xlabel="R [m]", ylabel="Z [m]", aspect="equal")
    figure.tight_layout()
    figure.savefig(path, dpi=130)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--candidate", type=Path)
    source.add_argument("--snapshot", type=Path, help="frozen-current native snapshot")
    parser.add_argument("--target", choices=tuple(check.TARGETS), default="reference401")
    parser.add_argument("--wout", type=Path, required=True, help="reference401 VMEC output")
    parser.add_argument("--output", type=Path, required=True, help="fresh directory")
    parser.add_argument("--transits", type=int, default=200)
    parser.add_argument("--direct", action="store_true", help="trace the exact coil field")
    args = parser.parse_args()
    report = run(args.candidate, args.wout, args.output, args.transits, args.direct,
                 args.snapshot, args.target)
    print(json.dumps(report["summary"], indent=1))


if __name__ == "__main__":
    main()
