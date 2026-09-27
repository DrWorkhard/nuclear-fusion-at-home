"""Public starter; retired research commands resolve at the named Git freeze."""

import sys
from pathlib import Path


def main():
    minimum = (3, 11)
    if sys.version_info[:2] < minimum:
        required = ".".join(map(str, minimum))
        detected = ".".join(map(str, sys.version_info[:3]))
        print(
            f"ERROR: This command requires Python {required}+; found {detected}. "
            "Use python3.12 fusion.py ... on macOS/Linux, or "
            "py -3.12 fusion.py ... on Windows. The macOS system python3 may be too old.",
            file=sys.stderr,
        )
        return 2
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    if len(sys.argv) == 1 or sys.argv[1:] in (["--help"], ["-h"]):
        print(
            "Nuclear Fusion @ Home\n\n"
            "Public, portable starter (Python 3.11+, no installation):\n"
            "  python fusion.py public --help\n"
            "  python fusion.py public demo --output results/my-first-demo\n\n"
            "Active native fitting: see docs/optimization/README.md.\n"
            "Frozen research: Git tag research-freeze-2026-09-27.\n"
            "  See docs/validation/REPRODUCING_RESULTS.md for old commands/evidence.\n\n"
            "Start with README.md and CONTRIBUTING.md. "
            "A successful check is not physical admission."
        )
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "public":
        from fusion_public.cli import main as public_main

        return public_main(sys.argv[2:])
    print(
        f"ERROR: The old research command {sys.argv[1]!r} is frozen at Git tag "
        "research-freeze-2026-09-27. Use 'python fusion.py public --help' for the "
        "current starter, or read docs/validation/REPRODUCING_RESULTS.md "
        "for historical replay.", file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
