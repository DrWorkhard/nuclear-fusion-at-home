"""Checkout-local launcher: .venv/bin/python fusion.py profiles --json."""

import sys
from pathlib import Path


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    from fusion_baselines.workflow_cli import main as workflow_main

    return workflow_main()


if __name__ == "__main__":
    raise SystemExit(main())
