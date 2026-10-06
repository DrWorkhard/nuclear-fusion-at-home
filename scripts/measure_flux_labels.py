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
sys.path.insert(0, str(ROOT/"scripts"))

from diagnose_flux_quadrature import controls as analytic_controls  # noqa: E402
from qualify_saved_flux_labels import independent_label, qualified  # noqa: E402

from fusion_baselines import coil_check as check  # noqa: E402
from fusion_baselines import coil_fit as fit  # noqa: E402
from fusion_baselines import flux_labels as labels  # noqa: E402
from fusion_baselines.provenance import build_run_record  # noqa: E402
from fusion_baselines.realized_field import Target, sample_points, winding  # noqa: E402

SNAPSHOT_SHA256 = {
    "reference401": "ec1f8ce7073177d31e1dc1d44aad6478169b602189b8e8b204373481da368799",
    "selected401": "c2ea45c171fd7452d5fc51395617f311bd2067f470dfd9d75a0fcf02896ade79",
}


SURFACES = (.1, .25, .5, .75, .9)
PHASES = (0., float(np.pi/2), float(np.pi), float(3*np.pi/2))


def launch_grid(full_grid=False):
    return ([(s, theta) for s in SURFACES for theta in PHASES] if full_grid else
            [(.25, 0.)]+[(.75, theta) for theta in PHASES])


def grid_summary(lines, controls_pass):
    rows = []
    for s in SURFACES:
        selected = [line for line in lines if line['s'] == s]
        complete = (len(selected) == 4
                    and sorted(line['theta'] for line in selected) == list(PHASES))
        passed = complete and controls_pass and all(line['passed'] for line in selected)
        values = [line['prefixes'][-1].get('label') for line in selected]
        row = dict(s=s, phases_complete=complete, numerically_qualified=bool(passed),
                   theta=[line['theta'] for line in selected], labels=values,
                   line_qualified=[line['passed'] for line in selected])
        if passed:
            row.update(max_absolute_offset=max(abs(value-s) for value in values),
                       phase_spread=max(values)-min(values),
                       phase_spread_exceeds_0_005=max(values)-min(values) > .005)
        rows.append(row)
    return rows


def save_trace(record, index, path, hit):
    """Preserve returned native data before rejecting a call that overran its deadline."""
    buffer = io.BytesIO()
    np.savez_compressed(buffer, path=path, hits=hit)
    record.save(f"line-{index}.npz", buffer.getvalue())
    record.guard()


def half_period_symmetry(field, points):
    """Require B and A to rotate with the nfp2 field before pooling R,Z sections."""
    rotation = np.array([-1., -1., 1.])
    field.set_points(np.ascontiguousarray(points))
    B, A = field.B().copy(), field.A().copy()
    field.set_points(np.ascontiguousarray(points*rotation))
    errors = dict(B=check.error(field.B(), B*rotation), A=check.error(field.A(), A*rotation))
    check.need(max(errors.values()) <= 1e-12, "half-period field symmetry failed")
    return errors


