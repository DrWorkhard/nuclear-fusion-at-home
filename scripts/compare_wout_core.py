"""Compare VMEC++ output to a VMEC reference using Proxima V&V tolerances."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import netCDF4
import numpy as np

SCALARS = [
    "niter",
    "wb",
    "wp",
    "aspect",
    "betatotal",
    "betapol",
    "betator",
    "betaxis",
    "b0",
    "rbtor0",
    "rbtor",
    "IonLarmor",
    "volavgB",
    "ctor",
    "Aminor_p",
    "Rmajor_p",
    "volume_p",
    "fsqr",
    "fsqz",
    "fsql",
]
PROFILES = [
    "iotaf",
    "q_factor",
    "presf",
    "phi",
    "phipf",
    "chi",
    "chipf",
    "jcuru",
    "jcurv",
    "iotas",
    "mass",
    "pres",
    "beta_vol",
    "buco",
    "bvco",
    "vp",
    "specw",
    "phips",
    "over_r",
    "jdotb",
    "bdotgradv",
    "DMerc",
    "DShear",
    "DWell",
    "DCurr",
    "DGeod",
    "equif",
]
FOURIER = [
    "raxis_cc",
    "zaxis_cs",
    "rmnc",
    "zmns",
    "lmns",
    "bmnc",
    "gmnc",
    "bsubumnc",
    "bsubvmnc",
    "bsubsmns",
    "bsupumnc",
    "bsupvmnc",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("under_test", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root / "external/vmecpp-validation"))
    from src.tolerances import _DEFAULT_TOL, _TOLERANCES  # noqa: PLC0415

    def fixed_boundary_tolerance(name: str) -> float:
        tolerance = _TOLERANCES.get(name, _DEFAULT_TOL)
        return tolerance[0] if isinstance(tolerance, tuple) else tolerance

    records = []
    with (
        netCDF4.Dataset(args.under_test) as test,
        netCDF4.Dataset(args.reference) as reference,
    ):
        for name in SCALARS + PROFILES + FOURIER:
            tolerance = fixed_boundary_tolerance(name)
            if name not in test.variables or name not in reference.variables:
                records.append({"variable": name, "status": "missing", "tolerance": tolerance})
                continue
            value = np.asarray(test[name][:])
            expected = np.asarray(reference[name][:])
            if value.shape != expected.shape:
                records.append(
                    {
                        "variable": name,
                        "status": "shape_mismatch",
                        "test_shape": value.shape,
                        "reference_shape": expected.shape,
                        "tolerance": tolerance,
                    }
                )
                continue
            error = np.abs((value - expected) / (1.0 + np.abs(expected)))
            maximum = float(np.max(error))
            records.append(
                {
                    "variable": name,
                    "status": "pass" if maximum <= tolerance else "fail",
                    "max_normalized_error": maximum,
                    "tolerance": tolerance,
                }
            )

    failed = [record for record in records if record["status"] != "pass"]
    summary = {
        "schema_version": 1,
        "tolerance_source_commit": subprocess_head(project_root / "external/vmecpp-validation"),
        "under_test": str(args.under_test.resolve()),
        "reference": str(args.reference.resolve()),
        "variables_checked": len(records),
        "variables_passed": len(records) - len(failed),
        "overall_pass": not failed,
        "failed": failed,
        "checks": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "checks"}, indent=2))
    return 0 if not failed else 1


def subprocess_head(path: Path) -> str | None:
    import subprocess

    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


if __name__ == "__main__":
    raise SystemExit(main())
