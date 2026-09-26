"""Check documentation layout/links without native physics dependencies."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fusion_baselines.documentation import check_documentation  # noqa: E402
from fusion_baselines.documentation_policy import check_overview_policy  # noqa: E402


def main():
    root = Path(__file__).resolve().parents[1]
    errors = check_documentation(root) + check_overview_policy(root)
    for error in errors:
        print(error)
    print(f"Documentation structure: {'FAIL' if errors else 'PASS'} ({len(errors)} errors)")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
