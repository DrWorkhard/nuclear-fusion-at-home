"""Inventory every finite-pressure configuration in the pinned Goodman ZIP."""

import argparse
from pathlib import Path

import netCDF4
import numpy as np

from fusion_baselines.intake import _scalar, _vmec_summary
from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic
from fusion_baselines.qi_archive import GOODMAN_MD5, extract_verified_members, finite_beta_cases


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=root / "external/data/qifiles.zip")
    parser.add_argument("--target", type=Path,
                        default=root / "external/data/qifiles-finite-beta-v1")
    parser.add_argument("--output", type=Path,
                        default=root / "evidence/qi-finite-beta-inventory-v1.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    cases = finite_beta_cases()
    result = {
        "schema_version": 1,
        "status": "started",
        "repository": git_state(root),
        "host": host_state(),
        "source": "https://zenodo.org/records/7220257",
        "scientific_admission": False,
        "limits": "Inventory only; filename beta is not an author tolerance or solver certificate.",
        "code": [{"path": str(path.relative_to(root)), "sha256": sha256_file(path)} for path in (
            Path(__file__), root / "src/fusion_baselines/qi_archive.py",
            root / "src/fusion_baselines/intake.py")],
    }
    result["archive"] = extract_verified_members(
        args.archive, args.target,
        [case[key] for case in cases for key in ("input_member", "wout_member")],
        expected_md5=GOODMAN_MD5,
    )
    result["archive"]["path"] = str(args.archive.resolve())
    result["extraction_root"] = str(args.target.resolve())
    result["cases"] = cases
    for case in cases:
        wout = args.target / case["wout_member"]
        case["metadata"] = _vmec_summary(wout)
        with netCDF4.Dataset(wout) as dataset:
            case["metadata"]["stellarator_asymmetric"] = _scalar(dataset, "lasym__logical__")
            for name in ("presf", "pres"):
                if name not in dataset.variables:
                    case["metadata"][name + "_finite"] = None
                    continue
                values = np.ma.asarray(dataset[name][:], dtype=float).filled(np.nan)
                case["metadata"][name + "_finite"] = bool(np.all(np.isfinite(values)))
                finite = values[np.isfinite(values)]
                case["metadata"][name + "_min_Pa"] = float(finite.min()) if finite.size else None
                case["metadata"][name + "_max_Pa"] = float(finite.max()) if finite.size else None
        beta = case["metadata"]["beta_total"]
        case["metadata"]["measured_beta_percent"] = 100 * beta if beta is not None else None
        case["nfp_matches_filename"] = case["metadata"]["nfp"] == case["nfp"]
    result["status"] = "completed"
    write_json_atomic(args.output, result)
    print(f"Inventoried {len(cases)} equilibria; scientific admission remains false.")


if __name__ == "__main__":
    main()