def run(snapshot_path, wout, target_id, output, seconds=900, crossings=160,
        half_period=False, start_index=None, launch_scales=None, full_grid=False,
        target_input=None):
    from simsopt.field import BiotSavart
    from simsopt.field.tracing import ToroidalTransitStoppingCriterion, compute_fieldlines

    check.need(0 < seconds <= 1800 and crossings in (160, 320), "bounded pilot required")
    check.need(not full_grid or (seconds == 1800 and half_period and crossings == 320
                                  and start_index is None
                                  and launch_scales is None),
               "full grid requires 1800 s, 320 turns, two sections and unchanged launch grid")
    check.need(all(os.environ.get(k) == "1" for k in (
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
        "MKL_NUM_THREADS")), "one-thread execution required")
    check.need(fit.shutil.disk_usage(ROOT).free >= fit.START_RESERVE, "3 GiB reserve required")
    started = time.monotonic()
    record = fit.Recorder(output, started+seconds)
    report = dict(kind="realized-flux-label-grid" if full_grid else "realized-flux-label-pilot",
                  completed=False, target_id=target_id, full_grid=full_grid,
                  provenance=build_run_record(ROOT), lines=[], controls=[],
                  requested_crossings=crossings*(2 if half_period else 1),
                  requested_transits=crossings, half_period_sections=half_period,
                  selected_start_index=start_index,
                  orientation="counterclockwise in R,Z; section normal minus e_phi",
                  physical_admission=False, flux_surface_proven=False)
    try:
        sources = {}
        spec = check.target_spec(target_id)
        check.bind(wout, spec["wout_sha256"], sources)
        check.bind(snapshot_path, SNAPSHOT_SHA256[target_id], sources)
        input_path = ROOT/spec["input"] if target_input is None else target_input
        check.bind(input_path, spec["input_sha256"], sources)
        for path in [Path(__file__), ROOT/'scripts/qualify_saved_flux_labels.py',
                     ROOT/'scripts/diagnose_flux_quadrature.py',
                     *sorted((ROOT/"src/fusion_baselines").glob("*.py"))]:
            check.bind(path, check.digest(path), sources)
        if full_grid:
            protocol = ROOT/'docs/optimization/ISSUE48_FULL_GRID.md'
            check.bind(protocol, check.digest(protocol), sources)
        starts = launch_grid(full_grid)
        scales = np.ones(len(starts))
        if launch_scales is not None:
            check.bind(launch_scales, check.digest(launch_scales), sources)
            scales = np.asarray(check.read_json(launch_scales), dtype=float)
            check.need(scales.shape == (5,) and np.isfinite(scales).all()
                       and np.all((scales >= .95) & (scales <= 1.05)) and scales[0] == 1.,
                       "five bounded scales with unchanged control launch required")
        report["launch_scales"] = scales.tolist()
        report["sources_before"] = dict(sources)
        snapshot = check.read_json(snapshot_path)
        coils, _, mapping = check.native_coils(snapshot, 512, target_id)
        report.update(current_A=1e5*snapshot["scale"], mapping=mapping)
        field = BiotSavart(coils)
        data = check.read_json(input_path)
        target = Target.from_wout(wout, data)
        center = np.array(target.axis(0.))
        theta = np.linspace(0, 2*np.pi, 2048, endpoint=False)
        edge = np.column_stack(target.rz(1., theta, np.zeros_like(theta)))
        edge_spline, _ = labels.polar_contour(edge, center)
        grids, radial = ((256, 512), 12) if crossings == 160 else ((1024, 2048), 24)
        report.update(radial_quadrature=radial,
                      quadrature_kind='interval Gauss' if full_grid else 'uniform periodic')
        interval_orders = (4, 8) if full_grid else None
        if full_grid:
            report['analytic_controls'] = analytic_controls(record.guard)
            check.need(all(row['passed'] for row in report['analytic_controls']),
                       'analytic controls failed')
            report['interval_orders'] = interval_orders
            edge_values = labels.interval_flux_integrals(field, edge_spline, center,
                                                         guard=record.guard)
        else:
            report['quadrature_grids'] = grids
            edge_values = labels.flux_integrals(field, edge_spline, center, grids[-1], radial,
                                                record.guard)
        edge_flux = edge_values["line_flux"]
        original_points, original_tangent = fit.loop_geometry(data, 512)
        field.set_points(original_points)
        original_flux = float(np.mean(np.sum(field.A()*original_tangent, axis=1)))
        if half_period:
            check.need(np.max(abs(np.asarray(target.axis(np.pi))-center)) <= 1e-12,
                       "target axis differs across equivalent sections")
            symmetry_points = sample_points(target, np.random.default_rng(4807), 64)
            report["half_period_symmetry"] = half_period_symmetry(field, symmetry_points)
        report.update(center_RZ=center.tolist(), edge=edge_values,
                      target_oriented_flux=original_flux,
                      target_flux_relative_error=abs(original_flux/spec["flux"]-1),
                      polar_edge_magnitude_error=abs(abs(edge_flux/original_flux)-1))
        check.need(report["target_flux_relative_error"] < 1e-6, "frozen edge flux mismatch")
        check.need(report["polar_edge_magnitude_error"] < 1e-5, "polar edge control failed")
        control_arrays = dict(edge=edge, center=center)
        for s in SURFACES if full_grid else (0.25, 0.75):
            exact = np.column_stack(target.rz(s, theta, np.zeros_like(theta)))
            spline, _ = labels.polar_contour(exact, center)
            dense = (labels.interval_flux_integrals(field, spline, center, guard=record.guard)
                     if full_grid else labels.flux_integrals(
                         field, spline, center, grids[-1], radial, record.guard))
            indices = np.sort(np.random.default_rng(4806).choice(len(exact), 160, replace=False))
            sample = exact[indices]
            control_arrays[f's{s}'] = exact
            control_arrays['sample_indices'] = indices
            control = labels.contour_diagnostics(field, sample, center, edge_flux, record.guard,
                                                  grids, radial, interval_orders)
            control.update(s=s, exact_flux=dense["line_flux"],
                           label_error=abs(control["label"]-dense["line_flux"]/edge_flux))
            report["controls"].append(control)
        if full_grid:
            buffer = io.BytesIO()
            np.savez_compressed(buffer, **control_arrays)
            record.save('control-contours.npz', buffer.getvalue())
            report['control_arrays_sha256'] = check.digest(output/'control-contours.npz')
        record.save("inputs.json", report)
        for index, (s, theta0) in enumerate(starts):
            if start_index is not None and index != start_index:
                continue
            record.guard()
            r, z = labels.scaled_launch(target.rz(s, theta0, 0.), center, scales[index])
            record.save(f'line-{index}-attempt.json', dict(index=index, s=s, theta=theta0,
                        actual_start_RZ=[float(r), float(z)]))
            paths, hits = compute_fieldlines(field, [float(r)], [float(z)], tmax=4800.,
                                             tol=1e-10, phis=[0., np.pi] if half_period else [0.],
                                             stopping_criteria=[
                                                 ToroidalTransitStoppingCriterion(
                                                     crossings+1, False)])
            path, hit = paths[0], hits[0]
            save_trace(record, index, path, hit)
            if len(hit) and hit[-1, 1] < 0 and hit[-1, 0] > path[-1, 0]:
                path = np.vstack((path, hit[-1, [0, 2, 3, 4]]))
            turns, iota = winding(path[:, 1:4], target)
            section_hits = hit[hit[:, 1] >= 0]
            # Exclude the launch event if this native version includes it.
            section_hits = section_hits[section_hits[:, 0] > 1e-8]
            section_hits = section_hits[np.argsort(section_hits[:, 0], kind="stable")]
            rz = np.column_stack((np.hypot(section_hits[:, 2], section_hits[:, 3]),
                                  section_hits[:, 4]))
            row = dict(index=index, s=s, theta=theta0, launch_scale=float(scales[index]),
                       actual_start_RZ=[float(r), float(z)],
                       transits=turns, iota=iota, prefixes=[],
                       crossings_per_turn=2 if half_period else 1)
            for count in (crossings//4, crossings//2, crossings):
                count *= row["crossings_per_turn"]
                try:
                    check.need(len(rz) >= count, "insufficient completed section crossings")
                    result = labels.contour_diagnostics(field, rz[:count], center, edge_flux,
                                                        record.guard, grids, radial,
                                                        interval_orders)
                    if full_grid and count == 640:
                        independent = independent_label(snapshot, rz[:count], center,
                                                        edge_flux, record)
                        result.update(independent_label=independent,
                                      independent_label_error=abs(result['label']-independent))
                    row["prefixes"].append(dict(requested=count, **result))
                except ValueError as exc:
                    row["prefixes"].append(dict(requested=count, error=str(exc)))
            if half_period:
                row["planes"] = []
                for plane in (0, 1):
                    mask = section_hits[:, 1] == plane
                    plane_rz = rz[mask][:crossings]
                    try:
                        check.need(len(plane_rz) == crossings, "incomplete plane coverage")
                        result = labels.contour_diagnostics(field, plane_rz, center, edge_flux,
                                                            record.guard, grids, radial,
                                                            interval_orders)
                        row["planes"].append(dict(plane=plane, **result))
                    except ValueError as exc:
                        row["planes"].append(dict(plane=plane, error=str(exc)))
                row["plane_hit_counts"] = [int(np.sum(section_hits[:, 1] == p)) for p in (0, 1)]
            if full_grid:
                row.update(qualified(row, edge_flux, expected_label=None))
            report["lines"].append(row)
            record.save("progress-labels.json", report)
            print(f"{target_id} line {index}: {turns:.1f} transits", flush=True)
        if full_grid:
            report['controls_pass'] = bool(len(report['controls']) == 5
                and all(control['label_error'] < 5e-4 for control in report['controls'])
                and edge_values['stokes_abs_error']/abs(edge_flux) < 1e-5)
            report['surface_summary'] = grid_summary(report['lines'], report['controls_pass'])
            report['all_points_numerically_qualified'] = all(
                row['numerically_qualified'] for row in report['surface_summary'])
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
    parser.add_argument("--crossings", type=int, choices=(160, 320), default=160,
                        help="full-turn sample count; --half-period doubles section crossings")
    parser.add_argument("--half-period", action="store_true")
    parser.add_argument("--start-index", type=int, choices=range(5))
    parser.add_argument("--launch-scales", type=Path)
    parser.add_argument("--full-grid", action="store_true",
                        help="measure all five surfaces/four geometric phases without matching")
    parser.add_argument("--target-input", type=Path,
                        help="explicit original hash-bound target JSON, if not in this checkout")
    args = parser.parse_args()
    raise SystemExit(run(args.snapshot.resolve(), args.wout.resolve(), args.target,
                         args.output.resolve(), args.seconds, args.crossings,
                         args.half_period, args.start_index, args.launch_scales,
                         args.full_grid, args.target_input))
