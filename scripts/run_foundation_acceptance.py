"""One sequential local foundation acceptance; no installation, new build or long search."""

import argparse
import os
import subprocess
from pathlib import Path

from audit_foundation_acceptance import PRIOR, PROTOCOL, external_state, preservation
from audit_foundation_cycle import CODE as AUDIT_CODE
from current_diagnostic_inputs import reference
from run_foundation_cycle import CODE as CYCLE_CODE
from run_jac_scaled_study import require_committed

from fusion_baselines.foundation_acceptance import UNSUPPORTED
from fusion_baselines.provenance import git_state, host_state, write_json_atomic
from fusion_baselines.resource_guard import GIB, guarded_run, space_check

CODE = sorted(
    set(CYCLE_CODE)
    | set(AUDIT_CODE)
    | {
        "scripts/run_foundation_acceptance.py",
        "scripts/audit_foundation_acceptance.py",
        "src/fusion_baselines/foundation_acceptance.py",
        "tests/test_foundation_acceptance.py",
        "scripts/run_coil_holdouts.py",
        "scripts/run_scientific_integration.py",
        "scripts/audit_netcdf_import_warning.py",
        "scripts/check_docs.py",
        "scripts/validate_normalized_candidates.py",
        "scripts/bound_continuous_curvature.py",
        "scripts/bound_continuous_coil_clearance.py",
        "scripts/validate_direct_native_constraints.py",
        "src/fusion_baselines/integration_audit.py",
        "pyproject.toml",
        "uv.lock",
    }
)


def phase_commands(root, output, raw):
    python = str(root / ".venv/bin/python")
    paths = dict(
        regression=output / "tests.xml",
        scientific=output / "scientific/summary.json",
        warning=output / "warning.json",
        cycle=output / "cycle/summary.json",
        **{
            "cycle-audit": output / "cycle-audit.json",
            "holdouts": output / "holdouts/summary.json",
        },
    )
    specs = [
        ("regression", [python, "-m", "pytest", "-q", f"--junitxml={paths['regression']}"]),
        ("ruff", [str(root / ".venv/bin/ruff"), "check", "."]),
        ("docs", [python, "scripts/check_docs.py"]),
        (
            "scientific",
            [python, "scripts/run_scientific_integration.py", str(output / "scientific")],
        ),
        ("warning", [python, "scripts/audit_netcdf_import_warning.py", str(paths["warning"])]),
        ("cycle", [python, "scripts/run_foundation_cycle.py", str(output / "cycle"), str(raw)]),
        (
            "cycle-audit",
            [
                python,
                "scripts/audit_foundation_cycle.py",
                str(output / "cycle"),
                str(paths["cycle-audit"]),
            ],
        ),
        (
            "holdouts",
            [
                python,
                "scripts/run_coil_holdouts.py",
                str(output / "cycle"),
                str(paths["cycle-audit"]),
                str(output / "holdouts"),
            ],
        ),
    ]
    return [(name, command, paths.get(name, output / f"{name}.log")) for name, command in specs]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("raw", type=Path)
    args = parser.parse_args()
    output, raw = args.output.resolve(), args.raw.resolve()
    if output.exists() or raw.exists() or output == raw:
        raise FileExistsError("distinct new immutable report and raw directories required")
    root = Path(__file__).resolve().parents[1]
    for path in [root / PROTOCOL, *(root / p for p in CODE)]:
        require_committed(root, path)
    before = preservation(root)
    if not before["all_pass"]:
        raise ValueError("historical state modified outside permitted overview updates")
    disk = space_check(root, 3 * GIB)
    env = {
        **os.environ,
        "PYTHONPATH": str(root / "src"),
        "MPLCONFIGDIR": "/private/tmp/fusion-mpl-cache",
        "OMPI_MCA_btl": "self",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    output.mkdir(parents=True)
    run = dict(
        status="running",
        repository=git_state(root),
        host=host_state(),
        protocol=reference(root / PROTOCOL),
        code=[reference(root / p) for p in CODE],
        prior_evidence={k: reference(root / v) for k, v in PRIOR.items()},
        preservation_before=before,
        external_before=external_state(root),
        raw_directory=str(raw),
        steps=[],
        disk_preflight=disk,
        unsupported_capabilities={k: False for k in UNSUPPORTED},
        controlled_environment={
            k: env[k]
            for k in (
                "PYTHONPATH",
                "MPLCONFIGDIR",
                "OMPI_MCA_btl",
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
            )
        },
        audit_command=[
            str(root / ".venv/bin/python"),
            "scripts/audit_foundation_acceptance.py",
            str(output / "run.json"),
            str(output / "summary.json"),
        ],
    )
    try:
        for name, command, result in phase_commands(root, output, raw):
            row = dict(name=name, command=command, status="running")
            run["steps"].append(row)
            write_json_atomic(output / "run.json", run)
            print(f"Foundation acceptance: {name}", flush=True)
            log = output / f"{name}.log"
            with log.open("xb") as stream:
                row.update(
                    guarded_run(
                        command,
                        cwd=root,
                        env=env,
                        stdout=stream,
                        space_root=root,
                        reserve_bytes=2 * GIB,
                    )
                )
            row["log"] = reference(log)
            if result.is_file():
                row["result"] = reference(result)
            if row["returncode"] != 0:
                raise RuntimeError(f"{name} failed, exit {row['returncode']}; retained at {log}")
            row["status"] = "completed"
        run["status"] = "completed"
    except Exception as exc:
        run.update(status="error", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        write_json_atomic(output / "run.json", run)
    # The immutable producer record is closed before the independent audit binds it.
    with (output / "audit.log").open("xb") as stream:
        result = subprocess.run(
            run["audit_command"],
            cwd=root,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    print((output / "audit.log").read_text(), end="", flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
