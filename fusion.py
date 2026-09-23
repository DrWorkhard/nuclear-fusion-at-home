"""Public starter: python fusion.py public --help; historical research stays separate."""

import sys
from pathlib import Path


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    if len(sys.argv) == 1 or sys.argv[1:] in (["--help"], ["-h"]):
        print(
            "Nuclear Fusion @ Home\n\n"
            "Public, portable starter (Python3.12+, no installation):\n"
            "  python fusion.py public --help\n"
            "  python fusion.py public demo --output results/my-first-demo\n\n"
            "Historical research workflows (native environment/local artifacts required):\n"
            "  python fusion.py profiles --json\n"
            "  python fusion.py evaluate --help\n"
            "  python fusion.py audit --help\n\n"
            "Start with README.md and CONTRIBUTING.md. "
            "A successful check is not physical admission."
        )
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "public":
        from fusion_public.cli import main as public_main

        return public_main(sys.argv[2:])
    from fusion_baselines.workflow_cli import main as workflow_main

    return workflow_main()


if __name__ == "__main__":
    raise SystemExit(main())
