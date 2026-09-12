"""Execute the fixed24-grid signed Clebsch normalization diagnostic."""

import argparse
import json
from pathlib import Path

import numpy as np

from fusion_baselines.clebsch_field import compare_fields, sample_coordinates
from fusion_baselines.provenance import git_state, sha256_file, write_json_atomic
from fusion_baselines.resource_guard import GIB, space_check


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.raw.exists():
        raise FileExistsError("new immutable diagnostic paths required")
    root = Path(__file__).resolve().parents[1]
    args.raw.mkdir(parents=True)
    result = dict(
        repository=git_state(root), status="running", all_pass=False, grids=[],
        protocol=reference(root / "docs/qi/QI_CLEBSCH_PROTOCOL.md"),
        code=[reference(root / p) for p in (
            "scripts/check_qi_clebsch.py", "src/fusion_baselines/clebsch_field.py",
            "src/fusion_baselines/vmec_trace.py")],
        convention_source=reference(
            root / "external/simsopt/src/simsopt/mhd/vmec_diagnostics.py"),
        absolute_drift_certified=False, global_qi_certified=False,
    )
    keys = ("psi", "g", "bt", "bp", "lt", "lp", "iota", "et", "ep", "mod_b")
    try:
        for case in ("nfp2-vacuum", "nfp2-beta2", "nfp3-vacuum", "nfp3-beta2"):
            source = root / f"evidence/qi-radial-action-v1/{case}.json"
            old = json.loads(source.read_text())
            wout = Path(old["wout"]["path"])
            if old["status"] != "completed" or sha256_file(wout) != old["wout"]["sha256"]:
                raise ValueError("completed unchanged historical case required")
            for surface in (0.25, 0.5, 0.75):
                for resolution in (16, 32):
                    space_check(root, 2 * GIB)
                    row = dict(case=case, source=reference(source), wout=reference(wout),
                               surface=surface, resolution=resolution, status="running")
                    result["grids"].append(row)
                    write_json_atomic(args.output, result)
                    arrays, metadata = sample_coordinates(wout, surface, resolution)
                    native, clebsch, errors, checks = compare_fields(
                        **{key: arrays[key] for key in keys})
                    path = args.raw / f"{case}-s{surface}-n{resolution}.npz"
                    with path.open("xb") as stream:
                        np.savez_compressed(stream, **arrays, native=native, clebsch=clebsch)
                    row.update(status="completed", arrays=reference(path), metadata=metadata,
                               errors=errors, checks=checks, all_pass=all(checks.values()))
                    write_json_atomic(args.output, result)
                    print(case, surface, resolution, row["all_pass"], errors, flush=True)
        result.update(status="completed", all_pass=all(r["all_pass"] for r in result["grids"]),
                      wout_grids_evaluated=len(result["grids"]))
    except Exception as error:
        result.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write_json_atomic(args.output, result)
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
