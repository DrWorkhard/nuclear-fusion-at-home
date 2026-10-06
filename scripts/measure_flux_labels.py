"""Bounded issue #48 pilot: flux labels of fixed coil-field Poincare contours."""

import argparse
import io
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines import flux_labels as labels  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402
from fusion_baselines.realized_field import Target, winding  # noqa: E402

SNAPSHOT_SHA256 = {
    "reference401": "ec1f8ce7073177d31e1dc1d44aad6478169b602189b8e8b204373481da368799",
    "selected401": "c2ea45c171fd7452d5fc51395617f311bd2067f470dfd9d75a0fcf02896ade79",
}


def save_trace(record, index, path, hit):
    """Preserve returned native data before rejecting a call that overran its deadline."""
    buffer = io.BytesIO()
    np.savez_compressed(buffer, path=path, hits=hit)
    record.save(f"line-{index}.npz", buffer.getvalue())
    record.guard()


def run(snapshot_path, wout, target_id, output, seconds=900, crossings=160):
    from simsopt.field import BiotSavart
    from simsopt.field.tracing import ToroidalTransitStoppingCriterion, compute_fieldlines

    check.need(0 < seconds <= 1800 and crossings in (160, 320), "bounded pilot required")
    check.need(all(os.environ.get(k) == "1" for k in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
        "MKL_NUM_THREADS")), "one-thread execution required")
    check.need(fit.shutil.disk_usage(ROOT).free >= fit.START_RESERVE, "3 GiB reserve required")
    started = time.monotonic()
    record = fit.Recorder(output, started+seconds)
    report = dict(kind="realized-flux-label-pilot", completed=False, target_id=target_id,
                  provenance=build_run_record(ROOT), lines=[], controls=[],
                  requested_crossings=crossings,
                  orientation="counterclockwise in R,Z; section normal minus e_phi",
                  physical_admission=False, flux_surface_proven=False)
    try:
        sources = {}
        spec = check.target_spec(target_id)
        check.bind(wout, spec["wout_sha256"], sources)
        check.bind(snapshot_path, SNAPSHOT_SHA256[target_id], sources)
        check.bind(ROOT/spec["input"], spec["input_sha256"], sources)
        for path in [Path(__file__), *sorted((ROOT/"src/fusion_baselines").glob("*.py"))]:
            check.bind(path, check.digest(path), sources)
        report["sources_before"] = dict(sources)
        snapshot = check.read_json(snapshot_path)
        coils, _, mapping = check.native_coils(snapshot, 512, target_id)
        report.update(current_A=1e5*snapshot["scale"], mapping=mapping)
        field = BiotSavart(coils)
        data = check.read_json(ROOT/spec["input"])
        target = Target.from_wout(wout, data)
        center = np.array(target.axis(0.))
        theta = np.linspace(0, 2*np.pi, 2048, endpoint=False)
        edge = np.column_stack(target.rz(1., theta, np.zeros_like(theta)))
        edge_spline, _ = labels.polar_contour(edge, center)
        grids, radial = ((256, 512), 12) if crossings == 160 else ((1024, 2048), 24)
        report.update(quadrature_grids=grids, radial_quadrature=radial)
        edge_values = labels.flux_integrals(field, edge_spline, center, grids[-1], radial,
                                            record.guard)
        edge_flux = edge_values["line_flux"]
        original_points, original_tangent = fit.loop_geometry(data, 512)
        field.set_points(original_points)
        original_flux = float(np.mean(np.sum(field.A()*original_tangent, axis=1)))
        report.update(center_RZ=center.tolist(), edge=edge_values,
                      target_oriented_flux=original_flux,
                      target_flux_relative_error=abs(original_flux/spec["flux"]-1),
                      polar_edge_magnitude_error=abs(abs(edge_flux/original_flux)-1))
        check.need(report["target_flux_relative_error"] < 1e-6, "frozen edge flux mismatch")
        check.need(report["polar_edge_magnitude_error"] < 1e-5, "polar edge control failed")
        for s in (0.25, 0.75):
            exact = np.column_stack(target.rz(s, theta, np.zeros_like(theta)))
            spline, _ = labels.polar_contour(exact, center)
            dense = labels.flux_integrals(field, spline, center, grids[-1], radial, record.guard)
            sample = exact[np.sort(np.random.default_rng(4806).choice(len(exact), 160,
                                                                        replace=False))]
            control = labels.contour_diagnostics(field, sample, center, edge_flux, record.guard,
                                                  grids, radial)
            control.update(s=s, exact_flux=dense["line_flux"],
                           label_error=abs(control["label"]-dense["line_flux"]/edge_flux))
            report["controls"].append(control)
        record.save("inputs.json", report)
        starts = [(0.25, 0.)]+[(0.75, float(t)) for t in (0., np.pi/2, np.pi, 3*np.pi/2)]
        for index, (s, theta0) in enumerate(starts):
            record.guard()
            r, z = target.rz(s, theta0, 0.)
            paths, hits = compute_fieldlines(field, [float(r)], [float(z)], tmax=4800.,
                                             tol=1e-10, phis=[0.], stopping_criteria=[
                                                 ToroidalTransitStoppingCriterion(
                                                     crossings+1, False)])
            path, hit = paths[0], hits[0]
            save_trace(record, index, path, hit)
            if len(hit) and hit[-1, 1] < 0 and hit[-1, 0] > path[-1, 0]:
                path = np.vstack((path, hit[-1, [0, 2, 3, 4]]))
            turns, iota = winding(path[:, 1:4], target)
            section_hits = hit[hit[:, 1] == 0]
            # Exclude the launch event if this native version includes it.
            section_hits = section_hits[section_hits[:, 0] > 1e-8]
            rz = np.column_stack((np.hypot(section_hits[:, 2], section_hits[:, 3]),
                                  section_hits[:, 4]))
            row = dict(s=s, theta=theta0, transits=turns, iota=iota, prefixes=[])
            for count in (crossings//4, crossings//2, crossings):
                try:
                    check.need(len(rz) >= count, "insufficient completed section crossings")
                    result = labels.contour_diagnostics(field, rz[:count], center, edge_flux,
                                                        record.guard, grids, radial)
                    row["prefixes"].append(dict(requested=count, **result))
                except ValueError as exc:
                    row["prefixes"].append(dict(requested=count, error=str(exc)))
            report["lines"].append(row)
            record.save("progress-labels.json", report)
            print(f"{target_id} line {index}: {turns:.1f} transits", flush=True)
        report["sources_after"] = {p: check.digest(p) for p in sources}
        check.need(sources == report["sources_after"], "sources changed during pilot")
        record.guard()
        report["completed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    record.finish(report, started)
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--wout", required=True, type=Path)
    parser.add_argument("--target", required=True, choices=tuple(check.TARGETS))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seconds", type=float, default=900)
    parser.add_argument("--crossings", type=int, choices=(160, 320), default=160)
    args = parser.parse_args()
    raise SystemExit(run(args.snapshot.resolve(), args.wout.resolve(), args.target,
                         args.output.resolve(), args.seconds, args.crossings))
