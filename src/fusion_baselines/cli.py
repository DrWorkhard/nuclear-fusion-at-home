"""Small public dispatcher and explicit retirement notice for the old research CLI."""

import sys

FREEZE = "research-freeze-2026-09-27"


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "public":
        from fusion_public.cli import main as public_main

        return public_main(args[1:])
    if not args or args in (["--help"], ["-h"]):
        print("Public starter: python fusion.py public --help\n"
              "Active native fitting: docs/optimization/README.md\n"
              f"Frozen research commands and evidence: Git tag {FREEZE}\n"
              "Reproduction: docs/validation/REPRODUCING_RESULTS.md")
        return 0
    print(f"ERROR: The old research command {args[0]!r} is frozen at Git tag {FREEZE}. "
          "Use 'python fusion.py public --help' for the current starter, or read "
          "docs/validation/REPRODUCING_RESULTS.md for historical replay.", file=sys.stderr)
    return 2
