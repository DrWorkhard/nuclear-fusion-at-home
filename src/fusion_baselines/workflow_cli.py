"""Thin, allowlisted entry points to existing source-bound research workflows.

Discovery and planning use only the standard library. Scientific computation,
source admission, budgets and result classification remain in frozen backends.
No generic single-candidate workflow is implied by the command name evaluate.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

PROFILE_ID = "clear-coil-field-start-v1"
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
PROFILE = {
    "id": PROFILE_ID,
    "schema_version": 1,
    "description": "Source-bound numerical startup qualification of four fixed coil/target cells",
    "supports_candidate_input": False,
    "operations": ["evaluate", "audit"],
    "fixed_matrix": {"cells": 4, "targets": ["reference", "selected"], "base_coils": [6, 8]},
    "backends": {
        "evaluate": "scripts/run_clear_coil_field_start.py",
        "audit": "scripts/audit_clear_coil_field_start.py",
    },
    "protocol": "docs/optimization/CLEAR_COIL_FIELD_START_PROTOCOL.md",
    "documentation": "docs/validation/PROJECT_ENTRYPOINTS.md",
    "inputs": {
        "evaluate": "Fixed source-bound seeds and targets; no --design or search input",
        "audit": "Complete saved backend run.json and every referenced local artifact",
    },
    "outputs": {
        "evaluate": "Fresh directory containing run.json, worker records and raw arrays",
        "audit": "Fresh JSON report; original inputs and evidence remain unchanged",
    },
    "prerequisites": [
        "Research checkout with scripts/; the Python wheel alone is insufficient",
        "Existing qualified native Python environment and pinned external checkouts",
        "Local source-bound predecessor evidence and raw artifacts, not just tracked JSON",
        "Committed scientific backend sources and unchanged registered protocol",
        "No concurrent heavy jobs during controlled evaluation",
    ],
    "evaluate_limits": {
        "serial_workers": 4,
        "wall_seconds_per_worker": 1800,
        "start_reserve_bytes": 3 * 1024**3,
        "live_reserve_bytes": 2 * 1024**3,
        "native_requests_per_complete_cell": 262,
        "automatic_retries": 0,
        "search_calls": 0,
        "equilibrium_solves": 0,
    },
    "exit_codes": {
        "discovery_and_dry_run": {"0": "Discovery or invocation planning only; no computation"},
        "evaluate": {
            "0": "Producer complete; independent audit still required",
            "1": "Error or incomplete producer",
        },
        "audit": {
            "0": "Numerical startup_pass only",
            "2": "Numerical rejection or audit error; inspect report status",
        },
        "dispatcher": {
            "1": "Checkout/path/process setup error",
            "2": "Command-line usage error",
            "128+N": "Backend signal N; interruption is 130",
        },
    },
    "not_claimed": [
        "Physical seed admission from exit code 0",
        "Generic evaluation of arbitrary new designs",
        "Completed step4, SoTA or SQuID-C readiness",
        "Qualification of the pending coil-perturbation matrix",
    ],
}


def profile_catalog():
    return {"schema_version": 1, "profiles": [copy.deepcopy(PROFILE)]}


def _parser():
    parser = argparse.ArgumentParser(
        prog="python -m fusion_baselines",
        description="Shared research entry points; use profiles to discover the bounded scope.",
    )
    register(parser.add_subparsers(dest="command", required=True))
    return parser


def main():
    try:
        return execute(_parser().parse_args())
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted; retained backend evidence is not a completed result.", file=sys.stderr)
        return 130


def register(commands):
    profiles = commands.add_parser("profiles", help="Discover supported evaluation/audit profiles")
    profiles.add_argument("--json", action="store_true", help="Print machine-readable contracts")
    for operation, description in (
        ("evaluate", "Execute a registered fixed study; not a generic single-design evaluator"),
        ("audit", "Independently check a complete saved study and its referenced evidence"),
    ):
        parser = commands.add_parser(operation, help=description, description=description)
        parser.add_argument("--profile", required=True, choices=[PROFILE_ID])
        if operation == "audit":
            parser.add_argument("--run", required=True, type=Path, help="Existing backend run.json")
        parser.add_argument(
            "--output",
            required=True,
            type=Path,
            help="Fresh directory" if operation == "evaluate" else "Fresh JSON report file",
        )
        parser.add_argument(
            "--project-root",
            type=Path,
            help="Research checkout (default: enclosing checkout or this source checkout)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print exact command/environment plan; no computation or files written",
        )


def _checkout(path):
    root = Path(path).resolve(strict=True)
    metadata = root / "pyproject.toml"
    if not metadata.is_file() or not (root / "src/fusion_baselines/cli.py").is_file():
        raise ValueError(f"Not a fusion-baselines research checkout: {root}")
    with metadata.open("rb") as stream:
        document = tomllib.load(stream)
    if document.get("project", {}).get("name") != "fusion-baselines":
        raise ValueError(f"Wrong project in {metadata}")
    return root


def project_root(explicit=None):
    if explicit is not None:
        return _checkout(explicit)
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents, Path(__file__).resolve().parents[2]):
        try:
            return _checkout(candidate)
        except (OSError, ValueError):
            continue
    raise ValueError(
        "Research checkout not found; use --project-root PATH (wheel alone is insufficient)"
    )


def _fresh(path):
    # Check before resolve too: a dangling symlink is not an unused output name.
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"Output must be new; existing evidence is never overwritten: {path}")
    for parent in path.absolute().parents:
        if parent.exists() or parent.is_symlink():
            if not parent.is_dir():
                raise NotADirectoryError(f"Output parent is not a usable directory: {parent}")
            break
    resolved = path.resolve()
    if resolved.exists() or resolved.is_symlink():
        raise FileExistsError(f"Output already exists: {resolved}")
    return resolved


def plan(args):
    if args.command not in ("evaluate", "audit") or args.profile != PROFILE_ID:
        raise ValueError("Unknown operation or unregistered profile")
    root = project_root(getattr(args, "project_root", None))
    backend = (root / PROFILE["backends"][args.command]).resolve(strict=True)
    if not backend.is_file() or not backend.is_relative_to(root):
        raise ValueError("Profile backend must be a file inside the research checkout")
    output = _fresh(args.output)
    source = None
    if args.command == "evaluate":
        command = [sys.executable, str(backend), "--raw", str(output)]
        report = output / "run.json"
    else:
        # The frozen atomic writer uses a fixed sibling temporary name. Protect
        # that existing file/link too; keep its historical implementation intact.
        _fresh(output.with_suffix(output.suffix + ".tmp"))
        source = Path(args.run).resolve(strict=True)
        if not source.is_file():
            raise ValueError("--run must name an existing backend JSON file")
        command = [sys.executable, str(backend), "--run", str(source), "--output", str(output)]
        report = output
    environment = {
        "PYTHONPATH": str(root / "src"),
        **{key: "1" for key in THREADS},
        "OMPI_MCA_btl": "self",
        "MPLCONFIGDIR": os.environ.get(
            "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "fusion-mpl-cache")
        ),
    }
    return {
        "schema_version": 1,
        "kind": "fusion-command-plan",
        "operation": args.command,
        "profile": PROFILE_ID,
        "project_root": str(root),
        "command": command,
        "cwd": str(root),
        "environment": environment,
        "output": str(output),
        "backend_report": str(report),
        "input": None if source is None else str(source),
        "dry_run": bool(args.dry_run),
        "prerequisites_checked": (
            "Checkout and paths only; backend performs full source/resource admission"
        ),
        "success_meaning": PROFILE["exit_codes"][args.command]["0"],
        "physical_admission_implied": False,
    }


def execute(args):
    if args.command == "profiles":
        if args.json:
            print(json.dumps(profile_catalog(), indent=2, sort_keys=True))
        else:
            print(f"{PROFILE_ID}: {PROFILE['description']}")
            print("  evaluate: fixed four-cell study; arbitrary --design input is NOT supported")
            print("  audit: saved run.json plus local source-bound artifacts")
            print("  Exit 0 is not physical admission. Use profiles --json for the full contract.")
        return 0
    invocation = plan(args)
    if args.dry_run:
        print(json.dumps(invocation, indent=2, sort_keys=True))
        return 0
    environment = dict(os.environ, **invocation["environment"])
    # Inherit streams and normal exits; map a POSIX signal to the usual128+N.
    # Existing backends own resource/worker guards.
    completed = subprocess.run(
        invocation["command"], cwd=invocation["cwd"], env=environment, shell=False, check=False
    )
    return completed.returncode if completed.returncode >= 0 else 128 - completed.returncode
