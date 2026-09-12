"""Registered60-row old-coordinate replay followed by full new-coordinate field grids."""

import argparse
from pathlib import Path

import numpy as np
from qi_pest_inputs import checked, closed_predecessors, frozen_sources, reference
from run_jac_scaled_study import require_committed

from fusion_baselines.clebsch_field import compare_fields
from fusion_baselines.provenance import git_state, write_json_atomic
from fusion_baselines.qi_field_grid import fidelity, nested_errors
from fusion_baselines.qi_pest_fields import evaluate, grid, read_coefficients, sample
from fusion_baselines.resource_guard import GIB, space_check

KEYS = ("psi", "g", "bt", "bp", "lt", "lp", "iota", "et", "ep", "mod_b")
CODE = ("scripts/evaluate_qi_pest.py", "scripts/qi_pest_inputs.py",
        "src/fusion_baselines/qi_pest_fields.py", "src/fusion_baselines/pest_coordinates.py",
        "src/fusion_baselines/qi_field_grid.py", "src/fusion_baselines/clebsch_field.py")


def save(path, values):
    with path.open("xb") as stream:
        np.savez_compressed(stream, **values)
    return reference(path)


def array_errors(new, old):
    result = {}
    for key in old:
        a, b = np.asarray(new[key]), np.asarray(old[key])
        if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError("matching finite old-coordinate arrays required")
        result[key] = float(np.max(abs(a-b))/max(1, float(np.max(abs(b)))))
    return result


def straight_fidelity(new, old):
    return fidelity(dict(new, et=new["eu"], ep=new["ep_u"]),
                    dict(old, et=old["eu"], ep=old["ep_u"]))


def subset(arrays, stride):
    return {k: v[::stride, ::stride] if v.ndim >= 2 else v for k, v in arrays.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable QI coordinate result paths required")
    root = Path(__file__).resolve().parents[1]
    previous = closed_predecessors(root)
    source, sources = frozen_sources(root)
    protocol = root / "docs/qi/QI_PEST_FIDELITY_PROTOCOL.md"
    for path in [protocol, *(root/p for p in CODE), *(checked(r) for r in sources)]:
        require_committed(root, path)
    disk = space_check(root, 3*GIB)
    args.raw.mkdir(parents=True)
    report = dict(repository=git_state(root), status="running", sources=sources,
                  predecessor=previous, protocol=reference(protocol), disk_preflight=disk,
                  code=[reference(root/p) for p in CODE], rows=[], cells=[],
                  all_coordinate_checks_pass=False, all_fidelity_screens_pass=False,
                  old_results_reclassified=False, absolute_drift_certified=False)
    coefficients, old_arrays, historical = {}, {}, {}
    try:
        # Complete every old-coordinate replay before evaluating any new coordinates.
        for i, row in enumerate(source):
            space_check(root, 2*GIB)
            c = read_coefficients(checked(row["wout"]), row["surface"])
            coefficients[i] = c
            with np.load(checked(row["old_arrays"]), allow_pickle=False) as stored:
                old = dict(stored)
            old_arrays[i] = old
            theta, phi = grid(c["nfp"], 128)
            replay = evaluate(c, theta, phi)
            if "native" in old:
                native, clebsch, _, _ = compare_fields(**{k: replay[k] for k in KEYS})
                replay.update(native=native, clebsch=clebsch)
            errors = array_errors(replay, old)
            report["rows"].append(dict(**row, nfp=c["nfp"], volume=c["volume"],
                                        replay_errors=errors,
                                        replay_pass=max(errors.values()) <= 1e-12,
                                        status="replayed", levels=[]))
            write_json_atomic(args.output, report)
        if not all(r["replay_pass"] for r in report["rows"]):
            raise ValueError("old128-point-field replay gate failed; no new coordinates evaluated")
        print("All60 original-coordinate replays pass", flush=True)
        old_indices = {(r["case"], r["surface"]): i for i, r in enumerate(source)
                       if r["kind"] == "historical"}
        for i, row in enumerate(report["rows"]):
            space_check(root, 2*GIB)
            coarse = None
            if row["kind"] == "fresh":
                old_index = old_indices[row["case"], row["surface"]]
                old_volume = coefficients[old_index]["volume"]
                row["volume_error"] = abs(row["volume"]-old_volume)/abs(old_volume)
            for n in (64, 128):
                inversion, values = sample(coefficients[i], n)
                level = dict(resolution=n, inversion=save(args.raw/f"row-{i}-n{n}-roots.npz",
                                                         inversion),
                             inversion_pass=bool(inversion["passed"].all()),
                             max_residual=float(np.max(abs(inversion["residual"]))),
                             min_denominator=float(np.min(inversion["denominator"])))
                row["levels"].append(level)
                if values is None:
                    continue
                level["fields"] = save(args.raw/f"row-{i}-n{n}-fields.npz", values)
                if row["kind"] == "historical":
                    historical[row["case"], row["surface"], n] = (i, values)
                else:
                    old_entry = historical.get((row["case"], row["surface"], n))
                    level["historical_coordinate_reference_available"] = old_entry is not None
                    if old_entry is not None:
                        level["pest_fidelity"] = straight_fidelity(values, old_entry[1])
                    stride = 128//n
                    level["vmec_fidelity"] = fidelity(subset(old_arrays[i], stride),
                                                       subset(old_arrays[old_index], stride))
                if coarse is not None:
                    level["nested_errors"] = nested_errors(coarse, values)
                    first = row["levels"][0]
                    if row["kind"] == "fresh":
                        level["error_refinement"] = {kind: {
                            k: abs(level[kind+"_fidelity"][k]-first[kind+"_fidelity"][k])
                            for k in level[kind+"_fidelity"]} for kind in ("vmec", "pest")
                            if kind+"_fidelity" in level and kind+"_fidelity" in first}
                coarse = values
            row.update(status="completed", coordinate_screen_pass=all(
                r["inversion_pass"] and max(r.get("nested_errors", {"x": 0}).values()) <= 1e-12
                for r in row["levels"]))
            if row["kind"] == "fresh":
                refinement = row["levels"][-1].get("error_refinement", {})
                row["refinement_pass"] = (row["coordinate_screen_pass"]
                    and set(refinement) == {"vmec", "pest"} and all(
                        max(v.values()) <= 1e-5 for v in refinement.values()))
                row["fidelity_screen_pass"] = (row["coordinate_screen_pass"]
                    and row["volume_error"] <= 1e-3 and all(
                        max(g.get("pest_fidelity", {"missing": float("inf")}).values()) <= 1e-3
                        for g in row["levels"]))
            print(i, row["case"], row["surface"], row["coordinate_screen_pass"],
                  row.get("fidelity_screen_pass"), flush=True)
            write_json_atomic(args.output, report)
        for cell in range(16):
            group = [r for r in report["rows"] if r["cell"] == cell]
            report["cells"].append(dict(cell=cell, case=group[0]["case"], ns=group[0]["ns"],
                angular=group[0]["angular"], coordinate_screen_pass=all(
                    r["coordinate_screen_pass"] for r in group),
                refinement_pass=all(r["refinement_pass"] for r in group),
                fidelity_screen_pass=all(r["fidelity_screen_pass"] for r in group)))
        report.update(status="completed", all_coordinate_checks_pass=all(
            r["coordinate_screen_pass"] for r in report["rows"]),
            all_refinement_screens_pass=all(r["refinement_pass"] for r in report["cells"]),
            all_fidelity_screens_pass=all(r["fidelity_screen_pass"] for r in report["cells"]))
    except Exception as error:
        report.update(status="error", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, report)
    return 0 if report["all_coordinate_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
