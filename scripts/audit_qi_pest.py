"""Independent scalar roots/fields and full saved-grid QI coordinate arithmetic audit."""

import argparse
import json
from pathlib import Path

import netCDF4
import numpy as np
from qi_pest_inputs import checked, frozen_sources, reference

from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.qi_pest_scalar import sample as scalar_sample
from fusion_baselines.resource_guard import GIB, space_check


def loaded(ref):
    with np.load(checked(ref), allow_pickle=False) as data:
        return dict(data)


def error(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("matched finite audit arrays required")
    if a.dtype.kind == "b" or b.dtype.kind == "b":
        return float(not np.array_equal(a, b))
    return float(abs(a-b).max()/max(1, float(abs(b).max())))


def subset(data, stride):
    return {k: v[::stride, ::stride] if v.ndim >= 2 else v for k, v in data.items()}


def metrics(new, old, straight):
    keys = ("mod_b", "radius", "height", "iota", "eu" if straight else "et",
            "ep_u" if straight else "ep")
    for key in keys:
        if (new[key].shape != old[key].shape or new[key].size == 0
                or not np.isfinite(new[key]).all() or not np.isfinite(old[key]).all()):
            raise ValueError("matched finite independent metric arrays required")
    result = {}
    for label, key in (("mod_b", "mod_b"), ("et", "eu" if straight else "et"),
                       ("ep", "ep_u" if straight else "ep")):
        result[label] = float(abs(new[key]-old[key]).max()/abs(old[key]).max())
    result["rz"] = float(max(abs(new[k]-old[k]).max() for k in ("radius", "height")) /
                          max(abs(old[k]).max() for k in ("radius", "height")))
    result["iota"] = float(abs(new["iota"].item()-old["iota"].item()))
    if not all(np.isfinite(v) for v in result.values()):
        raise ValueError("finite independent comparison scales required")
    return result


def close_dict(a, b, tolerance=1e-12):
    return set(a) == set(b) and all(np.isfinite(a[k]) and np.isfinite(b[k]) and
                                    abs(a[k]-b[k]) <= tolerance for k in a)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("new immutable QI coordinate audit required")
    root = Path(__file__).resolve().parents[1]
    source = json.loads(args.source.read_text())
    originals, sources = frozen_sources(root)
    if (source["status"] != "completed" or source["sources"] != sources
            or len(source["rows"]) != 60 or len(source["cells"]) != 16):
        raise ValueError("complete unchanged60-row/16-cell coordinate study required")
    for ref in [source["protocol"], *source["code"], *source["predecessor"]]:
        checked(ref)
    report = dict(repository=git_state(root), source=reference(args.source), status="running",
                  rows=[], cells=[], all_pass=False, new_equilibria=0,
                  independent_scalar_point_roots=0, absolute_drift_certified=False,
                  code=[reference(root/p) for p in (
                      "scripts/audit_qi_pest.py", "scripts/qi_pest_inputs.py",
                      "src/fusion_baselines/qi_pest_scalar.py",
                      "src/fusion_baselines/pest_root_audit.py")])
    old_vmec, old_pest, old_volumes = {}, {}, {}
    try:
        for i, (row, original) in enumerate(zip(source["rows"], originals, strict=True)):
            space_check(root, 2*GIB)
            if any(row[k] != v for k, v in original.items()) or row["status"] != "completed":
                raise ValueError("source row identity/status changed")
            with netCDF4.Dataset(checked(row["wout"])) as ds:
                nfp, volume = int(ds["nfp"][...]), float(ds["volume_p"][...])
            if row["nfp"] != nfp or row["volume"] != volume:
                raise ValueError("source NFP/volume mismatch")
            checks = dict(old_replay_record=bool(row["replay_pass"] and row["replay_errors"]
                          and all(np.isfinite(v) and 0 <= v <= 1e-12
                                  for v in row["replay_errors"].values())))
            saved_old = loaded(row["old_arrays"])
            pair = row["case"], row["surface"]
            if row["kind"] == "historical":
                old_vmec[pair], old_volumes[pair] = saved_old, volume
            measured = dict(index=i, case=row["case"], surface=row["surface"], checks=checks,
                            levels=[], cell=row["cell"])
            report["rows"].append(measured)
            if [g["resolution"] for g in row["levels"]] != [64, 128]:
                raise ValueError("both registered evaluation levels required")
            coarse_roots, coarse_fields = None, None
            coordinate, refined, physical = True, True, True
            previous_metrics = {}
            for level in row["levels"]:
                n = level["resolution"]
                roots = loaded(level["inversion"])
                phi, u = np.meshgrid(2*np.pi*np.arange(n)/(n*nfp),
                                     2*np.pi*np.arange(n)/n, indexing="ij")
                inversion = (roots["denominator"] > 1e-8) & (abs(roots["residual"]) <= 1e-12)
                inversion &= ~roots["encountered_nonpositive_jacobian"]
                invpass = bool(inversion.all())
                checks[f"inversion-{n}"] = bool(
                    np.array_equal(roots["u"], u) and np.array_equal(roots["phi"], phi)
                    and np.array_equal(roots["passed"], inversion)
                    and level["inversion_pass"] == invpass
                    and level["max_residual"] == float(abs(roots["residual"]).max())
                    and level["min_denominator"] == float(roots["denominator"].min())
                    and error(roots["residual"], roots["theta"]+roots["lam"]-u) <= 1e-14
                    and error(roots["denominator"], 1+roots["lt"]) <= 1e-14
                    and roots["iterations"].dtype.kind in "iu"
                    and np.all((roots["iterations"] >= 0) & (roots["iterations"] <= 50)))
                coordinate &= invpass
                local = dict(resolution=n, inversion_pass=invpass)
                measured["levels"].append(local)
                if coarse_roots is not None:
                    nested_roots = {k: error(roots[k][::2, ::2], v)
                                    for k, v in coarse_roots.items()}
                    checks["nested_root_arrays"] = max(nested_roots.values()) <= 1e-12
                    local["nested_root_errors"] = nested_roots
                coarse_roots = roots
                if not invpass:
                    checks[f"unavailable-{n}"] = "fields" not in level
                    refined = physical = False
                    continue
                fields = loaded(level["fields"])
                checks[f"fields_at_roots-{n}"] = all(error(fields[k], roots[k]) <= 1e-12
                                                     for k in ("theta", "phi", "lam", "lt", "lp"))
                if row["kind"] == "historical":
                    old_pest[pair, n] = fields
                if n == 128:
                    scalar = scalar_sample(checked(row["wout"]), row["surface"],
                                           u[::4, ::4], phi[::4, ::4])
                    report["independent_scalar_point_roots"] += 32*32
                    scalar_errors = {k: error(fields[k][::4, ::4] if fields[k].ndim >= 2
                                               else fields[k], scalar[k]) for k in (
                        "theta", "lam", "lt", "lp", "radius", "height", "mod_b",
                        "et", "ep", "eu", "ep_u", "iota")}
                    scalar_errors["theta"] = float(abs(
                        fields["theta"][::4, ::4]-scalar["theta"]).max())
                    local["independent_field_errors"] = scalar_errors
                    local["scalar_root_max_residual"] = float(abs(scalar["residual"]).max())
                    checks["scalar_roots_and_fields"] = bool(scalar["passed"].all()
                        and max(scalar_errors.values()) <= 1e-10
                        and local["scalar_root_max_residual"] <= 1e-12)
                if coarse_fields is not None:
                    nested = {k: error(fields[k][::2, ::2] if v.ndim >= 2 else fields[k], v)
                              for k, v in coarse_fields.items()}
                    checks["nested_fields"] = close_dict(nested, level["nested_errors"])
                    coordinate &= max(nested.values()) <= 1e-12
                coarse_fields = fields
                if row["kind"] == "fresh":
                    old = old_pest.get((pair, n))
                    available = old is not None
                    checks[f"reference-{n}"] = (
                        level["historical_coordinate_reference_available"] == available)
                    fresh_metrics = dict(vmec=metrics(subset(saved_old, 128//n),
                                                     subset(old_vmec[pair], 128//n), False))
                    if available:
                        fresh_metrics["pest"] = metrics(fields, old, True)
                    else:
                        physical = refined = False
                    for kind, value in fresh_metrics.items():
                        checks[f"{kind}_metrics-{n}"] = close_dict(value, level[kind+"_fidelity"])
                    vol_error = abs(volume-old_volumes[pair])/abs(old_volumes[pair])
                    checks["volume_error"] = row["volume_error"] == vol_error
                    physical &= vol_error <= 1e-3 and available and max(
                        fresh_metrics.get("pest", {"missing": 1}).values()) <= 1e-3
                    if n == 128:
                        checks["old_fidelity_preserved"] = close_dict(
                            fresh_metrics["vmec"], row["old_fidelity"])
                        checks["old_volume_preserved"] = vol_error == row["old_volume_error"]
                        changes = {kind: {k: abs(v-previous_metrics[kind][k])
                                         for k, v in values.items()}
                                   for kind, values in fresh_metrics.items()
                                   if kind in previous_metrics}
                        checks["comparison_refinement"] = (set(changes) == set(
                            level.get("error_refinement", {})) and all(close_dict(
                                v, level["error_refinement"][k]) for k, v in changes.items()))
                        refined &= set(changes) == {"vmec", "pest"} and all(
                            max(v.values()) <= 1e-5 for v in changes.values())
                    previous_metrics = fresh_metrics
            checks["coordinate_classification"] = row["coordinate_screen_pass"] == coordinate
            measured["coordinate_screen_pass"] = bool(coordinate)
            if row["kind"] == "fresh":
                measured.update(refinement_pass=bool(coordinate and refined),
                                fidelity_screen_pass=bool(coordinate and physical))
                checks["refinement_classification"] = row["refinement_pass"] == (
                    coordinate and refined)
                checks["fidelity_classification"] = row["fidelity_screen_pass"] == (
                    coordinate and physical)
            measured["all_pass"] = all(checks.values())
            print(i, measured["all_pass"], flush=True)
            write_json_atomic(args.output, report)
        for cell in range(16):
            group = [r for r in report["rows"] if r["cell"] == cell]
            expected = {k: all(r[k] for r in group) for k in (
                "coordinate_screen_pass", "refinement_pass", "fidelity_screen_pass")}
            measured = source["cells"][cell]
            if measured["cell"] != cell or any(measured[k] != v for k, v in expected.items()):
                raise ValueError("cell classification mismatch")
            report["cells"].append(dict(cell=cell, **expected))
        aggregate = dict(all_coordinate_checks_pass=all(r["coordinate_screen_pass"]
                         for r in report["rows"]),
                         all_refinement_screens_pass=all(r["refinement_pass"]
                             for r in report["cells"]),
                         all_fidelity_screens_pass=all(r["fidelity_screen_pass"]
                             for r in report["cells"]))
        report["aggregate_checks"] = {k: source[k] == v for k, v in aggregate.items()}
        report.update(status="completed", all_pass=bool(all(r["all_pass"] for r in report["rows"])
                      and all(report["aggregate_checks"].values())))
    except Exception as exc:
        report.update(status="error", error=f"{type(exc).__name__}: {exc}", all_pass=False)
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
