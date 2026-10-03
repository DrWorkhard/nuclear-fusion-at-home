"""Public entry point: stdlib only; real data is bundled, no native setup needed."""

import argparse
import json
import re
import sys
from pathlib import Path

from .data import CASE_ID, load, load_case, save_new
from .report import audit, evaluate
from .submission import validate
from .usability import score_comparison, set_coefficient, validate_for_cli


def parser():
    result = argparse.ArgumentParser(
        prog="python fusion.py public", description="Nuclear Fusion @ Home portable starter"
    )
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("cases", help="List portable cases and their scientific limits")
    init = commands.add_parser("init", help="Write a candidate template to a new file")
    init.add_argument("--output", type=Path, required=True)
    edit = commands.add_parser(
        "set-coefficient", help="Set one named coefficient to an absolute value in metres",
        description="Set an absolute Fourier coefficient, not an increment. "
        'Example name: "coil[0]/xc(0)". Use double quotes in your shell.',
    )
    # argparse's default pattern mistakes negative exponents for options before
    # type=float can run. Limit the extended number syntax to this subcommand.
    edit._negative_number_matcher = re.compile(
        r"^-(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
    )
    edit.add_argument("--candidate", type=Path, required=True)
    edit.add_argument("--name", required=True,
                      help='Exact parameter_names entry, e.g. "coil[0]/xc(0)"')
    edit.add_argument("--value", type=float, required=True,
                      help="Absolute value in metres, not a delta (e.g. --value -1e-4)")
    edit.add_argument("--output", type=Path, required=True, help="Fresh JSON file")
    demo = commands.add_parser("demo", help="Reproduce the starter and replay its report")
    demo.add_argument("--output", type=Path, required=True, help="Fresh directory")
    ev = commands.add_parser("evaluate", help="Compute sampled fields for a candidate")
    ev.add_argument("--candidate", type=Path, required=True)
    ev.add_argument("--output", type=Path, required=True, help="Fresh JSON file")
    au = commands.add_parser("audit", help="Recompute a report, not full design acceptance")
    au.add_argument("--report", type=Path, required=True)
    au.add_argument("--output", type=Path, required=True)
    submission = commands.add_parser("check-submission", help="Check optional PR metadata")
    submission.add_argument("--file", type=Path, required=True)
    return result


def fresh(path):
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"Output already exists; choose a fresh path: {path}")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "check-submission":
            print(json.dumps(validate(load(args.file)), indent=2))
            return 0
        case, digest = load_case()
        if args.command == "cases":
            print(json.dumps(dict(
                schema_version=1, cases=[dict(
                    id=CASE_ID, data_sha256=digest, accepts_candidate=True,
                    requirements="Python 3.11+ standard library; no network or native solver",
                    physical_admission=False,
                    scope="64 boundary, 64 inner, 64 loop points; fixed-current filament B/A",
                )],
            ), indent=2))
            return 0
        fresh(args.output)
        if args.command == "set-coefficient":
            candidate = set_coefficient(load(args.candidate), args.name, args.value)
            save_new(args.output, candidate)
            print(f"Set {args.name} = {args.value} m; saved {args.output}. "
                  "Evaluate this candidate next.")
            return 0
        if args.command == "init":
            save_new(args.output, case["seed"])
            print(f"Candidate written to {args.output}; this is not a feasible design.")
            return 0
        if args.command == "demo":
            args.output.mkdir(parents=True, exist_ok=False)
            save_new(args.output / "candidate.json", case["seed"])
            report = evaluate(case["seed"], case, digest)
            save_new(args.output / "report.json", report)
            replay = audit(report)
            save_new(args.output / "audit.json", replay)
            passed = replay["report_replay_pass"] and replay["seed_native_reference_pass"] is True
            print(json.dumps(dict(output=str(args.output), reference_reproduced=passed,
                                  comparison=score_comparison(report, case),
                                  physical_admission=False, step4_pass=False), indent=2))
            return 0 if passed else 2
        if args.command == "evaluate":
            report = evaluate(validate_for_cli(load(args.candidate)), case, digest)
            save_new(args.output, report)
            print(json.dumps(dict(output=str(args.output), physical_admission=False,
                                  comparison=score_comparison(report, case),
                                  sampled_metrics_512=report["levels"][1]["metrics"]), indent=2))
            return 0
        if args.command == "audit":
            replay = audit(load(args.report))
            save_new(args.output, replay)
            print(json.dumps(replay, indent=2))
            return 0
    except (ValueError, OSError, KeyError, TypeError, OverflowError, RecursionError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted. Saved files are not a completed result.", file=sys.stderr)
        return 130
    return 2
