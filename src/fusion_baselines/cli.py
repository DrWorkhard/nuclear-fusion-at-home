"""Small command-line surface for evidence capture and intake validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fusion_baselines.external import verify_external_spec
from fusion_baselines.manifest import load_manifest, validate_manifest
from fusion_baselines.provenance import build_run_record, write_json_atomic


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fusion-baselines")
    commands = parser.add_subparsers(dest="command", required=True)

    capture = commands.add_parser("capture-environment")
    capture.add_argument("--project-root", type=Path, default=Path.cwd())
    capture.add_argument("--stellcoilbench", type=Path)
    capture.add_argument("--output", type=Path)

    validate = commands.add_parser("validate-manifest")
    validate.add_argument("manifest", type=Path)
    validate.add_argument(
        "--data-root",
        type=Path,
        help="Trusted root against which file paths are resolved (default: manifest directory)",
    )
    validate.add_argument("--structure-only", action="store_true")

    verify = commands.add_parser("verify-stellcoilbench")
    verify.add_argument("--project-root", type=Path, default=Path.cwd())
    verify.add_argument(
        "--spec",
        type=Path,
        default=Path("references/stellcoilbench_baseline.json"),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "capture-environment":
        external = {"stellcoilbench": args.stellcoilbench} if args.stellcoilbench else {}
        record = build_run_record(args.project_root, external)
        if args.output:
            write_json_atomic(args.output, record)
        else:
            print(json.dumps(record, indent=2, sort_keys=True))
        return 0

    if args.command == "verify-stellcoilbench":
        errors = verify_external_spec(args.project_root, args.spec)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print(f"verified: {args.spec}")
        return 0

    manifest = load_manifest(args.manifest)
    data_root = args.data_root if args.data_root is not None else args.manifest.parent
    errors = validate_manifest(
        manifest,
        data_root,
        verify_files=not args.structure_only,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"valid: {args.manifest}")
    return 0
