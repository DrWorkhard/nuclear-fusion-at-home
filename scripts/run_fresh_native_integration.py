"""Preregistered isolated install/build/fresh-W7-X path; never alter qualified checkouts."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from fusion_baselines.provenance import git_state, host_state, sha256_file, write_json_atomic

PINS = {
    "stellcoilbench": "c7949edc4ea6378fc3be633304c69c288c3b79b5",
    "simsopt": "a79006b0bc1e6df8ab48de284e3457d39a49b995",
    "vmecpp": "1d7e09941c89210be95b6b20f4d4d555f0a63096",
    "vmecpp-validation": "4017e53095c09e2ead20c6bb64c12796583520c5",
    "stellopt-v251": "e59affaec7713aee8da1f1bccdf05cc0612c12e3",
}


def reference(path):
    return dict(path=str(path.resolve()), sha256=sha256_file(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("new immutable integration report directory required")
    root = Path(__file__).resolve().parents[1]
    output.mkdir(parents=True)
    scratch = Path(tempfile.mkdtemp(prefix="fusion-native-clean-", dir="/private/tmp"))
    fresh = scratch / "repo"
    report = dict(
        schema_version=1,
        repository=git_state(root),
        host=host_state(),
        protocol=reference(root / "docs/validation/FRESH_NATIVE_INTEGRATION_PROTOCOL.md"),
        scratch=str(scratch),
        fresh_checkout=str(fresh),
        status="running",
        steps=[],
        caches="local Git objects, checksum-verified QI zip, locked uv download/wheel cache",
        system_installation_permitted=False,
        copied_solver_outputs=False,
        code=[
            reference(root / p)
            for p in (
                "scripts/run_fresh_native_integration.py",
                "scripts/bootstrap_macos.sh",
                "scripts/bootstrap_vmecpp.sh",
                "scripts/bootstrap_vmec2000.sh",
                "scripts/bootstrap_qi_data.sh",
                "scripts/run_scientific_integration.py",
            )
        ],
    )
    env = {
        **os.environ,
        "HOMEBREW_NO_AUTO_UPDATE": "1",
        "HOMEBREW_NO_INSTALL_FROM_API": "1",
        "FUSION_NO_SYSTEM_INSTALL": "1",
        "GIT_LFS_SKIP_SMUDGE": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "OMPI_MCA_btl": "self",
        "MPLCONFIGDIR": str(scratch / "mpl-cache"),
        "FUSION_QI_ARCHIVE": str(root / "external/data/qifiles.zip"),
        "PYTHONPATH": "src",
    }
    report["controlled_environment"] = {
        k: env[k]
        for k in (
            "HOMEBREW_NO_AUTO_UPDATE",
            "HOMEBREW_NO_INSTALL_FROM_API",
            "FUSION_NO_SYSTEM_INSTALL",
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
            "FUSION_QI_ARCHIVE",
        )
    }

    def checkpoint():
        write_json_atomic(output / "summary.json", report)

    def run(name, command, cwd):
        path = output / f"{len(report['steps']) + 1:02}-{name}.log"
        record = dict(name=name, command=[str(v) for v in command], cwd=str(cwd), status="running")
        report["steps"].append(record)
        checkpoint()
        print(f"fresh integration: {name}", flush=True)
        started = time.monotonic()
        with path.open("xb") as log:
            process = subprocess.run(
                command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT
            )
        record.update(
            returncode=process.returncode,
            elapsed_seconds=time.monotonic() - started,
            log=reference(path),
            status="passed" if process.returncode == 0 else "failed",
        )
        checkpoint()
        if process.returncode:
            raise RuntimeError(f"{name} failed ({process.returncode}); retained log: {path}")

    try:
        run(
            "prerequisites",
            ["brew", "list", "--versions", "gcc", "open-mpi", "netcdf", "netcdf-fortran", "lapack"],
            root,
        )
        run("clone-project", ["git", "clone", "--no-hardlinks", str(root), str(fresh)], scratch)
        run("pin-project", ["git", "checkout", "--detach", report["repository"]["commit"]], fresh)
        (fresh / "external").mkdir(exist_ok=True)
        for name, pin in PINS.items():
            source, destination = root / "external" / name, fresh / "external" / name
            if not (source / ".git").exists():
                raise FileNotFoundError(f"missing read-only source cache: {source}")
            run(
                f"clone-{name}",
                ["git", "clone", "--no-hardlinks", str(source), str(destination)],
                fresh,
            )
            run(f"pin-{name}", ["git", "-C", str(destination), "checkout", "--detach", pin], fresh)
        run("benchmark-environment", ["bash", "scripts/bootstrap_macos.sh"], fresh)
        run("vmecpp-environment", ["bash", "scripts/bootstrap_vmecpp.sh"], fresh)
        run("vmec852-build", ["bash", "scripts/bootstrap_vmec2000.sh"], fresh)
        run("qi-fresh-extraction", ["bash", "scripts/bootstrap_qi_data.sh"], fresh)
        python = fresh / ".venv/bin/python"
        vmec_python = fresh / "environments/vmecpp/.venv/bin/python"
        case = (
            fresh
            / "external/stellcoilbench/plasma_surfaces"
            / "input.W7-X_without_coil_ripple_beta0p05_d23p4_tm"
        )
        if sha256_file(case) != "f927a2a4d0adba1dc12406ae9fbf51a82d38cb6f00f0b9cab1ff8908ef35fac8":
            raise ValueError("fixed W7-X input hash changed")
        report["input"] = reference(case)
        report["fresh_binary"] = reference(
            fresh / "external/stellopt-v251/VMEC2000/Release/xvmec2000"
        )
        run(
            "fresh-vmecpp-w7x",
            [
                str(vmec_python),
                "scripts/run_vmecpp_equilibrium.py",
                str(case),
                "artifacts/vmecpp/w7x-stellcoilbench",
            ],
            fresh,
        )
        run(
            "fresh-vmec852-w7x",
            [
                str(python),
                "scripts/run_vmec2000_reference.py",
                str(case),
                "artifacts/vmec2000/w7x-v852-reference",
            ],
            fresh,
        )
        run(
            "strict-six-test-integration",
            [
                str(python),
                "scripts/run_scientific_integration.py",
                "evidence/fresh-native-six-tests-v1",
            ],
            fresh,
        )
        integration = fresh / "evidence/fresh-native-six-tests-v1"
        for name in ("summary.json", "tests.xml", "pytest.log"):
            shutil.copy2(integration / name, output / f"strict-{name}")
        strict = json.loads((integration / "summary.json").read_text())
        report["strict_integration"] = reference(output / "strict-summary.json")
        report["wouts"] = [
            reference(fresh / p)
            for p in (
                "artifacts/vmecpp/w7x-stellcoilbench/wout.nc",
                "artifacts/vmec2000/w7x-v852-reference/wout_w7xbaseline.nc",
            )
        ]
        report.update(
            status="completed",
            all_pass=bool(strict["all_pass"]),
            full_global_physics_qualification=False,
        )
    except Exception as error:
        report.update(status="error", all_pass=False, error=f"{type(error).__name__}: {error}")
        raise
    finally:
        checkpoint()
    print(json.dumps({"all_pass": report["all_pass"]}), flush=True)


if __name__ == "__main__":
    main()
